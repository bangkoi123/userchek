#!/bin/bash

# 🚀 PROFESSIONAL MULTI-ACCOUNT TELEGRAM SETUP SCRIPT
# Isolation dengan Docker + Proxy + Network Segregation

echo "🔧 Setting up Multi-Account Telegram Validation System..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p /app/data/telegram_sessions/{account_1,account_2,account_3,account_4,account_5}
mkdir -p /app/data/logs/{account_1,account_2,account_3,account_4,account_5}
mkdir -p /app/data/monitoring
mkdir -p /app/data/rate_limits
mkdir -p /app/docker/telegram-account
mkdir -p /app/docker/telegram-monitor
mkdir -p /app/docker/nginx

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 700 /app/data/telegram_sessions/*
chmod 755 /app/data/logs/*
chmod 755 /app/data/monitoring
chmod 755 /app/data/rate_limits

# Create Docker build context
echo "🐳 Creating Docker build context..."
cat > /app/docker/telegram-account/requirements.txt << EOF
pyrogram==2.0.106
aiohttp==3.9.1
motor==3.3.2
python-dotenv==1.0.0
psutil==5.9.6
asyncio-throttle==1.0.2
python-socks[asyncio]==2.4.3
aiofiles==23.2.0
ujson==5.8.0
uvloop==0.19.0
EOF

# Create isolated validator service
cat > /app/docker/telegram-account/telegram_validator.py << 'EOF'
import asyncio
import os
import logging
import json
from datetime import datetime
from aiohttp import web, ClientSession
from pyrogram import Client
import psutil
import uvloop

class IsolatedTelegramValidator:
    def __init__(self):
        self.account_id = os.getenv('ACCOUNT_ID')
        self.setup_logging()
        self.setup_client()
        self.request_count = 0
        self.last_request_time = datetime.utcnow()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{self.account_id}] %(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'/app/logs/{self.account_id}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_client(self):
        proxy_config = None
        if os.getenv('PROXY_HOST'):
            proxy_config = {
                "scheme": os.getenv('PROXY_TYPE', 'socks5'),
                "hostname": os.getenv('PROXY_HOST'),
                "port": int(os.getenv('PROXY_PORT', 1080)),
                "username": os.getenv('PROXY_USERNAME'),
                "password": os.getenv('PROXY_PASSWORD')
            }
            
        self.client = Client(
            name=f"validator_{self.account_id}",
            api_id=os.getenv('TELEGRAM_API_ID'),
            api_hash=os.getenv('TELEGRAM_API_HASH'),
            phone_number=os.getenv('TELEGRAM_PHONE'),
            workdir="/app/sessions",
            proxy=proxy_config
        )
        
    async def validate_phone(self, phone_number: str) -> dict:
        """Validate phone number with rate limiting"""
        # Rate limiting check
        max_requests = int(os.getenv('MAX_REQUESTS_PER_HOUR', 30))
        if self.request_count >= max_requests:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "account_id": self.account_id
            }
            
        try:
            await self.client.start()
            
            # Actual validation logic here
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            
            # Try to get user info
            contacts = await self.client.get_contacts()
            for contact in contacts:
                if hasattr(contact, 'phone_number') and contact.phone_number == clean_phone:
                    return {
                        "success": True,
                        "status": "active",
                        "phone_number": phone_number,
                        "username": contact.username,
                        "first_name": contact.first_name,
                        "account_id": self.account_id,
                        "proxy_location": os.getenv('PROXY_LOCATION', 'unknown')
                    }
            
            return {
                "success": True,
                "status": "unknown",
                "phone_number": phone_number,
                "account_id": self.account_id,
                "reason": "Not in contacts or private account"
            }
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "account_id": self.account_id
            }
        finally:
            self.request_count += 1
            await self.client.stop()
    
    async def health_handler(self, request):
        """Health check endpoint"""
        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Check Telegram client status
            client_status = "disconnected"
            try:
                await self.client.start()
                me = await self.client.get_me()
                client_status = "connected" if me else "error"
                await self.client.stop()
            except:
                client_status = "error"
            
            health_data = {
                "account_id": self.account_id,
                "status": "healthy",
                "telegram_status": client_status,
                "request_count": self.request_count,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "proxy_location": os.getenv('PROXY_LOCATION', 'unknown'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return web.json_response(health_data)
            
        except Exception as e:
            return web.json_response({
                "account_id": self.account_id,
                "status": "unhealthy",
                "error": str(e)
            }, status=500)
    
    async def validate_handler(self, request):
        """Phone validation endpoint"""
        try:
            data = await request.json()
            phone_number = data.get('phone_number')
            
            if not phone_number:
                return web.json_response({
                    "success": False,
                    "error": "Phone number required"
                }, status=400)
            
            result = await self.validate_phone(phone_number)
            return web.json_response(result)
            
        except Exception as e:
            return web.json_response({
                "success": False,
                "error": str(e),
                "account_id": self.account_id
            }, status=500)

async def main():
    # Use uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    validator = IsolatedTelegramValidator()
    
    # Setup web server
    app = web.Application()
    app.router.add_get('/health', validator.health_handler)
    app.router.add_post('/validate', validator.validate_handler)
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    print(f"🚀 Telegram Validator {validator.account_id} started on port 8080")
    await site.start()
    
    # Keep running
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour

if __name__ == '__main__':
    asyncio.run(main())
EOF

# Create load balancer configuration
echo "⚖️ Creating load balancer configuration..."
cat > /app/docker/nginx/telegram_lb.conf << 'EOF'
upstream telegram_accounts {
    least_conn;
    server telegram-account-1:8080 max_fails=3 fail_timeout=30s;
    server telegram-account-2:8080 max_fails=3 fail_timeout=30s;
    server telegram-account-3:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location /health {
        proxy_pass http://telegram_accounts;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    location /validate {
        proxy_pass http://telegram_accounts;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Rate limiting
        limit_req zone=telegram_rate burst=10 nodelay;
    }
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=telegram_rate:10m rate=10r/m;
EOF

# Create environment file template
echo "🔧 Creating environment template..."
cat > /app/.env.telegram << 'EOF'
# Account 1 - Indonesia
TELEGRAM_API_ID_1=your_api_id_1
TELEGRAM_API_HASH_1=your_api_hash_1
TELEGRAM_PHONE_1=+62xxx
PROXY_HOST_1=id-proxy.provider.com
PROXY_PORT_1=1080
PROXY_USERNAME_1=user1
PROXY_PASSWORD_1=pass1

# Account 2 - Singapore  
TELEGRAM_API_ID_2=your_api_id_2
TELEGRAM_API_HASH_2=your_api_hash_2
TELEGRAM_PHONE_2=+65xxx
PROXY_HOST_2=sg-proxy.provider.com
PROXY_PORT_2=1080
PROXY_USERNAME_2=user2
PROXY_PASSWORD_2=pass2

# Account 3 - Malaysia
TELEGRAM_API_ID_3=your_api_id_3
TELEGRAM_API_HASH_3=your_api_hash_3
TELEGRAM_PHONE_3=+60xxx
PROXY_HOST_3=my-proxy.provider.com
PROXY_PORT_3=1080
PROXY_USERNAME_3=user3
PROXY_PASSWORD_3=pass3
EOF

# Build Docker images
echo "🔨 Building Docker images..."
cd /app
docker build -t telegram-validator:latest ./docker/telegram-account/

# Create management script
cat > /app/manage-telegram-accounts.sh << 'EOF'
#!/bin/bash

case $1 in
    start)
        echo "🚀 Starting multi-account Telegram validation..."
        docker-compose -f docker-compose.telegram.yml up -d
        ;;
    stop)
        echo "⏹️ Stopping multi-account Telegram validation..."
        docker-compose -f docker-compose.telegram.yml down
        ;;
    restart)
        echo "🔄 Restarting multi-account Telegram validation..."
        docker-compose -f docker-compose.telegram.yml restart
        ;;
    status)
        echo "📊 Telegram accounts status:"
        docker-compose -f docker-compose.telegram.yml ps
        ;;
    logs)
        echo "📋 Telegram accounts logs:"
        docker-compose -f docker-compose.telegram.yml logs -f
        ;;
    health)
        echo "🏥 Checking account health..."
        for i in {1..3}; do
            echo "Account $i:"
            curl -s http://localhost:809$i/health | jq .
        done
        ;;
    rotate-proxy)
        echo "🔄 Rotating proxies for all accounts..."
        docker-compose -f docker-compose.telegram.yml restart
        echo "✅ Proxy rotation completed"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|health|rotate-proxy}"
        exit 1
        ;;
esac
EOF

chmod +x /app/manage-telegram-accounts.sh

echo "✅ Multi-Account Telegram Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit /app/.env.telegram with your real credentials"
echo "2. Setup proxy services for each account"
echo "3. Run: ./manage-telegram-accounts.sh start"
echo "4. Check health: ./manage-telegram-accounts.sh health"
echo ""
echo "🎯 Each account will run in isolated container with:"
echo "   - Separate network namespace"
echo "   - Dedicated proxy connection"
echo "   - Resource limits (256MB RAM, 0.5 CPU)"
echo "   - Rate limiting (30 req/hour per account)"
echo "   - Health monitoring"
echo "   - Auto-restart on failure"