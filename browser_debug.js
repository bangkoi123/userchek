// Browser Console Debug Script for WhatsApp Account Creation
// Paste this into browser console at https://checktool.preview.emergentagent.com/admin/whatsapp-accounts

console.log("🔍 DEBUGGING WHATSAPP ACCOUNT CREATION IN BROWSER");
console.log("=".repeat(60));

// Step 1: Check authentication
console.log("\n1. Checking Authentication...");
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token) {
    console.log("❌ No authentication token found");
    console.log("💡 Please login as admin first");
} else {
    console.log("✅ Authentication token found");
    console.log(`   User: ${user.username} (${user.role})`);
    console.log(`   Token: ${token.substring(0, 50)}...`);
}

// Step 2: Check backend URL configuration
console.log("\n2. Checking Backend URL Configuration...");
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
console.log(`   Backend URL: ${backendUrl}`);
console.log(`   Current domain: ${window.location.origin}`);

if (backendUrl.includes(window.location.hostname)) {
    console.log("✅ Backend URL matches current domain");
} else {
    console.log("⚠️ Backend URL domain mismatch");
    console.log("💡 This might cause CORS issues");
}

// Step 3: Test API call function
console.log("\n3. Testing API Call Function...");

async function testApiCall() {
    try {
        // Import the apiCall function (if available in global scope)
        const { apiCall } = window.React || {};
        
        if (!apiCall) {
            console.log("⚠️ apiCall function not available in global scope");
            console.log("💡 Testing with direct fetch instead");
            
            // Direct fetch test
            const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: "Browser Debug Test",
                    phone_number: "+628123456789",
                    login_method: "qr_code",
                    max_daily_requests: 100,
                    notes: "Browser console debug test"
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log("✅ Direct fetch successful!");
                console.log("   Response:", result);
                return true;
            } else {
                console.log("❌ Direct fetch failed");
                console.log(`   Status: ${response.status} ${response.statusText}`);
                console.log("   Error:", result);
                return false;
            }
        }
        
    } catch (error) {
        console.log("❌ API test error:", error);
        console.log("   Error name:", error.name);
        console.log("   Error message:", error.message);
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            console.log("💡 Network connectivity issue");
        } else if (error.message.includes('CORS')) {
            console.log("💡 CORS policy issue");
        } else if (error.message.includes('401') || error.message.includes('403')) {
            console.log("💡 Authentication issue");
        }
        
        return false;
    }
}

// Step 4: Check for console errors
console.log("\n4. Checking for Console Errors...");
const originalError = console.error;
const errors = [];

console.error = function(...args) {
    errors.push(args);
    originalError.apply(console, args);
};

// Step 5: Check network tab
console.log("\n5. Network Debugging Instructions...");
console.log("💡 Open Network tab in DevTools");
console.log("💡 Try creating account again");
console.log("💡 Look for failed requests to /api/admin/whatsapp-accounts");
console.log("💡 Check request/response details");

// Step 6: Run the test
console.log("\n6. Running API Test...");
testApiCall().then(success => {
    console.log("\n" + "=".repeat(60));
    console.log("📊 BROWSER DEBUG SUMMARY");
    console.log("=".repeat(60));
    
    console.log(`Authentication: ${token ? '✅ OK' : '❌ MISSING'}`);
    console.log(`Backend URL: ${backendUrl}`);
    console.log(`API Test: ${success ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`Console Errors: ${errors.length > 0 ? `⚠️ ${errors.length} errors` : '✅ None'}`);
    
    if (errors.length > 0) {
        console.log("\n📋 Console Errors Found:");
        errors.forEach((error, i) => {
            console.log(`   ${i + 1}. ${error.join(' ')}`);
        });
    }
    
    if (success) {
        console.log("\n🎉 BROWSER TEST PASSED!");
        console.log("💡 API calls are working from browser");
        console.log("💡 Issue might be in React component logic");
    } else {
        console.log("\n❌ BROWSER TEST FAILED");
        console.log("💡 Check network tab for failed requests");
        console.log("💡 Check CORS configuration");
        console.log("💡 Verify authentication token");
    }
});

// Step 7: Additional debug info
console.log("\n7. Additional Debug Information...");
console.log(`   Current URL: ${window.location.href}`);
console.log(`   User Agent: ${navigator.userAgent}`);
console.log(`   Cookies: ${document.cookie || 'None'}`);
console.log(`   Local Storage Keys: ${Object.keys(localStorage).join(', ')}`);

console.log("\n🚀 Browser debug script loaded!");
console.log("💡 Results will appear above when API test completes");