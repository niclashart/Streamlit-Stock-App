FROM python:3.12-slim

WORKDIR /app

# Install system dependencies that might be needed by some python packages
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure stock_app.db is in the right place if copied, or use a volume (volume is handled in docker-compose)

EXPOSE 8501

HEALTHCHECK CMD streamlit healthcheck

# Run streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
