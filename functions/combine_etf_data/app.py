import json
import os
import pickle
from io import StringIO

import boto3
import pandas as pd

s3_client = boto3.client("s3")
s3_resource = boto3.resource('s3')

S3_BUCKET_IN = os.environ.get('INTERMEDIATE_BUCKET')
S3_FOLDER_IN = os.environ.get('FOLDER_IN')
S3_FILE_IN = os.environ.get('FILEIN')

S3_BUCKET_OUT = os.environ.get('PRIMARY_BUCKET')
S3_FILE_OUT = os.environ.get('FILEOUT')


def lambda_handler(event, context):

    # Create s3 resource just for extracting list of objects
    bucket = s3_resource.Bucket(S3_BUCKET_IN)

    # Extract list of files in source folder
    obj_paths = [
        obj.key for obj in bucket.objects.filter(Prefix=f"{S3_FOLDER_IN}") 
        if obj.key.endswith('pkl')
    ]

    # Download the pickled data from S3 and combine into a dict 
    combined_dict = {}
    for obj_path in obj_paths:
        response = s3_client.get_object(Bucket=S3_BUCKET_IN, Key=obj_path)
        file = response.get("Body")
        data = pickle.loads(file.read())
        isin = os.path.basename(obj_path).split('.')[0]
        combined_dict[isin] = data

    # Combine into one dataframe
    etf_summary = (
        pd.DataFrame.from_dict(combined_dict, orient='index', dtype='float')
        .assign(ISIN = lambda x: x.index)
        .assign(expense_ratio = lambda x: x['expense_ratio'].str[:-1].astype(float))
        .assign(date_latest_quote = lambda x: pd.to_datetime(x['date_latest_quote'], format="%d/%m/%Y", exact=False))
        .eval('dividend_yield = 100 * one_year_dividend / latest_quote')
        .eval('net_yield = dividend_yield - expense_ratio')
    )
    
    # load freetrade data
    freetrade = pd.read_csv(
        s3_client
        .get_object(Bucket=S3_BUCKET_IN, Key=S3_FILE_IN)
        .get("Body")
    )

    # combine scraped data with initial freetrade list
    etf_summary2 = (
        freetrade[['isin','title', 'long_title', 'subtitle', 'symbol']]
        .set_index('isin')
        .join(etf_summary[['latest_quote', 'net_yield', 'dividend_yield', 'expense_ratio']])
        .dropna()
        .sort_values('net_yield', ascending=False)
    )

    # save the results to S3 bucket (as a CSV)
    out_buffer = StringIO()
    etf_summary2.to_csv(out_buffer, index=False)
    s3_client.put_object(Bucket=S3_BUCKET_OUT, Key=S3_FILE_OUT, Body=out_buffer.getvalue())
    

    return {
        "body": json.dumps(
            {
                "message": f"{len(obj_paths)}",
            }
        ),
    }


