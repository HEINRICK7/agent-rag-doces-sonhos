# DOCES & SONHOS — ROADMAP MODULAR DE DESENVOLVIMENTO

## API externa, BFF, catálogo, RAG, agentes e CRM

Este documento é a fonte única de verdade do desenvolvimento e do painel
**Roadmap modular** no Deep Map. A plataforma será construída em módulos
sequenciais desde a conexão com a API externa de produtos até o atendimento por
IA e o CRM.

O agente só pode avançar quando o módulo atual estiver implementado, testado,
documentado e sem pendências bloqueantes.

Legenda:

- `[ ]` planejado;
- `[~]` em desenvolvimento;
- `[x]` concluído e validado;
- `[!]` bloqueado;
- `[-]` não aplicável;
- `[?]` precisa de decisão.

## Arquitetura macro

```text
API externa
→ Integration API
→ Ingestão
→ Validação e normalização
→ PostgreSQL
→ MinIO
→ Documentos de produto
→ Embeddings
→ pgvector
→ Busca estruturada + RAG
→ Tools
→ LangGraph
→ Agente vendedor
→ Redis
→ Customer BFF
→ Frontend do cliente

Eventos
→ Analytics
→ Admin BFF
→ CRM
```

## Contratos dos BFFs

### Customer BFF

Atende exclusivamente o frontend do cliente: recebe mensagens, cria ou recupera
sessões, aciona o LangGraph, agrega texto, produtos, imagens, preços e
disponibilidade, devolve um contrato estável, registra eventos e oculta os
serviços internos.

### Admin BFF

Atende exclusivamente o CRM: dashboard, produtos, métricas, sincronizações,
falhas, perguntas sem resposta, produtos mais e menos buscados, reindexação e
operações administrativas.

### Integration API

Atende operações técnicas protegidas: testar conexão externa, iniciar e
consultar sincronizações, reprocessar falhas e reindexar produtos.

## MÓDULO 00 — Diagnóstico e contratos [~]

### Objetivo

Entender a API externa e definir contratos antes de implementar a integração.

### Tarefas

- [x] Identificar URL base e autenticação no código da origem.
- [~] Capturar payloads reais: exemplos confirmados; chamada ao vivo pendente.
- [x] Mapear paginação, filtros e tratamento defensivo de rate limit.
- [x] Mapear IDs, preço, disponibilidade e imagens.
- [x] Registrar campos obrigatórios e opcionais.
- [x] Documentar inconsistências e riscos.
- [x] Definir o contrato interno de entrada do produto.
- [x] Criar `docs/integrations/external-api.md`.
- [x] Criar `docs/contracts/product-contract.md`.
- [x] Registrar o contexto inicial da arquitetura.

### Gate

- [ ] Resposta da API em execução documentada.
- [x] Autenticação e paginação compreendidas.
- [x] Campos críticos mapeados.
- [x] Riscos registrados.

## MÓDULO 01 — Fundação da aplicação [x]

### Objetivo

Consolidar FastAPI, Clean Architecture, SOLID, Punq, SQLAlchemy e unittest.

### Tarefas

- [x] Criar estrutura modular inicial.
- [x] Configurar FastAPI e health check.
- [x] Configurar Punq.
- [x] Configurar Settings e logs.
- [x] Configurar tratamento global de erros.
- [x] Configurar Ruff.
- [x] Configurar e aprovar MyPy estrito.
- [x] Configurar unittest.
- [x] Criar README e documentação da fundação.

### Gate

- [x] API inicia no ambiente Docker.
- [x] Health retorna 200 nos testes.
- [x] Ruff passa.
- [x] MyPy passa.
- [x] `unittest discover` executa 26 testes com sucesso.

## MÓDULO 02 — Infraestrutura local [x]

### Objetivo

Disponibilizar API, PostgreSQL com pgvector, Redis e MinIO em ambiente
reproduzível.

### Tarefas

- [x] Criar Dockerfile.
- [x] Criar `compose.yml`.
- [x] Configurar PostgreSQL.
- [x] Habilitar pgvector.
- [x] Configurar Redis.
- [x] Configurar MinIO e buckets.
- [x] Criar volumes persistentes.
- [x] Configurar health checks.
- [x] Criar `.env.example`.
- [x] Validar conexões reais da API.

### Gate

- [x] Todos os containers estão saudáveis.
- [x] API acessa PostgreSQL, Redis e MinIO.
- [x] pgvector está disponível.
- [x] Volumes persistem dados.

## MÓDULO 03 — Cliente da API externa [~]

### Tarefas

- [x] Criar cliente, autenticação, schemas, exceções e retry em `ingestion`.
- [x] Implementar timeout, retry limitado, paginação e headers.
- [x] Propagar correlation ID.
- [x] Tratar 4xx, 5xx e JSON inválido.
- [x] Criar cliente fake e testes com `unittest.mock`.

### Gate

- [ ] Conexão real validada.
- [x] Paginação e erros testados.
- [x] Cliente substituível por fake.
- [x] Cliente não salva, normaliza ou contém regra de negócio.

## MÓDULO 04 — Mapeamento externo para interno [x]

### Tarefas

- [x] Criar schemas externos e DTO interno.
- [x] Mapear nomes, tipos, categorias, status e imagens.
- [x] Mapear preço e disponibilidade sem inventar moeda ou estoque.
- [x] Registrar campos ignorados.
- [x] Testar payload incompleto e campos desconhecidos.

### Gate

- [x] Domínio não depende do payload externo.
- [x] Mapper testado.
- [x] Contratos documentados.

## MÓDULO 05 — Pipeline de ingestão [ ]

### Fluxo

```text
StartCatalogSync
→ FetchProductsPage
→ MapExternalProduct
→ ValidateAndNormalizeProduct
→ UpsertProduct
→ ProcessProductImage
→ IndexProductDocument
→ RegisterSyncResult
```

### Tarefas

- [ ] Criar caso de uso e entidade de execução da sincronização.
- [ ] Registrar status, início, fim, recebidos, processados e falhas.
- [ ] Percorrer todas as páginas sem perder o lote por falha de item.
- [ ] Impedir execução concorrente.
- [ ] Permitir reprocessamento.
- [ ] Criar testes.

### Gate

- [ ] Execução completa registrada.
- [ ] Falha isolada não perde o lote.
- [ ] Concorrência controlada.

## MÓDULO 06 — Validação e normalização [ ]

### Tarefas

- [ ] Normalizar nome, descrição, preço, categoria e disponibilidade.
- [ ] Normalizar unidade, URLs, imagens e identificador externo.
- [ ] Tratar textos vazios e espaços.
- [ ] Validar ID, preço e nome.
- [ ] Definir fallback de descrição.
- [ ] Registrar rejeições e testar cada regra.

### Gate

- [ ] Inválidos são rejeitados de forma controlada.
- [ ] Válidos geram um único formato interno.
- [ ] Regras cobertas por testes.

## MÓDULO 07 — Domínio de catálogo [ ]

### Tarefas

- [ ] Criar `Product`, `Category`, `ProductImage`, `ProductAvailability` e `Money`.
- [ ] Exigir ID e nome.
- [ ] Impedir preço negativo.
- [ ] Tornar disponibilidade explícita.
- [ ] Implementar ativação, desativação e última sincronização.
- [ ] Proteger dados críticos durante atualizações externas.

### Gate

- [ ] Domínio não importa FastAPI, SQLAlchemy ou MinIO.
- [ ] Cobertura do domínio acima de 90%.

## MÓDULO 08 — PostgreSQL e SQLAlchemy [ ]

### Tarefas

- [ ] Criar tabelas de produtos, categorias, imagens, execuções e erros.
- [ ] Criar modelos SQLAlchemy 2.0 e migrations Alembic.
- [ ] Criar mappers e contratos de repositório.
- [ ] Implementar `SqlAlchemyProductRepository`.
- [ ] Implementar upsert por ID externo, índices e constraints.
- [ ] Criar testes de integração.

### Gate

- [ ] Migration sobe e desce.
- [ ] Upsert não duplica.
- [ ] Rollback funciona.
- [ ] Testes passam.

## MÓDULO 09 — Sincronização incremental [ ]

### Tarefas

- [ ] Escolher hash, data externa, versão, ETag ou comparação de campos.
- [ ] Detectar produto novo, alterado, inalterado e removido.
- [ ] Definir política de remoção.
- [ ] Evitar reindexação desnecessária.
- [ ] Registrar diferenças.
- [ ] Testar idempotência.

### Gate

- [ ] Execuções repetidas não duplicam.
- [ ] Inalterados não reprocessam.
- [ ] Alterações são detectadas.

## MÓDULO 10 — Imagens e MinIO [ ]

### Tarefas

- [?] Escolher cópia, URL externa ou estratégia híbrida.
- [ ] Criar contrato `ImageStorage` e implementação MinIO.
- [ ] Baixar com timeout e validar content type e tamanho.
- [ ] Calcular hash, evitar duplicidade e criar nome seguro.
- [ ] Persistir metadados e definir imagem principal.
- [ ] Criar fallback e testes.

### Gate

- [ ] Upload funciona.
- [ ] Imagem inválida é rejeitada.
- [ ] Duplicidade é controlada.
- [ ] Produto recupera imagens.

## MÓDULO 11 — Documentos de produto [ ]

### Tarefas

- [ ] Criar `ProductDocument` e template canônico.
- [ ] Incluir metadados filtráveis.
- [ ] Versionar documento e calcular hash.
- [ ] Impedir documento vazio.
- [ ] Testar geração e mudanças relevantes.

### Gate

- [ ] Documento é consistente.
- [ ] Metadados são filtráveis.
- [ ] Mudança relevante altera o hash.

## MÓDULO 12 — Embeddings [ ]

### Tarefas

- [ ] Criar contrato `EmbeddingProvider`.
- [ ] Implementar provedor inicial substituível.
- [ ] Suportar batch e validar dimensão.
- [ ] Tratar timeout e rate limit.
- [ ] Registrar modelo e versão.
- [ ] Criar fake e testes.

### Gate

- [ ] Provedor é substituível.
- [ ] Dimensão é validada.
- [ ] Erros são tratados.

## MÓDULO 13 — pgvector [ ]

### Tarefas

- [ ] Criar migration de `product_documents`.
- [ ] Persistir conteúdo, hash, embedding, modelo e metadados.
- [ ] Criar `VectorRepository`.
- [ ] Implementar upsert, similaridade, filtros, atualização e remoção.
- [ ] Criar índice vetorial e testes de ranking.

### Gate

- [ ] Documento indexado é recuperado.
- [ ] Disponibilidade filtra.
- [ ] Reindexação atualiza o vetor.

## MÓDULO 14 — Busca estruturada [ ]

### Tarefas

- [ ] Filtrar nome, categoria, preço, disponibilidade, tamanho e sabor.
- [ ] Filtrar promoção, entrega e tags.
- [ ] Criar `SearchProductsUseCase`.
- [ ] Implementar paginação, ordenação e combinação de filtros.
- [ ] Garantir queries seguras e documentar contrato.

### Gate

- [ ] Consultas exatas e filtros combinados funcionam.
- [ ] Indisponíveis podem ser excluídos.
- [ ] Paginação é consistente.

## MÓDULO 15 — Recuperação semântica [ ]

### Tarefas

- [ ] Criar `RetrieveProductsUseCase`.
- [ ] Gerar embedding da consulta e consultar pgvector.
- [ ] Aplicar filtros, top-k e score mínimo.
- [ ] Combinar busca semântica e estruturada.
- [ ] Testar consultas reais e registrar ausência de resultado.

### Gate

- [ ] Resultados são relevantes.
- [ ] Score baixo não produz falsa resposta.
- [ ] Disponibilidade é respeitada.

## MÓDULO 16 — Tools do agente [ ]

### Tarefas

- [ ] Criar `search_products` e `get_product_details`.
- [ ] Criar `get_product_images` e `check_product_availability`.
- [ ] Criar `recommend_products` e `compare_products`.
- [ ] Validar entradas e estruturar saídas.
- [ ] Fazer tools chamarem casos de uso, nunca SQL ou MinIO diretamente.
- [ ] Criar erros previsíveis e testes.

### Gate

- [ ] Schemas e testes existem.
- [ ] Dados não são inventados.
- [ ] Indisponibilidade é explícita.

## MÓDULO 17 — Redis e memória [ ]

### Tarefas

- [ ] Criar `ConversationRepository` e implementação Redis.
- [ ] Persistir sessão, histórico, preferências e restrições.
- [ ] Persistir produtos apresentados e selecionados.
- [ ] Implementar TTL, serialização e limite de histórico.
- [ ] Isolar sessões e criar fallback.
- [ ] Criar testes.

### Gate

- [ ] Sessão é recuperada e isolada.
- [ ] TTL funciona.
- [ ] Falha é tratada.

## MÓDULO 18 — LangGraph [ ]

### Tarefas

- [ ] Definir estado, nós e transições.
- [ ] Implementar recebimento, memória, intenção e reescrita.
- [ ] Implementar busca, RAG, supervisão e resposta.
- [ ] Salvar memória e registrar eventos.
- [ ] Cobrir saudação, busca, detalhe, comparação e recomendação.
- [ ] Cobrir indisponibilidade, fora de escopo e erro recuperável.
- [ ] Limitar execução, impedir loops, registrar traces e criar fallback.

### Gate

- [ ] Rotas são previsíveis.
- [ ] Não há loop.
- [ ] Fallback e persistência funcionam.

## MÓDULO 19 — Agente vendedor [ ]

### Tarefas

- [ ] Entender o pedido e perguntar quando faltar contexto.
- [ ] Buscar, recomendar e comparar produtos.
- [ ] Exibir preço, imagem e disponibilidade reais.
- [ ] Não inventar dados.
- [ ] Reconhecer ausência de resultado.
- [ ] Retornar mensagem, produtos, ações, session ID e trace ID.

### Gate

- [ ] Agente usa tools.
- [ ] Preço, imagem e disponibilidade vêm das fontes corretas.
- [ ] Testes conversacionais passam.

## MÓDULO 20 — Customer BFF [ ]

### Tarefas

- [ ] Expor mensagens, sessões, detalhes de produto e eventos.
- [ ] Validar entrada e resolver sessão.
- [ ] Acionar o grafo.
- [ ] Agregar texto, produto, preço e imagem.
- [ ] Padronizar saída, eventos, rate limit e erros.
- [ ] Criar testes de API.

### Gate

- [ ] Uma chamada principal atende cada mensagem.
- [ ] Contrato está documentado.
- [ ] Testes passam.

## MÓDULO 21 — Frontend do cliente [ ]

### Tarefas

- [ ] Definir stack React/Next.js e gerenciamento de dados.
- [ ] Criar chat, lista de mensagens e indicador de digitação.
- [ ] Criar cards, carrossel, ações rápidas, preço e disponibilidade.
- [ ] Preservar sessão e tratar erros.
- [ ] Acessar somente o Customer BFF.

### Gate

- [ ] Conversa e produtos funcionam.
- [ ] Sessão é preservada.
- [ ] Erros são tratados.

## MÓDULO 22 — Eventos e analytics [ ]

### Tarefas

- [ ] Modelar início, pergunta, busca, resultado e recomendação.
- [ ] Modelar visualização, seleção, disponibilidade e encerramento.
- [ ] Criar entidade, repositório e persistência.
- [ ] Registrar session ID, product ID e timestamp.
- [ ] Garantir privacidade, agregações e testes.

### Gate

- [ ] Eventos são registrados sem bloquear o chat.
- [ ] Métricas são calculáveis.
- [ ] Privacidade está documentada.

## MÓDULO 23 — Admin BFF [ ]

### Tarefas

- [ ] Expor dashboard, produtos e detalhes.
- [ ] Expor produtos mais buscados, baixo interesse e perguntas sem resposta.
- [ ] Expor execuções de sincronização.
- [ ] Permitir iniciar sincronização e reindexar produto.
- [ ] Paginar consultas e preparar autenticação.

### Gate

- [ ] Admin BFF é separado do Customer BFF.
- [ ] Contratos são próprios.
- [ ] Sincronização é acompanhável.

## MÓDULO 24 — Frontend CRM [ ]

### Tarefas

- [ ] Criar dashboard, produtos, detalhes, sincronizações e falhas.
- [ ] Exibir mais buscados, menos buscados e perguntas sem resposta.
- [ ] Exibir conversas e recomendações.
- [ ] Exibir conversas, buscas, recomendações, seleção e falhas.
- [ ] Implementar filtros, estados vazios e tratamento de erros.
- [ ] Acessar somente o Admin BFF.

### Gate

- [ ] Dados são rastreáveis.
- [ ] Filtros e estados vazios funcionam.
- [ ] Erros são tratados.

## MÓDULO 25 — Observabilidade [ ]

### Tarefas

- [ ] Padronizar logs, correlation ID, trace ID, duração e status.
- [ ] Observar sincronização e falhas externas.
- [ ] Observar embeddings, pgvector, Redis e MinIO.
- [ ] Observar traces LangGraph e consumo de modelo.
- [ ] Registrar consultas sem resultado.

### Gate

- [ ] Mensagem é rastreável ponta a ponta.
- [ ] Sincronização é auditável.
- [ ] Erros são contextualizados e segredos protegidos.

## MÓDULO 26 — Segurança [ ]

### Tarefas

- [ ] Autenticar Admin BFF e proteger Integration API.
- [ ] Configurar CORS e rate limit.
- [ ] Validar payloads e proteger secrets.
- [ ] Mascarar logs e revisar sessões.
- [ ] Revisar dependências, SQL, prompts e tools.

### Gate

- [ ] Cliente não acessa admin.
- [ ] Integração não é pública.
- [ ] Secrets ficam fora do código.
- [ ] Tools não executam ações arbitrárias.

## MÓDULO 27 — Testes ponta a ponta [ ]

### Cenários

- [ ] Produto encontrado da API externa até a resposta do chat.
- [ ] Produto inexistente gera resposta segura e evento.
- [ ] Alteração de preço sincroniza, reindexa e aparece no chat.
- [ ] API externa indisponível preserva o catálogo atual.
- [ ] Redis indisponível usa fallback sem perder o catálogo.

### Gate

- [ ] Cenários passam de forma repetível.
- [ ] Ambiente limpo funciona.
- [ ] Falhas não corrompem dados.

## MÓDULO 28 — Deploy e operação [ ]

### Tarefas

- [ ] Criar imagem de produção e configurar variáveis.
- [ ] Automatizar migrations e volumes.
- [ ] Configurar proxy reverso e HTTPS.
- [ ] Definir backup, restore e rollback.
- [ ] Configurar health checks, restart e logs.
- [ ] Criar runbook.

### Gate

- [ ] Deploy é reproduzível.
- [ ] Backup e restore são testados.
- [ ] Rollback está documentado.

## MÓDULO 29 — Auditoria final [ ]

### Checklist

- [ ] API externa e contratos estão isolados.
- [ ] Pipeline é idempotente.
- [ ] Catálogo, imagens e documentos funcionam.
- [ ] Embeddings e pgvector funcionam.
- [ ] Busca estruturada e semântica funcionam.
- [ ] Tools usam casos de uso.
- [ ] LangGraph controla o fluxo.
- [ ] Redis mantém sessões.
- [ ] Customer BFF atende o cliente.
- [ ] Admin BFF atende o CRM.
- [ ] Eventos, observabilidade e segurança foram validados.
- [ ] Testes unitários, integração e E2E passam.
- [ ] Documentação está atualizada.

## Gate obrigatório entre módulos

- [ ] Implementação concluída.
- [ ] Contratos documentados.
- [ ] Testes unitários criados.
- [ ] Testes de integração criados quando aplicável.
- [ ] Testes passando.
- [ ] Ruff passando.
- [ ] MyPy passando.
- [ ] Migrations validadas quando aplicável.
- [ ] Logs adicionados quando aplicável.
- [ ] Documentação atualizada.
- [ ] Nenhuma credencial adicionada.
- [ ] Nenhum import proibido.
- [ ] Nenhum problema bloqueante.

## Regra de ouro

```text
Frontend não acessa API externa, banco, Redis, MinIO ou LangGraph.
Customer BFF não implementa regra de catálogo.
Admin BFF não executa SQL diretamente.
Agentes não acessam infraestrutura diretamente.
Tools chamam casos de uso.
Casos de uso dependem de contratos.
Infraestrutura implementa contratos.
Domínio não conhece frameworks.
```
