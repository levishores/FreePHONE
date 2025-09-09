#!/bin/bash

# FreeSWITCH CTI Setup Script

set -e

echo "🚀 Setting up FreeSWITCH CTI Application"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    echo "⚠️ PostgreSQL client not found. Make sure PostgreSQL is installed and accessible."
fi

echo "📦 Setting up Python backend..."

# Create virtual environment for backend
cd backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file. Please update it with your configuration."
fi

# Initialize database migrations
echo "🗄️ Setting up database migrations..."
alembic revision --autogenerate -m "Initial migration"

echo "✅ Backend setup complete!"

cd ..

echo "📦 Setting up Electron frontend..."

# Install Node.js dependencies for frontend
cd frontend
npm install

echo "✅ Frontend setup complete!"

cd ..

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your configuration"
echo "2. Start PostgreSQL database"
echo "3. Run database migrations: cd backend && alembic upgrade head"
echo "4. Start backend: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload"
echo "5. Start frontend: cd frontend && npm run dev"
echo ""
echo "For Docker setup:"
echo "1. Update docker-compose.yml environment variables"
echo "2. Place SSH private key in ./ssh/id_rsa"
echo "3. Run: docker-compose up -d"
