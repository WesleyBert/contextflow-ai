#!/usr/bin/env bash
# Start command do serviço web no Render: aplica as migrations, sobe o worker Celery
# em background e a API em foreground (mesmo processo/container — ver comentário no
# render.yaml sobre por que API e worker não são serviços separados aqui).
set -euo pipefail

echo "Aplicando migrations..."
alembic upgrade head

echo "Subindo worker Celery em background..."
celery -A src.infrastructure.queue.celery_app worker --loglevel=info --concurrency=2 &

echo "Subindo API..."
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
