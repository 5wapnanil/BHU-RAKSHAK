"""Deterministic offline tests for the verify_live_rag script."""

import asyncio
from typing import List, Optional
import unittest
from unittest.mock import AsyncMock, patch

from backend.app.services.backboard.config import BackboardSettings
from backend.app.services.backboard.exceptions import BackboardTimeoutError
from backend.app.services.backboard.models import BackboardMessageOutput
from backend.app.services.backboard.providers import BackboardProvider
from backend.scripts.verify_live_rag import QUERIES, run_rag_verification


class MockTestProvider(BackboardProvider):
    def __init__(
        self,
        thread_id: str = "th-test-12345",
        fail_at_query: Optional[int] = None,
        fail_status: bool = False,
        retrieved_files: Optional[List[str]] = None,
    ):
        self.thread_id = thread_id
        self.fail_at_query = fail_at_query
        self.fail_status = fail_status
        self.retrieved_files = retrieved_files if retrieved_files is not None else ["01_why_do_landslides_happen.md"]
        self.queries_dispatched: List[str] = []
        self.memory_flags: List[str] = []

    async def create_thread(self) -> str:
        return self.thread_id

    async def send_message(
        self,
        thread_id: str,
        content: str,
        memory: str = "off",
        stream: bool = False,
    ) -> BackboardMessageOutput:
        self.queries_dispatched.append(content)
        self.memory_flags.append(memory)

        if self.fail_at_query is not None and len(self.queries_dispatched) == self.fail_at_query:
            raise BackboardTimeoutError("Backboard message query timed out waiting for upstream response after 60.0s.")

        status = "FAILED" if self.fail_status else "COMPLETED"
        return BackboardMessageOutput(
            content=f"Detailed response for query: {content[:30]}",
            thread_id=thread_id,
            assistant_id="asst-test-12345",
            message_id=f"msg-{len(self.queries_dispatched)}",
            status=status,
            retrieved_files=self.retrieved_files,
            retrieved_files_count=len(self.retrieved_files),
            raw_response={"status": status, "cost_usd": 0.0001, "retrieved_files": self.retrieved_files},
        )


class TestVerifyLiveRAG(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.valid_cfg = BackboardSettings(
            api_key="valid-test-api-key",
            assistant_id="valid-test-assistant-id",
            base_url="https://app.backboard.io/api",
            timeout_seconds=60.0,
        )

    async def test_dry_run_without_live_flag_exits_zero(self):
        code = await run_rag_verification(live_flag=False, config=self.valid_cfg)
        self.assertEqual(code, 0)

    async def test_missing_credentials_exits_one(self):
        invalid_cfg = BackboardSettings(api_key="", assistant_id="")
        code = await run_rag_verification(live_flag=True, config=invalid_cfg)
        self.assertEqual(code, 1)

    async def test_successful_all_queries_verified(self):
        provider = MockTestProvider(retrieved_files=["01_why_do_landslides_happen.md", "04_why_rainfall_and_soil_moisture_matter.md"])
        code = await run_rag_verification(live_flag=True, provider=provider, config=self.valid_cfg)
        self.assertEqual(code, 0)
        self.assertEqual(len(provider.queries_dispatched), 3)
        self.assertTrue(all(m == "off" for m in provider.memory_flags))

    async def test_halts_immediately_on_query_timeout_without_retry(self):
        # Fail on query 2
        provider = MockTestProvider(fail_at_query=2)
        code = await run_rag_verification(live_flag=True, provider=provider, config=self.valid_cfg)
        self.assertEqual(code, 1)
        # Query 1 succeeded, Query 2 timed out, Query 3 was NOT attempted, Query 2 was NOT retried
        self.assertEqual(len(provider.queries_dispatched), 2)

    async def test_halts_immediately_on_upstream_status_failure(self):
        provider = MockTestProvider(fail_status=True)
        code = await run_rag_verification(live_flag=True, provider=provider, config=self.valid_cfg)
        self.assertEqual(code, 1)
        # First query failed status -> immediately halted, exactly 1 query dispatched
        self.assertEqual(len(provider.queries_dispatched), 1)

    async def test_successful_diagnose_queries_verified(self):
        provider = MockTestProvider(retrieved_files=["03_how_machine_learning_predicts_landslide_risk.md"])
        code = await run_rag_verification(live_flag=True, diagnose=True, provider=provider, config=self.valid_cfg)
        self.assertEqual(code, 0)
        self.assertEqual(len(provider.queries_dispatched), 2)
        self.assertTrue(all(m == "off" for m in provider.memory_flags))

    async def test_halts_if_thread_creation_fails(self):
        provider = MockTestProvider()
        provider.create_thread = AsyncMock(side_effect=BackboardTimeoutError("Connection timed out after 10.0s"))
        code = await run_rag_verification(live_flag=True, provider=provider, config=self.valid_cfg)
        self.assertEqual(code, 1)
        self.assertEqual(len(provider.queries_dispatched), 0)


if __name__ == "__main__":
    unittest.main()
