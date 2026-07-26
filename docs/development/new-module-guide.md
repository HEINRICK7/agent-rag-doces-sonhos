# Guia para novos módulos

1. Crie o domínio puro: entidade, value objects, exceções e um `Protocol` de
   repositório.
2. Crie DTOs e casos de uso que recebam o protocolo no construtor.
3. Crie modelos ORM, mappers e uma implementação do protocolo na infraestrutura.
4. Registre a implementação e os casos de uso em `app/bootstrap.py`.
5. Adicione schemas, dependências e router HTTP somente depois do caso de uso.
6. Crie testes unitários com repositório em memória e testes de integração para
   o adapter real.
7. Rode `make check`, atualize documentação e verifique as regras de dependência.

Não copie regras de negócio para endpoints nem crie um `Service` genérico com
responsabilidades de vários casos de uso.
