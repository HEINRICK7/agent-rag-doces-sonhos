"""Update-user-name use case."""

from app.shared.domain.exceptions import ValidationError
from app.users.application.dto.user_output import UserOutput
from app.users.domain.exceptions import UserNotFoundError
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.user_id import UserId


class UpdateUserNameUseCase:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UserId, name: str) -> UserOutput:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        if not name.strip():
            raise ValidationError("Nome não pode estar vazio.")
        user.update_name(name)
        await self._repository.update(user)
        return UserOutput.from_entity(user)
