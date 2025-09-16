"""
WhatsApp Deep Link Validator - Custom Implementation
Simple, lightweight, cost-effective validation using WhatsApp deep links
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional
from datetime import datetime
import random
import time

class WhatsAppDeepLinkValidator:
    def __init__(self):
        self.session = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
    
    async def __aenter__(self):
        """Async context manager setup"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            headers={'User-Agent': random.choice(self.user_agents)}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup"""
        if self.session:
            await self.session.close()
    
    def clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number for WhatsApp"""
        # Remove all non-digits
        clean = ''.join(filter(str.isdigit, phone))
        
        # Handle Indonesian numbers specifically
        if clean.startswith('62'):
            return clean
        elif clean.startswith('0'):
            return '62' + clean[1:]  # Remove leading 0, add country code
        elif len(clean) >= 9 and not clean.startswith('62'):
            return '62' + clean  # Add Indonesia country code
        
        return clean
    
    async def validate_single_number(self, phone: str, identifier: str = None) -> Dict:
        """Validate single WhatsApp number using deep link method"""
        
        # Clean phone number
        clean_phone = self.clean_phone_number(phone)
        
        # Create WhatsApp deep link
        deep_link = f"https://api.whatsapp.com/send/?phone={clean_phone}&text&type=phone_number&app_absent=0"
        
        try:
            # Add random delay to avoid detection
            await asyncio.sleep(random.uniform(1, 3))
            
            print(f"🔍 Validating {phone} (cleaned: {clean_phone})")
            
            async with self.session.get(deep_link, allow_redirects=True) as response:
                content = await response.text()
                final_url = str(response.url)
                status_code = response.status
                
                print(f"   └─ Status: {status_code}, Final URL: {final_url[:50]}...")
                
                # Analyze response
                validation_result = self._analyze_response(
                    content, final_url, status_code, phone, clean_phone
                )
                
                # Add metadata
                validation_result.update({
                    'identifier': identifier,
                    'validated_at': datetime.utcnow(),
                    'method': 'whatsapp_deeplink',
                    'deep_link_used': deep_link,
                    'response_status': status_code
                })
                
                return validation_result
                
        except asyncio.TimeoutError:
            print(f"   └─ ⏰ Timeout for {phone}")
            return self._create_error_result(phone, identifier, 'timeout')
            
        except Exception as e:
            print(f"   └─ ❌ Error for {phone}: {str(e)}")
            return self._create_error_result(phone, identifier, str(e))
    
    def _analyze_response(self, content: str, final_url: str, status_code: int, 
                         original_phone: str, clean_phone: str) -> Dict:
        """Analyze WhatsApp response to determine number validity"""
        
        content_lower = content.lower()
        
        # Check for explicit invalid number messages
        invalid_indicators = [
            'não válido',           # Portuguese: not valid
            'tidak valid',          # Indonesian: not valid  
            'invalid',              # English: invalid
            'not valid',            # English: not valid
            'número inválido',      # Spanish: invalid number
            'numero non valido',    # Italian: invalid number
            'ungültige nummer',     # German: invalid number
            'numéro invalide',      # French: invalid number
            'номер недействителен', # Russian: invalid number
        ]
        
        # Check for invalid number indicators
        for indicator in invalid_indicators:
            if indicator in content_lower:
                print(f"   └─ ❌ Invalid number detected: '{indicator}'")
                return {
                    'phone_number': original_phone,
                    'platform': 'whatsapp',
                    'status': 'inactive',
                    'confidence': 0.95,
                    'details': {
                        'provider': 'whatsapp_deeplink',
                        'detection_method': 'error_message',
                        'error_indicator': indicator,
                        'api_response': 'invalid'
                    }
                }
        
        # Check for successful redirects to WhatsApp
        success_indicators = [
            'web.whatsapp.com' in final_url,
            'whatsapp.com/send' in final_url,
            'chat' in content_lower,
            'message' in content_lower,
            'whatsapp' in final_url
        ]
        
        if any(success_indicators):
            print(f"   └─ ✅ Valid number detected")
            return {
                'phone_number': original_phone,
                'platform': 'whatsapp', 
                'status': 'active',
                'confidence': 0.85,
                'details': {
                    'provider': 'whatsapp_deeplink',
                    'detection_method': 'successful_redirect',
                    'final_url': final_url,
                    'api_response': 'valid'
                }
            }
        
        # Ambiguous response - default to inactive with lower confidence
        print(f"   └─ ⚠️ Ambiguous response, defaulting to inactive")
        return {
            'phone_number': original_phone,
            'platform': 'whatsapp',
            'status': 'inactive', 
            'confidence': 0.60,
            'details': {
                'provider': 'whatsapp_deeplink',
                'detection_method': 'ambiguous_response',
                'api_response': 'unknown'
            }
        }
    
    def _create_error_result(self, phone: str, identifier: str, error: str) -> Dict:
        """Create error result structure"""
        return {
            'phone_number': phone,
            'identifier': identifier,
            'platform': 'whatsapp',
            'status': 'error',
            'confidence': 0,
            'validated_at': datetime.utcnow(),
            'method': 'whatsapp_deeplink',
            'details': {
                'provider': 'whatsapp_deeplink',
                'error': error,
                'api_response': 'error'
            }
        }
    
    async def validate_bulk(self, phone_numbers: List[str], 
                           batch_size: int = 10, delay_between_batches: int = 5) -> List[Dict]:
        """Validate multiple numbers with batching and rate limiting"""
        
        results = []
        total_numbers = len(phone_numbers)
        
        print(f"🚀 Starting WhatsApp Deep Link validation for {total_numbers} numbers")
        print(f"📊 Processing in batches of {batch_size} with {delay_between_batches}s delays")
        
        # Process in batches to avoid overwhelming
        for i in range(0, len(phone_numbers), batch_size):
            batch = phone_numbers[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_numbers + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} numbers)")
            
            # Process batch concurrently
            batch_tasks = []
            for phone in batch:
                task = self.validate_single_number(phone, f"batch_{batch_num}_{phone}")
                batch_tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"   └─ ❌ Batch error: {str(result)}")
                    results.append(self._create_error_result("unknown", "batch_error", str(result)))
                else:
                    results.append(result)
            
            # Delay between batches (except for last batch)
            if i + batch_size < len(phone_numbers):
                print(f"⏸️ Waiting {delay_between_batches} seconds before next batch...")
                await asyncio.sleep(delay_between_batches)
        
        # Summary
        active_count = len([r for r in results if r.get('status') == 'active'])
        inactive_count = len([r for r in results if r.get('status') == 'inactive'])
        error_count = len([r for r in results if r.get('status') == 'error'])
        
        print(f"\n📊 Validation Summary:")
        print(f"   ✅ Active: {active_count}")
        print(f"   ❌ Inactive: {inactive_count}")
        print(f"   ⚠️ Errors: {error_count}")
        print(f"   📈 Success Rate: {((active_count + inactive_count) / total_numbers * 100):.1f}%")
        
        return results

# Integration function for existing webtools
async def validate_whatsapp_deeplink_batch(phone_numbers: List[str]) -> Dict:
    """Integration function for webtools - returns format compatible with existing system"""
    
    async with WhatsAppDeepLinkValidator() as validator:
        results = await validator.validate_bulk(phone_numbers, batch_size=5, delay_between_batches=3)
    
    # Convert to format expected by existing system
    formatted_results = {}
    for result in results:
        clean_phone = validator.clean_phone_number(result['phone_number'])
        
        formatted_results[clean_phone] = {
            'status': result['status'],
            'api_response': result['details'].get('api_response', 'unknown'),
            'confidence': result.get('confidence', 0),
            'provider': 'whatsapp_deeplink',
            'method': 'deep_link_validation'
        }
    
    return formatted_results

# Testing function
async def test_deeplink_validation():
    """Test function to validate the implementation"""
    
    test_numbers = [
        '+6281234567890',
        '081234567890', 
        '6285123456789',
        '+6289876543210',
        '08111222333'
    ]
    
    print("🧪 Testing WhatsApp Deep Link Validation")
    print("=" * 50)
    
    async with WhatsAppDeepLinkValidator() as validator:
        results = await validator.validate_bulk(test_numbers, batch_size=2, delay_between_batches=2)
    
    print("\n" + "=" * 50)
    print("📋 DETAILED RESULTS:")
    print("=" * 50)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'active' else "❌" if result['status'] == 'inactive' else "⚠️"
        confidence = result.get('confidence', 0)
        method = result['details'].get('detection_method', 'unknown')
        
        print(f"{status_icon} {result['phone_number']}")
        print(f"   Status: {result['status']} (confidence: {confidence:.0%})")
        print(f"   Method: {method}")
        print(f"   Provider: {result['details'].get('provider', 'unknown')}")
        print()

if __name__ == "__main__":
    # Run test
    asyncio.run(test_deeplink_validation())