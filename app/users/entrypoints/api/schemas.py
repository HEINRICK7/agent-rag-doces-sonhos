"""HTTP schemas for the users API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=320)


class UpdateUserNameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ErrorBody(BaseModel):
    code: str
    message: str
    correlation_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody
