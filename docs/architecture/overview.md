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

## Fluxo de ingestão disponível

```text
StartCatalogSyncUseCase
  -> ProductSource.iter_pages
  -> ProductPipelineProcessor
       -> map_external_product
       -> NormalizeProductUseCase
       -> BuildProductFromImportUseCase
       -> Product
  -> CatalogSyncExecution
  -> CatalogSyncExecutionRepository
```

O caso de uso é responsável por paginação, correlação, contadores, isolamento de
falhas e concorrência. `ProductSource` e `CatalogItemProcessor` são portas da
aplicação. Hoje a implementação do processador valida e mapeia o payload externo;
em seguida o normalizador cria o contrato canônico e o builder produz o agregado
`Product`. Os próximos módulos acrescentam persistência, processamento de
imagens e indexação sem transferir essas responsabilidades para o orquestrador.

`app/catalog/domain` é um anel puro e contém entidades, value objects e
invariantes. O verificador arquitetural impede imports de FastAPI, HTTPX,
Pydantic, Punq e SQLAlchemy nesse diretório.
