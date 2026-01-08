#!/bin/bash

echo "==========================================="
echo "  Database Initialization Script (SQLite)"
echo "==========================================="
echo ""

# Create data directory if it doesn't exist
mkdir -p /app/data

echo "✅ Data directory ready!"
echo ""

# Check if Alembic is available
if command -v alembic &> /dev/null; then
    echo "📦 Running Alembic database migrations..."
    cd /app

    # Run migrations (will create database if it doesn't exist)
    alembic upgrade head

    if [ $? -eq 0 ]; then
        echo "✅ Database migrations completed successfully!"
    else
        echo "⚠️  Warning: Database migrations failed or no migrations to run"
        echo "   The database will be created automatically on first use"
    fi
else
    echo "⚠️  Alembic not found, skipping migrations"
    echo "   Database will be created automatically on first use"
fi

echo ""
echo "==========================================="
echo "  Database initialization complete!"
echo "==========================================="
echo ""
