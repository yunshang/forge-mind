from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.orchestrator import Orchestrator
from tests.conftest import SAMPLE_MINIMAL, SAMPLE_VULNERABLE


@pytest.fixture
def orchestrator():
    return Orchestrator()


MOCK_CODE_RESULT = {
    "agent": "coder",
    "action": "generate",
    "contract_name": "TestContract",
    "solidity_code": SAMPLE_MINIMAL,
    "constructor_args": [],
    "description": "A test contract",
}

MOCK_GRAPH = {
    "nodes": [
        {"id": "contract-TestContract", "type": "contractNode", "position": {"x": 400, "y": 200}, "data": {"label": "TestContract", "type": "contract"}},
        {"id": "func-set-0", "type": "functionNode", "position": {"x": 100, "y": 400}, "data": {"label": "set", "visibility": "external", "node_type": "functionWrite"}},
    ],
    "edges": [
        {"id": "e1", "source": "contract-TestContract", "target": "func-set-0", "type": "smoothstep", "label": "external"},
    ],
}

MOCK_SANDBOX = {
    "status": "success",
    "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
    "abi": [],
    "functions": [],
}


class TestOrchestrator:
    async def test_pass_on_first_try(self, orchestrator: Orchestrator):
        """Audit passes on first iteration — no healing loop needed."""
        with (
            patch.object(orchestrator.coder, "generate", new_callable=AsyncMock, return_value=MOCK_CODE_RESULT),
            patch.object(orchestrator.reviewer, "review", new_callable=AsyncMock, return_value={"status": "PASS", "vulnerabilities": []}),
            patch.object(orchestrator.ast_skill, "execute", new_callable=AsyncMock, return_value=MOCK_GRAPH),
            patch.object(orchestrator.sandbox_skill, "execute", new_callable=AsyncMock, return_value=MOCK_SANDBOX),
        ):
            result = await orchestrator.run(prompt="Create a simple storage contract")

        assert result.status == "success"
        assert result.contract_name == "TestContract"
        assert result.iterations == 1
        assert result.audit_result["status"] == "PASS"
        assert len(result.graph_data["nodes"]) == 2

    async def test_healing_loop_fixes_vulnerabilities(self, orchestrator: Orchestrator):
        """Audit fails first, passes on second iteration."""
        fail_result = {"status": "FAIL", "vulnerabilities": [{"severity": "high", "vulnerability": "Reentrancy Risk", "location": "line 5", "description": "test"}]}
        pass_result = {"status": "PASS", "vulnerabilities": []}

        review_count = 0
        generate_count = 0

        async def mock_review(*args, **kwargs):
            nonlocal review_count
            review_count += 1
            return fail_result if review_count == 1 else pass_result

        async def mock_generate(*args, **kwargs):
            nonlocal generate_count
            generate_count += 1
            return MOCK_CODE_RESULT

        with (
            patch.object(orchestrator.coder, "generate", side_effect=mock_generate),
            patch.object(orchestrator.reviewer, "review", side_effect=mock_review),
            patch.object(orchestrator.reviewer, "format_feedback", return_value="Fix reentrancy"),
            patch.object(orchestrator.ast_skill, "execute", new_callable=AsyncMock, return_value=MOCK_GRAPH),
            patch.object(orchestrator.sandbox_skill, "execute", new_callable=AsyncMock, return_value=MOCK_SANDBOX),
        ):
            result = await orchestrator.run(prompt="Create a token")

        assert result.status == "success"
        assert result.iterations == 2
        assert result.audit_result["status"] == "PASS"
        assert generate_count == 2

    async def test_max_iterations_stops_loop(self, orchestrator: Orchestrator):
        """Loop stops after max iterations even if audit keeps failing."""
        fail_result = {"status": "FAIL", "vulnerabilities": [{"severity": "high", "vulnerability": "Reentrancy Risk", "location": "line 5", "description": "test"}]}

        generate_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal generate_count
            generate_count += 1
            return MOCK_CODE_RESULT

        with (
            patch.object(orchestrator.coder, "generate", side_effect=mock_generate),
            patch.object(orchestrator.reviewer, "review", new_callable=AsyncMock, return_value=fail_result),
            patch.object(orchestrator.reviewer, "format_feedback", return_value="Fix it"),
            patch.object(orchestrator.ast_skill, "execute", new_callable=AsyncMock, return_value=MOCK_GRAPH),
            patch.object(orchestrator.sandbox_skill, "execute", new_callable=AsyncMock, return_value=MOCK_SANDBOX),
        ):
            result = await orchestrator.run(prompt="Create a token")

        assert result.status == "success"
        assert result.iterations == 3
        assert generate_count == 3

    async def test_logs_are_collected(self, orchestrator: Orchestrator):
        with (
            patch.object(orchestrator.coder, "generate", new_callable=AsyncMock, return_value=MOCK_CODE_RESULT),
            patch.object(orchestrator.reviewer, "review", new_callable=AsyncMock, return_value={"status": "PASS", "vulnerabilities": []}),
            patch.object(orchestrator.ast_skill, "execute", new_callable=AsyncMock, return_value=MOCK_GRAPH),
            patch.object(orchestrator.sandbox_skill, "execute", new_callable=AsyncMock, return_value=MOCK_SANDBOX),
        ):
            result = await orchestrator.run(prompt="Test")

        assert len(result.logs) > 0
        agents = [log["agent"] for log in result.logs]
        assert "orchestrator" in agents
        assert "coder" in agents
        assert "reviewer" in agents

    async def test_on_log_callback_called(self, orchestrator: Orchestrator):
        callback = AsyncMock()

        with (
            patch.object(orchestrator.coder, "generate", new_callable=AsyncMock, return_value=MOCK_CODE_RESULT),
            patch.object(orchestrator.reviewer, "review", new_callable=AsyncMock, return_value={"status": "PASS", "vulnerabilities": []}),
            patch.object(orchestrator.ast_skill, "execute", new_callable=AsyncMock, return_value=MOCK_GRAPH),
            patch.object(orchestrator.sandbox_skill, "execute", new_callable=AsyncMock, return_value=MOCK_SANDBOX),
        ):
            await orchestrator.run(prompt="Test", on_log=callback)

        assert callback.await_count > 0

    async def test_coder_failure_returns_error(self, orchestrator: Orchestrator):
        with patch.object(orchestrator.coder, "generate", new_callable=AsyncMock, side_effect=RuntimeError("LLM timeout")):
            result = await orchestrator.run(prompt="Test")

        assert result.status == "error"
        assert "LLM timeout" in result.error
        assert result.iterations == 1

    async def test_sandbox_failure_does_not_crash(self, orchestrator: Orchestrator):
        """Sandbox failure should be recorded but not fail the whole pipeline."""
        with (
            patch.object(orchestrator.coder, "generate", new_callable=AsyncMock, return_value=MOCK_CODE_RESULT),
            patch.object(orchestrator.reviewer, "review", new_callable=AsyncMock, return_value={"status": "PASS", "vulnerabilities": []}),
            patch.object(orchestrator.ast_skill, "execute", new_callable=AsyncMock, return_value=MOCK_GRAPH),
            patch.object(orchestrator.sandbox_skill, "execute", new_callable=AsyncMock, side_effect=RuntimeError("Anvil down")),
        ):
            result = await orchestrator.run(prompt="Test")

        assert result.status == "success"
        assert result.sandbox_result["status"] == "error"
        assert "Anvil down" in result.sandbox_result["error"]
