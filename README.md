# Qlik AWS Cost Explorer Report Generator

## License Summary

This project is made available under a modified MIT license. See the LICENSE file.

## Purpose

The purpose of this script is use the [AWS Cost Explorer API] <https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html> GetCostAndUsage endpoint to retrieve cost data about one (or more) AWS accounts.

Based on a configuration file, this script will generate csv files that can be ingested by BI tools like Qlik Sense. We provide a qvf that is a template for that data consumption.

![image info](./img/highlevel.png)

This project was inspired by this [AWS sample]<https://github.com/aws-samples/aws-cost-explorer-report>

## Usage Options

There are several options to run this script.
One option is use this script as a standalone program to be executed in one server or machine with access to a S3 bucket.
This script may be deployed as a AWS Lambda function. Using this serveless approach is possible because the footprint to execute the script is really tiny (128Mb for small AWS accounts) increasing accordingly to how many records you retrieve from the API. For example, daily detailed extractions consummes more memory than monthly ones.

## Prerequesites

1. An AWS access key pair for IAM user (<https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html>)
2. An S3 bucket to store the final csv result. If this is not present, the file will be stored into the TEMP directory
3. Python 3.10
4. Pandas 1.4.2 (<https://pandas.pydata.org/pandas-docs/stable/>)
5. Boto 3 (<https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>)

## Using Lambda function to execute

One efficient way of executing this script is using AWS Lambda servless archictecture that allows the execution with  a tiny footprint.
Please refer to [this documentation]<https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html> about how to create a lambda function

One important mention is that we are using one layer provided by this project <https://github.com/aws-samples/aws-cost-explorer-report>

## AWS Costs

There are costs involved in data extraction from Cost Explorer API:

* Cost Explorer API calls
  * [$0.01 per API call (about 25 calls per run)](https://aws.amazon.com/aws-cost-management/pricing/)
* AWS Lambda Invocation (if you choose this option)
  * Usually [Free](https://aws.amazon.com/free/)  
* Amazon S3
  * Minimal usage
