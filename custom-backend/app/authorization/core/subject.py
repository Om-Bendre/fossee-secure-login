from abc import ABC, abstractmethod
from typing import Any


class Subject(ABC):
    """Generic authorization subject.

    The framework does not assume that a subject is a User, Employee,
    ServiceAccount, or any other domain object.
    """

    @abstractmethod
    def get_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_attributes(self) -> dict[str, Any]:
        raise NotImplementedError
