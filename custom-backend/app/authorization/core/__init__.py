"""Domain-agnostic ABAC primitives."""

from .action import Action
from .context import AuthorizationContext
from .decision import Decision
from .engine import PolicyEngine
from .environment import Environment
from .policy import Policy
from .resource import Resource
from .subject import Subject

__all__ = [
    "Action",
    "AuthorizationContext",
    "Decision",
    "PolicyEngine",
    "Environment",
    "Policy",
    "Resource",
    "Subject",
]
