"""Create-user use case."""

from app.users.application.dto.create_user_input import CreateUserInput
from app.users.application.dto.user_output import UserOutput
from app.users.domain.entities.user import User
from app.users.domain.exceptions import EmailAlreadyExistsError
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.email import Email


class CreateUserUseCase:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, input_data: CreateUserInput) -> UserOutput:
        email = Email(input_data.email)
        if await self._repository.get_by_email(email) is not None:
            raise EmailAlreadyExistsError()
        user = User.create(name=input_data.name, email=email)
        await self._repository.save(user)
        return UserOutput.from_entity(user)
