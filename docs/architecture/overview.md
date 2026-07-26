# Visão da arquitetura

O projeto usa quatro anéis simples:

```text
HTTP entrypoints -> application use cases -> domain
                         ^                 ^
                         |                 |
                  infrastructure -> contracts
```

`app/users/domain` contém entidades, value objects, exceções e contratos. A
aplicação transforma entradas em operações de negócio e devolve DTOs simples.
A infraestrutura traduz esses objetos para SQLAlchemy e PostgreSQL. O FastAPI
somente valida o transporte, resolve casos de uso e converte respostas.

`app/bootstrap.py` é o composition root. Ele é o único lugar que conhece a
implementação concreta do repositório e registra as dependências no Punq.
