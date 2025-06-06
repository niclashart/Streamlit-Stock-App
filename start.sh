#!/bin/bash
# filepath: /home/niclas/Schreibtisch/KI/6. Semester/Mobile Applikationen/Streamlit-Stock-App/start.sh

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker first."
  exit 1
fi

# Start the application
echo "Starting Stock Portfolio App..."
docker-compose up --build
