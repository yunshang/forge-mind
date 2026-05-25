from dataclasses import asdict
from unittest.mock import AsyncMock, patch

import pytest
from litestar.testing import TestClient

from backend.main import app
from backend.agents.orchestrator import OrchestrationResult


@pytest.fixture
def client():
    return TestClient(app)


MOCK_ORCHESTRATION_RESULT = OrchestrationResult(
    status="success",
    contract_name="TestToken",
    solidity_code="// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\ncontract TestToken {}",
    constructor_args=["supply"],
    description="A test token",
    audit_result={"status": "PASS", "vulnerabilities": []},
    graph_data={"nodes": [{"id": "c", "type": "contractNode", "position": {"x": 0, "y": 0}, "data": {"label": "TestToken"}}], "edges": []},
    sandbox_result={"status": "success", "contract_address": "0xabc", "abi": [], "functions": []},
    logs=[{"agent": "orchestrator", "message": "Starting...", "level": "info"}],
    iterations=1,
)


class TestGenerateRoute:
    def test_generate_returns_201(self, client: TestClient):
        with patch("backend.routes.contracts.Orchestrator") as MockOrch:
            mock_instance = MockOrch.return_value
            mock_instance.run = AsyncMock(return_value=MOCK_ORCHESTRATION_RESULT)

            response = client.post("/api/contracts/generate", json={"prompt": "Create a token"})

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["contract_name"] == "TestToken"
        assert data["iterations"] == 1

    def test_generate_includes_graph_data(self, client: TestClient):
        with patch("backend.routes.contracts.Orchestrator") as MockOrch:
            mock_instance = MockOrch.return_value
            mock_instance.run = AsyncMock(return_value=MOCK_ORCHESTRATION_RESULT)

            response = client.post("/api/contracts/generate", json={"prompt": "Create a token"})

        data = response.json()
        assert "graph_data" in data
        assert len(data["graph_data"]["nodes"]) == 1

    def test_generate_includes_sandbox_result(self, client: TestClient):
        with patch("backend.routes.contracts.Orchestrator") as MockOrch:
            mock_instance = MockOrch.return_value
            mock_instance.run = AsyncMock(return_value=MOCK_ORCHESTRATION_RESULT)

            response = client.post("/api/contracts/generate", json={"prompt": "Create a token"})

        data = response.json()
        assert data["sandbox_result"]["contract_address"] == "0xabc"

    def test_generate_missing_prompt_returns_400(self, client: TestClient):
        response = client.post("/api/contracts/generate", json={})

        assert response.status_code == 400


class TestSandboxCallRoute:
    def test_call_requires_connection(self, client: TestClient):
        """When Anvil is not running, should return error gracefully."""
        response = client.post("/api/sandbox/call", json={
            "contract_address": "0x1234567890123456789012345678901234567890",
            "abi": [{"type": "function", "name": "get", "inputs": [], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"}],
            "function_name": "get",
            "args": [],
            "is_read": True,
        })

        # Should return either success (if Anvil is running) or error (if not)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] in ("success", "error")
