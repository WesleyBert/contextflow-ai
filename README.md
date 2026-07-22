# ContextFlow AI

Plataforma de IA desenvolvida em Python para processamento de documentos e geração de
respostas contextualizadas utilizando RAG (Retrieval-Augmented Generation), arquitetura
assíncrona, busca vetorial, autenticação, testes automatizados e observabilidade.

> Projeto em desenvolvimento ativo. Acompanhe o progresso em [`PLANO_DESENVOLVIMENTO.md`](./PLANO_DESENVOLVIMENTO.md).

## Stack

- **Back-end:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- **Fila assíncrona:** Redis + Celery
- **IA:** RAG com chunking, embeddings e re-ranking; suporte a Ollama (local, gratuito)
  e OpenAI API (opcional, pago)
- **Banco vetorial:** PostgreSQL + pgvector
- **Front-end:** React + TypeScript
- **Infra:** Docker, Docker Compose, GitHub Actions, Pytest, Ruff, MyPy, pre-commit

## Arquitetura

```
src/
├── api/            # rotas, dependências e middlewares do FastAPI
├── application/    # services e use cases (regras de aplicação)
├── domain/         # entidades, exceções e contratos de repositório
├── infrastructure/ # banco de dados, repositórios, IA, storage
├── workers/        # tarefas assíncronas (Celery)
└── main.py
```

## Como rodar (em construção)

```bash
docker compose up -d   # sobe Postgres (pgvector) e Redis
cp .env.example .env
# instruções completas de setup do back-end e front-end virão nas próximas fases
```

## Roadmap

Veja o checklist completo de desenvolvimento em [`PLANO_DESENVOLVIMENTO.md`](./PLANO_DESENVOLVIMENTO.md).
