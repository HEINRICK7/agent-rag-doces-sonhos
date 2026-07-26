# Guia de testes

Testes unitários usam `unittest.TestCase` para código síncrono e
`unittest.IsolatedAsyncioTestCase` para código assíncrono. Eles não dependem de
PostgreSQL; use `InMemoryUserRepository` ou mocks.

Testes de integração exercitam mappers, repositórios, migrations e HTTP. O
repositório desta fundação usa SQLite assíncrono isolado nos testes rápidos; o
ambiente Docker deve ser usado para validar PostgreSQL e Alembic.

```bash
python -m unittest discover -s tests -p "test_*.py"
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```
