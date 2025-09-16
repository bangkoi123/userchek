// Quick WhatsApp Account Test Script
// Paste this into browser console at https://wa-deeplink-check.preview.emergentagent.com/admin/whatsapp-accounts

console.log("🚀 TESTING WHATSAPP ACCOUNT MANAGEMENT FIX");
console.log("=".repeat(50));

// Test 1: Check authentication
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token) {
    console.log("❌ Please login as admin first");
} else {
    console.log("✅ Authenticated as:", user.username, "(" + user.role + ")");
}

// Test 2: Test backend connectivity
async function testBackend() {
    try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://wa-deeplink-check.preview.emergentagent.com';
        console.log("🌐 Testing backend:", backendUrl);
        
        const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log("📊 Backend status:", response.status);
        if (response.ok) {
            const accounts = await response.json();
            console.log("✅ Backend working! Accounts:", accounts.length);
            return true;
        }
        return false;
    } catch (error) {
        console.log("❌ Backend error:", error.message);
        return false;
    }
}

// Test 3: Test account creation
async function testCreateAccount() {
    try {
        console.log("🎯 Testing account creation...");
        
        const accountData = {
            name: "Console Test Account",
            phone_number: "+628999888777",
            login_method: "qr_code",
            max_daily_requests: 100,
            notes: "Created via console test"
        };
        
        const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://wa-deeplink-check.preview.emergentagent.com';
        
        const response = await fetch(`${backendUrl}/api/admin/whatsapp-accounts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(accountData)
        });
        
        console.log("📊 Create response:", response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log("✅ Account created successfully!");
            console.log("📋 Result:", result);
            
            // Test login with new account
            const accountId = result.account._id;
            console.log("🔐 Testing login for new account:", accountId);
            
            const loginResponse = await fetch(`${backendUrl}/api/admin/whatsapp-accounts/${accountId}/login`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (loginResponse.ok) {
                const loginResult = await loginResponse.json();
                console.log("✅ Login successful!");
                console.log("📱 QR Code available:", !!loginResult.qr_code);
                console.log("📋 Login result:", loginResult);
                
                if (loginResult.qr_code) {
                    console.log("🎉 QR CODE GENERATED SUCCESSFULLY!");
                    console.log("📏 QR Code length:", loginResult.qr_code.length);
                    
                    // Display QR code in new window for testing
                    const qrWindow = window.open('', '_blank', 'width=400,height=500');
                    qrWindow.document.write(`
                        <html>
                        <head><title>WhatsApp QR Code</title></head>
                        <body style="text-align:center; padding:20px;">
                            <h2>📱 WhatsApp QR Code</h2>
                            <p>Scan dengan WhatsApp mobile app</p>
                            <img src="${loginResult.qr_code}" style="max-width:300px;" />
                            <p><small>Expires in: ${loginResult.expires_in || 300} seconds</small></p>
                        </body>
                        </html>
                    `);
                    
                    alert("✅ QR Code generated! Check new window to scan.");
                } else {
                    console.log("⚠️ No QR code in response");
                }
                
            } else {
                const loginError = await loginResponse.json();
                console.log("❌ Login failed:", loginError);
            }
            
            return true;
        } else {
            const errorData = await response.json();
            console.log("❌ Account creation failed:", errorData);
            return false;
        }
        
    } catch (error) {
        console.log("💥 Test error:", error);
        return false;
    }
}

// Auto-run tests
testBackend().then(backendOk => {
    if (backendOk) {
        console.log("\n🎯 Backend OK - Testing account creation...");
        testCreateAccount().then(success => {
            console.log("\n" + "=".repeat(50));
            console.log("📊 FINAL RESULT:", success ? "✅ ALL TESTS PASSED" : "❌ TESTS FAILED");
            console.log("=".repeat(50));
        });
    }
});

console.log("\n💡 Available commands:");
console.log("• testBackend() - Test backend connectivity");
console.log("• testCreateAccount() - Test full account creation + login flow");