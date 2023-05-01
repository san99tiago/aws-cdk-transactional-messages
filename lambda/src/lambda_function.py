################################################################################
# Lambda Function to "simulate" the processing of the messages
################################################################################

# Built-in imports
import time
import json

# External imports
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
from aws_lambda_powertools.utilities.batch.types import PartialItemFailureResponse
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord


tracer = Tracer(service="MessagesAPIService")
logger = Logger(service="MessagesAPIService", log_uncaught_exceptions=True, owner="san99tiago")
processor = BatchProcessor(event_type=EventType.SQS)


@tracer.capture_method
def process_message(record: SQSRecord):
    # Add message id for each log statement so we know which message is being processed
    logger.append_keys(message_id=record.message_id)

    # Batch will call this function for each record and will handle partial failures
    logger.info(record.body)

    # Simulate a "time" processing delay for the messages
    logger.debug("Processing message")
    tracer.put_annotation(key="sqs_id", value=record.message_id)
    time.sleep(4)
    logger.debug("Finished processing message")

    try:
        # Validate "Message" key on input, otherwise return failure
        # Note: if input does not contain "Message" key, this will raise an error
        message = json.loads(record.body)["Message"]
        logger.info(f"Message: {message}")
        return True
    except:
        logger.exception("Failed to process message")
        raise


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> PartialItemFailureResponse:
    logger.info("Starting messages processing")
    tracer.put_metadata(key="details", value="messages processing handler")

    number_of_records = len(event.get("Records", []))
    logger.debug(f"Number of messages is: {number_of_records}")
    tracer.put_metadata(key="total_messages", value=number_of_records)

    batch_response = process_partial_response(
        event=event,
        record_handler=process_message,
        processor=processor,
        context=context
    )
    logger.info("Finished messages processing")

    return batch_response
