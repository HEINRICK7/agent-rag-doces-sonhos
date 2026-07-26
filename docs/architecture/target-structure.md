# Estrutura modular alvo

Esta é a topologia planejada para a plataforma Doces & Sonhos. Ela orienta a
criação incremental dos módulos; diretórios futuros não devem ser criados
vazios apenas para simular progresso no Deep Map.

O nome do repositório atual é `agent-rag-doces-sonhos`. A referência original
usa `genai-commercial-platform`, mas a raiz lógica da aplicação permanece
`app/`.

```text
app/
├── main.py
├── shared/
│   ├── configuration/
│   │   ├── settings.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── minio.py
│   │   └── logging.py
│   ├── domain/
│   │   ├── exceptions.py
│   │   └── value_objects.py
│   └── infrastructure/
│       ├── database/
│       ├── cache/
│       ├── storage/
│       └── observability/
├── catalog/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── product.py
│   │   │   └── category.py
│   │   ├── value_objects/
│   │   │   ├── money.py
│   │   │   └── product_status.py
│   │   ├── repositories/product_repository.py
│   │   └── exceptions.py
│   ├── application/
│   │   ├── dto/
│   │   │   ├── product_input.py
│   │   │   └── product_output.py
│   │   ├── ports/image_storage.py
│   │   └── usecases/
│   │       ├── create_product.py
│   │       ├── get_product.py
│   │       ├── search_products.py
│   │       └── list_products.py
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── models.py
│   │   │   └── postgres_product_repository.py
│   │   └── storage/minio_image_storage.py
│   └── entrypoints/api/
│       ├── router.py
│       ├── schemas.py
│       └── dependencies.py
├── ingestion/
│   ├── domain/
│   │   ├── entities/
│   │   └── repositories/
│   ├── application/
│   │   ├── dto/
│   │   ├── ports/product_source.py
│   │   ├── exceptions.py
│   │   └── usecases/
│   │       ├── import_catalog.py
│   │       ├── normalize_product.py
│   │       ├── synchronize_images.py
│   │       └── index_product.py
│   ├── infrastructure/
│   │   ├── external_api/
│   │   │   ├── product_api_client.py
│   │   │   ├── schemas.py
│   │   │   └── mapper.py
│   │   └── jobs/catalog_sync_job.py
│   └── entrypoints/api/router.py
├── rag/
│   ├── domain/
│   │   ├── entities/product_document.py
│   │   └── repositories/vector_repository.py
│   ├── application/
│   │   ├── ports/
│   │   │   ├── embedding_provider.py
│   │   │   └── reranker.py
│   │   └── usecases/
│   │       ├── generate_product_document.py
│   │       ├── generate_embedding.py
│   │       ├── index_document.py
│   │       └── retrieve_products.py
│   └── infrastructure/
│       ├── embeddings/litellm_embedding_provider.py
│       └── vectorstore/pgvector_repository.py
├── chat/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   └── repositories/conversation_repository.py
│   ├── application/
│   │   ├── dto/
│   │   ├── ports/language_model.py
│   │   └── usecases/
│   │       ├── send_message.py
│   │       ├── get_conversation.py
│   │       └── recommend_products.py
│   ├── infrastructure/
│   │   ├── agents/
│   │   │   ├── seller_agent.py
│   │   │   ├── supervisor_agent.py
│   │   │   └── graph.py
│   │   ├── llm/litellm_provider.py
│   │   └── memory/redis_conversation_repository.py
│   └── entrypoints/api/
│       ├── router.py
│       └── schemas.py
├── crm/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── product_event.py
│   │   │   └── sales_metric.py
│   │   └── repositories/analytics_repository.py
│   ├── application/usecases/
│   │   ├── register_product_view.py
│   │   ├── register_recommendation.py
│   │   ├── get_most_requested_products.py
│   │   └── get_low_interest_products.py
│   ├── infrastructure/persistence/postgres_analytics_repository.py
│   └── entrypoints/api/router.py
└── health/entrypoints/api/router.py

tests/
├── unit/
│   ├── catalog/
│   ├── ingestion/
│   ├── rag/
│   ├── chat/
│   └── crm/
├── integration/
│   ├── database/
│   ├── redis/
│   ├── minio/
│   └── pgvector/
└── end_to_end/
    ├── test_catalog_flow.py
    └── test_chat_flow.py
```

## BFFs dentro dessa estrutura

- `ingestion/entrypoints/api` implementará a **Integration API**.
- `chat/entrypoints/api` implementará o **Customer BFF**.
- `crm/entrypoints/api` implementará o **Admin BFF**.

Essa associação mantém o desenho por capacidade de negócio sem criar uma
segunda árvore técnica para os BFFs.

## Regras de dependência

```text
entrypoints → application → domain
infrastructure ───────────→ domain contracts
bootstrap/composition → todas as implementações concretas
```

- Domínio não conhece frameworks.
- Aplicação conhece DTOs, casos de uso e contratos.
- Infraestrutura implementa contratos.
- Entrypoints validam transporte e chamam casos de uso.
- Tools e agentes nunca acessam infraestrutura diretamente.
