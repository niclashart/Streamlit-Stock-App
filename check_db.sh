#!/bin/bash
# filepath: /home/niclas/Schreibtisch/KI/6. Semester/Mobile Applikationen/Streamlit-Stock-App/check_db.sh

echo "Überprüfe Datenbankverbindung..."

# Warte auf die PostgreSQL-Instanz
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-stockapp}
DB_USER=${DB_USER:-stockuser}
DB_PASSWORD=${DB_PASSWORD:-stockpassword}

MAX_RETRIES=30
RETRY_INTERVAL=2

retry_count=0
until docker exec $(docker ps -q -f name=streamlit-stock-app_postgres) pg_isready -h localhost -U $DB_USER -d $DB_NAME || [ $retry_count -eq $MAX_RETRIES ]; do
  >&2 echo "Postgres startet... Versuch $retry_count von $MAX_RETRIES"
  retry_count=$((retry_count+1))
  sleep $RETRY_INTERVAL
done

if [ $retry_count -eq $MAX_RETRIES ]; then
  >&2 echo "Timeout beim Warten auf Postgres"
  exit 1
fi

echo "Datenbankverbindung hergestellt!"
exit 0
