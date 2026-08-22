from typing import Any

from .core import Resource, Subject
from .core.action import Action
from .core.environment import Environment


class UserSubject(Subject):
    """Application adapter that exposes a User as a generic ABAC subject."""

    def __init__(self, user: Any):
        self.user = user

    def get_id(self) -> str:
        return str(self.user.id)

    def get_attributes(self) -> dict[str, Any]:
        return {
            "id": str(self.user.id),
            "email": self.user.email,
            "role": self.user.role,
        }


class FileResource(Resource):
    """Application adapter that exposes a File as a generic ABAC resource."""

    def __init__(self, file: Any):
        self.file = file

    def get_id(self) -> str:
        return str(self.file.id)

    def get_attributes(self) -> dict[str, Any]:
        return {
            "id": str(self.file.id),
            "owner_id": str(self.file.owner_id),
            "file_name": self.file.file_name,
            "mime_type": self.file.mime_type,
        }


class FileReadAction(Action):
    def get_name(self) -> str:
        return "read"


class FileDownloadAction(Action):
    def get_name(self) -> str:
        return "download"


class EmptyEnvironment(Environment):
    """Default application environment for the current assignment."""

    pass
