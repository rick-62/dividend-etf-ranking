import json
import boto3
import os
import pickle

s3_client = boto3.client("s3")
s3_resource = boto3.resource('s3')

S3_BUCKET_IN = os.environ.get('INTERMEDIATE_BUCKET')
S3_FOLDER_IN = os.environ.get('FOLDER_IN')

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
        print(isin)

    # Combine into one dataframe

    

    # save the results to S3 bucket (as a CSV)
    



    return {
        "body": json.dumps(
            {
                "message": f"{len(obj_paths)}",
            }
        ),
    }


