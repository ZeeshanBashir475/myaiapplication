import json
import datetime
from src.agents.intent_classifier import IntentClassifier
from src.agents.journey_mapper import CustomerJourneyMapper
from src.agents.reddit_researcher import RedditResearcher
from src.agents.content_type_classifier import ContentTypeClassifier
from src.agents.human_input_identifier import HumanInputIdentifier
from src.agents.business_context_collector import BusinessContextCollector
from src.agents.eeat_assessor import EEATAssessor
from src.agents.content_quality_scorer import ContentQualityScorer
from src.agents.full_content_generator import FullContentGenerator

class EnhancedContentCreationAgent:
    """
    Enhanced Content Creation Agent incorporating Figment Agency's research:
    - Human content generates 5.44x more traffic than AI-only content
    - E-E-A-T compliance is critical for performance
    - Hybrid approach (AI + Human) delivers best results
    """
    def __init__(self):
        print("🚀 Initializing Enhanced Content Creation Agent...")
        print("📊 Incorporating Figment Agency's human vs AI performance research...")
        
        self.intent_classifier = IntentClassifier()
        self.journey_mapper = CustomerJourneyMapper()
        self.reddit_researcher = RedditResearcher()
        self.content_type_classifier = ContentTypeClassifier()
        self.human_input_identifier = HumanInputIdentifier()
        self.business_context_collector = BusinessContextCollector()
        self.eeat_assessor = EEATAssessor()
        self.quality_scorer = ContentQualityScorer()
        self.content_generator = FullContentGenerator()
        
        print("✅ Enhanced Agent initialized with human-AI collaboration framework!")
        print("💡 Ready to create content that performs 3-5x better than AI-only approaches!")
    
    def create_complete_content(self, topic, target_subreddits, interactive_mode=True):
        """Create complete content with human-AI collaboration based on Figment research"""
        
        print(f"\n🎯 Creating High-Performance Content for: {topic}")
        print("📈 Using human-AI hybrid approach for maximum performance")
        print("="*70)
        
        results = {
            'topic': topic,
            'subreddits_researched': target_subreddits,
            'timestamp': str(datetime.datetime.now()),
            'methodology': 'Figment Agency human-AI hybrid approach',
            'performance_target': '3-5x better than AI-only content'
        }
        
        try:
            # Step 1: Classify Intent
            print("\n📊 Step 1: Analyzing content intent...")
            intent_data = self.intent_classifier.classify_intent(topic)
            results['intent_analysis'] = intent_data
            print(f"✅ Intent: {intent_data.get('primary_intent', 'unknown')}")
            
            # Step 2: Map Customer Journey
            print("\n🗺️ Step 2: Mapping customer journey...")
            journey_data = self.journey_mapper.map_customer_journey(topic, intent_data)
            results['journey_analysis'] = journey_data
            print(f"✅ Primary stage: {journey_data.get('primary_stage', 'awareness')}")
            
            # Step 3: Research Reddit for Customer Voice
            print("\n🔍 Step 3: Researching authentic customer insights...")
            reddit_insights = self.reddit_researcher.research_topic(topic, target_subreddits)
            results['reddit_insights'] = reddit_insights
            print("✅ Customer voice captured from Reddit discussions")
            
            # Step 4: Collect Business Context
            if interactive_mode:
                print("\n🏢 Step 4: Collecting business context for E-E-A-T optimization...")
                business_context = self.business_context_collector.collect_interactive_context(
                    topic, intent_data.get('content_type_recommendation', 'blog_post')
                )
            else:
                business_context = {}
            
            business_analysis = self.business_context_collector.analyze_business_context(
                business_context, topic
            )
            results['business_context'] = business_context
            results['business_analysis'] = business_analysis
            
            # Step 5: Classify Content Type
            print("\n📄 Step 5: Determining optimal content type...")
            content_type_data = self.content_type_classifier.classify_content_type(
                topic, intent_data, business_context
            )
            
            if interactive_mode:
                self.display_content_type_options(content_type_data)
                chosen_type = self.get_user_content_type_choice(content_type_data)
            else:
                chosen_type = content_type_data['primary_recommendation']['type']
            
            results['content_type_analysis'] = content_type_data
            results['chosen_content_type'] = chosen_type
            
            # Step 6: Identify Critical Human Inputs (Based on Figment Research)
            print(f"\n🤝 Step 6: Identifying critical human expertise needed...")
            print("💡 Research shows: Human input is essential for high-performing content")
            
            human_input_needs = self.human_input_identifier.identify_human_inputs(
                topic, chosen_type, business_context
            )
            
            # Display why human input is critical
            if human_input_needs.get('critical_human_inputs'):
                print(f"\n⚠️ CRITICAL: Human expertise needed for optimal performance")
                for input_need in human_input_needs['critical_human_inputs']:
                    print(f"   🎯 {input_need['area']}: {input_need['why_critical']}")
            
            if interactive_mode:
                human_inputs = self.collect_specific_human_inputs(human_input_needs)
            else:
                human_inputs = {}
            
            results['human_input_needs'] = human_input_needs
            results['human_inputs'] = human_inputs
            
            # Step 7: Assess E-E-A-T Requirements
            print(f"\n🏆 Step 7: Assessing E-E-A-T compliance for search performance...")
            eeat_assessment = self.eeat_assessor.assess_content_eeat_requirements(
                topic, chosen_type, business_context, human_inputs
            )
            results['eeat_assessment'] = eeat_assessment
            print(f"✅ E-E-A-T score: {eeat_assessment.get('overall_eeat_score', 'N/A')}/10")
            
            # Step 8: Generate Complete Content
            print(f"\n✍️ Step 8: Creating high-performance {chosen_type}...")
            print("🔧 Using hybrid AI + human approach for maximum impact")
            
            complete_content = self.content_generator.generate_complete_content(
                topic, chosen_type, reddit_insights, journey_data, 
                business_context, human_inputs, eeat_assessment
            )
            
            # Step 9: Score Content Quality
            print(f"\n📊 Step 9: Scoring content quality vs AI baseline...")
            quality_score = self.quality_scorer.score_content_quality(
                complete_content, topic, business_context, human_inputs, eeat_assessment
            )
            
            results['final_content'] = complete_content
            results['quality_assessment'] = quality_score
            results['content_metadata'] = {
                'type': chosen_type,
                'word_count': len(complete_content.split()),
                'target_audience': business_context.get('target_audience', 'General'),
                'business_goal': business_context.get('content_goal', 'Education'),
                'eeat_score': eeat_assessment.get('overall_eeat_score', 'N/A'),
                'quality_score': quality_score.get('overall_quality_score', 'N/A'),
                'performance_prediction': quality_score.get('performance_prediction', 'N/A')
            }
            
            # Display Results Summary
            print("\n" + "="*70)
            print("🎉 HIGH-PERFORMANCE CONTENT CREATED!")
            print("="*70)
            print(f"📄 Content Type: {chosen_type}")
            print(f"📝 Word Count: {len(complete_content.split())}")
            print(f"🏆 E-E-A-T Score: {eeat_assessment.get('overall_eeat_score', 'N/A')}/10")
            print(f"⭐ Quality Score: {quality_score.get('overall_quality_score', 'N/A')}/10")
            print(f"📈 Performance Prediction: {quality_score.get('performance_prediction', 'N/A')}")
            print(f"🚀 Traffic Multiplier: {quality_score.get('traffic_multiplier_estimate', 'N/A')}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error during content creation: {str(e)}")
            results['error'] = str(e)
            return results
    
    def display_content_type_options(self, content_type_data):
        """Display content type options to user"""
        print("\n📄 CONTENT TYPE RECOMMENDATIONS")
        print("="*50)
        
        primary = content_type_data['primary_recommendation']
        print(f"🎯 PRIMARY RECOMMENDATION: {primary['type'].upper()}")
        print(f"   Reasoning: {primary['reasoning']}")
        print(f"   Conversion Potential: {primary.get('conversion_potential', 'N/A')}")
        print(f"   Effort Required: {primary.get('effort_required', 'N/A')}")
        
        if 'alternatives' in content_type_data:
            print(f"\n🔄 ALTERNATIVES:")
            for i, alt in enumerate(content_type_data['alternatives'], 1):
                print(f"   {i}. {alt['type']} - {alt['reasoning']}")
    
    def get_user_content_type_choice(self, content_type_data):
        """Get user's content type choice"""
        primary = content_type_data['primary_recommendation']['type']
        alternatives = [alt['type'] for alt in content_type_data.get('alternatives', [])]
        
        print(f"\nChoose content type:")
        print(f"1. {primary} (Recommended)")
        for i, alt in enumerate(alternatives, 2):
            print(f"{i}. {alt}")
        
        while True:
            try:
                choice = input(f"\nEnter choice (1-{len(alternatives) + 1}) or press Enter for recommendation: ").strip()
                if not choice:
                    return primary
                choice_num = int(choice)
                if choice_num == 1:
                    return primary
                elif 2 <= choice_num <= len(alternatives) + 1:
                    return alternatives[choice_num - 2]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
    
    def collect_specific_human_inputs(self, human_input_needs):
        """Collect specific human inputs based on identified needs"""
        human_inputs = {}
        
        if not human_input_needs.get('required_inputs'):
            return human_inputs
        
        print(f"\n🤝 HUMAN EXPERTISE NEEDED")
        print("="*50)
        print("The AI needs your expertise in these areas:")
        
        for input_need in human_input_needs['required_inputs']:
            category = input_need['category']
            priority = input_need['priority']
            
            print(f"\n📋 {category.upper()} ({priority})")
            print(f"Why needed: {input_need['reasoning']}")
            
            category_inputs = {}
            for question in input_need['questions']:
                answer = input(f"❓ {question}: ")
                category_inputs[question] = answer
            
            human_inputs[category] = category_inputs
        
        return human_inputs
    
    def save_complete_results(self, results, filename=None):
        """Save complete content creation results"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            content_type = results.get('chosen_content_type', 'content')
            filename = f"data/complete_{content_type}_{timestamp}.json"
        
        # Save JSON results
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save content as separate file
        if 'final_content' in results:
            content_filename = filename.replace('.json', '_content.txt')
            with open(content_filename, 'w', encoding='utf-8') as f:
                f.write(results['final_content'])
            print(f"📄 Content saved to: {content_filename}")
        
        print(f"💾 Complete results saved to: {filename}")
        return filename

# Example usage function
def create_enhanced_content():
    """Example of using the enhanced agent"""
    agent = EnhancedContentCreationAgent()
    
    # Example with interaction
    topic = input("Enter your content topic: ")
    subreddits = input("Enter relevant subreddits (comma-separated): ").split(',')
    subreddits = [s.strip() for s in subreddits if s.strip()]
    
    results = agent.create_complete_content(topic, subreddits, interactive_mode=True)
    filename = agent.save_complete_results(results)
    
    print(f"\n🎉 CONTENT CREATION COMPLETED!")
    print(f"📊 Type: {results.get('chosen_content_type', 'Unknown')}")
    print(f"📝 Words: {results.get('content_metadata', {}).get('word_count', 0)}")
    print(f"💾 Saved: {filename}")
    
    return results

if __name__ == "__main__":
    create_enhanced_content()