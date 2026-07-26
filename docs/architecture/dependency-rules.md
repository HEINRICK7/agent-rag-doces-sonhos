# Regras de dependência

Permitido:

- entrypoints importam application e schemas de transporte;
- application importa contratos e objetos do domain;
- infrastructure importa contratos/domain e bibliotecas externas;
- bootstrap importa todas as implementações necessárias para composição.

Proibido:

- domain importar FastAPI, Pydantic, SQLAlchemy, Punq ou settings;
- application importar FastAPI ou SQLAlchemy;
- casos de uso instanciar repositórios;
- endpoints acessarem sessões ou modelos ORM diretamente.

O teste `scripts/check_architecture.py` verifica os imports mais sensíveis.
