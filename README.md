# dividend-etf-ranking

This project contains source code and supporting files for a serverless pipeline application which automatically extracts and combines Dividend ETF data on a weekly schedule. It includes the following files and folders.

- functions - Code for the application's Lambda functions and Project Dockerfiles.
- events - not used.
- tests - not yet implemented. 
- template.yaml - A template that defines the application's AWS resources.

The application uses several AWS resources:
 - Lambda
 - S3
 - SQS
 
These resources are defined in the `template.yaml` file in this project.

## Deploy the application

Included in the project is a Github actions pipeline yaml, which will deploy a deployment test and production stack to AWS. This will be triggered automatically when the application is pushed to the main branch. All that is required is AWS credentials which must be manually updated in the Github repo.

## Additional Setup
Currently function to download the initial data required as part of the application has not been implemented and must be done manually for time being.

1. The Freetrade stocks list is required, which can be downloaded from this [Google Sheet](https://docs.google.com/spreadsheets/d/14Ep-CmoqWxrMU8HshxthRcdRW8IsXvh3n2-ZHVCzqzQ/edit#gid=1855920257) . 
2. It must be saved as a CSV and renamed *freetrade_stocks.csv*.
3. Provided the application has been deployed, this must then be uploaded to the *dividend-etf-ranking-prod-raw-data* & *dividend-etf-ranking-dev-raw-data* S3 buckets

## Pipeline
1. Once the Freetrade stock list has been uploaded to the S3 bucket, this will trigger transformation of this data which will output CSV into the *intermediate-data* S3 bucket
2. Every Sunday at 6am the main process will begin, first by extracting a list of ETF ISINs from the transformed Freetrade data, and then adding these to a SQS queue
3. In turn, this will trigger another Lambda to scrape the required data for each of these ISINs and saves the outputs into the *intermediate-data* bucket, until the queue is empty
4. Once complete one final Lambda will combine all the data into the desired summary table and output to the *primary-data* bucket

## Things to improve/add
- Local testing was achievable using the SAM CLI and Docker, but it was cumbersome and could take a while to deploy for individual Lambdas. However, it was very useful. Docker would only redeploy image if function had changed since last time, which could be good for changing environment variables but most of the time I found myself having to wait for a full redeploy. I would need to look into improving this, for quicker, iterative development. I think I can do this by spooling up local API, which I did get working with the original Hello World example. Also I was unable to easily test changes to the SAM template and found myself fully re-deploying to AWS every time to test whether the changes I had made worked.
- I had good intentions of setting up thorough unit and integration testing when I began this, but since I was lifting and shifting an existing project and was new to developing the serverless application, this slipped. Most of the Lambda function testing was more for testing whether I had correctly referenced S3 bucket etc and would have benefited little from unit testing at the time. I relied more heavily on debugging individual Lambda functions manually. Unit and integration testing are not included in the deployment pipeline.
- Another aspect I didn't get much chance to improve was Cloudwatch for logging and monitoring. There are aspects of this application that would benefit from monitoring especially so I can track which ETFs data could not be collected for. When the SQS triggers the Lambda to scrape data, if the Lambda fails for whatever reason this is not obvious and does not create an alarm or provide any tailored information.
- The SQS queue was possibly overkill, especially as I didn't even batch. I did consider using Step Function which includes the ability to run Lambdas in a loop. However, the free tier for Step Functions only provides 4,000 invocations per month which I thought might be too low. In Hindsight Step Functions would have made the whole process a lot simpler. 
- I decided to save the data into buckets, but did consider DynamoDB tables. I think this would have simplified things. Saving/reading from S3 buckets from Lambdas was a pain. So much additional code required. Also, the final function to combine all the data is triggered on a CRON which occurs an hour after entire process has started. I couldn't figure out an easy way to trigger once the SQS queue was empty. I did have it trigger every time the S3 bucket was updated with new scraped data. I soon realised there was a free limit on S3 access invocations of 20,000. I thought this was a lot, but considering there are about 200 ETFs this caused the Lambda to repeatedly trigger and read in 200 files, so approximately 200 x 200 times = 40,000. 
- For future, more complex Data Science applications, I will consider a hybrid of deploying pipeline to triggered EC2 instance (or run/test locally), using Serverless for more specialised processes, such as web scraping, scheduling and API interactions.

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name dividend-etf-ranking
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
