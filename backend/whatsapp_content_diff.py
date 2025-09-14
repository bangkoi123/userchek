import asyncio
from playwright.async_api import async_playwright
import difflib

async def get_whatsapp_content(phone):
    """Get full content for a WhatsApp number"""
    phone = phone.strip().replace('+', '').replace('-', '').replace(' ', '')
    if phone.startswith('0'):
        phone = '62' + phone[1:]
    elif not phone.startswith('62'):
        phone = '62' + phone
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        try:
            await page.goto(f"https://wa.me/{phone}", wait_until='networkidle', timeout=15000)
            await page.wait_for_timeout(3000)
            
            # Get both text and HTML content
            text_content = await page.evaluate("document.body.textContent")
            html_content = await page.content()
            
            await browser.close()
            
            return {
                "phone": phone,
                "text_content": text_content,
                "html_content": html_content,
                "text_length": len(text_content),
                "html_length": len(html_content)
            }
            
        except Exception as e:
            await browser.close()
            return {"phone": phone, "error": str(e)}

async def compare_whatsapp_content():
    """Compare content between active and inactive numbers"""
    print("🔍 CONTENT COMPARISON - ACTIVE vs INACTIVE")
    print("=" * 60)
    
    # Test numbers: one active, one inactive
    active_phone = "082253767671"   # Known active
    inactive_phone = "6285586712458"  # Known inactive
    
    print(f"📞 Getting content for ACTIVE number: {active_phone}")
    active_content = await get_whatsapp_content(active_phone)
    
    print(f"📞 Getting content for INACTIVE number: {inactive_phone}")
    inactive_content = await get_whatsapp_content(inactive_phone)
    
    if "error" in active_content or "error" in inactive_content:
        print("❌ Error getting content")
        return
    
    print(f"\n📊 CONTENT LENGTH COMPARISON:")
    print(f"Active  ({active_phone}):  {active_content['text_length']:,} chars")
    print(f"Inactive ({inactive_phone}): {inactive_content['text_length']:,} chars")
    print(f"Difference: {inactive_content['text_length'] - active_content['text_length']:,} chars")
    
    print(f"\n📊 HTML LENGTH COMPARISON:")
    print(f"Active  ({active_phone}):  {active_content['html_length']:,} chars")
    print(f"Inactive ({inactive_phone}): {inactive_content['html_length']:,} chars")
    print(f"Difference: {inactive_content['html_length'] - active_content['html_length']:,} chars")
    
    # Find text differences
    print(f"\n🔍 TEXT CONTENT DIFFERENCES:")
    
    active_lines = active_content['text_content'].splitlines()
    inactive_lines = inactive_content['text_content'].splitlines()
    
    diff = list(difflib.unified_diff(
        active_lines, 
        inactive_lines,
        fromfile=f'ACTIVE_{active_phone}',
        tofile=f'INACTIVE_{inactive_phone}',
        lineterm=''
    ))
    
    if diff:
        print("📝 Text differences found:")
        for line in diff[:50]:  # Show first 50 lines of diff
            print(f"  {line}")
    else:
        print("📝 No text differences found!")
    
    # Check for specific patterns in each
    print(f"\n🎯 PATTERN ANALYSIS:")
    
    # Check active content
    active_text = active_content['text_content'].lower()
    inactive_text = inactive_content['text_content'].lower()
    
    patterns_to_check = [
        "continue to chat",
        "send message", 
        "chat now",
        "download whatsapp",
        "install whatsapp",
        "tidak valid",
        "invalid number",
        "nomor telepon",
        "phone number shared via url is invalid",
        "nomor telepon yang dibagikan via tautan tidak valid"
    ]
    
    print(f"\n{'Pattern':<50} {'Active':<10} {'Inactive':<10}")
    print("-" * 70)
    
    differences_found = []
    
    for pattern in patterns_to_check:
        active_has = pattern in active_text
        inactive_has = pattern in inactive_text
        
        status_active = "✅" if active_has else "❌"
        status_inactive = "✅" if inactive_has else "❌"
        
        print(f"{pattern:<50} {status_active:<10} {status_inactive:<10}")
        
        if active_has != inactive_has:
            differences_found.append({
                "pattern": pattern,
                "active_has": active_has,
                "inactive_has": inactive_has
            })
    
    print(f"\n🚨 CRITICAL DIFFERENCES FOUND:")
    if differences_found:
        for diff in differences_found:
            print(f"  📍 '{diff['pattern']}':")
            print(f"    - Active: {'Present' if diff['active_has'] else 'NOT Present'}")
            print(f"    - Inactive: {'Present' if diff['inactive_has'] else 'NOT Present'}")
    else:
        print("  ⚠️ No pattern differences found in text content!")
    
    # Save content to files for manual inspection
    with open(f"/app/active_{active_phone}_content.txt", "w", encoding='utf-8') as f:
        f.write(active_content['text_content'])
    
    with open(f"/app/inactive_{inactive_phone}_content.txt", "w", encoding='utf-8') as f:
        f.write(inactive_content['text_content'])
    
    with open(f"/app/active_{active_phone}_html.html", "w", encoding='utf-8') as f:
        f.write(active_content['html_content'])
    
    with open(f"/app/inactive_{inactive_phone}_html.html", "w", encoding='utf-8') as f:
        f.write(inactive_content['html_content'])
    
    print(f"\n💾 Content saved to files for detailed inspection:")
    print(f"  - /app/active_{active_phone}_content.txt")
    print(f"  - /app/inactive_{inactive_phone}_content.txt")
    print(f"  - /app/active_{active_phone}_html.html")
    print(f"  - /app/inactive_{inactive_phone}_html.html")
    
    return differences_found

if __name__ == "__main__":
    asyncio.run(compare_whatsapp_content())