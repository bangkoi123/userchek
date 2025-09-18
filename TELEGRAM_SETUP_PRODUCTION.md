# 🚀 PRODUCTION TELEGRAM MTP SETUP GUIDE

## ⚠️ CRITICAL REQUIREMENTS FOR PROFESSIONAL WEBTOOLS

### STEP 1: Get Real Telegram API Credentials

1. **Visit**: https://my.telegram.org/apps
2. **Login** with your phone number
3. **Create New Application**:
   - App title: "Webtools Validation Service"
   - Short name: "webtools_val"
   - URL: https://phonecheck.gen-ai.fun
   - Platform: Server
   - Description: "Professional phone number validation service"

4. **Copy credentials**:
   - `api_id` (integer) - Example: 1234567
   - `api_hash` (32 chars) - Example: abcdef1234567890abcdef1234567890

### STEP 2: Setup Account for MTP Validation

**OPTION A: Use Your Personal Account (NOT RECOMMENDED)**
- Risk: Your personal Telegram could get banned
- Privacy: Your account will be used for validation

**OPTION B: Create Dedicated Business Account (RECOMMENDED)**
1. Get a new phone number (virtual/business line)
2. Create new Telegram account with this number
3. Use this account exclusively for validation
4. Setup 2FA and strong security

### STEP 3: Update Environment Variables

```bash
# Edit /app/backend/.env
TELEGRAM_API_ID=YOUR_REAL_API_ID
TELEGRAM_API_HASH=YOUR_REAL_API_HASH

# Optional: Bot token for additional features
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
```

### STEP 4: First Login & Session Creation

```bash
# Run this ONCE to create session file
cd /app/backend
python -c "
import asyncio
from telegram_mtp_validator import TelegramMTPValidator

async def setup():
    validator = TelegramMTPValidator(
        session_name='production_validator',
        phone_number='+YOUR_PHONE_NUMBER'  # The phone number of validator account
    )
    
    success = await validator.initialize()
    if success:
        print('✅ Session created successfully!')
        print('✅ Ready for production validation!')
    else:
        print('❌ Session creation failed')
    
    await validator.close()

asyncio.run(setup())
"
```

### STEP 5: Production Security Setup

1. **Proxy Setup (HIGHLY RECOMMENDED)**:
```bash
# Add to .env
TELEGRAM_USE_PROXY=true
TELEGRAM_PROXY_TYPE=socks5
TELEGRAM_PROXY_HOST=your-proxy-server.com
TELEGRAM_PROXY_PORT=1080
TELEGRAM_PROXY_USERNAME=proxy_user
TELEGRAM_PROXY_PASSWORD=proxy_pass
```

2. **Rate Limiting**:
```bash
# Conservative limits to avoid bans
TELEGRAM_MAX_REQUESTS_PER_HOUR=50
TELEGRAM_MAX_CONCURRENT_SESSIONS=3
```

3. **Session Security**:
```bash
# Ensure proper permissions
chmod 600 /app/data/telegram_sessions/*.session
chown app:app /app/data/telegram_sessions/
```

### STEP 6: Testing Real Validation

```bash
# Test real MTP validation
curl -X POST https://phonecheck.gen-ai.fun/api/validation/quick-check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "phone_inputs": ["+6281234567890"],
    "validate_telegram": true,
    "telegram_validation_method": "mtp_profile"
  }'
```

## 🛡️ PRODUCTION SAFEGUARDS

### Rate Limiting Implementation
- Max 50 requests/hour per validation account
- Automatic backoff on rate limit detection
- Multiple account rotation for high volume

### Account Health Monitoring
- Auto-detect banned/restricted accounts
- Session health checks every hour
- Automatic failover to backup accounts

### Privacy Compliance
- No storage of personal data from validation
- GDPR-compliant data handling
- User consent for advanced validations

## 📊 EXPECTED RESULTS

### Standard Validation (1 credit):
```json
{
  "success": true,
  "status": "active",
  "details": {
    "exists": true,
    "validation_type": "basic_check"
  }
}
```

### MTP Profile Validation (3 credits):
```json
{
  "success": true,
  "status": "active", 
  "profile_info": {
    "username": "john_doe",
    "first_name": "John",
    "has_username": true,
    "is_contact": false
  }
}
```

## ⚠️ IMPORTANT WARNINGS

1. **Account Ban Risk**: Real MTP validation can trigger Telegram bans
2. **Rate Limits**: Telegram has strict rate limiting (50-100 requests/day)
3. **Privacy Laws**: Ensure compliance with local privacy regulations
4. **Proxy Required**: Use residential proxies for better success rates
5. **Backup Accounts**: Always have 3-5 backup validation accounts

## 🚀 GO LIVE CHECKLIST

- [ ] Real API credentials obtained
- [ ] Dedicated business phone number setup
- [ ] Session file created successfully
- [ ] Proxy configured and tested
- [ ] Rate limiting implemented
- [ ] Backup accounts prepared
- [ ] Terms of service updated
- [ ] Privacy policy updated
- [ ] User consent mechanism implemented
- [ ] Monitoring and alerts setup

## 📞 SUPPORT

For production deployment issues:
1. Check Telegram API status
2. Verify proxy connectivity
3. Monitor rate limit headers
4. Check session file permissions
5. Review Telegram account status

**READY FOR PROFESSIONAL TELEGRAM VALIDATION! 🎯**