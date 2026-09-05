# System Architecture

## Overview

The Customer Support Chatbot is implemented using Amazon Bedrock Flows and
routes customer requests into three mutually exclusive categories:

1. Bug Report
2. Platform Question
3. Other / Unsupported Request

## Request Flow

User Input
    ↓
Classifier
    ↓
Condition Router
    ├── BUG_REPORT
    │       ↓
    │   Bug Report Formatter
    │       ↓
    │   AWS Lambda
    │       ↓
    │   Amazon DynamoDB
    │
    ├── PLATFORM_QUESTION
    │       ↓
    │   FAQ
    │       ↓
    │   Answer / Human Support
    │
    └── OTHER
            ↓
        Human Support

## Bug Report Path

The bug-report branch extracts:

- Description
- Steps to reproduce
- Environment

The structured bug report is passed to the Lambda function.

The Lambda function creates a ticket and stores the bug report in
Amazon DynamoDB.

## Platform Question Path

Platform questions are checked against the configured FAQ.

If the question is covered by the FAQ, the chatbot returns the supported
answer without inventing information.

If the question is not covered, the chatbot redirects the customer to
human support.

## Other Requests

Requests outside the supported customer-support scope are redirected to
human support.

## AWS Services

- Amazon Bedrock Flows
- Amazon Bedrock model inference
- AWS Lambda
- Amazon DynamoDB
- Amazon S3
- Amazon Bedrock Model Evaluation
