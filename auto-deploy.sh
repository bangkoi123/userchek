#!/bin/bash

# 🚀 WebTools Auto-Deployment Script
# One-command deployment untuk production VPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="webtools"
APP_DIR="/opt/webtools"
DOMAIN=""
EMAIL=""

# Banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    WebTools Auto-Deploy                     ║"
    echo "║              Multi-Platform Validation Service              ║"
    echo "║                  Production Ready v1.0                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"  
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
    
    if ! sudo -n true 2>/dev/null; then
        error "This script requires sudo privileges"
        exit 1
    fi
}

# System requirements check
check_requirements() {
    log "Checking system requirements..."
    
    # Check Ubuntu/Debian
    if ! command -v apt &> /dev/null; then
        error "This script requires Ubuntu/Debian"
        exit 1
    fi
    
    # Check system specs
    RAM=$(free -g | awk 'NR==2{printf "%d", $2}')
    if [ $RAM -lt 2 ]; then
        warning "Minimum 4GB RAM recommended (found ${RAM}GB)"
        read -p "Continue anyway? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check disk space
    DISK=$(df -h / | awk 'NR==2{print $4}' | head -c -2)
    if [ $DISK -lt 10 ]; then
        error "Minimum 10GB free disk space required"
        exit 1
    fi
    
    log "✅ System requirements check passed"
}

# Collect user input
collect_input() {
    log "Collecting deployment configuration..."
    
    echo -e "${BLUE}Please provide the following information:${NC}"
    
    read -p "Domain name (e.g., webtools.example.com): " DOMAIN
    if [[ -z "$DOMAIN" ]]; then
        DOMAIN="localhost"
        warning "Using localhost - you can configure domain later"
    fi
    
    read -p "Admin email (for SSL certificates): " EMAIL
    if [[ -z "$EMAIL" ]]; then
        EMAIL="admin@example.com"
        warning "Using default email - update later if needed"
    fi
    
    read -p "Stripe API Key (optional, press Enter to skip): " STRIPE_KEY
    read -p "CheckNumber.ai API Key (optional, press Enter to skip): " CHECKNUMBER_KEY
    read -p "Telegram API ID (optional, press Enter to skip): " TELEGRAM_API_ID
    read -p "Telegram API Hash (optional, press Enter to skip): " TELEGRAM_API_HASH
    
    log "Configuration collected"
}

# Update system packages
update_system() {
    log "Updating system packages..."
    sudo apt update -qq
    sudo apt upgrade -y -qq
    log "✅ System updated"
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    # Install basic tools
    sudo apt install -y -qq curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
    
    # Install Node.js 18
    log "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - > /dev/null 2>&1
    sudo apt-get install -y -qq nodejs
    
    # Install Python 3.9+
    log "Installing Python..."
    sudo apt install -y -qq python3 python3-pip python3-venv python3-dev
    
    # Install MongoDB 6.0
    log "Installing MongoDB..."
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add - > /dev/null 2>&1
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list > /dev/null
    sudo apt update -qq
    sudo apt install -y -qq mongodb-org
    
    # Install Redis
    log "Installing Redis..."
    sudo apt install -y -qq redis-server
    
    # Install Nginx
    log "Installing Nginx..."
    sudo apt install -y -qq nginx
    
    # Install Supervisor for process management
    log "Installing Supervisor..."
    sudo apt install -y -qq supervisor
    
    log "✅ Dependencies installed"
}

# Setup application
setup_application() {
    log "Setting up WebTools application..."
    
    # Create application directory
    sudo mkdir -p $APP_DIR
    sudo chown -R $USER:www-data $APP_DIR
    
    # Clone application (placeholder - replace with actual repo)
    if [ -d "/app" ]; then
        log "Copying application from /app..."
        cp -r /app/* $APP_DIR/
    else
        # git clone https://github.com/your-repo/webtools.git $APP_DIR
        error "Application source not found. Please provide repository URL."
        exit 1
    fi
    
    cd $APP_DIR
    
    # Setup backend
    log "Setting up backend..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Install Playwright browsers
    log "Installing Playwright browsers..."
    playwright install chromium > /dev/null 2>&1
    
    # Setup frontend  
    log "Setting up frontend..."
    cd ../frontend
    npm install --production > /dev/null 2>&1
    npm run build > /dev/null 2>&1
    
    log "✅ Application setup complete"
}

# Configure environment
configure_environment() {
    log "Configuring environment..."
    
    # Generate random secrets
    JWT_SECRET=$(openssl rand -hex 32)
    
    # Create backend environment file
    cat > $APP_DIR/backend/.env << EOF
# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=webtools_validation

# Security
JWT_SECRET=${JWT_SECRET}

# External APIs
STRIPE_API_KEY=${STRIPE_KEY:-sk_test_your_stripe_key_here}
CHECKNUMBER_API_KEY=${CHECKNUMBER_KEY:-your_checknumber_key_here}

# Telegram MTP Configuration
TELEGRAM_API_ID=${TELEGRAM_API_ID:-your_telegram_api_id}
TELEGRAM_API_HASH=${TELEGRAM_API_HASH:-your_telegram_api_hash}

# Email Configuration
SENDGRID_API_KEY=your_sendgrid_key_here
SENDER_EMAIL=noreply@${DOMAIN}

# System Configuration
CONTAINER_MODE=false
DEBUG=false
EOF

    # Create frontend environment file
    if [[ "$DOMAIN" == "localhost" ]]; then
        BACKEND_URL="http://localhost:8001"
    else
        BACKEND_URL="https://${DOMAIN}"
    fi
    
    cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=${BACKEND_URL}
EOF

    log "✅ Environment configured"
}

# Configure services
configure_services() {
    log "Configuring system services..."
    
    # Start and enable MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    # Start and enable Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Create Supervisor configuration for backend
    sudo tee /etc/supervisor/conf.d/webtools-backend.conf << EOF > /dev/null
[program:webtools-backend]
command=${APP_DIR}/backend/venv/bin/python server.py
directory=${APP_DIR}/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/webtools-backend.log
environment=PATH="${APP_DIR}/backend/venv/bin"
EOF

    # Create Supervisor configuration for frontend (if not using Nginx static files)
    if [[ "$DOMAIN" == "localhost" ]]; then
        sudo tee /etc/supervisor/conf.d/webtools-frontend.conf << EOF > /dev/null
[program:webtools-frontend]
command=/usr/bin/npm start
directory=${APP_DIR}/frontend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/webtools-frontend.log
environment=PORT="3000"
EOF
    fi
    
    # Reload Supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start all
    
    log "✅ Services configured"
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    # Remove default configuration
    sudo rm -f /etc/nginx/sites-enabled/default
    
    if [[ "$DOMAIN" == "localhost" ]]; then
        # Development configuration
        sudo tee /etc/nginx/sites-available/webtools << EOF > /dev/null
server {
    listen 80 default_server;
    server_name localhost;
    
    # Frontend (React dev server)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF
    else
        # Production configuration
        sudo tee /etc/nginx/sites-available/webtools << EOF > /dev/null
server {
    listen 80;
    server_name ${DOMAIN};
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};
    
    # SSL configuration (will be added by Certbot)
    
    # Frontend (React build)
    location / {
        root ${APP_DIR}/frontend/build;
        try_files \$uri \$uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    fi
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/webtools /etc/nginx/sites-enabled/
    
    # Test configuration
    sudo nginx -t
    sudo systemctl restart nginx
    
    log "✅ Nginx configured"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    if [[ "$DOMAIN" != "localhost" ]]; then
        log "Setting up SSL certificate..."
        
        # Install Certbot
        sudo apt install -y -qq certbot python3-certbot-nginx
        
        # Get certificate
        sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect
        
        # Setup auto-renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
        
        log "✅ SSL certificate configured"
    else
        log "⚠️ SSL skipped for localhost"
    fi
}

# Setup firewall
setup_firewall() {
    log "Configuring firewall..."
    
    # Install UFW if not present
    sudo apt install -y -qq ufw
    
    # Configure firewall rules
    sudo ufw --force reset > /dev/null 2>&1
    sudo ufw default deny incoming > /dev/null 2>&1
    sudo ufw default allow outgoing > /dev/null 2>&1
    sudo ufw allow ssh > /dev/null 2>&1
    sudo ufw allow 'Nginx Full' > /dev/null 2>&1
    sudo ufw --force enable > /dev/null 2>&1
    
    log "✅ Firewall configured"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Create log rotation for application logs
    sudo tee /etc/logrotate.d/webtools << EOF > /dev/null
/var/log/webtools-*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 www-data www-data
}
EOF

    # Create health check script
    sudo tee /usr/local/bin/webtools-health << 'EOF' > /dev/null
#!/bin/bash
# Simple health check for WebTools

# Check if backend is responding
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Backend: Healthy"
else
    echo "❌ Backend: Down"
    sudo supervisorctl restart webtools-backend
fi

# Check MongoDB
if systemctl is-active --quiet mongod; then
    echo "✅ MongoDB: Running"
else
    echo "❌ MongoDB: Down"
    sudo systemctl start mongod
fi

# Check Redis
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Down"  
    sudo systemctl start redis-server
fi

# Check Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx: Running"
else
    echo "❌ Nginx: Down"
    sudo systemctl start nginx
fi
EOF

    sudo chmod +x /usr/local/bin/webtools-health
    
    # Add health check to cron (every 5 minutes)
    echo "*/5 * * * * /usr/local/bin/webtools-health >> /var/log/webtools-health.log 2>&1" | sudo crontab -
    
    log "✅ Monitoring configured"
}

# Create management scripts
create_management_scripts() {
    log "Creating management scripts..."
    
    # Create management script
    sudo tee /usr/local/bin/webtools << 'EOF' > /dev/null
#!/bin/bash
# WebTools management script

case "$1" in
    start)
        echo "Starting WebTools..."
        sudo systemctl start mongod redis-server nginx
        sudo supervisorctl start all
        echo "✅ WebTools started"
        ;;
    stop)
        echo "Stopping WebTools..."
        sudo supervisorctl stop all
        sudo systemctl stop nginx
        echo "✅ WebTools stopped"
        ;;
    restart)
        echo "Restarting WebTools..."
        sudo supervisorctl restart all
        sudo systemctl restart nginx
        echo "✅ WebTools restarted"
        ;;
    status)
        echo "WebTools Status:"
        sudo supervisorctl status
        echo ""
        systemctl status mongod redis-server nginx --no-pager -l
        ;;
    logs)
        echo "WebTools Logs:"
        sudo tail -f /var/log/webtools-*.log
        ;;
    update)
        echo "Updating WebTools..."
        cd /opt/webtools
        git pull
        cd backend && source venv/bin/activate && pip install -r requirements.txt
        cd ../frontend && npm install && npm run build
        sudo supervisorctl restart all
        echo "✅ WebTools updated"
        ;;
    health)
        /usr/local/bin/webtools-health
        ;;
    *)
        echo "Usage: webtools {start|stop|restart|status|logs|update|health}"
        exit 1
        ;;
esac
EOF

    sudo chmod +x /usr/local/bin/webtools
    
    log "✅ Management scripts created"
}

# Final setup and verification
final_setup() {
    log "Performing final setup and verification..."
    
    # Set proper permissions
    sudo chown -R www-data:www-data $APP_DIR
    sudo chmod -R 755 $APP_DIR
    
    # Wait for services to start
    sleep 10
    
    # Verify services are running
    if sudo supervisorctl status webtools-backend | grep -q RUNNING; then
        log "✅ Backend service is running"
    else
        error "Backend service failed to start"
        sudo supervisorctl tail webtools-backend
    fi
    
    if systemctl is-active --quiet nginx; then
        log "✅ Nginx is running"
    else
        error "Nginx failed to start"
    fi
    
    # Test application
    sleep 5
    if curl -s http://localhost:8001/api/health > /dev/null; then
        log "✅ Application is responding"
    else
        warning "Application health check failed - may need manual configuration"
    fi
    
    log "✅ Final setup complete"
}

# Display completion message
show_completion() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 DEPLOYMENT COMPLETE! 🎉                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${BLUE}📋 Deployment Summary:${NC}"
    echo "  • Application: WebTools Multi-Platform Validation Service"
    echo "  • Location: $APP_DIR"
    echo "  • Domain: $DOMAIN"
    echo "  • SSL: $([ "$DOMAIN" != "localhost" ] && echo "Enabled" || echo "Not configured")"
    
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    if [[ "$DOMAIN" == "localhost" ]]; then
        echo "  • Application: http://localhost"
        echo "  • Backend API: http://localhost:8001/api"
    else
        echo "  • Application: https://$DOMAIN"
        echo "  • Backend API: https://$DOMAIN/api"
    fi
    
    echo ""
    echo -e "${BLUE}👤 Default Credentials:${NC}"
    echo "  • Admin: admin / admin123"
    echo "  • Demo: demo / demo123"
    
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • webtools start      - Start all services"
    echo "  • webtools stop       - Stop all services"
    echo "  • webtools restart    - Restart all services"
    echo "  • webtools status     - Check service status"
    echo "  • webtools logs       - View application logs"
    echo "  • webtools health     - Run health check"
    echo "  • webtools update     - Update application"
    
    echo ""
    echo -e "${BLUE}📁 Important Files:${NC}"
    echo "  • Application: $APP_DIR"
    echo "  • Backend Config: $APP_DIR/backend/.env"
    echo "  • Frontend Config: $APP_DIR/frontend/.env"
    echo "  • Nginx Config: /etc/nginx/sites-available/webtools"
    echo "  • Logs: /var/log/webtools-*.log"
    
    echo ""
    echo -e "${BLUE}⚙️ Next Steps:${NC}"
    echo "  1. Update API keys in: $APP_DIR/backend/.env"
    echo "  2. Configure domain DNS (if using custom domain)"
    echo "  3. Test application functionality"
    echo "  4. Setup monitoring and backups"
    echo "  5. Configure payment settings (Stripe)"
    
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo "  • Run 'webtools health' to check system status"
    echo "  • Logs are available at /var/log/webtools-*.log"
    echo "  • Application auto-starts on system boot"
    echo "  • SSL certificates auto-renew via cron"
    
    echo ""
    echo -e "${GREEN}🚀 WebTools is now ready for production use!${NC}"
}

# Main deployment function
main() {
    show_banner
    
    # Check if rerunning
    if [ -d "$APP_DIR" ]; then
        warning "WebTools appears to already be installed at $APP_DIR"
        read -p "Do you want to reinstall? This will overwrite existing installation [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            exit 0
        fi
        sudo rm -rf $APP_DIR
    fi
    
    check_root
    check_requirements
    collect_input
    
    echo ""
    log "🚀 Starting WebTools deployment..."
    
    update_system
    install_dependencies
    setup_application
    configure_environment
    configure_services
    configure_nginx
    setup_ssl
    setup_firewall
    setup_monitoring
    create_management_scripts
    final_setup
    
    show_completion
}

# Trap errors
trap 'error "Deployment failed at line $LINENO. Check the logs above."; exit 1' ERR

# Run deployment
main "$@"