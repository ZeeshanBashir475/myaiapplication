import json
from src.utils.llm_client import LLMClient

class HumanInputIdentifier:
    def __init__(self):
        self.llm = LLMClient()
        self.human_input_categories = {
            "business_specific": "Company policies, procedures, unique value props",
            "experiential": "Personal experiences, case studies, testimonials", 
            "technical_expertise": "Industry-specific technical knowledge",
            "current_data": "Real-time pricing, availability, specifications",
            "brand_voice": "Company tone, messaging, brand personality",
            "legal_compliance": "Industry regulations, disclaimers, legal requirements",
            "competitive_advantage": "What makes you different from competitors",
            "customer_insights": "Specific customer feedback, success stories"
        }
    
    def identify_human_inputs(self, topic, content_type, business_context):
        prompt = f"""
        Analyze this content creation task and identify where human input is essential:
        
        Topic: {topic}
        Content Type: {content_type}
        Business Context: {business_context}
        
        Human Input Categories:
        {json.dumps(self.human_input_categories, indent=2)}
        
        For each category that applies, specify:
        1. Why human input is needed
        2. What specific information to ask for
        3. How critical it is (critical/important/nice-to-have)
        
        Respond in JSON format:
        {{
            "required_inputs": [
                {{
                    "category": "category_name",
                    "reasoning": "why needed",
                    "questions": ["specific question 1", "specific question 2"],
                    "priority": "critical/important/nice-to-have",
                    "impact": "how this affects content quality"
                }}
            ],
            "ai_can_handle": [
                "aspects AI can create without human input"
            ],
            "collaboration_points": [
                "specific moments in content creation where human review is needed"
            ]
        }}
        """
        
        response = self.llm.generate_structured(prompt)
        try:
            return json.loads(response)
        except:
            return {"required_inputs": [], "ai_can_handle": [], "collaboration_points": []}
    
    def generate_business_context_questions(self):
        return {
            "basic_info": [
                "What industry are you in?",
                "What products/services do you offer?", 
                "Who is your target audience?",
                "What's your company size?",
                "What's your main business goal?"
            ],
            "competitive_landscape": [
                "Who are your main competitors?",
                "What makes you different from competitors?",
                "What's your unique value proposition?",
                "What are your key strengths?"
            ],
            "content_goals": [
                "What's the main goal for this content?",
                "Where will this content be published?",
                "What action do you want readers to take?",
                "What's your brand voice/tone?"
            ],
            "audience_specific": [
                "What are your customers' biggest pain points?",
                "What questions do customers frequently ask?",
                "What objections do customers typically have?",
                "What success stories can you share?"
            ]
        }