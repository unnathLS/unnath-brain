# Validação do MVP

Data: 2026-10-03.

- Imagem `unnath-brain:test` construída com sucesso.
- Suíte automatizada: 13 testes aprovados; 1 aviso de depreciação em dependência do Starlette.
- Dois consumidores autenticados (`unnatha` e `niyam`) recuperaram `DEC-TEST-001`.
- Context pack referenciou ID, caminho e hash da decisão.
- Proposta E2E foi criada como `pending`, com autor e timestamp; a decisão original manteve o mesmo hash.
- O índice foi removido isoladamente e reconstruído de dois Markdown canônicos durante o E2E (decisão + proposta temporária).
- Apó restart do container, healthcheck retornou `ok` e `DEC-TEST-001` manteve o mesmo hash.
- `docker compose config --quiet` validou a configuração.
- Containers temporários do teste foram removidos; containers externos permaneceram intactos.

