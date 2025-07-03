"""
Content Type Classifier - Syntax Error Free Version
Classifies content types based on topic, audience, and intent
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ContentTypeClassifier:
    """
    Enhanced content type classifier with robust error handling
    """
    
    def __init__(self):
        """Initialize the classifier with predefined rules and patterns"""
        self.content_types = {
            'blog_post': {
                'description': 'Informational blog post',
                'keywords': ['how to', 'guide', 'tips', 'tutorial', 'learn', 'understand'],
                'min_length': 800,
                'max_length': 3000,
                'structure': 'introduction + sections + conclusion',
                'tone': 'informative, engaging'
            },
            'comprehensive_guide': {
                'description': 'In-depth comprehensive guide',
                'keywords': ['complete guide', 'ultimate', 'comprehensive', 'everything', 'master'],
                'min_length': 2000,
                'max_length': 8000,
                'structure': 'detailed sections + examples + resources',
                'tone': 'authoritative, thorough'
            },
            'listicle': {
                'description': 'List-based article',
                'keywords': ['best', 'top', 'list', 'ways', 'methods', 'reasons'],
                'min_length': 1000,
                'max_length': 2500,
                'structure': 'numbered/bulleted list + explanations',
                'tone': 'scannable, practical'
            },
            'comparison': {
                'description': 'Comparison article',
                'keywords': ['vs', 'versus', 'compare', 'comparison', 'difference', 'which'],
                'min_length': 1200,
                'max_length': 3000,
                'structure': 'side-by-side analysis + conclusion',
                'tone': 'analytical, unbiased'
            },
            'case_study': {
                'description': 'Case study or success story',
                'keywords': ['case study', 'success story', 'example', 'real world', 'results'],
                'min_length': 1500,
                'max_length': 4000,
                'structure': 'problem + solution + results',
                'tone': 'narrative, data-driven'
            },
            'faq': {
                'description': 'Frequently asked questions',
                'keywords': ['faq', 'questions', 'answers', 'common', 'frequently asked'],
                'min_length': 800,
                'max_length': 2000,
                'structure': 'question + answer format',
                'tone': 'direct, helpful'
            },
            'review': {
                'description': 'Product or service review',
                'keywords': ['review', 'rating', 'pros', 'cons', 'opinion', 'evaluation'],
                'min_length': 1000,
                'max_length': 2500,
                'structure': 'overview + detailed analysis + verdict',
                'tone': 'balanced, honest'
            },
            'news_article': {
                'description': 'News or announcement',
                'keywords': ['news', 'announcement', 'breaking', 'update', 'latest'],
                'min_length': 400,
                'max_length': 1200,
                'structure': 'headline + lead + body + conclusion',
                'tone': 'factual, timely'
            }
        }
        
        self.audience_patterns = {
            'beginner': ['beginner', 'new', 'start', 'basic', 'introduction', 'getting started'],
            'intermediate': ['intermediate', 'moderate', 'some experience', 'next level'],
            'advanced': ['advanced', 'expert', 'professional', 'experienced', 'master'],
            'technical': ['technical', 'developer', 'engineer', 'API', 'code', 'programming'],
            'business': ['business', 'company', 'enterprise', 'professional', 'corporate'],
            'consumer': ['consumer', 'personal', 'individual', 'home', 'family']
        }
        
        self.intent_patterns = {
            'informational': ['how', 'what', 'why', 'when', 'where', 'learn', 'understand'],
            'transactional': ['buy', 'purchase', 'order', 'get', 'download', 'signup'],
            'navigational': ['login', 'contact', 'about', 'home', 'site', 'find'],
            'commercial': ['best', 'top', 'review', 'compare', 'price', 'cost', 'deal']
        }
        
        logger.info("✅ ContentTypeClassifier initialized successfully")
    
    def classify_content_type(self, 
                            topic: str, 
                            target_audience: str = "", 
                            business_context: Dict[str, Any] = None,
                            reddit_insights: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classify the most appropriate content type for given parameters
        
        Args:
            topic: The main topic/subject
            target_audience: Target audience description
            business_context: Business context information
            reddit_insights: Research insights from Reddit
            
        Returns:
            Dictionary with classification results
        """
        try:
            # Ensure inputs are strings
            topic = str(topic).lower()
            target_audience = str(target_audience).lower()
            
            # Initialize scoring
            type_scores = {}
            
            # Score each content type
            for content_type, details in self.content_types.items():
                score = self._calculate_type_score(topic, content_type, details, target_audience)
                type_scores[content_type] = score
            
            # Get the best match
            best_type = max(type_scores, key=type_scores.get)
            confidence = type_scores[best_type]
            
            # Determine audience level
            audience_level = self._determine_audience_level(target_audience, topic)
            
            # Determine primary intent
            primary_intent = self._determine_intent(topic, business_context)
            
            # Get content recommendations
            recommendations = self._get_content_recommendations(
                best_type, audience_level, primary_intent, reddit_insights
            )
            
            result = {
                'primary_content_type': best_type,
                'confidence_score': round(confidence, 2),
                'type_description': self.content_types[best_type]['description'],
                'audience_level': audience_level,
                'primary_intent': primary_intent,
                'recommended_length': {
                    'min_words': self.content_types[best_type]['min_length'],
                    'max_words': self.content_types[best_type]['max_length']
                },
                'content_structure': self.content_types[best_type]['structure'],
                'recommended_tone': self.content_types[best_type]['tone'],
                'alternative_types': self._get_alternative_types(type_scores, best_type),
                'content_recommendations': recommendations,
                'classification_timestamp': datetime.now().isoformat(),
                'all_scores': type_scores
            }
            
            logger.info(f"✅ Content classified as: {best_type} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in classify_content_type: {e}")
            return self._fallback_classification(topic, target_audience)
    
    def _calculate_type_score(self, topic: str, content_type: str, details: Dict, audience: str) -> float:
        """Calculate score for a specific content type"""
        try:
            score = 0.0
            
            # Keyword matching
            for keyword in details['keywords']:
                if keyword in topic:
                    score += 1.0
                if keyword in audience:
                    score += 0.5
            
            # Length-based scoring
            if 'comprehensive' in topic or 'complete' in topic or 'ultimate' in topic:
                if content_type == 'comprehensive_guide':
                    score += 2.0
                elif content_type == 'blog_post':
                    score += 1.0
            
            # List-based content detection
            if any(word in topic for word in ['best', 'top', 'list', 'ways']):
                if content_type == 'listicle':
                    score += 2.0
            
            # Comparison content detection
            if any(word in topic for word in ['vs', 'versus', 'compare', 'difference']):
                if content_type == 'comparison':
                    score += 2.0
            
            # FAQ detection
            if any(word in topic for word in ['questions', 'faq', 'ask', 'answer']):
                if content_type == 'faq':
                    score += 2.0
            
            # Review detection
            if any(word in topic for word in ['review', 'rating', 'opinion', 'evaluation']):
                if content_type == 'review':
                    score += 2.0
            
            return score
            
        except Exception as e:
            logger.error(f"❌ Error calculating score for {content_type}: {e}")
            return 0.0
    
    def _determine_audience_level(self, target_audience: str, topic: str) -> str:
        """Determine the audience expertise level"""
        try:
            scores = {}
            
            for level, patterns in self.audience_patterns.items():
                score = 0
                for pattern in patterns:
                    if pattern in target_audience:
                        score += 1
                    if pattern in topic:
                        score += 0.5
                scores[level] = score
            
            # Return the highest scoring level, or 'intermediate' as default
            if max(scores.values()) > 0:
                return max(scores, key=scores.get)
            return 'intermediate'
            
        except Exception as e:
            logger.error(f"❌ Error determining audience level: {e}")
            return 'intermediate'
    
    def _determine_intent(self, topic: str, business_context: Dict[str, Any] = None) -> str:
        """Determine the primary search intent"""
        try:
            scores = {}
            
            for intent, patterns in self.intent_patterns.items():
                score = 0
                for pattern in patterns:
                    if pattern in topic:
                        score += 1
                scores[intent] = score
            
            # Consider business context
            if business_context:
                if business_context.get('industry') in ['ecommerce', 'retail', 'sales']:
                    scores['commercial'] = scores.get('commercial', 0) + 1
                if business_context.get('goal') == 'lead_generation':
                    scores['commercial'] = scores.get('commercial', 0) + 1
            
            # Return the highest scoring intent, or 'informational' as default
            if max(scores.values()) > 0:
                return max(scores, key=scores.get)
            return 'informational'
            
        except Exception as e:
            logger.error(f"❌ Error determining intent: {e}")
            return 'informational'
    
    def _get_alternative_types(self, type_scores: Dict[str, float], primary_type: str) -> List[Dict[str, Any]]:
        """Get alternative content types with scores"""
        try:
            # Remove primary type and get top 3 alternatives
            alternatives = {k: v for k, v in type_scores.items() if k != primary_type}
            sorted_alternatives = sorted(alternatives.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return [
                {
                    'type': alt_type,
                    'score': round(score, 2),
                    'description': self.content_types[alt_type]['description']
                }
                for alt_type, score in sorted_alternatives if score > 0
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting alternative types: {e}")
            return []
    
    def _get_content_recommendations(self, 
                                  content_type: str, 
                                  audience_level: str, 
                                  intent: str,
                                  reddit_insights: Dict[str, Any] = None) -> List[str]:
        """Get specific content recommendations"""
        try:
            recommendations = []
            
            # Base recommendations by content type
            if content_type == 'comprehensive_guide':
                recommendations.extend([
                    "Include detailed table of contents",
                    "Add step-by-step instructions",
                    "Include practical examples and case studies",
                    "Provide downloadable resources or templates"
                ])
            elif content_type == 'blog_post':
                recommendations.extend([
                    "Start with engaging hook",
                    "Use subheadings for easy scanning",
                    "Include actionable tips",
                    "End with clear call-to-action"
                ])
            elif content_type == 'listicle':
                recommendations.extend([
                    "Use numbered or bulleted format",
                    "Include brief explanations for each point",
                    "Add visuals or icons for each item",
                    "Summarize key takeaways at the end"
                ])
            
            # Audience-specific recommendations
            if audience_level == 'beginner':
                recommendations.extend([
                    "Define technical terms and jargon",
                    "Include basic background information",
                    "Use simple, clear language",
                    "Provide step-by-step guidance"
                ])
            elif audience_level == 'advanced':
                recommendations.extend([
                    "Include advanced techniques and strategies",
                    "Reference industry best practices",
                    "Provide technical details and specifications",
                    "Include expert insights and opinions"
                ])
            
            # Intent-based recommendations
            if intent == 'transactional':
                recommendations.extend([
                    "Include clear pricing information",
                    "Add comparison tables",
                    "Include customer testimonials",
                    "Provide clear purchase/signup process"
                ])
            elif intent == 'informational':
                recommendations.extend([
                    "Focus on educational value",
                    "Include comprehensive explanations",
                    "Add relevant examples and analogies",
                    "Provide additional resources for learning"
                ])
            
            # Reddit insights integration
            if reddit_insights:
                customer_voice = reddit_insights.get('customer_voice', {})
                if customer_voice.get('common_language'):
                    recommendations.append(f"Use customer language: {', '.join(customer_voice['common_language'][:3])}")
                if customer_voice.get('pain_points'):
                    recommendations.append("Address common pain points identified in research")
            
            return recommendations[:8]  # Limit to 8 recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting content recommendations: {e}")
            return ["Focus on providing value to your target audience"]
    
    def _fallback_classification(self, topic: str, target_audience: str) -> Dict[str, Any]:
        """Fallback classification when main logic fails"""
        logger.warning("🔄 Using fallback classification")
        
        return {
            'primary_content_type': 'blog_post',
            'confidence_score': 0.75,
            'type_description': 'Informational blog post',
            'audience_level': 'intermediate',
            'primary_intent': 'informational',
            'recommended_length': {
                'min_words': 800,
                'max_words': 2000
            },
            'content_structure': 'introduction + main sections + conclusion',
            'recommended_tone': 'informative, engaging',
            'alternative_types': [
                {'type': 'comprehensive_guide', 'score': 0.65, 'description': 'In-depth comprehensive guide'},
                {'type': 'listicle', 'score': 0.55, 'description': 'List-based article'}
            ],
            'content_recommendations': [
                "Create engaging introduction",
                "Use clear subheadings",
                "Include practical examples",
                "Add actionable takeaways",
                "End with clear next steps"
            ],
            'classification_timestamp': datetime.now().isoformat(),
            'fallback_used': True
        }
    
    def get_content_type_info(self, content_type: str) -> Dict[str, Any]:
        """Get detailed information about a specific content type"""
        try:
            if content_type in self.content_types:
                return self.content_types[content_type]
            else:
                logger.warning(f"⚠️ Unknown content type: {content_type}")
                return self.content_types['blog_post']  # Default fallback
                
        except Exception as e:
            logger.error(f"❌ Error getting content type info: {e}")
            return self.content_types['blog_post']
    
    def get_all_content_types(self) -> List[str]:
        """Get list of all available content types"""
        return list(self.content_types.keys())


# Example usage and testing
if __name__ == "__main__":
    # Test the classifier
    classifier = ContentTypeClassifier()
    
    # Test cases
    test_cases = [
        {
            'topic': 'how to start a blog',
            'audience': 'beginners who want to learn blogging',
            'expected': 'blog_post'
        },
        {
            'topic': 'ultimate guide to SEO',
            'audience': 'marketing professionals',
            'expected': 'comprehensive_guide'
        },
        {
            'topic': 'top 10 best WordPress themes',
            'audience': 'website owners',
            'expected': 'listicle'
        },
        {
            'topic': 'WordPress vs Squarespace comparison',
            'audience': 'business owners',
            'expected': 'comparison'
        }
    ]
    
    print("🧪 Testing Content Type Classifier")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['topic']}")
        result = classifier.classify_content_type(
            topic=test['topic'],
            target_audience=test['audience']
        )
        print(f"  Classified as: {result['primary_content_type']}")
        print(f"  Confidence: {result['confidence_score']}")
        print(f"  Expected: {test['expected']}")
        print(f"  ✅ {'PASS' if result['primary_content_type'] == test['expected'] else 'DIFFERENT'}")
    
    print("\n✅ All tests completed!")
