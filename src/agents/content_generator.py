import json
from src.utils.llm_client import LLMClient

class ContentGenerator:
    def __init__(self):
        self.llm = LLMClient()
    
    def generate_content(self, topic, intent_data, journey_data, reddit_insights):
        """Generate compelling content based on all gathered insights"""
        
        prompt = f"""
        Create compelling content strategy and outline based on these insights:
        
        TOPIC: {topic}
        
        INTENT DATA: {json.dumps(intent_data, indent=2)}
        
        CUSTOMER JOURNEY: {json.dumps(journey_data, indent=2)}
        
        REDDIT INSIGHTS: {json.dumps(reddit_insights, indent=2)}
        
        Generate a comprehensive content strategy in JSON format:
        {{
            "headline_options": ["3 compelling headlines using customer language"],
            "content_structure": {{
                "hook": "Opening that grabs attention using customer pain points",
                "main_sections": [
                    {{
                        "section_title": "Title addressing specific pain point",
                        "key_points": ["point 1", "point 2"],
                        "customer_voice_integration": "How to incorporate authentic customer language"
                    }}
                ],
                "conclusion": "Strong conclusion with clear next steps"
            }},
            "semantic_elements": {{
                "emotional_triggers": ["emotions to evoke"],
                "pain_points_addressed": ["specific problems solved"],
                "value_propositions": ["clear benefits provided"],
                "social_proof_opportunities": ["where to add testimonials/examples"]
            }},
            "customer_language_integration": {{
                "phrases_to_use": ["exact customer phrases from Reddit"],
                "questions_to_answer": ["questions from Reddit to address"],
                "tone_recommendations": "conversational|professional|empathetic"
            }},
            "call_to_action": {{
                "primary_cta": "Main action you want readers to take",
                "secondary_cta": "Alternative action option",
                "placement_strategy": "Where to place CTAs for maximum impact"
            }},
            "seo_considerations": {{
                "primary_keywords": ["main keywords to target"],
                "semantic_keywords": ["related terms to include"],
                "content_length_recommendation": "word count range"
            }}
        }}
        
        Apply these semantic principles:
        1. Use authentic customer language from Reddit insights
        2. Address specific pain points identified in research
        3. Structure content for the identified customer journey stage
        4. Include emotional resonance based on sentiment analysis
        5. Provide clear, actionable value
        6. Make it scannable and easy to consume
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            return json.loads(response)
        except:
            return self._generate_fallback_content(topic, intent_data)
    
    def _generate_fallback_content(self, topic, intent_data):
        """Fallback content structure if generation fails"""
        return {
            "headline_options": [
                f"The Complete Guide to {topic}",
                f"Everything You Need to Know About {topic}",
                f"How to Master {topic}: A Step-by-Step Guide"
            ],
            "content_structure": {
                "hook": f"If you're struggling with {topic}, you're not alone.",
                "main_sections": [
                    {
                        "section_title": f"What is {topic}?",
                        "key_points": ["Definition", "Key benefits"],
                        "customer_voice_integration": "Use simple, clear language"
                    }
                ],
                "conclusion": f"Start implementing these {topic} strategies today"
            },
            "semantic_elements": {
                "emotional_triggers": ["confidence", "relief"],
                "pain_points_addressed": ["confusion", "lack of information"],
                "value_propositions": ["clear guidance", "actionable steps"],
                "social_proof_opportunities": ["case studies", "examples"]
            }
        }