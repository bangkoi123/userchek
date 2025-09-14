import aiohttp
import asyncio

async def debug_whatsapp_response(phone):
    """Debug actual HTML response for a phone number"""
    
    phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
    if phone.startswith('0'):
        phone = '62' + phone[1:]
    elif not phone.startswith('62'):
        phone = '62' + phone
    
    url = f"https://api.whatsapp.com/send/?phone={phone}&text&type=phone_number&app_absent=0"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                html = await response.text()
                
                print(f"=== DEBUGGING {phone} ===")
                print(f"URL: {url}")
                print(f"Status: {response.status}")
                print(f"Response length: {len(html)}")
                print(f"Response headers: {dict(response.headers)}")
                print("\n--- HTML CONTENT SAMPLE (first 1000 chars) ---")
                print(html[:1000])
                print("\n--- HTML CONTENT SAMPLE (last 1000 chars) ---")
                print(html[-1000:])
                
                # Check for specific patterns
                print("\n--- PATTERN ANALYSIS ---")
                print(f"Contains 'tidak valid': {'tidak valid' in html.lower()}")
                print(f"Contains 'invalid': {'invalid' in html.lower()}")
                print(f"Contains 'error': {'error' in html.lower()}")
                print(f"Contains 'nomor telepon': {'nomor telepon' in html.lower()}")
                print(f"Contains 'main_block': {'main_block' in html}")
                print(f"Contains 'fallback_block': {'fallback_block' in html}")
                print(f"Contains 'web.whatsapp.com': {'web.whatsapp.com' in html}")
                
                return html
                
        except Exception as e:
            print(f"Error: {e}")
            return None

async def main():
    # Debug the problematic number that should be inactive
    print("🔍 Debugging known INACTIVE number: 6285586712458")
    await debug_whatsapp_response("6285586712458")
    
    print("\n" + "="*80 + "\n")
    
    # Debug known ACTIVE number for comparison
    print("🔍 Debugging known ACTIVE number: 082253767671")
    await debug_whatsapp_response("082253767671")

if __name__ == "__main__":
    asyncio.run(main())