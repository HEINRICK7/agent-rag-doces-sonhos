# API externa de produtos

Status: **contrato confirmado no código-fonte; validação ao vivo pendente**.

O contrato foi conferido em 24 de julho de 2026 no repositório local
`../doces-sonhos-api`, por meio dos controllers, services, DTOs, schema Prisma e
referência Swagger. A API não estava disponível durante a primeira conferência,
portanto os fatos abaixo descrevem a implementação verificada, não uma captura
de ambiente.

## Acesso

| Item | Estado | Valor |
| --- | --- | --- |
| URL base local | confirmado | `http://localhost:3002` |
| Prefixo global | confirmado | nenhum; `/api` é apenas o Swagger |
| Autenticação nas rotas | não exigida no código verificado | `none` |
| Autenticação opcional | suportada pelo cliente | `Bearer` ou API key |
| Produtos | confirmado | `GET /products` |
| Paginação | confirmado | lista JSON direta, sem paginação |
| Filtros | confirmado | `search`, `categoryId`, `subcategoryId` |
| Rate limit | não encontrado no código verificado | cliente trata `429` defensivamente |
| Timeout local | decisão interna | 10 segundos por padrão |

Credenciais e tokens nunca devem ser adicionados a este documento. Ambientes
com autenticação na frente da API devem usar exclusivamente variáveis de
ambiente.

## Rotas confirmadas

| Método | Rota | Resultado |
| --- | --- | --- |
| `GET` | `/products` | lista direta de produtos ativos |
| `GET` | `/products/{id}` | detalhe de um produto ativo |
| `GET` | `/categories` | lista direta de categorias |
| `GET` | `/categories/{categoryId}/subcategories` | subcategorias da categoria |

`GET /products` aceita os filtros opcionais `search`, `categoryId` e
`subcategoryId`. Não existem `page`, `limit`, cursor ou envelope de paginação
na versão verificada.

## Contrato de produto confirmado

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | UUID em string | identificador externo estável |
| `name` | string | obrigatório |
| `description` | string ou `null` | opcional |
| `image` | string ou `null` | imagem única opcional |
| `categoryId` | UUID em string ou `null` | categoria opcional |
| `subcategoryId` | UUID em string ou `null` | subcategoria opcional |
| `isActive` | boolean | a listagem retorna somente ativos |
| `priceOptions` | lista | ao menos uma opção comercial |
| `createdAt` | datetime | disponível na origem |
| `updatedAt` | datetime | disponível na origem |

Cada item de `priceOptions` contém `id`, `label`, `quantity`, `unit`, `price` e
`isDefault`. O preço é `Decimal(10,2)` no schema Prisma e permanece `Decimal`
internamente.

`currency` e `stockQuantity` não existem no schema Prisma atualmente
verificado. O mapper aceita esses campos caso um ambiente ou uma versão futura
os envie, mas não inventa moeda nem estoque quando estiverem ausentes.

## Categorias e subcategorias

Categoria contém `id`, `name`, `icon`, `image`, `isActive`, `position`,
`createdAt` e `updatedAt`. Subcategoria contém `id`, `name`, `categoryId`,
`createdAt` e `updatedAt`.

## Cliente e mapper implementados

O `ProductApiClient` consome as listas diretas, aplica os filtros confirmados e
também consulta detalhe, categorias e subcategorias. Continuam disponíveis:

- autenticação opcional por bearer ou API key;
- timeout, retry exponencial limitado e `Retry-After`;
- propagação de `X-Correlation-ID`;
- proteção contra links de paginação de outra origem;
- erros distintos para autenticação, rate limit, indisponibilidade, outros 4xx
  e JSON inválido;
- fake substituível pelo contrato `ProductSource`.

O mapper externo → interno:

- preserva preço como `Decimal`;
- carrega IDs de categoria e subcategoria sem acoplar o domínio ao Pydantic;
- converte a imagem única em imagem principal;
- preserva `createdAt` e `updatedAt`;
- registra campos desconhecidos como evidência ignorada;
- não assume moeda ou estoque inexistentes.

Configuração local:

```dotenv
EXTERNAL_API_BASE_URL=http://localhost:3002
EXTERNAL_API_PRODUCTS_PATH=/products
EXTERNAL_API_AUTH_MODE=none
EXTERNAL_API_PAGINATION_MODE=none
```

Dentro do Docker, use `http://host.docker.internal:3002`; o Compose já registra
o alias `host-gateway`.

## Erros tratados

- `401` e `403`: credenciais rejeitadas quando existir autenticação frontal;
- `404`: produto ativo não encontrado;
- `429`: limite temporário, tratado defensivamente;
- `5xx`: indisponibilidade temporária;
- JSON inválido ou payload incompleto: erro explícito de transporte/mapeamento.

## Decisões ainda pendentes

1. Qual moeda deve ser associada aos preços sem `currency`?
2. A URL de imagem é permanente ou deve ser copiada para o MinIO?
3. Como detectar produto removido ou desativado, já que a listagem só expõe
   produtos ativos?
4. Há rate limit, autenticação frontal ou política de retry no ambiente real?
5. Existe webhook ou a sincronização será sempre consultiva?

## Evidências

- [x] código-fonte e referência Swagger;
- [x] URL base local;
- [x] mecanismo de autenticação das rotas verificadas;
- [x] exemplos de payload fornecidos no handoff;
- [x] regras de paginação e filtros;
- [x] exemplos e política interna para erros;
- [ ] resposta capturada da API em execução;
- [ ] limites do ambiente de produção.

## Riscos conhecidos

- a listagem somente de ativos exige política explícita de desativação local;
- preço sem moeda não pode se transformar em `Money` definitivo sem decisão de
  negócio;
- URLs temporárias de imagem podem exigir cópia para MinIO;
- campos opcionais podem surgir sem versionamento;
- o contrato no código-fonte pode divergir do ambiente até a validação ao vivo.
