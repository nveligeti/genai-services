# scripts/start.sh
# Runs migrations then starts server

#!/bin/bash
set -e

echo "============================================"
echo " DocuMind Startup"
echo "============================================"

echo "Running database migrations..."
python -m alembic upgrade head
echo "Migrations complete ✅"

echo "Starting application..."
exec uvicorn app.main:create_app \
    --factory \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1