#!/bin/bash

# Stock Portfolio App Launcher
echo "Starting Stock Portfolio Assistant..."

# Check if database initialization is needed
if grep -q "STORAGE_TYPE=database" .env 2>/dev/null; then
  if [ ! -f "stock_app.db" ] && ! psql -l 2>/dev/null | grep -q "stock_portfolio"; then
    echo "Database storage is configured, but no database found."
    echo "Run 'python init_db.py' first to initialize the database."
    echo "Or change STORAGE_TYPE=csv in your .env file."
    
    read -p "Do you want to initialize SQLite database now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      python init_db.py
    fi
  fi
fi

# Start the application
streamlit run src/main.py
