# Progresso

- Último marco: BRAIN-062 concluído; o parser Bearer rejeita ambiguidades e percorre todas as credenciais.
- Etapa atual: piloto local iniciado em 2026-10-03; MVP pronto para revisão do Presidente e observação de uso real.
- Testes: 111 aprovados; E2E, concorrência, rebuild, Compose, restart, governança, FTS, configuração, rollback de propostas, publicação atômica, dependências, confinamento, recursos, privacidade e rotação de logs aprovados; compilação limpa e `pip check` sem conflitos.
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
  4. `BRAIN-027`: impedir que o índice seja configurado dentro da fonte canônica — concluído; 64 testes aprovados.
  5. `BRAIN-028`: limitar CPU, memória e processos do container — concluído; 1 CPU, 512 MB e 128 processos verificados no runtime.
  6. `BRAIN-029`: impedir que consultas apareçam nos access logs — concluído; consulta autenticada ausente dos logs e 66 testes aprovados.
- Fronteira canônica:
  1. `BRAIN-030`: tornar o acervo somente leitura no runtime, exceto `proposals/` — concluído; mounts e escrita seletiva verificados.
  2. `BRAIN-031`: rejeitar documentos canônicos acessados por links simbólicos — concluído; 68 testes aprovados.
  3. `BRAIN-032`: exigir título explícito e conteúdo documental mínimo — concluído; 73 testes aprovados.
  4. `BRAIN-033`: alinhar `created` e `timestamp` nas propostas — concluído; 74 testes aprovados.
  5. `BRAIN-034`: reverter a proposta quando a atualização do índice falhar — concluído; 75 testes aprovados.
  6. `BRAIN-035`: serializar criações de propostas e rebuilds no processo — concluído; duas requisições simultâneas publicadas sem sobreposição e 76 testes aprovados.
- Robustez do MVP:
  1. `BRAIN-036`: limitar o tamanho individual dos documentos canônicos — concluído; 77 testes aprovados.
  2. `BRAIN-037`: rejeitar caracteres de controle invisíveis nos Markdown — concluído; 82 testes aprovados.
  3. `BRAIN-038`: exigir que `supersedes` relacione documentos do mesmo tipo — concluído; 83 testes aprovados.
  4. `BRAIN-039`: impedir sucessão documental com data retroativa — concluído; 84 testes aprovados.
  5. `BRAIN-040`: restringir `target_id` a documentos ativos não propositivos — concluído; 86 testes aprovados.
  6. `BRAIN-041`: indexar metadados de governança das propostas — concluído; migração compatível validada e 87 testes aprovados.
  7. `BRAIN-042`: verificar igualdade de título e conteúdo entre índice e FTS — concluído; 88 testes aprovados.
  8. `BRAIN-043`: configurar espera limitada para contenção do SQLite — concluído; 89 testes aprovados.
  9. `BRAIN-044`: limitar a complexidade das consultas por quantidade de termos — concluído; função e API validadas em 91 testes.
  10. `BRAIN-045`: impedir armazenamento intermediário de respostas HTTP — concluído; respostas de sucesso e erro validadas em 92 testes.
- Defesa operacional do MVP:
  1. `BRAIN-046`: impedir publicação de propostas por diretório simbólico — concluído; 93 testes aprovados.
  2. `BRAIN-047`: validar a forma canônica da proposta antes da publicação — concluído; 95 testes aprovados.
  3. `BRAIN-048`: rejeitar campos JSON desconhecidos nas requisições — concluído; 96 testes aprovados.
  4. `BRAIN-049`: validar IDs recebidos pela rota documental — concluído; 97 testes aprovados.
  5. `BRAIN-050`: normalizar e validar metadados dos context packs — concluído; 98 testes aprovados.
  6. `BRAIN-051`: rejeitar caracteres de controle nas consultas — concluído; busca e contexto validados em 100 testes.
  7. `BRAIN-052`: impedir bifurcações na cadeia de sucessão — concluído; 101 testes aprovados.
  8. `BRAIN-053`: versionar e verificar o esquema do índice derivado — concluído; 102 testes aprovados.
  9. `BRAIN-054`: aplicar o confinamento do índice também ao CLI — concluído; 103 testes aprovados.
  10. `BRAIN-055`: completar cabeçalhos defensivos das respostas HTTP — concluído; compilação, dependências e 103 testes aprovados.
- Experiência do piloto:
  1. `BRAIN-056`: direcionar a raiz do serviço para a documentação interativa — concluído; redirecionamento e destino cobertos em 104 testes.
- Operação assistida:
  1. `BRAIN-057`: executar o runtime com usuário sem privilégios — concluído; identidade efetiva e escrita seletiva verificadas em 105 testes.
  2. `BRAIN-058`: tratar sinais e encerramento gracioso no Compose — concluído; init e janela de 10 segundos validados em 106 testes.
  3. `BRAIN-059`: limitar conexões concorrentes do gateway — concluído; teto de 64 conexões validado em 107 testes.
  4. `BRAIN-060`: ocultar a assinatura do servidor HTTP — concluído; ausência do cabeçalho `Server` verificada em 108 testes e no runtime.
  5. `BRAIN-061`: declarar autenticação Bearer no OpenAPI — concluído; Swagger e rotas públicas/protegidas validados em 109 testes.
  6. `BRAIN-062`: tornar o parser Bearer estrito e uniforme — concluído; variação de caixa, formatos ambíguos e varredura integral cobertos em 111 testes.
- Próximos passos: revisão do Presidente e observação de uso real; a defesa operacional do MVP está concluída.
- Bloqueios: nenhum.
- Interrupções: shell sem rede exigiu aprovação única para atualizar o manual oficial do Codex; Docker recebeu regra persistente limitada a `docker compose`.
