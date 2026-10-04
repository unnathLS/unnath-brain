# Progresso

- Último marco: BRAIN-026 concluído; alvos de propostas têm integridade referencial no acervo.
- Etapa atual: piloto local iniciado em 2026-10-03; MVP pronto para revisão do Presidente e observação de uso real.
- Testes: 61 aprovados; E2E, rebuild, Compose, restart, governança, FTS, configuração, publicação atômica, dependências, confinamento e rotação de logs aprovados; `pip check` sem conflitos.
- Commits publicados: `44f7b78` (MVP), `1959775` (propostas válidas), `96527a8` (health íntegro), `0766ee0` (propostas atômicas), `1855345` (raiz válida), `075aee0` (clone limpo), `ada6a1c` (runtime mínimo), `2574e1b` (dependências fixadas), `f93ea4a` (imagem base), `f283ab2` (atores), `d9c4cda` (diretórios), `776a9d6` (sucessão), `b7860c6` (contexto ativo) e `4188b43` (confinamento) em `origin/development`.
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
  3. `BRAIN-013`: falhar quando a raiz canônica estiver ausente ou não for diretório — concluído; 36 testes aprovados.
  4. `BRAIN-014`: validar o HEAD publicado em clone limpo — concluído; build, compilação, `pip check` e 36 testes aprovados.
  5. `BRAIN-015`: separar imagens Docker de runtime e teste — concluído; runtime sem ferramentas de desenvolvimento e 36 testes aprovados no alvo de teste.
  6. `BRAIN-016`: fixar dependências transitivas para builds reproduzíveis — concluído; rebuild sem cache e 37 testes aprovados.
  7. `BRAIN-017`: fixar a imagem base Python pelo digest validado — concluído; build sem cache e 38 testes aprovados.
- Endurecimento final:
  1. `BRAIN-018`: validar identidades de atores usadas na autenticação e auditoria — concluído; 42 testes aprovados.
  2. `BRAIN-019`: garantir coerência entre tipo e diretório canônico — concluído; 45 testes aprovados.
  3. `BRAIN-020`: validar referências `supersedes` — concluído; 49 testes aprovados.
  4. `BRAIN-021`: limitar context packs a documentos ativos — concluído; 50 testes aprovados.
  5. `BRAIN-022`: confinar o container do piloto — concluído; raiz somente leitura, capabilities removidas e `no-new-privileges` verificados no container.
  6. `BRAIN-023`: limitar o crescimento dos logs Docker — concluído; retenção efetiva de 3 arquivos de 10 MB e 52 testes aprovados.
- Integridade e operação:
  1. `BRAIN-024`: rejeitar campos de frontmatter desconhecidos ou incompatíveis com o tipo — concluído; 53 testes aprovados.
  2. `BRAIN-025`: validar valores escalares de metadados e autores de propostas — concluído; 58 testes aprovados.
  3. `BRAIN-026`: validar referências `target_id` no acervo canônico — concluído; 61 testes aprovados.
  4. `BRAIN-027`: impedir que o índice seja configurado dentro da fonte canônica — em execução.
  5. `BRAIN-028`: limitar CPU, memória e processos do container — pendente.
  6. `BRAIN-029`: impedir que consultas apareçam nos access logs — pendente.
- Próximos passos: revisão do Presidente e observação de uso real; os seis checkpoints adicionais do MVP estão concluídos.
- Bloqueios: nenhum.
- Interrupções: shell sem rede exigiu aprovação única para atualizar o manual oficial do Codex; Docker recebeu regra persistente limitada a `docker compose`.
