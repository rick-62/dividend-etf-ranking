import json
import os
from io import StringIO
from typing import Dict

import boto3
import pandas as pd

s3_client = boto3.client("s3")
# S3_BUCKET_NAME = 'dividend-etf-ranking-dev-raw-data'
S3_BUCKET_NAME = os.environ.get('MY_BUCKET')

freetrade_mic_remap = {
  'XLON': 'London',
  'XNYS': 'NYSE',
  'XNAS': 'NASDAQ',
}

def lambda_handler(event, context):
    """transform Freetrade data"""
    # ft: pd.DataFrame, params: Dict
    
    # load data
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key="freetrade_stocks.csv")
    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    ft = pd.read_csv(response.get("Body"))

    # cleanse columns
    ft.columns = ft.columns.str.lower()
    ft.fractional_enabled.fillna(False, inplace=True)
    ft.symbol = ft.symbol.str.replace(".", "", regex=True)
    ft.currency = ft.currency.str.upper()

    # convert mic to exchange e.g. XLON: London (for joining to investpy)
    ft["stock_exchange"] = [freetrade_mic_remap.get(x) for x in ft.mic]

    # create description column for later searching/filtering
    ft["description"] = (ft.title + " " + ft.long_title + " " + ft.subtitle).str.upper()

    # flag ETF stock
    ft["ETF_flag"] = ft["description"].str.contains(" ETF")

    # apply index
    ft.set_index('isin', inplace=True)

    # save output to S3 bucket
    out_buffer = StringIO()
    ft.to_csv(out_buffer, index=False)
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key="freetrade_transformed.csv", Body=out_buffer.getvalue())

    return {
        "statusCode": status,
        "body": json.dumps(
            {
                "message": f"final data size is: {ft.size}",
            }
        ),
    }
