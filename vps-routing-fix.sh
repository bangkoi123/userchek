#!/bin/bash

# ========================================
# WEBTOOLS VPS ROUTING FIX SCRIPT
# Untuk memperbaiki masalah API routing
# ========================================

echo "🚀 WEBTOOLS VPS ROUTING FIX SCRIPT"
echo "=================================="

# 1. Cek status services saat ini
echo "📊 Checking current services status..."
systemctl status nginx --no-pager -l || echo "❌ Nginx not running"
systemctl status apache2 --no-pager -l || echo "❌ Apache2 not running"

# 2. Cek port yang sedang digunakan
echo "🔍 Checking ports in use..."
netstat -tlnp | grep -E ":(80|443|8001|3000)"

# 3. Cek konfigurasi nginx yang sebenarnya menangani traffic
echo "🔧 Finding actual nginx configuration..."
find /etc -name "*.conf" -path "*/nginx/*" 2>/dev/null | head -10
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "No nginx sites-enabled directory"

# 4. Cek apakah ada reverse proxy lain (apache/caddy)
echo "🕵️ Checking for other reverse proxies..."
which apache2 && echo "Apache2 found"
which caddy && echo "Caddy found"
ps aux | grep -E "(nginx|apache|caddy)" | grep -v grep

# 5. Test internal API endpoints
echo "🧪 Testing internal API endpoints..."
curl -s http://localhost:8001/api/health && echo " ✅ Backend directly accessible"
curl -s http://localhost/api/health && echo " ✅ Through local proxy"

# 6. Test backend admin endpoints directly
echo "🔐 Testing admin endpoints directly..."
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
echo "Token obtained: ${TOKEN:0:50}..."

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/admin/users | head -c 200
echo ""

# 7. Identifikasi masalah routing
echo "🎯 DIAGNOSIS RESULTS:"
echo "===================="

# Check if there's external routing blocking
curl -I https://phonecheck.gen-ai.fun/api/admin/users 2>/dev/null | grep -E "(Server|HTTP)"

echo ""
echo "📋 NEXT STEPS TO FIX:"
echo "====================="
echo "1. Find the actual web server handling external traffic"
echo "2. Update routing configuration for /api/admin/* and /api/dashboard/*"
echo "3. Restart web server services"
echo "4. Verify all endpoints are accessible"

echo ""
echo "🏁 Script completed. Review output above to identify the issue."