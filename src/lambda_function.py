# Simple lambda to "simulate" the processing of the messages

import time
import json


def handler(event, context):
    for record in event["Records"]:
        payload = record["body"]
        print(payload)

        # Simulate a "time" processing delay
        time.sleep(5)

        # Validate "Message" key on input, otherwise return failure
        # Note: if input does not contain "Message" key, this will raise an error
        message = json.loads(payload)["Message"]
        print("Message: {}".format(message))

    # Return success if all messages were processed correctly
    return {
        "statusCode": 200,
        "body": json.dumps({
            "Region ": "Successfully processed message"
        }),
    }
