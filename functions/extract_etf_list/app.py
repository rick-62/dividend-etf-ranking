import json
import os
from io import StringIO
from typing import Dict

import boto3
import pandas as pd

s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")

S3_BUCKET_INPUT = os.environ.get('INTERMEDIATE_BUCKET')
S3_KEY_INPUT = os.environ.get('FILEIN')
SQS_QUEUE = os.environ.get('QUEUE')


def lambda_handler(event, context):
    """extract filtered ETF ISINs from transformed Freetrade data"""

    # load data
    response = s3_client.get_object(Bucket=S3_BUCKET_INPUT, Key=S3_KEY_INPUT)
    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    ft = pd.read_csv(response.get("Body"))

    # filter for distributing ETFs only (which are isa_eligible)
    ft.query(f'ETF_flag and isa_eligible', inplace=True)
    ft = ft[~ft["description"].str.contains("ACC")]
    
    # process each filtered ETF and send to the SQS queue
    count = 0
    for isin in ft['Isin']:
        response = sqs_client.send_message(QueueUrl=SQS_QUEUE, MessageBody=isin)
        count += 1

    return {
        "statusCode": status,
        "body": json.dumps(
            {
                "message": f"{count} ETF ISINs sent to the queue.",
            }
        ),
    }
