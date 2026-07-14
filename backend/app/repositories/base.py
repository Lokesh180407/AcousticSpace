from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

ModelT = TypeVar("ModelT")


class AsyncRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, obj_id: Any) -> ModelT | None:
        result = await self.session.execute(select(self._model).where(self._model.id == obj_id))  # type: ignore[attr-defined]
        return result.scalar_one_or_none()

    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def commit(self) -> None:
        await self.session.commit()

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
