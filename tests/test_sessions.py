from unittest.mock import AsyncMock, patch

import pytest
from litestar.testing import TestClient

from backend.main import app
from backend.store import SessionStore
from backend.agents.orchestrator import OrchestrationResult


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def store():
    return SessionStore()


MOCK_RESULT = OrchestrationResult(
    status="success",
    contract_name="TestToken",
    solidity_code="// code",
    audit_result={"status": "PASS", "vulnerabilities": []},
    graph_data={"nodes": [], "edges": []},
    sandbox_result={"status": "success", "contract_address": "0xabc"},
    logs=[{"agent": "orchestrator", "message": "done", "level": "info"}],
    iterations=1,
)


class TestSessionStore:
    def test_create_session(self, store: SessionStore):
        session = store.create_session("Test")
        assert session.name == "Test"
        assert session.id
        assert len(session.messages) == 0

    def test_get_session(self, store: SessionStore):
        session = store.create_session()
        found = store.get_session(session.id)
        assert found is not None
        assert found.id == session.id

    def test_get_nonexistent_session(self, store: SessionStore):
        assert store.get_session("nope") is None

    def test_list_sessions(self, store: SessionStore):
        store.create_session("A")
        store.create_session("B")
        sessions = store.list_sessions()
        assert len(sessions) == 2

    def test_add_message(self, store: SessionStore):
        session = store.create_session()
        msg = store.add_message(session.id, "user", "hello")
        assert msg is not None
        assert msg.role == "user"
        assert msg.content == "hello"

        updated = store.get_session(session.id)
        assert len(updated.messages) == 1

    def test_add_message_nonexistent(self, store: SessionStore):
        assert store.add_message("nope", "user", "hi") is None

    def test_update_result(self, store: SessionStore):
        session = store.create_session()
        assert store.update_result(session.id, {"status": "ok"})
        updated = store.get_session(session.id)
        assert updated.current_result == {"status": "ok"}

    def test_delete_session(self, store: SessionStore):
        session = store.create_session()
        assert store.delete_session(session.id)
        assert store.get_session(session.id) is None

    def test_delete_nonexistent(self, store: SessionStore):
        assert not store.delete_session("nope")


class TestSessionRoutes:
    def test_create_session(self, client: TestClient):
        resp = client.post("/api/sessions", json={"name": "My Session"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Session"
        assert data["id"]

    def test_list_sessions(self, client: TestClient):
        client.post("/api/sessions", json={"name": "A"})
        client.post("/api/sessions", json={"name": "B"})
        resp = client.get("/api/sessions")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_session(self, client: TestClient):
        create = client.post("/api/sessions", json={"name": "Test"})
        sid = create.json()["id"]
        resp = client.get(f"/api/sessions/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test"

    def test_get_nonexistent_session(self, client: TestClient):
        resp = client.get("/api/sessions/nonexistent")
        assert resp.status_code == 404

    def test_delete_session(self, client: TestClient):
        create = client.post("/api/sessions", json={"name": "Del"})
        sid = create.json()["id"]
        resp = client.delete(f"/api/sessions/{sid}")
        assert resp.status_code == 200
        # Verify deleted
        resp = client.get(f"/api/sessions/{sid}")
        assert resp.status_code == 404

    def test_generate_in_session(self, client: TestClient):
        create = client.post("/api/sessions", json={"name": "Gen"})
        sid = create.json()["id"]

        with patch("backend.routes.sessions.Orchestrator") as MockOrch:
            mock = MockOrch.return_value
            mock.run = AsyncMock(return_value=MOCK_RESULT)

            resp = client.post(f"/api/sessions/{sid}/generate", json={"prompt": "Create a token"})

        assert resp.status_code == 201
        data = resp.json()
        assert data["contract_name"] == "TestToken"
        assert data["session_id"] == sid

        # Verify messages were added to session
        session_resp = client.get(f"/api/sessions/{sid}")
        session_data = session_resp.json()
        assert len(session_data["messages"]) == 2  # user + assistant
        assert session_data["messages"][0]["role"] == "user"
        assert session_data["messages"][1]["role"] == "assistant"

    def test_generate_nonexistent_session(self, client: TestClient):
        resp = client.post("/api/sessions/nope/generate", json={"prompt": "test"})
        assert resp.status_code == 404
