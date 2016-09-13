#!/usr/bin/env python
"""Upload and Create Elastic Beanstalk Application Version

This can be used as an alternative to the Terraform managed resource aws_elastic_beanstalk_application_version. This
script is meant to be used by a continuous deployment system (Bamboo, Jenkins, etc) and it should be called in two
places:

1) Separate task/stage that runs before Terraform
2) As a Terraform provisioner for the aws_elastic_beanstalk_application resource

This will ensure that the application version is created before Terraform creates or updates the Elastic Beanstalk
Environment. This also enables the Environment to be updated with one API call, instead of potentially two. On the
initial run, the script may fail if the Elastic Beanstalk Application has not been created yet. Because of this that
specific error is ignored by the script.

The following environment variables are used
  TF_VAR_aws_region
  TF_VAR_elastic_beanstalk_s3_bucket
  TF_VAR_elastic_beanstalk_s3_key
  TF_VAR_elastic_beanstalk_application_name
  TF_VAR_elastic_beanstalk_application_version


Example Terraform Document

variable "aws_region" { }
variable "elastic_beanstalk_application_name" { }
variable "elastic_beanstalk_application_version" { }

provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_elastic_beanstalk_application" "default" {
  name        = "${var.elastic_beanstalk_application_name}"
  description = ""

  provisioner "local-exec" {
    command = "./create_application_version.py"
  }
}

resource "aws_elastic_beanstalk_environment" "default" {
  name                = ""
  application         = "${aws_elastic_beanstalk_application.default.name}"
  solution_stack_name = ""
  version_label       = "${var.elastic_beanstalk_application_version}"
}

"""

import boto3, botocore.exceptions
import os, sys
import re


def check_bundle():
    """Check if the Elastic Beanstalk Application Version source bundle already exists"""
    s3 = boto3.client('s3', region_name=os.environ['TF_VAR_aws_region'])

    try:
        s3.get_object(
            Bucket=os.environ['TF_VAR_elastic_beanstalk_s3_bucket'],
            Key=os.environ['TF_VAR_elastic_beanstalk_s3_key']
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            return False
        else:
            raise e
    else:
        return True


def upload_bundle():
    """Upload Elastic Beanstalk Application Version source bundle to S3"""
    s3 = boto3.client('s3', region_name=os.environ['TF_VAR_aws_region'])

    try:
        s3.put_object(
            Body=os.environ['TF_VAR_elastic_beanstalk_s3_key'],
            Bucket=os.environ['TF_VAR_elastic_beanstalk_s3_bucket'],
            Key=os.environ['TF_VAR_elastic_beanstalk_s3_key']
        )
    except Exception as e:
        raise e


def create_application_version():
    """Create Elastic Beanstalk Application Version"""
    beanstalk = boto3.client('elasticbeanstalk', region_name=os.environ['TF_VAR_aws_region'])
    application_not_found_re = r'^No Application named .*? found.$'

    try:
        beanstalk.create_application_version(
            ApplicationName=os.environ['TF_VAR_elastic_beanstalk_application_name'],
            VersionLabel=os.environ['TF_VAR_elastic_beanstalk_application_version'],
            SourceBundle={
                'S3Bucket': os.environ['TF_VAR_elastic_beanstalk_s3_bucket'],
                'S3Key': os.environ['TF_VAR_elastic_beanstalk_s3_key']
            }
        )
    except botocore.exceptions.ClientError as e:
        if re.match(application_not_found_re, e.response['Error']['Message']):
            pass
        else:
            raise e


if __name__ == "__main__":
    if not check_bundle():
        upload_bundle()
        create_application_version()
    else:
        print("Failed to create Application Version: source bundle already exists, please use a uniqe name")
        sys.exit(-1)
