"""
Container Orchestrator - Manages WhatsApp Account Containers
"""

import asyncio
import docker
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import yaml

logger = logging.getLogger(__name__)

class WhatsAppContainerOrchestrator:
    def __init__(self, db):
        self.db = db
        self.docker_client = docker.from_env()
        self.active_containers: Dict[str, dict] = {}
        
    async def create_account_container(self, account_data: Dict) -> Dict:
        """Create and start a new WhatsApp account container"""
        try:
            account_id = account_data["_id"]
            container_name = f"whatsapp_account_{account_id}"
            
            logger.info(f"🐳 Creating container for account: {account_id}")
            
            # Container configuration
            environment = {
                'ACCOUNT_ID': account_id,
                'MONGO_URL': 'mongodb://admin:password123@mongo:27017/webtools_validation?authSource=admin',
                'MAIN_API_URL': 'http://main-api:8001',
                'REDIS_URL': 'redis://redis:6379'
            }
            
            # Add proxy configuration if provided
            proxy_config = account_data.get('proxy_config', {})
            if proxy_config.get('enabled'):
                environment.update({
                    'PROXY_URL': proxy_config.get('url', ''),
                    'PROXY_USERNAME': proxy_config.get('username', ''),
                    'PROXY_PASSWORD': proxy_config.get('password', '')
                })
                logger.info(f"🌐 Proxy configured for {account_id}: {proxy_config.get('url')}")
            
            # Create container
            container = self.docker_client.containers.run(
                image="webtools-whatsapp-account:latest",
                name=container_name,
                environment=environment,
                networks=["webtools_webtools-network"],  # Connect to docker-compose network
                volumes={
                    f"whatsapp_sessions_{account_id}": {
                        'bind': '/app/sessions',
                        'mode': 'rw'
                    }
                },
                ports={'8080/tcp': None},  # Random port assignment
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                mem_limit="512m",  # Memory limit per container
                cpu_quota=50000,   # 50% CPU limit
                remove=False
            )
            
            # Wait for container to be ready
            await self.wait_for_container_health(container_name, timeout=60)
            
            # Get assigned port
            container.reload()
            port = container.attrs['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort']
            
            # Store container info
            container_info = {
                'container_id': container.id,
                'container_name': container_name,
                'account_id': account_id,
                'port': port,
                'url': f"http://localhost:{port}",
                'proxy_enabled': proxy_config.get('enabled', False),
                'created_at': datetime.utcnow(),
                'status': 'running'
            }
            
            self.active_containers[account_id] = container_info
            
            # Update database
            await self.db.whatsapp_accounts.update_one(
                {"_id": account_id},
                {
                    "$set": {
                        "container_info": container_info,
                        "status": "container_ready",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✅ Container created successfully: {container_name} on port {port}")
            
            return {
                "success": True,
                "container_info": container_info,
                "message": f"Container created for account {account_id}"
            }
            
        except Exception as e:
            logger.error(f"❌ Container creation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create container for account {account_id}"
            }
    
    async def destroy_account_container(self, account_id: str) -> Dict:
        """Stop and remove account container"""
        try:
            container_name = f"whatsapp_account_{account_id}"
            
            logger.info(f"🗑️ Destroying container: {container_name}")
            
            # Get container
            try:
                container = self.docker_client.containers.get(container_name)
                
                # Stop container gracefully
                container.stop(timeout=10)
                
                # Remove container
                container.remove(force=True)
                
            except docker.errors.NotFound:
                logger.warning(f"⚠️ Container {container_name} not found")
            
            # Remove from active containers
            if account_id in self.active_containers:
                del self.active_containers[account_id]
            
            # Update database
            await self.db.whatsapp_accounts.update_one(
                {"_id": account_id},
                {
                    "$unset": {"container_info": ""},
                    "$set": {
                        "status": "logged_out",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Remove volume
            try:
                volume_name = f"whatsapp_sessions_{account_id}"
                volume = self.docker_client.volumes.get(volume_name)
                volume.remove(force=True)
            except:
                pass
            
            logger.info(f"✅ Container destroyed: {container_name}")
            
            return {
                "success": True,
                "message": f"Container destroyed for account {account_id}"
            }
            
        except Exception as e:
            logger.error(f"❌ Container destruction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def login_account_container(self, account_id: str) -> Dict:
        """Trigger login for account container"""
        try:
            container_info = self.active_containers.get(account_id)
            if not container_info:
                return {
                    "success": False,
                    "error": "Container not found for account"
                }
            
            # Call container's login endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{container_info['url']}/login"
                
                async with session.post(url, timeout=30) as response:
                    result = await response.json()
                    
                    logger.info(f"🔐 Login triggered for container {account_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Container login failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def logout_account_container(self, account_id: str) -> Dict:
        """Trigger logout for account container"""
        try:
            container_info = self.active_containers.get(account_id)
            if not container_info:
                return {
                    "success": False,
                    "error": "Container not found for account"
                }
            
            # Call container's logout endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{container_info['url']}/logout"
                
                async with session.post(url, timeout=30) as response:
                    result = await response.json()
                    
                    logger.info(f"🚪 Logout triggered for container {account_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Container logout failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_with_account_container(self, account_id: str, phone_number: str) -> Dict:
        """Validate phone number using specific account container"""
        try:
            container_info = self.active_containers.get(account_id)
            if not container_info:
                return {
                    "success": False,
                    "error": "Container not found for account"
                }
            
            # Call container's validation endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{container_info['url']}/validate/{phone_number}"
                
                async with session.post(url, timeout=30) as response:
                    result = await response.json()
                    
                    # Update usage stats
                    await self.increment_container_usage(account_id)
                    
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Container validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_container_status(self, account_id: str) -> Dict:
        """Get status of account container"""
        try:
            container_info = self.active_containers.get(account_id)
            if not container_info:
                return {"status": "not_found"}
            
            # Call container's health endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{container_info['url']}/health"
                
                async with session.get(url, timeout=10) as response:
                    health_data = await response.json()
                    
                    return {
                        "status": "healthy" if health_data.get("status") == "healthy" else "unhealthy",
                        "container_info": container_info,
                        "health_data": health_data
                    }
                    
        except Exception as e:
            logger.error(f"❌ Container status check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def wait_for_container_health(self, container_name: str, timeout: int = 60):
        """Wait for container to be healthy"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).seconds < timeout:
            try:
                container = self.docker_client.containers.get(container_name)
                
                if container.status == "running":
                    # Try health check
                    port = container.attrs['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort']
                    
                    async with aiohttp.ClientSession() as session:
                        url = f"http://localhost:{port}/health"
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                return True
                            
            except:
                pass
            
            await asyncio.sleep(2)
        
        raise Exception(f"Container {container_name} failed to become healthy within {timeout}s")
    
    async def increment_container_usage(self, account_id: str):
        """Increment usage counter for account"""
        await self.db.whatsapp_accounts.update_one(
            {"_id": account_id},
            {
                "$inc": {"daily_usage": 1, "usage_count": 1},
                "$set": {"last_used": datetime.utcnow()}
            }
        )
    
    async def list_active_containers(self) -> List[Dict]:
        """List all active WhatsApp account containers"""
        containers = []
        
        for account_id, container_info in self.active_containers.items():
            status = await self.get_container_status(account_id)
            
            containers.append({
                "account_id": account_id,
                "container_info": container_info,
                "status": status
            })
        
        return containers
    
    async def restart_container(self, account_id: str) -> Dict:
        """Restart account container"""
        try:
            container_name = f"whatsapp_account_{account_id}"
            
            logger.info(f"🔄 Restarting container: {container_name}")
            
            container = self.docker_client.containers.get(container_name)
            container.restart()
            
            # Wait for health
            await self.wait_for_container_health(container_name)
            
            logger.info(f"✅ Container restarted: {container_name}")
            
            return {
                "success": True,
                "message": f"Container restarted for account {account_id}"
            }
            
        except Exception as e:
            logger.error(f"❌ Container restart failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_orphaned_containers(self):
        """Clean up containers without corresponding database records"""
        try:
            # Get all containers with our prefix
            containers = self.docker_client.containers.list(
                filters={"name": "whatsapp_account_"}
            )
            
            for container in containers:
                container_name = container.name
                account_id = container_name.replace("whatsapp_account_", "")
                
                # Check if account exists in database
                account = await self.db.whatsapp_accounts.find_one({"_id": account_id})
                
                if not account:
                    logger.info(f"🧹 Cleaning up orphaned container: {container_name}")
                    
                    try:
                        container.stop(timeout=10)
                        container.remove(force=True)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")

# Global orchestrator instance
_orchestrator = None

def get_orchestrator(db) -> WhatsAppContainerOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WhatsAppContainerOrchestrator(db)
    return _orchestrator