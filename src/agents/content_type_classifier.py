import json
from src.utils.llm_client import LLMClient

class ContentTypeClassifier:
    def __init__(self):
        self.llm = LLMClient()
        self.content_types = {
            "blog_post": "Educational or informational article for blog",
            "landing_page": "Conversion-focused page for specific offer/product",
            "product_page": "Detailed product description and sales copy",
            "category_page": "Overview page for product category",
            "guide": "Step-by-step instructional content",
            "comparison": "Side-by-side product/service comparison",
            "review": "In-depth product or service review",
            "listicle": "List-based article (Top 10, Best of, etc.)",
            "case_study": "Success story or implementation example",
            "faq": "Frequently asked questions format",
            "email": "Email marketing content",
            "social_media": "Social media posts and captions"
        }
    
    def classify_content_type(self, topic, intent_data, business_context=None):
        """Determine the best content type and get user confirmation"""
        
        prompt = f"""
        Based on this topic and intent, suggest the best content type and alternatives:
        
        Topic: {topic}
        Intent: {intent_data}
        Business Context: {business_context or 'Not provided'}
        
        Available Content Types:
        {json.dumps(self.content_types, indent=2)}
        
        Provide response in JSON format:
        {{
            "primary_recommendation": {{
                "type": "content_type_key",
                "reasoning": "why this type is best",
                "conversion_potential": "high/medium/low",
                "effort_required": "high/medium/low"
            }},
            "alternatives": [
                {{
                    "type": "alternative_type", 
                    "reasoning": "why this could work",
                    "use_case": "when to choose this instead"
                }}
            ],
            "content_strategy": {{
                "primary_goal": "main objective",
                "target_audience": "specific audience description",
                "key_messages": ["message1", "message2"],
                "call_to_action": "recommended CTA"
            }}
        }}
        """
        
        response = self.llm.generate_structured(prompt)
        try:
            return json.loads(response)
        except:
            return {
                "primary_recommendation": {
                    "type": "blog_post",
                    "reasoning": "Default educational content",
                    "conversion_potential": "medium",
                    "effort_required": "medium"
                },
                "alternatives": [
                    {
                        "type": "guide",
                        "reasoning": "Detailed step-by-step approach",
                        "use_case": "When users need comprehensive instructions"
                    }
                ],
                "content_strategy": {
                    "primary_goal": "education and engagement",
                    "target_audience": "general audience",
                    "key_messages": ["helpful information", "actionable advice"],
                    "call_to_action": "learn more"
                }
            }