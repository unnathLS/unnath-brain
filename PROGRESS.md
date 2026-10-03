# Progresso

- Último marco: BRAIN-012 concluído; publicação de propostas tornada atômica.
- Etapa atual: piloto local iniciado em 2026-10-03; MVP pronto para revisão do Presidente e observação de uso real.
- Testes: 35 aprovados; E2E, rebuild, Compose, restart, governança, FTS, configuração, publicação atômica, clone limpo, validação CLI e health íntegro do índice aprovados; `pip check` sem conflitos.
- Commits publicados: `44f7b78` (MVP), `16cf518` (endurecimento), `1902686` (operação), `1959775` (propostas válidas), `fdca86a` (falhas do índice), `96527a8` (health íntegro) e `cbb85f3` (tokens fortes) em `origin/development`.
- Decisões: Markdown + Git como fonte; SQLite/FTS5 como índice derivado; API reservada para a porta 8080.
- Restrições: Honcho, Hermes e Unnath HQ não serão modificados.
- Problemas: aviso de depreciação interno do Starlette nos testes; sem impacto funcional.
- Fila autônoma:
  1. `BRAIN-008`: validar conteúdo e alvo antes de persistir propostas — concluído; 23 testes aprovados.
  2. `BRAIN-009`: normalizar falhas do índice como indisponibilidade da API — concluído; 24 testes aprovados.
  3. `BRAIN-010`: detectar inconsistência entre índice documental e FTS no healthcheck — concluído; 25 testes aprovados.
- Revisão final:
  1. `BRAIN-011`: rejeitar credenciais fracas ou ambíguas na configuração de produção — concluído; 33 testes aprovados.
  2. `BRAIN-012`: publicar propostas atomicamente para evitar leitura parcial durante rebuild — concluído; 35 testes aprovados.
- Próximos passos: revisão do Presidente e observação de uso real; nenhuma funcionalidade adicional é necessária no escopo atual do MVP.
- Bloqueios: nenhum.
- Interrupções: shell sem rede exigiu aprovação única para atualizar o manual oficial do Codex; Docker recebeu regra persistente limitada a `docker compose`.
