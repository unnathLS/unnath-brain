# Validação do MVP

Data: 2026-10-03.

- Imagem `unnath-brain:test` construída com sucesso.
- Suíte automatizada: 18 testes aprovados; 1 aviso de depreciação em dependência do Starlette.
- Dois consumidores autenticados (`unnatha` e `niyam`) recuperaram `DEC-TEST-001`.
- Context pack referenciou ID, caminho e hash da decisão.
- Proposta E2E foi criada como `pending`, com autor e timestamp; a decisão original manteve o mesmo hash.
- O índice foi removido isoladamente e reconstruído de dois Markdown canônicos durante o E2E (decisão + proposta temporária).
- Apó restart do container, healthcheck retornou `ok` e `DEC-TEST-001` manteve o mesmo hash.
- `docker compose config --quiet` validou a configuração.
- E2E de endurecimento: context pack com `project` e `mission` recuperou `DEC-TEST-001`; consulta composta apenas por sintaxe FTS retornou HTTP 422.
- Validação de governança impede `pending` fora de propostas e impede propostas com status diferente de `pending`.
- Referência Git só é atribuída a documentos rastreados e sem alterações em relação ao `HEAD`.
- Validação de distribuição: um clone limpo de `origin/development` gerou a imagem Docker, compilou o pacote, passou em `pip check` e aprovou os 18 testes.
- Prontidão operacional: 21 testes aprovados; `brain_gateway.cli validate` confirmou os Markdown sem alterar o índice; `/health` confirmou o índice com `documents: 1`.
- Ciclo autônomo de prontidão: 25 testes aprovados; propostas inválidas são rejeitadas antes da escrita, falhas do SQLite retornam HTTP 503 de forma consistente e o healthcheck detecta divergência entre documentos e FTS.
- Revisão final de autenticação: 33 testes aprovados; configuração rejeita identidades vazias, tokens duplicados, espaços periféricos e tokens com menos de 32 caracteres; compilação e `pip check` aprovados.
- Persistência de propostas: 35 testes aprovados; escrita temporária, `fsync` e publicação atômica impedem que rebuilds observem Markdown parcial e removem temporários após falhas.
- Containers temporários do teste foram removidos; containers externos permaneceram intactos.
