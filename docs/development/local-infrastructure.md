# Infraestrutura local

O ambiente local usa serviços isolados e persistentes:

```text
FastAPI
├── PostgreSQL 16 + pgvector 0.8.0
├── Redis 7.4
└── MinIO + bucket products
```

## Inicialização

```bash
cp .env.example .env
docker-compose up -d --build
docker-compose exec api alembic upgrade head
```

O serviço `minio-init` cria o bucket configurado por `MINIO_BUCKET` de forma
idempotente. PostgreSQL, Redis e MinIO usam volumes nomeados.

O head atual é `0004_incremental_sync_evidence`, que acrescenta fingerprints de
produtos, contadores e evidências de mudança às execuções. O upgrade foi validado no
PostgreSQL local; o downgrade é testado em banco isolado para não remover dados
do ambiente de desenvolvimento.

## Verificação

```bash
curl http://localhost:${API_PORT:-8000}/api/v1/health
curl http://localhost:${API_PORT:-8000}/api/v1/ready
make test-infrastructure
```

`/health` comprova que o processo HTTP responde. `/ready` retorna `200` somente
quando banco, extensão vector, Redis, MinIO e bucket estão disponíveis. Em caso
de falha retorna `503` sem expor credenciais ou mensagens internas.

## Portas

As portas externas são configuráveis por `API_PORT`, `DB_PORT`, `REDIS_PORT`,
`MINIO_PORT` e `MINIO_CONSOLE_PORT`. Os endereços usados entre containers
permanecem `db:5432`, `redis:6379` e `minio:9000`.
