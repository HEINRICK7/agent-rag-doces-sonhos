"""Create-user input DTO."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateUserInput:
    name: str
    email: str
