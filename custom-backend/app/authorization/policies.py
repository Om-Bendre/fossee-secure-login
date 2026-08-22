from .core import AuthorizationContext, Decision, Policy


class FileOwnershipPolicy(Policy):
    """Allow access only when the subject owns the file resource."""

    def evaluate(self, context: AuthorizationContext) -> Decision:
        subject = context.subject.get_attributes()
        resource = context.resource.get_attributes()

        if subject.get("id") == resource.get("owner_id"):
            return Decision.ALLOW

        return Decision.DENY
