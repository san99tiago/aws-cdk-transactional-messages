################################################################################
# Lambda Function to "simulate" the processing of the messages
################################################################################

# Built-in imports
import time
import json

# External imports
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import event_source, SQSEvent


tracer = Tracer(service="MessagesAPIService")
logger = Logger(service="MessagesAPIService", log_uncaught_exceptions=True)
logger.append_keys(owner="san99tiago")


@tracer.capture_method
def process_messages(event: SQSEvent):
    tracer.put_metadata(key="total_messages", value=len(list(event.records)))
    # Multiple records can be delivered in a single event, so loop through them
    for record in event.records:
        logger.debug(record.raw_event)
        payload = record.body
        sqs_message_id = record.message_id
        logger.info(payload)
        logger.info(sqs_message_id)

        # Simulate a "time" processing delay for the messages
        logger.debug("Processing message")
        tracer.put_annotation(key="sqs_id", value=sqs_message_id)
        time.sleep(4)
        logger.debug("Finished processing message")

        # Validate "Message" key on input, otherwise return failure
        # Note: if input does not contain "Message" key, this will raise an error
        message = json.loads(payload)["Message"]
        logger.info("Message: {}".format(message))


@logger.inject_lambda_context(log_event=True)
@event_source(data_class=SQSEvent)
@tracer.capture_lambda_handler
def handler(event: SQSEvent, context: LambdaContext) -> str:
    logger.debug("Starting messages processing")
    tracer.put_metadata(key="details", value="messages processing handler")
    try:
        process_messages(event)
    except Exception as e:
        logger.exception("Error processing the messages")
        raise RuntimeError("Processing failed for the input messages") from e
    logger.debug("Finished messages processing")

    return "Successfully processed message"
