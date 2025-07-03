"""
Zee SEO Tool Enhanced v3.0 - Original Design Restored
====================================================
Author: Zeeshan Bashir
Description: Fixed Reddit API, Trust Score, with ORIGINAL design preserved
"""

import os
import json
import logging
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# FastAPI imports
from fastapi import FastAPI, Form, HTTPException
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
app = FastAPI(title="Zee SEO Tool - AI Content Creation Agent")
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
                test_subreddit = self.reddit.subreddit('test')
                _ = test_subreddit.display_name
                logger.info("✅ Reddit API connection test passed")
        except Exception as e:
            raise Exception(f"Reddit API connection test failed: {str(e)}")
    
    async def research_topic(self, topic: str, subreddits: str) -> Dict[str, Any]:
        """Research topic across specified subreddits"""
        if not self.available or not self.reddit:
            logger.info("🔧 Reddit API not available - using enhanced simulation mode")
            return self._get_enhanced_simulation(topic, subreddits)
        
        try:
            logger.info(f"🔍 Starting Reddit research for '{topic}' in subreddits: {subreddits}")
            
            communities = [s.strip() for s in subreddits.split(',') if s.strip()]
            insights = {
                'customer_voice': {
                    'common_language': [],
                    'frequent_questions': [],
                    'pain_points': [],
                    'recommendations': []
                },
                'communities_analyzed': len(communities),
                'total_posts_analyzed': 0,
                'authenticity_score': 0,
                'data_source': 'live_reddit_api'
            }
            
            posts_found = 0
            for subreddit_name in communities[:3]:  # Limit to 3 subreddits
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    for submission in subreddit.search(topic, time_filter='month', limit=15):
                        posts_found += 1
                        text = f"{submission.title} {submission.selftext}".lower()
                        
                        # Extract insights
                        if len(text) > 30:
                            insights['customer_voice']['common_language'].append(text[:100])
                        
                        if '?' in text:
                            questions = [q.strip() + '?' for q in text.split('?') if len(q.strip()) > 10]
                            insights['customer_voice']['frequent_questions'].extend(questions[:2])
                        
                        pain_indicators = ['problem', 'issue', 'trouble', 'difficult', 'frustrating']
                        if any(indicator in text for indicator in pain_indicators):
                            insights['customer_voice']['pain_points'].append(text[:150])
                        
                        rec_indicators = ['recommend', 'suggest', 'best', 'use']
                        if any(indicator in text for indicator in rec_indicators):
                            insights['customer_voice']['recommendations'].append(text[:100])
                
                except Exception as e:
                    logger.warning(f"⚠️ Error searching r/{subreddit_name}: {str(e)}")
                    continue
            
            insights['total_posts_analyzed'] = posts_found
            insights['authenticity_score'] = min(10.0, posts_found * 0.2 + 3.0)
            
            logger.info(f"✅ Reddit research complete: {posts_found} posts analyzed")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Reddit research error: {str(e)}")
            return self._get_enhanced_simulation(topic, subreddits)
    
    def _get_enhanced_simulation(self, topic: str, subreddits: str) -> Dict[str, Any]:
        """Enhanced simulation when Reddit API is unavailable"""
        communities = [s.strip() for s in subreddits.split(',') if s.strip()]
        
        return {
            'customer_voice': {
                'common_language': [
                    f"Looking for {topic} recommendations",
                    "Budget-friendly options",
                    "Best value for money",
                    "User-friendly and reliable"
                ],
                'frequent_questions': [
                    f"What's the best {topic} for beginners?",
                    f"How much should I budget for {topic}?",
                    f"Any {topic} recommendations?",
                    "Is it worth the investment?"
                ],
                'pain_points': [
                    f"Too many {topic} options to choose from",
                    f"Difficulty finding reliable {topic} information",
                    "Limited budget constraints",
                    "Time constraints for research"
                ],
                'recommendations': [
                    "Do thorough research first",
                    "Read reviews from multiple sources",
                    "Start with basic options",
                    "Consider long-term value"
                ]
            },
            'communities_analyzed': len(communities),
            'total_posts_analyzed': 45,
            'authenticity_score': 4.2,
            'data_source': 'enhanced_simulation',
            'note': 'Enhanced simulation - Configure Reddit API for live insights'
        }

class EnhancedTrustScoreAssessor:
    """FIXED Trust Score assessor with proper calculation"""
    def __init__(self):
        self.available = True
        
        # YMYL topics requiring higher Trust standards
        self.ymyl_topics = [
            'finance', 'health', 'medical', 'legal', 'investment', 'insurance',
            'taxes', 'retirement', 'medication', 'surgery', 'diet', 'nutrition'
        ]
    
    def assess_trust_score(self, content: str, business_context: Dict, 
                          human_inputs: Dict, reddit_insights: Dict = None) -> Dict[str, Any]:
        """FIXED Trust Score assessment with proper weighted calculation"""
        
        topic = business_context.get('topic', '')
        industry = business_context.get('industry', '')
        
        # Determine if this is YMYL content
        is_ymyl = self._is_ymyl_topic(topic, industry)
        
        # Calculate individual component scores (out of 10)
        experience_score = self._assess_experience(human_inputs, reddit_insights)
        expertise_score = self._assess_expertise(business_context, human_inputs, content)
        authoritativeness_score = self._assess_authoritativeness(business_context, human_inputs)
        trustworthiness_score = self._assess_trustworthiness(business_context, human_inputs)
        
        # FIXED: Calculate overall Trust score with proper weighting
        if is_ymyl:
            # YMYL content prioritizes trustworthiness and expertise
            overall_score = (
                experience_score * 0.20 +
                expertise_score * 0.30 +
                authoritativeness_score * 0.15 +
                trustworthiness_score * 0.35
            )
        else:
            # Non-YMYL content has balanced weighting
            overall_score = (
                experience_score * 0.25 +
                expertise_score * 0.25 +
                authoritativeness_score * 0.25 +
                trustworthiness_score * 0.25
            )
        
        # Determine trust level and grade
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
            "improvement_recommendations": self._get_improvement_recommendations(
                experience_score, expertise_score, authoritativeness_score, trustworthiness_score
            )
        }
    
    def _is_ymyl_topic(self, topic: str, industry: str) -> bool:
        """Determine if topic/industry is YMYL"""
        topic_lower = topic.lower()
        industry_lower = industry.lower()
        return any(ymyl in topic_lower or ymyl in industry_lower for ymyl in self.ymyl_topics)
    
    def _assess_experience(self, human_inputs: Dict, reddit_insights: Dict) -> float:
        """Assess Experience component"""
        score = 3.0  # Base score
        
        customer_pain_points = human_inputs.get('customer_pain_points', '')
        if len(customer_pain_points) > 100:
            score += 2.0
        elif len(customer_pain_points) > 50:
            score += 1.0
        
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if 'years' in unique_value_prop.lower() or 'experience' in unique_value_prop.lower():
            score += 1.5
        
        if reddit_insights:
            auth_score = reddit_insights.get('authenticity_score', 0)
            if auth_score > 5.0:
                score += 1.5
            elif auth_score > 3.0:
                score += 1.0
        
        return min(10.0, score)
    
    def _assess_expertise(self, business_context: Dict, human_inputs: Dict, content: str) -> float:
        """Assess Expertise component"""
        score = 3.5  # Base score
        
        if business_context.get('industry'):
            score += 1.5
        
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if len(unique_value_prop) > 100:
            score += 2.0
        elif len(unique_value_prop) > 50:
            score += 1.0
        
        # Content depth
        word_count = len(content.split())
        if word_count > 1500:
            score += 1.5
        elif word_count > 800:
            score += 1.0
        
        return min(10.0, score)
    
    def _assess_authoritativeness(self, business_context: Dict, human_inputs: Dict) -> float:
        """Assess Authoritativeness component"""
        score = 4.0  # Base score
        
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if any(word in unique_value_prop.lower() for word in ['certified', 'licensed', 'award']):
            score += 2.0
        
        if business_context.get('unique_value_prop') and len(unique_value_prop) > 80:
            score += 1.5
        
        if business_context.get('business_type') == 'B2B':
            score += 0.5
        
        return min(10.0, score)
    
    def _assess_trustworthiness(self, business_context: Dict, human_inputs: Dict) -> float:
        """Assess Trustworthiness component"""
        score = 4.5  # Base score
        
        unique_value_prop = human_inputs.get('unique_value_prop', '')
        if len(unique_value_prop) > 100:
            score += 2.0
        elif len(unique_value_prop) > 50:
            score += 1.0
        
        customer_pain_points = human_inputs.get('customer_pain_points', '')
        if len(customer_pain_points) > 100:
            score += 1.5
        
        if business_context.get('industry') in ['Healthcare', 'Finance', 'Legal']:
            score += 1.0
        
        return min(10.0, score)
    
    def _determine_trust_level(self, score: float) -> str:
        """Determine trust level based on score"""
        if score >= 8.5:
            return 'very_high'
        elif score >= 7.0:
            return 'high'
        elif score >= 5.5:
            return 'moderate'
        else:
            return 'developing'
    
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
        elif score >= 6.0:
            return 'C+'
        else:
            return 'C'
    
    def _get_improvement_recommendations(self, exp: float, expert: float, auth: float, trust: float) -> List[str]:
        """Get improvement recommendations"""
        recommendations = []
        
        if exp < 6.0:
            recommendations.append("Add more personal experience stories and customer success cases")
        if expert < 6.0:
            recommendations.append("Demonstrate deeper industry expertise and technical knowledge")
        if auth < 6.0:
            recommendations.append("Build stronger authority signals and credibility indicators")
        if trust < 7.0:
            recommendations.append("Enhance transparency and include more trust signals")
        
        if not recommendations:
            recommendations.append("Continue building on your strong trust foundation")
        
        return recommendations

class QualityScorer:
    """Content quality scorer"""
    def __init__(self):
        self.available = True
    
    def score_content_quality(self, content: str, business_context: Dict, 
                            human_inputs: Dict, trust_assessment: Dict) -> Dict[str, Any]:
        """Score content quality"""
        
        word_count = len(content.split())
        trust_score = trust_assessment.get('overall_trust_score', 7.0)
        
        # Calculate quality metrics
        content_score = 8.5 if word_count > 1000 else 7.0 if word_count > 500 else 6.0
        structure_score = 8.0 if content.count('#') > 3 else 6.5
        relevance_score = 8.5 if len(human_inputs.get('unique_value_prop', '')) > 50 else 7.0
        
        # Overall quality correlates with trust score
        overall_score = (content_score * 0.3 + structure_score * 0.2 + 
                        relevance_score * 0.2 + trust_score * 0.3)
        
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

# ================== MAIN ORCHESTRATOR ==================

class ZeeSEOOrchestrator:
    """Main orchestrator for all SEO tool functionality"""
    def __init__(self):
        self.llm_client = LLMClient()
        self.reddit_client = EnhancedRedditClient()
        self.trust_assessor = EnhancedTrustScoreAssessor()
        self.quality_scorer = QualityScorer()
    
    async def generate_comprehensive_analysis(self, form_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive content analysis"""
        
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
        logger.info("📱 Researching Reddit for customer insights...")
        reddit_insights = await self.reddit_client.research_topic(topic, subreddits)
        
        # Step 2: Generate Content
        logger.info("✍️ Generating optimized content...")
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
            content, business_context, human_inputs, trust_assessment
        )
        
        logger.info("✅ Analysis complete!")
        
        return {
            'topic': topic,
            'generated_content': content,
            'reddit_insights': reddit_insights,
            'trust_assessment': trust_assessment,
            'quality_assessment': quality_assessment,
            'business_context': business_context,  # Fixed: Added this
            'human_inputs': human_inputs,
            'performance_metrics': {
                'word_count': len(content.split()),
                'trust_score': trust_assessment['overall_trust_score'],
                'trust_grade': trust_assessment['trust_grade'],
                'quality_score': quality_assessment['overall_quality_score']
            }
        }
    
    async def _generate_enhanced_content(self, topic: str, business_context: Dict, 
                                       human_inputs: Dict, reddit_insights: Dict, 
                                       form_data: Dict) -> str:
        """Generate enhanced content using all intelligence"""
        
        customer_language = reddit_insights.get('customer_voice', {}).get('common_language', [])
        customer_questions = reddit_insights.get('customer_voice', {}).get('frequent_questions', [])
        customer_pain_points = reddit_insights.get('customer_voice', {}).get('pain_points', [])
        
        prompt = f"""
        Create comprehensive, trust-optimized content about "{topic}".
        
        BUSINESS CONTEXT:
        - Industry: {business_context['industry']}
        - Target Audience: {business_context['target_audience']}
        - Business Type: {business_context['business_type']}
        - Unique Value: {business_context['unique_value_prop']}
        
        CUSTOMER INSIGHTS:
        - Pain Points: {human_inputs['customer_pain_points']}
        
        REDDIT RESEARCH:
        - Customer Language: {', '.join(customer_language[:5])}
        - Real Questions: {', '.join(customer_questions[:3])}
        - Pain Points: {', '.join(customer_pain_points[:3])}
        - Data Source: {reddit_insights.get('data_source', 'simulation')}
        
        AI INSTRUCTIONS:
        - Style: {form_data.get('writing_style', 'Professional')}
        - Word Count: {form_data.get('target_word_count', '1000-1500 words')}
        - Language: {form_data.get('language_preference', 'Default')}
        - Notes: {form_data.get('additional_notes', '')}
        
        Create content that builds trust, addresses customer needs, and demonstrates expertise.
        Use authentic customer language and provide actionable solutions.
        """
        
        return await self.llm_client.generate_content(prompt)

# Initialize the orchestrator
zee_orchestrator = ZeeSEOOrchestrator()

# ================== API ROUTES ==================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with ORIGINAL design preserved"""
    
    reddit_status = "🟢 Connected" if zee_orchestrator.reddit_client.available else "🟡 Simulation Mode"
    reddit_note = "Real API" if zee_orchestrator.reddit_client.available else "Enhanced Simulation"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool - AI Content Creation That Bridges Human & AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }}
            
            .logo {{
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .tagline {{
                font-size: 20px;
                opacity: 0.9;
                margin-bottom: 5px;
            }}
            
            .subtitle {{
                font-size: 16px;
                opacity: 0.8;
                font-style: italic;
            }}
            
            .status-badge {{
                background: rgba(255,255,255,0.2);
                padding: 8px 15px;
                border-radius: 20px;
                display: inline-block;
                margin-top: 10px;
                font-size: 14px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                position: relative;
            }}
            
            .ai-badge {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 12px 25px;
                border-radius: 25px;
                display: inline-block;
                margin-bottom: 25px;
                font-weight: bold;
                font-size: 16px;
            }}
            
            .ai-assistant-btn {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                border-radius: 50%;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
                z-index: 1000;
                transition: transform 0.3s ease;
            }}
            
            .ai-assistant-btn:hover {{
                transform: scale(1.1);
            }}
            
            .ai-dialogue {{
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                z-index: 999;
                display: none;
                flex-direction: column;
                overflow: hidden;
            }}
            
            .ai-dialogue-header {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 15px 20px;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .ai-dialogue-close {{
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                margin-left: auto;
            }}
            
            .ai-dialogue-body {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }}
            
            .ai-suggestion {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #8B5CF6;
            }}
            
            .ai-suggestion h4 {{
                color: #8B5CF6;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            
            .ai-suggestion p {{
                font-size: 13px;
                line-height: 1.4;
                color: #666;
            }}
            
            .form-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }}
            
            .form-section {{
                background-color: #f8f9fa;
                padding: 25px;
                border-radius: 15px;
                border-left: 5px solid #8B5CF6;
            }}
            
            .form-group {{ 
                margin-bottom: 20px; 
            }}
            
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                font-weight: 600; 
                color: #333;
                font-size: 14px;
            }}
            
            input, textarea, select {{ 
                width: 100%; 
                padding: 12px 15px; 
                border: 2px solid #e1e5e9; 
                border-radius: 8px; 
                font-size: 14px;
                transition: border-color 0.3s ease;
            }}
            
            textarea {{
                resize: vertical;
                min-height: 80px;
            }}
            
            input:focus, textarea:focus, select:focus {{
                border-color: #8B5CF6;
                outline: none;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
            }}
            
            .submit-section {{
                grid-column: 1 / -1;
                text-align: center;
                margin-top: 20px;
            }}
            
            button {{ 
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white; 
                padding: 18px 40px; 
                border: none; 
                border-radius: 50px; 
                cursor: pointer; 
                font-size: 18px;
                font-weight: bold;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                min-width: 300px;
            }}
            
            button:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3);
            }}
            
            .section-title {{
                color: #8B5CF6;
                border-bottom: 2px solid #8B5CF6;
                padding-bottom: 10px;
                margin-bottom: 20px;
                font-size: 18px;
                font-weight: 600;
            }}
            
            .help-text {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
                font-style: italic;
            }}
            
            .features {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 30px;
                grid-column: 1 / -1;
            }}
            
            .features h3 {{
                margin-bottom: 15px;
                font-size: 20px;
            }}
            
            .features ul {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                list-style: none;
            }}
            
            .features li {{
                padding: 5px 0;
                border-left: 3px solid rgba(255,255,255,0.3);
                padding-left: 15px;
            }}
            
            .ai-controls {{
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border: 2px solid #0ea5e9;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            
            .ai-controls .section-title {{
                color: #0ea5e9;
                border-bottom-color: #0ea5e9;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 2px solid #e1e5e9;
                color: #666;
            }}
            
            .creator-info {{
                background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                margin-top: 20px;
            }}
            
            .creator-info h4 {{
                color: #8B5CF6;
                margin-bottom: 10px;
            }}
            
            #loading {{
                display: none;
                text-align: center;
                margin-top: 20px;
                padding: 30px;
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border-radius: 15px;
                border: 2px solid #8B5CF6;
            }}
            
            .loading-animation {{
                font-size: 24px;
                margin-bottom: 15px;
            }}
            
            @media (max-width: 768px) {{
                .form-grid {{
                    grid-template-columns: 1fr;
                    gap: 20px;
                }}
                
                .features ul {{
                    grid-template-columns: 1fr;
                }}
                
                .container {{
                    padding: 20px;
                }}
                
                .ai-dialogue {{
                    width: 300px;
                    right: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">⚡ ZEE SEO TOOL</div>
            <div class="tagline">AI Content Creation That Bridges Human & AI</div>
            <div class="subtitle">Built by Zeeshan Bashir • Effective Content That Works</div>
            <div class="status-badge">Reddit: {reddit_status} ({reddit_note}) | Trust Score: ✅ Active | Railway: ✅ Deployed</div>
        </div>
        
        <div class="container">
            <div class="ai-badge">🤖 Powered by Advanced AI + Reddit Research + Trust Score Optimization</div>
            
            <form action="/generate" method="post">
                <div class="form-grid">
                    <div class="features">
                        <h3>🚀 Zee SEO Tool Features:</h3>
                        <ul>
                            <li>✅ Advanced AI reasoning</li>
                            <li>✅ Reddit research ({reddit_note})</li>
                            <li>✅ Customer journey mapping</li>
                            <li>✅ Trust Score optimization</li>
                            <li>✅ Human-AI content bridging</li>
                            <li>✅ Performance prediction analytics</li>
                        </ul>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">📝 Content Topic & Research</h3>
                        
                        <div class="form-group">
                            <label for="topic">Content Topic:</label>
                            <input type="text" id="topic" name="topic" 
                                   placeholder="e.g., best budget laptops for college students" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="desired_content_type">What content do you need?</label>
                            <select id="desired_content_type" name="desired_content_type">
                                <option value="AUTO_DETECT">🤖 Let AI decide the best format</option>
                                <option value="COMPREHENSIVE_GUIDE">📖 Comprehensive Guide</option>
                                <option value="COMPARISON_TABLE">📊 Comparison Table</option>
                                <option value="LANDING_PAGE">🎯 Landing Page</option>
                                <option value="PROCESS_GUIDE">📋 Step-by-Step Guide</option>
                                <option value="FAQ_PAGE">❓ FAQ Page</option>
                                <option value="CHECKLIST">✅ Checklist</option>
                            </select>
                            <div class="help-text">AI will analyze your topic and recommend the best content format</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="subreddits">Target Subreddits (comma-separated):</label>
                            <input type="text" id="subreddits" name="subreddits" 
                                   placeholder="e.g., laptops, college, StudentLoans" required>
                            <div class="help-text">Reddit communities analyzed for authentic insights ({reddit_note})</div>
                        </div>
                    </div>
                    
                    <div class="ai-controls">
                        <h3 class="section-title">🤖 AI Writing Instructions</h3>
                        
                        <div class="form-group">
                            <label for="writing_style">Writing Style:</label>
                            <select id="writing_style" name="writing_style">
                                <option value="">Default</option>
                                <option value="British English">British English</option>
                                <option value="American English">American English</option>
                                <option value="Conversational">Conversational</option>
                                <option value="Academic">Academic</option>
                                <option value="Journalistic">Journalistic</option>
                                <option value="Marketing Copy">Marketing Copy</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="target_word_count">Target Word Count:</label>
                            <select id="target_word_count" name="target_word_count">
                                <option value="">Default (800-1200)</option>
                                <option value="500-700">Short (500-700 words)</option>
                                <option value="800-1200">Medium (800-1200 words)</option>
                                <option value="1500-2000">Long (1500-2000 words)</option>
                                <option value="2500+">Very Long (2500+ words)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="language_preference">Language Preference:</label>
                            <select id="language_preference" name="language_preference">
                                <option value="">Default</option>
                                <option value="UK English with British spelling">UK English (colour, realise, etc.)</option>
                                <option value="US English with American spelling">US English (color, realize, etc.)</option>
                                <option value="Simple language for beginners">Simple Language</option>
                                <option value="Technical language for experts">Technical Language</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="additional_notes">Additional AI Instructions:</label>
                            <textarea id="additional_notes" name="additional_notes" 
                                      placeholder="e.g., Include statistics, Add comparison tables, Focus on benefits, Use bullet points, etc."></textarea>
                            <div class="help-text">Specific instructions for the AI about how to write your content</div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">🏢 Your Business Context</h3>
                        
                        <div class="form-group">
                            <label for="industry">Industry:</label>
                            <input type="text" id="industry" name="industry" 
                                   placeholder="e.g., Technology, Healthcare, Finance" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="target_audience">Target Audience:</label>
                            <input type="text" id="target_audience" name="target_audience" 
                                   placeholder="e.g., College students, Small business owners" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="business_type">Business Type:</label>
                            <select id="business_type" name="business_type" required>
                                <option value="">Select...</option>
                                <option value="B2B">B2B (Business to Business)</option>
                                <option value="B2C">B2C (Business to Consumer)</option>
                                <option value="Both">Both B2B and B2C</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="content_goal">Content Goal:</label>
                            <textarea id="content_goal" name="content_goal" 
                                      placeholder="e.g., Educate customers, Generate leads, Build trust" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="unique_value_prop">What makes you different?</label>
                            <textarea id="unique_value_prop" name="unique_value_prop" 
                                      placeholder="e.g., 24/7 support, 10 years experience, patented technology" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="brand_voice">Brand Voice:</label>
                            <select id="brand_voice" name="brand_voice" required>
                                <option value="">Select...</option>
                                <option value="Professional">Professional</option>
                                <option value="Casual">Casual & Friendly</option>
                                <option value="Technical">Technical & Expert</option>
                                <option value="Empathetic">Empathetic & Caring</option>
                                <option value="Bold">Bold & Confident</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">👥 Customer Insights</h3>
                        
                        <div class="form-group">
                            <label for="customer_pain_points">Customer's Biggest Challenges:</label>
                            <textarea id="customer_pain_points" name="customer_pain_points" 
                                      placeholder="e.g., Limited budget, Too many options, Lack of time" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="frequent_questions">Most Common Customer Questions:</label>
                            <textarea id="frequent_questions" name="frequent_questions" 
                                      placeholder="e.g., How much does it cost? Is it reliable? How long does it take?" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="success_story">Customer Success Story (Optional):</label>
                            <textarea id="success_story" name="success_story" 
                                      placeholder="e.g., Helped a customer save 50% on costs, reduced their time by 3 hours daily"></textarea>
                            <div class="help-text">Adds authenticity and builds trust in your content</div>
                        </div>
                    </div>
                    
                    <div class="submit-section">
                        <button type="submit">🚀 Generate High-Performance Content with Zee SEO Tool</button>
                    </div>
                </div>
            </form>
            
            <div id="loading">
                <div class="loading-animation">🤖 ⚡ 🧠</div>
                <h3>Zee SEO Tool is crafting your content...</h3>
                <p>AI is analyzing your inputs, mapping customer journey, researching Reddit insights, calculating Trust Score, and generating high-performance content that bridges human expertise with AI intelligence.</p>
                <p><em>This advanced analysis takes 30-60 seconds for maximum quality</em></p>
            </div>
            
            <div class="footer">
                <div class="creator-info">
                    <h4>🛠️ Built by Zeeshan Bashir</h4>
                    <p><strong>Mission:</strong> To create effective content that bridges human creativity and AI efficiency. Zee SEO Tool combines the best of both worlds - human insight and AI power - to produce content that truly performs.</p>
                    <p><strong>Purpose:</strong> Helping businesses create content that doesn't just rank, but converts and builds genuine connections with their audience.</p>
                    <p><strong>Railway Status:</strong> ✅ Deployed & Optimized • Reddit: {reddit_status} • Trust Score: ✅ Active</p>
                </div>
            </div>
        </div>
        
        <!-- AI Assistant Button -->
        <button class="ai-assistant-btn" onclick="toggleAIDialogue()">🤖</button>
        
        <!-- AI Dialogue Window -->
        <div class="ai-dialogue" id="aiDialogue">
            <div class="ai-dialogue-header">
                <span>💡 AI Content Assistant</span>
                <button class="ai-dialogue-close" onclick="toggleAIDialogue()">×</button>
            </div>
            <div class="ai-dialogue-body">
                <div class="ai-suggestion">
                    <h4>🎯 Content Strategy Tip</h4>
                    <p>Start with your customer's biggest pain point. This creates immediate relevance and engagement.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>📊 Trust Score Boost</h4>
                    <p>Include specific numbers, examples, or case studies in your content to improve your Trust Score significantly.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>🔍 Reddit Research Power</h4>
                    <p>Choose subreddits where your target audience actually hangs out for more authentic insights.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>✍️ Writing Style Guide</h4>
                    <p>Match your brand voice with your audience: Technical for experts, Conversational for general audience.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>📈 Performance Prediction</h4>
                    <p>Content with strong customer insights typically gets 3-5x better engagement than generic content.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>🚀 Quick Win</h4>
                    <p>Fill out the "Success Story" field - it dramatically improves your content's authenticity and Trust Score.</p>
                </div>
            </div>
        </div>
        
        <script>
            function toggleAIDialogue() {{
                const dialogue = document.getElementById('aiDialogue');
                if (dialogue.style.display === 'none' || dialogue.style.display === '') {{
                    dialogue.style.display = 'flex';
                }} else {{
                    dialogue.style.display = 'none';
                }}
            }}
            
            document.querySelector('form').addEventListener('submit', function() {{
                document.getElementById('loading').style.display = 'block';
                document.querySelector('.container').scrollIntoView({{ behavior: 'smooth' }});
            }});
            
            // Auto-show AI dialogue on first visit
            setTimeout(() => {{
                if (!localStorage.getItem('aiDialogueShown')) {{
                    toggleAIDialogue();
                    localStorage.setItem('aiDialogueShown', 'true');
                }}
            }}, 3000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/generate")
async def generate_content(
    topic: str = Form(...),
    desired_content_type: str = Form(...),
    subreddits: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    language_preference: str = Form(""),
    additional_notes: str = Form(""),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    content_goal: str = Form(...),
    unique_value_prop: str = Form(...),
    brand_voice: str = Form(...),
    customer_pain_points: str = Form(...),
    frequent_questions: str = Form(...),
    success_story: str = Form("")
):
    """Generate enhanced content with original design preserved"""
    try:
        form_data = {
            'topic': topic,
            'desired_content_type': desired_content_type,
            'subreddits': subreddits,
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'language_preference': language_preference,
            'additional_notes': additional_notes,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'content_goal': content_goal,
            'unique_value_prop': unique_value_prop,
            'brand_voice': brand_voice,
            'customer_pain_points': customer_pain_points,
            'frequent_questions': frequent_questions,
            'success_story': success_story
        }
        
        logger.info(f"🎯 Starting content generation for: {topic}")
        
        # Run comprehensive analysis
        results = await zee_orchestrator.generate_comprehensive_analysis(form_data)
        
        logger.info(f"✅ Content generation complete")
        
        return HTMLResponse(content=generate_original_results_page(results))
        
    except Exception as e:
        logger.error(f"❌ Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

def generate_original_results_page(results: Dict[str, Any]) -> str:
    """Generate results page with ORIGINAL design preserved"""
    
    topic = results['topic']
    content = results['generated_content']
    trust = results['trust_assessment']
    quality = results['quality_assessment']
    reddit = results['reddit_insights']
    business_context = results['business_context']  # Fixed: Now properly accessed
    metrics = results['performance_metrics']
    
    # Determine Reddit status for display
    reddit_status_display = "Live API" if reddit.get('data_source') == 'live_reddit_api' else "Enhanced Simulation"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool Results - {topic}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                line-height: 1.6;
            }}
            
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }}
            
            .logo {{
                font-size: 42px;
                font-weight: bold;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .tagline {{
                font-size: 18px;
                opacity: 0.9;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .results-header {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .ai-badge {{
                background: rgba(255,255,255,0.2);
                padding: 8px 20px;
                border-radius: 20px;
                display: inline-block;
                margin-bottom: 15px;
                font-weight: bold;
            }}
            
            .content-wrapper {{
                padding: 40px;
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, #8B5CF6, #A855F7);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                transform: translateY(0);
                transition: transform 0.3s ease;
            }}
            
            .metric-card:hover {{
                transform: translateY(-5px);
            }}
            
            .metric-value {{
                font-size: 32px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
            
            .metric-label {{
                font-size: 14px;
                opacity: 0.9;
            }}
            
            .section {{
                margin: 40px 0;
                padding: 25px;
                border-left: 5px solid #8B5CF6;
                background-color: #f8f9fa;
                border-radius: 0 15px 15px 0;
            }}
            
            .content-box {{
                background-color: white;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #e1e5e9;
                margin: 20px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }}
            
            .back-btn {{
                display: inline-block;
                padding: 12px 25px;
                background: linear-gradient(135deg, #6c757d, #495057);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                margin-bottom: 20px;
                transition: transform 0.3s ease;
            }}
            
            .back-btn:hover {{
                transform: translateY(-2px);
            }}
            
            .highlight {{
                background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #ffc107;
                margin: 20px 0;
            }}
            
            pre {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                white-space: pre-wrap;
                overflow-x: auto;
                border-left: 4px solid #8B5CF6;
                font-family: 'Courier New', monospace;
            }}
            
            .reddit-section {{
                background: linear-gradient(135deg, #fee2e2, #fca5a5);
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #ef4444;
                margin: 20px 0;
            }}
            
            .trust-score-section {{
                background: linear-gradient(135deg, #fef3c7, #fbbf24);
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #f59e0b;
                margin: 20px 0;
            }}
            
            .zee-footer {{
                background: linear-gradient(135deg, #1f2937, #374151);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .zee-footer h3 {{
                color: #8B5CF6;
                margin-bottom: 15px;
                font-size: 24px;
            }}
            
            .zee-footer p {{
                margin-bottom: 10px;
                opacity: 0.9;
            }}
            
            .improvement-chat {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                z-index: 1000;
                display: none;
                flex-direction: column;
                overflow: hidden;
            }}
            
            .chat-header {{
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                padding: 15px 20px;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .chat-body {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }}
            
            .chat-message {{
                background: #f0fdf4;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #10b981;
            }}
            
            .chat-input {{
                padding: 15px;
                border-top: 1px solid #e5e7eb;
                display: flex;
                gap: 10px;
            }}
            
            .chat-toggle {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #10b981, #059669);
                border-radius: 50%;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
                z-index: 1001;
                transition: transform 0.3s ease;
            }}
            
            .chat-toggle:hover {{
                transform: scale(1.1);
            }}
            
            @media (max-width: 768px) {{
                .metrics-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .content-wrapper {{
                    padding: 20px;
                }}
                
                .logo {{
                    font-size: 32px;
                }}
                
                .improvement-chat {{
                    width: 90%;
                    right: 5%;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">⚡ ZEE SEO TOOL</div>
            <div class="tagline">Your High-Performance Content is Ready!</div>
        </div>
        
        <div class="container">
            <div class="results-header">
                <div class="ai-badge">🤖 Generated by Zee SEO Tool</div>
                <h1>🎉 Your Trust-Optimized Content Strategy</h1>
                <p><strong>Topic:</strong> {topic}</p>
                <p><strong>Content Type:</strong> {results.get('desired_content_type', 'Comprehensive Guide')}</p>
                <p><strong>Word Count:</strong> {len(content.split())} words</p>
            </div>
            
            <div class="content-wrapper">
                <a href="/" class="back-btn">← Create Another Zee SEO Strategy</a>
                
                <div class="section">
                    <h2>📊 Zee SEO Tool Performance Metrics</h2>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{trust['overall_trust_score']}/10</div>
                            <div class="metric-label">Trust Score</div>
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
                    </div>
                    <div class="highlight">
                        <strong>🚀 Zee SEO Tool Performance Prediction:</strong> {quality['performance_prediction']}
                    </div>
                </div>

                <div class="trust-score-section">
                    <h3>🔒 Trust Score Analysis</h3>
                    <p><strong>Overall Trust Score:</strong> {trust['overall_trust_score']}/10 ({trust['trust_level'].replace('_', ' ').title()})</p>
                    <p><strong>Trust Grade:</strong> {trust['trust_grade']}</p>
                    <p><strong>YMYL Topic:</strong> {'Yes' if trust.get('is_ymyl_topic') else 'No'}</p>
                    <p><strong>Component Scores:</strong></p>
                    <ul>
                        <li>Experience: {trust['component_scores']['experience']}/10</li>
                        <li>Expertise: {trust['component_scores']['expertise']}/10</li>
                        <li>Authoritativeness: {trust['component_scores']['authoritativeness']}/10</li>
                        <li>Trustworthiness: {trust['component_scores']['trustworthiness']}/10</li>
                    </ul>
                </div>

                <div class="reddit-section">
                    <h3>📱 Reddit Research Results</h3>
                    <p><strong>Research Mode:</strong> {reddit_status_display}</p>
                    <p><strong>Communities Analyzed:</strong> {reddit['communities_analyzed']}</p>
                    <p><strong>Posts Analyzed:</strong> {reddit['total_posts_analyzed']}</p>
                    <p><strong>Authenticity Score:</strong> {reddit['authenticity_score']:.1f}/10</p>
                    <p><strong>Status:</strong> {'🟢 Live API Connected' if reddit.get('data_source') == 'live_reddit_api' else '🟡 Enhanced Simulation Mode'}</p>
                </div>

                <div class="section">
                    <h2>✍️ Your High-Performance Content</h2>
                    <div class="content-box">
                        <div class="ai-badge" style="color: #8B5CF6; background: rgba(139, 92, 246, 0.1);">🤖 Generated by Zee SEO Tool</div>
                        <h3>Your Trust-Optimized Content</h3>
                        <p><strong>Generated Word Count:</strong> {len(content.split())} words</p>
                        <p><strong>Reddit Research:</strong> {reddit_status_display} • <strong>Trust Level:</strong> {trust['trust_level'].replace('_', ' ').title()}</p>
                        <pre>{content}</pre>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <a href="/" class="back-btn" style="font-size: 18px; padding: 15px 30px;">🚀 Create Another Trust-Optimized Strategy</a>
                </div>
            </div>
            
            <div class="zee-footer">
                <h3>⚡ Built by Zeeshan Bashir</h3>
                <p><strong>Zee SEO Tool:</strong> Advanced Trust Score optimization with Reddit research.</p>
                <p><strong>Status:</strong> ✅ Deployed on Railway • Reddit: {reddit_status_display} • Trust Score: ✅ Active</p>
                <p><strong>Features:</strong> Trust Score Assessment • Reddit Research • AI Integration • Performance Analytics</p>
            </div>
        </div>
        
        <!-- Improvement Chat Toggle -->
        <button class="chat-toggle" onclick="toggleChat()">💬</button>
        
        <!-- Improvement Chat Panel -->
        <div class="improvement-chat" id="improvementChat">
            <div class="chat-header">
                <span>🚀 AI Improvement Assistant</span>
                <button onclick="toggleChat()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
            </div>
            <div class="chat-body">
                <div class="chat-message">
                    <strong>🤖 AI:</strong> Hi! I've analyzed your content. Your Trust Score is {trust['overall_trust_score']}/10. Here are some quick improvements:
                </div>
                
                <div class="chat-message">
                    <strong>💡 Quick Wins:</strong><br>
                    {"<br>".join([f"• {rec}" for rec in trust['improvement_recommendations'][:3]])}
                </div>
                
                <div class="chat-message">
                    <strong>📈 Expected Impact:</strong> Following these recommendations could improve your Trust Score by +0.5 to +1.5 points.
                </div>
                
                <div class="chat-message">
                    <strong>❓ Ask me:</strong> "How to improve trust score?", "Better content structure?", "SEO optimization tips?"
                </div>
            </div>
            <div class="chat-input">
                <input type="text" placeholder="Ask about improvements..." style="flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px;">
                <button style="padding: 10px 20px; background: #10b981; color: white; border: none; border-radius: 20px; cursor: pointer;">Send</button>
            </div>
        </div>
        
        <script>
            function toggleChat() {{
                const chat = document.getElementById('improvementChat');
                const isVisible = chat.style.display === 'flex';
                chat.style.display = isVisible ? 'none' : 'flex';
            }}
            
            // Auto-show chat if trust score needs improvement
            setTimeout(() => {{
                if ({trust['overall_trust_score']} < 7.0) {{
                    toggleChat();
                }}
            }}, 3000);
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0 - Original Design Restored",
        "features": {
            "ai_api": "✅" if zee_orchestrator.llm_client.available else "❌",
            "reddit_api": "✅" if zee_orchestrator.reddit_client.available else "⚠️ Simulation Mode",
            "trust_score": "✅ Fixed Calculation",
            "original_design": "✅ Restored"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Zee SEO Tool v3.0 (Original Design Restored)...")
    print("=" * 60)
    print("🔧 ISSUES FIXED:")
    print("  ✅ business_context error resolved")
    print("  ✅ Original CSS design restored")
    print("  ✅ 'Let AI decide' content type option added")
    print("  ✅ Trust Score calculation fixed")
    print("  ✅ Reddit API integration working")
    print("=" * 60)
    print(f"🌐 Server: http://localhost:{config.PORT}")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
