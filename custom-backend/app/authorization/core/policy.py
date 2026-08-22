from abc import ABC, abstractmethod

from .context import AuthorizationContext
from .decision import Decision


class Policy(ABC):
    """Base policy contract.

    A consumer may subclass this class and implement any authorization
    logic appropriate to its own domain.
    """

    @abstractmethod
    def evaluate(self, context: AuthorizationContext) -> Decision:
        raise NotImplementedError
