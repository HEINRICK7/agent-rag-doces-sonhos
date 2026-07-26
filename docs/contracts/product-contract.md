# Contrato interno de produto

Status: **contrato de ingestão v1 implementado; entidade de catálogo pendente**.

O contrato interno não reproduz o Pydantic nem o formato da API externa. O
mapper da infraestrutura valida o transporte e entrega dataclasses imutáveis à
aplicação. `NormalizeProductUseCase` transforma essa entrada no formato canônico
antes dos estágios de persistência e indexação.

## ProductImportInput

| Campo | Tipo interno | Regra confirmada |
| --- | --- | --- |
| `external_id` | string | vem de `id`, UUID estável na origem |
| `name` | string | obrigatório e não vazio |
| `description` | string opcional | preserva ausência como `None` |
| `category_external_id` | string opcional | vem de `categoryId` |
| `subcategory_external_id` | string opcional | vem de `subcategoryId` |
| `is_active` | boolean | vem de `isActive` |
| `availability` | enum | derivado sem confundir ausência de estoque com indisponibilidade |
| `currency` | string opcional | somente quando a origem enviar |
| `stock_quantity` | Decimal opcional | somente quando a origem enviar |
| `price_options` | tupla | ao menos uma opção, com preço `Decimal` |
| `images` | tupla | imagem externa única vira imagem principal |
| `source_created_at` | datetime opcional | vem de `createdAt` |
| `source_updated_at` | datetime opcional | vem de `updatedAt` |
| `ignored_fields` | tupla de strings | registra campos externos desconhecidos |

## PriceOptionInput

```text
external_id: string opcional
label: string opcional
quantity: Decimal positivo
unit: string
price: Decimal não negativo
is_default: boolean
```

O schema externo usa `Decimal(10,2)`. `float` não é usado no contrato interno.
A API verificada não publica moeda; por isso o mapper não assume `BRL`.

Na normalização, preços são arredondados para duas casas com `ROUND_HALF_UP`,
quantidade deve ser positiva e existe exatamente uma opção padrão. Quando a
origem não marca uma opção, a primeira é escolhida; quando marca mais de uma,
somente a primeira permanece padrão.

## ProductAvailability

Mapeamento atual:

| Condição externa | Estado interno |
| --- | --- |
| `isActive == false` | `unavailable` |
| ativo e `stockQuantity == 0` | `out_of_stock` |
| ativo e `stockQuantity > 0` | `available` |
| ativo e estoque ausente | `unknown` |

`GET /products` retorna somente produtos ativos. O mapper suporta inativos para
detalhes, fixtures e futura evolução do contrato, mas a sincronização precisa de
uma política separada para detectar itens removidos.

## ProductImageInput

| Campo | Tipo | Regra |
| --- | --- | --- |
| `source_url` | string | URL fornecida pela origem |
| `is_primary` | boolean | `true` para a imagem única atual |
| `position` | — | a API atual fornece somente uma imagem, mantida como principal |

`storage_key`, checksum e metadados de mídia pertencem ao processamento de
imagem do pipeline, não ao mapper externo.

O normalizador aceita somente URL absoluta HTTP(S), remove fragmentos, elimina
duplicatas e garante que apenas a primeira imagem seja principal. Isso não
decide se o arquivo será mantido externamente ou copiado para o MinIO.

## Categoria e subcategoria

`CategoryImportInput` preserva `id`, `name`, `icon`, `image`, `isActive`,
`position`, `createdAt` e `updatedAt`.

`SubcategoryImportInput` preserva `id`, `name`, `categoryId`, `createdAt` e
`updatedAt`.

As referências continuam por ID externo nesta fronteira. A resolução para IDs
internos será responsabilidade do pipeline/repositório.

## Isolamento arquitetural

- Pydantic permanece em `ingestion.infrastructure.external_api`;
- aplicação recebe somente dataclasses e tipos da biblioteca padrão;
- domínio e catálogo não importam schemas da API;
- campos desconhecidos são tolerados e registrados;
- payload inválido produz `ExternalProductMappingError` explícito.

## Entidade de catálogo planejada

O Módulo 07 transformará a entrada normalizada em uma entidade persistível com:

- UUID interno;
- `external_id` único por fonte;
- preço/opções comerciais normalizadas;
- histórico sem exclusão física;
- `last_synced_at` e hash de origem;
- imagem externa, copiada ou híbrida conforme decisão;
- categoria resolvida para referência interna.

## Decisões pendentes

- moeda padrão para preços sem `currency`;
- política de produto removido ou desativado;
- estratégia de imagem: externa, cópia ou híbrida;
- campos protegidos contra sobrescrita externa.

## Regras de normalização decididas

- nomes e descrições usam Unicode NFKC, espaços internos únicos e sem bordas;
- nome e identificador externo vazios são rejeitados;
- descrição vazia vira `Descrição não informada.`;
- moeda é normalizada para três letras maiúsculas, sem moeda implícita;
- estoque negativo ou não finito é rejeitado;
- disponibilidade é derivada novamente de atividade e estoque;
- categoria e subcategoria vazias viram ausência explícita;
- preços e quantidades inválidos geram `ProductNormalizationError`;
- rejeições são registradas na execução sem interromper os demais produtos.

## Gate

- [x] campos obrigatórios da entrada possuem origem confirmada;
- [x] valores nulos e ausentes estão mapeados;
- [x] preço e precisão externa estão comprovados;
- [ ] moeda padrão está decidida;
- [x] disponibilidade possui mapeamento conservador;
- [ ] estratégia de imagens está decidida;
- [x] payloads desconhecidos possuem política explícita;
- [x] mapper está coberto por exemplos, ausências e payload inválido;
- [ ] contrato foi exercitado contra a API em execução.
