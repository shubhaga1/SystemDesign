#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# SQL Runner — targets SQLite or Postgres
#
# Usage:
#   ./run.sh <file.sql>              → runs against SQLite (no server needed)
#   ./run.sh <file.sql> pg           → runs against Postgres in Docker
#
# Postgres requires Docker running:
#   docker-compose up -d
# ─────────────────────────────────────────────────────────────────────────────

FILE=$1
TARGET=${2:-sqlite}   # default to sqlite if no second arg

if [ -z "$FILE" ]; then
    echo "Usage:"
    echo "  ./run.sh <file.sql>       → SQLite (offline, instant)"
    echo "  ./run.sh <file.sql> pg    → Postgres (Docker must be running)"
    exit 1
fi

if [ "$TARGET" = "pg" ]; then
    echo "▶ Running on Postgres (Docker)..."
    docker exec -i postgres-local psql -U admin -d learndb < "$FILE"
else
    echo "▶ Running on SQLite (in-memory)..."
    sqlite3 :memory: < "$FILE"
fi
