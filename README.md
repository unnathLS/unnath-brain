# Unnath Brain

Fonte canônica de conhecimento corporativo baseada em Markdown + Git, com uma API local para consulta, pacotes de contexto e propostas de alteração.

O índice SQLite é derivado e pode ser reconstruído integralmente a partir de `brain/`.

## Executar

1. Copie `.env.example` para `.env` e gere tokens aleatórios diferentes.
2. Execute `docker compose up --build -d`.
3. Verifique `http://127.0.0.1:8080/health`.

Exemplo de consulta:

```bash
curl -H "Authorization: Bearer SEU_TOKEN" \
  "http://127.0.0.1:8080/api/v1/search?q=publicacoes"
```

Reconstrução explícita do índice:

```bash
docker compose run --rm gateway python -m brain_gateway.cli rebuild
```

Testes:

```bash
docker build -t unnath-brain:test .
docker run --rm unnath-brain:test pytest
```

Consulte `docs/api.md` para o contrato resumido e `PROGRESS.md` para o estado.

