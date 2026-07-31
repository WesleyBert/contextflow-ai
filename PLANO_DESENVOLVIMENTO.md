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

- [x] Redis + Celery configurados no projeto
- [x] Worker dedicado: upload → extração → chunking → embeddings em background
- [x] Endpoint de status — implementado como `GET /api/v1/documents/{id}/status`
      (acoplado ao documento, não a uma task genérica; mais simples pro cliente,
      que já teria que buscar o documento de qualquer forma)
- [x] SSE para status em tempo real (`GET /api/v1/documents/{id}/status/stream`)
- [x] Testes unitários dos services (`tests/unit/test_auth_service.py`,
      `test_document_service.py`, `test_document_processing_service.py`,
      `test_conversation_service.py`, `test_rag_service.py`)
- [x] Testes de integração da API (`tests/integration/test_auth_routes.py`,
      `test_documents_routes.py`, `test_conversations_routes.py`, `test_health.py`),
      incluindo upload → status pending → worker roda → status ready, e o endpoint SSE
- [x] Testes dos repositórios, contra Postgres real (banco `contextflow_test` dedicado,
      criado automaticamente e isolado por transação com rollback por teste) —
      `tests/integration/test_document_repository.py`, `test_document_chunk_repository.py`
      (inclui busca por similaridade via pgvector), `test_conversation_repository.py`,
      `test_user_repository.py`
- [x] Mock da API de IA nos testes (`tests/fakes.py`: `FakeEmbeddingClient` determinístico
      por hash, `FakeLLMClient`) — nenhum teste depende de Ollama/OpenAI rodando
- [x] Testes de autenticação e permissões (registro/login, token inválido/ausente/tipo
      errado, usuário do token não existe mais, ownership 403/404 em documentos e
      conversas)
- [x] Testes de erros e entradas inválidas (tipo/tamanho de arquivo, senha curta, título
      vazio, e2e de falha de processamento levando o documento a `status="failed"`)
- [x] Cobertura de testes: 95% em `src/` (meta era ~80%) — os 5% restantes são
      adaptadores finos de rede (Ollama/OpenAI clients) já validados manualmente

## Fase 4 — V4: Nível produção

- [ ] Rate limiting
- [x] Validação de tipo e tamanho de arquivo — já existia desde a Fase 1
      (`DocumentService.upload_document`), coberta por teste desde a Fase 3
- [x] Controle de acesso: usuário não acessa documento de outro usuário — já existia desde
      a Fase 1 (`ForbiddenError` em `get_document`/`delete_document`), coberto por teste
- [ ] Paginação, filtros e ordenação nos endpoints de listagem
- [x] IDs com UUID — já era o padrão desde a Fase 1 em todas as entidades
- [ ] Idempotência em operações importantes
- [ ] Logs estruturados
- [ ] Métricas e tratamento centralizado de erros (o tratamento de erros em si já é
      centralizado desde a Fase 1 — `api/middlewares/error_handling.py` — falta só métricas)
- [x] GitHub Actions: lint, type-check e testes no CI (`.github/workflows/ci.yml`)
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
- 2026-07-31: **Fase 3 (parte 1) concluída — processamento assíncrono.** Coluna `status`
  (`pending`/`processing`/`ready`/`failed`) na entidade/model de documento + migration.
  `TaskQueue` como Protocol (`domain/repositories/task_queue.py`) com implementação Celery
  (`infrastructure/queue/`: `celery_app.py`, `celery_task_queue.py`, `tasks.py`).
  `DocumentService.upload_document` agora só enfileira a task em vez de processar sync; o
  worker roda `DocumentProcessingService` (mesma lógica da Fase 2, sem mudanças) e atualiza o
  status ao longo do caminho. Endpoints `GET /documents/{id}/status` e SSE em
  `/documents/{id}/status/stream`. Testado ponta a ponta com Postgres/Redis reais (Docker) e
  Ollama local: upload → `pending` → `processing` → `ready`, chunk e embedding gravados.
  **Bug encontrado e corrigido:** o `engine` assíncrono do SQLAlchemy é um singleton de módulo
  compartilhado entre API e worker; como cada task Celery roda `asyncio.run()` (loop novo a
  cada chamada), a segunda task em diante quebrava tentando reusar uma conexão do pool presa
  ao loop já fechado da task anterior (`AttributeError` dentro do asyncpg). Corrigido com
  `await engine.dispose()` num `finally` ao fim de cada task, forçando conexões novas no loop
  seguinte. Reproduzido com uploads em sequência antes e depois da correção pra confirmar.
  Lint e type-check seguem 100% limpos.
- 2026-07-31: **Fase 3 (parte 2) concluída — testes automatizados.** 96 testes, 95% de
  cobertura em `src/`. Infra em `tests/conftest.py`: `DATABASE_URL` redirecionado pra um
  banco `contextflow_test` dedicado (criado automaticamente, extensão `vector` habilitada),
  isolamento por teste via transação com `SAVEPOINT` (rollback no final, mesmo com `commit()`
  no meio do teste — `join_transaction_mode` padrão do SQLAlchemy 2.0 cobre isso). Duplos em
  `tests/fakes.py`: `FakeEmbeddingClient` (determinístico via hash) e `FakeLLMClient`, nenhum
  teste depende de Ollama/OpenAI rodando; `InlineTaskQueue` substitui o Celery — enfileira só
  registra o id, e o teste chama `run_pending()` explicitamente, o que também deixou testável
  a transição `pending` → (worker roda) → `ready`/`failed` sem subir Redis.
  **Bug de infraestrutura de teste encontrado e corrigido:** com `pytest-asyncio` no escopo
  padrão (`function`, um event loop novo por teste), o `engine` do SQLAlchemy — singleton de
  módulo — quebrava no segundo teste que tocasse o banco, com "Future attached to a different
  loop": basicamente a mesma causa-raiz do bug do worker Celery corrigido na parte 1, só que
  entre testes em vez de entre tasks. Resolvido configurando
  `asyncio_default_fixture_loop_scope = "session"` e `asyncio_default_test_loop_scope =
  "session"` no `pyproject.toml`, pra todos os testes assíncronos compartilharem um loop só.
  Teste de regressão dedicado (`tests/integration/test_tasks.py`) chama a task Celery direto
  — sem `.delay()`, sem precisar do Redis — rodando-a de verdade em threads separadas via
  `asyncio.to_thread` (cada uma com seu próprio `asyncio.run()`, igual a duas execuções
  sucessivas de worker); validado removendo o `engine.dispose()` temporariamente e confirmando
  que o teste quebra do jeito esperado antes de restaurar a correção. Cobertura restante fora
  dos 95% é majoritariamente os adaptadores finos de rede (`ollama_client.py`,
  `openai_client.py` e os de embedding) — não mockados propositalmente, já validados
  manualmente ponta a ponta nas Fases 1–3. Lint e type-check seguem 100% limpos.
- 2026-07-31: **Início da Fase 4 — CI no GitHub Actions.** `.github/workflows/ci.yml`: roda
  `ruff check .`, `mypy src/` e `pytest --cov=src --cov-fail-under=80` a cada push/PR na
  `main`, com Postgres (`pgvector/pgvector:pg16`) e Redis como service containers — os
  mesmos parâmetros do `docker-compose.yml` local, então o `TEST_DATABASE_URL` padrão do
  `conftest.py` funciona sem configuração extra. Validado rodando a sequência completa
  (install limpo → ruff → mypy → pytest) num venv novo antes de commitar, pra não descobrir
  problema de empacotamento só depois de rodar no GitHub; passou de primeira (96 testes,
  95% de cobertura). Aproveitei pra marcar no checklist três itens da Fase 4 que já
  existiam desde a Fase 1 e passaram a ter teste na Fase 3 (validação de arquivo, controle
  de acesso, IDs UUID) — não foi trabalho novo, só reconhecimento do que já estava feito.
  Próximos itens em aberto na Fase 4: rate limiting, paginação/filtros, idempotência, logs
  estruturados, métricas, avaliação de respostas e tela administrativa.
