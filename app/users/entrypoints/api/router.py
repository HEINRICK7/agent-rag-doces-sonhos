"""Users HTTP routes."""

from fastapi import APIRouter, Depends, Query, status

from app.users.application.dto.create_user_input import CreateUserInput
from app.users.application.dto.user_output import UserOutput
from app.users.application.usecases.create_user import CreateUserUseCase
from app.users.application.usecases.deactivate_user import DeactivateUserUseCase
from app.users.application.usecases.get_user import GetUserUseCase
from app.users.application.usecases.list_users import ListUsersUseCase
from app.users.application.usecases.update_user_name import UpdateUserNameUseCase
from app.users.domain.value_objects.user_id import UserId
from app.users.entrypoints.api.dependencies import (
    create_user_use_case,
    deactivate_user_use_case,
    get_user_use_case,
    list_users_use_case,
    update_user_name_use_case,
)
from app.users.entrypoints.api.schemas import CreateUserRequest, UpdateUserNameRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def _response(output: UserOutput) -> UserResponse:
    return UserResponse(
        id=output.id,
        name=output.name,
        email=output.email,
        is_active=output.is_active,
        created_at=output.created_at,
        updated_at=output.updated_at,
    )


def _user_id(value: str) -> UserId:
    try:
        return UserId.from_string(value)
    except ValueError as error:
        from app.shared.domain.exceptions import ValidationError

        raise ValidationError("ID de usuário inválido.") from error


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    use_case: CreateUserUseCase = Depends(create_user_use_case),
) -> UserResponse:
    output = await use_case.execute(CreateUserInput(name=payload.name, email=payload.email))
    return _response(output)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    use_case: GetUserUseCase = Depends(get_user_use_case),
) -> UserResponse:
    return _response(await use_case.execute(_user_id(user_id)))


@router.get("", response_model=list[UserResponse])
async def list_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    use_case: ListUsersUseCase = Depends(list_users_use_case),
) -> list[UserResponse]:
    return [_response(output) for output in await use_case.execute(limit=limit, offset=offset)]


@router.patch("/{user_id}/name", response_model=UserResponse)
async def update_user_name(
    user_id: str,
    payload: UpdateUserNameRequest,
    use_case: UpdateUserNameUseCase = Depends(update_user_name_use_case),
) -> UserResponse:
    return _response(await use_case.execute(_user_id(user_id), payload.name))


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    use_case: DeactivateUserUseCase = Depends(deactivate_user_use_case),
) -> UserResponse:
    return _response(await use_case.execute(_user_id(user_id)))
