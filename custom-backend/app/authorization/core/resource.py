from abc import ABC, abstractmethod
from typing import Any


class Resource(ABC):
    """Generic protected resource."""

    @abstractmethod
    def get_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_attributes(self) -> dict[str, Any]:
        raise NotImplementedError
