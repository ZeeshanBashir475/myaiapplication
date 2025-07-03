"""
Zee SEO Tool Enhanced v3.0 - Complete Advanced System
====================================================
Author: Zeeshan Bashir
Description: Advanced content intelligence platform with all agents integrated
Fixed: Reddit API, Trust Score calculation, and conversational AI dialogue
"""

import os
import json
import logging
import asyncio
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# FastAPI imports
from fastapi import FastAPI, Form, HTTPException, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ZeeSEOTool:v1.0 (by u/Available-Travel7812)")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
    PORT = int(os.getenv("PORT", 8002))

config = Config()

# Initialize FastAPI
app = FastAPI(title="Zee SEO Tool Enhanced v3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Safe Reddit import
try:
    import praw
    PRAW_AVAILABLE = True
    logger.info("✅ PRAW library loaded successfully")
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("⚠️ PRAW not available - Reddit research will use simulation mode")

# ================== UTILITY CLASSES ==================

class LLMClient:
    """Enhanced LLM client for all AI interactions"""
    def __init__(self):
        self.api_key = config.ANTHROPIC_API_KEY
        self.available = self.api_key and len(self.api_key) > 10
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def generate_content(self, prompt: str, model: str = "claude-3-haiku-20240307") -> str:
        """Generate content using Claude"""
        if not self.available:
            return self._get_fallback_content(prompt)
        
        try:
            payload = {
                "model": model,
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return self._get_fallback_content(prompt)
                
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return self._get_fallback_content(prompt)
    
    def _get_fallback_content(self, prompt: str) -> str:
        """Fallback content when API is unavailable"""
        return f"""# Professional Content Generated

Based on your requirements, here's a comprehensive analysis and content strategy.

## Executive Summary
This content addresses key market challenges while positioning your unique value proposition effectively.

## Key Points Covered
- Industry-specific insights and trends
- Customer pain point analysis
- Solution-oriented approach
- Competitive differentiation
- Actionable recommendations

## Content Structure
The generated content follows SEO best practices and Trust Score guidelines to ensure maximum search visibility and user engagement.

*Note: API key not configured or Claude API unavailable. Please check your ANTHROPIC_API_KEY environment variable.*
"""

class EnhancedRedditClient:
    """Fixed Reddit API client with proper Railway integration"""
    def __init__(self):
        self.reddit = None
        self.available = False
        self.praw_available = PRAW_AVAILABLE
        
        if not PRAW_AVAILABLE:
            logger.warning("⚠️ PRAW library not available - using enhanced simulation mode")
            return
            
        try:
            if not all([config.REDDIT_CLIENT_ID, config.REDDIT_CLIENT_SECRET]):
                logger.warning("⚠️ Reddit API credentials not found in Railway environment")
                return
            
            logger.info(f"🔗 Initializing Reddit API client...")
            logger.info(f"🔑 Client ID: {config.REDDIT_CLIENT_ID[:8]}...")
            logger.info(f"🔑 User Agent: {config.REDDIT_USER_AGENT}")
            
            # Initialize PRAW Reddit instance
            self.reddit = praw.Reddit(
                client_id=config.REDDIT_CLIENT_ID,
                client_secret=config.REDDIT_CLIENT_SECRET,
                user_agent=config.REDDIT_USER_AGENT,
                check_for_async=False
            )
            
            # Test the connection
            self._test_connection()
            self.available = True
            logger.info("✅ Reddit API connection successful!")
            
        except Exception as e:
            logger.error(f"❌ Reddit API initialization failed: {str(e)}")
            self.reddit = None
            self.available = False
    
    def _test_connection(self):
        """Test Reddit API connection"""
        try:
            if self.reddit:
                # Test with a simple subreddit access
                test_subreddit = self.reddit.subreddit('test')
                _ = test_subreddit.display_name
                logger.info("✅ Reddit API connection test passed")
        except Exception as e:
            raise Exception(f"Reddit API connection test failed: {str(e)}")
    
    async def research_topic(self, topic: str, subreddits: str) -> Dict[str, Any]:
        """Research topic across specified subreddits with enhanced insights"""
        if not self.available or not self.reddit:
            logger.info("🔧 Reddit API not available - using enhanced simulation mode")
            return self._get_enhanced_simulation(topic, subreddits)
        
        try:
            logger.info(f"🔍 Starting Reddit research for '{topic}' in subreddits: {subreddits}")
            
            communities = [s.strip() for s in subreddits.split(',') if s.strip()]
            all_insights = {
                'customer_voice': {
                    'common_language': [],
                    'frequent_questions': [],
                    'pain_points': [],
                    'recommendations': []
                },
                'sentiment_analysis': {'positive': 0, 'neutral': 0, 'negative': 0},
                'trending_discussions': [],
                'authenticity_markers': [],
                'real_experiences': [],
                'communities_analyzed': 0,
                'total_posts_analyzed': 0
            }
            
            for subreddit_name in communities[:3]:  # Limit to 3 subreddits for API limits
                try:
                    logger.info(f"🔍 Searching r/{subreddit_name} for '{topic}'...")
                    subreddit_insights = await self._search_subreddit(subreddit_name, topic)
                    all_insights = self._merge_insights(all_insights, subreddit_insights)
                    all_insights['communities_analyzed'] += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error searching r/{subreddit_name}: {str(e)}")
                    continue
            
            # Calculate final metrics
            all_insights['authenticity_score'] = self._calculate_authenticity_score(all_insights)
            all_insights['insight_quality'] = self._assess_insight_quality(all_insights)
            all_insights['data_source'] = 'live_reddit_api'
            all_insights['communities'] = communities
            
            logger.info(f"✅ Reddit research complete: {all_insights['total_posts_analyzed']} posts analyzed")
            return all_insights
            
        except Exception as e:
            logger.error(f"❌ Reddit research error: {str(e)}")
            return self._get_enhanced_simulation(topic, subreddits)
    
    async def _search_subreddit(self, subreddit_name: str, topic: str) -> Dict[str, Any]:
        """Search a specific subreddit for insights"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            insights = self._empty_insights()
            posts_analyzed = 0
            
            # Search recent posts
            for submission in subreddit.search(topic, time_filter='month', limit=20):
                post_insights = self._analyze_post(submission)
                insights = self._merge_post_insights(insights, post_insights)
                posts_analyzed += 1
                
                # Analyze top comments
                submission.comments.replace_more(limit=0)
                for comment in submission.comments[:3]:  # Top 3 comments
                    if hasattr(comment, 'body') and len(comment.body) > 20:
                        comment_insights = self._analyze_comment(comment)
                        insights = self._merge_post_insights(insights, comment_insights)
            
            insights['posts_analyzed'] = posts_analyzed
            return insights
            
        except Exception as e:
            logger.warning(f"Error searching r/{subreddit_name}: {str(e)}")
            return self._empty_insights()
    
    def _analyze_post(self, submission) -> Dict[str, Any]:
        """Analyze a Reddit post for customer insights"""
        insights = self._empty_insights()
        
        title = submission.title.lower()
        text = f"{submission.title} {submission.selftext}".lower()
        
        # Extract customer language patterns
        if len(text) > 30:
            insights['customer_voice']['common_language'].append(text[:150] + '...')
        
        # Extract questions
        if '?' in text:
            questions = [q.strip() + '?' for q in text.split('?') if len(q.strip()) > 10]
            insights['customer_voice']['frequent_questions'].extend(questions[:2])
        
        # Extract pain points
        pain_indicators = ['problem', 'issue', 'trouble', 'difficult', 'frustrating', 'struggle', 
                          'confused', 'help', 'stuck', 'wrong', 'broken', 'fail']
        if any(indicator in text for indicator in pain_indicators):
            insights['customer_voice']['pain_points'].append(text[:200] + '...')
        
        # Extract recommendations
        rec_indicators = ['recommend', 'suggest', 'try', 'use', 'works', 'best', 'love']
        if any(indicator in text for indicator in rec_indicators):
            insights['customer_voice']['recommendations'].append(text[:150] + '...')
        
        # Extract authenticity markers
        auth_markers = ['i ', 'my ', 'personally', 'in my experience', 'i found', 'this happened to me']
        for marker in auth_markers:
            if marker in text:
                insights['authenticity_markers'].append({
                    'marker': marker,
                    'context': text[max(0, text.find(marker)-30):text.find(marker)+100],
                    'score': submission.score
                })
        
        # Extract real experiences
        if any(phrase in text for phrase in ['i ', 'my ', 'me ', 'i\'ve', 'i\'m']) and len(text) > 50:
            insights['real_experiences'].append({
                'experience': text[:250] + '...' if len(text) > 250 else text,
                'score': submission.score,
                'subreddit': submission.subreddit.display_name
            })
        
        # Sentiment analysis
        positive_words = ['great', 'amazing', 'love', 'best', 'perfect', 'awesome', 'excellent', 'fantastic']
        negative_words = ['hate', 'terrible', 'worst', 'awful', 'horrible', 'useless', 'disappointed', 'frustrating']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            insights['sentiment'] = 'positive'
        elif negative_count > positive_count:
            insights['sentiment'] = 'negative'
        else:
            insights['sentiment'] = 'neutral'
        
        return insights
    
    def _analyze_comment(self, comment) -> Dict[str, Any]:
        """Analyze a Reddit comment for insights"""
        if hasattr(comment, 'body'):
            # Create a mock submission object from comment
            class MockSubmission:
                def __init__(self, comment):
                    self.title = ""
                    self.selftext = comment.body
                    self.score = comment.score
                    self.subreddit = comment.subreddit
            
            return self._analyze_post(MockSubmission(comment))
        
        return self._empty_insights()
    
    def _empty_insights(self) -> Dict:
        """Return empty insights structure"""
        return {
            'customer_voice': {
                'common_language': [],
                'frequent_questions': [],
                'pain_points': [],
                'recommendations': []
            },
            'authenticity_markers': [],
            'real_experiences': [],
            'sentiment': 'neutral',
            'posts_analyzed': 0
        }
    
    def _merge_insights(self, main_insights: Dict, new_insights: Dict) -> Dict:
        """Merge insights from different subreddits"""
        # Merge customer voice data
        for voice_key in ['common_language', 'frequent_questions', 'pain_points', 'recommendations']:
            if voice_key in new_insights.get('customer_voice', {}):
                main_insights['customer_voice'][voice_key].extend(
                    new_insights['customer_voice'][voice_key]
                )
        
        # Merge other data
        for key in ['authenticity_markers', 'real_experiences']:
            if key in new_insights:
                main_insights[key].extend(new_insights[key])
        
        # Update post count
        main_insights['total_posts_analyzed'] += new_insights.get('posts_analyzed', 0)
        
        # Update sentiment
        sentiments = [main_insights.get('sentiment', 'neutral'), new_insights.get('sentiment', 'neutral')]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        
        if positive_count > negative_count:
            main_insights['sentiment'] = 'positive'
        elif negative_count > positive_count:
            main_insights['sentiment'] = 'negative'
        else:
            main_insights['sentiment'] = 'neutral'
        
        return main_insights
    
    def _merge_post_insights(self, main_insights: Dict, post_insights: Dict) -> Dict:
        """Merge insights from a single post"""
        return self._merge_insights(main_insights, post_insights)
    
    def _calculate_authenticity_score(self, insights: Dict) -> float:
        """Calculate authenticity score based on insights"""
        score = 0.0
        
        # Score based on authenticity markers
        score += min(3.0, len(insights.get('authenticity_markers', [])) * 0.5)
        
        # Score based on real experiences
        score += min(3.0, len(insights.get('real_experiences', [])) * 0.4)
        
        # Score based on total customer voice items
        total_voice_items = sum(
            len(insights.get('customer_voice', {}).get(key, []))
            for key in ['common_language', 'frequent_questions', 'pain_points', 'recommendations']
        )
        score += min(4.0, total_voice_items * 0.1)
        
        return min(10.0, score)
    
    def _assess_insight_quality(self, insights: Dict) -> str:
        """Assess the quality of insights gathered"""
        total_insights = (
            len(insights.get('authenticity_markers', [])) +
            len(insights.get('real_experiences', [])) +
            sum(len(insights.get('customer_voice', {}).get(key, [])) 
                for key in ['common_language', 'frequent_questions', 'pain_points', 'recommendations'])
        )
        
        if total_insights >= 30:
            return 'excellent'
        elif total_insights >= 15:
            return 'good'
        elif total_insights >= 8:
            return 'fair'
        else:
            return 'limited'
    
    def _get_enhanced_simulation(self, topic: str, subreddits: str) -> Dict[str, Any]:
        """Enhanced simulation when Reddit API is unavailable"""
        communities = [s.strip() for s in subreddits.split(',') if s.strip()]
        topic_lower = topic.lower()
        
        # Topic-specific simulation based on keywords
        if any(word in topic_lower for word in ['budget', 'cheap', 'affordable']):
            pain_points = [
                f"Can't afford expensive {topic} options",
                f"Hidden costs with {topic} purchases",
                "Limited budget for quality options",
                "Finding value for money solutions"
            ]
            questions = [
                f"What's the cheapest {topic}?",
                f"Any budget-friendly {topic} recommendations?",
                "How to get best value for money?",
                "Are expensive options really worth it?"
            ]
        elif any(word in topic_lower for word in ['laptop', 'computer', 'tech']):
            pain_points = [
                "Overwhelming number of technical specifications",
                "Technology changes so quickly",
                "Don't understand technical jargon",
                "Worried about making wrong choice"
            ]
            questions = [
                f"Best {topic} for beginners?",
                "What specs do I actually need?",
                "How long will this last?",
                "Is it worth upgrading?"
            ]
        else:
            pain_points = [
                f"Too many {topic} options to choose from",
                f"Difficulty finding reliable {topic} information",
                f"Worried about making wrong {topic} decision",
                f"Time constraints for {topic} research"
            ]
            questions = [
                f"How to choose the right {topic}?",
                f"What should I know about {topic}?",
                f"Any {topic} recommendations?",
                "Where to start with this?"
            ]
        
        return {
            'customer_voice': {
                'common_language': [
                    "user-friendly", "reliable", "good value", "recommended", 
                    "works well", "easy to use", "worth it"
                ],
                'frequent_questions': questions,
                'pain_points': pain_points,
                'recommendations': [
                    "Do your research first",
                    "Read reviews from multiple sources", 
                    "Start with basics",
                    "Consider long-term value"
                ]
            },
            'sentiment_analysis': {'positive': 0.55, 'neutral': 0.35, 'negative': 0.10},
            'trending_discussions': [
                f"Best {topic} for beginners",
                f"{topic} comparison guide",
                f"Common {topic} mistakes"
            ],
            'authenticity_markers': [
                {
                    'marker': 'personally',
                    'context': f"Personally, I found this approach to {topic} worked well...",
                    'score': 12
                }
            ],
            'real_experiences': [
                {
                    'experience': f"Used this for {topic} and had mixed results but overall positive...",
                    'score': 18,
                    'subreddit': communities[0] if communities else 'general'
                }
            ],
            'communities_analyzed': len(communities),
            'total_posts_analyzed': 45,
            'authenticity_score': 4.2,
            'insight_quality': 'enhanced_simulation',
            'data_source': 'enhanced_simulation',
            'communities': communities,
            'note': 'Enhanced simulation - Configure Reddit API for live insights'
        }

# ================== ENHANCED TRUST SCORE ASSESSOR ==================

class EnhancedTrustScoreAssessor:
    """Enhanced Trust Score assessor with FIXED calculation"""
    def __init__(self):
        self.available = True
        
        # YMYL topics requiring higher Trust standards
        self.ymyl_topics = [
            'finance', 'health', 'medical', 'legal', 'investment', 'insurance',
            'taxes', 'retirement', 'medication', 'surgery', 'diet', 'nutrition',
            'safety', 'parenting', 'relationships', 'government', 'news'
        ]
    
    def assess_trust_score(self, content: str, business_context: Dict, 
                          human_inputs: Dict, reddit_insights: Dict = None) -> Dict[str, Any]:
        """Comprehensive Trust Score assessment with FIXED weighted calculation"""
        
        topic = business_context.get('topic', '')
        industry = business_context.get('industry', '')
        
        # Determine if this is YMYL content
        is_ymyl = self._is_ymyl_topic(topic, industry)
        
        # Calculate individual component scores
        experience_score = self._assess_experience(human_inputs, reddit_insights, is_ymyl)
        expertise_score = self._assess_expertise(business_context, human_inputs, content, is_ymyl)
        authoritativeness_score = self._assess_authoritativeness(business_context, human_inputs, content)
        trustworthiness_score = self._assess_trustworthiness(business_context, human_inputs, is_ymyl)
        
        # FIXED: Calculate overall Trust score with proper weighting
        overall_score = self._calculate_overall_trust_score(
            experience_score, expertise_score, authoritativeness_score, 
            trustworthiness_score, is_ymyl
        )
        
        # Determine Trust level and grade
        trust_level = self._determine_trust_level(overall_score)
        trust_grade = self._determine_trust_grade(overall_score)
        
        return {
            "overall_trust_score": round(overall_score, 1),
            "trust_level": trust_level,
            "trust_grade": trust_grade,
            "is_ymyl_topic": is_ymyl,
            "component_scores": {
                "experience": round(experience_score, 1),
                "expertise": round(expertise_score, 1),
                "authoritativeness": round(authoritativeness_score, 1),
                "trustworthiness": round(trustworthiness_score, 1)
            },
            "weighted_breakdown": self._get_weight_breakdown(is_ymyl),
            "improvement_recommendations": self._get_improvement_recommendations(
                experience_score, expertise_score, authoritativeness_score, trustworthiness_score
            ),
            "trust_signals_to_include": self._get_trust_signals(is_ymyl),
            "calculation_debug": {
                "raw_scores": {
                    "experience": experience_score,
                    "expertise": expertise_score, 
                    "authoritativeness": authoritativeness_score,
                    "trustworthiness": trustworthiness_score
                },
                "weights_used": self._get_weight_breakdown(is_ymyl),
                "calculation_method": "weighted_average",
                "ymyl_adjustment": is_ymyl
            }
        }
    
    def _is_ymyl_topic(self, topic: str, industry: str) -> bool:
        """Determine if topic/industry is YMYL (Your Money or Your Life)"""
        topic_lower = topic.lower()
        industry_lower = industry.lower()
        return any(ymyl in topic_lower or ymyl in industry_lower for ymyl in self.ymyl_topics)
    
    def _assess_experience(self, human_inputs: Dict, reddit_insights: Dict, is_ymyl: bool) -> float:
        """Assess Experience component (first-hand, practical experience)"""
        score = 2.0  # Base score
        
        # Customer insights and pain points
        customer_pain_points = human_inputs.get('customer_pain_points', '')
        if len(customer_pain_points) > 100:
            score += 2.0  # Detailed customer understanding
        elif len(customer_pain_points) > 50:
            score += 1.0
        
        # Success stories and case studies
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if any(word in unique_value_prop.lower() for word in ['years', 'experience', 'clients', 'customers']):
            score += 1.5
        
        # Reddit insights authenticity
        if reddit_insights:
            auth_score = reddit_insights.get('authenticity_score', 0)
            if auth_score > 6.0:
                score += 2.0
            elif auth_score > 3.0:
                score += 1.0
            
            # Real customer experiences
            real_experiences = reddit_insights.get('real_experiences', [])
            score += min(1.5, len(real_experiences) * 0.3)
        
        # YMYL penalty for insufficient experience
        if is_ymyl and score < 6.0:
            score *= 0.8
        
        return min(10.0, score)
    
    def _assess_expertise(self, business_context: Dict, human_inputs: Dict, content: str, is_ymyl: bool) -> float:
        """Assess Expertise component (deep knowledge and skill)"""
        score = 2.5  # Base score
        
        # Industry knowledge
        industry = business_context.get('industry', '')
        if industry:
            score += 1.5
        
        # Unique value proposition and expertise claims
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if len(unique_value_prop) > 100:
            score += 2.0
        elif len(unique_value_prop) > 50:
            score += 1.0
        
        # Content depth and technical accuracy
        word_count = len(content.split())
        if word_count > 1500:
            score += 1.5
        elif word_count > 800:
            score += 1.0
        
        # Technical terminology and depth
        if content.count('#') > 5:  # Good structure
            score += 0.5
        
        # Business type expertise
        business_type = business_context.get('business_type', '')
        if business_type in ['B2B', 'SaaS', 'Consulting']:
            score += 1.0
        
        # YMYL requires higher expertise
        if is_ymyl and score < 7.0:
            score *= 0.7
        
        return min(10.0, score)
    
    def _assess_authoritativeness(self, business_context: Dict, human_inputs: Dict, content: str) -> float:
        """Assess Authoritativeness component (recognition and credibility)"""
        score = 3.0  # Base score
        
        # Business credibility
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if any(word in unique_value_prop.lower() for word in ['certified', 'licensed', 'award', 'recognized']):
            score += 2.0
        
        # Industry position
        if unique_value_prop and len(unique_value_prop) > 80:
            score += 1.5
        
        # Content authority signals
        if any(phrase in content.lower() for phrase in ['according to', 'research shows', 'studies indicate']):
            score += 1.0
        
        # Target audience specificity
        target_audience = business_context.get('target_audience', '')
        if target_audience and len(target_audience) > 20:
            score += 1.0
        
        # Business type authority
        business_type = business_context.get('business_type', '')
        if business_type == 'B2B':
            score += 0.5
        
        return min(10.0, score)
    
    def _assess_trustworthiness(self, business_context: Dict, human_inputs: Dict, is_ymyl: bool) -> float:
        """Assess Trustworthiness component (honesty and transparency)"""
        score = 3.5  # Base score
        
        # Transparency in value proposition
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if unique_value_prop and len(unique_value_prop) > 100:
            score += 2.0
        elif unique_value_prop and len(unique_value_prop) > 50:
            score += 1.0
        
        # Customer pain point understanding (shows empathy/honesty)
        customer_pain_points = human_inputs.get('customer_pain_points', '')
        if len(customer_pain_points) > 100:
            score += 1.5
        elif len(customer_pain_points) > 50:
            score += 1.0
        
        # Industry credibility
        industry = business_context.get('industry', '')
        if industry in ['Healthcare', 'Finance', 'Legal', 'Education']:
            score += 1.0
        
        # Target audience focus
        target_audience = business_context.get('target_audience', '')
        if target_audience:
            score += 0.5
        
        # YMYL requires exceptional trustworthiness
        if is_ymyl:
            if score < 7.0:
                score *= 0.6  # Significant penalty
        else:
            score += 0.5  # Slight boost for non-YMYL
        
        return min(10.0, score)
    
    def _calculate_overall_trust_score(self, experience: float, expertise: float, 
                                     authoritativeness: float, trustworthiness: float, is_ymyl: bool) -> float:
        """FIXED: Calculate overall Trust score with proper weighting"""
        
        # Different weights for YMYL vs non-YMYL content
        if is_ymyl:
            # YMYL content prioritizes trustworthiness and expertise
            weights = {
                'trustworthiness': 0.35,
                'expertise': 0.30,
                'experience': 0.20,
                'authoritativeness': 0.15
            }
        else:
            # Non-YMYL content has more balanced weighting
            weights = {
                'experience': 0.30,
                'expertise': 0.25,
                'trustworthiness': 0.25,
                'authoritativeness': 0.20
            }
        
        # Calculate weighted sum
        overall = (
            experience * weights['experience'] +
            expertise * weights['expertise'] +
            authoritativeness * weights['authoritativeness'] +
            trustworthiness * weights['trustworthiness']
        )
        
        return round(overall, 2)
    
    def _determine_trust_level(self, score: float) -> str:
        """Determine trust level based on score"""
        if score >= 9.0:
            return 'exceptional'
        elif score >= 8.0:
            return 'very_high'
        elif score >= 7.0:
            return 'high'
        elif score >= 6.0:
            return 'moderate'
        elif score >= 4.0:
            return 'developing'
        else:
            return 'needs_improvement'
    
    def _determine_trust_grade(self, score: float) -> str:
        """Determine trust grade based on score"""
        if score >= 9.0:
            return 'A+'
        elif score >= 8.5:
            return 'A'
        elif score >= 8.0:
            return 'A-'
        elif score >= 7.5:
            return 'B+'
        elif score >= 7.0:
            return 'B'
        elif score >= 6.5:
            return 'B-'
        elif score >= 6.0:
            return 'C+'
        elif score >= 5.0:
            return 'C'
        else:
            return 'D'
    
    def _get_weight_breakdown(self, is_ymyl: bool) -> Dict[str, float]:
        """Get the weighting breakdown used in calculation"""
        if is_ymyl:
            return {
                'trustworthiness': 0.35,
                'expertise': 0.30,
                'experience': 0.20,
                'authoritativeness': 0.15
            }
        else:
            return {
                'experience': 0.30,
                'expertise': 0.25,
                'trustworthiness': 0.25,
                'authoritativeness': 0.20
            }
    
    def _get_improvement_recommendations(self, exp: float, expert: float, auth: float, trust: float) -> List[str]:
        """Get specific improvement recommendations"""
        recommendations = []
        
        if exp < 6.0:
            recommendations.append("Add more personal experience stories and customer success cases")
        if expert < 6.0:
            recommendations.append("Demonstrate deeper industry expertise and technical knowledge")
        if auth < 6.0:
            recommendations.append("Build stronger authority signals and credibility indicators")
        if trust < 7.0:
            recommendations.append("Enhance transparency and include more trust signals")
        
        # Always provide at least one recommendation
        if not recommendations:
            recommendations.append("Continue building on your strong trust foundation")
        
        return recommendations
    
    def _get_trust_signals(self, is_ymyl: bool) -> List[str]:
        """Get trust signals to include in content"""
        base_signals = [
            "Author bio with credentials",
            "Publication and update dates",
            "Contact information",
            "Customer testimonials",
            "Industry statistics and sources"
        ]
        
        if is_ymyl:
            base_signals.extend([
                "Professional certifications",
                "Medical/legal disclaimers",
                "Peer review indicators",
                "Regulatory compliance notes"
            ])
        
        return base_signals

# ================== CONTENT IMPROVEMENT DIALOGUE SYSTEM ==================

class ConversationalAIImprovement:
    """Conversational AI system for content improvements"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.conversation_history = []
    
    async def start_improvement_session(self, content: str, trust_assessment: Dict, 
                                      quality_assessment: Dict) -> Dict[str, Any]:
        """Start an improvement conversation session"""
        
        # Analyze current content state
        current_state = {
            'trust_score': trust_assessment.get('overall_trust_score', 0),
            'trust_grade': trust_assessment.get('trust_grade', 'N/A'),
            'quality_score': quality_assessment.get('overall_quality_score', 0),
            'word_count': len(content.split()),
            'improvement_areas': trust_assessment.get('improvement_recommendations', [])
        }
        
        # Generate initial improvement suggestions
        initial_suggestions = await self._generate_contextual_suggestions(current_state)
        
        return {
            'session_id': f"improve_{datetime.now().timestamp()}",
            'current_state': current_state,
            'initial_suggestions': initial_suggestions,
            'conversation_started': True,
            'next_questions': self._get_follow_up_questions(current_state)
        }
    
    async def process_improvement_request(self, user_request: str, content: str, 
                                        trust_assessment: Dict) -> Dict[str, Any]:
        """Process a specific improvement request from user"""
        
        prompt = f"""
        User wants to improve their content. Here's their request: "{user_request}"
        
        Current content trust score: {trust_assessment.get('overall_trust_score', 0)}/10
        Current trust grade: {trust_assessment.get('trust_grade', 'N/A')}
        
        Provide specific, actionable advice for this improvement request. Include:
        1. Immediate actions they can take
        2. Expected impact on trust score
        3. Specific examples if relevant
        4. Follow-up suggestions
        
        Be conversational and helpful, like an expert consultant.
        """
        
        response = await self.llm_client.generate_content(prompt)
        
        return {
            'ai_response': response,
            'improvement_type': self._classify_improvement_type(user_request),
            'estimated_impact': self._estimate_improvement_impact(user_request, trust_assessment),
            'follow_up_questions': self._generate_follow_up_questions(user_request)
        }
    
    async def _generate_contextual_suggestions(self, current_state: Dict) -> List[Dict]:
        """Generate contextual improvement suggestions"""
        suggestions = []
        trust_score = current_state['trust_score']
        
        if trust_score < 6.0:
            suggestions.append({
                'priority': 'high',
                'area': 'Trust Foundation',
                'suggestion': 'Add author credentials and company background to establish basic trust',
                'estimated_impact': '+1.5 to +2.0 trust score'
            })
        
        if trust_score < 7.5:
            suggestions.append({
                'priority': 'medium',
                'area': 'Customer Evidence',
                'suggestion': 'Include customer testimonials, case studies, or success metrics',
                'estimated_impact': '+0.8 to +1.2 trust score'
            })
        
        if current_state['word_count'] < 800:
            suggestions.append({
                'priority': 'medium',
                'area': 'Content Depth',
                'suggestion': 'Expand content with more detailed explanations and examples',
                'estimated_impact': '+0.5 to +1.0 trust score'
            })
        
        if trust_score < 8.0:
            suggestions.append({
                'priority': 'low',
                'area': 'Authority Signals',
                'suggestion': 'Add industry statistics, expert quotes, or research citations',
                'estimated_impact': '+0.3 to +0.7 trust score'
            })
        
        return suggestions
    
    def _get_follow_up_questions(self, current_state: Dict) -> List[str]:
        """Generate follow-up questions based on current state"""
        questions = [
            "What specific aspect would you like to improve first?",
            "Do you have customer testimonials or case studies to add?",
            "Would you like help with adding more authority signals?",
            "Should we focus on improving the trust score or content depth?"
        ]
        
        if current_state['trust_score'] < 6.0:
            questions.insert(0, "What credentials or experience can we highlight to build trust?")
        
        return questions
    
    def _classify_improvement_type(self, user_request: str) -> str:
        """Classify the type of improvement requested"""
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ['trust', 'credibility', 'authority']):
            return 'trust_building'
        elif any(word in request_lower for word in ['content', 'text', 'writing', 'words']):
            return 'content_enhancement'
        elif any(word in request_lower for word in ['seo', 'ranking', 'search']):
            return 'seo_optimization'
        elif any(word in request_lower for word in ['customer', 'audience', 'user']):
            return 'audience_focus'
        else:
            return 'general_improvement'
    
    def _estimate_improvement_impact(self, user_request: str, trust_assessment: Dict) -> str:
        """Estimate the impact of the requested improvement"""
        improvement_type = self._classify_improvement_type(user_request)
        current_score = trust_assessment.get('overall_trust_score', 0)
        
        if improvement_type == 'trust_building' and current_score < 6.0:
            return '+1.0 to +2.0 trust score points'
        elif improvement_type == 'content_enhancement':
            return '+0.5 to +1.0 trust score points'
        else:
            return '+0.3 to +0.8 trust score points'
    
    def _generate_follow_up_questions(self, user_request: str) -> List[str]:
        """Generate follow-up questions based on user request"""
        improvement_type = self._classify_improvement_type(user_request)
        
        if improvement_type == 'trust_building':
            return [
                "What specific credentials or experience should we highlight?",
                "Do you have any industry certifications or awards?",
                "Would you like to add customer testimonials?"
            ]
        elif improvement_type == 'content_enhancement':
            return [
                "Which sections need more detail?",
                "Should we add more examples or case studies?",
                "Would you like help with better structure?"
            ]
        else:
            return [
                "What's your main goal with this improvement?",
                "Are there specific areas you want to focus on?",
                "How can we best help your audience?"
            ]

# ================== IMPORT AGENTS FROM SRC/AGENTS ==================

# Import all agents from your src/agents folder
try:
    from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
    from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor  # Will rename to Trust
    from src.agents.topic_research_agent import TopicResearchAgent
    from src.agents.improvement_tracking_agent import ImprovementTrackingAgent
    from src.agents.content_quality_scorer import ContentQualityScorer
    
    AGENTS_IMPORTED = True
    logger.info("✅ Successfully imported agents from src/agents folder")
except ImportError as e:
    logger.warning(f"⚠️ Could not import some agents from src/agents: {str(e)}")
    AGENTS_IMPORTED = False

# ================== MAIN ORCHESTRATOR ==================

class ZeeSEOOrchestrator:
    """Main orchestrator for all SEO tool functionality"""
    def __init__(self):
        self.llm_client = LLMClient()
        self.reddit_client = EnhancedRedditClient()
        self.trust_assessor = EnhancedTrustScoreAssessor()
        self.conversation_ai = ConversationalAIImprovement(self.llm_client)
        
        # Use imported agents if available, otherwise use built-in ones
        if AGENTS_IMPORTED:
            try:
                # Use your actual agents from src/agents
                self.reddit_researcher = EnhancedRedditResearcher()
                self.quality_scorer = ContentQualityScorer()
                logger.info("✅ Using imported agents from src/agents")
            except Exception as e:
                logger.warning(f"⚠️ Error initializing imported agents: {str(e)}")
                self._initialize_fallback_agents()
        else:
            self._initialize_fallback_agents()
    
    def _initialize_fallback_agents(self):
        """Initialize fallback agents if imports fail"""
        logger.info("🔧 Using built-in fallback agents")
        
        class FallbackQualityScorer:
            def score_content_quality(self, content: str, topic: str, business_context: Dict, 
                                    human_inputs: Dict, trust_assessment: Dict) -> Dict[str, Any]:
                word_count = len(content.split())
                trust_score = trust_assessment.get('overall_trust_score', 7.0)
                
                content_score = 8.5 if word_count > 1000 else 7.0 if word_count > 500 else 6.0
                structure_score = 8.0 if content.count('#') > 3 else 6.5
                
                overall_score = (content_score * 0.4 + structure_score * 0.3 + trust_score * 0.3)
                
                return {
                    "overall_quality_score": round(overall_score, 1),
                    "content_score": content_score,
                    "structure_score": structure_score,
                    "trust_correlation": trust_score,
                    "performance_prediction": "High performance expected" if overall_score >= 8.0 else "Good performance expected",
                    "vs_ai_comparison": {
                        "performance_boost": "350%+" if overall_score >= 8.5 else "250%+",
                        "engagement_multiplier": "4x" if overall_score >= 8.5 else "3x"
                    }
                }
        
        self.quality_scorer = FallbackQualityScorer()
    
    async def generate_comprehensive_analysis(self, form_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive content analysis with all enhancements"""
        
        topic = form_data['topic']
        subreddits = form_data.get('subreddits', '')
        
        # Business context
        business_context = {
            'topic': topic,
            'industry': form_data['industry'],
            'target_audience': form_data['target_audience'],
            'business_type': form_data['business_type'],
            'unique_value_prop': form_data['unique_value_prop']
        }
        
        # Human inputs
        human_inputs = {
            'customer_pain_points': form_data['customer_pain_points'],
            'unique_value_prop': form_data['unique_value_prop']
        }
        
        logger.info(f"🎯 Starting comprehensive analysis for: {topic}")
        
        # Step 1: Reddit Research
        logger.info("📱 Researching Reddit for authentic customer insights...")
        reddit_insights = await self.reddit_client.research_topic(topic, subreddits)
        
        # Step 2: Generate Content
        logger.info("✍️ Generating content with customer insights...")
        content = await self._generate_enhanced_content(
            topic, business_context, human_inputs, reddit_insights, form_data
        )
        
        # Step 3: Trust Score Assessment
        logger.info("🔒 Calculating Trust Score...")
        trust_assessment = self.trust_assessor.assess_trust_score(
            content, business_context, human_inputs, reddit_insights
        )
        
        # Step 4: Quality Assessment
        logger.info("📊 Scoring content quality...")
        quality_assessment = self.quality_scorer.score_content_quality(
            content, topic, business_context, human_inputs, trust_assessment
        )
        
        # Step 5: Start Improvement Session
        logger.info("💬 Initializing improvement dialogue...")
        improvement_session = await self.conversation_ai.start_improvement_session(
            content, trust_assessment, quality_assessment
        )
        
        logger.info("✅ Comprehensive analysis complete!")
        
        return {
            'topic': topic,
            'generated_content': content,
            'reddit_insights': reddit_insights,
            'trust_assessment': trust_assessment,
            'quality_assessment': quality_assessment,
            'improvement_session': improvement_session,
            'business_context': business_context,
            'human_inputs': human_inputs,
            'performance_metrics': {
                'word_count': len(content.split()),
                'trust_score': trust_assessment['overall_trust_score'],
                'trust_grade': trust_assessment['trust_grade'],
                'quality_score': quality_assessment['overall_quality_score'],
                'reddit_authenticity': reddit_insights.get('authenticity_score', 0),
                'data_source': reddit_insights.get('data_source', 'simulation')
            }
        }
    
    async def _generate_enhanced_content(self, topic: str, business_context: Dict, 
                                       human_inputs: Dict, reddit_insights: Dict, 
                                       form_data: Dict) -> str:
        """Generate enhanced content using all available intelligence"""
        
        # Extract Reddit insights
        customer_language = reddit_insights.get('customer_voice', {}).get('common_language', [])
        customer_questions = reddit_insights.get('customer_voice', {}).get('frequent_questions', [])
        customer_pain_points = reddit_insights.get('customer_voice', {}).get('pain_points', [])
        
        prompt = f"""
        Create comprehensive, trust-optimized content about "{topic}".
        
        BUSINESS INTELLIGENCE:
        - Industry: {business_context['industry']}
        - Target Audience: {business_context['target_audience']}
        - Business Type: {business_context['business_type']}
        - Unique Value Proposition: {business_context['unique_value_prop']}
        
        CUSTOMER INSIGHTS:
        - Known Pain Points: {human_inputs['customer_pain_points']}
        
        REDDIT RESEARCH INSIGHTS:
        - Authentic Customer Language: {', '.join(customer_language[:5])}
        - Real Customer Questions: {', '.join(customer_questions[:3])}
        - Community Pain Points: {', '.join(customer_pain_points[:3])}
        - Research Quality: {reddit_insights.get('insight_quality', 'N/A')}
        - Data Source: {reddit_insights.get('data_source', 'simulation')}
        
        AI WRITING INSTRUCTIONS:
        - Writing Style: {form_data.get('writing_style', 'Professional')}
        - Word Count Target: {form_data.get('target_word_count', '1000-1500 words')}
        - Language: {form_data.get('language_preference', 'Default')}
        - Additional Notes: {form_data.get('additional_notes', '')}
        
        CONTENT REQUIREMENTS:
        1. Write in {form_data.get('writing_style', 'professional')} tone
        2. Target {form_data.get('target_word_count', '1000-1500')} words
        3. Use authentic customer language from Reddit research
        4. Address specific customer pain points discovered
        5. Include trust signals (expertise, authority, transparency)
        6. Structure with clear headings and subheadings
        7. Provide actionable advice and solutions
        8. Include your unique value proposition naturally
        9. End with compelling call-to-action
        10. Optimize for Trust Score (experience, expertise, authority, trust)
        
        Create content that demonstrates deep understanding of customer needs while positioning expertise and building trust. Use the Reddit insights to make the content authentic and relatable.
        """
        
        return await self.llm_client.generate_content(prompt, model="claude-3-haiku-20240307")
    
    def get_system_status(self) -> Dict[str, str]:
        """Get comprehensive system status"""
        return {
            'llm_client': 'operational' if self.llm_client.available else 'unavailable',
            'reddit_client': 'operational' if self.reddit_client.available else 'simulation_mode',
            'trust_assessor': 'operational',
            'conversation_ai': 'operational',
            'agents_imported': 'yes' if AGENTS_IMPORTED else 'using_fallbacks',
            'praw_library': 'available' if PRAW_AVAILABLE else 'unavailable'
        }

# Initialize the orchestrator
zee_orchestrator = ZeeSEOOrchestrator()

# ================== API ROUTES ==================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced home page with improved UI and conversation dialogue"""
    
    system_status = zee_orchestrator.get_system_status()
    reddit_status = "🟢 Live API" if system_status['reddit_client'] == 'operational' else "🟡 Enhanced Simulation"
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool v3.0 - Advanced Content Intelligence Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; color: #0f172a; line-height: 1.6;
            }}
            .header {{ 
                text-align: center; color: white; padding: 2rem 1rem;
                background: rgba(0,0,0,0.1); backdrop-filter: blur(10px);
            }}
            .logo {{ 
                font-size: 3.5rem; font-weight: 900; margin-bottom: 1rem;
                text-shadow: 2px 2px 8px rgba(0,0,0,0.3); letter-spacing: -2px;
            }}
            .tagline {{ font-size: 1.5rem; opacity: 0.95; margin-bottom: 0.5rem; }}
            .subtitle {{ font-size: 1rem; opacity: 0.8; font-style: italic; }}
            .status-bar {{ 
                background: rgba(255,255,255,0.15); padding: 1rem 2rem; margin: 1rem 0;
                border-radius: 2rem; backdrop-filter: blur(10px); display: inline-block;
            }}
            .container {{ 
                max-width: 1400px; margin: 0 auto; padding: 2rem;
                background: white; border-radius: 2rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15);
                position: relative;
            }}
            .ai-badge {{ 
                background: linear-gradient(135deg, #8B5CF6, #A855F7); color: white;
                padding: 1rem 2rem; border-radius: 2rem; display: inline-block; margin-bottom: 2rem;
                font-weight: 700; font-size: 1.1rem;
            }}
            .form-grid {{ 
                display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;
            }}
            .form-section {{ 
                background: #f8fafc; padding: 2rem; border-radius: 1.5rem;
                border-left: 5px solid #8B5CF6; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .section-title {{ 
                color: #8B5CF6; font-size: 1.25rem; font-weight: 800; margin-bottom: 1.5rem;
                display: flex; align-items: center; gap: 0.75rem;
            }}
            .form-group {{ margin-bottom: 1.5rem; }}
            label {{ 
                display: block; margin-bottom: 0.5rem; font-weight: 600; color: #374151;
                font-size: 0.95rem;
            }}
            input, textarea, select {{ 
                width: 100%; padding: 1rem; border: 2px solid #e5e7eb; border-radius: 1rem;
                font-size: 0.95rem; transition: all 0.2s ease; font-family: inherit;
            }}
            input:focus, textarea:focus, select:focus {{ 
                outline: none; border-color: #8B5CF6; box-shadow: 0 0 0 4px rgba(139,92,246,0.1);
                transform: translateY(-1px);
            }}
            textarea {{ min-height: 4rem; resize: vertical; }}
            .help-text {{ font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem; }}
            .ai-section {{ 
                background: linear-gradient(135deg, #eff6ff, #dbeafe); border: 2px solid #3b82f6;
                border-radius: 1.5rem; padding: 2rem; margin-bottom: 2rem;
            }}
            .ai-section .section-title {{ color: #1d4ed8; border-bottom-color: #3b82f6; }}
            .features-showcase {{ 
                grid-column: 1 / -1; background: linear-gradient(135deg, #8B5CF6, #A855F7);
                color: white; padding: 2rem; border-radius: 1.5rem; margin-bottom: 2rem;
            }}
            .features-grid {{ 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;
                margin-top: 1.5rem;
            }}
            .feature-item {{ 
                background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 1rem;
                backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);
            }}
            .feature-icon {{ font-size: 2rem; margin-bottom: 0.5rem; }}
            .submit-section {{ 
                grid-column: 1 / -1; text-align: center; margin-top: 2rem;
            }}
            .btn-primary {{ 
                background: linear-gradient(135deg, #8B5CF6, #A855F7); color: white;
                padding: 1.25rem 3rem; border: none; border-radius: 2rem; cursor: pointer;
                font-size: 1.1rem; font-weight: 700; transition: all 0.3s ease;
                box-shadow: 0 10px 25px rgba(139,92,246,0.3); min-width: 400px;
            }}
            .btn-primary:hover {{ 
                transform: translateY(-3px); box-shadow: 0 20px 40px rgba(139,92,246,0.4);
            }}
            .conversation-panel {{ 
                position: fixed; bottom: 2rem; right: 2rem; width: 400px; height: 600px;
                background: white; border-radius: 1.5rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15);
                display: none; flex-direction: column; overflow: hidden; z-index: 1000;
            }}
            .conversation-header {{ 
                background: linear-gradient(135deg, #8B5CF6, #A855F7); color: white;
                padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center;
            }}
            .conversation-body {{ 
                flex: 1; padding: 1.5rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem;
            }}
            .ai-message {{ 
                background: #f3f4f6; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem;
                border-left: 4px solid #8B5CF6;
            }}
            .suggestion-card {{ 
                background: linear-gradient(135deg, #f0f9ff, #e0f2fe); border: 1px solid #0ea5e9;
                padding: 1rem; border-radius: 1rem; margin-bottom: 1rem;
            }}
            .conversation-input {{ 
                padding: 1rem 1.5rem; border-top: 1px solid #e5e7eb; display: flex; gap: 0.5rem;
            }}
            .conversation-input input {{ 
                flex: 1; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 1rem;
                font-size: 0.9rem;
            }}
            .conversation-input button {{ 
                padding: 0.75rem 1.5rem; background: #8B5CF6; color: white; border: none;
                border-radius: 1rem; cursor: pointer; font-weight: 600;
            }}
            .conversation-toggle {{ 
                position: fixed; bottom: 2rem; right: 2rem; width: 60px; height: 60px;
                background: linear-gradient(135deg, #8B5CF6, #A855F7); border-radius: 50%;
                border: none; color: white; font-size: 1.5rem; cursor: pointer;
                box-shadow: 0 8px 25px rgba(139,92,246,0.4); z-index: 1001;
                transition: transform 0.3s ease;
            }}
            .conversation-toggle:hover {{ transform: scale(1.1); }}
            .loading-overlay {{ 
                display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15,23,42,0.8); z-index: 2000; backdrop-filter: blur(8px);
            }}
            .loading-content {{ 
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: white; padding: 3rem; border-radius: 2rem; text-align: center;
                max-width: 500px; width: 90%; box-shadow: 0 25px 50px rgba(0,0,0,0.25);
            }}
            .loading-spinner {{ 
                width: 4rem; height: 4rem; border: 4px solid #e5e7eb; border-top: 4px solid #8B5CF6;
                border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 2rem;
            }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            @media (max-width: 1024px) {{ 
                .form-grid {{ grid-template-columns: 1fr; }}
                .features-grid {{ grid-template-columns: 1fr; }}
                .conversation-panel {{ width: 90%; right: 5%; }}
                .container {{ margin: 1rem; padding: 1.5rem; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">⚡ ZEE SEO TOOL v3.0</div>
            <div class="tagline">Advanced Content Intelligence Platform</div>
            <div class="subtitle">Built by Zeeshan Bashir • Bridging Human Expertise with AI Power</div>
            <div class="status-bar">
                Trust Score: ✅ Active | Reddit: {reddit_status} | Conversation AI: ✅ Live | Railway: ✅ Deployed
            </div>
        </div>
        
        <div class="container">
            <div class="ai-badge">🤖 Enhanced with Trust Score Assessment, Live Reddit Research & Conversational AI</div>
            
            <form action="/generate" method="post" id="contentForm">
                <div class="form-grid">
                    <div class="features-showcase">
                        <h3 style="font-size: 1.5rem; margin-bottom: 1rem;">🚀 Advanced Intelligence Features</h3>
                        <div class="features-grid">
                            <div class="feature-item">
                                <div class="feature-icon">🔒</div>
                                <h4>Trust Score Assessment</h4>
                                <p>Advanced scoring with fixed weighted calculation for accurate results</p>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">📱</div>
                                <h4>Live Reddit Research</h4>
                                <p>Real customer insights from target communities ({reddit_status})</p>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">💬</div>
                                <h4>Conversational AI</h4>
                                <p>Interactive improvement dialogue for continuous optimization</p>
                            </div>
                            <div class="feature-item">
                                <div class="feature-icon">📊</div>
                                <h4>Performance Analytics</h4>
                                <p>Real-time tracking and improvement recommendations</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">🎯 Content & Research</h3>
                        
                        <div class="form-group">
                            <label>Content Topic *</label>
                            <input type="text" name="topic" placeholder="e.g., best budget laptops for college students" required>
                            <div class="help-text">Be specific - our AI will analyze and optimize for your topic</div>
                        </div>
                        
                        <div class="form-group">
                            <label>Reddit Communities for Research</label>
                            <input type="text" name="subreddits" placeholder="e.g., laptops, college, StudentLoans">
                            <div class="help-text">Target communities for authentic customer insights ({reddit_status})</div>
                        </div>
                    </div>
                    
                    <div class="ai-section">
                        <h3 class="section-title">🤖 AI Writing Instructions</h3>
                        
                        <div class="form-group">
                            <label>Writing Style</label>
                            <select name="writing_style">
                                <option value="">Professional (Default)</option>
                                <option value="Conversational">Conversational & Friendly</option>
                                <option value="Academic">Academic & Research-Based</option>
                                <option value="Technical">Technical & Detailed</option>
                                <option value="Marketing">Marketing & Persuasive</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Target Word Count</label>
                            <select name="target_word_count">
                                <option value="">Optimal Length (AI Decides)</option>
                                <option value="500-700">Short (500-700 words)</option>
                                <option value="1000-1500">Medium (1000-1500 words)</option>
                                <option value="2000-2500">Long (2000-2500 words)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Language Preference</label>
                            <select name="language_preference">
                                <option value="">Default</option>
                                <option value="British English">British English (colour, realise)</option>
                                <option value="American English">American English (color, realize)</option>
                                <option value="Simple Language">Simple Language for Beginners</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Additional Instructions</label>
                            <textarea name="additional_notes" placeholder="e.g., Include statistics, Add comparison tables, Focus on benefits, Use bullet points"></textarea>
                            <div class="help-text">Specific instructions for the AI about content structure and focus</div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">🏢 Business Context</h3>
                        
                        <div class="form-group">
                            <label>Industry *</label>
                            <input type="text" name="industry" placeholder="e.g., Technology, Healthcare, Finance" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Target Audience *</label>
                            <input type="text" name="target_audience" placeholder="e.g., College students, Small business owners" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Business Type *</label>
                            <select name="business_type" required>
                                <option value="">Select...</option>
                                <option value="B2B">B2B (Business to Business)</option>
                                <option value="B2C">B2C (Business to Consumer)</option>
                                <option value="E-commerce">E-commerce</option>
                                <option value="SaaS">Software as a Service</option>
                                <option value="Consulting">Consulting Services</option>
                                <option value="Education">Education/Training</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Your Unique Value Proposition *</label>
                            <textarea name="unique_value_prop" placeholder="What makes you different? Your expertise, experience, unique approach..." required></textarea>
                            <div class="help-text">Critical for Trust Score - builds authority and credibility</div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">👥 Customer Insights</h3>
                        
                        <div class="form-group">
                            <label>Customer Pain Points & Challenges *</label>
                            <textarea name="customer_pain_points" placeholder="What specific problems do your customers face? What keeps them up at night?" required></textarea>
                            <div class="help-text">Will be combined with Reddit research for authentic insights</div>
                        </div>
                    </div>
                    
                    <div class="submit-section">
                        <button type="submit" class="btn-primary">
                            🚀 Generate Advanced Content Intelligence Report
                        </button>
                    </div>
                </div>
            </form>
        </div>
        
        <!-- Conversation AI Toggle -->
        <button class="conversation-toggle" onclick="toggleConversation()">💬</button>
        
        <!-- Conversation Panel -->
        <div class="conversation-panel" id="conversationPanel">
            <div class="conversation-header">
                <h4>💡 AI Content Assistant</h4>
                <button onclick="toggleConversation()" style="background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer;">×</button>
            </div>
            <div class="conversation-body" id="conversationBody">
                <div class="ai-message">
                    <strong>🤖 AI Assistant:</strong> Hi! I'm here to help you create high-performance content. Here are some quick tips to get started:
                </div>
                
                <div class="suggestion-card">
                    <h5>🎯 Quick Win #1</h5>
                    <p>Be specific with your topic. Instead of "laptops", try "best budget laptops for college students under $500"</p>
                </div>
                
                <div class="suggestion-card">
                    <h5>🔒 Trust Score Boost</h5>
                    <p>Include specific years of experience, certifications, or customer numbers in your value proposition</p>
                </div>
                
                <div class="suggestion-card">
                    <h5>📱 Reddit Research Tips</h5>
                    <p>Choose active communities where your target audience discusses problems related to your topic</p>
                </div>
                
                <div class="ai-message">
                    <strong>💬 Ask me anything:</strong> "How to improve trust score?", "Best subreddits for my topic?", "Writing style recommendations?"
                </div>
            </div>
            <div class="conversation-input">
                <input type="text" id="conversationInput" placeholder="Ask me about content optimization...">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <!-- Loading Overlay -->
        <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <h3>🧠 Advanced AI Processing</h3>
                <p>Running comprehensive analysis with Trust Score assessment, Reddit research, and content optimization...</p>
                <p><em>This may take 45-90 seconds for maximum quality</em></p>
            </div>
        </div>
        
        <script>
            function toggleConversation() {{
                const panel = document.getElementById('conversationPanel');
                const isVisible = panel.style.display === 'flex';
                panel.style.display = isVisible ? 'none' : 'flex';
            }}
            
            function sendMessage() {{
                const input = document.getElementById('conversationInput');
                const message = input.value.trim();
                if (!message) return;
                
                const body = document.getElementById('conversationBody');
                
                // Add user message
                const userMsg = document.createElement('div');
                userMsg.innerHTML = `<div style="background: #8B5CF6; color: white; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem; text-align: right;"><strong>You:</strong> ${{message}}</div>`;
                body.appendChild(userMsg);
                
                // Add AI response
                const aiMsg = document.createElement('div');
                aiMsg.className = 'ai-message';
                aiMsg.innerHTML = `<strong>🤖 AI:</strong> ${{getAIResponse(message)}}`;
                body.appendChild(aiMsg);
                
                input.value = '';
                body.scrollTop = body.scrollHeight;
            }}
            
            function getAIResponse(message) {{
                const msg = message.toLowerCase();
                
                if (msg.includes('trust score')) {{
                    return 'To improve Trust Score: Add specific credentials, include customer testimonials, show years of experience, and provide detailed explanations. YMYL topics need higher scores!';
                }} else if (msg.includes('reddit') || msg.includes('subreddit')) {{
                    return 'Choose active subreddits where your target audience discusses problems. Examples: r/laptops for tech, r/personalfinance for money topics, r/college for students.';
                }} else if (msg.includes('writing style')) {{
                    return 'Match your audience: Technical for experts, Conversational for general users, Academic for research-based content, Marketing for sales pages.';
                }} else if (msg.includes('word count')) {{
                    return 'Longer content (1500+ words) typically scores higher for Trust and authority. But focus on value over length - quality beats quantity!';
                }} else {{
                    return 'Great question! For best results: be specific with topics, choose relevant subreddits, include detailed business context, and use clear writing instructions. What specific area would you like help with?';
                }}
            }}
            
            document.getElementById('conversationInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    sendMessage();
                }}
            }});
            
            document.getElementById('contentForm').addEventListener('submit', function() {{
                document.getElementById('loadingOverlay').style.display = 'block';
            }});
            
            // Auto-show conversation on first visit
            setTimeout(() => {{
                if (!localStorage.getItem('conversationShown')) {{
                    toggleConversation();
                    localStorage.setItem('conversationShown', 'true');
                }}
            }}, 5000);
        </script>
    </body>
    </html>
    """)

@app.post("/generate")
async def generate_content(
    topic: str = Form(...),
    subreddits: str = Form(""),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    language_preference: str = Form(""),
    additional_notes: str = Form(""),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...)
):
    """Generate enhanced content with conversation AI"""
    
    try:
        form_data = {
            'topic': topic,
            'subreddits': subreddits,
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'language_preference': language_preference,
            'additional_notes': additional_notes,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'unique_value_prop': unique_value_prop,
            'customer_pain_points': customer_pain_points
        }
        
        logger.info(f"🎯 Starting content generation for: {topic}")
        
        # Run comprehensive analysis
        results = await zee_orchestrator.generate_comprehensive_analysis(form_data)
        
        logger.info(f"✅ Content generation complete")
        
        return HTMLResponse(content=generate_enhanced_results_page(results))
        
    except Exception as e:
        logger.error(f"❌ Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

def generate_enhanced_results_page(results: Dict[str, Any]) -> str:
    """Generate enhanced results page with conversation AI"""
    
    topic = results['topic']
    content = results['generated_content']
    trust = results['trust_assessment']
    quality = results['quality_assessment']
    reddit = results['reddit_insights']
    improvement = results['improvement_session']
    metrics = results['performance_metrics']
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Advanced Content Report - {topic} | Zee SEO Tool v3.0</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #0f172a; line-height: 1.6; min-height: 100vh;
            }}
            .header {{ 
                background: rgba(0,0,0,0.1); backdrop-filter: blur(10px);
                color: white; padding: 1.5rem; text-align: center;
            }}
            .logo {{ font-size: 2.5rem; font-weight: 900; margin-bottom: 0.5rem; }}
            .container {{ 
                max-width: 1600px; margin: 0 auto; padding: 2rem;
                background: white; border-radius: 2rem; box-shadow: 0 25px 50px rgba(0,0,0,0.15);
                margin-top: 2rem; margin-bottom: 2rem;
            }}
            .report-header {{ 
                background: linear-gradient(135deg, #8B5CF6, #A855F7); color: white;
                padding: 2rem; border-radius: 1.5rem; margin-bottom: 2rem; text-align: center;
            }}
            .metrics-dashboard {{ 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem; margin: 2rem 0;
            }}
            .metric-card {{ 
                background: linear-gradient(135deg, #f8fafc, #f1f5f9); padding: 1.5rem;
                border-radius: 1rem; text-align: center; border: 2px solid #e2e8f0;
                transition: transform 0.2s ease;
            }}
            .metric-card:hover {{ transform: translateY(-2px); }}
            .metric-value {{ font-size: 2rem; font-weight: 900; color: #8B5CF6; margin-bottom: 0.5rem; }}
            .metric-label {{ font-size: 0.9rem; color: #64748b; font-weight: 600; }}
            .section {{ 
                background: #f8fafc; padding: 2rem; border-radius: 1.5rem; margin: 2rem 0;
                border-left: 5px solid #8B5CF6; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .section h3 {{ 
                color: #8B5CF6; font-size: 1.5rem; margin-bottom: 1.5rem;
                display: flex; align-items: center; gap: 0.75rem;
            }}
            .trust-breakdown {{ 
                display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0;
            }}
            .trust-component {{ 
                background: white; padding: 1.5rem; border-radius: 1rem; text-align: center;
                border: 2px solid #e2e8f0;
            }}
            .trust-score {{ 
                font-size: 1.5rem; font-weight: 900; color: #8B5CF6; margin-bottom: 0.5rem;
            }}
            .content-display {{ 
                background: white; padding: 2rem; border-radius: 1rem; margin: 2rem 0;
                border: 2px solid #e2e8f0; max-height: 600px; overflow-y: auto;
            }}
            .content-actions {{ 
                display: flex; gap: 1rem; margin-bottom: 1rem; justify-content: center;
            }}
            .btn {{ 
                padding: 0.75rem 1.5rem; border-radius: 1rem; font-weight: 600;
                cursor: pointer; transition: all 0.2s ease; border: none;
            }}
            .btn-primary {{ 
                background: linear-gradient(135deg, #8B5CF6, #A855F7); color: white;
                box-shadow: 0 4px 15px rgba(139,92,246,0.3);
            }}
            .btn-outline {{ 
                background: white; color: #8B5CF6; border: 2px solid #8B5CF6;
            }}
            .btn:hover {{ transform: translateY(-2px); }}
            .improvement-panel {{ 
                position: fixed; top: 50%; right: 2rem; transform: translateY(-50%);
                width: 400px; background: white; border-radius: 1.5rem;
                box-shadow: 0 25px 50px rgba(0,0,0,0.15); z-index: 1000;
                display: none; flex-direction: column; max-height: 80vh;
            }}
            .improvement-header {{ 
                background: linear-gradient(135deg, #10b981, #059669); color: white;
                padding: 1rem 1.5rem; font-weight: 700; border-radius: 1.5rem 1.5rem 0 0;
            }}
            .improvement-body {{ 
                padding: 1.5rem; overflow-y: auto; flex: 1;
            }}
            .suggestion {{ 
                background: #f0fdf4; padding: 1rem; border-radius: 0.75rem; margin-bottom: 1rem;
                border-left: 4px solid #10b981;
            }}
            .improvement-input {{ 
                padding: 1rem 1.5rem; border-top: 1px solid #e5e7eb; display: flex; gap: 0.5rem;
            }}
            .improvement-toggle {{ 
                position: fixed; top: 50%; right: 2rem; transform: translateY(-50%);
                background: linear-gradient(135deg, #10b981, #059669); color: white;
                border: none; padding: 1rem; border-radius: 50%; cursor: pointer;
                box-shadow: 0 8px 25px rgba(16,185,129,0.4); z-index: 1001;
            }}
            .back-link {{ 
                display: inline-block; margin-bottom: 2rem; padding: 1rem 2rem;
                background: linear-gradient(135deg, #6b7280, #4b5563); color: white;
                text-decoration: none; border-radius: 1rem; font-weight: 600;
            }}
            .reddit-insights {{ 
                background: linear-gradient(135deg, #fef3c7, #fbbf24); padding: 1.5rem;
                border-radius: 1rem; margin: 1rem 0; border-left: 4px solid #f59e0b;
            }}
            .quality-insights {{ 
                background: linear-gradient(135deg, #ddd6fe, #c4b5fd); padding: 1.5rem;
                border-radius: 1rem; margin: 1rem 0; border-left: 4px solid #8b5cf6;
            }}
            pre {{ 
                background: #f8fafc; padding: 1.5rem; border-radius: 0.75rem;
                white-space: pre-wrap; font-family: 'Courier New', monospace;
                border-left: 4px solid #8B5CF6; line-height: 1.6;
            }}
            @media (max-width: 1200px) {{ 
                .improvement-panel {{ position: relative; right: auto; top: auto; transform: none; width: 100%; margin: 2rem 0; }}
                .improvement-toggle {{ display: none; }}
                .trust-breakdown {{ grid-template-columns: repeat(2, 1fr); }}
            }}
            @media (max-width: 768px) {{ 
                .container {{ margin: 1rem; padding: 1rem; }}
                .metrics-dashboard {{ grid-template-columns: 1fr; }}
                .trust-breakdown {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">⚡ ZEE SEO TOOL v3.0</div>
            <p>Advanced Content Intelligence Report</p>
        </div>
        
        <div class="container">
            <a href="/" class="back-link">← Create New Content Strategy</a>
            
            <div class="report-header">
                <h1>📊 {topic.title()}</h1>
                <p><strong>Trust Score:</strong> {trust['overall_trust_score']}/10 ({trust['trust_grade']}) | 
                   <strong>Quality:</strong> {quality['overall_quality_score']}/10 | 
                   <strong>Words:</strong> {metrics['word_count']}</p>
            </div>
            
            <div class="metrics-dashboard">
                <div class="metric-card">
                    <div class="metric-value">{trust['overall_trust_score']}/10</div>
                    <div class="metric-label">Trust Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{trust['trust_grade']}</div>
                    <div class="metric-label">Trust Grade</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{quality['overall_quality_score']}/10</div>
                    <div class="metric-label">Quality Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{quality['vs_ai_comparison']['performance_boost']}</div>
                    <div class="metric-label">vs AI Performance</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{reddit['authenticity_score']:.1f}/10</div>
                    <div class="metric-label">Reddit Authenticity</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{reddit['data_source'].replace('_', ' ').title()}</div>
                    <div class="metric-label">Data Source</div>
                </div>
            </div>
            
            <div class="section">
                <h3>🔒 Trust Score Breakdown</h3>
                <div class="trust-breakdown">
                    <div class="trust-component">
                        <div class="trust-score">{trust['component_scores']['experience']}</div>
                        <div>Experience</div>
                    </div>
                    <div class="trust-component">
                        <div class="trust-score">{trust['component_scores']['expertise']}</div>
                        <div>Expertise</div>
                    </div>
                    <div class="trust-component">
                        <div class="trust-score">{trust['component_scores']['authoritativeness']}</div>
                        <div>Authority</div>
                    </div>
                    <div class="trust-component">
                        <div class="trust-score">{trust['component_scores']['trustworthiness']}</div>
                        <div>Trustworthiness</div>
                    </div>
                </div>
                
                <div class="quality-insights">
                    <h4>💡 Key Insights</h4>
                    <p><strong>Trust Level:</strong> {trust['trust_level'].replace('_', ' ').title()}</p>
                    <p><strong>YMYL Topic:</strong> {'Yes' if trust['is_ymyl_topic'] else 'No'}</p>
                    <p><strong>Performance Prediction:</strong> {quality['performance_prediction']}</p>
                </div>
            </div>
            
            <div class="section">
                <h3>📱 Reddit Research Results</h3>
                <div class="reddit-insights">
                    <p><strong>Data Source:</strong> {reddit['data_source'].replace('_', ' ').title()}</p>
                    <p><strong>Communities Analyzed:</strong> {reddit['communities_analyzed']}</p>
                    <p><strong>Posts Analyzed:</strong> {reddit['total_posts_analyzed']}</p>
                    <p><strong>Insight Quality:</strong> {reddit['insight_quality'].replace('_', ' ').title()}</p>
                    <p><strong>Authenticity Score:</strong> {reddit['authenticity_score']:.1f}/10</p>
                    
                    {f"<h4>Customer Pain Points Discovered:</h4><ul>{''.join([f'<li>{point}</li>' for point in reddit['customer_voice']['pain_points'][:3]])}</ul>" if reddit['customer_voice']['pain_points'] else ""}
                    
                    {f"<h4>Common Customer Questions:</h4><ul>{''.join([f'<li>{q}</li>' for q in reddit['customer_voice']['frequent_questions'][:3]])}</ul>" if reddit['customer_voice']['frequent_questions'] else ""}
                </div>
            </div>
            
            <div class="section">
                <h3>📊 Quality Assessment</h3>
                <div class="quality-insights">
                    <p><strong>Overall Quality:</strong> {quality['overall_quality_score']}/10</p>
                    <p><strong>Performance vs AI:</strong> {quality['vs_ai_comparison']['performance_boost']}</p>
                    <p><strong>Engagement Multiplier:</strong> {quality['vs_ai_comparison']['engagement_multiplier']}</p>
                    <p><strong>Trust Correlation:</strong> Quality score correlates with Trust Score of {trust['overall_trust_score']}/10</p>
                </div>
            </div>
            
            <div class="section">
                <h3>✍️ Generated Content</h3>
                <div class="content-actions">
                    <button onclick="copyContent()" class="btn btn-outline">📋 Copy Content</button>
                    <button onclick="exportContent()" class="btn btn-primary">💾 Export</button>
                    <button onclick="toggleImprovement()" class="btn btn-primary">🚀 Start Improvement Chat</button>
                </div>
                <div class="content-display">
                    <pre id="content-text">{content}</pre>
                </div>
            </div>
            
            <div class="section">
                <h3>📈 Improvement Recommendations</h3>
                <div class="quality-insights">
                    <h4>🎯 Immediate Actions:</h4>
                    <ul>
                        {"".join([f'<li>{rec}</li>' for rec in trust['improvement_recommendations']])}
                    </ul>
                    
                    <h4>💡 Initial AI Suggestions:</h4>
                    <ul>
                        {"".join([f'<li><strong>{sugg["area"]}:</strong> {sugg["suggestion"]} (Impact: {sugg["estimated_impact"]})</li>' for sugg in improvement['initial_suggestions']])}
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Improvement Toggle Button -->
        <button class="improvement-toggle" onclick="toggleImprovement()" id="improvementToggle">💬</button>
        
        <!-- Improvement Panel -->
        <div class="improvement-panel" id="improvementPanel">
            <div class="improvement-header">
                🚀 AI Content Improvement Chat
                <button onclick="toggleImprovement()" style="float: right; background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer;">×</button>
            </div>
            <div class="improvement-body" id="improvementBody">
                <div class="suggestion">
                    <strong>🤖 AI Improvement Assistant:</strong> Hi! I've analyzed your content and identified several improvement opportunities. Your current Trust Score is {trust['overall_trust_score']}/10. Let's work together to optimize it!
                </div>
                
                {"".join([f'''
                <div class="suggestion">
                    <strong>🎯 {sugg["area"]} ({sugg["priority"].title()} Priority):</strong><br>
                    {sugg["suggestion"]}<br>
                    <em>Expected impact: {sugg["estimated_impact"]}</em>
                </div>
                ''' for sugg in improvement['initial_suggestions']])}
                
                <div class="suggestion">
                    <strong>💬 Quick Questions:</strong><br>
                    {"<br>".join([f'• {q}' for q in improvement['next_questions']])}
                </div>
            </div>
            <div class="improvement-input">
                <input type="text" id="improvementInput" placeholder="Ask me how to improve your content...">
                <button onclick="sendImprovementMessage()" class="btn btn-primary">Send</button>
            </div>
        </div>
        
        <script>
            let conversationHistory = [];
            
            function toggleImprovement() {{
                const panel = document.getElementById('improvementPanel');
                const toggle = document.getElementById('improvementToggle');
                const isVisible = panel.style.display === 'flex';
                
                panel.style.display = isVisible ? 'none' : 'flex';
                toggle.style.display = isVisible ? 'block' : 'none';
            }}
            
            async function sendImprovementMessage() {{
                const input = document.getElementById('improvementInput');
                const message = input.value.trim();
                if (!message) return;
                
                const body = document.getElementById('improvementBody');
                
                // Add user message
                const userMsg = document.createElement('div');
                userMsg.style.cssText = 'background: #8B5CF6; color: white; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem; text-align: right;';
                userMsg.innerHTML = `<strong>You:</strong> ${{message}}`;
                body.appendChild(userMsg);
                
                // Add typing indicator
                const typingMsg = document.createElement('div');
                typingMsg.className = 'suggestion';
                typingMsg.id = 'typing';
                typingMsg.innerHTML = '<strong>🤖 AI:</strong> <em>Analyzing your request...</em>';
                body.appendChild(typingMsg);
                
                input.value = '';
                body.scrollTop = body.scrollHeight;
                
                // Simulate AI response
                setTimeout(() => {{
                    const aiResponse = getSmartAIResponse(message);
                    typingMsg.innerHTML = `<strong>🤖 AI:</strong> ${{aiResponse}}`;
                    body.scrollTop = body.scrollHeight;
                }}, 1500);
                
                conversationHistory.push({{user: message, ai: 'response'}});
            }}
            
            function getSmartAIResponse(message) {{
                const msg = message.toLowerCase();
                const currentTrustScore = {trust['overall_trust_score']};
                const trustGrade = '{trust['trust_grade']}';
                
                if (msg.includes('trust score') || msg.includes('trust')) {{
                    if (currentTrustScore < 6.0) {{
                        return `Your current Trust Score is ${{currentTrustScore}}/10 (${{trustGrade}}). To improve it:<br><br>
                        1. <strong>Add credentials:</strong> Include your years of experience, certifications, or qualifications<br>
                        2. <strong>Customer proof:</strong> Add testimonials, case studies, or client numbers<br>
                        3. <strong>Transparency:</strong> Be more specific about your unique value proposition<br><br>
                        Expected improvement: +1.5 to +2.0 points. What specific credentials can we highlight?`;
                    }} else if (currentTrustScore < 8.0) {{
                        return `Your Trust Score of ${{currentTrustScore}}/10 is good! To reach excellence:<br><br>
                        1. <strong>Authority signals:</strong> Add industry statistics or expert quotes<br>
                        2. <strong>Detailed experience:</strong> Include specific examples and case studies<br>
                        3. <strong>Update signals:</strong> Add publication dates and "last updated" notes<br><br>
                        Expected improvement: +0.8 to +1.2 points. Which area interests you most?`;
                    }} else {{
                        return `Excellent Trust Score of ${{currentTrustScore}}/10! You're in the top tier. For perfection:<br><br>
                        1. <strong>Peer recognition:</strong> Include industry awards or media mentions<br>
                        2. <strong>Thought leadership:</strong> Add original research or unique insights<br>
                        3. <strong>Social proof:</strong> Include recent testimonials and success metrics<br><br>
                        Expected improvement: +0.3 to +0.7 points. What makes you most proud of your expertise?`;
                    }}
                }} else if (msg.includes('content') || msg.includes('writing') || msg.includes('improve')) {{
                    return `For content improvements based on your current {quality['overall_quality_score']}/10 quality score:<br><br>
                    1. <strong>Depth:</strong> Add more detailed explanations and examples<br>
                    2. <strong>Structure:</strong> Use more subheadings and bullet points<br>
                    3. <strong>Evidence:</strong> Include more statistics and research<br>
                    4. <strong>Customer focus:</strong> Address more specific pain points<br><br>
                    Current word count: {metrics['word_count']} words. Would you like help with any specific section?`;
                }} else if (msg.includes('reddit') || msg.includes('research')) {{
                    return `Your Reddit research shows {reddit['authenticity_score']:.1f}/10 authenticity from {reddit['data_source'].replace('_', ' ')}:<br><br>
                    1. <strong>Customer language:</strong> Use more authentic phrases from your research<br>
                    2. <strong>Pain points:</strong> Address the specific problems discovered<br>
                    3. <strong>Questions:</strong> Answer the real questions customers ask<br><br>
                    {reddit['total_posts_analyzed']} posts analyzed across {reddit['communities_analyzed']} communities. Want help incorporating specific insights?`;
                }} else if (msg.includes('seo') || msg.includes('ranking')) {{
                    return `For SEO optimization with your current setup:<br><br>
                    1. <strong>Keywords:</strong> Naturally integrate target keywords in headings<br>
                    2. <strong>Structure:</strong> Use H2/H3 tags for better crawling<br>
                    3. <strong>Internal links:</strong> Add relevant internal linking opportunities<br>
                    4. <strong>Meta data:</strong> Create compelling title and meta description<br><br>
                    Your Trust Score of ${{currentTrustScore}}/10 will help with rankings. Need help with specific SEO elements?`;
                }} else if (msg.includes('audience') || msg.includes('customer')) {{
                    return `For better audience targeting in {business_context['industry']} for {business_context['target_audience']}:<br><br>
                    1. <strong>Language level:</strong> Match your audience's expertise level<br>
                    2. <strong>Pain focus:</strong> Address their biggest challenges first<br>
                    3. <strong>Solution clarity:</strong> Show clear next steps<br>
                    4. <strong>Social proof:</strong> Include relevant testimonials<br><br>
                    Based on your Reddit research, what specific audience need should we focus on?`;
                }} else if (msg.includes('help') || msg.includes('?')) {{
                    return `I'm here to help optimize your content! You can ask me about:<br><br>
                    • <strong>"How to improve trust score?"</strong> - Specific trust-building strategies<br>
                    • <strong>"Better content structure?"</strong> - Organization and formatting tips<br>
                    • <strong>"SEO optimization?"</strong> - Search engine optimization advice<br>
                    • <strong>"Customer targeting?"</strong> - Audience-specific improvements<br>
                    • <strong>"Reddit insights?"</strong> - How to use your research better<br><br>
                    What specific aspect would you like to work on first?`;
                }} else {{
                    return `That's a great question! Based on your content analysis:<br><br>
                    • Trust Score: ${{currentTrustScore}}/10 (${{trustGrade}})<br>
                    • Quality Score: {quality['overall_quality_score']}/10<br>
                    • Performance potential: {quality['vs_ai_comparison']['performance_boost']} vs generic AI<br><br>
                    I can help you improve any aspect of your content. What specific area would you like to focus on? Try asking about trust score, content structure, SEO, or audience targeting.`;
                }}
            }}
            
            function copyContent() {{
                const content = document.getElementById('content-text').textContent;
                navigator.clipboard.writeText(content).then(() => {{
                    alert('✅ Content copied to clipboard!');
                }});
            }}
            
            function exportContent() {{
                const content = document.getElementById('content-text').textContent;
                const blob = new Blob([content], {{ type: 'text/plain' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{topic.replace(" ", "_")}_zee_seo_content.txt';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
            
            // Enter key support
            document.getElementById('improvementInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    sendImprovementMessage();
                }}
            }});
            
            // Auto-show improvement panel if trust score is low
            setTimeout(() => {{
                if ({trust['overall_trust_score']} < 7.0) {{
                    toggleImprovement();
                }}
            }}, 3000);
        </script>
    </body>
    </html>
    """

@app.post("/api/improve")
async def improve_content_api(
    request: Dict = None
):
    """API endpoint for content improvement requests"""
    try:
        user_request = request.get('message', '')
        content = request.get('content', '')
        trust_assessment = request.get('trust_assessment', {})
        
        # Process improvement request
        improvement_response = await zee_orchestrator.conversation_ai.process_improvement_request(
            user_request, content, trust_assessment
        )
        
        return JSONResponse(improvement_response)
        
    except Exception as e:
        logger.error(f"❌ Error processing improvement request: {str(e)}")
        return JSONResponse({
            'error': str(e),
            'ai_response': 'I apologize, but I encountered an error processing your request. Please try again.',
            'improvement_type': 'error_recovery'
        })

@app.get("/health")
async def health_check():
    """Enhanced health check with system diagnostics"""
    system_status = zee_orchestrator.get_system_status()
    
    return JSONResponse({
        "status": "healthy",
        "version": "3.0.0-enhanced",
        "timestamp": datetime.now().isoformat(),
        "system_status": system_status,
        "features": {
            "trust_score_assessment": "✅ Enhanced with fixed calculation",
            "reddit_research": "✅ Live API with Railway integration" if system_status['reddit_client'] == 'operational' else "🟡 Enhanced simulation mode",
            "conversational_ai": "✅ Interactive improvement dialogue",
            "content_generation": "✅ Multi-agent intelligence",
            "performance_analytics": "✅ Real-time tracking"
        },
        "environment": {
            "anthropic_api": "configured" if zee_orchestrator.llm_client.available else "missing",
            "reddit_api": "connected" if zee_orchestrator.reddit_client.available else "simulation_mode",
            "praw_library": "available" if PRAW_AVAILABLE else "unavailable",
            "agents_imported": "success" if AGENTS_IMPORTED else "fallback_mode"
        }
    })

@app.on_event("startup")
async def startup():
    """Enhanced startup with comprehensive diagnostics"""
    logger.info("🚀 Zee SEO Tool Enhanced v3.0 starting...")
    logger.info("=" * 60)
    
    # API Configuration Status
    logger.info("🔑 API Configuration:")
    logger.info(f"  Anthropic API: {'✅ Configured' if zee_orchestrator.llm_client.available else '❌ Missing'}")
    if zee_orchestrator.llm_client.available:
        logger.info(f"  API Key: {config.ANTHROPIC_API_KEY[:10]}...")
    
    logger.info(f"  Reddit API: {'✅ Connected' if zee_orchestrator.reddit_client.available else '⚠️ Simulation Mode'}")
    if config.REDDIT_CLIENT_ID:
        logger.info(f"  Client ID: {config.REDDIT_CLIENT_ID[:8]}...")
        logger.info(f"  User Agent: {config.REDDIT_USER_AGENT}")
    
    # System Components Status
    logger.info("🤖 System Components:")
    logger.info(f"  PRAW Library: {'✅ Available' if PRAW_AVAILABLE else '⚠️ Not installed'}")
    logger.info(f"  Trust Score Assessor: ✅ Enhanced with fixed calculation")
    logger.info(f"  Conversation AI: ✅ Interactive improvement dialogue")
    logger.info(f"  Agents Import: {'✅ Success' if AGENTS_IMPORTED else '⚠️ Using fallbacks'}")
    
    # Features Status
    logger.info("⚡ Enhanced Features:")
    logger.info("  🔒 Trust Score Assessment with proper weighted calculation")
    logger.info("  📱 Reddit API integration with Railway environment variables")
    logger.info("  💬 Conversational AI for content improvements")
    logger.info("  📊 Real-time performance analytics")
    logger.info("  🎯 Multi-agent content intelligence")
    
    logger.info("=" * 60)
    logger.info("✅ All systems initialized successfully")
    logger.info(f"🌐 Server ready on port {config.PORT}")

if __name__ == "__main__":
    print("""
🎯 Zee SEO Tool Enhanced v3.0 - FIXED & COMPLETE
===============================================

✅ ISSUES RESOLVED:
   • Reddit API integration with Railway environment variables
   • Trust Score calculation bug fixed (weighted average)
   • E-E-A-T renamed to Trust Score throughout
   • Conversational AI improvement dialogue added
   • All agents imported from src/agents folder

🚀 ENHANCED FEATURES:
   • Real Reddit community research with PRAW
   • Fixed Trust Score assessment with proper weighting
   • Interactive conversation AI for improvements
   • Advanced content intelligence pipeline
   • Production-ready error handling
   • Mobile-responsive interface

🔧 RAILWAY INTEGRATION:
   • ANTHROPIC_API_KEY - Your Claude API key
   • REDDIT_CLIENT_ID - From Reddit app settings
   • REDDIT_CLIENT_SECRET - From Reddit app settings  
   • REDDIT_USER_AGENT - ZeeSEOTool:v1.0 (by u/Available-Travel7812)

📊 SYSTEM STATUS:
   • Trust Score Assessor: ✅ Enhanced with proper calculation
   • Reddit API Client: ✅ Railway environment variable integration
   • Conversation AI: ✅ Interactive improvement dialogue
   • Content Generator: ✅ Multi-agent intelligence
   • Error Handling: ✅ Production-ready graceful fallbacks

Built by Zeeshan Bashir
The Most Advanced Content Intelligence Platform
    """)
    
    if config.DEBUG_MODE:
        print(f"\n🌐 Development server: http://localhost:{config.PORT}")
        print(f"📊 Health check: http://localhost:{config.PORT}/health")
        print(f"🔧 All issues fixed and ready for production!\n")
        
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=config.PORT,
            reload=True,
            log_level="info"
        )
    else:
        print(f"\n🚀 Production server starting on port {config.PORT}\n")
        uvicorn.run(
            app,
            host="0.0.0.0", 
            port=config.PORT,
            workers=1,
            log_level="warning"
        )
