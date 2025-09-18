#!/bin/bash

# 🎭 VERIFY UNIQUE FINGERPRINTS PER ACCOUNT
# Script untuk memverifikasi bahwa setiap account punya fingerprint berbeda

echo "🎭 VERIFYING UNIQUE FINGERPRINTS FOR MULTI-ACCOUNT TELEGRAM"
echo "============================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if containers are running
echo -e "${BLUE}📋 Checking container status...${NC}"
if ! docker-compose -f docker-telegram-simple.yml ps | grep -q "Up"; then
    echo -e "${RED}❌ Containers not running. Please start them first:${NC}"
    echo "./telegram-manager.sh start"
    exit 1
fi

echo ""
echo -e "${BLUE}🎭 FINGERPRINT COMPARISON${NC}"
echo "========================================"

# Function to get detailed info from each account
get_account_fingerprint() {
    local account_num=$1
    local port=$((8080 + account_num))
    
    echo -e "${YELLOW}Account $account_num (port $port):${NC}"
    
    # Get health info which includes fingerprint data
    health_response=$(curl -s http://localhost:$port/health 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "  📱 Container Info:"
        docker inspect telegram_account_$account_num --format '    Hostname: {{.Config.Hostname}}'
        docker inspect telegram_account_$account_num --format '    Environment:' && \
        docker inspect telegram_account_$account_num --format '{{range .Config.Env}}      {{.}}{{"\n"}}{{end}}' | grep -E "(TZ|LANG|DEVICE_TYPE|DEVICE_BRAND)" | head -4
        
        echo "  🌐 Network Info:"
        docker inspect telegram_account_$account_num --format '    DNS: {{.HostConfig.Dns}}'
        
        echo "  ⚡ Resource Limits:"
        docker inspect telegram_account_$account_num --format '    Memory: {{.HostConfig.Memory}} bytes'
        docker inspect telegram_account_$account_num --format '    CPU: {{.HostConfig.NanoCpus}} nanocpus'
        
        echo "  📊 Health Status:"
        echo "$health_response" | jq -r '.telegram_status // "unknown"' | sed 's/^/    Telegram: /'
        echo "$health_response" | jq -r '.proxy_host // "direct"' | sed 's/^/    Proxy: /'
        
        echo ""
    else
        echo -e "    ${RED}❌ Cannot connect to account $account_num${NC}"
        echo ""
    fi
}

# Test validation with fingerprint info
test_validation_fingerprint() {
    local account_num=$1
    local port=$((8080 + account_num))
    local test_phone="+6281234567890"
    
    echo -e "${BLUE}🧪 Testing validation fingerprint for Account $account_num:${NC}"
    
    response=$(curl -s -X POST http://localhost:$port/validate \
        -H "Content-Type: application/json" \
        -d "{\"phone_number\":\"$test_phone\"}" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "  📱 Device Fingerprint:"
        echo "$response" | jq -r '.details.fingerprint.device // "unknown"' | sed 's/^/    Device: /'
        echo "$response" | jq -r '.details.fingerprint.system // "unknown"' | sed 's/^/    System: /'
        echo "$response" | jq -r '.details.fingerprint.lang // "unknown"' | sed 's/^/    Language: /'
        echo "$response" | jq -r '.details.method // "unknown"' | sed 's/^/    Method: /'
        echo ""
    else
        echo -e "    ${RED}❌ Validation test failed${NC}"
        echo ""
    fi
}

# Check each account
for i in {1..3}; do
    get_account_fingerprint $i
done

echo -e "${BLUE}🧪 VALIDATION FINGERPRINT TESTS${NC}"
echo "========================================"

for i in {1..3}; do
    test_validation_fingerprint $i
done

# Summary comparison
echo -e "${BLUE}📊 FINGERPRINT UNIQUENESS SUMMARY${NC}"
echo "========================================"

echo "🎯 Container Hostnames:"
for i in {1..3}; do
    hostname=$(docker inspect telegram_account_$i --format '{{.Config.Hostname}}')
    echo "  Account $i: $hostname"
done

echo ""
echo "🌍 Timezone Settings:"
for i in {1..3}; do
    tz=$(docker inspect telegram_account_$i --format '{{range .Config.Env}}{{if contains . "TZ="}}{{.}}{{end}}{{end}}')
    echo "  Account $i: $tz"
done

echo ""
echo "📱 Device Types:"
for i in {1..3}; do
    device_type=$(docker inspect telegram_account_$i --format '{{range .Config.Env}}{{if contains . "DEVICE_TYPE="}}{{.}}{{end}}{{end}}')
    device_brand=$(docker inspect telegram_account_$i --format '{{range .Config.Env}}{{if contains . "DEVICE_BRAND="}}{{.}}{{end}}{{end}}')
    echo "  Account $i: $device_type | $device_brand"
done

echo ""
echo "🌐 DNS Settings:"
for i in {1..3}; do
    dns=$(docker inspect telegram_account_$i --format '{{.HostConfig.Dns}}')
    echo "  Account $i: $dns"
done

echo ""
echo -e "${GREEN}✅ FINGERPRINT VERIFICATION COMPLETE${NC}"
echo ""
echo "🎭 Each account should show DIFFERENT values for:"
echo "   • Hostname (container name)"
echo "   • Timezone (TZ environment)" 
echo "   • Language (LANG environment)"
echo "   • Device type and brand"
echo "   • DNS servers"
echo "   • Telegram device model"
echo "   • System version"
echo "   • App version"
echo "   • Session timing patterns"
echo ""
echo "⚠️  If any values are identical, accounts may be detectable as related!"

# Check for proxy usage
echo ""
echo -e "${BLUE}🌐 PROXY CONFIGURATION CHECK${NC}"
echo "========================================"

proxy_count=0
for i in {1..3}; do
    port=$((8080 + i))
    proxy_info=$(curl -s http://localhost:$port/health | jq -r '.proxy_host // "direct"')
    echo "Account $i proxy: $proxy_info"
    if [ "$proxy_info" != "direct" ]; then
        proxy_count=$((proxy_count + 1))
    fi
done

echo ""
if [ $proxy_count -eq 0 ]; then
    echo -e "${YELLOW}⚠️  NO PROXIES CONFIGURED${NC}"
    echo "All accounts using same VPS IP - higher detection risk"
    echo "Recommend: Configure different proxies per account"
elif [ $proxy_count -eq 3 ]; then
    echo -e "${GREEN}✅ ALL ACCOUNTS USING PROXIES${NC}"
    echo "Maximum stealth configuration achieved"
else
    echo -e "${YELLOW}⚠️  PARTIAL PROXY CONFIGURATION${NC}"
    echo "$proxy_count/3 accounts using proxies"
    echo "Recommend: Enable proxies for all accounts"
fi