import json
from src.utils.llm_client import LLMClient

class IntentClassifier:
    def __init__(self):
        self.llm = LLMClient()
    
    def classify_intent(self, topic_description):
        prompt = f"""
        Analyze this content topic and classify its search intent:
        
        Topic: "{topic_description}"
        
        Provide your analysis in JSON format:
        {{
            "primary_intent": "commercial|informational|navigational|commercial_informational",
            "search_stage": "awareness|consideration|decision",
            "target_audience": "brief description",
            "user_goals": ["goal1", "goal2", "goal3"],
            "content_type_recommendation": "blog_post|guide|comparison|review|tutorial",
            "urgency_level": "low|medium|high"
        }}
        
        Intent definitions:
        - Commercial: User wants to buy something
        - Informational: User wants to learn something
        - Navigational: User wants to find a specific website/page
        - Commercial_informational: User researching before buying
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            return json.loads(response)
        except:
            # Fallback if JSON parsing fails
            return {
                "primary_intent": "informational",
                "search_stage": "awareness",
                "target_audience": "general users",
                "user_goals": ["learn about topic"],
                "content_type_recommendation": "blog_post",
                "urgency_level": "medium"
            }