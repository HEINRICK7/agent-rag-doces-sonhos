"""List-users use case."""

from app.shared.domain.exceptions import ValidationError
from app.users.application.dto.user_output import UserOutput
from app.users.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, limit: int = 20, offset: int = 0) -> list[UserOutput]:
        if limit < 1 or limit > 100:
            raise ValidationError("Limit deve estar entre 1 e 100.")
        if offset < 0:
            raise ValidationError("Offset não pode ser negativo.")
        users = await self._repository.list(limit=limit, offset=offset)
        return [UserOutput.from_entity(user) for user in users]
