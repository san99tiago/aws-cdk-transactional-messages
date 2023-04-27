# Built-in imports
import os, sys
import json
import unittest

# External imports
from aws_lambda_powertools.utilities.data_classes import event_source, SQSEvent
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
        event = self.load_test_event("test_event_01_good_single.json")

        # Middleware to load event with correct SQSEvent data class
        event_sqs = SQSEvent(event)
        result = _lambda.process_messages(event_sqs)

        self.assertEqual(result, True)

    @mock_sts()
    def test_process_messages_success_multiple(self):
        """
        Test successful process_messages call for multiple messages.
        """
        # Load pre-configured event for current test case
        event = self.load_test_event("test_event_02_good_multiple.json")

        # Middleware to load event with correct SQSEvent data class
        event_sqs = SQSEvent(event)
        result = _lambda.process_messages(event_sqs)

        self.assertEqual(result, True)

    @mock_sts()
    def test_process_messages_error(self):
        """
        Test errors on process_messages call due to wrong message format.
        """
        # Load pre-configured event for current test case
        event = self.load_test_event("test_event_03_bad.json")

        # Middleware to load event with correct SQSEvent data class
        event_sqs = SQSEvent(event)

        # Expected an exception intentionally, otherwise fails
        with self.assertRaises(Exception):
            _lambda.process_messages(event_sqs)


if __name__ == "__main__":
    unittest.main()
