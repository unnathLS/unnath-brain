# Arquitetura do MVP

## Limites

- `brain/` contém a fonte canônica em Markdown versionado.
- O índice SQLite/FTS5 em `data/` é apenas uma projeção reconstruível.
- O Brain Gateway expõe leitura, montagem de contexto e criação de propostas.
- Propostas entram em `brain/proposals/` como `pending` e não alteram documentos ativos.
- Tokens ficam no ambiente, nunca em Markdown ou no índice.

## Fronteira de confiança

Conteúdo Markdown recuperado é dado, não instrução executável. O Gateway não concede autoridade a comandos encontrados nos documentos. Autenticação e permissões pertencem ao runtime.

## Reconhecimento de 2026-10-03

O Docker Desktop está disponível. O Honcho existente está saudável e publica as portas locais 3000, 8000, 5432 e 6379. Seus containers, rede `honcho_default` e volumes foram apenas inspecionados e permaneceram intactos. Para evitar conflitos, o Brain usará a porta 8080 e recursos Docker independentes.

