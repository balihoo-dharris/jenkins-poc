variable "aws_region" { }
variable "elastic_beanstalk_application_name" { }
variable "elastic_beanstalk_application_version" { }

provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_elastic_beanstalk_application" "default" {
  name        = "${var.elastic_beanstalk_application_name}"
  description = "Elastic Beanstalk Test"

  provisioner "local-exec" {
    command = "./create_application_version.py"
  }
}

resource "aws_elastic_beanstalk_environment" "default" {
  name                = "test"
  application         = "${aws_elastic_beanstalk_application.default.name}"
  solution_stack_name = "64bit Amazon Linux 2016.03 v2.1.6 running Go 1.5"
  version_label       = "${var.elastic_beanstalk_application_version}"
}
