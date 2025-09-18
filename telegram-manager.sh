#!/bin/bash

# 🚀 SIMPLE TELEGRAM MULTI-ACCOUNT MANAGER
# Easy management untuk 3 account Telegram di 1 VPS

set -e

DOCKER_COMPOSE_FILE="docker-telegram-simple.yml"
ENV_FILE=".env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not installed"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found"
        print_status "Copying template..."
        cp .env.telegram .env
        print_warning "Please edit .env file with your Telegram credentials"
        exit 1
    fi
    
    print_success "Requirements check passed"
}

setup_directories() {
    print_status "Setting up directories..."
    
    mkdir -p data/sessions/account_{1,2,3}
    mkdir -p data/logs
    mkdir -p nginx
    
    # Set permissions
    chmod 755 data/sessions/account_*
    chmod 755 data/logs
    
    print_success "Directories created"
}

build_images() {
    print_status "Building Docker images..."
    docker build -t telegram-simple:latest ./docker/telegram-simple/
    print_success "Images built successfully"
}

start_accounts() {
    print_status "Starting Telegram accounts..."
    
    # Create directories if not exist
    setup_directories
    
    # Start containers
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    print_success "All accounts started!"
    
    # Wait for startup
    print_status "Waiting for accounts to initialize..."
    sleep 10
    
    # Check status
    show_status
}

stop_accounts() {
    print_status "Stopping Telegram accounts..."
    docker-compose -f $DOCKER_COMPOSE_FILE down
    print_success "All accounts stopped"
}

restart_accounts() {
    print_status "Restarting Telegram accounts..."
    docker-compose -f $DOCKER_COMPOSE_FILE restart
    print_success "All accounts restarted"
}

show_status() {
    print_status "Checking accounts status..."
    echo ""
    
    # Docker containers status
    echo "📦 Container Status:"
    docker-compose -f $DOCKER_COMPOSE_FILE ps
    echo ""
    
    # Health checks
    echo "🏥 Health Checks:"
    for i in {1..3}; do
        port=$((8080 + i))
        echo -n "Account $i (port $port): "
        
        if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Healthy${NC}"
        else
            echo -e "${RED}❌ Unhealthy${NC}"
        fi
    done
    echo ""
    
    # Load balancer status
    echo -n "Load Balancer (port 8090): "
    if curl -s -f http://localhost:8090/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
    else
        echo -e "${RED}❌ Not responding${NC}"
    fi
}

show_logs() {
    if [ -z "$2" ]; then
        print_status "Showing logs for all accounts..."
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f
    else
        account_num=$2
        print_status "Showing logs for account $account_num..."
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f telegram-$account_num
    fi
}

test_validation() {
    phone_number=${2:-"+6281234567890"}
    
    print_status "Testing validation with phone: $phone_number"
    
    # Test individual accounts
    echo "🧪 Testing individual accounts:"
    for i in {1..3}; do
        port=$((8080 + i))
        echo -n "Account $i: "
        
        response=$(curl -s -X POST http://localhost:$port/validate \
            -H "Content-Type: application/json" \
            -d "{\"phone_number\":\"$phone_number\"}" 2>/dev/null)
        
        if echo "$response" | grep -q '"success":true'; then
            echo -e "${GREEN}✅ Success${NC}"
        else
            echo -e "${RED}❌ Failed${NC}"
        fi
    done
    
    echo ""
    echo "🎯 Testing load balancer:"
    response=$(curl -s -X POST http://localhost:8090/validate \
        -H "Content-Type: application/json" \
        -d "{\"phone_number\":\"$phone_number\"}")
    
    echo "Response:"
    echo "$response" | jq . 2>/dev/null || echo "$response"
}

show_detailed_health() {
    print_status "Detailed health information..."
    
    for i in {1..3}; do
        port=$((8080 + i))
        echo "📊 Account $i detailed health:"
        curl -s http://localhost:$port/health | jq . 2>/dev/null || echo "Error getting health info"
        echo ""
    done
}

first_time_setup() {
    print_status "First-time setup for Telegram Multi-Account..."
    
    # Check requirements
    check_requirements
    
    # Setup directories
    setup_directories
    
    # Build images
    build_images
    
    print_success "Setup completed!"
    print_warning "Next steps:"
    echo "1. Edit .env file with your real Telegram API credentials"
    echo "2. Run: ./telegram-manager.sh start"
    echo "3. Check status: ./telegram-manager.sh status"
}

case $1 in
    setup)
        first_time_setup
        ;;
    start)
        check_requirements
        build_images
        start_accounts
        ;;
    stop)
        stop_accounts
        ;;
    restart) 
        restart_accounts
        ;;
    status|health)
        show_status
        ;;
    logs)
        show_logs $@
        ;;
    test)
        test_validation $@
        ;;
    detailed-health)
        show_detailed_health
        ;;
    build)
        build_images
        ;;
    *)
        echo "🚀 Telegram Multi-Account Manager"
        echo ""
        echo "Usage: $0 {command} [options]"
        echo ""
        echo "Commands:"
        echo "  setup           - First-time setup (run this first)"
        echo "  start           - Start all accounts"
        echo "  stop            - Stop all accounts"
        echo "  restart         - Restart all accounts"
        echo "  status          - Show accounts status"
        echo "  logs [account]  - Show logs (optional: specific account 1-3)"
        echo "  test [phone]    - Test validation (optional: phone number)"
        echo "  detailed-health - Show detailed health information"
        echo "  build           - Rebuild Docker images"
        echo ""
        echo "Examples:"
        echo "  $0 setup                    # First time setup"
        echo "  $0 start                    # Start all accounts"
        echo "  $0 logs 1                   # Show logs for account 1"
        echo "  $0 test +6281234567890      # Test with specific number"
        echo ""
        echo "Ports:"
        echo "  Account 1: 8081"
        echo "  Account 2: 8082"  
        echo "  Account 3: 8083"
        echo "  Load Balancer: 8090"
        exit 1
        ;;
esac