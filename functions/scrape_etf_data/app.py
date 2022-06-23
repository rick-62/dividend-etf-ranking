import json

def lambda_handler(event, context):

    for record in event['Records']:
        print("test")
        payload = record["body"]
        print(str(payload))

    return {
        "body": json.dumps(
            {
                "message": f"contents: {payload}",
            }
        ),
    }
