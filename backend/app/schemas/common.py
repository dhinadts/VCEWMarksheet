from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "Success"


def ok(data: Any, message: str = "Success") -> dict:
    return {"success": True, "data": data, "message": message}
