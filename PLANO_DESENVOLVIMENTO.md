# ContextFlow AI — Plano de Desenvolvimento

> Plataforma de IA desenvolvida em Python para processamento de documentos e geração de
> respostas contextualizadas utilizando RAG, arquitetura assíncrona, busca vetorial,
> autenticação, testes automatizados e observabilidade.

Este arquivo é o **checklist vivo** do projeto. Cada vez que avançarmos em uma sessão,
marcamos os itens concluídos (`- [x]`) e podemos adicionar notas curtas do que foi
aprendido/decidido, se fizer sentido.

## Stack decidida

- **Back-end:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- **Fila assíncrona:** Redis + Celery
- **IA:** camada de abstração própria (Strategy) para trocar entre **Ollama (local, gratuito)**
  e **OpenAI API (pago, opcional)**; RAG com chunking, embeddings e re-ranking
- **Banco vetorial:** PostgreSQL + pgvector
- **Front-end:** React + TypeScript
- **Infra:** Docker + Docker Compose, GitHub Actions, Pytest, Ruff, MyPy, pre-commit

Por padrão o projeto roda **100% gratuito** usando Ollama local. A OpenAI API fica disponível
como opção configurável via variável de ambiente, documentada no README, nunca obrigatória.

---

## Fase 0 — Fundamentos + Setup

- [x] Estrutura de pastas em camadas (api / application / domain / infrastructure / workers / tests)
- [x] `PLANO_DESENVOLVIMENTO.md` criado
- [ ] Ambiente virtual e `pyproject.toml` com dependências
- [ ] Ruff, MyPy e pre-commit configurados
- [ ] `docker-compose.yml` com Postgres + Redis subindo localmente
- [x] Git inicializado com primeiro commit
- [ ] Reforço de Python conforme necessidade: type hints, Pydantic, async/await,
      context managers, decorators (explicado junto com o código real, não como aula isolada)

## Fase 1 — V1: API básica funcional

- [x] FastAPI: app, roteamento, dependências (`Depends`) — `src/main.py`, app factory `create_app()`
- [x] Configuração via Pydantic Settings (`src/infrastructure/config.py`)
- [x] Engine assíncrono SQLAlchemy + `get_db()` dependency (`src/infrastructure/database/session.py`)
- [x] Alembic configurado (template async), ligado às Settings e ao `Base.metadata`
- [x] Primeira migration real — tabela `users` criada no Postgres (`alembic/versions/8ef8b24e0113_*.py`)
- [x] Autenticação: registro, login, JWT (access + refresh token), hash de senha
      (`domain/entities/user.py`, `infrastructure/security/`, `application/services/auth_service.py`,
      `api/routes/auth.py`) — testado ponta a ponta via curl (registro, e-mail duplicado → 409,
      login, senha errada → 401, rota protegida `/me` com e sem token → 200/401)
- [x] CRUD de documentos (sem processamento de IA ainda) — upload (multipart), listar, buscar
      por id, deletar; validação de tipo/tamanho; isolamento por dono testado (403 pra outro
      usuário, 404 após deletar) (`application/services/document_service.py`,
      `infrastructure/storage/local_storage.py`, `api/routes/documents.py`)
- [x] CRUD de conversas — criar, listar, histórico de mensagens; isolamento por dono testado
      (`application/services/conversation_service.py`, `api/routes/conversations.py`)
- [x] Integração simples com um LLM (pergunta → resposta, sem RAG ainda) — Strategy Ollama/OpenAI
      (`domain/repositories/llm_client.py`, `infrastructure/ai/`), testado de ponta a ponta com
      Ollama local rodando de verdade (modelo `llama3.2:1b`)
- [x] Versionamento `/api/v1`, tratamento padronizado de erros (`src/api/middlewares/error_handling.py`)
- [x] Health check (`/health`) — testado, retorna `{"status":"ok"}`
- [x] Documentação automática via Swagger — testado em `/docs`

## Fase 2 — V2: RAG de verdade

- [x] Upload de PDF e extração de texto (`infrastructure/text/pdf_extractor.py`, via `pypdf`) —
      testado com um PDF real gerado na hora, texto extraído corretamente
- [x] Chunking de documentos (`infrastructure/text/chunker.py`, janela de caracteres com
      sobreposição, hand-rolled em vez de depender de LangChain)
- [x] Geração de embeddings via camada de abstração de IA — Strategy Ollama
      (`nomic-embed-text`) / OpenAI (`domain/repositories/embedding_client.py`,
      `infrastructure/ai/ollama_embedding_client.py` / `openai_embedding_client.py`)
- [x] pgvector: armazenamento e busca por similaridade (coluna `Vector` via pacote `pgvector`,
      busca por `cosine_distance`, escopada por usuário dono —
      `infrastructure/repositories/document_chunk_repository.py`)
- [x] Pipeline RAG completo: pergunta → busca de contexto → resposta com fontes citadas
      (`application/services/rag_service.py`) — testado ponta a ponta: perguntas sobre fatos
      exclusivos de um documento (.txt e .pdf) respondidas corretamente citando a fonte;
      isolamento por usuário confirmado (outro usuário não recupera documentos alheios)
- [x] Re-ranking dos resultados recuperados — léxico, misturando similaridade vetorial com
      sobreposição de palavras-chave (`infrastructure/text/reranker.py`), sem depender de um
      modelo de cross-encoder

## Fase 3 — V3: Processamento assíncrono

- [ ] Redis + Celery configurados no projeto
- [ ] Worker dedicado: upload → extração → chunking → embeddings em background
- [ ] Endpoint `GET /api/v1/tasks/{id}/status`
- [ ] WebSocket ou SSE para status em tempo real
- [ ] Testes unitários dos services
- [ ] Testes de integração da API
- [ ] Testes dos repositórios
- [ ] Mock da API de IA nos testes
- [ ] Testes de autenticação e permissões
- [ ] Testes de erros e entradas inválidas
- [ ] Cobertura de testes em torno de 80%

## Fase 4 — V4: Nível produção

- [ ] Rate limiting
- [ ] Validação de tipo e tamanho de arquivo
- [ ] Controle de acesso: usuário não acessa documento de outro usuário
- [ ] Paginação, filtros e ordenação nos endpoints de listagem
- [ ] IDs com UUID, idempotência em operações importantes
- [ ] Logs estruturados
- [ ] Métricas e tratamento centralizado de erros
- [ ] GitHub Actions: lint, type-check e testes no CI
- [ ] Avaliação de respostas pelo usuário (👍/👎)
- [ ] Tela administrativa: documentos processados, tempo médio de processamento,
      nº de perguntas, custo estimado de tokens, taxa de erro, tempo médio de resposta,
      modelos de IA mais usados

## Fase 5 — Front-end (React + TypeScript)

- [ ] Autenticação (login/registro)
- [ ] Upload de documentos + status em tempo real
- [ ] Interface de conversa com exibição das fontes citadas
- [ ] Organização de documentos por projeto
- [ ] Avaliação de respostas (thumbs up/down)
- [ ] Tela administrativa com as métricas da Fase 4

## Fase 6 — Apresentação no GitHub

- [ ] README profissional com diagrama de arquitetura
- [ ] Instruções de execução via Docker
- [ ] Documentação dos endpoints com exemplos de request/response
- [ ] Explicação das decisões técnicas (por que fila assíncrona, por que pgvector, etc.)
- [ ] Prints ou vídeo demonstrativo
- [ ] Roadmap
- [ ] Badge de cobertura de testes
- [ ] Pipeline do GitHub Actions visível e funcionando

---

## Notas de sessão

_(Vamos registrando aqui decisões, trade-offs e coisas aprendidas ao longo do caminho.)_

- 2026-07-22: Setup inicial do repositório e estrutura de pastas.
- 2026-07-22: Início da Fase 1 — app FastAPI (app factory), config via Pydantic Settings,
  engine assíncrono SQLAlchemy, tratamento padronizado de erros, health check testado
  (`/api/v1/health` → 200) e Swagger testado (`/docs` → 200). Alembic configurado (template
  async) e testado — a conexão falhou por falta de Postgres local (esperado, sem Docker
  instalado nesta máquina), mas confirmou que a configuração está correta.
- 2026-07-23: Docker Desktop instalado e funcionando (precisou habilitar virtualização na
  BIOS/UEFI e instalar o WSL2 via `wsl --install`, rodando como administrador). Postgres
  (pgvector) e Redis sobem via `docker compose up -d`. Camada de auth completa: entidade de
  domínio `User`, `UserRepository` como Protocol (inversão de dependência), implementação
  SQLAlchemy, hash de senha com `bcrypt` (trocado de `passlib` por incompatibilidade
  conhecida com bcrypt novo), JWT (access + refresh) com `python-jose`, `AuthService`,
  endpoints `POST /auth/register`, `POST /auth/login`, `GET /auth/me` (protegida). Primeira
  migration real gerada via `alembic revision --autogenerate` e aplicada. Lint (Ruff) e
  type-check (MyPy strict) 100% limpos.
- 2026-07-23: **Fase 1 concluída.** Ollama instalado via winget (modelo `llama3.2:1b`, ~1.3GB,
  escolhido por ser leve o suficiente pra rodar bem localmente) pra testar a integração com IA
  de verdade. CRUD de documentos (upload multipart validando tipo/tamanho, storage local em
  disco via `LocalFileStorage`) e CRUD de conversas, ambos com isolamento por usuário dono
  (403 ao tentar acessar recurso de outro usuário). Cliente de LLM com Strategy pattern
  (`LLMClient` Protocol + `OllamaLLMClient`/`OpenAILLMClient`, escolhidos por `AI_PROVIDER`),
  testado ponta a ponta: pergunta "qual a capital do Brasil?" → resposta correta do Ollama
  local em ~7s. Todos os fluxos validados via curl (uploads, tipos inválidos, ownership,
  conversas, mensagens). Lint e type-check seguem limpos.
- 2026-07-23: **Fase 2 concluída.** Extração de PDF (`pypdf`), chunking hand-rolled (janela de
  caracteres com sobreposição), embeddings via Strategy (Ollama `nomic-embed-text` local /
  OpenAI), armazenamento vetorial no Postgres com a extensão `pgvector`
  (`CREATE EXTENSION vector`, coluna `Vector(768)`, busca por `cosine_distance`), pipeline RAG
  completo (`RAGService`) com re-ranking léxico de segundo estágio, e mensagens agora guardam
  `sources` (documento + trecho usado) pra citação. Criado `ChatMessage`, um tipo leve separado
  da entidade `Message` persistida, pra poder injetar uma instrução de sistema (contexto RAG)
  numa chamada ao LLM sem isso virar uma linha de verdade na conversa. **Decisão técnica
  importante:** o modelo `llama3.2:1b` (usado na Fase 1) é rápido mas fraco demais pra RAG —
  ele ignorava o contexto fornecido e alucinava. Trocado pelo `llama3.2:3b` (~2GB), que segue
  a instrução "responda só com base no contexto" de forma confiável. Testado ponta a ponta com
  três fatos inventados (só existentes nos documentos de teste, um `.txt` e um `.pdf` gerado na
  hora): todas as respostas corretas, citando a fonte certa. Confirmado isolamento por usuário
  na busca vetorial (outro usuário não recupera documentos alheios, cai de volta pro
  conhecimento geral do modelo). Lint e type-check seguem 100% limpos.
