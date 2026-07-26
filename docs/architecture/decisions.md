# Decisões técnicas

## Estado inicial

- Python 3.12.3 disponível.
- Docker 29.1.3 disponível.
- `docker-compose` 1.x disponível; `docker compose` v2 não está instalado.
- Git 2.43.0 disponível.
- O diretório inicial estava vazio e sem repositório Git.

## Decisões

1. **FastAPI + Uvicorn**: fornecem uma entrada HTTP tipada e um servidor ASGI
   adequado para operações assíncronas.
2. **SQLAlchemy 2.0 + asyncpg**: ORM isolado na infraestrutura, com sessões
   assíncronas e PostgreSQL como banco principal.
3. **Alembic**: migrations versionadas e reproduzíveis.
4. **Punq**: composição centralizada em `app/bootstrap.py`; o domínio não conhece
   o container.
5. **unittest**: framework de testes obrigatório do projeto, incluindo sua variante
   assíncrona `IsolatedAsyncioTestCase`.
6. **Pydantic e pydantic-settings**: validação somente nas bordas/configuração; DTOs
   da aplicação permanecem objetos Python simples.
7. **Ruff, MyPy, Coverage.py e pre-commit**: qualidade automatizada sem adicionar
   pytest, que está fora da stack definida.
8. **PostgreSQL via Docker Compose**: ambiente local reproduzível sem credenciais
   reais versionadas.

## Limites arquiteturais

O domínio é Python puro. A aplicação depende de protocolos e DTOs. FastAPI e
SQLAlchemy ficam nas bordas. Casos de uso não criam repositórios nem sessões.
