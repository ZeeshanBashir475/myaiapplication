import json
from src.utils.llm_client import LLMClient

class EEATAssessor:
    def __init__(self):
        self.llm = LLMClient()
        
        # Based on Figment's E-E-A-T breakdown
        self.eeat_criteria = {
            "experience": {
                "description": "First-hand, lived involvement with the topic",
                "signals": ["Personal use stories", "Real case studies", "Behind-the-scenes access"],
                "ai_limitation": "Cannot fake real experience",
                "human_required": True
            },
            "expertise": {
                "description": "Deep knowledge and skill in the subject area",
                "signals": ["Credentials", "Industry experience", "Technical accuracy"],
                "ai_limitation": "Limited to training data patterns",
                "human_required": "For specialized topics"
            },
            "authoritativeness": {
                "description": "Recognition as a go-to source in the field",
                "signals": ["Backlinks", "Citations", "Industry recognition"],
                "ai_limitation": "Cannot build real authority",
                "human_required": "For credibility building"
            },
            "trustworthiness": {
                "description": "Reliability and honesty of content and creator",
                "signals": ["Accurate sources", "Transparent disclaimers", "Consistent quality"],
                "ai_limitation": "Risk of hallucinations and inaccuracies",
                "human_required": "For fact-checking and verification"
            }
        }
    
    def assess_content_eeat_requirements(self, topic, content_type, business_context, human_inputs):
        industry = business_context.get('industry', '').lower()
        
        prompt = f"""
        Assess this content against Google's E-E-A-T criteria:
        
        Topic: {topic}
        Content Type: {content_type}
        Industry: {industry}
        Business Context: {business_context}
        Available Human Inputs: {json.dumps(human_inputs, indent=2) if human_inputs else 'None'}
        
        For each E-E-A-T component, assess:
        1. Current strength level (1-10)
        2. Critical gaps that need human input
        3. Specific improvements needed
        4. Risk level if gaps remain unaddressed
        
        Respond in JSON format:
        {{
            "eeat_assessment": {{
                "experience": {{
                    "current_score": 1-10,
                    "gaps": ["specific gap 1", "specific gap 2"],
                    "human_requirements": ["what human input is needed"],
                    "improvement_actions": ["specific actions to improve"]
                }},
                "expertise": {{
                    "current_score": 1-10,
                    "gaps": ["specific gap 1", "specific gap 2"],
                    "human_requirements": ["what human input is needed"],
                    "improvement_actions": ["specific actions to improve"]
                }},
                "authoritativeness": {{
                    "current_score": 1-10,
                    "gaps": ["specific gap 1", "specific gap 2"],
                    "human_requirements": ["what human input is needed"],
                    "improvement_actions": ["specific actions to improve"]
                }},
                "trustworthiness": {{
                    "current_score": 1-10,
                    "gaps": ["specific gap 1", "specific gap 2"],
                    "human_requirements": ["what human input is needed"],
                    "improvement_actions": ["specific actions to improve"]
                }}
            }},
            "overall_eeat_score": 1-10,
            "performance_prediction": "expected performance vs AI-only content",
            "critical_improvements": ["most important changes needed"],
            "industry_specific_requirements": ["additional requirements for this industry"]
        }}
        """
        
        response = self.llm.generate_structured(prompt)
        try:
            return json.loads(response)
        except:
            return self._generate_fallback_eeat_assessment(topic, content_type, business_context)
    
    def _generate_fallback_eeat_assessment(self, topic, content_type, business_context):
        industry = business_context.get('industry', '').lower()
        
        # Higher standards for regulated industries
        base_score = 4 if industry in ['healthcare', 'finance', 'legal'] else 6
        
        return {
            "eeat_assessment": {
                "experience": {
                    "current_score": base_score,
                    "gaps": ["Need first-hand experience", "Missing real-world examples"],
                    "human_requirements": ["Personal experience sharing", "Case study collection"],
                    "improvement_actions": ["Add personal anecdotes", "Include customer stories"]
                },
                "expertise": {
                    "current_score": base_score + 1,
                    "gaps": ["Need industry credentials", "Missing technical depth"],
                    "human_requirements": ["Expert interviews", "Professional verification"],
                    "improvement_actions": ["Add author credentials", "Include expert quotes"]
                },
                "authoritativeness": {
                    "current_score": base_score,
                    "gaps": ["Need citation building", "Missing industry recognition"],
                    "human_requirements": ["Industry connections", "Credible source access"],
                    "improvement_actions": ["Build backlink strategy", "Cite authoritative sources"]
                },
                "trustworthiness": {
                    "current_score": base_score + 1,
                    "gaps": ["Need fact verification", "Missing transparency"],
                    "human_requirements": ["Human fact-checking", "Compliance review"],
                    "improvement_actions": ["Verify all claims", "Add appropriate disclaimers"]
                }
            },
            "overall_eeat_score": base_score,
            "performance_prediction": "Moderate performance without human enhancement",
            "critical_improvements": ["Add human experience", "Verify all facts", "Include expert input"],
            "industry_specific_requirements": ["Higher compliance standards"] if industry in ['healthcare', 'finance', 'legal'] else []
        }