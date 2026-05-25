import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SessionMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}


@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    messages: list[SessionMessage] = field(default_factory=list)
    current_result: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self, include_result: bool = True) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_result:
            d["current_result"] = self.current_result
        return d

    def to_summary(self) -> dict:
        """Lightweight version for list endpoints."""
        return {
            "id": self.id,
            "name": self.name,
            "message_count": len(self.messages),
            "has_result": bool(self.current_result),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
