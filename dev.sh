#!/bin/bash

# OvernightApp Local Development Script
# Quick script to run migrations and start the dev server

set -e

echo "🚀 Starting OvernightApp in development mode..."

# Activate virtual environment if not already activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run migrations
echo "🗄️  Running migrations..."
python manage.py migrate

# Create default options for new users
echo "🎯 Creating default event options..."
python manage.py create_default_options || echo "⚠️  Options may already exist"

# Collect static files (for development)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start development server
echo "🌐 Starting development server..."
echo "   Access at: http://localhost:8000"
echo ""
python manage.py runserver
