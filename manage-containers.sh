#!/bin/bash

# WhatsApp Account Container Management Script
# Provides easy commands to manage WhatsApp account containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_help() {
    echo -e "${BLUE}WebTools WhatsApp Container Manager${NC}"
    echo -e "${BLUE}====================================${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC} $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}list${NC}                    List all WhatsApp account containers"
    echo -e "  ${GREEN}create${NC} <account_id>     Create container for account"
    echo -e "  ${GREEN}start${NC} <account_id>      Start account container"
    echo -e "  ${GREEN}stop${NC} <account_id>       Stop account container"
    echo -e "  ${GREEN}restart${NC} <account_id>    Restart account container"
    echo -e "  ${GREEN}destroy${NC} <account_id>    Destroy account container"
    echo -e "  ${GREEN}logs${NC} <account_id>       Show container logs"
    echo -e "  ${GREEN}exec${NC} <account_id>       Execute command in container"
    echo -e "  ${GREEN}health${NC} <account_id>     Check container health"
    echo -e "  ${GREEN}cleanup${NC}                 Clean up orphaned containers"
    echo -e "  ${GREEN}stats${NC}                   Show container statistics"
    echo -e "  ${GREEN}proxy${NC} <account_id>      Configure proxy for account"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 list"
    echo -e "  $0 create account_123"
    echo -e "  $0 logs account_123"
    echo -e "  $0 proxy account_123"
    echo ""
}

list_containers() {
    echo -e "${CYAN}📋 WhatsApp Account Containers${NC}"
    echo -e "${CYAN}==============================${NC}"
    
    containers=$(docker ps -a --filter "name=whatsapp_account_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")
    
    if [ -z "$containers" ]; then
        echo -e "${YELLOW}No WhatsApp account containers found${NC}"
        return
    fi
    
    echo "$containers"
    echo ""
    echo -e "${GREEN}Total containers: $(docker ps -a --filter 'name=whatsapp_account_' -q | wc -l)${NC}"
}

create_container() {
    local account_id="$1"
    
    if [ -z "$account_id" ]; then
        echo -e "${RED}❌ Account ID is required${NC}"
        echo -e "Usage: $0 create <account_id>"
        exit 1
    fi
    
    echo -e "${CYAN}🐳 Creating container for account: ${account_id}${NC}"
    
    # Check if container already exists
    if docker ps -a --filter "name=whatsapp_account_${account_id}" --format "{{.Names}}" | grep -q "whatsapp_account_${account_id}"; then
        echo -e "${YELLOW}⚠️ Container for account ${account_id} already exists${NC}"
        return 1
    fi
    
    # Create container
    docker run -d \
        --name "whatsapp_account_${account_id}" \
        --network "webtools_webtools-network" \
        -e ACCOUNT_ID="$account_id" \
        -e MONGO_URL="mongodb://admin:password123@mongo:27017/webtools_validation?authSource=admin" \
        -e MAIN_API_URL="http://main-api:8001" \
        -e REDIS_URL="redis://redis:6379" \
        -v "whatsapp_sessions_${account_id}:/app/sessions" \
        --restart unless-stopped \
        --memory="512m" \
        --cpus="0.5" \
        webtools-whatsapp-account:latest
    
    echo -e "${GREEN}✅ Container created successfully for account: ${account_id}${NC}"
}

container_action() {
    local action="$1"
    local account_id="$2"
    local container_name="whatsapp_account_${account_id}"
    
    if [ -z "$account_id" ]; then
        echo -e "${RED}❌ Account ID is required${NC}"
        echo -e "Usage: $0 $action <account_id>"
        exit 1
    fi
    
    case "$action" in
        "start")
            echo -e "${CYAN}▶️ Starting container: ${container_name}${NC}"
            docker start "$container_name"
            ;;
        "stop")
            echo -e "${CYAN}⏹️ Stopping container: ${container_name}${NC}"
            docker stop "$container_name"
            ;;
        "restart")
            echo -e "${CYAN}🔄 Restarting container: ${container_name}${NC}"
            docker restart "$container_name"
            ;;
        "destroy")
            echo -e "${CYAN}💥 Destroying container: ${container_name}${NC}"
            read -p "Are you sure you want to destroy this container? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker stop "$container_name" 2>/dev/null || true
                docker rm -f "$container_name" 2>/dev/null || true
                docker volume rm "whatsapp_sessions_${account_id}" 2>/dev/null || true
                echo -e "${GREEN}✅ Container destroyed: ${container_name}${NC}"
            else
                echo -e "${YELLOW}❌ Operation cancelled${NC}"
            fi
            ;;
    esac
}

show_logs() {
    local account_id="$1"
    local container_name="whatsapp_account_${account_id}"
    
    if [ -z "$account_id" ]; then
        echo -e "${RED}❌ Account ID is required${NC}"
        echo -e "Usage: $0 logs <account_id>"
        exit 1
    fi
    
    echo -e "${CYAN}📋 Logs for container: ${container_name}${NC}"
    echo -e "${CYAN}$(printf '=%.0s' {1..50})${NC}"
    
    docker logs -f "$container_name"
}

exec_command() {
    local account_id="$1"
    local container_name="whatsapp_account_${account_id}"
    shift
    local command="$@"
    
    if [ -z "$account_id" ]; then
        echo -e "${RED}❌ Account ID is required${NC}"
        echo -e "Usage: $0 exec <account_id> [command]"
        exit 1
    fi
    
    if [ -z "$command" ]; then
        command="/bin/bash"
    fi
    
    echo -e "${CYAN}🖥️ Executing in container: ${container_name}${NC}"
    docker exec -it "$container_name" $command
}

check_health() {
    local account_id="$1"
    local container_name="whatsapp_account_${account_id}"
    
    if [ -z "$account_id" ]; then
        echo -e "${RED}❌ Account ID is required${NC}"
        echo -e "Usage: $0 health <account_id>"
        exit 1
    fi
    
    echo -e "${CYAN}🏥 Health check for: ${container_name}${NC}"
    echo -e "${CYAN}$(printf '=%.0s' {1..30})${NC}"
    
    # Check if container is running
    if ! docker ps --filter "name=${container_name}" --format "{{.Names}}" | grep -q "${container_name}"; then
        echo -e "${RED}❌ Container is not running${NC}"
        return 1
    fi
    
    # Get container port
    port=$(docker port "$container_name" 8080/tcp | cut -d: -f2)
    
    if [ -z "$port" ]; then
        echo -e "${RED}❌ Container port not found${NC}"
        return 1
    fi
    
    # Check health endpoint
    if curl -s "http://localhost:${port}/health" > /dev/null; then
        echo -e "${GREEN}✅ Container is healthy${NC}"
        curl -s "http://localhost:${port}/health" | python -m json.tool 2>/dev/null || echo "Health data received"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        return 1
    fi
}

cleanup_containers() {
    echo -e "${CYAN}🧹 Cleaning up orphaned containers${NC}"
    
    # Stop and remove containers without corresponding database records
    containers=$(docker ps -a --filter "name=whatsapp_account_" --format "{{.Names}}")
    
    if [ -z "$containers" ]; then
        echo -e "${GREEN}✅ No containers to clean up${NC}"
        return
    fi
    
    echo "Found containers to review:"
    echo "$containers"
    echo ""
    
    read -p "Remove all WhatsApp account containers? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$containers" | while read container; do
            if [ -n "$container" ]; then
                echo -e "${YELLOW}Removing: $container${NC}"
                docker stop "$container" 2>/dev/null || true
                docker rm -f "$container" 2>/dev/null || true
            fi
        done
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    else
        echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
    fi
}

show_stats() {
    echo -e "${CYAN}📊 Container Statistics${NC}"
    echo -e "${CYAN}======================${NC}"
    
    total_containers=$(docker ps -a --filter "name=whatsapp_account_" -q | wc -l)
    running_containers=$(docker ps --filter "name=whatsapp_account_" -q | wc -l)
    stopped_containers=$((total_containers - running_containers))
    
    echo -e "${GREEN}Total Containers: ${total_containers}${NC}"
    echo -e "${GREEN}Running: ${running_containers}${NC}"
    echo -e "${YELLOW}Stopped: ${stopped_containers}${NC}"
    echo ""
    
    if [ "$running_containers" -gt 0 ]; then
        echo -e "${CYAN}Resource Usage:${NC}"
        docker stats --no-stream --filter "name=whatsapp_account_" --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "Stats not available"
    fi
}

configure_proxy() {
    local account_id="$1"
    
    if [ -z "$account_id" ]; then
        echo -e "${RED}❌ Account ID is required${NC}"
        echo -e "Usage: $0 proxy <account_id>"
        exit 1
    fi
    
    echo -e "${CYAN}🌐 Proxy Configuration for Account: ${account_id}${NC}"
    echo -e "${CYAN}$(printf '=%.0s' {1..40})${NC}"
    
    read -p "Proxy URL (e.g., http://proxy-server:port): " proxy_url
    read -p "Proxy Username (optional): " proxy_username
    read -s -p "Proxy Password (optional): " proxy_password
    echo ""
    
    if [ -n "$proxy_url" ]; then
        echo -e "${YELLOW}Recreating container with proxy configuration...${NC}"
        
        # Stop and remove existing container
        docker stop "whatsapp_account_${account_id}" 2>/dev/null || true
        docker rm -f "whatsapp_account_${account_id}" 2>/dev/null || true
        
        # Create new container with proxy
        docker run -d \
            --name "whatsapp_account_${account_id}" \
            --network "webtools_webtools-network" \
            -e ACCOUNT_ID="$account_id" \
            -e MONGO_URL="mongodb://admin:password123@mongo:27017/webtools_validation?authSource=admin" \
            -e MAIN_API_URL="http://main-api:8001" \
            -e REDIS_URL="redis://redis:6379" \
            -e PROXY_URL="$proxy_url" \
            -e PROXY_USERNAME="$proxy_username" \
            -e PROXY_PASSWORD="$proxy_password" \
            -v "whatsapp_sessions_${account_id}:/app/sessions" \
            --restart unless-stopped \
            --memory="512m" \
            --cpus="0.5" \
            webtools-whatsapp-account:latest
        
        echo -e "${GREEN}✅ Container recreated with proxy configuration${NC}"
    else
        echo -e "${YELLOW}❌ No proxy URL provided, configuration cancelled${NC}"
    fi
}

# Main script logic
case "${1:-help}" in
    "list")
        list_containers
        ;;
    "create")
        create_container "$2"
        ;;
    "start"|"stop"|"restart"|"destroy")
        container_action "$1" "$2"
        ;;
    "logs")
        show_logs "$2"
        ;;
    "exec")
        exec_command "$2" "${@:3}"
        ;;
    "health")
        check_health "$2"
        ;;
    "cleanup")
        cleanup_containers
        ;;
    "stats")
        show_stats
        ;;
    "proxy")
        configure_proxy "$2"
        ;;
    "help"|*)
        print_help
        ;;
esac