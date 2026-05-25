import threading
from datetime import datetime, timezone

from backend.models.session import Session, SessionMessage


class SessionStore:
    """Thread-safe in-memory session store."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create_session(self, name: str = "") -> Session:
        session = Session(name=name or f"Session {len(self._sessions) + 1}")
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        return sorted(
            self._sessions.values(),
            key=lambda s: s.updated_at,
            reverse=True,
        )

    def add_message(self, session_id: str, role: str, content: str) -> SessionMessage | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        msg = SessionMessage(role=role, content=content)
        with self._lock:
            session.messages.append(msg)
            session.updated_at = datetime.now(timezone.utc).isoformat()
        return msg

    def update_result(self, session_id: str, result: dict) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        with self._lock:
            session.current_result = result
            session.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


# Global singleton
session_store = SessionStore()
