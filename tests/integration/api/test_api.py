"""HTTP integration tests with an in-memory application container."""

import unittest

from app.main import create_app
from app.shared.configuration.settings import Settings
from app.users.application.usecases.create_user import CreateUserUseCase
from app.users.application.usecases.deactivate_user import DeactivateUserUseCase
from app.users.application.usecases.get_user import GetUserUseCase
from app.users.application.usecases.list_users import ListUsersUseCase
from app.users.application.usecases.update_user_name import UpdateUserNameUseCase
from fastapi.testclient import TestClient

from tests.fixtures.in_memory_user_repository import InMemoryUserRepository


class FakeInfrastructureHealth:
    def __init__(self, ready: bool = True) -> None:
        self.ready = ready

    async def check(self) -> dict[str, object]:
        status = "ok" if self.ready else "error"
        return {
            "status": "ready" if self.ready else "not_ready",
            "components": {
                "database": {"status": status, "detail": "teste"},
                "pgvector": {"status": status, "detail": "teste"},
                "redis": {"status": status, "detail": "teste"},
                "minio": {"status": status, "detail": "teste"},
            },
        }


class TestContainer:
    def __init__(self) -> None:
        repository = InMemoryUserRepository()
        self.instances = {
            CreateUserUseCase: CreateUserUseCase(repository),
            GetUserUseCase: GetUserUseCase(repository),
            ListUsersUseCase: ListUsersUseCase(repository),
            UpdateUserNameUseCase: UpdateUserNameUseCase(repository),
            DeactivateUserUseCase: DeactivateUserUseCase(repository),
        }

    def resolve(self, use_case_type: type[object]) -> object:
        return self.instances[use_case_type]


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app(Settings(_env_file=None, app_env="test"))
        app.state.container = TestContainer()
        app.state.infrastructure_health = FakeInfrastructureHealth()
        self.client = TestClient(app)

    def test_health_returns_ok_and_correlation_id(self) -> None:
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertTrue(response.headers.get("X-Correlation-ID"))

    def test_readiness_reports_every_infrastructure_dependency(self) -> None:
        response = self.client.get("/api/v1/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
        self.assertEqual(
            set(response.json()["components"]),
            {"database", "pgvector", "redis", "minio"},
        )

    def test_readiness_returns_503_when_a_dependency_is_unavailable(self) -> None:
        self.client.app.state.infrastructure_health = FakeInfrastructureHealth(ready=False)

        response = self.client.get("/api/v1/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "not_ready")

    def test_users_endpoints_use_cases(self) -> None:
        created = self.client.post(
            "/api/v1/users", json={"name": "Carlos", "email": "carlos@example.com"}
        )
        user_id = created.json()["id"]

        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get(f"/api/v1/users/{user_id}").status_code, 200)
        updated = self.client.patch(f"/api/v1/users/{user_id}/name", json={"name": "Ana"})
        deactivated = self.client.patch(f"/api/v1/users/{user_id}/deactivate")

        self.assertEqual(updated.json()["name"], "Ana")
        self.assertFalse(deactivated.json()["is_active"])

    def test_duplicate_email_returns_conflict(self) -> None:
        payload = {"name": "Carlos", "email": "carlos@example.com"}
        self.client.post("/api/v1/users", json=payload)

        duplicate = self.client.post("/api/v1/users", json=payload)

        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.json()["error"]["code"], "EMAIL_ALREADY_EXISTS")
