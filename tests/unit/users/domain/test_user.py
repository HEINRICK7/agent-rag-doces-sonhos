"""Unit tests for user domain invariants."""

import unittest

from app.shared.domain.exceptions import ValidationError
from app.users.domain.entities.user import User
from app.users.domain.exceptions import InvalidEmailError, UserAlreadyInactiveError
from app.users.domain.value_objects.email import Email


class UserDomainTestCase(unittest.TestCase):
    def test_creates_user_with_normalized_email(self) -> None:
        user = User.create(" Carlos Henrique ", Email(" CARLOS@EXAMPLE.COM "))

        self.assertEqual(user.name, "Carlos Henrique")
        self.assertEqual(str(user.email), "carlos@example.com")
        self.assertTrue(user.is_active)

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(ValidationError):
            User.create("   ", Email("carlos@example.com"))

    def test_rejects_invalid_email(self) -> None:
        with self.assertRaises(InvalidEmailError):
            Email("invalid-email")

    def test_updates_name_and_deactivates_once(self) -> None:
        user = User.create("Carlos", Email("carlos@example.com"))
        user.update_name("Ana")
        user.deactivate()

        self.assertEqual(user.name, "Ana")
        self.assertFalse(user.is_active)
        with self.assertRaises(UserAlreadyInactiveError):
            user.deactivate()
