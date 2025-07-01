import json
from src.utils.llm_client import LLMClient

class ContentQualityScorer:
    def __init__(self):
        self.llm = LLMClient()
        
        # Quality factors from Figment research
        self.quality_factors = {
            "authenticity": {
                "weight": 25,
                "description": "Real voice, personal experience, genuine insights",
                "human_advantage": "Cannot be faked by AI"
            },
            "emotional_connection": {
                "weight": 20,
                "description": "Empathy, tone, emotional intelligence",
                "human_advantage": "AI lacks emotional understanding"
            },
            "industry_insight": {
                "weight": 20,
                "description": "Deep understanding of industry nuances",
                "human_advantage": "Lived experience vs training data"
            },
            "accuracy": {
                "weight": 15,
                "description": "Factual correctness, source credibility",
                "human_advantage": "Can verify and fact-check"
            },
            "originality": {
                "weight": 10,
                "description": "Unique perspective, novel insights",
                "human_advantage": "Original thinking vs pattern matching"
            },
            "contextual_relevance": {
                "weight": 10,
                "description": "Current events, situational awareness",
                "human_advantage": "Real-time understanding"
            }
        }
    
    def score_content_quality(self, content, topic, business_context, human_inputs, eeat_assessment):
        prompt = f"""
        Score this content's quality using research methodology that shows
        human content gets 5.44x more traffic than AI content.
        
        Content Preview: {content[:500] if content else 'Not provided'}...
        Topic: {topic}
        Business Context: {business_context}
        Human Inputs Available: {json.dumps(list(human_inputs.keys()) if human_inputs else [], indent=2)}
        E-E-A-T Assessment: {eeat_assessment.get('overall_eeat_score', 'Not assessed')}
        
        Quality Factors:
        {json.dumps(self.quality_factors, indent=2)}
        
        For each factor, score 1-10 and identify:
        1. Current performance level
        2. What makes it human-quality vs AI-quality
        3. Specific gaps that reduce performance
        4. Improvement suggestions
        
        Respond in JSON format:
        {{
            "quality_scores": {{
                "authenticity": {{
                    "score": 1-10,
                    "analysis": "why this score",
                    "human_vs_ai": "how human input would improve this",
                    "improvement_actions": ["specific improvements"]
                }},
                "emotional_connection": {{
                    "score": 1-10,
                    "analysis": "why this score", 
                    "human_vs_ai": "how human input would improve this",
                    "improvement_actions": ["specific improvements"]
                }},
                "industry_insight": {{
                    "score": 1-10,
                    "analysis": "why this score",
                    "human_vs_ai": "how human input would improve this", 
                    "improvement_actions": ["specific improvements"]
                }},
                "accuracy": {{
                    "score": 1-10,
                    "analysis": "why this score",
                    "human_vs_ai": "how human input would improve this",
                    "improvement_actions": ["specific improvements"]
                }},
                "originality": {{
                    "score": 1-10,
                    "analysis": "why this score",
                    "human_vs_ai": "how human input would improve this",
                    "improvement_actions": ["specific improvements"]
                }},
                "contextual_relevance": {{
                    "score": 1-10,
                    "analysis": "why this score",
                    "human_vs_ai": "how human input would improve this",
                    "improvement_actions": ["specific improvements"]
                }}
            }},
            "overall_quality_score": "weighted average 1-10",
            "performance_prediction": "expected performance vs pure AI content",
            "traffic_multiplier_estimate": "estimated traffic improvement vs AI baseline",
            "figment_performance_category": "Poor/Fair/Good/Excellent based on human input quality",
            "critical_improvements": ["top 3 changes needed for better performance"],
            "human_enhancement_value": "ROI of adding human input to this content"
        }}
        """
        
        response = self.llm.generate_structured(prompt)
        try:
            return json.loads(response)
        except:
            return self._generate_fallback_quality_score(content, human_inputs)
    
    def _generate_fallback_quality_score(self, content, human_inputs):
        # Base score depends on human input availability
        base_score = 7 if human_inputs else 4
        
        return {
            "quality_scores": {
                "authenticity": {"score": base_score, "analysis": "Based on human input availability"},
                "emotional_connection": {"score": base_score, "analysis": "Depends on human touch"},
                "industry_insight": {"score": base_score, "analysis": "Requires expert knowledge"},
                "accuracy": {"score": base_score + 1, "analysis": "Can be fact-checked"},
                "originality": {"score": base_score, "analysis": "Human creativity advantage"},
                "contextual_relevance": {"score": base_score, "analysis": "Current awareness needed"}
            },
            "overall_quality_score": base_score,
            "performance_prediction": "Above average" if human_inputs else "Below average",
            "traffic_multiplier_estimate": "3-5x improvement" if human_inputs else "Baseline AI performance",
            "figment_performance_category": "Good" if human_inputs else "Fair",
            "critical_improvements": [
                "Add human experience and insights",
                "Include real customer stories", 
                "Verify all factual claims"
            ],
            "human_enhancement_value": "High ROI - human input significantly improves performance"
        }