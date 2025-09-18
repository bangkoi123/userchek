#!/usr/bin/env python3
"""
Real Telegram Account Login Script
Manual login process untuk real account
"""

import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def login_real_account():
    """Login real Telegram account manually"""
    
    print("🚀 REAL TELEGRAM ACCOUNT LOGIN")
    print("=" * 40)
    
    # Get credentials from user input
    api_id = input("Enter your API ID (from my.telegram.org): ").strip()
    api_hash = input("Enter your API Hash (from my.telegram.org): ").strip()
    phone_number = input("Enter your phone number (with +): ").strip()
    
    if not api_id or not api_hash or not phone_number:
        print("❌ All fields are required!")
        return
    
    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ API ID must be a number!")
        return
    
    # Setup session directory
    sessions_dir = "/app/data/sessions/real_accounts"
    os.makedirs(sessions_dir, exist_ok=True)
    
    session_name = f"real_account_{phone_number.replace('+', '').replace(' ', '')}"
    
    print(f"\n📱 Creating session: {session_name}")
    print(f"📁 Session directory: {sessions_dir}")
    
    # Optional proxy setup
    proxy_config = None
    use_proxy = input("\nDo you want to use proxy? (y/n): ").lower().strip()
    
    if use_proxy == 'y':
        proxy_host = input("Proxy host: ").strip()
        proxy_port = input("Proxy port (1080): ").strip() or "1080"
        proxy_user = input("Proxy username (optional): ").strip() or None
        proxy_pass = input("Proxy password (optional): ").strip() or None
        
        if proxy_host:
            proxy_config = {
                "scheme": "socks5",
                "hostname": proxy_host,
                "port": int(proxy_port), 
                "username": proxy_user,
                "password": proxy_pass
            }
            print(f"🌐 Using proxy: {proxy_host}:{proxy_port}")
    
    # Create Telegram client
    client = Client(
        name=session_name,
        api_id=api_id,
        api_hash=api_hash,
        phone_number=phone_number,
        workdir=sessions_dir,
        proxy=proxy_config
    )
    
    try:
        print(f"\n🔐 Starting login process for {phone_number}...")
        
        # Start client (this will trigger login flow)
        await client.start()
        
        # Get account info
        me = await client.get_me()
        
        print(f"\n✅ LOGIN SUCCESSFUL!")
        print(f"👤 Name: {me.first_name} {me.last_name or ''}")
        print(f"📱 Phone: {me.phone_number}")
        print(f"🆔 Username: @{me.username or 'No username'}")
        print(f"🔒 User ID: {me.id}")
        print(f"💎 Premium: {'Yes' if me.is_premium else 'No'}")
        
        # Test basic functionality
        print(f"\n🧪 Testing account functionality...")
        
        # Get contacts count
        contacts = await client.get_contacts()
        print(f"📞 Contacts: {len(contacts)} contacts")
        
        # Get dialogs count  
        dialogs_count = 0
        async for dialog in client.get_dialogs(limit=10):
            dialogs_count += 1
        print(f"💬 Recent chats: {dialogs_count}+ dialogs")
        
        print(f"\n📁 Session file created: {sessions_dir}/{session_name}.session")
        print(f"🎯 Account ready for validation service!")
        
        # Save account info for integration
        account_info = {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone_number": phone_number,
            "user_id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "is_premium": me.is_premium,
            "session_file": f"{sessions_dir}/{session_name}.session",
            "proxy_config": proxy_config,
            "contacts_count": len(contacts),
            "status": "active"
        }
        
        # Save to file for later integration
        import json
        with open(f"/app/data/real_account_info.json", "w") as f:
            json.dump(account_info, f, indent=2)
        
        print(f"\n📋 Account info saved to: /app/data/real_account_info.json")
        
        await client.stop()
        
        print(f"\n🎉 SETUP COMPLETE!")
        print(f"Next steps:")
        print(f"1. Account session is now active")
        print(f"2. You can use this account for validation")
        print(f"3. Add to admin panel or Docker system")
        
    except Exception as e:
        print(f"\n❌ Login failed: {e}")
        
        if "PHONE_CODE_INVALID" in str(e):
            print("💡 Tip: Make sure you entered the correct verification code")
        elif "PHONE_NUMBER_INVALID" in str(e):
            print("💡 Tip: Make sure phone number format is correct (+6281234567890)")
        elif "API_ID_INVALID" in str(e):
            print("💡 Tip: Check your API ID from my.telegram.org")
        elif "API_HASH_INVALID" in str(e):
            print("💡 Tip: Check your API Hash from my.telegram.org")
        
        try:
            await client.stop()
        except:
            pass

async def main():
    """Main function"""
    try:
        await login_real_account()
    except KeyboardInterrupt:
        print("\n\n⏹️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🔐 TELEGRAM REAL ACCOUNT LOGIN SCRIPT")
    print("====================================")
    print("This script will help you login your real Telegram account")
    print("and create a session file for validation service.")
    print("\nRequirements:")
    print("1. API ID and API Hash from https://my.telegram.org/apps")  
    print("2. Your Telegram phone number")
    print("3. Access to Telegram app for verification")
    print("\n" + "="*50)
    
    asyncio.run(main())