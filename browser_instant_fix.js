// INSTANT WHATSAPP ACCOUNT CREATION FIX
// Copy-paste script ini ke browser console di https://checktool.preview.emergentagent.com/admin/whatsapp-accounts

console.log("🚀 INSTANT WHATSAPP ACCOUNT CREATION");
console.log("=".repeat(50));

// Function to create WhatsApp account directly
async function createWhatsAppAccountInstant() {
    try {
        // Get auth token
        const token = localStorage.getItem('token');
        if (!token) {
            console.log("❌ No auth token found - please login as admin first");
            return false;
        }
        
        console.log("✅ Auth token found");
        
        // Account data (modify as needed)
        const accountData = {
            name: "Browser Console Account",
            phone_number: "+628123456789",
            login_method: "qr_code", 
            max_daily_requests: 100,
            notes: "Created via browser console debug"
        };
        
        console.log("📋 Account data:", accountData);
        
        // Try different backend URLs
        const backendUrls = [
            'https://checktool.preview.emergentagent.com',
            'https://wa-deeplink-check.preview.emergentagent.com',
            window.location.origin
        ];
        
        for (const baseUrl of backendUrls) {
            try {
                console.log(`🌐 Trying: ${baseUrl}`);
                
                const response = await fetch(`${baseUrl}/api/admin/whatsapp-accounts`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(accountData),
                    mode: 'cors'
                });
                
                console.log(`📊 ${baseUrl} - Status: ${response.status}`);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log("🎉 SUCCESS! Account created:");
                    console.log(result);
                    
                    // Refresh the page to see new account
                    console.log("🔄 Refreshing page to show new account...");
                    window.location.reload();
                    
                    return true;
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    console.log(`❌ ${baseUrl} failed: ${response.status} - ${errorData.detail || response.statusText}`);
                }
                
            } catch (fetchError) {
                console.log(`❌ ${baseUrl} network error:`, fetchError.message);
            }
        }
        
        console.log("❌ All backend URLs failed");
        return false;
        
    } catch (error) {
        console.log("💥 Unexpected error:", error);
        return false;
    }
}

// Function to test backend connectivity
async function testBackendConnectivity() {
    console.log("\n🔍 TESTING BACKEND CONNECTIVITY");
    console.log("-".repeat(40));
    
    const testUrls = [
        'https://checktool.preview.emergentagent.com/docs',
        'https://wa-deeplink-check.preview.emergentagent.com/docs', 
        `${window.location.origin}/docs`
    ];
    
    for (const url of testUrls) {
        try {
            const response = await fetch(url, { method: 'GET', mode: 'cors' });
            console.log(`✅ ${url} - Status: ${response.status}`);
            
            if (response.ok) {
                console.log(`   🎯 Working backend found: ${url.replace('/docs', '')}`);
            }
            
        } catch (error) {
            console.log(`❌ ${url} - Error: ${error.message}`);
        }
    }
}

// Function to check current environment
function checkEnvironment() {
    console.log("\n📊 ENVIRONMENT CHECK");
    console.log("-".repeat(30));
    console.log(`Current URL: ${window.location.href}`);
    console.log(`Origin: ${window.location.origin}`);
    console.log(`Protocol: ${window.location.protocol}`);
    console.log(`Host: ${window.location.host}`);
    
    // Check React environment variables
    if (window.React && window.React.env) {
        console.log(`React Env Backend URL: ${window.React.env.REACT_APP_BACKEND_URL}`);
    }
    
    // Check auth status
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    console.log(`Auth Token: ${token ? 'Present' : 'Missing'}`);
    console.log(`User: ${user.username} (${user.role})`);
}

// Auto-run all tests
console.log("🏁 RUNNING AUTO-DIAGNOSIS...");
checkEnvironment();

testBackendConnectivity().then(() => {
    console.log("\n🚀 READY TO CREATE ACCOUNT");
    console.log("💡 Run: createWhatsAppAccountInstant()");
    console.log("💡 Or modify account data in script and run again");
});

// Make function available globally
window.createWhatsAppAccountInstant = createWhatsAppAccountInstant;
window.testBackendConnectivity = testBackendConnectivity;

console.log("\n📋 AVAILABLE COMMANDS:");
console.log("• createWhatsAppAccountInstant() - Create account directly");
console.log("• testBackendConnectivity() - Test backend URLs");
console.log("\n🎯 Try running: createWhatsAppAccountInstant()");