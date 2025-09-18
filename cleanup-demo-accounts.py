#!/usr/bin/env python3
"""
Cleanup Demo Telegram Accounts
Hapus semua demo accounts dari database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def cleanup_demo_accounts():
    """Hapus semua demo telegram accounts"""
    
    print("🧹 CLEANUP DEMO TELEGRAM ACCOUNTS")
    print("=" * 40)
    
    # Get MongoDB connection
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME = os.environ.get('DB_NAME', 'webtools_validation')
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Get all telegram accounts
        all_accounts = await db.telegram_accounts.find({}).to_list(length=None)
        print(f"📊 Total accounts found: {len(all_accounts)}")
        
        # Count demo accounts
        demo_accounts = [acc for acc in all_accounts if acc.get('demo_account', False) or acc.get('account_type') == 'demo']
        real_accounts = [acc for acc in all_accounts if not acc.get('demo_account', False) and acc.get('account_type') != 'demo']
        
        print(f"🎭 Demo accounts: {len(demo_accounts)}")
        print(f"🔐 Real accounts: {len(real_accounts)}")
        
        if len(demo_accounts) == 0:
            print("✅ No demo accounts to delete")
            return
        
        # Show demo accounts that will be deleted
        print(f"\n📋 Demo accounts to be deleted:")
        for acc in demo_accounts:
            name = acc.get('name', 'Unknown')
            phone = acc.get('phone_number', 'Unknown')
            account_type = acc.get('account_type', 'demo')
            print(f"  - {name} ({phone}) [{account_type}]")
        
        # Confirm deletion
        print(f"\n⚠️  This will DELETE {len(demo_accounts)} demo accounts")
        print("Real accounts will be preserved")
        
        confirm = input("\nContinue? (y/N): ").lower().strip()
        
        if confirm == 'y':
            # Delete demo accounts
            delete_filter = {
                "$or": [
                    {"demo_account": True},
                    {"account_type": "demo"},
                    {"name": {"$regex": "^Telegram Demo"}},
                    {"name": {"$regex": "^Demo"}}
                ]
            }
            
            result = await db.telegram_accounts.delete_many(delete_filter)
            
            print(f"\n✅ Successfully deleted {result.deleted_count} demo accounts")
            
            # Verify cleanup
            remaining = await db.telegram_accounts.find({}).to_list(length=None)
            real_remaining = [acc for acc in remaining if not acc.get('demo_account', False) and acc.get('account_type') != 'demo']
            
            print(f"📊 Remaining accounts: {len(remaining)}")
            print(f"🔐 Real accounts preserved: {len(real_remaining)}")
            
            if len(real_remaining) > 0:
                print(f"\n📋 Remaining real accounts:")
                for acc in real_remaining:
                    name = acc.get('name', 'Unknown')
                    phone = acc.get('phone_number', 'Unknown')
                    status = acc.get('status', 'unknown')
                    print(f"  - {name} ({phone}) [{status}]")
            
            print(f"\n🎉 CLEANUP COMPLETED!")
            
        else:
            print("❌ Cleanup cancelled")
    
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_demo_accounts())