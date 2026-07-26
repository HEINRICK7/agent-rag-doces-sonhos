# API externa de produtos

Status: **diagnóstico em andamento — integração ainda não autorizada**.

Este documento registra somente fatos confirmados sobre a fonte externa. Campos
desconhecidos permanecem explícitos para impedir que o cliente seja desenvolvido
com suposições.

## Acesso

| Item | Estado | Valor |
| --- | --- | --- |
| URL base | não informado | — |
| Ambiente de homologação | não informado | — |
| Autenticação | não informada | — |
| Endpoint de produtos | não informado | — |
| Rate limit | não informado | — |
| Timeout recomendado | não informado | — |

Credenciais e tokens nunca devem ser adicionados a este documento. Use variáveis
de ambiente e registre aqui somente o nome dos headers ou o mecanismo de
autenticação.

## Contratos que precisam de payload real

- listagem de produtos;
- detalhe de um produto;
- paginação vazia, inicial e final;
- produto indisponível;
- produto sem imagem ou descrição;
- erros `401`, `403`, `404`, `429` e `5xx`;
- resposta inválida ou incompleta.

## Perguntas obrigatórias

1. A paginação usa página, offset, cursor ou link?
2. O identificador externo é estável?
3. Preço é inteiro, decimal ou texto? Em qual moeda?
4. Estoque representa quantidade ou apenas disponibilidade?
5. Imagens são públicas, assinadas ou expiram?
6. Existe data de alteração, versão, hash ou ETag?
7. Produtos removidos deixam de aparecer ou recebem status?
8. Há categorias hierárquicas?
9. Campos desconhecidos podem aparecer sem versionamento?
10. Existe webhook ou a sincronização precisa ser consultiva?

## Evidências aguardadas

- [ ] documentação oficial ou coleção da API;
- [ ] URL base de homologação;
- [ ] mecanismo de autenticação;
- [ ] payloads reais anonimizados;
- [ ] regras de paginação e filtros;
- [ ] limites e política de retry;
- [ ] exemplos de erro.

## Riscos iniciais

- ausência de identificador estável pode impedir upsert idempotente;
- ausência de versão ou data de alteração pode exigir comparação por hash;
- URLs temporárias de imagem podem exigir cópia para MinIO;
- preço sem moeda ou precisão definida pode gerar perda de informação;
- ausência de sinal de remoção exige política de desativação local.
