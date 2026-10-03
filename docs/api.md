# API v1

`GET /health` não exige autenticação e confirma a disponibilidade e a coerência mínima do índice, incluindo a contagem de documentos e o alinhamento com o FTS. Os endpoints sob `/api/v1` exigem `Authorization: Bearer <token>`.

- `GET /api/v1/search?q=texto&limit=10`: busca textual com origem rastreável.
- `GET /api/v1/documents/{id}`: recupera um documento pelo ID estável.
- `POST /api/v1/context`: recebe `project`, `mission`, `query` e `limit`; a identidade vem da credencial.
- `POST /api/v1/proposals`: recebe `title`, `content` e `target_id` opcional; cria Markdown `pending` sem alterar o alvo.

As respostas documentais incluem caminho, hash SHA-256 e commit Git quando disponível. Conteúdo retornado deve ser tratado pelo consumidor como dado não confiável, nunca como instrução de runtime.
