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

- [x] Rate limiting — janela fixa no Redis (`RateLimiter` Protocol +
      `RedisRateLimiter`), aplicado em `/auth/register` e `/auth/login` (por IP,
      contadores independentes por rota) e em `POST /documents` (por usuário)
- [x] Validação de tipo e tamanho de arquivo — já existia desde a Fase 1
      (`DocumentService.upload_document`), coberta por teste desde a Fase 3
- [x] Controle de acesso: usuário não acessa documento de outro usuário — já existia desde
      a Fase 1 (`ForbiddenError` em `get_document`/`delete_document`), coberto por teste
- [x] Paginação, filtros e ordenação nos endpoints de listagem — `GET /documents`
      (filtro por `status` e busca por `q` no filename, `order_by` created_at/filename
      asc/desc) e `GET /conversations` (busca por `q` no título, `order_by`
      created_at/title asc/desc); resposta paginada (`Page[T]` genérico: `items`,
      `total`, `page`, `page_size`, `pages`) via `page`/`page_size` (padrão 20, máx 100)
- [x] IDs com UUID — já era o padrão desde a Fase 1 em todas as entidades
- [x] Idempotência em operações importantes — header `Idempotency-Key` (Redis, TTL
      configurável), aplicado em `POST /documents` e `POST /conversations/{id}/messages`
- [x] Logs estruturados — JSON puro (sem lib externa) em `infrastructure/logging.py`,
      correlação por `request_id` (API, via `ContextVar` + middleware) e `task_id`
      (worker, `document_id` também). Substitui de fato o echo do SQLAlchemy: as
      mesmas linhas de SQL agora saem como JSON em vez de texto puro
- [x] Métricas e tratamento centralizado de erros (o tratamento de erros em si já é
      centralizado desde a Fase 1 — `api/middlewares/error_handling.py`) — métricas via
      `GET /metrics` no formato Prometheus (`prometheus-client`): contadores/histogramas
      de requisições HTTP e de processamento de documento
- [x] GitHub Actions: lint, type-check e testes no CI (`.github/workflows/ci.yml`)
- [x] Avaliação de respostas pelo usuário (👍/👎) — `POST
      /conversations/{id}/messages/{message_id}/feedback`, só em respostas da IA
- [x] Tela administrativa: documentos processados, tempo médio de processamento,
      nº de perguntas, custo estimado de tokens, taxa de erro, tempo médio de resposta,
      modelos de IA mais usados — `GET /admin/metrics`, acesso restrito por `ADMIN_EMAILS`

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
- 2026-07-31: **Rate limiting.** Janela fixa contada no Redis (`INCR` + `EXPIRE` na
  primeira ocorrência da chave), seguindo o mesmo molde Protocol + implementação já usado
  em `TaskQueue`/`EmbeddingClient`: `RateLimiter` (`domain/repositories/rate_limiter.py`) +
  `RedisRateLimiter` (`infrastructure/rate_limit/`). Aplicado como dependência do FastAPI
  (`api/dependencies/rate_limit.py`) via `dependencies=[Depends(...)]` nas rotas, sem
  poluir a assinatura das funções: `rate_limit_auth` protege `/auth/register` e
  `/auth/login` por IP (chave inclui o path, então esgotar o limite de registro não afeta
  login), `rate_limit_upload` protege `POST /documents` por usuário (cada upload dispara
  processamento de IA — custa tempo de CPU/GPU e, com OpenAI, dinheiro de verdade). Limites
  configuráveis via Settings (`RATE_LIMIT_*` no `.env`), 5/60s pra auth e 10/60s pra upload
  por padrão. Nova exceção `RateLimitExceededError` → 429, registrada no mapa central de
  `error_handling.py`. Testado com o `RedisRateLimiter` de verdade (Redis local) em
  `tests/integration/test_rate_limiting.py`, e manualmente contra o servidor rodando de
  verdade (6 tentativas de login errado: as 5 primeiras 401, a 6ª 429). **Detalhe de
  design nos testes:** o `client` padrão em conftest.py passou a sobrescrever
  `get_rate_limiter` com um fake que nunca limita — confirmei que `request.client.host`
  é sempre `"127.0.0.1"` sob o `ASGITransport` do httpx, então sem esse fake qualquer
  teste com várias chamadas de auth/upload esbarraria no limite por compartilhar o mesmo
  IP falso entre testes. Os testes de rate limiting de verdade sobem sua própria instância
  da app com o `RedisRateLimiter` real, e limpam as chaves usadas antes/depois. 99 testes,
  96% de cobertura. Lint e type-check seguem 100% limpos.
- 2026-07-31: **Paginação, filtros e ordenação.** `GET /documents` e `GET /conversations`
  agora aceitam `page`/`page_size` (padrão 20, máximo 100), devolvendo um envelope `Page[T]`
  genérico (`api/schemas/pagination.py`: `items`, `total`, `page`, `page_size`, `pages`) em
  vez de uma lista crua — mudança que quebra o formato de resposta desses dois endpoints
  (aceitável nesse estágio do projeto, sem consumidores externos ainda). Documentos: filtro
  por `status` (usa o alias `status` no query param pra não colidir com o `status` do
  FastAPI já importado nas rotas — o parâmetro em si chama `document_status`) e busca por
  `q` no filename (`ILIKE`); `order_by` com `created_at`/`filename` × `asc`/`desc`.
  Conversas: busca por `q` no título; `order_by` com `created_at`/`title` × `asc`/`desc`.
  `DocumentRepository.list_by_owner`/`ConversationRepository.list_by_owner` mudaram de
  `list[T]` pra `tuple[list[T], int]` (itens da página + contagem total via `COUNT(*)`
  com os mesmos filtros) — Protocol, implementação SQLAlchemy, services e todos os
  fakes/testes que dependiam da assinatura antiga foram atualizados juntos. Decisão
  consciente de escopo: `GET /conversations/{id}/messages` ficou de fora da paginação por
  ora — histórico de conversa costuma ser consumido inteiro (ou via scroll incremental,
  um padrão diferente de paginação por página), não é um "endpoint de listagem" no mesmo
  sentido de documentos/conversas. Testado com Postgres real (paginação, filtro por
  status/busca, ordenação nos dois repositórios) e validado manualmente contra o servidor
  rodando de verdade. 113 testes, 95,75% de cobertura. Lint e type-check seguem 100% limpos.
- 2026-07-31: **Logs estruturados.** `infrastructure/logging.py`: `JsonFormatter` (uma
  linha JSON por evento — timestamp, level, logger, message, mais qualquer campo passado
  via `extra=`) e `RequestIdFilter` (injeta o `request_id` da requisição atual, via
  `ContextVar`, em todo LogRecord que não tenha um explícito). Como todo logger filho
  propaga pro root por padrão, isso vale pra qualquer `logging.getLogger(__name__)` do
  projeto sem precisar configurar nada por módulo. `RequestLoggingMiddleware`
  (`api/middlewares/request_logging.py`) é ASGI puro, não `BaseHTTPMiddleware` — que
  bufferiza a resposta pra poder inspecioná-la, o que quebraria o streaming do SSE em
  `/documents/{id}/status/stream`; aqui só envelopa `send`, então cada chunk do SSE
  continua passando direto. Gera (ou ecoa, se o cliente já mandou) um `X-Request-ID`,
  loga uma linha "request completed" com method/path/status_code/duration_ms ao final.
  Worker: `process_document_task` virou `bind=True` pra logar com `task_id` (via
  `self.request.id`) e `document_id` no início/sucesso/falha do processamento, com
  duração; `celery_app.conf.worker_hijack_root_logger = False` pra impedir o Celery de
  reconfigurar o root logger por cima do nosso na hora que o worker sobe.
  **Duas armadilhas de integração, achadas testando manualmente com servidor e worker
  reais (não apareceram nos testes automatizados, que não passam pelo bootstrap completo
  dos processos):** (1) o engine do SQLAlchemy (`echo=True`) anexa o próprio handler de
  texto puro no logger `sqlalchemy.engine.Engine` na hora em que é criado, *se* esse
  logger ainda não tiver nenhum handler — resultado: toda linha de SQL saía duplicada
  (uma em texto puro do handler do SQLAlchemy, outra em JSON via propagação pro root).
  A ordem de criação do engine em relação ao `configure_logging()` é diferente na API
  (engine já existe quando `create_app()` roda, por causa da cadeia de imports dos
  routers) e no worker (o `include=[...]` do Celery importa `tasks.py` — e por tabela
  `session.py`, criando o engine — só depois do próprio `celery_app.py` já ter chamado
  `configure_logging()`), então corrigir só num sentido (limpar o handler depois de
  criado) resolvia a API e quebrava o worker. Resolvido de um jeito independente de
  ordem: anexar um `NullHandler` nesse logger dentro de `configure_logging()`, que
  simultaneamente impede o SQLAlchemy de anexar o handler dele (`if not
  self.logger.handlers`) e limpa o que já tiver sido anexado antes. (2) o access log
  embutido do uvicorn duplicava a mesma informação do nosso "request completed" com
  menos contexto — desligado via `logging.getLogger("uvicorn.access").disabled = True`.
  Validado manualmente com API e worker reais rodando ao mesmo tempo: nenhuma linha de
  texto puro sobrou, `request_id`/`task_id`/`document_id` corretos em cada log, upload
  → processamento rastreável ponta a ponta pelos dois ids. 123 testes, 95,93% de
  cobertura. Lint e type-check seguem 100% limpos.
- 2026-08-12: **Fase 4 concluída** — os quatro itens que faltavam (idempotência, métricas,
  avaliação de respostas, tela administrativa). **Idempotência:** header `Idempotency-Key`
  opcional em `POST /documents` e `POST /conversations/{id}/messages` — as duas operações
  que disparam processamento de IA (custo de tempo/dinheiro), então um retry do cliente com
  a mesma chave devolve a resposta cacheada em vez de reprocessar. Cache simples no Redis
  (`IdempotencyStore` Protocol + `RedisIdempotencyStore`, TTL configurável), reaproveitando o
  mesmo Redis do rate limiter. **Métricas:** endpoint `GET /metrics` no formato Prometheus
  (`prometheus-client`), contadores/histogramas de requisições HTTP (por método + rota +
  status, hooked no `RequestLoggingMiddleware` já existente) e de processamento de documento
  (hooked no worker). Usa o *template* da rota (`scope["route"].path`) como label, não o path
  cru — evita explosão de cardinalidade por causa dos UUIDs nos paths de recurso.
  **Avaliação de respostas:** `POST /conversations/{id}/messages/{message_id}/feedback`
  (`rating: "up"|"down"`), só permitido em mensagens `role="assistant"` (`ValidationError`
  em mensagem de usuário) — coluna `feedback` nullable em `messages`. **Tela administrativa:**
  `GET /admin/metrics`, acesso restrito a e-mails listados em `ADMIN_EMAILS` (sem coluna nova
  em `users` — decisão consciente de escopo, dá pra promover um usuário só editando o `.env`).
  Duas fontes de dado novas: (1) colunas `processing_started_at`/`processing_finished_at` em
  `documents`, preenchidas pelo worker nas transições de status, usadas pro tempo médio de
  processamento; (2) tabela nova `ai_interactions`, um registro por pergunta respondida via
  RAG (sucesso ou falha) com provider/modelo, tokens estimados, custo estimado e duração —
  populada em `ConversationService.send_message`. **Decisão técnica importante:** nem Ollama
  nem OpenAI devolvem contagem real de tokens pro `LLMClient` deste projeto, então tokens e
  custo são estimados por heurística (`len(texto) // 4`, ~4 caracteres por token) — deixado
  explícito no código e no nome dos campos (`*_estimate`) que não é uma cobrança real; preço
  por 1k tokens configurável via `.env` (`TOKEN_PRICE_PER_1K_*_USD`), zero por padrão porque
  o provedor padrão (Ollama) roda local e de graça. Uma única migration nova pros três itens
  de schema (timestamps de documento, coluna de feedback, tabela `ai_interactions`). Validado
  manualmente com API + worker + Ollama reais rodando: upload duas vezes com o mesmo
  `Idempotency-Key` devolveu o mesmo documento; `/metrics` expôs as séries esperadas; feedback
  gravado e refletido em `GET /messages`; `/admin/metrics` bloqueado (403) pra usuário comum e
  liberado (200, com números batendo, inclusive tempo médio de processamento não-nulo depois
  do worker rodar) pro e-mail configurado em `ADMIN_EMAILS`. 140 testes, 97% de cobertura em
  `src/`. Lint e type-check seguem 100% limpos.
