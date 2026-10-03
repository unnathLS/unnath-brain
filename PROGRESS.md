# Progresso

- Último marco: BRAIN-007 concluído; endurecimento e prontidão operacional concluídos.
- Etapa atual: piloto local iniciado em 2026-10-03; ciclo autônomo de prontidão operacional em execução.
- Testes: 24 aprovados; E2E, rebuild, Compose, restart, governança, FTS, clone limpo, validação CLI e health do índice aprovados; `pip check` sem conflitos.
- Commits publicados: `44f7b78` (MVP), `16cf518` (endurecimento), `1902686` (operação) e `1959775` (propostas válidas) em `origin/development`.
- Decisões: Markdown + Git como fonte; SQLite/FTS5 como índice derivado; API reservada para a porta 8080.
- Restrições: Honcho, Hermes e Unnath HQ não serão modificados.
- Problemas: aviso de depreciação interno do Starlette nos testes; sem impacto funcional.
- Fila autônoma:
  1. `BRAIN-008`: validar conteúdo e alvo antes de persistir propostas — concluído; 23 testes aprovados.
  2. `BRAIN-009`: normalizar falhas do índice como indisponibilidade da API — concluído; 24 testes aprovados.
  3. `BRAIN-010`: detectar inconsistência entre índice documental e FTS no healthcheck — pendente.
- Próximos passos: concluir a fila, validar o piloto e seguir com revisão do Presidente e observação de uso real.
- Bloqueios: nenhum.
- Interrupções: shell sem rede exigiu aprovação única para atualizar o manual oficial do Codex; Docker recebeu regra persistente limitada a `docker compose`.
