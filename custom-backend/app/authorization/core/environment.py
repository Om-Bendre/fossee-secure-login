from typing import Any


class Environment:
    """Optional request/environment attributes.

    Consumers can instantiate this directly or subclass it when their
    authorization policies need contextual information.
    """

    def get_attributes(self) -> dict[str, Any]:
        return {}
