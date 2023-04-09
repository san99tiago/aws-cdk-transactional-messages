#!/usr/bin/env python3
import aws_cdk as cdk


def add_tags_to_stack(stack, main_resources_name, deployment_environment):
    """
    Function to add custom tags to stack in a centralized fashion.
    :param stack: (aws_cdk.Stack) to apply tags to.
    :param main_resources_name: (string) value of the tag "MainResourcesName".
    :param deployment_environment: (string) value of the tag "environment".
    """

    cdk.Tags.of(stack).add("Owner", "Santiago Garcia Arango")
    cdk.Tags.of(stack).add("Environment", deployment_environment)
    cdk.Tags.of(stack).add("MainResourcesName", main_resources_name)
    cdk.Tags.of(stack).add("Confidential", "true")
    cdk.Tags.of(stack).add("Source", "https://github.com/san99tiago/aws-cdk-apigw-sqs-lambda")
    cdk.Tags.of(stack).add("Usage", "Template for an AWS API Gateway SQS and Lambda solution")
