# Customer Support Chatbot with Amazon Bedrock Flows

> An intelligent, production-oriented customer support automation system built with **Amazon Bedrock Flows**, **Amazon Nova Pro**, **AWS Lambda**, and **Amazon DynamoDB**.

[![AWS](https://img.shields.io/badge/AWS-Amazon%20Bedrock-orange?logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Amazon DynamoDB](https://img.shields.io/badge/Database-DynamoDB-blue?logo=amazondynamodb)](https://aws.amazon.com/dynamodb/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Overview

The **Customer Support Chatbot** is an event-driven AI support system that automatically understands incoming customer messages, classifies their intent, and routes each request to the appropriate workflow.

Instead of treating every customer message identically, the system uses an **Amazon Bedrock Flow** to orchestrate specialized paths:

1. **Bug Report** → extracts structured information → invokes an AWS Lambda function → creates a persistent support ticket in DynamoDB.
2. **Platform Question** → routes the request to the FAQ/support response path.
3. **Other Request** → redirects the customer toward human support.

The architecture combines **LLM-based reasoning with deterministic workflow routing and serverless persistence**, providing a foundation for scalable customer-support automation.

---

## 🎯 Problem Statement

Traditional support systems often require customers to manually identify their issue, provide structured information, and wait for a support representative.

This creates several problems:

* Unstructured customer messages
* Repetitive manual triage
* Inconsistent bug-report information
* Slow ticket creation
* Difficulty separating actionable bugs from general questions
* Lack of structured persistence for reported issues

This project addresses these problems by automatically interpreting incoming messages and routing them through specialized workflows.

---

## 💡 Solution

The system introduces an AI-powered routing layer using **Amazon Bedrock Flows**.

A customer message is first classified according to its intent.

```text
                         ┌─────────────────────┐
                         │   Customer Message  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Intent Classifier │
                         │  Amazon Bedrock LLM │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌───────────────┐      ┌─────────────┐
       │ Bug Report  │       │    Platform   │      │    Other    │
       │    Path     │       │    Question   │      │   Request   │
       └──────┬──────┘       └───────┬───────┘      └──────┬──────┘
              │                      │                     │
              ▼                      ▼                     ▼
       ┌─────────────┐        ┌───────────────┐     ┌──────────────┐
       │ Bug Report  │        │ FAQ / Support │     │    Human     │
       │  Formatter  │        │    Response   │     │   Support    │
       └──────┬──────┘        └───────────────┘     │  Redirect    │
              │                                     └──────────────┘
              ▼
       ┌─────────────┐
       │ AWS Lambda  │
       │ create_bug_ │
       │    report   │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │   Amazon    │
       │  DynamoDB   │
       └─────────────┘
```

---

# 🏗️ Architecture

## Core Components

| Component                | Purpose                                                    |
| ------------------------ | ---------------------------------------------------------- |
| **Amazon Bedrock Flows** | Orchestrates the complete AI workflow                      |
| **Amazon Nova Pro**      | Performs natural-language understanding and classification |
| **Classifier Node**      | Determines the customer's request category                 |
| **Condition Nodes**      | Deterministically route the request                        |
| **Bug Report Formatter** | Converts unstructured bug reports into structured JSON     |
| **AWS Lambda**           | Validates and creates bug-report tickets                   |
| **Amazon DynamoDB**      | Persists bug-report records                                |
| **Flow Version**         | Provides an immutable deployment snapshot                  |
| **Flow Alias**           | Provides the stable deployment target                      |

Amazon Bedrock Flow versions are immutable snapshots, while aliases can point to a selected version for application invocation.

---

# 🔄 Workflow

## 1. Customer Message

The system receives an unstructured customer message such as:

> "The checkout page crashes whenever I click Pay Now."

---

## 2. Intent Classification

The message is analyzed by the classifier and assigned to one of the supported categories:

```text
BUG_REPORT
PLATFORM_QUESTION
OTHER
```

The classifier is responsible only for determining the appropriate route.

---

## 3. Bug Report Path

Bug reports are passed to a dedicated formatter.

The formatter extracts:

```json
{
  "description": "The checkout page crashes when Pay Now is clicked.",
  "stepsToReproduce": "Open checkout and click Pay Now.",
  "environment": ""
}
```

### Extraction principles

The formatter follows strict rules:

* Extract only information provided by the customer.
* Do not invent missing information.
* Represent missing fields using empty strings.
* Return valid JSON only.
* Preserve the customer's reported issue.

This separates **LLM-based extraction** from the deterministic ticket-creation logic.

---

## 4. Lambda Ticket Creation

The structured bug report is passed to the AWS Lambda function.

The Lambda function:

1. Receives the structured parameters.
2. Validates the required description.
3. Generates a unique ticket ID.
4. Assigns an `OPEN` status.
5. Generates a UTC timestamp.
6. Stores the ticket in DynamoDB.
7. Returns the created ticket information.

Example response:

```json
{
  "ticketId": "generated-ticket-id",
  "status": "OPEN",
  "message": "Bug report created successfully"
}
```

---

## 5. DynamoDB Persistence

Successfully created tickets are stored in Amazon DynamoDB.

A typical record contains:

```json
{
  "ticketId": "generated-ticket-id",
  "description": "The checkout page crashes when Pay Now is clicked.",
  "stepsToReproduce": "Open checkout and click Pay Now.",
  "environment": "",
  "status": "OPEN",
  "createdAt": "UTC timestamp"
}
```

This provides persistent storage for support tickets and allows the workflow to return a trackable ticket identifier to the customer.

---

# 🧠 Bug Report Formatter

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

The strict schema makes the downstream Lambda interface predictable and reduces the risk of malformed data.

---

# 🧩 Lambda Interface

The Lambda function expects the Bedrock function-style request structure and supports the following parameters:

| Parameter          | Description                                         | Required |
| ------------------ | --------------------------------------------------- | -------- |
| `description`      | Description of the reported bug                     | Yes      |
| `stepsToReproduce` | Steps supplied by the customer                      | No       |
| `environment`      | Environment/device/context supplied by the customer | No       |

The Lambda rejects requests without a valid bug description and persists valid reports in DynamoDB.

---

# 🗄️ Data Model

The DynamoDB ticket structure is:

| Attribute          | Description                              |
| ------------------ | ---------------------------------------- |
| `ticketId`         | Unique identifier for the support ticket |
| `description`      | Customer's bug description               |
| `stepsToReproduce` | Reproduction steps                       |
| `environment`      | Reported environment                     |
| `status`           | Ticket lifecycle state                   |
| `createdAt`        | UTC creation timestamp                   |

### Example

```json
{
  "ticketId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "description": "Checkout crashes when clicking Pay Now.",
  "stepsToReproduce": "Open checkout and click Pay Now.",
  "environment": "Web browser",
  "status": "OPEN",
  "createdAt": "2026-09-05T00:00:00+00:00"
}
```

---

# 🧪 Testing & Validation

The system was validated using multiple representative scenarios.

| # | Test Case                  | Expected Path                  | Result   |
| - | -------------------------- | ------------------------------ | -------- |
| 1 | Complete bug report        | Bug Report → Lambda → DynamoDB | ✅ Passed |
| 2 | Incomplete bug report      | Bug Report → Lambda → DynamoDB | ✅ Passed |
| 3 | Platform question          | FAQ / Platform Question        | ✅ Passed |
| 4 | General/other request      | Human Support                  | ✅ Passed |
| 5 | Realistic checkout failure | Bug Report → Lambda → DynamoDB | ✅ Passed |

## Example Test Cases

### Test 1 — Complete Bug Report

**Input**

```text
The checkout page crashes when I click Pay Now.
Steps: Open checkout, add an item, and click Pay Now.
Environment: Chrome on Windows.
```

**Expected behavior**

```text
Bug Report
    ↓
Formatter
    ↓
Lambda
    ↓
DynamoDB
```

**Result:** ✅ Ticket successfully created and persisted.

---

### Test 2 — Missing Optional Information

**Input**

```text
The checkout page crashes whenever I click Pay Now.
```

The formatter should not invent reproduction steps or environment information.

Expected structure:

```json
{
  "description": "The checkout page crashes whenever I click Pay Now.",
  "stepsToReproduce": "",
  "environment": ""
}
```

**Result:** ✅ Ticket successfully created with missing optional fields represented by empty strings.

---

### Test 3 — Platform Question

**Input**

```text
How do I reset my password?
```

**Expected path**

```text
Classifier
    ↓
Platform Question
    ↓
FAQ / Support Response
```

**Result:** ✅ Correctly routed without creating a bug ticket.

---

### Test 4 — Other Request

**Input**

```text
Can you recommend a good laptop for programming?
```

**Expected path**

```text
Classifier
    ↓
Other
    ↓
Human Support Redirect
```

**Result:** ✅ Correctly routed to the other-request path.

---

### Test 5 — Realistic Production-Style Bug

**Input**

```text
The checkout page crashes whenever I click the Pay Now button.
```

**Expected path**

```text
Classifier
    ↓
Bug Report
    ↓
Bug Report Formatter
    ↓
Create Bug Report Lambda
    ↓
DynamoDB
```

**Result:** ✅ Ticket created successfully and persisted in DynamoDB.

---

# 🔐 Security Considerations

This repository should **never contain AWS credentials or sensitive account information**.

Do not commit:

```text
AWS access keys
AWS secret keys
AWS session tokens
.env files
local credential files
temporary authentication tokens
private configuration
```

Use AWS IAM permissions and local AWS credential configuration instead of hardcoding credentials into source code.

The repository's `.gitignore` should prevent common local and secret-bearing files from being committed.

---

# 🚀 Deployment

The project uses Amazon Bedrock Flow deployment semantics.

The deployment lifecycle is:

```text
DRAFT
  ↓
Publish Version
  ↓
VERSION 1
  ↓
Alias
  ↓
Application / InvokeFlow
```

Amazon Bedrock creates immutable versions of a flow. An alias can then point to the version intended for application use.

### Deployment Configuration

Replace the placeholders below with your public deployment metadata if you want to expose it:

```text
AWS Region: us-east-1
Flow Version: <PUBLISHED_VERSION>
Flow Alias: <DEPLOYMENT_ALIAS>
```

Do **not** publish AWS account IDs, IAM credentials, access keys, or other sensitive identifiers.

---

# 📁 Recommended Repository Structure

```text
customer-support-chatbot/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── lambda/
│   └── index.py
│
├── screenshots/
│   ├── 01-flow-architecture.png
│   ├── 02-classifier.png
│   ├── 03-condition-routing.png
│   ├── 04-bug-formatter.png
│   ├── 05-lambda-configuration.png
│   ├── 06-successful-flow-test.png
│   ├── 07-dynamodb-record.png
│   └── 08-version-and-alias.png
│
└── test-results/
    └── test-cases.md
```

---

# 🛠️ Technology Stack

### Cloud & AI

* Amazon Bedrock
* Amazon Bedrock Flows
* Amazon Nova Pro
* AWS Lambda
* Amazon DynamoDB

### Programming

* Python 3.12
* JSON
* AWS SDK for Python (`boto3`)

### Development & Deployment

* AWS Management Console
* AWS CLI
* Git
* GitHub

---

# 📋 Requirements

Before deploying the project, ensure you have:

* An AWS account
* Access to Amazon Bedrock
* Access to the required Bedrock model
* Permission to create/use Bedrock Flows
* AWS Lambda permissions
* DynamoDB permissions
* AWS CLI configured
* Python 3.9+
* `boto3`

Required AWS permissions depend on the deployment environment and IAM configuration.

---

# ⚙️ Configuration

The Lambda function uses an environment variable to identify the DynamoDB table:

```text
TABLE_NAME=<your-dynamodb-table>
```

The table name should be configured through the Lambda environment rather than hardcoded into application logic.

---

# ▶️ Local Lambda Development

Install the AWS SDK:

```bash
pip install boto3
```

The Lambda handler is:

```text
index.lambda_handler
```

The deployed Lambda should use:

```text
Runtime: Python 3.12
Handler: index.lambda_handler
```

---

# 📊 Design Principles

The implementation follows several important engineering principles:

### 1. Separation of Concerns

The system separates:

* intent classification
* information extraction
* business logic
* persistence

This makes individual components easier to test and maintain.

### 2. Structured Data Contracts

The formatter produces a predictable JSON structure before invoking downstream business logic.

### 3. Deterministic Routing

The LLM determines the intent, while explicit Flow conditions control the actual workflow path.

### 4. Serverless Architecture

Lambda and DynamoDB eliminate the need to maintain traditional application servers for the ticket-creation workflow.

### 5. Fail-Safe Extraction

Missing information is not fabricated. Optional missing fields are represented using empty strings.

### 6. Immutable Deployment

The production flow should use a published Bedrock Flow version through an alias rather than relying on the continuously changing draft.

---

# 🔍 Observability & Debugging

During development, the system can be validated at multiple layers:

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

This layered validation makes it possible to identify whether an issue originates from classification, routing, extraction, Lambda execution, or persistence.

---

# 📈 Future Improvements

Potential production enhancements include:

* Authentication and authorization
* Conversation history
* Ticket-status lookup
* Ticket updates and closing workflows
* Human-agent dashboard
* Amazon CloudWatch monitoring and alarms
* Dead-letter/error handling
* Retry strategies
* Input validation and abuse protection
* Confidence-aware classification
* Guardrails for unsafe or inappropriate requests
* Automated regression testing
* CI/CD deployment
* Infrastructure as Code using AWS CloudFormation, AWS CDK, or Terraform
* Multi-language customer support
* Integration with existing CRM/help-desk systems
* Analytics for support volume and intent distribution

---

# 🎓 Project Outcomes

This project demonstrates practical implementation of:

* Generative AI workflow orchestration
* Amazon Bedrock Flows
* LLM-based intent classification
* Structured information extraction
* Conditional workflow routing
* AWS Lambda integration
* Serverless database persistence
* JSON-based tool interfaces
* End-to-end cloud application testing
* Immutable AI workflow deployment using versions and aliases

The project moves beyond a simple chatbot by combining **LLM reasoning with deterministic cloud automation and persistent backend state**.

---

# 📸 Evidence

The `screenshots/` directory contains implementation and validation evidence, including:

1. Complete Bedrock Flow architecture
2. Classifier configuration
3. Routing conditions
4. Bug Report Formatter configuration
5. Lambda configuration
6. Successful end-to-end execution
7. DynamoDB ticket record
8. Published Flow version and deployment alias

These screenshots provide visual evidence of both the implementation and successful execution of the system.

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

For substantial changes:

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Commit your changes with a descriptive message.
5. Open a pull request.

Please avoid committing credentials, private configuration, or sensitive AWS information.

---

# 📄 License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the complete license text.

---

# 👤 Author

**Ahmad Saleem**

Computer Science Student | AI/ML & Generative AI Enthusiast

Interested in:

* Artificial Intelligence
* Machine Learning
* Generative AI
* LLM Applications
* AI Agents
* Cloud Computing
* Intelligent Automation

---

## ⭐ Acknowledgements

Built using services and technologies provided by **Amazon Web Services**, including Amazon Bedrock, AWS Lambda, and Amazon DynamoDB.

---

## ⭐ If You Find This Project Useful

Consider giving the repository a ⭐ on GitHub and sharing feedback or suggestions.

---

**Built with Python, AWS, Amazon Bedrock, and a focus on practical AI engineering.**
