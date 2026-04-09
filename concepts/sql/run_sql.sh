#!/bin/bash
# Usage: ./run_sql.sh <file.sql>
# Runs SQL file using SQLite (no server needed)

FILE=$1

if [ -z "$FILE" ]; then
    echo "Usage: ./run_sql.sh <path/to/file.sql>"
    exit 1
fi

sqlite3 :memory: < "$FILE"
