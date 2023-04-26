# Built-in imports
import os

# External imports
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_apigateway,
    aws_sqs,
    aws_lambda,
    aws_iam,
    aws_lambda_event_sources,
    aws_cloudwatch,
    aws_cloudwatch_actions,
    aws_sns,
    aws_sns_subscriptions,
)
from constructs import Construct


class ApiGatewaySqsLambdaStack(Stack):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            name_prefix: str,
            main_resources_name: str,
            deployment_environment: str,
            **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Input parameters
        self.construct_id = construct_id
        self.name_prefix = name_prefix
        self.main_resources_name = main_resources_name
        self.deployment_environment = deployment_environment

        # Additional configurations
        self.api_stage_deployment_version = "v1"
        self.sns_notifications_email = "san99tiagodevsecops+alarms@gmail.com"
        self.powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            id="Lambda-Powertools",
            layer_version_arn=f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31"
        )

        # Main methods for the deployment
        self.create_queues()
        self.create_alarm_and_notifications_for_dlq()
        self.create_lambda()
        self.configure_sqs_event_source_for_lambda()
        self.create_api_gateway()
        self.create_api_gateway_to_sqs_role()
        self.create_api_gateway_integration_proxy_to_sqs()
        self.create_api_gateway_resource_and_route()

        # Create CloudFormation outputs
        self.generate_cloudformation_outputs()

    def create_queues(self):
        """
        Create the SQS queue.
        """
        # Configure DLQ for the queue (for non-processed messages)
        self.dead_letter_queue = aws_sqs.Queue(
            self,
            id="DeadLetterQueue",
            queue_name="{}{}-queue-dlq".format(self.name_prefix, self.main_resources_name),
            retention_period=Duration.days(7),
        )

        # Main queue for the solution
        self.queue = aws_sqs.Queue(
            self,
            id="Queue",
            queue_name="{}{}-queue".format(self.name_prefix, self.main_resources_name),
            retention_period=Duration.days(5),
            visibility_timeout=Duration.seconds(60),
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.dead_letter_queue
            ),
        )

    def create_alarm_and_notifications_for_dlq(self):
        """
        Create the alarm and SNS notifications for the SQS Dead Letter Queue
        (DLQ) based on messages on the queue.
        """
        # Create SNS topic and email subscription for it
        self.sns_topic_dlq = aws_sns.Topic(
            self,
            id="DLQTopic",
            topic_name="{}{}-topic".format(self.name_prefix, self.main_resources_name),
            display_name="{}{}-topic".format(self.name_prefix, self.main_resources_name),
        )
        self.sns_topic_dlq.add_subscription(
            aws_sns_subscriptions.EmailSubscription(self.sns_notifications_email)
        )

        # Create DLQ alarm for 1+ messages in queue
        self.dead_letter_queue_alarm = aws_cloudwatch.Alarm(
            self,
            id="DLQAlarm",
            alarm_name="{}{}-alarm".format(self.name_prefix, self.main_resources_name),
            alarm_description="Messages on DLQ for {} solution".format(self.main_resources_name),
            metric=self.dead_letter_queue.metric("ApproximateNumberOfMessagesVisible"),
            threshold=0.5,
            evaluation_periods=1,
            actions_enabled=True,
        )

        # Configure CW Alarm action with the SNS topic
        self.sns_action_alarm = aws_cloudwatch_actions.SnsAction(self.sns_topic_dlq)
        self.dead_letter_queue_alarm.add_alarm_action(self.sns_action_alarm)

    def create_lambda(self):
        """
        Create the Lambda Function.
        """
        # Get relative path for folder that contains Lambda function source
        # ! Note--> we must obtain parent dirs to create path (that"s why there is "os.path.dirname()")
        PATH_TO_FUNCTION_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "lambda",
            "src",
        )
        self.lambda_function = aws_lambda.Function(
            self,
            id="Lambda",
            function_name="{}{}-lambda".format(self.name_prefix, self.main_resources_name),
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.handler",
            code=aws_lambda.Code.from_asset(PATH_TO_FUNCTION_FOLDER),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "ENVIRONMENT": self.deployment_environment,
                "OWNER": "Santiago Garcia Arango",
                "LOG_LEVEL": "DEBUG",
            },
            layers=[self.powertools_layer],
            tracing=aws_lambda.Tracing.ACTIVE,
        )
        self.lambda_function.role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name("AWSXrayWriteOnlyAccess")
        )

    def configure_sqs_event_source_for_lambda(self):
        """
        Configure the SQS as the event source of the Lambda Function.
        """
        self.sqs_event_source = aws_lambda_event_sources.SqsEventSource(
            self.queue,
            enabled=True,
            batch_size=5,
        )
        self.lambda_function.add_event_source(self.sqs_event_source)

    def create_api_gateway(self):
        """
        Create the API Gateway.
        """
        self.api_gateway = aws_apigateway.RestApi(
            self,
            id="ApiGateway",
            rest_api_name="{}{}-api".format(self.name_prefix, self.main_resources_name),
            description="API Gateway for {} solution".format(self.main_resources_name),
            deploy=True,
            deploy_options=aws_apigateway.StageOptions(
                stage_name=self.api_stage_deployment_version,
                description="{} deployment".format(self.api_stage_deployment_version),
                logging_level=aws_apigateway.MethodLoggingLevel.INFO,
                tracing_enabled=True,  # Relevant config for X-ray tracing for complete traces
            ),
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_credentials=False,
                allow_headers=["*"],
                allow_methods=["POST"],
                allow_origins=["*"],
            ),
        )

    def create_api_gateway_to_sqs_role(self):
        """
        Create the IAM Role for the API Gateway to SQS actions.
        """
        self.api_gateway_sqs_integration_role = aws_iam.Role(
            self,
            id="ApiGatewayRole",
            assumed_by=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
        )

        # Allow CW operations to API Gateway Role
        self.api_gateway_sqs_integration_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                managed_policy_name="service-role/AmazonAPIGatewayPushToCloudWatchLogs",
            ),
        )

        # Allow API Gateway Role to "sqs:sendMessage*" to queue
        self.queue.grant_send_messages(self.api_gateway_sqs_integration_role)

        # Allow API Gateway Role to send traces to X-Ray
        self.api_gateway_sqs_integration_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name("AWSXrayWriteOnlyAccess")
        )

    def create_api_gateway_integration_proxy_to_sqs(self):
        """
        Create the API Gateway integration proxy to SQS.
        """
        # Note 1: The "request_templates" allows us to proxy the request payload to SQS structure
        # Note 2: the "integration_responses" are important, otherwise we get error:
        # ... <Execution failed due to configuration error>
        self.api_gateway_integration = aws_apigateway.AwsIntegration(
            service="sqs",
            path="{}/{}".format(os.environ.get("CDK_DEFAULT_ACCOUNT"), self.queue.queue_name),
            integration_http_method="POST",
            options=aws_apigateway.IntegrationOptions(
                credentials_role=self.api_gateway_sqs_integration_role,
                passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_MATCH,
                request_templates={
                    "application/json": "Action=SendMessage&MessageBody=$input.body",
                },
                request_parameters={
                    "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'",
                },
                integration_responses=[
                    aws_apigateway.IntegrationResponse(status_code="200"),
                    aws_apigateway.IntegrationResponse(status_code="400"),
                    aws_apigateway.IntegrationResponse(status_code="500"),
                ],
            ),
        )

    def create_api_gateway_resource_and_route(self):
        """
        Create the API Gateway "/message" resource and route for the POST requests,
        which are messages that will be integrated via aws_proxy to the SQS.
        """
        # Create the "<api_endpoint>/message" resource (path)
        self.send_message_api_gateway_resource = self.api_gateway.root.add_resource(
            path_part="message",
        )

        # Add to the "<api_endpoint>/message" resource the POST method and integration
        # Note: the "method_responses" are important, otherwise we get error:
        # ... <Execution failed due to configuration error>
        self.send_message_api_gateway_resource.add_method(
            http_method="POST",
            integration=self.api_gateway_integration,
            operation_name="SendMessage",
            method_responses=[
                aws_apigateway.MethodResponse(status_code="200"),
                aws_apigateway.MethodResponse(status_code="400"),
                aws_apigateway.MethodResponse(status_code="500"),
            ],
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """

        CfnOutput(
            self,
            "DeploymentEnvironment",
            value=self.deployment_environment,
            description="Deployment environment",
        )

        CfnOutput(
            self,
            "ApiEndpoint",
            value=self.api_gateway.url_for_path("/message"),
            description="API Gateway endpoint",
        )
