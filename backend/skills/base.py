from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    """Base class for all agent skills."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the skill and return structured result."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
