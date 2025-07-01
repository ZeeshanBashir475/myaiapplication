import json
from src.utils.llm_client import LLMClient

class BusinessContextCollector:
    def __init__(self):
        self.llm = LLMClient()
    
    def collect_interactive_context(self, topic, content_type):
        print(f"\n🏢 Let's understand your business better for: {topic}")
        print(f"📄 Content Type: {content_type}")
        print("="*60)
        
        context = {}
        
        # Basic Business Info
        print("\n📋 BASIC BUSINESS INFORMATION")
        context['industry'] = input("What industry are you in? ")
        context['business_type'] = input("What type of business? (B2B/B2C/Both): ")
        context['target_audience'] = input("Who is your primary target audience? ")
        context['company_size'] = input("Company size? (Startup/Small/Medium/Enterprise): ")
        
        # Competitive Advantage  
        print("\n🎯 COMPETITIVE POSITIONING")
        context['main_competitors'] = input("Who are your main competitors? ")
        context['unique_value_prop'] = input("What makes you different from competitors? ")
        context['key_strengths'] = input("What are your key strengths/advantages? ")
        
        # Content Goals
        print("\n📝 CONTENT OBJECTIVES")
        context['content_goal'] = input("What's the main goal for this content? ")
        context['target_action'] = input("What action do you want readers to take? ")
        context['brand_voice'] = input("How would you describe your brand voice? (Professional/Casual/Technical/etc.): ")
        
        # Customer Insights
        print("\n👥 CUSTOMER INSIGHTS")
        context['customer_pain_points'] = input("What are your customers' biggest challenges? ")
        context['frequent_questions'] = input("What questions do customers ask most often? ")
        context['success_stories'] = input("Can you share a brief customer success story? ")
        
        return context
    
    def analyze_business_context(self, context, topic):
        prompt = f"""
        Analyze this business context to optimize content creation:
        
        Topic: {topic}
        Business Context: {json.dumps(context, indent=2)}
        
        Provide strategic recommendations in JSON format:
        {{
            "content_angle": "best angle for this business to approach the topic",
            "key_differentiators": ["unique points this business should emphasize"],
            "audience_insights": {{
                "primary_motivations": ["what drives their audience"],
                "preferred_communication_style": "how to communicate with them",
                "decision_factors": ["what influences their decisions"]
            }},
            "competitive_advantages": ["how to position against competitors"],
            "content_hooks": ["compelling angles based on business strengths"],
            "trust_signals": ["credibility elements to include"],
            "customization_opportunities": ["where to add business-specific details"]
        }}
        """
        
        response = self.llm.generate_structured(prompt)
        try:
            return json.loads(response)
        except:
            return {
                "content_angle": "Educational approach based on business context",
                "key_differentiators": ["Focus on business strengths"],
                "competitive_advantages": ["Unique market positioning"],
                "audience_insights": {
                    "primary_motivations": ["Learning and problem-solving"],
                    "preferred_communication_style": "Clear and helpful",
                    "decision_factors": ["Quality and trustworthiness"]
                }
            }