"""Tests for the external product API client."""

import unittest
from unittest.mock import AsyncMock

import httpx
from app.ingestion.application.dto.external_product_page import (
    ExternalProductPage,
    ProductFilters,
    ProductPageRequest,
)
from app.ingestion.application.exceptions import (
    InvalidProductSourcePayloadError,
    ProductSourceAuthenticationError,
    ProductSourceConfigurationError,
    ProductSourceRateLimitError,
    ProductSourceResponseError,
)
from app.ingestion.infrastructure.external_api.product_api_client import ProductApiClient
from app.shared.configuration.settings import Settings

from tests.fixtures.fake_product_source import FakeProductSource


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "external_api_base_url": "https://catalog.example.test",
        "external_api_pagination_mode": "page",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


class ProductPageRequestTestCase(unittest.TestCase):
    def test_rejects_invalid_pagination_values(self) -> None:
        with self.assertRaises(ValueError):
            ProductPageRequest(page=0)
        with self.assertRaises(ValueError):
            ProductPageRequest(offset=-1)
        with self.assertRaises(ValueError):
            ProductPageRequest(limit=501)


class FakeProductSourceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_is_substitutable_and_records_correlation_id(self) -> None:
        request = ProductPageRequest()
        page = ExternalProductPage(
            items=({"id": "cake-1"},),
            request=request,
            has_more=False,
            next_request=None,
        )
        source = FakeProductSource([page])

        result = await source.fetch_page(request, "corr-fake")

        self.assertEqual(result.items[0]["id"], "cake-1")
        self.assertEqual(source.correlation_ids, ["corr-fake"])


class ProductApiClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_requires_base_url_before_opening_a_connection(self) -> None:
        client = ProductApiClient(Settings(_env_file=None))

        with self.assertRaises(ProductSourceConfigurationError):
            await client.fetch_page(ProductPageRequest())
        await client.close()

    async def test_iterates_pages_and_propagates_auth_and_correlation_headers(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            page = int(request.url.params["page"])
            return httpx.Response(
                200,
                json={
                    "items": [{"id": f"cake-{page}"}],
                    "has_more": page == 1,
                    "total": 2,
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(
                settings(external_api_auth_mode="bearer", external_api_token="secret"),
                http_client,
            )
            pages = [page async for page in client.iter_pages(correlation_id="corr-123")]

        self.assertEqual([page.items[0]["id"] for page in pages], ["cake-1", "cake-2"])
        self.assertEqual(requests[0].headers["Authorization"], "Bearer secret")
        self.assertEqual(requests[0].headers["X-Correlation-ID"], "corr-123")
        self.assertEqual(requests[0].url.params["limit"], "100")

    async def test_consumes_confirmed_direct_list_with_product_filters(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json=[{"id": "cake-1", "name": "Crostini"}])

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(
                settings(external_api_pagination_mode="none"),
                http_client,
            )
            pages = [
                page
                async for page in client.iter_pages(
                    ProductFilters(
                        search="cros",
                        category_id="category-1",
                        subcategory_id="subcategory-1",
                    )
                )
            ]

        self.assertEqual(len(pages), 1)
        self.assertEqual(
            dict(requests[0].url.params),
            {
                "search": "cros",
                "categoryId": "category-1",
                "subcategoryId": "subcategory-1",
            },
        )

    async def test_reads_product_category_and_subcategory_endpoints(self) -> None:
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            if request.url.path == "/products/product-1":
                return httpx.Response(200, json={"id": "product-1", "name": "Crostini"})
            if request.url.path == "/categories":
                return httpx.Response(200, json=[{"id": "category-1", "name": "Natal"}])
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "subcategory-1",
                        "name": "Entradas",
                        "categoryId": "category-1",
                    }
                ],
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(
                settings(external_api_pagination_mode="none"),
                http_client,
            )
            product = await client.fetch_product("product-1", "corr-detail")
            categories = await client.fetch_categories()
            subcategories = await client.fetch_subcategories("category-1")

        self.assertEqual(product["id"], "product-1")
        self.assertEqual(categories[0]["name"], "Natal")
        self.assertEqual(subcategories[0]["name"], "Entradas")
        self.assertEqual(
            paths,
            [
                "/products/product-1",
                "/categories",
                "/categories/category-1/subcategories",
            ],
        )

    async def test_supports_nested_items_and_cursor_pagination(self) -> None:
        cursors: list[str | None] = []

        def handler(request: httpx.Request) -> httpx.Response:
            cursor = request.url.params.get("after")
            cursors.append(cursor)
            if cursor is None:
                return httpx.Response(
                    200,
                    json={"data": {"products": [{"id": "1"}], "more": True, "after": "next"}},
                )
            return httpx.Response(
                200,
                json={"data": {"products": [{"id": "2"}], "more": False, "after": None}},
            )

        configured = settings(
            external_api_pagination_mode="cursor",
            external_api_cursor_param="after",
            external_api_items_key="data.products",
            external_api_has_more_key="data.more",
            external_api_next_cursor_key="data.after",
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(configured, http_client)
            pages = [page async for page in client.iter_pages()]

        self.assertEqual(cursors, [None, "next"])
        self.assertEqual(len(pages), 2)

    async def test_follows_same_origin_link_pagination(self) -> None:
        requested_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(str(request.url))
            if request.url.params.get("page") is None:
                return httpx.Response(
                    200,
                    json={"items": [{"id": "1"}]},
                    headers={"Link": '<https://catalog.example.test/products?page=2>; rel="next"'},
                )
            return httpx.Response(200, json={"items": [{"id": "2"}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(
                settings(external_api_pagination_mode="link"),
                http_client,
            )
            pages = [page async for page in client.iter_pages()]

        self.assertEqual(
            requested_paths,
            [
                "https://catalog.example.test/products?limit=100",
                "https://catalog.example.test/products?page=2",
            ],
        )
        self.assertEqual([page.items[0]["id"] for page in pages], ["1", "2"])

    async def test_blocks_cross_origin_pagination_links(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"items": [{"id": "1"}]},
                headers={"Link": '<https://attacker.example/products>; rel="next"'},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(
                settings(external_api_pagination_mode="link"),
                http_client,
            )
            first_page = await client.fetch_page(ProductPageRequest())
            assert first_page.next_request is not None
            with self.assertRaises(InvalidProductSourcePayloadError):
                await client.fetch_page(first_page.next_request)

    async def test_retries_server_errors_with_limited_backoff(self) -> None:
        attempts = 0
        sleeper = AsyncMock()

        def handler(_: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, headers={"Retry-After": "0.1"})
            return httpx.Response(200, json={"items": []})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(settings(), http_client, sleeper=sleeper)
            page = await client.fetch_page(ProductPageRequest())

        self.assertEqual(page.items, ())
        self.assertEqual(attempts, 2)
        sleeper.assert_awaited_once_with(0.1)

    async def test_raises_rate_limit_after_retry_budget(self) -> None:
        sleeper = AsyncMock()

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(429)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(
                settings(external_api_retry_attempts=2),
                http_client,
                sleeper=sleeper,
            )
            with self.assertRaises(ProductSourceRateLimitError):
                await client.fetch_page(ProductPageRequest())

        sleeper.assert_awaited_once()

    async def test_distinguishes_authentication_and_other_client_errors(self) -> None:
        responses = iter([httpx.Response(401), httpx.Response(422)])

        def handler(_: httpx.Request) -> httpx.Response:
            return next(responses)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(settings(), http_client)
            with self.assertRaises(ProductSourceAuthenticationError):
                await client.fetch_page(ProductPageRequest())
            with self.assertRaises(ProductSourceResponseError) as context:
                await client.fetch_page(ProductPageRequest())

        self.assertEqual(context.exception.status_code, 422)

    async def test_rejects_invalid_json_and_item_shape(self) -> None:
        responses = iter(
            [
                httpx.Response(200, content=b"not-json"),
                httpx.Response(200, json={"items": ["not-an-object"]}),
            ]
        )

        def handler(_: httpx.Request) -> httpx.Response:
            return next(responses)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = ProductApiClient(settings(), http_client)
            with self.assertRaises(InvalidProductSourcePayloadError):
                await client.fetch_page(ProductPageRequest())
            with self.assertRaises(InvalidProductSourcePayloadError):
                await client.fetch_page(ProductPageRequest())
