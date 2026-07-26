"""HTTP dependency resolution through the composition root."""

from typing import TypeVar, cast

from fastapi import Request

from app.users.application.usecases.create_user import CreateUserUseCase
from app.users.application.usecases.deactivate_user import DeactivateUserUseCase
from app.users.application.usecases.get_user import GetUserUseCase
from app.users.application.usecases.list_users import ListUsersUseCase
from app.users.application.usecases.update_user_name import UpdateUserNameUseCase

UseCaseT = TypeVar("UseCaseT")


def resolve(request: Request, use_case_type: type[UseCaseT]) -> UseCaseT:
    """Resolve a use case from the application container."""

    return cast(UseCaseT, request.app.state.container.resolve(use_case_type))


def create_user_use_case(request: Request) -> CreateUserUseCase:
    return resolve(request, CreateUserUseCase)


def get_user_use_case(request: Request) -> GetUserUseCase:
    return resolve(request, GetUserUseCase)


def list_users_use_case(request: Request) -> ListUsersUseCase:
    return resolve(request, ListUsersUseCase)


def update_user_name_use_case(request: Request) -> UpdateUserNameUseCase:
    return resolve(request, UpdateUserNameUseCase)


def deactivate_user_use_case(request: Request) -> DeactivateUserUseCase:
    return resolve(request, DeactivateUserUseCase)
