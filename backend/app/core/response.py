from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    """Consistent API envelope."""

    model_config = ConfigDict(from_attributes=True)

    data: T | None = None
    meta: Meta = Meta()


class ApiError(BaseModel):
    code: str
    message: str
    path: str | None = None


class ErrorEnvelope(BaseModel):
    error: ApiError

