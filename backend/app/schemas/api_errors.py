from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    path: str | None = None


ErrorCode = Literal[
    "VALIDATION_ERROR",
    "INTERNAL_SERVER_ERROR",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "AUDIO_VALIDATION_ERROR",
    "AUTH_ERROR",
    "RATE_LIMITED",
]

