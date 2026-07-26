"""Transaction helpers."""

from sqlalchemy.ext.asyncio import AsyncSession


async def commit(session: AsyncSession) -> None:
    """Commit the current transaction."""

    await session.commit()


async def rollback(session: AsyncSession) -> None:
    """Rollback the current transaction."""

    await session.rollback()
