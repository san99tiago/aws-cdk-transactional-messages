#!/usr/bin/env python3

################################################################################
# CDK SOLUTION FOR: APIGATEWAY-SQS-LAMBDA (TEMPLATE)
################################################################################

# Built-in imports
import os

# External imports
import aws_cdk as cdk

# Own imports
import add_tags
from stacks.cdk_api_gateway_sqs_lambda import ApiGatewaySqsLambdaStack


print("--> Deployment AWS configuration (safety first):")
print("CDK_DEFAULT_ACCOUNT", os.getenv("CDK_DEFAULT_ACCOUNT"))
print("CDK_DEFAULT_REGION", os.getenv("CDK_DEFAULT_REGION"))


# Global configurations for the deployment (standard way across CDK deployments)
DEPLOYMENT_ENVIRONMENT = "dev"
NAME_PREFIX = ""
MAIN_RESOURCES_NAME = "apigw-sqs-lambda"


app = cdk.App()
stack = ApiGatewaySqsLambdaStack(
    app,
    "ApiGatewaySqsLambdaStack",
    NAME_PREFIX,
    MAIN_RESOURCES_NAME,
    DEPLOYMENT_ENVIRONMENT,
    env={
        "account": os.getenv("CDK_DEFAULT_ACCOUNT"),
        "region": os.getenv("CDK_DEFAULT_REGION"),
    },
    description="Stack for {} infrastructure in {} environment".format(MAIN_RESOURCES_NAME, DEPLOYMENT_ENVIRONMENT),
)

add_tags.add_tags_to_stack(
    stack,
    MAIN_RESOURCES_NAME,
    DEPLOYMENT_ENVIRONMENT,
)

app.synth()
