from collections.abc import Iterable

from .context import AuthorizationContext
from .decision import Decision
from .policy import Policy


class PolicyEngine:
    """Deterministic ABAC policy evaluator.

    Semantics:
    - Any explicit DENY overrides every ALLOW.
    - Otherwise, any ALLOW permits the request.
    - If no policy applies, the engine fails closed with DENY.
    """

    def __init__(self, policies: Iterable[Policy] = ()):
        self._policies = list(policies)

    @property
    def policies(self) -> tuple[Policy, ...]:
        return tuple(self._policies)

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def decide(self, context: AuthorizationContext) -> Decision:
        saw_allow = False

        for policy in self._policies:
            decision = policy.evaluate(context)
            if decision == Decision.DENY:
                return Decision.DENY
            if decision == Decision.ALLOW:
                saw_allow = True

        return Decision.ALLOW if saw_allow else Decision.DENY

    def authorize(self, context: AuthorizationContext) -> bool:
        return self.decide(context) == Decision.ALLOW
