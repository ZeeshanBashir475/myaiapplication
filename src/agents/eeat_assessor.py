import json
import re
from typing import Dict, List, Any, Optional
from src.utils.llm_client import LLMClient

class EnhancedEEATAssessor:
    def __init__(self):
        self.llm = LLMClient()
        
        # YMYL (Your Money or Your Life) topics requiring higher E-E-A-T standards
        self.ymyl_topics = [
            'finance', 'health', 'medical', 'legal', 'investment', 'insurance',
            'taxes', 'retirement', 'medication', 'surgery', 'diet', 'nutrition',
            'safety', 'parenting', 'relationships', 'government', 'news'
        ]
        
        # E-E-A-T scoring matrix based on Google's Quality Rater Guidelines
        self.eeat_levels = {
            'lowest': {'score': 1, 'description': 'Harmful, fraudulent, or completely lacking credibility'},
            'lacking': {'score': 3, 'description': 'Missing critical E-E-A-T elements for the topic'},
            'moderate': {'score': 5, 'description': 'Adequate E-E-A-T but room for improvement'},
            'high': {'score': 7, 'description': 'Strong E-E-A-T demonstration across all areas'},
            'very_high': {'score': 9, 'description': 'Exceptional E-E-A-T, go-to authoritative source'}
        }
    
    def assess_comprehensive_eeat(self, 
                                 content: str,
                                 topic: str,
                                 business_context: Dict[str, Any],
                                 human_inputs: Dict[str, Any],
                                 reddit_insights: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive E-E-A-T assessment based on Google's Quality Rater Guidelines
        """
        
        print(f"🔍 Performing comprehensive E-E-A-T assessment for: {topic}")
        
        # Determine if this is YMYL content
        is_ymyl = self._is_ymyl_topic(topic, business_context.get('industry', ''))
        
        # Individual E-E-A-T component assessments
        experience_assessment = self._assess_experience(content, topic, business_context, human_inputs, reddit_insights)
        expertise_assessment = self._assess_expertise(content, topic, business_context, human_inputs, is_ymyl)
        authoritativeness_assessment = self._assess_authoritativeness(content, topic, business_context, human_inputs)
        trustworthiness_assessment = self._assess_trustworthiness(content, topic, business_context, human_inputs, is_ymyl)
        
        # Calculate overall E-E-A-T score (Trust is weighted higher as per Google guidelines)
        overall_score = self._calculate_overall_eeat_score(
            experience_assessment['score'],
            expertise_assessment['score'],
            authoritativeness_assessment['score'],
            trustworthiness_assessment['score'],
            is_ymyl
        )
        
        # Determine E-E-A-T level
        eeat_level = self._determine_eeat_level(overall_score)
        
        # Generate improvement recommendations
        improvements = self._generate_improvement_recommendations(
            experience_assessment, expertise_assessment, 
            authoritativeness_assessment, trustworthiness_assessment,
            is_ymyl, topic
        )
        
        # Calculate competitive advantage
        competitive_analysis = self._assess_competitive_advantage(overall_score, is_ymyl)
        
        return {
            'eeat_assessment': {
                'overall_score': round(overall_score, 1),
                'eeat_level': eeat_level,
                'is_ymyl_topic': is_ymyl,
                'components': {
                    'experience': experience_assessment,
                    'expertise': expertise_assessment,
                    'authoritativeness': authoritativeness_assessment,
                    'trustworthiness': trustworthiness_assessment
                }
            },
            'improvement_analysis': improvements,
            'competitive_advantage': competitive_analysis,
            'content_performance_prediction': self._predict_content_performance(overall_score, is_ymyl),
            'human_vs_ai_analysis': self._analyze_human_vs_ai_elements(content, human_inputs, reddit_insights)
        }
    
    def _assess_experience(self, content: str, topic: str, business_context: Dict, 
                          human_inputs: Dict, reddit_insights: Optional[Dict]) -> Dict[str, Any]:
        """Assess Experience component of E-E-A-T"""
        
        experience_indicators = {
            'personal_anecdotes': self._count_personal_indicators(content),
            'first_hand_details': self._count_specific_details(content),
            'real_world_examples': self._count_examples(content),
            'customer_stories': self._has_customer_stories(human_inputs),
            'practical_insights': self._count_practical_insights(content)
        }
        
        # Base experience score
        base_score = 3.0
        
        # Boost for human inputs
        if human_inputs.get('customer_pain_points'):
            base_score += 1.5
        if human_inputs.get('unique_value_prop'):
            base_score += 1.0
        
        # Boost for Reddit insights (real customer voice)
        if reddit_insights and reddit_insights.get('authenticity_markers'):
            base_score += 1.0
        
        # Boost for specific experience indicators
        base_score += min(2.0, sum(experience_indicators.values()) * 0.3)
        
        # Cap at 10
        final_score = min(10.0, base_score)
        
        return {
            'score': round(final_score, 1),
            'indicators': experience_indicators,
            'strengths': self._identify_experience_strengths(experience_indicators, human_inputs),
            'gaps': self._identify_experience_gaps(experience_indicators, human_inputs),
            'improvement_potential': round(10.0 - final_score, 1)
        }
    
    def _assess_expertise(self, content: str, topic: str, business_context: Dict,
                         human_inputs: Dict, is_ymyl: bool) -> Dict[str, Any]:
        """Assess Expertise component of E-E-A-T"""
        
        expertise_indicators = {
            'technical_accuracy': self._assess_technical_depth(content),
            'industry_knowledge': self._assess_industry_knowledge(content, business_context),
            'specialized_terminology': self._count_specialized_terms(content, topic),
            'comprehensive_coverage': self._assess_topic_coverage(content, topic),
            'authoritative_sources': self._count_authoritative_references(content)
        }
        
        # Base expertise score
        base_score = 4.0
        
        # YMYL topics require higher expertise standards
        if is_ymyl:
            base_score = 2.0  # Start lower for YMYL
        
        # Boost for business context
        if business_context.get('industry'):
            base_score += 1.0
        if business_context.get('unique_value_prop'):
            base_score += 1.0
        
        # Boost for expertise indicators
        base_score += min(3.0, sum(expertise_indicators.values()) * 0.4)
        
        # Additional boost for comprehensive human inputs
        if len(human_inputs.get('customer_pain_points', '')) > 100:
            base_score += 0.5
        
        final_score = min(10.0, base_score)
        
        return {
            'score': round(final_score, 1),
            'indicators': expertise_indicators,
            'strengths': self._identify_expertise_strengths(expertise_indicators, business_context),
            'gaps': self._identify_expertise_gaps(expertise_indicators, is_ymyl),
            'improvement_potential': round(10.0 - final_score, 1)
        }
    
    def _assess_authoritativeness(self, content: str, topic: str, business_context: Dict,
                                 human_inputs: Dict) -> Dict[str, Any]:
        """Assess Authoritativeness component of E-E-A-T"""
        
        authority_indicators = {
            'brand_recognition': self._assess_brand_strength(business_context),
            'industry_standing': self._assess_industry_position(business_context),
            'content_depth': self._assess_content_authority(content),
            'unique_insights': self._count_unique_insights(content, human_inputs),
            'thought_leadership': self._assess_thought_leadership(content, business_context)
        }
        
        # Base authority score
        base_score = 3.5
        
        # Boost for established business
        if business_context.get('business_type'):
            base_score += 0.5
        if business_context.get('unique_value_prop'):
            base_score += 1.0
        
        # Boost for authority indicators
        base_score += min(2.5, sum(authority_indicators.values()) * 0.5)
        
        # Boost for comprehensive human inputs showing industry knowledge
        if human_inputs.get('customer_pain_points') and len(human_inputs['customer_pain_points']) > 50:
            base_score += 1.0
        
        final_score = min(10.0, base_score)
        
        return {
            'score': round(final_score, 1),
            'indicators': authority_indicators,
            'strengths': self._identify_authority_strengths(authority_indicators, business_context),
            'gaps': self._identify_authority_gaps(authority_indicators),
            'improvement_potential': round(10.0 - final_score, 1)
        }
    
    def _assess_trustworthiness(self, content: str, topic: str, business_context: Dict,
                               human_inputs: Dict, is_ymyl: bool) -> Dict[str, Any]:
        """Assess Trustworthiness component of E-E-A-T (most important according to Google)"""
        
        trust_indicators = {
            'accuracy_signals': self._assess_accuracy_signals(content),
            'transparency': self._assess_transparency(content, business_context),
            'balanced_perspective': self._assess_balanced_view(content),
            'source_credibility': self._assess_source_credibility(content),
            'safety_reliability': self._assess_safety_reliability(content, is_ymyl)
        }
        
        # Base trust score
        base_score = 4.0
        
        # YMYL topics require higher trust standards
        if is_ymyl:
            base_score = 2.5  # Start lower for YMYL
        
        # Boost for business transparency
        if business_context.get('unique_value_prop'):
            base_score += 1.0
        if business_context.get('business_type'):
            base_score += 0.5
        
        # Boost for trust indicators
        base_score += min(3.0, sum(trust_indicators.values()) * 0.6)
        
        # Boost for honest acknowledgment of limitations (shows trustworthiness)
        if self._has_honest_disclaimers(content):
            base_score += 0.5
        
        final_score = min(10.0, base_score)
        
        return {
            'score': round(final_score, 1),
            'indicators': trust_indicators,
            'strengths': self._identify_trust_strengths(trust_indicators, business_context),
            'gaps': self._identify_trust_gaps(trust_indicators, is_ymyl),
            'improvement_potential': round(10.0 - final_score, 1)
        }
    
    def _calculate_overall_eeat_score(self, experience: float, expertise: float, 
                                     authoritativeness: float, trustworthiness: float, 
                                     is_ymyl: bool) -> float:
        """Calculate overall E-E-A-T score with Trust weighted higher"""
        
        if is_ymyl:
            # YMYL content: Trust is critical, Expertise is essential
            weights = {'trust': 0.4, 'expertise': 0.3, 'experience': 0.15, 'authority': 0.15}
        else:
            # Regular content: More balanced but Trust still weighted higher
            weights = {'trust': 0.35, 'experience': 0.25, 'expertise': 0.2, 'authority': 0.2}
        
        overall = (
            experience * weights['experience'] +
            expertise * weights['expertise'] +
            authoritativeness * weights['authority'] +
            trustworthiness * weights['trust']
        )
        
        return overall
    
    def _determine_eeat_level(self, score: float) -> str:
        """Determine E-E-A-T level based on score"""
        if score >= 8.5:
            return 'very_high'
        elif score >= 7.0:
            return 'high'
        elif score >= 5.0:
            return 'moderate'
        elif score >= 3.0:
            return 'lacking'
        else:
            return 'lowest'
    
    def _is_ymyl_topic(self, topic: str, industry: str) -> bool:
        """Determine if topic/industry is YMYL"""
        topic_lower = topic.lower()
        industry_lower = industry.lower()
        
        return any(ymyl in topic_lower or ymyl in industry_lower for ymyl in self.ymyl_topics)
    
    # Helper methods for detailed assessments
    def _count_personal_indicators(self, content: str) -> float:
        """Count personal experience indicators"""
        indicators = ['I', 'my', 'our', 'we', 'personally', 'in my experience', 'I found', 'we discovered']
        count = sum(1 for indicator in indicators if indicator in content.lower())
        return min(2.0, count * 0.2)
    
    def _count_specific_details(self, content: str) -> float:
        """Count specific details that indicate first-hand experience"""
        detail_patterns = [r'\d+%', r'\$\d+', r'\d+ hours?', r'\d+ days?', r'\d+ months?', 
                          r'exactly', r'specifically', r'precisely']
        count = sum(1 for pattern in detail_patterns if re.search(pattern, content, re.I))
        return min(2.0, count * 0.3)
    
    def _count_examples(self, content: str) -> float:
        """Count real-world examples"""
        example_indicators = ['for example', 'for instance', 'such as', 'like when', 'case study']
        count = sum(1 for indicator in example_indicators if indicator in content.lower())
        return min(1.5, count * 0.3)
    
    def _has_customer_stories(self, human_inputs: Dict) -> float:
        """Check if customer stories are present"""
        pain_points = human_inputs.get('customer_pain_points', '')
        return 1.0 if len(pain_points) > 50 else 0.0
    
    def _count_practical_insights(self, content: str) -> float:
        """Count practical, actionable insights"""
        practical_words = ['how to', 'step by step', 'practical', 'actionable', 'implementation', 'apply']
        count = sum(1 for word in practical_words if word in content.lower())
        return min(1.5, count * 0.2)
    
    def _assess_technical_depth(self, content: str) -> float:
        """Assess technical depth and accuracy"""
        technical_indicators = len(re.findall(r'\b[A-Z]{2,}\b', content))  # Acronyms
        detailed_explanations = content.count('because') + content.count('therefore') + content.count('however')
        return min(2.0, (technical_indicators * 0.1) + (detailed_explanations * 0.2))
    
    def _assess_industry_knowledge(self, content: str, business_context: Dict) -> float:
        """Assess industry-specific knowledge"""
        industry = business_context.get('industry', '').lower()
        if not industry:
            return 0.5
        
        industry_mentioned = 1.0 if industry in content.lower() else 0.0
        business_terms = ['market', 'industry', 'sector', 'business', 'commercial']
        business_context_score = sum(0.2 for term in business_terms if term in content.lower())
        
        return min(2.0, industry_mentioned + business_context_score)
    
    def _count_specialized_terms(self, content: str, topic: str) -> float:
        """Count specialized terminology usage"""
        # This would ideally use a domain-specific dictionary
        words = content.split()
        complex_words = sum(1 for word in words if len(word) > 8)
        return min(1.5, complex_words * 0.01)
    
    def _assess_topic_coverage(self, content: str, topic: str) -> float:
        """Assess comprehensiveness of topic coverage"""
        word_count = len(content.split())
        coverage_score = min(2.0, word_count / 500)  # 500+ words gets full score
        
        # Boost for comprehensive coverage indicators
        comprehensive_words = ['comprehensive', 'complete', 'thorough', 'detailed', 'in-depth']
        comprehensiveness_boost = sum(0.2 for word in comprehensive_words if word in content.lower())
        
        return min(2.0, coverage_score + comprehensiveness_boost)
    
    def _count_authoritative_references(self, content: str) -> float:
        """Count references to authoritative sources"""
        authority_indicators = ['research shows', 'studies indicate', 'according to', 'data shows', 'statistics']
        count = sum(1 for indicator in authority_indicators if indicator in content.lower())
        return min(1.5, count * 0.3)
    
    def _assess_brand_strength(self, business_context: Dict) -> float:
        """Assess brand strength from business context"""
        strength = 0.0
        if business_context.get('unique_value_prop'):
            strength += 1.0
        if business_context.get('business_type'):
            strength += 0.5
        if business_context.get('industry'):
            strength += 0.5
        return min(2.0, strength)
    
    def _assess_industry_position(self, business_context: Dict) -> float:
        """Assess industry position and standing"""
        unique_value = business_context.get('unique_value_prop', '')
        return min(1.5, len(unique_value) / 100) if unique_value else 0.0
    
    def _assess_content_authority(self, content: str) -> float:
        """Assess content's authoritative tone and depth"""
        authority_words = ['proven', 'established', 'recognized', 'leading', 'expert', 'professional']
        count = sum(1 for word in authority_words if word in content.lower())
        return min(1.5, count * 0.25)
    
    def _count_unique_insights(self, content: str, human_inputs: Dict) -> float:
        """Count unique insights that show original thought"""
        unique_indicators = ['unique', 'original', 'innovative', 'breakthrough', 'exclusive']
        content_score = sum(0.2 for indicator in unique_indicators if indicator in content.lower())
        
        # Boost for substantial customer insights
        customer_insights = len(human_inputs.get('customer_pain_points', '')) / 200
        
        return min(2.0, content_score + customer_insights)
    
    def _assess_thought_leadership(self, content: str, business_context: Dict) -> float:
        """Assess thought leadership elements"""
        leadership_indicators = ['future', 'trend', 'prediction', 'forecast', 'innovation', 'evolution']
        count = sum(1 for indicator in leadership_indicators if indicator in content.lower())
        
        # Boost for unique value proposition
        uvp_boost = 0.5 if business_context.get('unique_value_prop') else 0.0
        
        return min(1.5, (count * 0.2) + uvp_boost)
    
    def _assess_accuracy_signals(self, content: str) -> float:
        """Assess signals that indicate accuracy"""
        accuracy_indicators = ['accurate', 'verified', 'confirmed', 'validated', 'tested', 'proven']
        count = sum(1 for indicator in accuracy_indicators if indicator in content.lower())
        return min(2.0, count * 0.3)
    
    def _assess_transparency(self, content: str, business_context: Dict) -> float:
        """Assess transparency and openness"""
        transparency_score = 0.0
        
        # Check for honest language
        honest_words = ['honest', 'transparent', 'openly', 'frankly', 'admittedly']
        transparency_score += sum(0.2 for word in honest_words if word in content.lower())
        
        # Boost for business context transparency
        if business_context.get('unique_value_prop'):
            transparency_score += 0.5
        
        return min(2.0, transparency_score)
    
    def _assess_balanced_view(self, content: str) -> float:
        """Assess balanced perspective"""
        balance_indicators = ['however', 'although', 'while', 'despite', 'on the other hand', 'pros and cons']
        count = sum(1 for indicator in balance_indicators if indicator in content.lower())
        return min(1.5, count * 0.25)
    
    def _assess_source_credibility(self, content: str) -> float:
        """Assess credibility of sources mentioned"""
        credible_sources = ['research', 'study', 'university', 'institute', 'official', 'government']
        count = sum(1 for source in credible_sources if source in content.lower())
        return min(1.5, count * 0.25)
    
    def _assess_safety_reliability(self, content: str, is_ymyl: bool) -> float:
        """Assess safety and reliability, especially for YMYL content"""
        safety_words = ['safe', 'reliable', 'trusted', 'secure', 'certified', 'approved']
        count = sum(1 for word in safety_words if word in content.lower())
        base_score = min(1.5, count * 0.3)
        
        # Higher standards for YMYL
        return base_score * 0.7 if is_ymyl and base_score < 1.0 else base_score
    
    def _has_honest_disclaimers(self, content: str) -> bool:
        """Check for honest disclaimers and limitations"""
        disclaimer_words = ['disclaimer', 'limitation', 'not guaranteed', 'may vary', 'consult']
        return any(word in content.lower() for word in disclaimer_words)
    
    def _generate_improvement_recommendations(self, experience_assessment: Dict, expertise_assessment: Dict,
                                            authoritativeness_assessment: Dict, trustworthiness_assessment: Dict,
                                            is_ymyl: bool, topic: str) -> Dict[str, Any]:
        """Generate specific improvement recommendations"""
        
        recommendations = {
            'immediate_actions': [],
            'content_enhancements': [],
            'strategic_improvements': [],
            'priority_level': 'medium'
        }
        
        # Experience recommendations
        if experience_assessment['score'] < 6.0:
            recommendations['immediate_actions'].extend([
                'Add personal experience stories and anecdotes',
                'Include specific details that only someone with experience would know',
                'Share real customer examples and case studies'
            ])
        
        # Expertise recommendations
        if expertise_assessment['score'] < 6.0:
            recommendations['content_enhancements'].extend([
                'Increase technical depth and accuracy',
                'Add industry-specific terminology appropriately',
                'Reference authoritative sources and research'
            ])
        
        # Authoritativeness recommendations
        if authoritativeness_assessment['score'] < 6.0:
            recommendations['strategic_improvements'].extend([
                'Build topical authority with comprehensive content coverage',
                'Develop unique insights and original perspectives',
                'Establish thought leadership in your industry'
            ])
        
        # Trustworthiness recommendations (most important)
        if trustworthiness_assessment['score'] < 7.0:
            recommendations['immediate_actions'].extend([
                'Add transparency about limitations and potential biases',
                'Include credible sources and references',
                'Provide balanced perspectives on controversial topics'
            ])
            if is_ymyl:
                recommendations['immediate_actions'].extend([
                    'Add appropriate disclaimers for YMYL content',
                    'Ensure all claims are verifiable and accurate',
                    'Consider professional review of content'
                ])
        
        # Determine priority level
        lowest_score = min(
            experience_assessment['score'],
            expertise_assessment['score'],
            authoritativeness_assessment['score'],
            trustworthiness_assessment['score']
        )
        
        if lowest_score < 4.0:
            recommendations['priority_level'] = 'critical'
        elif lowest_score < 6.0:
            recommendations['priority_level'] = 'high'
        else:
            recommendations['priority_level'] = 'medium'
        
        return recommendations
    
    def _assess_competitive_advantage(self, overall_score: float, is_ymyl: bool) -> Dict[str, Any]:
        """Assess competitive advantage based on E-E-A-T score"""
        
        # Benchmark scores (typical AI-generated content)
        ai_benchmark = 4.5 if is_ymyl else 5.5
        
        advantage_multiplier = max(1.0, overall_score / ai_benchmark)
        
        performance_categories = {
            'traffic_potential': f"{round(advantage_multiplier * 100)}% better than AI-only content",
            'engagement_boost': f"{round((advantage_multiplier - 1) * 200)}% higher engagement expected",
            'conversion_improvement': f"{round((advantage_multiplier - 1) * 150)}% better conversion rates",
            'search_ranking_boost': f"{round((advantage_multiplier - 1) * 100)}% ranking improvement potential"
        }
        
        competitive_level = 'exceptional' if overall_score > 8.0 else 'strong' if overall_score > 6.5 else 'moderate' if overall_score > 5.0 else 'weak'
        
        return {
            'competitive_level': competitive_level,
            'advantage_multiplier': round(advantage_multiplier, 2),
            'performance_predictions': performance_categories,
            'market_position': self._determine_market_position(overall_score, is_ymyl)
        }
    
    def _determine_market_position(self, score: float, is_ymyl: bool) -> str:
        """Determine market position based on E-E-A-T score"""
        if is_ymyl:
            if score > 8.0:
                return 'Industry leader - trusted authoritative source'
            elif score > 6.5:
                return 'Strong competitor - reliable and credible'
            elif score > 5.0:
                return 'Market participant - room for authority building'
            else:
                return 'Needs significant improvement for YMYL topics'
        else:
            if score > 8.0:
                return 'Market leader - go-to resource'
            elif score > 6.5:
                return 'Strong brand - trusted by audience'
            elif score > 5.0:
                return 'Competitive player - good foundation'
            else:
                return 'Opportunity for differentiation'
    
    def _predict_content_performance(self, overall_score: float, is_ymyl: bool) -> Dict[str, Any]:
        """Predict content performance based on E-E-A-T score"""
        
        # Performance metrics based on E-E-A-T score
        base_performance = {
            'search_visibility': min(100, overall_score * 10),
            'user_engagement': min(100, overall_score * 11),
            'conversion_potential': min(100, overall_score * 9),
            'social_sharing': min(100, overall_score * 8),
            'brand_trust': min(100, overall_score * 12)
        }
        
        # YMYL content has different performance patterns
        if is_ymyl:
            base_performance['search_visibility'] *= 0.8  # Harder to rank
            base_performance['brand_trust'] *= 1.2  # More important
        
        performance_tier = 'excellent' if overall_score > 8.0 else 'good' if overall_score > 6.5 else 'fair' if overall_score > 5.0 else 'poor'
        
        return {
            'performance_tier': performance_tier,
            'metrics': {k: round(v, 1) for k, v in base_performance.items()},
            'expected_outcomes': self._generate_performance_outcomes(overall_score, is_ymyl),
            'timeline_to_results': self._estimate_results_timeline(overall_score)
        }
    
    def _generate_performance_outcomes(self, score: float, is_ymyl: bool) -> List[str]:
        """Generate expected performance outcomes"""
        outcomes = []
        
        if score > 8.0:
            outcomes.extend([
                'High search engine visibility',
                'Strong user engagement and trust',
                'Excellent conversion rates',
                'Natural backlink attraction',
                'Brand authority establishment'
            ])
        elif score > 6.5:
            outcomes.extend([
                'Good search rankings',
                'Positive user reception',
                'Above-average conversion rates',
                'Growing brand recognition'
            ])
        elif score > 5.0:
            outcomes.extend([
                'Moderate search visibility',
                'Decent user engagement',
                'Standard conversion performance'
            ])
        else:
            outcomes.extend([
                'Limited search visibility',
                'Basic user engagement',
                'Below-average performance'
            ])
        
        if is_ymyl and score < 7.0:
            outcomes.append('May struggle with YMYL content standards')
        
        return outcomes
    
    def _estimate_results_timeline(self, score: float) -> str:
        """Estimate timeline to see results"""
        if score > 8.0:
            return '2-4 weeks for initial results, 2-3 months for full impact'
        elif score > 6.5:
            return '4-6 weeks for initial results, 3-4 months for full impact'
        elif score > 5.0:
            return '6-8 weeks for initial results, 4-6 months for full impact'
        else:
            return '8-12 weeks for initial results, 6+ months for meaningful impact'
    
    def _analyze_human_vs_ai_elements(self, content: str, human_inputs: Dict, 
                                     reddit_insights: Optional[Dict]) -> Dict[str, Any]:
        """Analyze human vs AI elements in the content"""
        
        human_elements = {
            'customer_insights': bool(human_inputs.get('customer_pain_points')),
            'business_context': bool(human_inputs.get('unique_value_prop')),
            'real_experience': self._detect_experience_markers(content),
            'authentic_voice': self._detect_authentic_voice(content, reddit_insights),
            'industry_knowledge': bool(human_inputs.get('industry'))
        }
        
        human_score = sum(human_elements.values()) / len(human_elements) * 10
        
        ai_limitations = [
            'Cannot provide genuine personal experience',
            'Lacks real customer interaction insights',
            'May hallucinate facts without verification',
            'Cannot build authentic authority',
            'Limited to training data patterns'
        ]
        
        human_advantages = [
            'Authentic personal experience and stories',
            'Real customer pain point understanding',
            'Industry-specific insider knowledge',
            'Genuine problem-solving perspective',
            'Ability to build trust through transparency'
        ]
        
        return {
            'human_elements_score': round(human_score, 1),
            'human_elements_present': human_elements,
            'ai_limitations': ai_limitations,
            'human_advantages': human_advantages,
            'improvement_opportunity': round(10 - human_score, 1),
            'authenticity_level': self._determine_authenticity_level(human_score)
        }
    
    def _detect_experience_markers(self, content: str) -> bool:
        """Detect markers of genuine experience in content"""
        experience_markers = ['I', 'we', 'our experience', 'in practice', 'personally', 'first-hand']
        return any(marker in content.lower() for marker in experience_markers)
    
    def _detect_authentic_voice(self, content: str, reddit_insights: Optional[Dict]) -> bool:
        """Detect authentic voice elements"""
        if reddit_insights and reddit_insights.get('authenticity_markers'):
            return True
        
        authentic_indicators = ['honestly', 'frankly', 'in my opinion', 'I believe', 'personally']
        return any(indicator in content.lower() for indicator in authentic_indicators)
    
    def _determine_authenticity_level(self, human_score: float) -> str:
        """Determine level of authenticity"""
        if human_score > 8.0:
            return 'highly_authentic'
        elif human_score > 6.0:
            return 'moderately_authentic'
        elif human_score > 4.0:
            return 'somewhat_authentic'
        else:
            return 'generic_ai_like'
    
    # Identification methods for strengths and gaps
    def _identify_experience_strengths(self, indicators: Dict, human_inputs: Dict) -> List[str]:
        """Identify experience strengths"""
        strengths = []
        if indicators.get('personal_anecdotes', 0) > 1:
            strengths.append('Strong personal narrative')
        if indicators.get('customer_stories', 0) > 0:
            strengths.append('Real customer insights')
        if indicators.get('practical_insights', 0) > 1:
            strengths.append('Practical, actionable advice')
        return strengths or ['Basic experience foundation']
    
    def _identify_experience_gaps(self, indicators: Dict, human_inputs: Dict) -> List[str]:
        """Identify experience gaps"""
        gaps = []
        if indicators.get('personal_anecdotes', 0) < 1:
            gaps.append('Need more personal stories and anecdotes')
        if indicators.get('first_hand_details', 0) < 1:
            gaps.append('Add specific details from experience')
        if indicators.get('customer_stories', 0) == 0:
            gaps.append('Include customer examples and case studies')
        return gaps or ['Experience well-demonstrated']
    
    def _identify_expertise_strengths(self, indicators: Dict, business_context: Dict) -> List[str]:
        """Identify expertise strengths"""
        strengths = []
        if indicators.get('technical_accuracy', 0) > 1:
            strengths.append('Strong technical foundation')
        if indicators.get('industry_knowledge', 0) > 1:
            strengths.append('Clear industry expertise')
        if indicators.get('comprehensive_coverage', 0) > 1:
            strengths.append('Comprehensive topic coverage')
        return strengths or ['Basic expertise demonstrated']
    
    def _identify_expertise_gaps(self, indicators: Dict, is_ymyl: bool) -> List[str]:
        """Identify expertise gaps"""
        gaps = []
        if indicators.get('technical_accuracy', 0) < 1:
            gaps.append('Increase technical depth and accuracy')
        if indicators.get('authoritative_sources', 0) < 1:
            gaps.append('Add more authoritative references')
        if is_ymyl and sum(indicators.values()) < 3:
            gaps.append('YMYL content requires higher expertise standards')
        return gaps or ['Expertise well-established']
    
    def _identify_authority_strengths(self, indicators: Dict, business_context: Dict) -> List[str]:
        """Identify authoritativeness strengths"""
        strengths = []
        if indicators.get('brand_recognition', 0) > 1:
            strengths.append('Strong brand foundation')
        if indicators.get('unique_insights', 0) > 1:
            strengths.append('Original thinking and insights')
        if indicators.get('thought_leadership', 0) > 1:
            strengths.append('Thought leadership elements')
        return strengths or ['Authority foundation present']
    
    def _identify_authority_gaps(self, indicators: Dict) -> List[str]:
        """Identify authoritativeness gaps"""
        gaps = []
        if indicators.get('brand_recognition', 0) < 1:
            gaps.append('Build stronger brand recognition')
        if indicators.get('unique_insights', 0) < 1:
            gaps.append('Add more unique insights and perspectives')
        if indicators.get('content_depth', 0) < 1:
            gaps.append('Increase content authority and depth')
        return gaps or ['Authority well-established']
    
    def _identify_trust_strengths(self, indicators: Dict, business_context: Dict) -> List[str]:
        """Identify trustworthiness strengths"""
        strengths = []
        if indicators.get('accuracy_signals', 0) > 1:
            strengths.append('Strong accuracy indicators')
        if indicators.get('transparency', 0) > 1:
            strengths.append('Good transparency and openness')
        if indicators.get('balanced_perspective', 0) > 1:
            strengths.append('Balanced and fair perspective')
        return strengths or ['Basic trust foundation']
    
    def _identify_trust_gaps(self, indicators: Dict, is_ymyl: bool) -> List[str]:
        """Identify trustworthiness gaps"""
        gaps = []
        if indicators.get('accuracy_signals', 0) < 1:
            gaps.append('Add more accuracy and verification signals')
        if indicators.get('source_credibility', 0) < 1:
            gaps.append('Include more credible sources')
        if is_ymyl and indicators.get('safety_reliability', 0) < 1.5:
            gaps.append('YMYL content needs stronger safety and reliability signals')
        return gaps or ['Trust well-established']
