"""HTTP client for the external product catalog."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Any
from urllib.parse import quote, urljoin, urlparse

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
    ProductSourceUnavailableError,
)
from app.ingestion.application.ports.product_source import ProductSource
from app.ingestion.infrastructure.external_api.schemas import ExternalProductPageEnvelope
from app.shared.configuration.settings import Settings

Sleep = Callable[[float], Awaitable[None]]
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class ProductApiClient(ProductSource):
    """Read raw product pages without persisting or normalizing business data."""

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
        sleeper: Sleep = asyncio.sleep,
    ) -> None:
        self._settings = settings
        self._client = http_client or httpx.AsyncClient()
        self._owns_client = http_client is None
        self._sleep = sleeper

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch_page(
        self,
        request: ProductPageRequest,
        correlation_id: str | None = None,
    ) -> ExternalProductPage:
        response = await self._request(request, correlation_id)
        payload = self._decode_json(response)
        envelope = self._parse_envelope(payload)
        next_request = self._next_request(request, response, envelope)
        return ExternalProductPage(
            items=tuple(dict(item) for item in envelope.items),
            request=request,
            has_more=next_request is not None,
            next_request=next_request,
            total=envelope.total,
        )

    async def iter_pages(
        self,
        filters: ProductFilters | None = None,
        correlation_id: str | None = None,
    ) -> AsyncIterator[ExternalProductPage]:
        request = ProductPageRequest(
            limit=self._settings.external_api_page_size,
            filters=filters or ProductFilters(),
        )
        seen: set[tuple[int, int, str | None, str | None]] = set()
        for _ in range(self._settings.external_api_max_pages):
            identity = (request.page, request.offset, request.cursor, request.next_url)
            if identity in seen:
                raise InvalidProductSourcePayloadError("A paginação externa entrou em ciclo.")
            seen.add(identity)
            page = await self.fetch_page(request, correlation_id)
            yield page
            if page.next_request is None:
                return
            request = page.next_request
        raise InvalidProductSourcePayloadError(
            f"A paginação excedeu {self._settings.external_api_max_pages} páginas."
        )

    async def fetch_product(
        self,
        external_id: str,
        correlation_id: str | None = None,
    ) -> dict[str, object]:
        identifier = quote(external_id.strip(), safe="")
        if not identifier:
            raise ValueError("external_id não pode ser vazio")
        payload = self._decode_json(
            await self._request_path(
                f"{self._settings.external_api_products_path.rstrip('/')}/{identifier}",
                correlation_id,
            )
        )
        if not isinstance(payload, Mapping):
            raise InvalidProductSourcePayloadError(
                "O detalhe de produto deve retornar um objeto JSON."
            )
        return dict(payload)

    async def fetch_categories(
        self,
        correlation_id: str | None = None,
    ) -> tuple[dict[str, object], ...]:
        return await self._fetch_object_list("/categories", correlation_id)

    async def fetch_subcategories(
        self,
        category_id: str,
        correlation_id: str | None = None,
    ) -> tuple[dict[str, object], ...]:
        identifier = quote(category_id.strip(), safe="")
        if not identifier:
            raise ValueError("category_id não pode ser vazio")
        return await self._fetch_object_list(
            f"/categories/{identifier}/subcategories",
            correlation_id,
        )

    async def _request(
        self,
        request: ProductPageRequest,
        correlation_id: str | None,
    ) -> httpx.Response:
        url = self._request_url(request)
        params = self._query_params(request)
        return await self._send(url, params, correlation_id)

    async def _request_path(
        self,
        path: str,
        correlation_id: str | None,
        params: dict[str, str | int] | None = None,
    ) -> httpx.Response:
        base_url = self._settings.external_api_base_url
        if not base_url:
            raise ProductSourceConfigurationError("EXTERNAL_API_BASE_URL não foi configurada.")
        url = urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
        return await self._send(url, params, correlation_id)

    async def _send(
        self,
        url: str,
        params: dict[str, str | int] | None,
        correlation_id: str | None,
    ) -> httpx.Response:
        headers = self._headers(correlation_id)
        last_transport_error: httpx.TransportError | None = None

        for attempt in range(self._settings.external_api_retry_attempts):
            try:
                response = await self._client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self._settings.external_api_timeout_seconds,
                    follow_redirects=True,
                )
            except httpx.TransportError as exc:
                last_transport_error = exc
                if attempt + 1 >= self._settings.external_api_retry_attempts:
                    break
                await self._sleep(self._retry_delay(attempt, None))
                continue

            if response.status_code not in RETRYABLE_STATUS_CODES:
                return self._validate_status(response)
            if attempt + 1 >= self._settings.external_api_retry_attempts:
                if response.status_code == 429:
                    raise ProductSourceRateLimitError(
                        "A API externa manteve o rate limit após os retries."
                    )
                raise ProductSourceUnavailableError(
                    f"A API externa permaneceu indisponível ({response.status_code})."
                )
            await self._sleep(self._retry_delay(attempt, response))

        raise ProductSourceUnavailableError(
            "Não foi possível conectar à API externa após os retries."
        ) from last_transport_error

    async def _fetch_object_list(
        self,
        path: str,
        correlation_id: str | None,
    ) -> tuple[dict[str, object], ...]:
        payload = self._decode_json(await self._request_path(path, correlation_id))
        if not isinstance(payload, list) or any(not isinstance(item, Mapping) for item in payload):
            raise InvalidProductSourcePayloadError(
                f"O endpoint '{path}' deve retornar uma lista de objetos."
            )
        return tuple(dict(item) for item in payload)

    def _request_url(self, request: ProductPageRequest) -> str:
        base_url = self._settings.external_api_base_url
        if not base_url:
            raise ProductSourceConfigurationError("EXTERNAL_API_BASE_URL não foi configurada.")
        if request.next_url:
            next_url = urljoin(f"{base_url.rstrip('/')}/", request.next_url)
            base_origin = urlparse(base_url)
            next_origin = urlparse(next_url)
            if (next_origin.scheme, next_origin.netloc) != (
                base_origin.scheme,
                base_origin.netloc,
            ):
                raise InvalidProductSourcePayloadError(
                    "O link de paginação aponta para uma origem externa não autorizada."
                )
            return next_url
        return urljoin(
            f"{base_url.rstrip('/')}/",
            self._settings.external_api_products_path.lstrip("/"),
        )

    def _headers(self, correlation_id: str | None) -> dict[str, str]:
        settings = self._settings
        headers = {
            "Accept": "application/json",
            "User-Agent": f"{settings.app_name}/catalog-ingestion",
        }
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        token = (
            settings.external_api_token.get_secret_value()
            if settings.external_api_token is not None
            else None
        )
        if settings.external_api_auth_mode == "bearer":
            if not token:
                raise ProductSourceConfigurationError(
                    "EXTERNAL_API_TOKEN é obrigatório para autenticação bearer."
                )
            headers["Authorization"] = f"Bearer {token}"
        elif settings.external_api_auth_mode == "api_key":
            if not token:
                raise ProductSourceConfigurationError(
                    "EXTERNAL_API_TOKEN é obrigatório para autenticação por API key."
                )
            headers[settings.external_api_api_key_header] = token
        return headers

    def _query_params(self, request: ProductPageRequest) -> dict[str, str | int] | None:
        settings = self._settings
        if request.next_url:
            return None
        params: dict[str, str | int] = {}
        if request.filters.search:
            params["search"] = request.filters.search
        if request.filters.category_id:
            params["categoryId"] = request.filters.category_id
        if request.filters.subcategory_id:
            params["subcategoryId"] = request.filters.subcategory_id
        if settings.external_api_pagination_mode == "none":
            return params
        params[settings.external_api_limit_param] = request.limit
        if settings.external_api_pagination_mode == "page":
            params[settings.external_api_page_param] = request.page
        elif settings.external_api_pagination_mode == "offset":
            params[settings.external_api_offset_param] = request.offset
        elif settings.external_api_pagination_mode == "cursor" and request.cursor:
            params[settings.external_api_cursor_param] = request.cursor
        return params

    def _decode_json(self, response: httpx.Response) -> object:
        try:
            return response.json()
        except ValueError as exc:
            raise InvalidProductSourcePayloadError("A API externa retornou JSON inválido.") from exc

    def _parse_envelope(self, payload: object) -> ExternalProductPageEnvelope:
        if isinstance(payload, list):
            raw_items: object = payload
            raw_has_more: object = False
            raw_cursor: object = None
            raw_total: object = None
        elif isinstance(payload, Mapping):
            raw_items = self._read_path(payload, self._settings.external_api_items_key)
            raw_has_more = self._read_path(
                payload,
                self._settings.external_api_has_more_key,
            )
            raw_cursor = self._read_path(
                payload,
                self._settings.external_api_next_cursor_key,
            )
            raw_total = self._read_path(payload, self._settings.external_api_total_key)
        else:
            raise InvalidProductSourcePayloadError(
                "O payload externo deve ser um objeto ou uma lista."
            )

        if not isinstance(raw_items, list) or any(
            not isinstance(item, Mapping) for item in raw_items
        ):
            raise InvalidProductSourcePayloadError(
                f"O campo '{self._settings.external_api_items_key}' deve ser uma lista de objetos."
            )
        try:
            return ExternalProductPageEnvelope.model_validate(
                {
                    "items": [dict(item) for item in raw_items],
                    "has_more": False if raw_has_more is None else raw_has_more,
                    "next_cursor": raw_cursor,
                    "total": raw_total,
                }
            )
        except ValueError as exc:
            raise InvalidProductSourcePayloadError(
                "Os metadados de paginação da API externa são inválidos."
            ) from exc

    def _next_request(
        self,
        request: ProductPageRequest,
        response: httpx.Response,
        envelope: ExternalProductPageEnvelope,
    ) -> ProductPageRequest | None:
        settings = self._settings
        link = response.links.get("next", {}).get("url")
        has_more = envelope.has_more or bool(envelope.next_cursor) or bool(link)
        if settings.external_api_infer_has_more_from_page_size:
            has_more = has_more or len(envelope.items) == request.limit
        if not has_more:
            return None
        if settings.external_api_pagination_mode == "cursor":
            if not envelope.next_cursor:
                raise InvalidProductSourcePayloadError(
                    "A resposta indicou próxima página sem fornecer cursor."
                )
            return ProductPageRequest(
                limit=request.limit,
                cursor=envelope.next_cursor,
                filters=request.filters,
            )
        if settings.external_api_pagination_mode == "link":
            if not link:
                raise InvalidProductSourcePayloadError(
                    "A resposta indicou próxima página sem um link 'next'."
                )
            return ProductPageRequest(
                limit=request.limit,
                next_url=link,
                filters=request.filters,
            )
        if settings.external_api_pagination_mode == "offset":
            return ProductPageRequest(
                page=request.page + 1,
                offset=request.offset + request.limit,
                limit=request.limit,
                filters=request.filters,
            )
        return ProductPageRequest(
            page=request.page + 1,
            offset=request.offset,
            limit=request.limit,
            filters=request.filters,
        )

    def _validate_status(self, response: httpx.Response) -> httpx.Response:
        if response.status_code in {401, 403}:
            raise ProductSourceAuthenticationError(
                "A API externa rejeitou as credenciais configuradas."
            )
        if response.status_code >= 400:
            raise ProductSourceResponseError(response.status_code)
        return response

    def _retry_delay(self, attempt: int, response: httpx.Response | None) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), self._settings.external_api_max_retry_delay)
                except ValueError:
                    pass
        delay = self._settings.external_api_retry_backoff_seconds * (2**attempt)
        return float(min(delay, self._settings.external_api_max_retry_delay))

    @staticmethod
    def _read_path(payload: Mapping[str, Any], path: str) -> object:
        current: object = payload
        for segment in path.split("."):
            if not isinstance(current, Mapping) or segment not in current:
                return None
            current = current[segment]
        return current
