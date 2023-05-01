# Built-in imports
import os, sys
import json
import unittest

# External imports
from aws_lambda_powertools.utilities.data_classes import SQSEvent
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from moto import mock_sts

# Add path to find lambda directory for own imports
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Own imports
import src.lambda_function as _lambda  # noqa: E402


class TestLambdaFunction(unittest.TestCase):
    """
    TestCase for unit testing the inner Lambda Function functionalities.
    """

    def load_test_event(self, test_event_name: str) -> dict:
        """
        Load test event from given file.
        """
        path_to_event = os.path.join(
            os.path.dirname(__file__),
            test_event_name,
        )
        with open(path_to_event) as file:
            test_event = json.load(file)
        return test_event

    # The "mock_sts" decorator allows to "mock/fake" the sts API calls for tests
    @mock_sts()
    def test_process_messages_success_single(self):
        """
        Test successful process_messages call for a single message.
        """
        # Load pre-configured event for current test case
        event = self.load_test_event("test_event_01_good.json")

        # Middleware to load event with correct SQSEvent and SQSRecord data classes
        event_sqs = SQSEvent(event)
        sqs_record = SQSRecord(event_sqs.get("Records", [])[0])
        result = _lambda.process_message(sqs_record)

        self.assertEqual(result, True)

    @mock_sts()
    def test_process_messages_error(self):
        """
        Test errors on process_messages call due to wrong message format.
        """
        # Load pre-configured event for current test case
        event = self.load_test_event("test_event_02_bad.json")

        # Middleware to load event with correct SQSEvent and SQSRecord data classes
        event_sqs = SQSEvent(event)
        sqs_record = SQSRecord(event_sqs.get("Records", [])[0])

        # Expected an exception intentionally, otherwise fails
        with self.assertRaises(Exception):
            _lambda.process_message(sqs_record)


if __name__ == "__main__":
    unittest.main()
