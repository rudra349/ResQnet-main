"""
ResQNet — AWS Lambda Client
Triggers the report-analyzer Lambda function asynchronously.
Falls back to inline processing when USE_LAMBDA_MOCK=true.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from app.config import settings

logger = logging.getLogger("resqnet.aws.lambda")


async def trigger_report_analysis(report_id: str, report_content: str) -> None:
    """
    Invoke the resqnet-report-analyzer Lambda function.
    Lambda: generates embedding + AI analysis + stores result as memory.

    If USE_LAMBDA_MOCK=true, processes inline (same process, async).
    """
    payload = {
        "report_id": report_id,
        "report_content": report_content,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if settings.use_lambda_mock:
        logger.info(f"[MOCK Lambda] Would invoke {settings.lambda_function_name} with report {report_id}")
        # In mock mode, the memory is stored by the FastAPI route directly
        return

    try:
        import asyncio
        import boto3
        loop = asyncio.get_event_loop()
        client = boto3.client(
            "lambda",
            region_name=settings.lambda_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        await loop.run_in_executor(
            None,
            lambda: client.invoke(
                FunctionName=settings.lambda_function_name,
                InvocationType="Event",  # Async invocation
                Payload=json.dumps(payload),
            )
        )
        logger.info(f"Lambda invoked for report {report_id}")
    except Exception as e:
        logger.error(f"Lambda invocation failed (non-fatal): {e}")
