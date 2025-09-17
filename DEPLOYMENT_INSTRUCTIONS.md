# 🚀 **DEPLOYMENT WEBTOOLS KE VPS - SUPER MUDAH!**

## 📋 **PERSYARATAN VPS:**
- **OS**: Ubuntu 20.04+ atau Debian 11+
- **RAM**: Minimum 2GB (Recommended 4GB)
- **Storage**: Minimum 20GB
- **CPU**: Minimum 2 cores
- **Network**: Public IP address

---

## 🎯 **ONE-CLICK DEPLOYMENT (5 MENIT!)**

### **LANGKAH 1: Download Files ke VPS**

Login ke VPS Anda via SSH dan jalankan:

```bash
# Download deployment package
cd /tmp
wget https://github.com/your-repo/webtools-validation/archive/main.zip
unzip main.zip
cd webtools-validation-main/

# OR jika ada akses Git:
git clone https://github.com/your-repo/webtools-validation.git
cd webtools-validation/
```

**ALTERNATIF - Copy Files Manual:**
Jika tidak ada GitHub, upload semua files dari folder `/app` ke VPS Anda dalam folder `/tmp/webtools/`

### **LANGKAH 2: Jalankan Deployment Script**

```bash
# Pastikan script executable
chmod +x vps-deploy.sh

# Jalankan deployment (sebagai root)
sudo ./vps-deploy.sh
```

### **LANGKAH 3: Input Configuration**

Script akan bertanya:
```
Enter your domain name: yourdomain.com
Enter your email for SSL: your@email.com
Continue with deployment? (y/N): y
```

**✅ SELESAI! Script akan otomatis install semua yang dibutuhkan**

---

## 🎉 **SETELAH DEPLOYMENT SELESAI:**

### **Akses Aplikasi:**
- **URL**: https://yourdomain.com
- **Admin Login**: admin / admin123
- **User Login**: demo / demo123

### **Test Semua Fitur:**
1. Login sebagai admin
2. Coba WhatsApp validation
3. Coba Telegram validation
4. Cek account management
5. Test bulk validation

---

## 🛠️ **MANAGEMENT COMMANDS:**

```bash
# Start/Stop/Restart services
/opt/webtools/manage.sh start
/opt/webtools/manage.sh stop
/opt/webtools/manage.sh restart

# Check status
/opt/webtools/manage.sh status

# View logs
/opt/webtools/manage.sh logs backend
/opt/webtools/manage.sh logs frontend

# Update application
/opt/webtools/manage.sh update
```

---

## ⚠️ **TROUBLESHOOTING:**

### **Jika Service Tidak Start:**
```bash
# Check logs
sudo journalctl -u webtools-backend -f
sudo journalctl -u webtools-frontend -f

# Restart services
sudo systemctl restart webtools-backend webtools-frontend
```

### **Jika Domain Tidak Accessible:**
```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check firewall
sudo ufw status
```

### **Jika MongoDB Error:**
```bash
# Restart MongoDB
sudo systemctl restart mongod
sudo systemctl status mongod
```

---

## 🔧 **PRODUCTION CUSTOMIZATION:**

### **Update API Keys (Optional):**
Edit `/opt/webtools/backend/.env`:
```bash
sudo nano /opt/webtools/backend/.env

# Update these for production:
TELEGRAM_API_ID=your_real_api_id
TELEGRAM_API_HASH=your_real_api_hash
SENDGRID_API_KEY=your_sendgrid_key
STRIPE_API_KEY=your_stripe_key
```

### **Restart After Changes:**
```bash
sudo systemctl restart webtools-backend
```

---

## 📊 **MONITORING:**

### **Check System Health:**
```bash
# System resources
htop
df -h

# Service status
systemctl status webtools-backend webtools-frontend mongod nginx

# Application logs
tail -f /opt/webtools/data/logs/backend.log
tail -f /opt/webtools/data/logs/frontend.log
```

### **Performance Monitoring:**
```bash
# Database status
sudo systemctl status mongod

# Memory usage
free -h

# Disk space
df -h
```

---

## 🚨 **BACKUP & SECURITY:**

### **Backup Database:**
```bash
# Create backup
mongodump --db webtools_validation --out /opt/webtools/backup/$(date +%Y%m%d)

# Restore backup
mongorestore --db webtools_validation /opt/webtools/backup/20240101/webtools_validation/
```

### **Security Checklist:**
- ✅ SSL certificate installed (via Let's Encrypt)
- ✅ Firewall configured (UFW)
- ✅ Services running as non-root user
- ✅ Environment files protected (600 permissions)
- ✅ MongoDB secured (local access only)

---

## 📞 **SUPPORT:**

### **Common Issues:**
1. **502 Bad Gateway**: Backend service down
   ```bash
   sudo systemctl restart webtools-backend
   ```

2. **SSL Certificate Error**: Run certbot again
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

3. **High Memory Usage**: Restart services
   ```bash
   /opt/webtools/manage.sh restart
   ```

### **Get Help:**
- Check application logs: `/opt/webtools/data/logs/`
- Check system logs: `sudo journalctl -u webtools-backend`
- System health: `htop` and `df -h`

---

## 🎯 **DEPLOYMENT SUMMARY:**

**✅ WHAT'S INSTALLED:**
- ✅ Node.js 18 + Yarn + PM2
- ✅ Python 3.11 + Virtual Environment
- ✅ MongoDB 7.0
- ✅ Nginx with SSL (Let's Encrypt)
- ✅ UFW Firewall configured
- ✅ Systemd services for auto-start
- ✅ All Python/Node dependencies
- ✅ Playwright browsers for WhatsApp automation
- ✅ 29 Demo Telegram accounts + 6 Demo WhatsApp accounts
- ✅ Production environment configuration

**✅ WHAT'S READY:**
- ✅ Admin panel fully functional
- ✅ User management system
- ✅ WhatsApp & Telegram validation
- ✅ Bulk validation with CSV upload
- ✅ Payment system (Stripe) ready
- ✅ Multi-tenant architecture
- ✅ Real-time notifications
- ✅ Job history & analytics
- ✅ Account management
- ✅ Session persistence

**🎉 YOUR WEBTOOLS VALIDATION SYSTEM IS NOW LIVE AND PRODUCTION-READY!**