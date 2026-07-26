"""Get-user use case."""

from app.users.application.dto.user_output import UserOutput
from app.users.domain.exceptions import UserNotFoundError
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.user_id import UserId


class GetUserUseCase:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UserId) -> UserOutput:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return UserOutput.from_entity(user)
