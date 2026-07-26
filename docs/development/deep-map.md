# Integração com o Deep Map

## Comportamento

O Deep Map analisa esta pasta localmente e não executa o código do projeto. Ao
criar, editar, renomear ou remover um arquivo textual relevante, o watcher da
extensão agenda uma nova análise e publica outro snapshot para a interface.

Os arquivos Markdown alimentam duas áreas:

1. **Documentação**: todos os `.md` e `.mdx` aparecem com caminho, conteúdo,
   headings e atalho para abertura no VS Code.
2. **Roadmap modular**: headings no formato `MÓDULO NN — Nome`, marcadores de
   status e checklists são transformados em módulos, tarefas, progresso e
   bloqueios sequenciais.

O snapshot também registra `createdAt` e `updatedAt` em arquivos, componentes e
eventos. A Timeline usa esses eventos e abre por padrão no período **Hoje**; a
conversão da data é feita no fuso local da interface.

Dados de negócio vindos da API não substituem datas do workspace. O contrato de
ingestão preserva separadamente `source_created_at` e `source_updated_at` para
que os próximos módulos possam mostrar quando produtos, categorias e
subcategorias surgiram ou mudaram na origem.

## Clean Architecture

Os caminhos do código são classificados automaticamente:

- `domain/` → Domínio;
- `application/` → Aplicação;
- `entrypoints/` → Entrypoints;
- `infrastructure/` → Infraestrutura;
- `app/bootstrap.py` → Composição.

Essa classificação alimenta a seção **Clean Architecture** da sidebar.

O cliente externo, seus métodos, schemas e mapper aparecem como nós de
Infraestrutura; os DTOs e o contrato `ProductSource` aparecem como Aplicação.
Imports e chamadas detectáveis viram relações automaticamente. Um fluxo de
execução completo somente será criado quando o Módulo 05 adicionar o caso de
uso que orquestra origem, mapper e destinos.

## Atualização do roadmap

Edite somente
[`roadmap.md`](roadmap.md). O Deep Map usa os marcadores abaixo:

```text
[ ] planejado
[~] em desenvolvimento
[x] concluído e validado
[!] bloqueado
[-] não aplicável
[?] precisa de decisão
```

Um módulo planejado é mostrado como bloqueado enquanto houver um módulo
anterior não concluído. Ao concluir e salvar o módulo anterior, o próximo é
liberado automaticamente na interface.

## Atualização manual

Quando necessário, execute o comando `Deep Map: Reanalisar workspace` pela
paleta do VS Code. A atualização automática continua sendo o caminho padrão.

## Versão validada

A integração foi validada com o Deep Map `0.3.0`: sidebar Clean Architecture,
roadmap Markdown, desbloqueio sequencial e abertura das evidências no VS Code.
