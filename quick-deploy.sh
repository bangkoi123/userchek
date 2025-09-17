#!/bin/bash

# 🚀 WEBTOOLS VALIDATION - QUICK DEPLOYMENT SCRIPT
# This script helps you transfer and deploy to your VPS quickly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Display header
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 WEBTOOLS VALIDATION - QUICK VPS DEPLOYMENT             ║
║                                                              ║
║   This script will help you deploy to your VPS easily       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo
echo -e "${BLUE}Choose your deployment method:${NC}"
echo "1. Create deployment package (ZIP file for manual upload)"
echo "2. Direct SCP transfer to VPS"
echo "3. Show manual deployment instructions"
echo

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        print_status "Creating deployment package..."
        
        # Create deployment directory
        mkdir -p /tmp/webtools-deployment
        
        # Copy essential files
        cp -r backend/ /tmp/webtools-deployment/
        cp -r frontend/ /tmp/webtools-deployment/
        cp -r data/ /tmp/webtools-deployment/
        cp vps-deploy.sh /tmp/webtools-deployment/
        cp DEPLOYMENT_INSTRUCTIONS.md /tmp/webtools-deployment/
        cp production_setup.md /tmp/webtools-deployment/
        
        # Create package
        cd /tmp
        tar -czf webtools-deployment.tar.gz webtools-deployment/
        
        print_status "✅ Deployment package created: /tmp/webtools-deployment.tar.gz"
        echo
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Download the file: /tmp/webtools-deployment.tar.gz"
        echo "2. Upload to your VPS (using SCP, SFTP, or web upload)"
        echo "3. On VPS, extract: tar -xzf webtools-deployment.tar.gz"
        echo "4. Run deployment: cd webtools-deployment && sudo ./vps-deploy.sh"
        ;;
        
    2)
        print_status "Setting up direct SCP transfer..."
        
        # Get VPS details
        read -p "Enter VPS IP address: " vps_ip
        read -p "Enter VPS username (default: root): " vps_user
        vps_user=${vps_user:-root}
        read -p "Enter SSH port (default: 22): " ssh_port
        ssh_port=${ssh_port:-22}
        
        print_status "Creating deployment package..."
        
        # Create clean deployment directory
        rm -rf /tmp/webtools-deployment
        mkdir -p /tmp/webtools-deployment
        
        # Copy files
        cp -r backend/ /tmp/webtools-deployment/
        cp -r frontend/ /tmp/webtools-deployment/
        cp -r data/ /tmp/webtools-deployment/
        cp vps-deploy.sh /tmp/webtools-deployment/
        cp DEPLOYMENT_INSTRUCTIONS.md /tmp/webtools-deployment/
        cp production_setup.md /tmp/webtools-deployment/
        
        print_status "Transferring files to VPS..."
        
        # Transfer files
        scp -P $ssh_port -r /tmp/webtools-deployment/ $vps_user@$vps_ip:/tmp/
        
        print_status "✅ Files transferred successfully!"
        echo
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. SSH to your VPS: ssh -p $ssh_port $vps_user@$vps_ip"
        echo "2. Run deployment: cd /tmp/webtools-deployment && sudo ./vps-deploy.sh"
        ;;
        
    3)
        print_status "Manual deployment instructions:"
        echo
        echo -e "${BLUE}==== MANUAL DEPLOYMENT STEPS ====${NC}"
        echo
        echo "1. Copy these files to your VPS in /tmp/webtools/:"
        echo "   - backend/ (entire folder)"
        echo "   - frontend/ (entire folder)"
        echo "   - data/ (entire folder)"
        echo "   - vps-deploy.sh"
        echo "   - DEPLOYMENT_INSTRUCTIONS.md"
        echo
        echo "2. On your VPS, run:"
        echo "   cd /tmp/webtools"
        echo "   chmod +x vps-deploy.sh"
        echo "   sudo ./vps-deploy.sh"
        echo
        echo "3. Follow the prompts for domain name and email"
        echo
        echo "4. Access your application at https://yourdomain.com"
        echo "   - Admin: admin/admin123"
        echo "   - Demo: demo/demo123"
        ;;
        
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo
print_status "For detailed instructions, see: DEPLOYMENT_INSTRUCTIONS.md"
echo