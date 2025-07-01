import json
from src.utils.llm_client import LLMClient

class CustomerJourneyMapper:
    def __init__(self):
        self.llm = LLMClient()
        self.journey_stages = {
            "awareness": "Customer realizes they have a problem/need",
            "consideration": "Customer researches solutions and evaluates options", 
            "decision": "Customer decides on a specific solution/purchase",
            "retention": "Post-purchase experience and loyalty"
        }
    
    def map_customer_journey(self, topic, intent_data):
        primary_stage = intent_data.get('search_stage', 'awareness')
        
        prompt = f"""
        Map the customer journey for this topic: "{topic}"
        Focus primarily on the {primary_stage} stage but provide context for all stages.
        
        Provide analysis in JSON format:
        {{
            "journey_analysis": {{
                "awareness": {{
                    "customer_questions": ["question1", "question2"],
                    "pain_points": ["pain1", "pain2"],
                    "emotions": ["emotion1", "emotion2"],
                    "information_needs": ["need1", "need2"]
                }},
                "consideration": {{
                    "customer_questions": ["question1", "question2"],
                    "pain_points": ["pain1", "pain2"],
                    "emotions": ["emotion1", "emotion2"],
                    "information_needs": ["need1", "need2"]
                }},
                "decision": {{
                    "customer_questions": ["question1", "question2"],
                    "pain_points": ["pain1", "pain2"],
                    "emotions": ["emotion1", "emotion2"],
                    "information_needs": ["need1", "need2"]
                }}
            }},
            "primary_stage": "{primary_stage}",
            "key_pain_points": ["most important pain points"],
            "emotional_triggers": ["key emotions to address"],
            "content_opportunities": ["content ideas that address pain points"]
        }}
        
        Focus on authentic customer language and real problems people face.
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            return json.loads(response)
        except:
            # Fallback structure
            return {
                "journey_analysis": {
                    "awareness": {
                        "customer_questions": ["What is this?", "Do I need this?"],
                        "pain_points": ["Lack of information", "Confusion"],
                        "emotions": ["Curious", "Uncertain"],
                        "information_needs": ["Basic understanding", "Benefits"]
                    }
                },
                "primary_stage": primary_stage,
                "key_pain_points": ["Information gaps"],
                "emotional_triggers": ["Curiosity"],
                "content_opportunities": ["Educational content"]
            }