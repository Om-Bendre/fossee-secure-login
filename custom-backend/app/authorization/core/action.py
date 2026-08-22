from abc import ABC, abstractmethod
from typing import Any


class Action(ABC):
    """Generic operation requested against a resource."""

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError

    def get_attributes(self) -> dict[str, Any]:
        """Optional action attributes; consumers may override this."""
        return {}
