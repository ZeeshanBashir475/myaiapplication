#!/usr/bin/env python3
"""
Test script for Anthropic API - Add this to your GitHub repository
Run with: python test_api.py
"""

import os
import sys

def test_anthropic_api():
    print("🧪 Testing Anthropic API Connection...")
    print("=" * 50)
    
    # Check if anthropic is installed
    try:
        import anthropic
        print(f"✅ Anthropic library installed: version {getattr(anthropic, '__version__', 'unknown')}")
    except ImportError:
        print("❌ Anthropic library not installed!")
        print("🔧 Run: pip install anthropic")
        return False
    
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("🔧 Set it with: export ANTHROPIC_API_KEY='sk-ant-your-key-here'")
        print("🔧 Or add it to your .env file")
        return False
    
    print(f"✅ API Key found")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Format: {api_key[:15]}...{api_key[-10:]}")
    print(f"   Starts with 'sk-ant-': {api_key.startswith('sk-ant-')}")
    
    if not api_key.startswith("sk-ant-"):
        print("❌ Invalid API key format!")
        print("🔧 Anthropic keys should start with 'sk-ant-'")
        print("🔧 Get a new key from: https://console.anthropic.com/settings/keys")
        return False
    
    try:
        print("\n🔍 Testing API connection...")
        
        # Initialize client
        client = anthropic.Anthropic(
            api_key=api_key,
            timeout=30.0
        )
        
        # Test API call
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=25,
            messages=[{"role": "user", "content": "Respond with: 'API test successful! Your Anthropic key is working.'"}]
        )
        
        print("✅ API test SUCCESSFUL!")
        print(f"✅ Response: {response.content[0].text}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Usage: {response.usage.input_tokens} input tokens, {response.usage.output_tokens} output tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ API test FAILED: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        
        # Provide specific solutions
        error_str = str(e).lower()
        print("\n🔧 SOLUTIONS:")
        
        if "authentication" in error_str or "invalid" in error_str:
            print("   → Your API key is invalid")
            print("   → Get a new key: https://console.anthropic.com/settings/keys")
            print("   → Make sure you copied the complete key")
        elif "quota" in error_str or "insufficient" in error_str:
            print("   → No credits remaining on your account")
            print("   → Add credits: https://console.anthropic.com/settings/billing")
        elif "rate_limit" in error_str:
            print("   → Rate limit exceeded")
            print("   → Wait 1 minute and try again")
        elif "timeout" in error_str:
            print("   → Network timeout")
            print("   → Check your internet connection")
        else:
            print(f"   → Unknown error: {e}")
            print("   → Check Anthropic status: https://status.anthropic.com")
        
        return False

def test_environment_setup():
    """Test if environment is properly set up"""
    print("\n🌍 Testing Environment Setup...")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check required libraries
    required_libs = ['anthropic', 'fastapi', 'uvicorn', 'aiohttp']
    
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"✅ {lib} installed")
        except ImportError:
            print(f"❌ {lib} NOT installed")
            print(f"🔧 Install with: pip install {lib}")
    
    # Check environment variables
    env_vars = ['ANTHROPIC_API_KEY', 'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET']
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} is set ({len(value)} chars)")
        else:
            print(f"⚠️  {var} not set")

if __name__ == "__main__":
    print("🚀 API Testing Suite")
    print("=" * 50)
    
    # Test environment first
    test_environment_setup()
    
    # Test API
    api_success = test_anthropic_api()
    
    print("\n" + "=" * 50)
    if api_success:
        print("🎉 SUCCESS! Your Anthropic API is working correctly.")
        print("   If your Railway app still isn't working, the issue is with")
        print("   environment variables in Railway, not your API key.")
    else:
        print("❌ FAILED! Fix the API key issue first before deploying.")
    
    print("\n🔍 Next steps:")
    print("   1. Fix any issues shown above")
    print("   2. Test your Railway app with: /debug-ai-detailed")
    print("   3. Check Railway environment variables")
