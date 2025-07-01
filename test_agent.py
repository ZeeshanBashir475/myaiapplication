from src.main import ContentCreationAgent

def test_basic_functionality():
    """Test basic agent functionality"""
    print("🧪 Testing AI Content Agent...")
    
    # Initialize agent
    agent = ContentCreationAgent()
    
    # Test with simple topic
    topic = "best wireless headphones"
    subreddits = ["headphones", "audiophile"]
    
    print(f"\n📝 Testing with topic: {topic}")
    print(f"📍 Subreddits: {subreddits}")
    
    # Run content creation
    results = agent.create_content_strategy(topic, subreddits)
    
    # Check results
    if 'error' in results:
        print(f"❌ Test failed: {results['error']}")
        return False
    
    print("✅ Test passed! Agent is working correctly.")
    
    # Print summary
    if 'content_strategy' in results:
        headlines = results['content_strategy'].get('headline_options', [])
        print(f"\n📋 Generated Headlines: {headlines}")
    
    return True

if __name__ == "__main__":
    test_basic_functionality()