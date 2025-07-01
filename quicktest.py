print("🧪 Testing AI Content Agent Setup...")

try:
    # Test basic imports
    import os
    from dotenv import load_dotenv
    print("✅ Basic imports working")
    
    # Load environment variables
    load_dotenv()
    print("✅ Environment loading working")
    
    # Check if API keys exist
    reddit_id = os.getenv("REDDIT_CLIENT_ID")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"✅ Reddit ID exists: {bool(reddit_id)}")
    print(f"✅ Anthropic key exists: {bool(anthropic_key)}")
    
    if reddit_id and anthropic_key:
        print("🎉 API keys are loaded successfully!")
    else:
        print("❌ API keys missing - check your .env file")
    
except Exception as e:
    print(f"❌ Error: {e}")