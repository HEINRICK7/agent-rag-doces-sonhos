# Agent RAG Doces & Sonhos

Plataforma modular para catálogo, RAG, agentes e CRM da Doces & Sonhos, construída
em Python 3.12+, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic e Punq. O módulo
`users` é a implementação de referência da fundação Clean Architecture.

## Requisitos

- Python 3.12+
- Docker e `docker-compose` (ou Docker Compose v2)
- Git

## Execução local

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
make install
docker-compose up --build -d
docker-compose exec api alembic upgrade head
```

A API fica disponível em `http://localhost:8000`. O liveness check é
`GET /api/v1/health`. O readiness check `GET /api/v1/ready` valida PostgreSQL,
pgvector, Redis, MinIO e o bucket de produtos. A documentação está em `/docs`
no ambiente de desenvolvimento.

As portas externas da API, banco, Redis, MinIO e console do MinIO podem ser
alteradas no `.env` sem mudar a rede interna dos containers.

## Ingestão externa

O módulo `ingestion` já fornece cliente e mapper substituíveis para a API Doces
Sonhos. O contrato confirmado usa `http://localhost:3002`, listas JSON diretas
sem paginação e filtros `search`, `categoryId` e `subcategoryId`. O cliente
também implementa timeout, retry, correlation ID e autenticação opcional.

O mapper preserva preços como `Decimal`, timestamps e referências de categoria,
sem acoplar aplicação ou domínio ao payload externo. A chamada ao serviço em
execução e decisões de moeda, remoção e imagem ainda são gates explícitos. Veja
`docs/integrations/external-api.md`.

## Qualidade

```bash
make check
make coverage
make test-infrastructure
```

Os testes usam exclusivamente `unittest`/`unittest.IsolatedAsyncioTestCase`.
`make test-infrastructure` requer os containers locais em execução.

## Arquitetura

As entradas HTTP dependem da aplicação, a aplicação depende de contratos do domínio,
e a infraestrutura implementa esses contratos. O domínio não importa FastAPI,
Pydantic, SQLAlchemy ou Punq. A composição de dependências fica em
`app/bootstrap.py`.

Veja:

- `docs/architecture/overview.md`
- `docs/architecture/dependency-rules.md`
- `docs/architecture/target-structure.md`
- `docs/development/new-module-guide.md`
- `docs/development/testing-guide.md`
- `docs/development/troubleshooting.md`
- `docs/development/local-infrastructure.md`
- `docs/development/roadmap.md`
- `docs/development/deep-map.md`

## Endpoints de users

- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `GET /api/v1/users?limit=20&offset=0`
- `PATCH /api/v1/users/{user_id}/name`
- `PATCH /api/v1/users/{user_id}/deactivate`

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H 'content-type: application/json' \
  -d '{"name":"Carlos Henrique","email":"carlos@example.com"}'
```

## Migrations

```bash
alembic upgrade head
alembic downgrade -1
```

## Segurança

`.env` nunca deve ser versionado. Os valores do exemplo são somente para ambiente
local. Em produção, defina `APP_ENV=production`, uma `DATABASE_URL` segura e
`DOCS_ENABLED=false`.
