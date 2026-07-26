# Contrato interno de produto

Status: **proposta v0 — aguarda validação contra payloads reais**.

O contrato interno não reproduz o formato da API externa. Ele representa os
dados necessários para catálogo, busca, RAG, atendimento e CRM.

## Product

| Campo | Tipo interno | Obrigatório | Regra |
| --- | --- | --- | --- |
| `id` | UUID | sim | gerado internamente |
| `external_id` | string | sim | estável e único por fonte |
| `name` | string | sim | normalizado e não vazio |
| `description` | string | não | recebe fallback documentado |
| `category` | CategoryReference | não | não depende do schema externo |
| `price` | Money | sim | nunca negativo |
| `availability` | ProductAvailability | sim | estado explícito |
| `images` | lista de ProductImage | não | principal identificada |
| `is_active` | boolean | sim | remoção externa não apaga histórico |
| `source_updated_at` | datetime | não | data fornecida pela origem |
| `last_synced_at` | datetime | sim | data da sincronização local |
| `source_hash` | string | não | usado quando não houver versão externa |

## Money

```text
amount: Decimal
currency: código ISO 4217
```

Não usar `float`. A precisão e a moeda padrão só serão fixadas após confirmar o
contrato externo.

## ProductAvailability

Estados internos propostos:

- `available`;
- `unavailable`;
- `out_of_stock`;
- `unknown`.

Quantidade de estoque, quando existir, deve ser um campo separado. Ausência de
quantidade não será interpretada automaticamente como indisponibilidade.

## ProductImage

| Campo | Tipo |
| --- | --- |
| `source_url` | string |
| `storage_key` | string opcional |
| `content_type` | string opcional |
| `checksum` | string opcional |
| `is_primary` | boolean |
| `position` | inteiro |

## Decisões pendentes

- moeda padrão;
- precisão monetária;
- política de produto removido;
- estratégia de imagem: externa, cópia ou híbrida;
- fallback da descrição;
- formato e hierarquia de categorias;
- mecanismo de detecção incremental;
- campos que o negócio protege contra sobrescrita externa.

## Gate de aprovação

- [ ] cada campo obrigatório possui origem confirmada;
- [ ] valores nulos e ausentes estão mapeados;
- [ ] preço e moeda estão comprovados;
- [ ] disponibilidade está mapeada;
- [ ] estratégia de imagens está decidida;
- [ ] payloads desconhecidos possuem política explícita;
- [ ] contrato revisado contra ao menos três payloads reais.
