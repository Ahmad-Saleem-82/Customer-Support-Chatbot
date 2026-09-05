import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


# -----------------------------------------------------------------------------
# Lambda Handler
# -----------------------------------------------------------------------------

def lambda_handler(event, context):
    """
    Create a customer bug report and persist it in DynamoDB.

    Expected Bedrock function parameters:
        - description
        - stepsToReproduce
        - environment

    Returns:
        Bedrock-compatible function response containing the ticket ID.
    """

    logger.info(
        "Received event: %s",
        json.dumps(event, default=str)
    )

    # -------------------------------------------------------------------------
    # Validate Bedrock function request
    # -------------------------------------------------------------------------

    if (
        event.get("messageVersion") != "1.0"
        or event.get("function") != "create_bug_report"
    ):
        logger.warning("Unsupported request format.")

        return _response(
            event,
            {
                "error": "unsupported",
                "message": "Unsupported request format."
            }
        )

    # -------------------------------------------------------------------------
    # Extract parameters
    # -------------------------------------------------------------------------

    parameters = event.get("parameters") or []

    request_data = {
        parameter.get("name"): parameter.get("value")
        for parameter in parameters
        if isinstance(parameter, dict)
        and parameter.get("name") is not None
    }

    description = (request_data.get("description") or "").strip()
    steps_to_reproduce = (
        request_data.get("stepsToReproduce") or ""
    ).strip()
    environment = (
        request_data.get("environment") or ""
    ).strip()

    # -------------------------------------------------------------------------
    # Validate required field
    # -------------------------------------------------------------------------

    if not description:
        logger.warning("Bug report rejected: description is missing.")

        return _response(
            event,
            {
                "error": "missing",
                "field": "description",
                "message": "Bug description is required."
            }
        )

    # -------------------------------------------------------------------------
    # Create ticket
    # -------------------------------------------------------------------------

    ticket_id = str(uuid.uuid4())

    created_at = datetime.now(timezone.utc).isoformat()

    item = {
        "ticketId": ticket_id,
        "description": description,
        "stepsToReproduce": steps_to_reproduce,
        "environment": environment,
        "status": "OPEN",
        "createdAt": created_at,
    }

    # -------------------------------------------------------------------------
    # Persist ticket in DynamoDB
    # -------------------------------------------------------------------------

    try:
        table.put_item(Item=item)

        logger.info(
            "Bug report created successfully: %s",
            ticket_id
        )

    except Exception:
        logger.exception(
            "Failed to persist bug report: %s",
            ticket_id
        )

        return _response(
            event,
            {
                "error": "database_error",
                "message": "Unable to create bug report."
            }
        )

    # -------------------------------------------------------------------------
    # Return successful response
    # -------------------------------------------------------------------------

    return _response(
        event,
        {
            "ticketId": ticket_id,
            "status": "OPEN",
            "message": "Bug report created successfully"
        }
    )


# -----------------------------------------------------------------------------
# Bedrock-Compatible Response
# -----------------------------------------------------------------------------

def _response(event, body):
    """
    Build the response expected by the Bedrock function/action interface.
    """

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "function": event.get("function"),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(body)
                    }
                }
            },
        },
    }
