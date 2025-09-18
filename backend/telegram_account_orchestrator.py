"""
Telegram Multi-Account Orchestrator
Advanced isolation and management system
"""

import asyncio
import docker
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import subprocess
import psutil

class TelegramAccountOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.docker_client = docker.from_env()
        self.accounts = {}
        self.account_status = {}
        self.proxy_rotation = {}
        
    async def create_isolated_account(self, account_config: Dict) -> Dict:
        """Create completely isolated Telegram account container"""
        try:
            account_id = account_config["account_id"]
            
            # 1. NETWORK ISOLATION - Create dedicated network
            network_name = f"telegram_net_{account_id}"
            try:
                network = self.docker_client.networks.create(
                    network_name,
                    driver="bridge",
                    ipam=docker.types.IPAMConfig(
                        pool_configs=[
                            docker.types.IPAMPool(
                                subnet=f"172.30.{account_id}.0/24"
                            )
                        ]
                    )
                )
            except Exception as e:
                # Network might already exist
                network = self.docker_client.networks.get(network_name)
            
            # 2. PROXY ISOLATION - Each account different proxy
            proxy_config = await self.get_proxy_for_account(account_id)
            
            # 3. RESOURCE ISOLATION - CPU and Memory limits
            container_config = {
                "image": "telegram-validator:latest",
                "name": f"telegram_account_{account_id}",
                "environment": {
                    "TELEGRAM_API_ID": account_config["api_id"],
                    "TELEGRAM_API_HASH": account_config["api_hash"],
                    "TELEGRAM_PHONE": account_config["phone_number"],
                    "ACCOUNT_ID": account_id,
                    "PROXY_HOST": proxy_config["host"],
                    "PROXY_PORT": proxy_config["port"],
                    "PROXY_USERNAME": proxy_config.get("username"),
                    "PROXY_PASSWORD": proxy_config.get("password"),
                    "PROXY_TYPE": proxy_config.get("type", "socks5"),
                    "MAX_REQUESTS_PER_HOUR": account_config.get("max_requests", 30),
                    "RATE_LIMIT_WINDOW": "3600",  # 1 hour
                    "SESSION_TIMEOUT": "86400",   # 24 hours
                },
                "volumes": {
                    f"/app/data/telegram_sessions/{account_id}": {"bind": "/app/sessions", "mode": "rw"},
                    f"/app/data/logs/{account_id}": {"bind": "/app/logs", "mode": "rw"}
                },
                "mem_limit": "256m",
                "nano_cpus": int(0.5 * 1e9),  # 0.5 CPU
                "restart_policy": {"Name": "unless-stopped"},
                "network": network_name,
                "ports": {f"808{account_id}": 8080},  # Different port per account
            }
            
            # 4. FINGERPRINT ISOLATION - Different user agents, timezones
            container_config["environment"].update({
                "USER_AGENT": self.generate_user_agent(),
                "TIMEZONE": self.get_random_timezone(),
                "LOCALE": self.get_random_locale(),
                "DEVICE_MODEL": self.get_random_device(),
            })
            
            # Create and start container
            container = self.docker_client.containers.run(
                detach=True,
                **container_config
            )
            
            # 5. HEALTH MONITORING SETUP
            await self.setup_account_monitoring(account_id, container.id)
            
            # 6. RATE LIMITING SETUP
            await self.setup_rate_limiting(account_id)
            
            self.accounts[account_id] = {
                "container": container,
                "config": account_config,
                "proxy": proxy_config,
                "created_at": datetime.utcnow(),
                "status": "active",
                "network": network_name
            }
            
            self.logger.info(f"✅ Created isolated account {account_id}")
            
            return {
                "success": True,
                "account_id": account_id,
                "container_id": container.id,
                "network": network_name,
                "proxy_location": proxy_config.get("location", "unknown")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create isolated account {account_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_proxy_for_account(self, account_id: int) -> Dict:
        """Get dedicated proxy for account with rotation"""
        
        # Proxy pool - each account gets different location
        proxy_pools = [
            {
                "location": "Indonesia",
                "host": "id-proxy-1.proxyservice.com",
                "port": 1080,
                "type": "socks5",
                "username": "user_id_1",
                "password": "pass_id_1"
            },
            {
                "location": "Singapore", 
                "host": "sg-proxy-1.proxyservice.com",
                "port": 1080,
                "type": "socks5",
                "username": "user_sg_1",
                "password": "pass_sg_1"
            },
            {
                "location": "Malaysia",
                "host": "my-proxy-1.proxyservice.com", 
                "port": 1080,
                "type": "socks5",
                "username": "user_my_1",
                "password": "pass_my_1"
            },
            {
                "location": "Thailand",
                "host": "th-proxy-1.proxyservice.com",
                "port": 1080,
                "type": "socks5", 
                "username": "user_th_1",
                "password": "pass_th_1"
            },
            {
                "location": "Philippines",
                "host": "ph-proxy-1.proxyservice.com",
                "port": 1080,
                "type": "socks5",
                "username": "user_ph_1", 
                "password": "pass_ph_1"
            }
        ]
        
        # Assign proxy based on account_id to ensure consistency
        proxy_index = (account_id - 1) % len(proxy_pools)
        assigned_proxy = proxy_pools[proxy_index].copy()
        
        # Add rotation logic - change proxy daily
        rotation_key = f"account_{account_id}_{datetime.utcnow().strftime('%Y-%m-%d')}"
        if rotation_key not in self.proxy_rotation:
            # Rotate to different server in same location
            server_num = random.randint(1, 3)
            assigned_proxy["host"] = assigned_proxy["host"].replace("-1.", f"-{server_num}.")
            self.proxy_rotation[rotation_key] = assigned_proxy
        else:
            assigned_proxy = self.proxy_rotation[rotation_key]
        
        return assigned_proxy
    
    def generate_user_agent(self) -> str:
        """Generate realistic user agent for fingerprinting"""
        user_agents = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        return random.choice(user_agents)
    
    def get_random_timezone(self) -> str:
        """Get random timezone for account"""
        timezones = [
            "Asia/Jakarta", "Asia/Singapore", "Asia/Kuala_Lumpur", 
            "Asia/Bangkok", "Asia/Manila", "Asia/Ho_Chi_Minh"
        ]
        return random.choice(timezones)
    
    def get_random_locale(self) -> str:
        """Get random locale"""
        locales = ["id_ID", "en_SG", "ms_MY", "th_TH", "en_PH", "vi_VN"]
        return random.choice(locales)
    
    def get_random_device(self) -> str:
        """Get random device model"""
        devices = [
            "Samsung Galaxy S23", "iPhone 15 Pro", "OnePlus 11", 
            "Xiaomi 13", "OPPO Find X6", "Vivo X90"
        ]
        return random.choice(devices)
    
    async def setup_account_monitoring(self, account_id: str, container_id: str):
        """Setup health monitoring for account"""
        monitor_config = {
            "account_id": account_id,
            "container_id": container_id,
            "health_check_interval": 60,  # seconds
            "max_failures": 3,
            "auto_restart": True,
            "ban_detection": True,
            "rate_limit_monitoring": True
        }
        
        # Store monitoring config
        with open(f"/app/data/monitoring/{account_id}_config.json", "w") as f:
            json.dump(monitor_config, f, indent=2)
    
    async def setup_rate_limiting(self, account_id: str):
        """Setup advanced rate limiting per account"""
        rate_limit_config = {
            "requests_per_hour": 30,
            "requests_per_day": 500,
            "burst_limit": 5,
            "cooldown_period": 300,  # 5 minutes
            "adaptive_limiting": True,
            "ban_detection_threshold": 10
        }
        
        # Store rate limiting config
        with open(f"/app/data/rate_limits/{account_id}_limits.json", "w") as f:
            json.dump(rate_limit_config, f, indent=2)
    
    async def rotate_account_proxy(self, account_id: str) -> Dict:
        """Rotate proxy for account (daily rotation)"""
        try:
            if account_id not in self.accounts:
                return {"success": False, "error": "Account not found"}
            
            account = self.accounts[account_id]
            container = account["container"]
            
            # Get new proxy
            new_proxy = await self.get_proxy_for_account(int(account_id))
            
            # Update container environment
            container.reload()
            
            # Restart container with new proxy (graceful restart)
            await self.graceful_restart_account(account_id, new_proxy)
            
            self.logger.info(f"✅ Rotated proxy for account {account_id} to {new_proxy['location']}")
            
            return {
                "success": True,
                "account_id": account_id,
                "new_proxy_location": new_proxy.get("location")
            }
            
        except Exception as e:
            self.logger.error(f"Proxy rotation failed for {account_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def graceful_restart_account(self, account_id: str, new_proxy: Dict):
        """Gracefully restart account with new configuration"""
        try:
            account = self.accounts[account_id]
            container = account["container"]
            
            # Stop container gracefully
            container.stop(timeout=30)
            
            # Update configuration
            account["proxy"] = new_proxy
            
            # Restart with new proxy config
            container.start()
            
            # Wait for health check
            await asyncio.sleep(10)
            
            # Verify container is healthy
            container.reload()
            if container.status == "running":
                self.logger.info(f"✅ Account {account_id} restarted successfully")
                return True
            else:
                self.logger.error(f"❌ Account {account_id} failed to restart")
                return False
                
        except Exception as e:
            self.logger.error(f"Graceful restart failed for {account_id}: {e}")
            return False
    
    async def get_account_health(self) -> Dict:
        """Get health status of all accounts"""
        health_status = {}
        
        for account_id, account in self.accounts.items():
            try:
                container = account["container"]
                container.reload()
                
                # Get container stats
                stats = container.stats(stream=False)
                
                health_status[account_id] = {
                    "status": container.status,
                    "proxy_location": account["proxy"].get("location"),
                    "cpu_usage": self.calculate_cpu_usage(stats),
                    "memory_usage": self.calculate_memory_usage(stats),
                    "network": account["network"],
                    "uptime": (datetime.utcnow() - account["created_at"]).total_seconds(),
                    "last_proxy_rotation": self.proxy_rotation.get(f"account_{account_id}_{datetime.utcnow().strftime('%Y-%m-%d')}", {}).get("rotated_at")
                }
                
            except Exception as e:
                health_status[account_id] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    def calculate_cpu_usage(self, stats: Dict) -> float:
        """Calculate CPU usage percentage"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_count = stats["cpu_stats"]["online_cpus"]
            
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
                return round(cpu_percent, 2)
        except:
            pass
        return 0.0
    
    def calculate_memory_usage(self, stats: Dict) -> Dict:
        """Calculate memory usage"""
        try:
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"] 
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                "usage_mb": round(memory_usage / 1024 / 1024, 2),
                "limit_mb": round(memory_limit / 1024 / 1024, 2),
                "percentage": round(memory_percent, 2)
            }
        except:
            return {"usage_mb": 0, "limit_mb": 0, "percentage": 0}

# Global orchestrator instance
_orchestrator = None

async def get_telegram_orchestrator() -> TelegramAccountOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TelegramAccountOrchestrator()
    return _orchestrator