# Customer Support Chatbot with Amazon Bedrock Flows

> An AI-powered customer support automation system built with **Amazon Bedrock Flows**, **Amazon Nova Pro**, **AWS Lambda**, and **Amazon DynamoDB**.

[![AWS](https://img.shields.io/badge/AWS-Amazon%20Bedrock-orange?logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Amazon DynamoDB](https://img.shields.io/badge/Database-DynamoDB-blue?logo=amazondynamodb)](https://aws.amazon.com/dynamodb/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Overview

The **Customer Support Chatbot** is a serverless AI support workflow implemented with **Amazon Bedrock Flows**.

The workflow classifies an incoming customer request into one of three mutually exclusive categories:

1. **BUG_REPORT** — collects/structures bug information and creates a support ticket.
2. **PLATFORM_QUESTION** — handles questions through the configured FAQ/support path.
3. **OTHER** — redirects unsupported or out-of-scope requests to human support.

The bug-report path combines LLM-based structured extraction with deterministic workflow execution:

```text
Customer Message
       |
       v
Intent Classifier
       |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
 BUG_REPORT          PLATFORM_QUESTION           OTHER
       |                      |                      |
       v                      v                      v
Bug Report Formatter       FAQ / Support       Human Support
       |
       v
AWS Lambda
       |
       v
Amazon DynamoDB
```

The project demonstrates an end-to-end cloud workflow in which the LLM performs language understanding/extraction while explicit Bedrock Flow conditions control routing and AWS services perform ticket creation and persistence.

---

## Problem Statement

Customer support requests frequently arrive as unstructured natural-language messages. Manual triage can require customers to provide the same information repeatedly and can make it difficult to separate actionable bug reports from general platform questions.

This project addresses those problems by:

- classifying incoming requests,
- extracting structured bug information,
- creating persistent bug tickets,
- answering supported platform questions through a configured FAQ,
- escalating unsupported questions to human support, and
- routing other requests away from the supported automation path.

---

## Architecture

### Core Components

| Component | Purpose |
|---|---|
| **Amazon Bedrock Flows** | Orchestrates the complete workflow |
| **Amazon Nova Pro** | Performs natural-language understanding/classification |
| **Classifier Node** | Determines the request category |
| **Condition Nodes** | Deterministically route the request |
| **Bug Report Formatter** | Converts bug-report information into structured JSON |
| **AWS Lambda** | Creates the bug-report ticket |
| **Amazon DynamoDB** | Persists bug-report records |
| **Flow Version** | Provides an immutable deployment snapshot |
| **Flow Alias** | Provides the stable deployment target |

Amazon Bedrock Flow versions are immutable snapshots, and an alias can point to a selected version for invocation. This is the documented Bedrock deployment model for Flows. citehttps://docs.aws.amazon.com/bedrock/latest/userguide/flows-deploy.html

### Routing Model

The classifier produces one of:

```text
BUG_REPORT
PLATFORM_QUESTION
OTHER
```

The explicit Flow conditions then determine which workflow path executes.

---

# Workflow

## 1. Customer Message

The system receives an unstructured customer message, for example:

```text
My application crashes whenever I click the Login button.
```

## 2. Intent Classification

The classifier determines whether the request is:

- `BUG_REPORT`
- `PLATFORM_QUESTION`
- `OTHER`

The classifier is responsible for intent classification; the Flow condition nodes perform the deterministic routing.

## 3. Bug Report Path

Bug reports are processed by the Bug Report Formatter.

The formatter produces a predictable JSON structure:

```json
{
  "description": "The application crashes whenever I click the Login button.",
  "stepsToReproduce": "Click the Login button.",
  "environment": "Windows 11, Chrome"
}
```

The formatter follows these principles:

- extract only information provided by the customer,
- do not invent missing information,
- represent missing optional information with empty strings,
- return valid JSON, and
- preserve the reported issue.

The structured result is then passed to the Lambda ticket-creation path.

## 4. Lambda Ticket Creation

The AWS Lambda function creates the support ticket from the structured bug-report information.

The deployed function used by this project is:

```text
create-bug-report-1c16e0e0
```

The Lambda returns a ticket identifier and status after successful creation.

Example:

```json
{
  "ticketId": "generated-ticket-id",
  "status": "OPEN",
  "message": "Bug report created successfully"
}
```

## 5. DynamoDB Persistence

Bug reports are persisted in:

```text
bug-report-tool-stack-bug-reports
```

A ticket record contains fields such as:

```json
{
  "ticketId": "generated-ticket-id",
  "description": "The application crashes when Login is clicked.",
  "stepsToReproduce": "Open the login page and click Login.",
  "environment": "Windows 11, Chrome",
  "status": "OPEN",
  "createdAt": "UTC timestamp"
}
```

This gives the support workflow a persistent, trackable ticket identifier.

## 6. Platform Questions

A platform question follows the configured FAQ/support path.

For a covered question, the chatbot returns the corresponding supported FAQ answer rather than creating a bug ticket.

For an uncovered platform question, the chatbot redirects the customer to human support instead of inventing unsupported information.

## 7. Other Requests

Requests outside the supported customer-support categories are routed to the `OTHER` path and redirected to human support.

---

# Bug Report Formatter

The formatter uses the following structured-output contract:

```text
Extract the bug report information from the customer's message below.

Customer message:
{{customer_message}}

Return ONLY valid JSON in exactly this format:
{
  "description": "string",
  "stepsToReproduce": "string",
  "environment": "string"
}

Rules:
- Extract only information actually provided by the customer.
- Do not invent missing information.
- If information is missing, use an empty string.
- Return valid JSON only.
```

This contract keeps the interface between LLM-based extraction and deterministic ticket creation predictable.

---

# Lambda Interface

The Lambda ticket-creation path uses these bug-report fields:

| Parameter | Description | Required |
|---|---|---|
| `description` | Description of the reported bug | Yes |
| `stepsToReproduce` | Reproduction steps supplied by the customer | No |
| `environment` | Environment/device/context supplied by the customer | No |

The repository contains the Lambda implementation under:

```text
lambda/index.py
```

Dependency declaration:

```text
lambda/requirements.txt
```

---

# Data Model

The DynamoDB ticket structure used by the workflow is:

| Attribute | Description |
|---|---|
| `ticketId` | Unique support-ticket identifier |
| `description` | Customer's bug description |
| `stepsToReproduce` | Reproduction steps |
| `environment` | Reported environment |
| `status` | Ticket status |
| `createdAt` | UTC creation timestamp |

Example:

```json
{
  "ticketId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "description": "Checkout crashes when clicking Pay Now.",
  "stepsToReproduce": "Open checkout and click Pay Now.",
  "environment": "Web browser",
  "status": "OPEN",
  "createdAt": "UTC timestamp"
}
```

---

# Testing and Validation

The implementation was tested across the required routing and execution paths.

| Test Scenario | Expected Behavior |
|---|---|
| Complete bug report | Bug Report → Formatter → Lambda → DynamoDB |
| Incomplete bug report | Collect/structure available information without inventing missing data |
| Covered platform question | FAQ/support response |
| Uncovered platform question | Human-support handoff |
| Other/out-of-scope request | Human-support handoff |

### Bug Report Test

Example:

```text
My application crashes whenever I click the Login button.
```

The conversation collects the required bug-report information and the completed workflow creates a ticket.

### Covered Platform Question

Example:

```text
How do I reset my password?
```

The request follows the platform-question path and uses the configured FAQ response.

### Uncovered Platform Question

An unsupported platform question is routed to human support rather than answered with invented information.

### Other Request

An out-of-scope request is routed to the `OTHER` path and handed to human support.

Detailed test cases and evaluation artifacts are stored under:

```text
evaluation/
```

---

# Evaluation

The project includes an Amazon Bedrock **LLM-as-a-judge** evaluation using the completed chatbot responses.

The evaluation uses the built-in:

```text
Builtin.Correctness
```

metric.

Amazon Bedrock's judge-based evaluation can score supplied model responses, and the `Builtin.Correctness` metric measures whether a response is correct. citehttps://docs.aws.amazon.com/bedrock/latest/userguide/model-evaluation-metrics.html

The custom evaluation dataset is stored as JSONL in Amazon S3, as required for Bedrock LLM-as-a-judge evaluation datasets. citehttps://docs.aws.amazon.com/bedrock/latest/userguide/model-evaluation-prompt-datasets-judge.html

Repository evaluation artifacts:

```text
evaluation/
├── test-cases.json
├── output_eval_dataset.jsonl
└── evaluation-observations.md
```

The evaluation screenshots are stored under:

```text
screenshots/
```

The evaluation observations document the actual results and findings from the completed evaluation.

---

# Deployment

The Flow uses Amazon Bedrock's version-and-alias deployment model.

Deployment lifecycle:

```text
Working Draft
     |
     v
Publish Version
     |
     v
Immutable Flow Version
     |
     v
Flow Alias
     |
     v
Application / Flow Invocation
```

Amazon Bedrock documents versions as immutable snapshots of a Flow. An alias can then point to the version intended for invocation. citehttps://docs.aws.amazon.com/bedrock/latest/userguide/flows-deploy.html

Deployment region:

```text
us-east-1
```

The repository does not publish AWS account credentials, access keys, session tokens, or other secrets.

---

# Repository Structure

```text
customer-support-chatbot/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── lambda/
│   ├── index.py
│   ├── requirements.txt
│   └── README.md
│
├── flow/
│   ├── classifier-prompt.txt
│   ├── bug-report-formatter-prompt.txt
│   └── flow-configuration.md
│
├── architecture/
│   └── architecture.md
│
├── evaluation/
│   ├── test-cases.json
│   ├── output_eval_dataset.jsonl
│   └── evaluation-observations.md
│
├── tests/
│   ├── bug-report-test.md
│   ├── platform-question-test.md
│   ├── unsupported-question-test.md
│   └── out-of-scope-test.md
│
├── screenshots/
│   ├── Condition Routing.png
│   ├── Flow Architecture.png
│   ├── Lambda Configuration.png
│   ├── Message Classifier.png
│   ├── bug-formatter.png
│   ├── dynamodb-chatbot-item.png
│   ├── dynamodb-record.png
│   ├── successful-flow-test.png
│   ├── version-and-alias.png
│   ├── bug-report-conversation.png
│   ├── covered-faq.png
│   ├── uncovered-faq.png
│   ├── out-of-scope.png
│   ├── evaluation-job.png
│   └── evaluation-results.png
│
└── docs/
    ├── project-overview.md
    ├── deployment.md
    └── testing.md
```

If a file listed above is not part of the submitted repository, remove it from this documentation rather than leaving a fictional path.

---

# Technology Stack

### Cloud & AI

- Amazon Bedrock
- Amazon Bedrock Flows
- Amazon Nova Pro
- AWS Lambda
- Amazon DynamoDB
- Amazon S3 for evaluation artifacts

### Programming

- Python 3.12
- JSON
- AWS SDK for Python (`boto3`)

### Development & Deployment

- AWS Management Console
- AWS CLI
- Git
- GitHub

---

# Requirements

Before deploying or reproducing the project, ensure that you have:

- An AWS account
- Access to Amazon Bedrock
- Access to the required Bedrock model
- Permissions to create and use Bedrock Flows
- Lambda permissions
- DynamoDB permissions
- Amazon S3 permissions for evaluation artifacts
- AWS CLI configured
- Python 3.12
- `boto3`

Required IAM permissions depend on the deployment environment and should be granted according to least-privilege requirements.

---

# Configuration

The Lambda function uses the following environment variable to identify the DynamoDB table:

```text
TABLE_NAME=<your-dynamodb-table>
```

For the deployed project, the table is:

```text
bug-report-tool-stack-bug-reports
```

The table name should be configured through the Lambda environment rather than hardcoded into application logic.

---

# Local Lambda Development

Install the declared dependency:

```bash
pip install -r lambda/requirements.txt
```

The Lambda handler is:

```text
index.lambda_handler
```

The deployed Lambda runtime is:

```text
Python 3.12
```

---

# Security

Never commit AWS credentials or other sensitive information to the repository.

Do not commit:

```text
AWS access keys
AWS secret keys
AWS session tokens
.env files containing secrets
.aws credential/configuration files
private authentication tokens
```

Use AWS IAM and local AWS credential configuration instead of hardcoding credentials into source code.

---

# Evidence

The `screenshots/` directory contains evidence for the implemented and tested workflow.

The evidence set covers:

1. Flow architecture
2. Message classification
3. Conditional routing
4. Bug-report formatting
5. Flow-to-Lambda configuration
6. DynamoDB persistence
7. Successful Flow execution
8. Published version and alias
9. End-to-end bug-report conversation
10. Covered FAQ behavior
11. Uncovered platform-question handoff
12. Other-request handoff
13. Evaluation job configuration
14. Evaluation results

The repository also contains the evaluation dataset and written observations required to reproduce and inspect the evaluation process.

---

# Design Principles

### 1. Separation of Concerns

The implementation separates:

- intent classification,
- information extraction,
- ticket creation,
- persistence, and
- support escalation.

### 2. Structured Data Contracts

The Bug Report Formatter produces a predictable JSON structure before downstream ticket creation.

### 3. Deterministic Routing

The LLM determines the intent category, while explicit Bedrock Flow conditions control the workflow path.

### 4. Serverless Architecture

Lambda and DynamoDB provide the ticket-creation and persistence layer without requiring traditional application servers.

### 5. No Fabricated Bug Information

The formatter is instructed to extract only information provided by the customer and represent missing optional fields as empty strings.

### 6. Immutable Deployment

The deployed Flow uses a published version through an alias rather than relying on a continuously changing draft.

---

# Observability and Debugging

The workflow can be validated layer by layer:

```text
Customer Input
      ↓
Classifier Output
      ↓
Routing Decision
      ↓
Formatter Output
      ↓
Lambda Invocation
      ↓
Lambda Response
      ↓
DynamoDB Record
```

This layered structure makes it possible to identify whether a problem originates in classification, routing, extraction, Lambda execution, or persistence.

---

# Future Improvements

Potential production enhancements include:

- Authentication and authorization
- Conversation history
- Ticket-status lookup
- Ticket updates and closing workflows
- Human-agent dashboard
- CloudWatch monitoring and alarms
- Retry and error-handling strategies
- Input validation and abuse protection
- Confidence-aware classification
- Guardrails for unsafe or inappropriate requests
- Automated regression testing
- CI/CD deployment
- Infrastructure as Code
- Multi-language support
- CRM/help-desk integration

These are **future improvements**, not claims about functionality currently implemented in this submission.

---

# Project Outcomes

This project demonstrates practical implementation of:

- Generative AI workflow orchestration
- Amazon Bedrock Flows
- LLM-based intent classification
- Structured information extraction
- Conditional workflow routing
- AWS Lambda integration
- DynamoDB persistence
- JSON-based data contracts
- End-to-end cloud application testing
- Bedrock LLM-as-a-judge evaluation
- Immutable Flow deployment using versions and aliases

The implementation combines **LLM reasoning with deterministic cloud workflow orchestration and persistent backend state**.

---

# License

This project is licensed under the **Apache License 2.0**.

See the [`LICENSE`](LICENSE) file for the complete license text.

---

# Author

**Ahmad Saleem**

Computer Science Student | AI/ML & Generative AI Enthusiast

Interested in:

- Artificial Intelligence
- Machine Learning
- Generative AI
- LLM Applications
- Cloud Computing
- Intelligent Automation

---

# Acknowledgements

Built using services and technologies provided by **Amazon Web Services**, including Amazon Bedrock, AWS Lambda, Amazon DynamoDB, and Amazon S3.

---

**Built with Python, AWS, Amazon Bedrock, and a focus on practical AI engineering.**
