# Create this new file in your root directory
from src.main import EnhancedContentCreationAgent

def test_enhanced_agent():
    """Test the enhanced agent with Figment methodology"""
    print("🧪 Testing Enhanced AI Content Agent with Human-AI Collaboration...")
    
    # Create enhanced agent
    agent = EnhancedContentCreationAgent()
    
    # Test with a sample topic
    topic = "best budget laptops for college students"
    subreddits = ["laptops", "college", "StudentLoans"]
    
    print(f"\n📝 Testing with topic: {topic}")
    print(f"📍 Subreddits: {subreddits}")
    
    # Generate high-performance content
    results = agent.create_complete_content(
        topic=topic,
        target_subreddits=subreddits,
        interactive_mode=True  # Will ask you questions
    )
    
    # Review performance predictions
    print("\n" + "="*50)
    print("📊 PERFORMANCE ANALYSIS")
    print("="*50)
    
    if 'eeat_assessment' in results:
        eeat_score = results['eeat_assessment'].get('overall_eeat_score', 'N/A')
        print(f"🏆 E-E-A-T Score: {eeat_score}/10")
    
    if 'quality_assessment' in results:
        quality_score = results['quality_assessment'].get('overall_quality_score', 'N/A')
        performance = results['quality_assessment'].get('performance_prediction', 'N/A')
        traffic_mult = results['quality_assessment'].get('traffic_multiplier_estimate', 'N/A')
        
        print(f"⭐ Quality Score: {quality_score}/10")
        print(f"📈 Performance Prediction: {performance}")
        print(f"🚀 Traffic Multiplier: {traffic_mult}")
    
    # Save results
    filename = agent.save_complete_results(results)
    print(f"\n💾 Results saved to: {filename}")
    
    return results

if __name__ == "__main__":
    test_enhanced_agent()