# Status modular

O status detalhado e a sequência de desbloqueio agora vivem em
[`roadmap.md`](roadmap.md). Esse arquivo é a fonte única de verdade consumida
pelo Deep Map.

## Estado atual

- Fundação funcional com API, módulo de usuários, SQLAlchemy, Alembic, Docker,
  testes, CI e documentação.
- 26 testes na suíte padrão, teste real de infraestrutura aprovado e cobertura
  total de 92%.
- Ruff, MyPy estrito, formatação e regras arquiteturais aprovados.
- PostgreSQL, pgvector 0.8.0, Redis e MinIO validados em containers saudáveis.
- Alembic está em `0002_enable_pgvector (head)`.
- O endpoint `/api/v1/ready` comprova banco, pgvector, Redis, MinIO e bucket.
- Módulos específicos de catálogo, RAG e agente permanecem planejados e
  bloqueados pelo diagnóstico e pelos contratos da API externa.
