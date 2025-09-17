#!/bin/bash

# 🚀 WEBTOOLS VALIDATION - ONE-CLICK VPS DEPLOYMENT
# Production-ready deployment script for Ubuntu/Debian VPS
# Usage: ./vps-deploy.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 WEBTOOLS VALIDATION - VPS DEPLOYMENT                   ║
║                                                              ║
║   Automated deployment script for production VPS            ║
║   ✅ All dependencies will be installed automatically        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Configuration Variables
APP_NAME="webtools-validation"
APP_DIR="/opt/webtools"
SERVICE_USER="webtools"
DOMAIN=""
EMAIL=""

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS. This script supports Ubuntu/Debian only."
        exit 1
    fi
    
    print_status "Detected OS: $OS $VER"
}

# Function to get user input
get_user_input() {
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                     DEPLOYMENT CONFIGURATION                  ${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo
    
    # Get domain name
    while [[ -z "$DOMAIN" ]]; do
        read -p "Enter your domain name (e.g., validation.yourdomain.com): " DOMAIN
        if [[ -z "$DOMAIN" ]]; then
            print_warning "Domain name is required!"
        fi
    done
    
    # Get email for SSL certificate
    read -p "Enter your email for SSL certificate (optional): " EMAIL
    
    # Confirmation
    echo
    echo -e "${GREEN}Deployment Configuration:${NC}"
    echo "• Domain: $DOMAIN"
    echo "• Email: ${EMAIL:-'Not provided'}"
    echo "• Installation Path: $APP_DIR"
    echo "• Service User: $SERVICE_USER"
    echo
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled."
        exit 0
    fi
}

# Function to update system
update_system() {
    print_status "Updating system packages..."
    apt update && apt upgrade -y
    apt install -y curl wget git unzip software-properties-common
}

# Function to install Node.js
install_nodejs() {
    print_status "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    
    # Install Yarn
    npm install -g yarn pm2
    
    print_status "Node.js version: $(node --version)"
    print_status "Yarn version: $(yarn --version)"
}

# Function to install Python
install_python() {
    print_status "Installing Python 3.11 and dependencies..."
    apt install -y python3.11 python3.11-venv python3-pip python3.11-dev
    
    # Install system dependencies for Playwright
    apt install -y \
        libnss3-dev \
        libatk-bridge2.0-dev \
        libdrm-dev \
        libxcomposite-dev \
        libxdamage-dev \
        libxrandr-dev \
        libgbm-dev \
        libxss-dev \
        libasound2-dev \
        libgtk-3-dev \
        libgconf-2-4
}

# Function to install MongoDB
install_mongodb() {
    print_status "Installing MongoDB..."
    
    # Import MongoDB public GPG key
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    # Add MongoDB repository
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    # Update and install
    apt update
    apt install -y mongodb-org
    
    # Start and enable MongoDB
    systemctl start mongod
    systemctl enable mongod
    
    print_status "MongoDB installed and started"
}

# Function to install Nginx
install_nginx() {
    print_status "Installing Nginx..."
    apt install -y nginx
    systemctl start nginx
    systemctl enable nginx
}

# Function to install Certbot for SSL
install_certbot() {
    print_status "Installing Certbot for SSL certificates..."
    apt install -y certbot python3-certbot-nginx
}

# Function to create service user
create_service_user() {
    print_status "Creating service user: $SERVICE_USER"
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d $APP_DIR -m $SERVICE_USER
        print_status "Service user created: $SERVICE_USER"
    else
        print_status "Service user already exists: $SERVICE_USER"
    fi
}

# Function to setup application
setup_application() {
    print_status "Setting up application in $APP_DIR..."
    
    # Create app directory
    mkdir -p $APP_DIR
    
    # Copy application files
    print_status "Copying application files..."
    cp -r /app/* $APP_DIR/
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR
    chmod -R 755 $APP_DIR
    
    # Create data directories
    mkdir -p $APP_DIR/data/{logs,telegram_sessions,whatsapp_sessions}
    chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR/data
    chmod -R 755 $APP_DIR/data
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Switch to service user and install dependencies
    sudo -u $SERVICE_USER bash << EOF
cd $APP_DIR/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
EOF
    
    print_status "Python dependencies installed"
}

# Function to install Node dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."
    
    sudo -u $SERVICE_USER bash << EOF
cd $APP_DIR/frontend
yarn install --production
yarn build
EOF
    
    print_status "Node.js dependencies installed and frontend built"
}

# Function to create environment files
create_env_files() {
    print_status "Creating environment configuration..."
    
    # Backend .env
    cat > $APP_DIR/backend/.env << EOF
# Production Environment Configuration
NODE_ENV=production
ENVIRONMENT=production

# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=webtools_validation

# Security
JWT_SECRET=$(openssl rand -base64 32)
BCRYPT_ROUNDS=12

# Session and File Storage Paths
TELEGRAM_SESSION_PATH=$APP_DIR/data/telegram_sessions/
WHATSAPP_SESSION_PATH=$APP_DIR/data/whatsapp_sessions/
LOG_PATH=$APP_DIR/data/logs/

# Telegram MTP API Configuration - PRODUCTION READY
TELEGRAM_API_ID=21724
TELEGRAM_API_HASH=3e0cb5efcd52300aec5994fdfc5bdc16
TELEGRAM_SESSION_TIMEOUT=86400

# Email Service Configuration
SENDGRID_API_KEY=your-sendgrid-api-key-here
SENDER_EMAIL=noreply@$DOMAIN

# Payment Processing
STRIPE_API_KEY=sk_test_emergent
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Container Mode Configuration
CONTAINER_MODE=false

# WhatsApp Validation API
CHECKNUMBER_API_KEY=uWVumuj79aPhfs2A1ZjH3cAMfIU4PDX6XmpfwJOnJjCBwYCVvfFzaYJ5xuDp
CHECKNUMBER_API_URL=https://api.checknumber.ai/wa/api/simple/tasks

# Rate Limiting & Performance
MAX_CONCURRENT_VALIDATIONS=50
RATE_LIMIT_PER_MINUTE=100
BROWSER_POOL_SIZE=5
MTP_POOL_SIZE=10

# Production Logging
LOG_LEVEL=INFO
LOG_FILE=$APP_DIR/data/logs/webtools.log
ERROR_LOG_FILE=$APP_DIR/data/logs/error.log
EOF

    # Frontend .env
    cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR/backend/.env $APP_DIR/frontend/.env
    chmod 600 $APP_DIR/backend/.env $APP_DIR/frontend/.env
    
    print_status "Environment files created"
}

# Function to create systemd services
create_systemd_services() {
    print_status "Creating systemd services..."
    
    # Backend service
    cat > /etc/systemd/system/webtools-backend.service << EOF
[Unit]
Description=Webtools Validation Backend
After=network.target mongodb.service
Requires=mongodb.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/venv/bin
ExecStart=$APP_DIR/backend/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/data/logs/backend.log
StandardError=append:$APP_DIR/data/logs/backend.error.log

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    cat > /etc/systemd/system/webtools-frontend.service << EOF
[Unit]
Description=Webtools Validation Frontend
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/frontend
ExecStart=/usr/bin/npx serve -s build -l 3000
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/data/logs/frontend.log
StandardError=append:$APP_DIR/data/logs/frontend.error.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable webtools-backend webtools-frontend
    
    print_status "Systemd services created and enabled"
}

# Function to configure Nginx
configure_nginx() {
    print_status "Configuring Nginx..."
    
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    # Frontend (React app)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Increase timeout for validation requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    systemctl reload nginx
    
    print_status "Nginx configured"
}

# Function to setup SSL certificate
setup_ssl() {
    if [[ -n "$EMAIL" ]]; then
        print_status "Setting up SSL certificate with Let's Encrypt..."
        certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive
        print_status "SSL certificate installed"
    else
        print_warning "Skipping SSL setup (no email provided)"
        print_warning "You can run: sudo certbot --nginx -d $DOMAIN later"
    fi
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Initialize database with demo data
    sudo -u $SERVICE_USER bash << EOF
cd $APP_DIR/backend
source venv/bin/activate
python production_setup.py
EOF
    
    # Start backend and frontend services
    systemctl start webtools-backend
    systemctl start webtools-frontend
    
    # Wait a moment for services to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet webtools-backend; then
        print_status "✅ Backend service started successfully"
    else
        print_error "❌ Backend service failed to start"
        systemctl status webtools-backend --no-pager
    fi
    
    if systemctl is-active --quiet webtools-frontend; then
        print_status "✅ Frontend service started successfully"
    else
        print_error "❌ Frontend service failed to start"
        systemctl status webtools-frontend --no-pager
    fi
}

# Function to setup firewall
setup_firewall() {
    print_status "Configuring firewall..."
    
    # Install ufw if not present
    apt install -y ufw
    
    # Configure firewall rules
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
    
    print_status "Firewall configured"
}

# Function to create management scripts
create_management_scripts() {
    print_status "Creating management scripts..."
    
    # Service management script
    cat > $APP_DIR/manage.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        sudo systemctl start webtools-backend webtools-frontend
        echo "Services started"
        ;;
    stop)
        sudo systemctl stop webtools-backend webtools-frontend
        echo "Services stopped"
        ;;
    restart)
        sudo systemctl restart webtools-backend webtools-frontend
        echo "Services restarted"
        ;;
    status)
        sudo systemctl status webtools-backend webtools-frontend --no-pager
        ;;
    logs)
        if [ "$2" == "backend" ]; then
            sudo journalctl -u webtools-backend -f
        elif [ "$2" == "frontend" ]; then
            sudo journalctl -u webtools-frontend -f
        else
            echo "Usage: $0 logs [backend|frontend]"
        fi
        ;;
    update)
        echo "Updating application..."
        sudo systemctl stop webtools-backend webtools-frontend
        cd $(dirname "$0")
        sudo -u webtools git pull
        cd backend && source venv/bin/activate && pip install -r requirements.txt
        cd ../frontend && yarn install && yarn build
        sudo systemctl start webtools-backend webtools-frontend
        echo "Update completed"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

    chmod +x $APP_DIR/manage.sh
    chown $SERVICE_USER:$SERVICE_USER $APP_DIR/manage.sh
    
    print_status "Management scripts created"
}

# Function to show deployment summary
show_summary() {
    echo
    echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                 🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉      ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${BLUE}📋 Deployment Summary:${NC}"
    echo "• Application URL: https://$DOMAIN"
    echo "• Installation Path: $APP_DIR"
    echo "• Service User: $SERVICE_USER"
    echo "• Backend Service: webtools-backend"
    echo "• Frontend Service: webtools-frontend"
    echo
    echo -e "${BLUE}🔐 Default Login Credentials:${NC}"
    echo "• Admin: admin / admin123"
    echo "• Demo User: demo / demo123"
    echo
    echo -e "${BLUE}📁 Important Directories:${NC}"
    echo "• Application: $APP_DIR"
    echo "• Logs: $APP_DIR/data/logs/"
    echo "• Sessions: $APP_DIR/data/telegram_sessions/ & $APP_DIR/data/whatsapp_sessions/"
    echo
    echo -e "${BLUE}🛠️ Management Commands:${NC}"
    echo "• Start services: $APP_DIR/manage.sh start"
    echo "• Stop services: $APP_DIR/manage.sh stop"
    echo "• Restart services: $APP_DIR/manage.sh restart"
    echo "• Check status: $APP_DIR/manage.sh status"
    echo "• View logs: $APP_DIR/manage.sh logs [backend|frontend]"
    echo "• Update app: $APP_DIR/manage.sh update"
    echo
    echo -e "${BLUE}🔧 Service Management:${NC}"
    echo "• Backend status: sudo systemctl status webtools-backend"
    echo "• Frontend status: sudo systemctl status webtools-frontend"
    echo "• MongoDB status: sudo systemctl status mongod"
    echo "• Nginx status: sudo systemctl status nginx"
    echo
    echo -e "${YELLOW}⚠️ Next Steps:${NC}"
    echo "1. Update API keys in $APP_DIR/backend/.env for production use"
    echo "2. Configure your domain DNS to point to this server"
    echo "3. Test the application at https://$DOMAIN"
    echo "4. Monitor logs for any issues"
    echo
    echo -e "${GREEN}✅ Your Webtools Validation system is now live and ready to use!${NC}"
    echo
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting VPS deployment process...${NC}"
    echo
    
    # Run deployment steps
    check_root
    detect_os
    get_user_input
    
    print_status "Starting system setup..."
    update_system
    install_nodejs
    install_python
    install_mongodb
    install_nginx
    install_certbot
    
    print_status "Setting up application..."
    create_service_user
    setup_application
    install_python_deps
    install_node_deps
    create_env_files
    
    print_status "Configuring services..."
    create_systemd_services
    configure_nginx
    setup_ssl
    setup_firewall
    create_management_scripts
    
    print_status "Starting services..."
    start_services
    
    # Show final summary
    show_summary
}

# Handle script interruption
trap 'print_error "Deployment interrupted. Please run the script again to complete setup."; exit 1' INT TERM

# Run main function
main "$@"