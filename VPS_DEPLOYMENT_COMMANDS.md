# 🚀 **COPY-PASTE DEPLOYMENT COMMANDS**

## **BERIKAN SAYA INFO VPS ANDA:**
```
VPS IP: _______________
Domain: _______________  
Username: _____________ (biasanya root)
SSH Port: _____________ (biasanya 22)
OS: ___________________ (Ubuntu/Debian version)
```

---

## **STEP 1: TRANSFER FILES KE VPS**

### **Metode A: SCP Transfer (Dari komputer lokal)**
```bash
# Download deployment package dulu
wget https://your-server/webtools-vps-ready.tar.gz

# Extract locally
tar -xzf webtools-vps-ready.tar.gz
cd webtools-vps-ready/

# Transfer ke VPS (ganti dengan IP Anda)
scp -r ./* root@YOUR_VPS_IP:/tmp/webtools-deploy/
```

### **Metode B: Direct Download di VPS**
```bash
# SSH ke VPS Anda
ssh root@YOUR_VPS_IP

# Download langsung di VPS
cd /tmp
wget https://github.com/your-files/webtools-vps-ready.tar.gz
tar -xzf webtools-vps-ready.tar.gz
mv webtools-vps-ready webtools-deploy
cd webtools-deploy
```

---

## **STEP 2: JALANKAN DEPLOYMENT DI VPS**

**Copy-paste commands ini di VPS Anda:**

```bash
# Pastikan di direktori yang benar
cd /tmp/webtools-deploy

# Make script executable
chmod +x vps-deploy.sh

# Check system info
echo "System info:"
cat /etc/os-release
df -h
free -h

# Run deployment script
sudo ./vps-deploy.sh
```

---

## **STEP 3: INPUT SAAT DIMINTA**

Script akan bertanya:
```
Enter your domain name: yourdomain.com
Enter your email for SSL: your@email.com
Continue with deployment? (y/N): y
```

**⏱️ Tunggu 5-10 menit untuk instalasi otomatis**

---

## **STEP 4: VERIFY DEPLOYMENT**

Setelah script selesai, test dengan commands ini:

```bash
# Check services status
sudo systemctl status webtools-backend webtools-frontend mongod nginx

# Check if ports are listening
sudo netstat -tlnp | grep -E ':3000|:8001|:80|:443|:27017'

# Test backend API
curl -k https://yourdomain.com/api/health

# Check logs if needed
tail -f /opt/webtools/data/logs/backend.log
```

---

## **STEP 5: ACCESS APPLICATION**

- **URL**: https://yourdomain.com
- **Admin Login**: admin / admin123
- **Demo Login**: demo / demo123

---

## **TROUBLESHOOTING COMMANDS**

**If services don't start:**
```bash
# Restart all services
sudo systemctl restart webtools-backend webtools-frontend mongod nginx

# Check individual service logs
sudo journalctl -u webtools-backend --no-pager -n 50
sudo journalctl -u webtools-frontend --no-pager -n 50

# Check nginx error log
sudo tail -f /var/log/nginx/error.log
```

**If SSL fails:**
```bash
# Manually run certbot
sudo certbot --nginx -d yourdomain.com --email your@email.com

# Or use HTTP for testing
sudo nano /etc/nginx/sites-available/webtools-validation
# Comment SSL redirect line temporarily
```

**If MongoDB fails:**
```bash
# Restart MongoDB
sudo systemctl restart mongod
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

---

## **MANAGEMENT COMMANDS**

**After successful deployment:**
```bash
# Start/Stop services
/opt/webtools/manage.sh start
/opt/webtools/manage.sh stop
/opt/webtools/manage.sh restart

# Check status
/opt/webtools/manage.sh status

# View live logs
/opt/webtools/manage.sh logs backend
/opt/webtools/manage.sh logs frontend

# Update application
/opt/webtools/manage.sh update
```

---

## **TESTING COMMANDS**

**Test all validation methods:**
```bash
# Test backend directly
curl -k -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test WhatsApp validation
curl -k -X POST https://yourdomain.com/api/validation/quick-check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"phone_inputs":["+6281234567890"],"validate_whatsapp":true,"validate_telegram":false}'
```

---

## **IMPORTANT NOTES**

1. **Domain DNS**: Pastikan domain sudah pointing ke IP VPS
2. **Firewall**: Script akan configure UFW automatically
3. **SSL**: Let's Encrypt akan setup automatic renewal
4. **Backup**: Database backup otomatis tersedia
5. **Monitoring**: Gunakan `htop` dan `df -h` untuk monitor resources

---

## **SUCCESS INDICATORS**

✅ **Deployment berhasil jika:**
- Services running: `sudo systemctl status webtools-backend webtools-frontend`
- Ports listening: `sudo netstat -tlnp | grep -E ':3000|:8001|:80|:443'`
- Application accessible: `curl -k https://yourdomain.com`
- Login working: Admin panel accessible via browser

---

**🎯 READY TO DEPLOY? BERIKAN SAYA INFO VPS ANDA DAN KITA MULAI!**