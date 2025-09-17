# 🚀 **DEPLOY KE VPS - 3 LANGKAH MUDAH!**

## 📦 **LANGKAH 1: DOWNLOAD PACKAGE**

Package deployment sudah siap di: `/tmp/webtools-deployment.tar.gz` (99MB)

**Download file ini ke komputer Anda**

---

## 📤 **LANGKAH 2: UPLOAD KE VPS**

Upload file `webtools-deployment.tar.gz` ke VPS Anda menggunakan:

### **Metode A: SCP (dari terminal lokal)**
```bash
scp webtools-deployment.tar.gz root@YOUR_VPS_IP:/tmp/
```

### **Metode B: SFTP Client (WinSCP, FileZilla)**
- Upload ke folder `/tmp/` di VPS

### **Metode C: Web Panel (cPanel, Plesk)**
- Upload via File Manager ke `/tmp/`

---

## 🚀 **LANGKAH 3: DEPLOY (DI VPS)**

Login ke VPS via SSH dan jalankan:

```bash
# Extract package
cd /tmp
tar -xzf webtools-deployment.tar.gz
cd webtools-deployment

# Make script executable  
chmod +x vps-deploy.sh

# Run deployment (ONE COMMAND!)
sudo ./vps-deploy.sh
```

**Input yang diminta:**
```
Enter your domain name: yourdomain.com
Enter your email for SSL: your@email.com  
Continue with deployment? (y/N): y
```

---

## ✅ **SELESAI!**

**Setelah 5-10 menit, aplikasi ready di:**
- **URL**: https://yourdomain.com
- **Admin**: admin / admin123
- **User**: demo / demo123

---

## 🛠️ **PERINTAH MANAGEMENT:**

```bash
# Start/Stop services
/opt/webtools/manage.sh start
/opt/webtools/manage.sh stop  
/opt/webtools/manage.sh restart

# Check status
/opt/webtools/manage.sh status

# View logs
/opt/webtools/manage.sh logs backend
```

---

## 🚨 **JIKA ADA ERROR:**

```bash
# Restart semua services
sudo systemctl restart webtools-backend webtools-frontend mongod nginx

# Check logs
sudo journalctl -u webtools-backend -f
```

---

## 📞 **BUTUH BANTUAN?**

1. **Cek status services**: `sudo systemctl status webtools-backend`
2. **Cek logs**: `tail -f /opt/webtools/data/logs/backend.log`
3. **Restart jika ada masalah**: `/opt/webtools/manage.sh restart`

---

## 🎯 **SETELAH DEPLOY - TEST FITUR:**

1. ✅ Login sebagai admin
2. ✅ Test WhatsApp validation  
3. ✅ Test Telegram validation
4. ✅ Upload CSV untuk bulk validation
5. ✅ Cek account management
6. ✅ Test user registration

**🎉 WEBTOOLS VALIDATION SYSTEM READY TO USE!**