#!/bin/bash

# WebTools WhatsApp Container Deployment Script
# This script builds and deploys the containerized WhatsApp account system

set -e

echo "🚀 WebTools WhatsApp Container Deployment"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p ./docker/main-api
mkdir -p ./docker/frontend
mkdir -p ./logs
mkdir -p ./backups

# Build Docker images
echo "🔨 Building Docker images..."

# Build main API image
echo "Building main API image..."
cat > ./docker/main-api/Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
EOF

# Build frontend image
echo "Building frontend image..."
cat > ./docker/frontend/Dockerfile << EOF
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Install serve to run the app
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Serve the built app
CMD ["serve", "-s", "build", "-l", "3000"]
EOF

# Build WhatsApp Account Service image
echo "Building WhatsApp Account Service image..."
docker build -t webtools-whatsapp-account:latest -f ./docker/whatsapp-account/Dockerfile .

# Create MongoDB initialization script
echo "📝 Creating MongoDB init script..."
cat > ./mongo-init.js << EOF
db = db.getSiblingDB('webtools_validation');

// Create collections
db.createCollection('users');
db.createCollection('whatsapp_accounts');
db.createCollection('whatsapp_account_events');
db.createCollection('jobs');
db.createCollection('validation_cache');
db.createCollection('admin_settings');

// Create indexes
db.whatsapp_accounts.createIndex({ "status": 1 });
db.whatsapp_accounts.createIndex({ "daily_usage": 1 });
db.jobs.createIndex({ "user_id": 1, "created_at": -1 });
db.validation_cache.createIndex({ "phone_number": 1 });
db.validation_cache.createIndex({ "cached_at": 1 }, { expireAfterSeconds: 604800 }); // 7 days

print('Database initialized successfully');
EOF

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# MongoDB Configuration
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=password123

# Application Configuration
CONTAINER_MODE=true
DEBUG=true

# API Keys (update these with your actual keys)
CHECKNUMBER_AI_API_KEY=your_checknumber_ai_key_here
CHECKNUMBER_AI_API_URL=https://api.checknumber.ai

# JWT Secret (generate a secure secret)
JWT_SECRET=your_jwt_secret_here

# Redis Configuration
REDIS_URL=redis://redis:6379
EOF
    echo "⚠️ Please update the .env file with your actual API keys and secrets"
fi

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."

# Check MongoDB
if docker-compose exec -T mongo mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is ready"
else
    echo "❌ MongoDB failed to start"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis failed to start"
fi

# Check Main API
sleep 5
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Main API is ready"
else
    echo "⏳ Main API is starting... (this may take a minute)"
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is ready"
else
    echo "⏳ Frontend is starting... (this may take a minute)"
fi

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📱 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   MongoDB: mongodb://localhost:27017"
echo "   Redis: redis://localhost:6379"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 Next Steps:"
echo "1. Update .env file with your actual API keys"
echo "2. Login to admin panel at http://localhost:3000"
echo "3. Navigate to WhatsApp Account Management"
echo "4. Create your first WhatsApp account"
echo "5. Configure proxy settings (optional)"
echo ""
echo "🐳 Container Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop all: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Rebuild: docker-compose up --build -d"
echo ""
echo "📚 Documentation:"
echo "   WhatsApp accounts will run in isolated Docker containers"
echo "   Each account can have its own proxy configuration"
echo "   Containers are automatically managed by the orchestrator"
echo ""