# Bug Report Lambda

The Lambda function receives a structured bug report from the Amazon
Bedrock Flow.

## Input

The function accepts:

- description
- stepsToReproduce
- environment

## Processing

The function:

1. Generates a unique ticket ID.
2. Creates an OPEN ticket.
3. Stores the bug report in Amazon DynamoDB.
4. Returns the ticket ID and status.

## Output

Example:

{
  "ticketId": "example-ticket-id",
  "status": "OPEN",
  "message": "Bug report created successfully"
}

## AWS Resources

Lambda:
create-bug-report-1c16e0e0

DynamoDB:
bug-report-tool-stack-bug-reports

Region:
us-east-1
