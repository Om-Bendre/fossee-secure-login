from enum import Enum


class Decision(str, Enum):
    """Outcome produced by a policy or the policy engine."""

    ALLOW = "allow"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"
