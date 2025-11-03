import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# HTML template for testing
TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Environment Test</title>
    <style>
        body { font-family: Arial; padding: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #1e3c72; }
        .test-result { padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ccc; }
        .success { background: #d4edda; border-color: #28a745; }
        .error { background: #f8d7da; border-color: #dc3545; }
        .warning { background: #fff3cd; border-color: #ffc107; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        .key-display { font-family: monospace; background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Environment Variable Test</h1>
        <p>This page checks if your OpenAI API key is accessible to the application.</p>
        
        <div id="results">
            <p>Loading test results...</p>
        </div>
        
        <button onclick="runTest()" style="padding: 10px 20px; background: #1e3c72; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 20px;">
            🔄 Run Test Again
        </button>
    </div>
    
    <script>
        async function runTest() {
            try {
                const response = await fetch('/api/test-env');
                const data = await response.json();
                
                let html = '<h2>Test Results:</h2>';
                
                // Check 1: Variable names
                html += '<div class="test-result ' + (data.Open_Api_Key_found || data.OPENAI_API_KEY_found ? 'success' : 'error') + '">';
                html += '<strong>✓ Check 1: Environment Variables</strong><br>';
                html += 'Open_Api_Key found: ' + (data.Open_Api_Key_found ? '✅ Yes' : '❌ No') + '<br>';
                html += 'OPENAI_API_KEY found: ' + (data.OPENAI_API_KEY_found ? '✅ Yes' : '❌ No');
                html += '</div>';
                
                // Check 2: Key format
                if (data.key_info) {
                    html += '<div class="test-result ' + (data.key_info.valid_format ? 'success' : 'error') + '">';
                    html += '<strong>✓ Check 2: Key Format</strong><br>';
                    html += 'Starts with "sk-": ' + (data.key_info.starts_with_sk ? '✅ Yes' : '❌ No') + '<br>';
                    html += 'Key length: ' + data.key_info.length + ' characters<br>';
                    html += 'Masked key: <code>' + data.key_info.masked + '</code>';
                    html += '</div>';
                } else {
                    html += '<div class="test-result error">';
                    html += '<strong>✗ Check 2: No Key Found</strong><br>';
                    html += 'No OpenAI API key detected in environment variables';
                    html += '</div>';
                }
                
                // Check 3: OpenAI library
                html += '<div class="test-result ' + (data.openai_imported ? 'success' : 'error') + '">';
                html += '<strong>✓ Check 3: OpenAI Library</strong><br>';
                html += 'Library imported: ' + (data.openai_imported ? '✅ Yes' : '❌ No') + '<br>';
                if (data.openai_version) {
                    html += 'Version: ' + data.openai_version;
                }
                html += '</div>';
                
                // Check 4: Client initialization
                if (data.client_test) {
                    html += '<div class="test-result ' + (data.client_test.success ? 'success' : 'error') + '">';
                    html += '<strong>✓ Check 4: OpenAI Client</strong><br>';
                    if (data.client_test.success) {
                        html += '✅ Client initialized successfully!';
                    } else {
                        html += '❌ Client initialization failed<br>';
                        html += 'Error: ' + data.client_test.error;
                    }
                    html += '</div>';
                }
                
                // Check 5: API test
                if (data.api_test) {
                    html += '<div class="test-result ' + (data.api_test.success ? 'success' : 'error') + '">';
                    html += '<strong>✓ Check 5: API Connection</strong><br>';
                    if (data.api_test.success) {
                        html += '✅ API call successful! OpenAI is working!';
                    } else {
                        html += '❌ API call failed<br>';
                        html += 'Error: ' + data.api_test.error;
                    }
                    html += '</div>';
                }
                
                // Diagnosis
                html += '<div class="test-result warning">';
                html += '<strong>📋 Diagnosis:</strong><br>';
                html += data.diagnosis;
                html += '</div>';
                
                document.getElementById('results').innerHTML = html;
            } catch (error) {
                document.getElementById('results').innerHTML = '<div class="test-result error">Error running test: ' + error + '</div>';
            }
        }
        
        // Run test on page load
        runTest();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(TEST_PAGE)

@app.route('/api/test-env')
def test_env():
    """Test environment variables and OpenAI setup"""
    results = {
        "Open_Api_Key_found": False,
        "OPENAI_API_KEY_found": False,
        "key_info": None,
        "openai_imported": False,
        "openai_version": None,
        "client_test": None,
        "api_test": None,
        "diagnosis": ""
    }
    
    # Check 1: Look for API keys
    open_api_key = os.getenv('Open_Api_Key')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    results["Open_Api_Key_found"] = bool(open_api_key)
    results["OPENAI_API_KEY_found"] = bool(openai_api_key)
    
    # Use whichever key we found
    api_key = openai_api_key or open_api_key
    
    # Check 2: Analyze key format
    if api_key:
        results["key_info"] = {
            "starts_with_sk": api_key.startswith('sk-'),
            "length": len(api_key),
            "masked": f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***",
            "valid_format": api_key.startswith('sk-') and len(api_key) >= 40
        }
    
    # Check 3: Import OpenAI
    try:
        import openai
        results["openai_imported"] = True
        results["openai_version"] = getattr(openai, '__version__', 'unknown')
    except Exception as e:
        results["diagnosis"] += f"❌ Cannot import openai library: {str(e)}\n"
    
    # Check 4: Initialize client
    if results["openai_imported"] and api_key:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key, timeout=30.0)
            results["client_test"] = {
                "success": True,
                "error": None
            }
        except Exception as e:
            results["client_test"] = {
                "success": False,
                "error": str(e)
            }
    
    # Check 5: Test API call
    if results["client_test"] and results["client_test"]["success"]:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key, timeout=30.0)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            results["api_test"] = {
                "success": True,
                "error": None
            }
        except Exception as e:
            results["api_test"] = {
                "success": False,
                "error": str(e)
            }
    
    # Generate diagnosis
    if not results["Open_Api_Key_found"] and not results["OPENAI_API_KEY_found"]:
        results["diagnosis"] = "❌ NO API KEY FOUND: Neither 'Open_Api_Key' nor 'OPENAI_API_KEY' exists in environment. Add your OpenAI API key in Railway variables."
    elif api_key and not api_key.startswith('sk-'):
        results["diagnosis"] = "❌ INVALID KEY FORMAT: Your API key doesn't start with 'sk-'. Get a valid key from platform.openai.com/api-keys"
    elif api_key and len(api_key) < 40:
        results["diagnosis"] = "❌ KEY TOO SHORT: Your API key is only " + str(len(api_key)) + " characters. Valid keys are 40-60 characters. The key may be truncated."
    elif not results["openai_imported"]:
        results["diagnosis"] = "❌ OPENAI LIBRARY NOT INSTALLED: Add 'openai' to requirements.txt"
    elif results["client_test"] and not results["client_test"]["success"]:
        results["diagnosis"] = f"❌ CLIENT INITIALIZATION FAILED: {results['client_test']['error']}"
    elif results["api_test"] and not results["api_test"]["success"]:
        error_msg = results["api_test"]["error"]
        if "insufficient_quota" in error_msg:
            results["diagnosis"] = "❌ NO OPENAI CREDITS: Add payment method and credits at platform.openai.com/account/billing"
        elif "invalid_api_key" in error_msg or "Incorrect API key" in error_msg:
            results["diagnosis"] = "❌ INVALID API KEY: The key is wrong or expired. Generate a new key at platform.openai.com/api-keys"
        elif "rate_limit" in error_msg:
            results["diagnosis"] = "⚠️ RATE LIMIT: Too many requests. Wait a minute and try again."
        else:
            results["diagnosis"] = f"❌ API CALL FAILED: {error_msg}"
    else:
        results["diagnosis"] = "✅ EVERYTHING WORKS! Your OpenAI API key is valid and the connection is working. The issue must be in your main app.py file."
    
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print("=" * 60)
    print("STARTING TEST APPLICATION")
    print("=" * 60)
    print(f"Visit the app URL to see test results")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
