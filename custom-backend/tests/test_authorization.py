import os
import sys
from dataclasses import dataclass

# Bootstrapping import path so running directly or via IDE handles imports properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.authorization.core import (
    Action,
    AuthorizationContext,
    Decision,
    Environment,
    Policy,
    PolicyEngine,
    Resource,
    Subject,
)


@dataclass
class ExampleSubject(Subject):
    identifier: str
    clearance: int

    def get_id(self) -> str:
        return self.identifier

    def get_attributes(self) -> dict:
        return {"clearance": self.clearance}


@dataclass
class ExampleResource(Resource):
    identifier: str
    required_clearance: int

    def get_id(self) -> str:
        return self.identifier

    def get_attributes(self) -> dict:
        return {"required_clearance": self.required_clearance}


class ReadAction(Action):
    def get_name(self) -> str:
        return "read"


class ClearancePolicy(Policy):
    def evaluate(self, context: AuthorizationContext) -> Decision:
        subject = context.subject.get_attributes()
        resource = context.resource.get_attributes()
        if subject["clearance"] >= resource["required_clearance"]:
            return Decision.ALLOW
        return Decision.DENY


class NotForThisActionPolicy(Policy):
    def evaluate(self, context: AuthorizationContext) -> Decision:
        if context.action.get_name() == "read":
            return Decision.NOT_APPLICABLE
        return Decision.ALLOW


class ExplicitDenyPolicy(Policy):
    def evaluate(self, context: AuthorizationContext) -> Decision:
        return Decision.DENY


def context_for(clearance: int, required_clearance: int) -> AuthorizationContext:
    return AuthorizationContext(
        subject=ExampleSubject("subject-1", clearance),
        resource=ExampleResource("resource-1", required_clearance),
        action=ReadAction(),
        environment=Environment(),
    )


def test_abac_allows_when_policy_conditions_match():
    engine = PolicyEngine([ClearancePolicy()])
    assert engine.decide(context_for(3, 3)) == Decision.ALLOW
    assert engine.authorize(context_for(3, 3)) is True


def test_abac_denies_when_policy_conditions_do_not_match():
    engine = PolicyEngine([ClearancePolicy()])
    assert engine.decide(context_for(1, 3)) == Decision.DENY
    assert engine.authorize(context_for(1, 3)) is False


def test_no_applicable_policy_fails_closed():
    engine = PolicyEngine([NotForThisActionPolicy()])
    assert engine.decide(context_for(3, 3)) == Decision.DENY


def test_explicit_deny_overrides_allow():
    engine = PolicyEngine([ClearancePolicy(), ExplicitDenyPolicy()])
    assert engine.decide(context_for(3, 3)) == Decision.DENY
