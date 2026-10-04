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
- Validação da raiz canônica: 36 testes aprovados; raiz ausente ou apontando para arquivo encerra a validação com código 1, sem criar índice vazio aparentemente saudável.
- Distribuição após revisão final: clone limpo de `origin/development` construiu a imagem, compilou o pacote, passou em `pip check` e aprovou os 36 testes; diretório temporário removido após a validação.
- Runtime mínimo: alvo Docker `runtime` validado sem `pytest`, `httpx` ou pacote `tests`; alvo `test` aprovou 36 testes, compilação e `pip check`; configuração Compose aprovada usando explicitamente o runtime.
- Dependências reproduzíveis: build sem cache aprovado com backend e transitivas fixados em `constraints.txt`; teste de cobertura das distribuições instaladas, 37 testes, compilação e `pip check` aprovados; runtime permaneceu mínimo.
- Imagem base reproduzível: índice multi-arquitetura de `python:3.12-slim` fixado por digest após confirmação no registry; build sem cache, verificação automática do Dockerfile, 38 testes, compilação e `pip check` aprovados.
- Identidades auditáveis: atores aceitam somente 1 a 64 caracteres alfanuméricos, ponto, sublinhado ou hífen; espaços internos, quebras de linha, caminhos e nomes longos são rejeitados; 42 testes, compilação e `pip check` aprovados.
- Árvore canônica: decisões, procedimentos, conhecimento, projetos, companhia, agentes e propostas devem residir em seus diretórios correspondentes; `archive` e `inbox` preservam o fluxo de documentos não propositivos; 45 testes aprovados.
- Integridade de sucessão: `supersedes` exige ID válido e existente, rejeita autorreferência e ciclos e aceita cadeias acíclicas; 49 testes, compilação e `pip check` aprovados.
- Contexto aprovado: propostas `pending` permanecem disponíveis na busca administrativa, mas são excluídas dos context packs até se tornarem documentos `active`; 50 testes aprovados.
- Confinamento do piloto: Compose e estado efetivo confirmaram raiz somente leitura, `cap_drop: ALL`, `no-new-privileges` e `/tmp` efêmero; escrita falhou na raiz e funcionou somente nos mounts de Brain e dados; health permaneceu íntegro com 1 documento; 51 testes aprovados.
- Retenção de logs: driver efetivo `json-file` confirmado com `max-size: 10m` e `max-file: 3`; após recriação, health retornou `ok` e busca autenticada recuperou `DEC-TEST-001`; 52 testes aprovados.
- Esquema documental estrito: campos desconhecidos e metadados exclusivos de propostas em outros tipos são rejeitados antes da indexação; 53 testes, compilação e `pip check` aprovados.
- Metadados seguros: `scope` aceita somente identificadores de até 120 caracteres e autores de propostas seguem o mesmo contrato das identidades autenticadas; 58 testes aprovados.
- Integridade de alvos: propostas adicionadas diretamente ao acervo também rejeitam `target_id` inexistente ou autorreferente e aceitam alvos canônicos existentes; 61 testes aprovados.
- Separação da projeção: configurações diretas ou por ambiente falham quando `BRAIN_DB_PATH` coincide com ou fica abaixo de `BRAIN_ROOT`; índice externo aceito; 64 testes aprovados.
- Recursos limitados: configuração e `HostConfig` efetivo confirmaram 1 CPU, 512 MB de memória e 128 processos; container permaneceu saudável; 65 testes aprovados.
- Containers temporários do teste foram removidos; containers externos permaneceram intactos.
