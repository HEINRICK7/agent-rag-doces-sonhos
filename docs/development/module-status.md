# Status modular

O status detalhado e a sequência de desbloqueio agora vivem em
[`roadmap.md`](roadmap.md). Esse arquivo é a fonte única de verdade consumida
pelo Deep Map.

## Estado atual

- Fundação funcional com API, módulo de usuários, SQLAlchemy, Alembic, Docker,
  testes, CI e documentação.
- 45 testes na suíte padrão, teste real de infraestrutura aprovado e cobertura
  total acima do gate de 80%.
- Ruff, MyPy estrito, formatação e regras arquiteturais aprovados.
- PostgreSQL, pgvector 0.8.0, Redis e MinIO validados em containers saudáveis.
- Alembic está em `0002_enable_pgvector (head)`.
- O endpoint `/api/v1/ready` comprova banco, pgvector, Redis, MinIO e bucket.
- O contrato da API Doces Sonhos foi confirmado no código-fonte da origem:
  base local, rotas, filtros, listas sem paginação e schemas conhecidos.
- O cliente externo possui autenticação opcional, timeout, retry, correlation
  ID, erros explícitos, filtros confirmados e fake para testes.
- O mapper externo → interno está concluído, preserva `Decimal` e timestamps,
  tolera evolução de campos e não acopla aplicação ou domínio ao Pydantic.
- A validação contra a API em execução continua pendente; moeda, política de
  remoção e permanência das imagens ainda exigem decisão.
