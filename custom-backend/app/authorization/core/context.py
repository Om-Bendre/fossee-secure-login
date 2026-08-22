from dataclasses import dataclass

from .action import Action
from .environment import Environment
from .resource import Resource
from .subject import Subject


@dataclass(frozen=True)
class AuthorizationContext:
    """Complete input to an authorization decision."""

    subject: Subject
    resource: Resource
    action: Action
    environment: Environment
