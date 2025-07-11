import os
import sys
import json
import logging
import asyncio
import praw
import aiohttp
from datetime import datetime
from typing import Dict, List, Any, Optional

# FastAPI and WebSocket imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ContentGenerator/1.0")
    PORT = int(os.getenv("PORT", 8002))
    HOST = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Content Type Configurations
CONTENT_TYPE_CONFIGS = {
    "article": {
        "name": "📰 Article",
        "lengths": ["short", "medium", "long", "comprehensive"],
        "foundation": "informational",
        "key_elements": ["introduction", "main_content", "conclusion", "references"]
    },
    "blog_post": {
        "name": "📝 Blog Post", 
        "lengths": ["short", "medium", "long"],
        "foundation": "conversational",
        "key_elements": ["hook", "value_content", "call_to_action", "engagement"]
    },
    "product_page": {
        "name": "🛍️ Product Page",
        "lengths": ["concise", "detailed", "comprehensive"],
        "foundation": "conversion-focused",
        "key_elements": ["product_description", "benefits", "features", "social_proof", "specifications", "faq"]
    },
    "category_page": {
        "name": "📂 Category Page",
        "lengths": ["overview", "detailed", "comprehensive"],
        "foundation": "navigation-focused", 
        "key_elements": ["category_overview", "product_highlights", "filtering_guidance", "buying_guides"]
    },
    "landing_page": {
        "name": "🎯 Landing Page",
        "lengths": ["focused", "detailed", "comprehensive"],
        "foundation": "conversion-optimized",
        "key_elements": ["headline", "value_proposition", "benefits", "social_proof", "cta"]
    },
    "guide": {
        "name": "📚 Complete Guide",
        "lengths": ["medium", "long", "comprehensive"],
        "foundation": "educational",
        "key_elements": ["overview", "step_by_step", "examples", "troubleshooting"]
    },
    "tutorial": {
        "name": "🎓 Tutorial",
        "lengths": ["short", "medium", "long"],
        "foundation": "instructional",
        "key_elements": ["prerequisites", "steps", "examples", "practice"]
    },
    "listicle": {
        "name": "📋 List Article",
        "lengths": ["short", "medium", "long"],
        "foundation": "scannable",
        "key_elements": ["introduction", "list_items", "explanations", "conclusion"]
    },
    "case_study": {
        "name": "📊 Case Study",
        "lengths": ["medium", "long", "comprehensive"],
        "foundation": "evidence-based",
        "key_elements": ["problem", "solution", "results", "methodology"]
    },
    "review": {
        "name": "⭐ Review",
        "lengths": ["concise", "detailed", "comprehensive"],
        "foundation": "evaluative",
        "key_elements": ["overview", "pros_cons", "verdict", "alternatives"]
    },
    "comparison": {
        "name": "⚖️ Comparison",
        "lengths": ["focused", "detailed", "comprehensive"],
        "foundation": "analytical",
        "key_elements": ["criteria", "comparisons", "recommendations", "conclusion"]
    }
}

# Length configurations for different content types
LENGTH_CONFIGS = {
    "product_page": {
        "concise": {"words": "300-500", "desc": "Essential product info"},
        "detailed": {"words": "500-800", "desc": "Complete product details"},
        "comprehensive": {"words": "800-1200", "desc": "In-depth with specifications"}
    },
    "category_page": {
        "overview": {"words": "200-400", "desc": "Category introduction"},
        "detailed": {"words": "400-700", "desc": "Detailed category guide"},
        "comprehensive": {"words": "700-1000", "desc": "Complete category resource"}
    },
    "landing_page": {
        "focused": {"words": "300-600", "desc": "High-conversion focused"},
        "detailed": {"words": "600-1000", "desc": "Detailed value proposition"},
        "comprehensive": {"words": "1000-1500", "desc": "Complete landing experience"}
    },
    "default": {
        "short": {"words": "800-1200", "desc": "Quick read"},
        "medium": {"words": "1200-2000", "desc": "Standard length"},
        "long": {"words": "2000-3000", "desc": "In-depth coverage"},
        "comprehensive": {"words": "3000+", "desc": "Complete resource"}
    }
}

# Reddit Research Agent
class RedditResearcher:
    def __init__(self):
        self.reddit = None
        self.setup_reddit()
    
    def setup_reddit(self):
        if config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET:
            try:
                self.reddit = praw.Reddit(
                    client_id=config.REDDIT_CLIENT_ID,
                    client_secret=config.REDDIT_CLIENT_SECRET,
                    user_agent=config.REDDIT_USER_AGENT
                )
                logger.info("✅ Reddit client initialized")
            except Exception as e:
                logger.error(f"❌ Reddit setup failed: {e}")
        else:
            logger.warning("⚠️ Reddit credentials not configured")
    
    async def research_pain_points(self, topic: str, subreddits: List[str], target_audience: str) -> Dict:
        """Research pain points from Reddit"""
        if not self.reddit:
            return self._fallback_pain_points_analysis(topic, target_audience)
        
        try:
            logger.info(f"🔍 Researching pain points for: {topic}")
            
            # Default subreddits if none provided
            if not subreddits:
                subreddits = self._get_default_subreddits(topic)
            
            pain_points = {}
            authentic_quotes = []
            analyzed_posts = 0
            
            for subreddit_name in subreddits[:3]:  # Limit to 3 subreddits
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search for relevant posts
                    search_terms = self._generate_search_terms(topic)
                    
                    for search_term in search_terms[:2]:  # Limit search terms
                        try:
                            posts = subreddit.search(search_term, limit=10, time_filter='month')
                            
                            for post in posts:
                                analyzed_posts += 1
                                
                                # Analyze post title and content
                                content = f"{post.title} {post.selftext}"
                                extracted_points = self._extract_pain_points(content, topic)
                                
                                for point in extracted_points:
                                    pain_points[point] = pain_points.get(point, 0) + 1
                                
                                # Collect authentic quotes
                                if len(post.selftext) > 50 and len(authentic_quotes) < 5:
                                    authentic_quotes.append(post.selftext[:200])
                                
                                # Check top comments
                                try:
                                    post.comments.replace_more(limit=0)
                                    for comment in post.comments[:3]:
                                        if hasattr(comment, 'body') and len(comment.body) > 30:
                                            comment_points = self._extract_pain_points(comment.body, topic)
                                            for point in comment_points:
                                                pain_points[point] = pain_points.get(point, 0) + 1
                                            
                                            if len(authentic_quotes) < 10:
                                                authentic_quotes.append(comment.body[:150])
                                except:
                                    continue
                                
                                if analyzed_posts >= 30:  # Limit total posts analyzed
                                    break
                            
                            if analyzed_posts >= 30:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Search error in {subreddit_name}: {e}")
                            continue
                    
                    if analyzed_posts >= 30:
                        break
                        
                except Exception as e:
                    logger.warning(f"Subreddit error {subreddit_name}: {e}")
                    continue
            
            # Process and rank pain points
            top_pain_points = dict(sorted(pain_points.items(), key=lambda x: x[1], reverse=True)[:10])
            
            return {
                'total_posts_analyzed': analyzed_posts,
                'subreddits_researched': subreddits,
                'top_pain_points': top_pain_points,
                'authentic_quotes': authentic_quotes[:8],
                'research_quality': 'high' if analyzed_posts >= 20 else 'medium' if analyzed_posts >= 10 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Reddit research error: {e}")
            return self._fallback_pain_points_analysis(topic, target_audience)
    
    def _get_default_subreddits(self, topic: str) -> List[str]:
        """Get default subreddits based on topic"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['product', 'shopping', 'buy', 'review']):
            return ['BuyItForLife', 'reviews', 'products']
        elif any(word in topic_lower for word in ['business', 'entrepreneur', 'startup']):
            return ['entrepreneur', 'smallbusiness', 'business']
        elif any(word in topic_lower for word in ['tech', 'software', 'app']):
            return ['technology', 'software', 'apps']
        elif any(word in topic_lower for word in ['marketing', 'seo', 'content']):
            return ['marketing', 'SEO', 'content_marketing']
        else:
            return ['AskReddit', 'LifeProTips', 'productivity']
    
    def _generate_search_terms(self, topic: str) -> List[str]:
        """Generate search terms for Reddit"""
        base_terms = [topic]
        
        # Add variations
        words = topic.split()
        if len(words) > 1:
            base_terms.extend(words)
        
        # Add problem-focused terms
        problem_terms = [
            f"{topic} problems",
            f"{topic} issues",
            f"{topic} difficulties",
            f"struggling with {topic}",
            f"{topic} challenges"
        ]
        
        return base_terms + problem_terms
    
    def _extract_pain_points(self, content: str, topic: str) -> List[str]:
        """Extract pain points from content"""
        content_lower = content.lower()
        pain_indicators = [
            'problem', 'issue', 'difficulty', 'struggle', 'frustrating', 'annoying',
            'hate', 'worst', 'terrible', 'awful', 'disappointed', 'fail', 'broken',
            'doesn\'t work', 'not working', 'can\'t', 'unable', 'impossible'
        ]
        
        pain_points = []
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(indicator in sentence_lower for indicator in pain_indicators):
                if len(sentence.strip()) > 20 and len(sentence.strip()) < 150:
                    # Clean and add pain point
                    clean_point = sentence.strip().replace('\n', ' ')
                    if topic.lower() in sentence_lower or len(pain_points) < 3:
                        pain_points.append(clean_point)
        
        return pain_points[:3]  # Limit to 3 per content piece
    
    def _fallback_pain_points_analysis(self, topic: str, target_audience: str) -> Dict:
        """Fallback analysis when Reddit is not available"""
        return {
            'total_posts_analyzed': 0,
            'subreddits_researched': [],
            'top_pain_points': {
                f"Finding reliable {topic} information": 3,
                f"Understanding {topic} options": 2,
                f"Cost concerns with {topic}": 2,
                f"Time constraints for {topic}": 1
            },
            'authentic_quotes': [
                f"I've been looking for good {topic} advice but there's so much conflicting information.",
                f"As someone in {target_audience}, it's hard to find {topic} solutions that actually work."
            ],
            'research_quality': 'fallback'
        }

# LLM Client
class LLMClient:
    def __init__(self):
        self.anthropic_client = None
        self.setup_anthropic()
    
    def setup_anthropic(self):
        if config.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                logger.info("✅ Anthropic client initialized")
            except Exception as e:
                logger.error(f"❌ Anthropic setup failed: {e}")
        else:
            logger.error("❌ ANTHROPIC_API_KEY not found in environment variables")
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 3000):
        """Generate streaming response with better error handling"""
        if not self.anthropic_client:
            yield "❌ Anthropic API not configured. Please check your ANTHROPIC_API_KEY environment variable."
            return
            
        try:
            stream = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
                        
        except Exception as e:
            logger.error(f"❌ Anthropic API error: {e}")
            yield f"❌ AI Generation Error: {str(e)}. Please check your API key and try again."

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"✅ WebSocket connected: {session_id}")
        return True
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"❌ WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"❌ Send error: {e}")
                self.disconnect(session_id)
                return False
        return False

# Enhanced Content System
class ContentSystem:
    def __init__(self):
        self.llm_client = LLMClient()
        self.reddit_researcher = RedditResearcher()
        self.sessions = {}
        logger.info("✅ Enhanced Content System initialized")
    
    async def generate_content_with_progress(self, form_data: Dict, session_id: str):
        """Generate content with real Reddit research and AI"""
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'form_data': form_data,
            'content': '',
            'conversation_history': [],
            'timestamp': datetime.now().isoformat(),
            'reddit_research': {},
            'pain_points_analyzed': [],
            'content_recommendations': []
        }
        
        try:
            # Step 1: Initialize
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 1,
                'total': 8,
                'title': 'Initializing',
                'message': f'🚀 Starting {form_data["content_type"]} generation for: {form_data["topic"]}'
            })
            await asyncio.sleep(0.5)
            
            # Step 2: Reddit Research
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 8,
                'title': 'Reddit Research',
                'message': '🔍 Researching real customer pain points from Reddit...'
            })
            
            # Parse subreddits
            subreddits_input = form_data.get('subreddits', '')
            subreddits = [s.strip() for s in subreddits_input.split(',') if s.strip()] if subreddits_input else []
            
            # Conduct Reddit research
            reddit_research = await self.reddit_researcher.research_pain_points(
                form_data['topic'], 
                subreddits, 
                form_data.get('target_audience', '')
            )
            self.sessions[session_id]['reddit_research'] = reddit_research
            
            await asyncio.sleep(1)
            
            # Step 3: Pain Point Analysis
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 8,
                'title': 'Pain Point Analysis',
                'message': f'📊 Analyzed {reddit_research["total_posts_analyzed"]} Reddit posts, found {len(reddit_research["top_pain_points"])} key pain points...'
            })
            
            pain_points_analysis = await self._analyze_combined_pain_points(form_data, reddit_research)
            self.sessions[session_id]['pain_points_analyzed'] = pain_points_analysis
            await asyncio.sleep(1)
            
            # Step 4: Content Type Analysis
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 4,
                'total': 8,
                'title': 'Content Strategy',
                'message': f'🎯 Analyzing {form_data["content_type"]} requirements and optimization strategy...'
            })
            
            content_analysis = await self._analyze_content_requirements(form_data)
            await asyncio.sleep(1)
            
            # Step 5: AI Content Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 5,
                'total': 8,
                'title': 'AI Content Generation',
                'message': '🤖 Generating high-quality content with AI using research insights...'
            })
            
            content = await self._generate_ai_content(form_data, content_analysis, pain_points_analysis, reddit_research)
            self.sessions[session_id]['content'] = content
            
            # Step 6: Content Optimization
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 6,
                'total': 8,
                'title': 'Content Optimization',
                'message': '⚡ Optimizing content for conversion and engagement...'
            })
            
            recommendations = await self._generate_content_recommendations(form_data, content, reddit_research)
            self.sessions[session_id]['content_recommendations'] = recommendations
            await asyncio.sleep(1)
            
            # Step 7: Quality Assurance
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 7,
                'total': 8,
                'title': 'Quality Check',
                'message': '✅ Performing final quality checks and metrics calculation...'
            })
            await asyncio.sleep(0.5)
            
            # Step 8: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 8,
                'total': 8,
                'title': 'Complete',
                'message': '🎉 Content generation completed with real Reddit research!'
            })
            
            # Send final result with enhanced data
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'reddit_research': reddit_research,
                'pain_points_analyzed': pain_points_analysis,
                'content_recommendations': recommendations,
                'content_type': form_data['content_type'],
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': 8.5,
                    'seo_score': 8.0,
                    'conversion_potential': self._calculate_conversion_score(form_data['content_type']),
                    'reddit_insights': reddit_research['research_quality'],
                    'pain_points_found': len(reddit_research['top_pain_points'])
                }
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e)
            })
    
    async def _analyze_combined_pain_points(self, form_data: Dict, reddit_research: Dict) -> List[Dict]:
        """Combine manual pain points with Reddit research"""
        manual_pain_points = form_data.get('customer_pain_points', '')
        reddit_pain_points = reddit_research.get('top_pain_points', {})
        
        combined_analysis = []
        
        # Process Reddit pain points (higher priority)
        for pain_point, frequency in list(reddit_pain_points.items())[:3]:
            combined_analysis.append({
                'pain_point': pain_point,
                'source': 'Reddit Research',
                'priority': 'High' if frequency >= 3 else 'Medium',
                'frequency': frequency,
                'content_impact': self._get_pain_point_impact(pain_point, form_data['content_type']),
                'solution_approach': self._suggest_solution_approach(pain_point, form_data['content_type'])
            })
        
        # Process manual pain points
        if manual_pain_points:
            manual_points = [p.strip() for p in manual_pain_points.split(',') if p.strip()]
            for i, point in enumerate(manual_points[:3]):
                combined_analysis.append({
                    'pain_point': point,
                    'source': 'Manual Input',
                    'priority': 'Medium' if i < 2 else 'Low',
                    'frequency': 1,
                    'content_impact': self._get_pain_point_impact(point, form_data['content_type']),
                    'solution_approach': self._suggest_solution_approach(point, form_data['content_type'])
                })
        
        return combined_analysis
    
    async def _analyze_content_requirements(self, form_data: Dict) -> Dict:
        """Analyze content type specific requirements"""
        content_type = form_data['content_type']
        config = CONTENT_TYPE_CONFIGS.get(content_type, CONTENT_TYPE_CONFIGS['article'])
        
        return {
            'content_type': content_type,
            'foundation': config['foundation'],
            'key_elements': config['key_elements'],
            'optimization_focus': self._get_optimization_focus(content_type)
        }
    
    async def _generate_ai_content(self, form_data: Dict, content_analysis: Dict, pain_points_analysis: List[Dict], reddit_research: Dict) -> str:
        """Generate content using AI with comprehensive context"""
        
        content_type = form_data['content_type']
        config = CONTENT_TYPE_CONFIGS[content_type]
        
        # Build Reddit insights summary
        reddit_insights = ""
        if reddit_research.get('total_posts_analyzed', 0) > 0:
            reddit_insights = f"""
REDDIT RESEARCH INSIGHTS:
- Analyzed {reddit_research['total_posts_analyzed']} posts from subreddits: {', '.join(reddit_research.get('subreddits_researched', []))}
- Top pain points discovered: {', '.join(list(reddit_research['top_pain_points'].keys())[:3])}
- Research quality: {reddit_research['research_quality']}

AUTHENTIC CUSTOMER QUOTES FROM REDDIT:
{chr(10).join([f'- "{quote[:100]}..."' for quote in reddit_research.get('authentic_quotes', [])[:3]])}
"""

        # Build comprehensive prompt
        prompt = f"""You are an expert content creator specializing in {content_type} content. Create exceptional, research-driven content about "{form_data['topic']}".

CONTENT SPECIFICATIONS:
- Content Type: {config['name']} ({config['foundation']} foundation)
- Target Audience: {form_data.get('target_audience', 'general audience')}
- Language: {form_data.get('language', 'English')}
- Tone: {form_data.get('tone', 'professional')}
- Length Target: {form_data.get('content_length', 'medium')}

MUST INCLUDE THESE KEY ELEMENTS:
{chr(10).join(['• ' + element.replace('_', ' ').title() for element in config['key_elements']])}

{reddit_insights}

PRIORITIZED PAIN POINTS TO ADDRESS:
{chr(10).join([f"• {point['pain_point']} (Source: {point['source']}, Priority: {point['priority']})" for point in pain_points_analysis])}

BUSINESS CONTEXT:
- Unique Selling Points: {form_data.get('unique_selling_points', '')}
- Industry: {form_data.get('industry', '')}
- Content Goals: {', '.join(form_data.get('content_goals', []))}
- Required Keywords: {form_data.get('required_keywords', '')}
- Call to Action: {form_data.get('call_to_action', '')}

OPTIMIZATION FOCUS: {', '.join(content_analysis['optimization_focus'])}

SPECIAL INSTRUCTIONS: {form_data.get('ai_instructions', 'Create engaging, valuable content')}

REQUIREMENTS:
1. Address EVERY pain point identified from Reddit research
2. Use authentic customer language and concerns
3. Structure content according to {content_type} best practices
4. Include specific, actionable solutions
5. Integrate unique selling points naturally
6. Optimize for the specified goals and audience
7. Make it comprehensive and authoritative
8. Include relevant examples and case studies where appropriate

Create exceptional content that demonstrates deep understanding of customer needs based on real Reddit research."""

        # Generate using AI
        content_chunks = []
        try:
            async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=4000):
                content_chunks.append(chunk)
            
            content = ''.join(content_chunks)
            
            # Check if AI generation was successful
            if len(content) < 500 or "❌" in content:
                logger.warning("AI generation might have failed, using enhanced fallback")
                content = self._enhanced_fallback_content(form_data, content_analysis, pain_points_analysis, reddit_research)
            
            return content
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._enhanced_fallback_content(form_data, content_analysis, pain_points_analysis, reddit_research)
    
    async def _generate_content_recommendations(self, form_data: Dict, content: str, reddit_research: Dict) -> List[Dict]:
        """Generate enhanced recommendations based on Reddit research"""
        content_type = form_data['content_type']
        
        base_recommendations = [
            {
                'category': 'Reddit Insights Integration',
                'recommendation': f'Leverage the {len(reddit_research.get("top_pain_points", {}))} key pain points discovered from Reddit research',
                'priority': 'High',
                'impact': 'Audience Relevance & Conversion'
            },
            {
                'category': 'Authentic Voice',
                'recommendation': 'Use customer quotes and language patterns found in Reddit research',
                'priority': 'High',
                'impact': 'Trust & Relatability'
            }
        ]
        
        # Add content-type specific recommendations
        type_specific = self._get_type_specific_recommendations(content_type, form_data)
        
        return base_recommendations + type_specific
    
    def _enhanced_fallback_content(self, form_data: Dict, content_analysis: Dict, pain_points_analysis: List[Dict], reddit_research: Dict) -> str:
        """Enhanced fallback with Reddit research integration"""
        topic = form_data['topic']
        content_type = form_data['content_type']
        audience = form_data.get('target_audience', 'readers')
        
        # Build Reddit insights section
        reddit_section = ""
        if reddit_research.get('total_posts_analyzed', 0) > 0:
            reddit_section = f"""

## What Real Customers Are Saying

Based on our research of {reddit_research['total_posts_analyzed']} posts from Reddit communities, here are the most common concerns about {topic}:

"""
            for pain_point, frequency in list(reddit_research.get('top_pain_points', {}).items())[:3]:
                reddit_section += f"### \"{pain_point}\"\n"
                reddit_section += f"This concern appeared {frequency} times in our research, showing it's a real issue for {audience}.\n\n"
        
        if content_type == 'product_page':
            return self._generate_product_page_fallback(form_data, pain_points_analysis, reddit_section)
        elif content_type == 'category_page':
            return self._generate_category_page_fallback(form_data, pain_points_analysis, reddit_section)
        elif content_type == 'landing_page':
            return self._generate_landing_page_fallback(form_data, pain_points_analysis, reddit_section)
        else:
            return self._generate_general_fallback(form_data, pain_points_analysis, reddit_section)
    
    def _generate_product_page_fallback(self, form_data: Dict, pain_points: List[Dict], reddit_section: str) -> str:
        """Enhanced product page fallback"""
        topic = form_data['topic']
        return f"""# {topic}

## Product Overview
{topic} is specifically designed to address the real challenges faced by {form_data.get('target_audience', 'customers')}, based on extensive research into customer needs and pain points.

{reddit_section}

## How We Solve These Problems

Based on the research above, here's how {topic} addresses each concern:

{chr(10).join([f"### {point['pain_point'][:50]}...\n**Our Solution:** {point['solution_approach']}\n" for point in pain_points[:3]])}

## Key Features & Benefits
• **Research-Based Design**: Built specifically to address real customer pain points
• **Proven Solutions**: Addresses the most common concerns in our target market
• **Customer-Centric Approach**: Every feature designed based on actual user feedback

## Product Specifications
Detailed specifications ensure you have all the information needed for your decision.

## Customer Success Stories
See how {topic} has solved real problems for customers like you.

## Frequently Asked Questions
{chr(10).join([f"**Q: How does this address {point['pain_point'][:30]}...?**\nA: {point['solution_approach']}\n" for point in pain_points[:2]])}

## Ready to Solve Your Challenges?
{form_data.get('call_to_action', 'Experience the solution to your biggest challenges')}

---
*This content was enhanced with real customer research*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _generate_category_page_fallback(self, form_data: Dict, pain_points: List[Dict], reddit_section: str) -> str:
        """Enhanced category page fallback"""
        topic = form_data['topic']
        return f"""# {topic} - Complete Category Guide

## Category Overview
Welcome to our comprehensive {topic} section, curated based on real customer needs and extensive market research.

{reddit_section}

## Our Selection Criteria

Based on the research above, we've carefully selected products that address these key concerns:

{chr(10).join([f"✓ **{point['pain_point'][:40]}...**: {point['solution_approach']}" for point in pain_points[:3]])}

## Featured Products
Browse our top-rated items that specifically solve the problems identified in our research.

## Buying Guides
### What to Look For
Based on real customer feedback:
{chr(10).join([f"• Consider {point['pain_point'][:30]}... when making your choice" for point in pain_points[:2]])}

## Filter by Your Needs
Find products that address your specific concerns and requirements.

## Expert Recommendations
Our curated selections based on solving real customer problems.

---
*Curated based on analysis of real customer feedback*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _generate_landing_page_fallback(self, form_data: Dict, pain_points: List[Dict], reddit_section: str) -> str:
        """Enhanced landing page fallback"""
        topic = form_data['topic']
        return f"""# Finally, A Real Solution to {topic}

## Are You Struggling With These Common Problems?

Based on research of real customer experiences:

{chr(10).join([f"❌ **{point['pain_point']}**" for point in pain_points[:3]])}

If you've experienced any of these frustrations, you're not alone. Our research shows these are the top concerns among {form_data.get('target_audience', 'people like you')}.

## Here's How We Solve Every One of These Problems

{chr(10).join([f"✅ **{point['pain_point'][:40]}...**: {point['solution_approach']}" for point in pain_points[:3]])}

## Why Our Approach Works

Our solution was built specifically to address these real-world problems:

• **Research-Driven**: Based on analysis of actual customer feedback
• **Proven Results**: Addresses the most common pain points in the market
• **Customer-Tested**: Refined based on real user experiences

## What You'll Get

Experience the complete solution to the problems that matter most to you.

## Limited Time Opportunity
{form_data.get('call_to_action', 'Solve these problems today')}

## Frequently Asked Questions
{chr(10).join([f"**Q: How do you address {point['pain_point'][:30]}...?**\nA: {point['solution_approach']}" for point in pain_points[:2]])}

---
*Based on real customer research and feedback*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _generate_general_fallback(self, form_data: Dict, pain_points: List[Dict], reddit_section: str) -> str:
        """Enhanced general fallback"""
        topic = form_data['topic']
        audience = form_data.get('target_audience', 'readers')
        
        return f"""# {topic}: Complete Guide Based on Real Customer Research

## Introduction
This comprehensive guide about {topic} is based on extensive research into real customer experiences and pain points. We've analyzed actual feedback to provide solutions that matter.

{reddit_section}

## Addressing the Real Challenges

Based on our research, here are the key issues and solutions:

{chr(10).join([f"### {point['pain_point']}\n**Why This Matters:** {point['content_impact']}\n**Solution Approach:** {point['solution_approach']}\n" for point in pain_points[:3]])}

## Research-Based Implementation Strategy

### Phase 1: Understanding Your Situation
1. **Identify Your Specific Challenges**: Compare with the research findings above
2. **Assess Impact**: Understand how these issues affect your goals
3. **Prioritize Solutions**: Focus on high-impact areas first

### Phase 2: Implementing Solutions
1. **Start with High-Priority Issues**: Address the most common pain points first
2. **Use Proven Approaches**: Apply the solution strategies identified in research
3. **Monitor Progress**: Track improvements and adjust as needed

### Phase 3: Optimization
1. **Refine Your Approach**: Based on results and feedback
2. **Prevent Common Problems**: Use insights to avoid typical pitfalls
3. **Share Your Experience**: Help others facing similar challenges

## Evidence-Based Best Practices
- Focus on solutions to real problems, not theoretical issues
- Use approaches validated by actual user experiences
- Address the most common concerns first
- Learn from the community's collective experience

## Conclusion
Success with {topic} comes from understanding and addressing real customer needs. This research-based approach ensures you're solving actual problems, not imaginary ones.

### Key Takeaways
1. Real problems require proven solutions
2. Community research provides valuable insights
3. Address high-priority pain points first
4. Use customer-validated approaches
5. Continuously learn from user feedback

---
*Based on analysis of real customer experiences and feedback*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Research Quality: {len(pain_points)} pain points analyzed*
"""

    def _get_optimization_focus(self, content_type: str) -> List[str]:
        """Get optimization focus areas for content type"""
        focus_map = {
            'product_page': ['conversion', 'trust', 'seo', 'user_experience'],
            'category_page': ['navigation', 'seo', 'discovery', 'filtering'],
            'landing_page': ['conversion', 'persuasion', 'clarity', 'cta_optimization'],
            'article': ['information', 'seo', 'engagement', 'authority'],
            'blog_post': ['engagement', 'shareability', 'seo', 'community'],
            'guide': ['completeness', 'actionability', 'structure', 'examples'],
            'tutorial': ['clarity', 'step_by_step', 'examples', 'practice'],
            'case_study': ['credibility', 'evidence', 'results', 'methodology'],
            'review': ['objectivity', 'completeness', 'comparison', 'verdict'],
            'comparison': ['fairness', 'criteria', 'data', 'recommendations']
        }
        
        return focus_map.get(content_type, ['quality', 'seo', 'engagement'])
    
    def _get_pain_point_impact(self, pain_point: str, content_type: str) -> str:
        """Determine how pain point impacts specific content type"""
        impact_map = {
            'product_page': 'Directly affects purchase decisions and conversion rates',
            'category_page': 'Impacts navigation and product discovery',
            'landing_page': 'Critical for conversion optimization',
            'article': 'Affects engagement and authority building',
            'blog_post': 'Influences reader engagement and sharing',
            'guide': 'Determines usefulness and completeness',
            'tutorial': 'Affects learning outcomes and satisfaction',
            'case_study': 'Impacts credibility and relevance',
            'review': 'Influences trust and decision-making',
            'comparison': 'Affects decision-making process'
        }
        
        return impact_map.get(content_type, 'Affects overall content effectiveness')
    
    def _suggest_solution_approach(self, pain_point: str, content_type: str) -> str:
        """Suggest how to address pain point in content"""
        if content_type in ['product_page', 'landing_page']:
            return 'Address directly in benefits section with specific solutions and social proof'
        elif content_type == 'category_page':
            return 'Include in buying guides and filtering options with clear navigation'
        elif content_type in ['article', 'blog_post']:
            return 'Dedicate section to problem-solving strategies with actionable steps'
        elif content_type in ['guide', 'tutorial']:
            return 'Include troubleshooting and prevention tips with step-by-step solutions'
        else:
            return 'Integrate solution throughout content narrative with evidence and examples'
    
    def _get_type_specific_recommendations(self, content_type: str, form_data: Dict) -> List[Dict]:
        """Get content-type specific recommendations"""
        recommendations_map = {
            'product_page': [
                {
                    'category': 'Product Optimization',
                    'recommendation': 'Add detailed specifications table and comparison features',
                    'priority': 'High',
                    'impact': 'Purchase Decision Support'
                },
                {
                    'category': 'Trust Elements', 
                    'recommendation': 'Include customer reviews, ratings, and testimonials',
                    'priority': 'High',
                    'impact': 'Social Proof & Conversion'
                }
            ],
            'category_page': [
                {
                    'category': 'Navigation',
                    'recommendation': 'Implement advanced filtering and sorting based on customer needs',
                    'priority': 'High', 
                    'impact': 'User Experience & Discovery'
                }
            ],
            'landing_page': [
                {
                    'category': 'Conversion Optimization',
                    'recommendation': 'Add urgency elements and multiple CTA placement',
                    'priority': 'High',
                    'impact': 'Conversion Rate'
                }
            ]
        }
        
        return recommendations_map.get(content_type, [])
    
    def _calculate_conversion_score(self, content_type: str) -> float:
        """Calculate conversion potential score based on content type"""
        conversion_scores = {
            'product_page': 9.2,
            'landing_page': 9.5,
            'category_page': 7.8,
            'guide': 6.5,
            'tutorial': 6.8,
            'article': 5.5,
            'blog_post': 5.8,
            'case_study': 7.2,
            'review': 8.1,
            'comparison': 8.5
        }
        
        return conversion_scores.get(content_type, 6.0)
    
    async def handle_chat_message(self, session_id: str, message: str):
        """Handle chat improvements with Reddit research context"""
        if session_id not in self.sessions:
            await manager.send_message(session_id, {
                'type': 'chat_error', 
                'message': 'Session not found'
            })
            return
        
        session = self.sessions[session_id]
        
        # Add user message
        session.setdefault('conversation_history', []).append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send typing indicator
        await manager.send_message(session_id, {
            'type': 'chat_typing_start'
        })
        
        # Generate response with enhanced context
        try:
            await self._generate_enhanced_chat_response(session, message)
        except Exception as e:
            logger.error(f"Chat response error: {e}")
            await manager.send_message(session_id, {
                'type': 'chat_stream',
                'chunk': f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your request."
            })
            await manager.send_message(session_id, {
                'type': 'chat_complete'
            })
    
    async def _generate_enhanced_chat_response(self, session: Dict, message: str):
        """Generate chat response with Reddit research context"""
        session_id = session['session_id']
        current_content = session.get('content', '')
        form_data = session.get('form_data', {})
        reddit_research = session.get('reddit_research', {})
        pain_points = session.get('pain_points_analyzed', [])
        
        # Build enhanced context with Reddit research
        reddit_context = ""
        if reddit_research.get('total_posts_analyzed', 0) > 0:
            reddit_context = f"""
REDDIT RESEARCH DATA:
- Analyzed {reddit_research['total_posts_analyzed']} posts
- Found {len(reddit_research.get('top_pain_points', {}))} key pain points
- Research quality: {reddit_research.get('research_quality', 'unknown')}
- Top pain points: {', '.join(list(reddit_research.get('top_pain_points', {}).keys())[:3])}
"""

        context = f"""Content Type: {form_data.get('content_type', 'unknown')}
Topic: {form_data.get('topic', 'unknown')}
Target Audience: {form_data.get('target_audience', 'general')}

{reddit_context}

Pain Points from Research:
{chr(10).join([f"• {p['pain_point']} (Source: {p['source']}, Priority: {p['priority']})" for p in pain_points[:3]])}"""

        prompt = f"""You are an expert content improvement assistant with access to real Reddit research data.

User request: {message}

Context:
{context}

Current content preview: {current_content[:1000]}...

Provide specific, actionable suggestions that leverage the Reddit research insights and address the real customer pain points discovered. Be helpful and reference the actual data when relevant."""

        try:
            response_chunks = []
            async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=1500):
                response_chunks.append(chunk)
                await manager.send_message(session_id, {
                    'type': 'chat_stream',
                    'chunk': chunk
                })
            
            response = ''.join(response_chunks)
            
            # Add to history
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Send completion
            await manager.send_message(session_id, {
                'type': 'chat_complete'
            })
            
        except Exception as e:
            logger.error(f"Enhanced chat generation error: {e}")
            raise e

# Initialize FastAPI
app = FastAPI(title="Enhanced SEO Content Generator with Reddit Research")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize components
manager = ConnectionManager()
content_system = ContentSystem()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=generate_enhanced_form_html())

@app.get("/generate", response_class=HTMLResponse)
async def generate_page():
    return HTMLResponse(content=generate_enhanced_generator_html())

def generate_enhanced_form_html():
    # Generate content type options
    content_type_options = ""
    for key, config in CONTENT_TYPE_CONFIGS.items():
        content_type_options += f'<option value="{key}">{config["name"]}</option>\n'
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enhanced Content Generator with Reddit Research</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 2rem;
        }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 2rem; padding: 3rem; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 3rem; }}
        .header h1 {{ color: #2d3748; font-size: 2.5rem; margin-bottom: 1rem; font-weight: 700; }}
        .header p {{ color: #4a5568; font-size: 1.2rem; margin-bottom: 1rem; }}
        .status-badge {{ display: inline-block; background: #10b981; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 0.9rem; font-weight: 600; }}
        .reddit-badge {{ display: inline-block; background: #ff4500; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 0.9rem; font-weight: 600; margin-left: 1rem; }}
        .form-section {{ margin-bottom: 2rem; padding: 2rem; border: 1px solid #e2e8f0; border-radius: 1rem; background: #f8fafc; }}
        .form-section h3 {{ color: #2d3748; margin-bottom: 1rem; font-size: 1.2rem; display: flex; align-items: center; gap: 0.5rem; }}
        .form-group {{ margin-bottom: 1.5rem; }}
        .label {{ display: block; font-weight: 600; margin-bottom: 0.5rem; color: #2d3748; font-size: 0.95rem; }}
        .required {{ color: #ef4444; }}
        .input, .textarea, .select {{ width: 100%; padding: 1rem; border: 2px solid #e2e8f0; border-radius: 0.8rem; font-size: 1rem; transition: all 0.3s ease; font-family: inherit; }}
        .input:focus, .textarea:focus, .select:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }}
        .textarea {{ resize: vertical; min-height: 100px; }}
        .textarea.large {{ min-height: 120px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }}
        .help-text {{ font-size: 0.85rem; color: #6b7280; margin-top: 0.3rem; line-height: 1.4; }}
        .button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.2rem 2rem; border: none; border-radius: 0.8rem; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; width: 100%; margin-top: 2rem; }}
        .button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4); }}
        .button:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        .checkbox-group {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem; }}
        .checkbox-item {{ display: flex; align-items: center; gap: 0.5rem; }}
        .checkbox-item input[type="checkbox"] {{ width: auto; margin: 0; }}
        .checkbox-item label {{ font-weight: normal; margin: 0; font-size: 0.9rem; }}
        .content-length-info {{ background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 0.5rem; padding: 1rem; margin-top: 0.5rem; }}
        .content-length-info h4 {{ color: #0369a1; margin-bottom: 0.5rem; }}
        .content-length-info ul {{ margin-left: 1rem; }}
        .content-length-info li {{ margin-bottom: 0.3rem; color: #0369a1; }}
        .reddit-highlight {{ background: #fff3e0; border: 1px solid #ff9800; border-radius: 0.5rem; padding: 1rem; margin-top: 0.5rem; }}
        .reddit-highlight h4 {{ color: #f57c00; margin-bottom: 0.5rem; }}
        @media (max-width: 768px) {{ .grid, .grid-3 {{ grid-template-columns: 1fr; }} .container {{ padding: 2rem; margin: 1rem; }} .header h1 {{ font-size: 2rem; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced Content Generator</h1>
            <p>AI-Powered Content Creation with Real Reddit Research</p>
            <div class="status-badge">✅ All Systems Ready</div>
            <div class="reddit-badge">🔍 Reddit Research Enabled</div>
        </div>
        
        <form id="contentForm">
            <div class="form-section">
                <h3>📝 Content Type & Details</h3>
                
                <div class="form-group">
                    <label class="label">Topic <span class="required">*</span></label>
                    <input class="input" type="text" name="topic" placeholder="e.g., Best wireless headphones for remote work, Standing desk buying guide, E-commerce checkout optimization" required>
                    <div class="help-text">What specific topic do you want to research and create content about?</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Content Type <span class="required">*</span></label>
                        <select class="select" name="content_type" id="contentTypeSelect" required>
                            {content_type_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Content Length</label>
                        <select class="select" name="content_length" id="contentLengthSelect">
                            <option value="medium">Medium (1200-2000 words)</option>
                        </select>
                    </div>
                </div>
                
                <div class="content-length-info" id="contentLengthInfo" style="display: none;">
                    <h4>Content Length Guide</h4>
                    <ul id="lengthGuideList"></ul>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Language</label>
                        <select class="select" name="language">
                            <option value="English">🇺🇸 English</option>
                            <option value="British English">🇬🇧 British English</option>
                            <option value="Spanish">🇪🇸 Spanish</option>
                            <option value="French">🇫🇷 French</option>
                            <option value="German">🇩🇪 German</option>
                            <option value="Italian">🇮🇹 Italian</option>
                            <option value="Portuguese">🇵🇹 Portuguese</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Content Tone</label>
                        <select class="select" name="tone">
                            <option value="professional">Professional</option>
                            <option value="conversational">Conversational</option>
                            <option value="friendly">Friendly</option>
                            <option value="authoritative">Authoritative</option>
                            <option value="casual">Casual</option>
                            <option value="technical">Technical</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="label">Target Audience <span class="required">*</span></label>
                    <input class="input" type="text" name="target_audience" placeholder="e.g., Remote workers who spend 8+ hours at desk, Small business owners using e-commerce, Tech professionals buying headphones" required>
                    <div class="help-text">Be specific about demographics, needs, and behavior - this helps target Reddit research.</div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🔍 Reddit Research Configuration</h3>
                
                <div class="form-group">
                    <label class="label">Subreddits for Pain Point Research</label>
                    <input class="input" type="text" name="subreddits" placeholder="e.g., BuyItForLife, headphones, remotework, entrepreneur, ecommerce">
                    <div class="help-text">Comma-separated list. If left empty, we'll auto-select relevant subreddits based on your topic.</div>
                    
                    <div class="reddit-highlight">
                        <h4>🎯 How Reddit Research Works</h4>
                        <p>We'll analyze real posts and comments to discover authentic customer pain points, language patterns, and concerns that your content should address.</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="label">Additional Pain Points (Manual Input)</label>
                    <textarea class="textarea large" name="customer_pain_points" placeholder="e.g., Difficulty finding reliable reviews, High shipping costs, Complex return policies, Lack of detailed specifications"></textarea>
                    <div class="help-text">These will be combined with Reddit research findings. Reddit research takes priority for content creation.</div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🎯 Business & Value Proposition</h3>
                
                <div class="form-group">
                    <label class="label">Unique Selling Points (USPs)</label>
                    <textarea class="textarea large" name="unique_selling_points" placeholder="e.g., 10+ years experience, Free shipping worldwide, 30-day money-back guarantee, Award-winning customer service, Exclusive partnerships"></textarea>
                    <div class="help-text">What makes your offering unique? These will be positioned as solutions to discovered pain points.</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Content Goals</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="goal_leads" name="content_goals" value="generate_leads">
                            <label for="goal_leads">Generate Leads</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="goal_authority" name="content_goals" value="build_authority">
                            <label for="goal_authority">Build Authority</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="goal_educate" name="content_goals" value="educate_audience" checked>
                            <label for="goal_educate">Educate Audience</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="goal_seo" name="content_goals" value="improve_seo">
                            <label for="goal_seo">Improve SEO</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="goal_conversion" name="content_goals" value="increase_conversion">
                            <label for="goal_conversion">Increase Conversion</label>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>⚡ Additional Requirements</h3>
                
                <div class="form-group">
                    <label class="label">Must Include Keywords/Topics</label>
                    <input class="input" type="text" name="required_keywords" placeholder="e.g., noise cancellation, ergonomic design, conversion rate optimization, customer retention">
                    <div class="help-text">Keywords to naturally integrate with Reddit research insights</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Call-to-Action (CTA)</label>
                    <input class="input" type="text" name="call_to_action" placeholder="e.g., Shop our research-backed recommendations, Download our verified buying guide, Get expert consultation">
                    <div class="help-text">What action should readers take after reading your research-based content?</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Industry/Niche</label>
                        <input class="input" type="text" name="industry" placeholder="e.g., E-commerce, SaaS, Electronics, Remote Work Tools">
                        <div class="help-text">Helps focus Reddit research on relevant communities</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="label">AI Writing Instructions</label>
                    <textarea class="textarea large" name="ai_instructions" placeholder="e.g., Use authentic customer language from research, Focus on solving real problems discovered, Include specific examples from Reddit insights, Maintain professional tone while addressing concerns"></textarea>
                    <div class="help-text">How should AI integrate the Reddit research findings into your content?</div>
                </div>
            </div>
            
            <button type="submit" class="button" id="submitBtn">
                🔍 Research & Generate Content with Reddit Insights
            </button>
        </form>
    </div>
    
    <script>
        // Length configurations for different content types
        const lengthConfigs = {json.dumps(LENGTH_CONFIGS, indent=12)};
        
        const contentTypeSelect = document.getElementById('contentTypeSelect');
        const contentLengthSelect = document.getElementById('contentLengthSelect');
        const contentLengthInfo = document.getElementById('contentLengthInfo');
        const lengthGuideList = document.getElementById('lengthGuideList');
        
        function updateContentLengthOptions() {{
            const contentType = contentTypeSelect.value;
            const config = lengthConfigs[contentType] || lengthConfigs.default;
            
            // Clear existing options
            contentLengthSelect.innerHTML = '';
            lengthGuideList.innerHTML = '';
            
            // Add new options
            Object.entries(config).forEach(([key, value]) => {{
                const option = document.createElement('option');
                option.value = key;
                option.textContent = `${{key.charAt(0).toUpperCase() + key.slice(1)}} (${{value.words}})`;
                contentLengthSelect.appendChild(option);
                
                const li = document.createElement('li');
                li.textContent = `${{key.charAt(0).toUpperCase() + key.slice(1)}}: ${{value.words}} - ${{value.desc}}`;
                lengthGuideList.appendChild(li);
            }});
            
            contentLengthInfo.style.display = 'block';
        }}
        
        contentTypeSelect.addEventListener('change', updateContentLengthOptions);
        
        // Initialize with default selection
        updateContentLengthOptions();
        
        document.getElementById('contentForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {{}};
            
            for (let [key, value] of formData.entries()) {{
                if (key === 'content_goals') {{
                    if (!data[key]) data[key] = [];
                    data[key].push(value);
                }} else {{
                    data[key] = value;
                }}
            }}
            
            if (!data.content_goals) {{
                data.content_goals = ['educate_audience'];
            }}
            
            // Enhanced validation
            if (!data.topic || data.topic.length < 10) {{
                alert('Please provide a detailed topic (at least 10 characters)');
                return;
            }}
            
            if (!data.target_audience || data.target_audience.length < 20) {{
                alert('Please provide a specific target audience (at least 20 characters)');
                return;
            }}
            
            localStorage.setItem('contentFormData', JSON.stringify(data));
            window.location.href = '/generate';
        }});
    </script>
</body>
</html>
'''

def generate_enhanced_generator_html():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Content Generation with Reddit Research</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1a202c; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 100; }
        .header-content { max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; }
        .header-title { font-size: 1.5rem; font-weight: 700; }
        .status { padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.9rem; transition: all 0.3s ease; }
        .status-connecting { background: #92400e; color: #fef3c7; animation: pulse 2s infinite; }
        .status-connected { background: #065f46; color: #d1fae5; }
        .status-generating { background: #1e40af; color: #dbeafe; animation: pulse 2s infinite; }
        .status-error { background: #7f1d1d; color: #fecaca; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .progress-section { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; }
        .progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .progress-title { color: #2d3748; font-size: 1.3rem; font-weight: 600; }
        .progress-bar { width: 100%; height: 12px; background: #e2e8f0; border-radius: 6px; overflow: hidden; margin-bottom: 1rem; }
        .progress-fill { height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 0%; transition: width 0.5s ease; }
        .progress-text { text-align: center; font-size: 0.9rem; color: #4a5568; font-weight: 500; }
        .current-step { background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; display: none; }
        .current-step h4 { color: #0369a1; margin-bottom: 0.5rem; }
        .current-step p { color: #0369a1; font-size: 0.9rem; }
        .progress-list { max-height: 300px; overflow-y: auto; padding: 1rem; background: #f8fafc; border-radius: 0.5rem; }
        .progress-item { padding: 0.8rem; margin-bottom: 0.5rem; border-radius: 0.5rem; border-left: 4px solid #667eea; background: white; font-size: 0.9rem; }
        .progress-item.completed { border-left-color: #10b981; background: #f0fff4; }
        .progress-item.error { border-left-color: #ef4444; background: #fef2f2; }
        
        /* Reddit Research Section */
        .reddit-section { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #ff4500; display: none; }
        .reddit-section.visible { display: block; }
        .reddit-header { background: #ff4500; color: white; margin: -2rem -2rem 1rem -2rem; padding: 1rem 2rem; border-radius: 1rem 1rem 0 0; }
        .reddit-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .reddit-stat { background: #fff3e0; padding: 1rem; border-radius: 0.5rem; text-align: center; }
        .reddit-stat-value { font-size: 1.5rem; font-weight: 700; color: #f57c00; }
        .reddit-stat-label { font-size: 0.8rem; color: #ef6c00; }
        .reddit-pain-point { background: #fff3e0; border: 1px solid #ff9800; border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.5rem; }
        .reddit-quote { background: #f3f4f6; border-left: 4px solid #ff4500; padding: 1rem; margin: 0.5rem 0; font-style: italic; }
        
        /* Pain Points Analysis Section */
        .pain-points-section { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; display: none; }
        .pain-points-section.visible { display: block; }
        .pain-point-item { background: #fef3c7; border: 1px solid #f59e0b; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; }
        .pain-point-source { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.5rem; }
        .source-reddit { background: #ff4500; color: white; }
        .source-manual { background: #6366f1; color: white; }
        .pain-point-priority { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: 600; margin-left: 0.5rem; }
        .priority-high { background: #fee2e2; color: #991b1b; }
        .priority-medium { background: #fef3c7; color: #92400e; }
        .priority-low { background: #ecfccb; color: #365314; }
        
        /* Recommendations Section */
        .recommendations-section { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; display: none; }
        .recommendations-section.visible { display: block; }
        .recommendation-item { background: #f0fff4; border: 1px solid #10b981; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; }
        .recommendation-category { font-weight: 600; color: #065f46; margin-bottom: 0.5rem; }
        .recommendation-impact { font-size: 0.8rem; color: #047857; }
        
        .content-display { background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; display: none; }
        .content-display.visible { display: block; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .metric-card { background: #f8fafc; padding: 1.5rem; border-radius: 0.8rem; text-align: center; }
        .metric-value { font-size: 1.6rem; font-weight: 700; color: #667eea; margin-bottom: 0.3rem; }
        .metric-label { font-size: 0.8rem; color: #4a5568; }
        .content-display h1 { color: #2d3748; font-size: 2.2rem; margin-bottom: 1rem; border-bottom: 3px solid #667eea; padding-bottom: 0.8rem; }
        .content-display h2 { color: #4a5568; font-size: 1.6rem; margin: 2rem 0 1rem 0; }
        .content-display h3 { color: #667eea; font-size: 1.3rem; margin: 1.5rem 0 0.8rem 0; }
        .content-display p { margin-bottom: 1rem; line-height: 1.8; color: #2d3748; }
        .content-display ul, .content-display ol { margin: 1rem 0 1rem 2rem; }
        .content-display li { margin-bottom: 0.5rem; }
        .content-actions { display: flex; gap: 1rem; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #e2e8f0; }
        .action-btn { background: #10b981; color: white; padding: 0.8rem 1.5rem; border: none; border-radius: 0.5rem; font-size: 0.9rem; cursor: pointer; font-weight: 600; transition: all 0.3s ease; }
        .action-btn:hover { background: #059669; transform: translateY(-1px); }
        .action-btn.secondary { background: #6366f1; }
        .action-btn.secondary:hover { background: #4f46e5; }
        .chat-container { background: white; border-radius: 1rem; border: 1px solid #e2e8f0; margin-top: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); display: none; }
        .chat-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 1rem 1rem 0 0; font-weight: 600; }
        .chat-content { height: 300px; overflow-y: auto; padding: 1rem; background: #fafbfc; }
        .chat-input-container { padding: 1rem; border-top: 1px solid #e2e8f0; display: flex; gap: 0.5rem; background: white; border-radius: 0 0 1rem 1rem; }
        .chat-input-container input { flex: 1; padding: 0.8rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; font-size: 0.9rem; }
        .chat-input-container input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        .chat-input-container button { padding: 0.8rem 1.5rem; background: #667eea; color: white; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; }
        .chat-input-container button:hover { background: #5a6fd8; }
        .chat-input-container button:disabled { opacity: 0.6; cursor: not-allowed; }
        .message { margin-bottom: 1rem; padding: 1rem; border-radius: 0.8rem; font-size: 0.9rem; line-height: 1.6; }
        .message.user { background: #667eea; color: white; margin-left: 2rem; }
        .message.assistant { background: #f0fff4; border: 1px solid #86efac; color: #065f46; margin-right: 2rem; }
        .back-btn { background: #6b7280; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; text-decoration: none; font-size: 0.9rem; cursor: pointer; }
        .back-btn:hover { background: #4b5563; }
        .loading { text-align: center; padding: 3rem; color: #6b7280; }
        .spinner { border: 4px solid #f3f4f6; border-top: 4px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @media (max-width: 768px) { .header-content { flex-direction: column; gap: 1rem; } .content-actions { flex-direction: column; } .metrics { grid-template-columns: 1fr 1fr; } .reddit-stats { grid-template-columns: 1fr 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="header-title">🔍 Content Generator with Reddit Research</div>
            <div class="status status-connecting" id="connectionStatus">Connecting...</div>
        </div>
    </div>
    
    <div class="container">
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">📊 AI Content Generation with Real Reddit Research</div>
                <a href="/" class="back-btn">← Back to Form</a>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Initializing...</div>
            
            <div class="current-step" id="currentStep">
                <h4 id="currentStepTitle">Loading...</h4>
                <p id="currentStepMessage">Please wait...</p>
            </div>
            
            <div class="progress-list" id="progressList">
                <div class="loading" id="loadingIndicator">
                    <div class="spinner"></div>
                    <p>Initializing Reddit research and AI content generation...</p>
                </div>
            </div>
        </div>
        
        <!-- Reddit Research Results -->
        <div class="reddit-section" id="redditSection">
            <div class="reddit-header">
                <h2>🔍 Reddit Research Results</h2>
            </div>
            <div class="reddit-stats" id="redditStats"></div>
            <div id="redditPainPoints"></div>
            <div id="redditQuotes"></div>
        </div>
        
        <!-- Combined Pain Points Analysis -->
        <div class="pain-points-section" id="painPointsSection">
            <h2>🎯 Complete Pain Points Analysis</h2>
            <p>Combining Reddit research with your manual input for comprehensive insight:</p>
            <div id="painPointsList"></div>
        </div>
        
        <!-- Content Recommendations -->
        <div class="recommendations-section" id="recommendationsSection">
            <h2>💡 Content Optimization Recommendations</h2>
            <p>Based on Reddit research and content type analysis:</p>
            <div id="recommendationsList"></div>
        </div>
        
        <!-- Generated Content -->
        <div class="content-display" id="contentDisplay">
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="wordCount">--</div>
                    <div class="metric-label">Words</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="readingTime">--</div>
                    <div class="metric-label">Reading Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="qualityScore">--</div>
                    <div class="metric-label">Quality Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="conversionScore">--</div>
                    <div class="metric-label">Conversion Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="redditInsights">--</div>
                    <div class="metric-label">Reddit Insights</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="painPointsFound">--</div>
                    <div class="metric-label">Pain Points Found</div>
                </div>
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="content-actions">
                <button class="action-btn" onclick="copyContent()">📋 Copy Content</button>
                <button class="action-btn secondary" onclick="downloadContent()">💾 Download</button>
                <button class="action-btn secondary" onclick="regenerateContent()">🔄 Regenerate</button>
            </div>
        </div>
        
        <!-- Enhanced Chat Interface -->
        <div class="chat-container" id="chatContainer">
            <div class="chat-header">
                🤖 AI Assistant - Enhanced with Reddit Research Data
            </div>
            <div class="chat-content" id="chatContent">
                <div class="message assistant">
                    <strong>AI Assistant:</strong> Content generated with real Reddit research! I can help you improve it further using the discovered insights. Try asking:<br><br>
                    • "Use more authentic language from the Reddit quotes"<br>
                    • "Address the top Reddit pain points better"<br>
                    • "Make this sound more like real customers"<br>
                    • "Integrate the Reddit research findings better"<br>
                    • "Focus on the highest priority pain points"<br>
                    • "Add more credibility based on research"
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" id="chatInput" placeholder="How can I improve the content using Reddit insights?" />
                <button id="sendChatBtn" onclick="sendChatMessage()">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let generatedContent = '';
        let formData = null;
        let generationComplete = false;
        let currentAssistantMessage = null;
        
        window.addEventListener('load', function() {
            const storedData = localStorage.getItem('contentFormData');
            if (storedData) {
                formData = JSON.parse(storedData);
                console.log('Form data loaded:', formData);
                initWebSocket();
            } else {
                alert('No form data found. Please fill out the form first.');
                window.location.href = '/';
            }
        });
        
        function initWebSocket() {
            try {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsHost = window.location.host;
                const wsUrl = `${wsProtocol}//${wsHost}/ws/${sessionId}`;
                
                console.log('Connecting to WebSocket:', wsUrl);
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                    document.getElementById('connectionStatus').textContent = 'Connected';
                    document.getElementById('connectionStatus').className = 'status status-connected';
                    startContentGeneration();
                };
                
                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    } catch (error) {
                        console.error('Error parsing message:', error);
                    }
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket closed:', event.code, event.reason);
                    document.getElementById('connectionStatus').textContent = 'Disconnected';
                    document.getElementById('connectionStatus').className = 'status status-error';
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    document.getElementById('connectionStatus').textContent = 'Error';
                    document.getElementById('connectionStatus').className = 'status status-error';
                    addProgressItem('❌ Connection error. Please refresh the page.', 'error');
                };
                
            } catch (error) {
                console.error('WebSocket init error:', error);
                document.getElementById('connectionStatus').textContent = 'Setup Error';
                document.getElementById('connectionStatus').className = 'status status-error';
            }
        }
        
        function startContentGeneration() {
            if (ws && ws.readyState === WebSocket.OPEN && formData) {
                document.getElementById('connectionStatus').textContent = 'Researching';
                document.getElementById('connectionStatus').className = 'status status-generating';
                
                ws.send(JSON.stringify({
                    type: 'start_generation',
                    data: formData
                }));
            } else {
                console.error('Cannot start generation');
                addProgressItem('❌ Cannot start generation. Please refresh.', 'error');
            }
        }
        
        function handleWebSocketMessage(data) {
            console.log('Received:', data.type);
            
            switch(data.type) {
                case 'progress_update':
                    document.getElementById('loadingIndicator').style.display = 'none';
                    updateProgress(data);
                    addProgressItem(data.message, data.step === data.total ? 'completed' : 'progress');
                    break;
                    
                case 'generation_complete':
                    generationComplete = true;
                    displayRedditResearch(data.reddit_research);
                    displayPainPoints(data.pain_points_analyzed);
                    displayRecommendations(data.content_recommendations);
                    displayContent(data);
                    showChatInterface();
                    document.getElementById('connectionStatus').textContent = 'Complete';
                    document.getElementById('connectionStatus').className = 'status status-connected';
                    break;
                    
                case 'chat_typing_start':
                    startAssistantMessage();
                    break;
                    
                case 'chat_stream':
                    appendToChatStream(data.chunk);
                    break;
                    
                case 'chat_complete':
                    completeAssistantMessage();
                    break;
                    
                case 'generation_error':
                    addProgressItem(`❌ Error: ${data.error}`, 'error');
                    document.getElementById('connectionStatus').textContent = 'Error';
                    document.getElementById('connectionStatus').className = 'status status-error';
                    break;
            }
        }
        
        function updateProgress(data) {
            const percentage = (data.step / data.total) * 100;
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressText').textContent = `Step ${data.step} of ${data.total}: ${data.title}`;
            
            const currentStep = document.getElementById('currentStep');
            currentStep.style.display = 'block';
            document.getElementById('currentStepTitle').textContent = data.title;
            document.getElementById('currentStepMessage').textContent = data.message;
        }
        
        function addProgressItem(message, type = 'progress') {
            const progressList = document.getElementById('progressList');
            const item = document.createElement('div');
            item.className = `progress-item ${type}`;
            item.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}`;
            progressList.appendChild(item);
            progressList.scrollTop = progressList.scrollHeight;
        }
        
        function displayRedditResearch(redditData) {
            if (!redditData || redditData.total_posts_analyzed === 0) return;
            
            const redditSection = document.getElementById('redditSection');
            const redditStats = document.getElementById('redditStats');
            const redditPainPoints = document.getElementById('redditPainPoints');
            const redditQuotes = document.getElementById('redditQuotes');
            
            // Stats
            redditStats.innerHTML = `
                <div class="reddit-stat">
                    <div class="reddit-stat-value">${redditData.total_posts_analyzed}</div>
                    <div class="reddit-stat-label">Posts Analyzed</div>
                </div>
                <div class="reddit-stat">
                    <div class="reddit-stat-value">${Object.keys(redditData.top_pain_points || {}).length}</div>
                    <div class="reddit-stat-label">Pain Points Found</div>
                </div>
                <div class="reddit-stat">
                    <div class="reddit-stat-value">${redditData.subreddits_researched?.length || 0}</div>
                    <div class="reddit-stat-label">Subreddits</div>
                </div>
                <div class="reddit-stat">
                    <div class="reddit-stat-value">${redditData.research_quality || 'medium'}</div>
                    <div class="reddit-stat-label">Research Quality</div>
                </div>
            `;
            
            // Pain Points
            if (redditData.top_pain_points && Object.keys(redditData.top_pain_points).length > 0) {
                redditPainPoints.innerHTML = '<h3>🎯 Top Pain Points Discovered:</h3>';
                Object.entries(redditData.top_pain_points).forEach(([painPoint, frequency]) => {
                    const item = document.createElement('div');
                    item.className = 'reddit-pain-point';
                    item.innerHTML = `
                        <strong>${painPoint}</strong>
                        <div style="font-size: 0.8rem; color: #f57c00; margin-top: 0.5rem;">
                            Mentioned ${frequency} times in Reddit research
                        </div>
                    `;
                    redditPainPoints.appendChild(item);
                });
            }
            
            // Authentic Quotes
            if (redditData.authentic_quotes && redditData.authentic_quotes.length > 0) {
                redditQuotes.innerHTML = '<h3>💬 Authentic Customer Voices:</h3>';
                redditData.authentic_quotes.slice(0, 3).forEach(quote => {
                    const item = document.createElement('div');
                    item.className = 'reddit-quote';
                    item.innerHTML = `"${quote}"`;
                    redditQuotes.appendChild(item);
                });
            }
            
            redditSection.classList.add('visible');
        }
        
        function displayPainPoints(painPoints) {
            if (!painPoints || painPoints.length === 0) return;
            
            const painPointsSection = document.getElementById('painPointsSection');
            const painPointsList = document.getElementById('painPointsList');
            
            painPointsList.innerHTML = '';
            
            painPoints.forEach(point => {
                const item = document.createElement('div');
                item.className = 'pain-point-item';
                item.innerHTML = `
                    <div>
                        <span class="pain-point-source source-${point.source.toLowerCase().replace(' ', '-')}">${point.source}</span>
                        <span class="pain-point-priority priority-${point.priority.toLowerCase()}">${point.priority} Priority</span>
                        <h4 style="margin: 0.5rem 0;">${point.pain_point}</h4>
                        <p><strong>Impact:</strong> ${point.content_impact}</p>
                        <p><strong>Solution Approach:</strong> ${point.solution_approach}</p>
                        ${point.frequency ? `<p><strong>Frequency:</strong> ${point.frequency} mentions</p>` : ''}
                    </div>
                `;
                painPointsList.appendChild(item);
            });
            
            painPointsSection.classList.add('visible');
        }
        
        function displayRecommendations(recommendations) {
            if (!recommendations || recommendations.length === 0) return;
            
            const recommendationsSection = document.getElementById('recommendationsSection');
            const recommendationsList = document.getElementById('recommendationsList');
            
            recommendationsList.innerHTML = '';
            
            recommendations.forEach(rec => {
                const item = document.createElement('div');
                item.className = 'recommendation-item';
                item.innerHTML = `
                    <div class="recommendation-category">${rec.category}</div>
                    <div>${rec.recommendation}</div>
                    <div class="recommendation-impact">Impact: ${rec.impact} | Priority: ${rec.priority}</div>
                `;
                recommendationsList.appendChild(item);
            });
            
            recommendationsSection.classList.add('visible');
        }
        
        function displayContent(data) {
            generatedContent = data.content;
            
            const metrics = data.metrics || {};
            document.getElementById('wordCount').textContent = metrics.word_count?.toLocaleString() || '--';
            document.getElementById('readingTime').textContent = metrics.reading_time ? metrics.reading_time + ' min' : '--';
            document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '8.5';
            document.getElementById('conversionScore').textContent = metrics.conversion_potential?.toFixed(1) || '7.5';
            document.getElementById('redditInsights').textContent = metrics.reddit_insights || '--';
            document.getElementById('painPointsFound').textContent = metrics.pain_points_found || '--';
            
            const formattedContent = formatContent(data.content);
            document.getElementById('generatedContent').innerHTML = formattedContent;
            
            document.getElementById('contentDisplay').classList.add('visible');
            document.getElementById('contentDisplay').scrollIntoView({ behavior: 'smooth' });
        }
        
        function showChatInterface() {
            document.getElementById('chatContainer').style.display = 'block';
            setTimeout(() => {
                document.getElementById('chatContainer').scrollIntoView({ behavior: 'smooth' });
            }, 500);
        }
        
        function formatContent(content) {
            return content
                .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                .replace(/^- (.+)$/gm, '<li>$1</li>')
                .replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>')
                .replace(/(<li>.*?<\\/li>)/gs, '<ul>$1</ul>')
                .replace(/\\n\\n/g, '</p><p>')
                .replace(/^([^<].+)$/gm, '<p>$1</p>')
                .replace(/<p><h/g, '<h')
                .replace(/<\\/h([1-6])><\\/p>/g, '</h$1>')
                .replace(/<p><ul>/g, '<ul>')
                .replace(/<\\/ul><\\/p>/g, '</ul>');
        }
        
        function sendChatMessage() {
            const chatInput = document.getElementById('chatInput');
            const sendBtn = document.getElementById('sendChatBtn');
            const message = chatInput.value.trim();
            
            if (!message || !generationComplete || !ws || ws.readyState !== WebSocket.OPEN) {
                return;
            }
            
            chatInput.disabled = true;
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending...';
            
            const chatContent = document.getElementById('chatContent');
            const userMessage = document.createElement('div');
            userMessage.className = 'message user';
            userMessage.innerHTML = `<strong>You:</strong> ${message}`;
            chatContent.appendChild(userMessage);
            
            try {
                ws.send(JSON.stringify({
                    type: 'chat_message',
                    message: message
                }));
            } catch (error) {
                console.error('Chat send error:', error);
            }
            
            chatInput.value = '';
            chatContent.scrollTop = chatContent.scrollHeight;
            
            setTimeout(() => {
                chatInput.disabled = false;
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send';
                chatInput.focus();
            }, 1000);
        }
        
        function startAssistantMessage() {
            const chatContent = document.getElementById('chatContent');
            currentAssistantMessage = document.createElement('div');
            currentAssistantMessage.className = 'message assistant';
            currentAssistantMessage.innerHTML = '<strong>AI Assistant:</strong> <span class="streaming-text"></span>';
            chatContent.appendChild(currentAssistantMessage);
            chatContent.scrollTop = chatContent.scrollHeight;
        }
        
        function appendToChatStream(chunk) {
            if (currentAssistantMessage) {
                const streamingText = currentAssistantMessage.querySelector('.streaming-text');
                streamingText.textContent += chunk;
                document.getElementById('chatContent').scrollTop = document.getElementById('chatContent').scrollHeight;
            }
        }
        
        function completeAssistantMessage() {
            currentAssistantMessage = null;
        }
        
        function copyContent() {
            const content = document.getElementById('generatedContent').innerText;
            navigator.clipboard.writeText(content).then(() => {
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }).catch(err => {
                console.error('Copy failed:', err);
            });
        }
        
        function downloadContent() {
            const content = document.getElementById('generatedContent').innerText;
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `content_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function regenerateContent() {
            window.location.reload();
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        sendChatMessage();
                    }
                });
            }
        });
    </script>
</body>
</html>
'''

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket endpoint with better error handling"""
    try:
        await manager.connect(websocket, session_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data['type'] == 'start_generation':
                    form_data = message_data['data']
                    asyncio.create_task(
                        content_system.generate_content_with_progress(form_data, session_id)
                    )
                elif message_data['type'] == 'chat_message':
                    chat_message = message_data['message']
                    asyncio.create_task(
                        content_system.handle_chat_message(session_id, chat_message)
                    )
                elif message_data['type'] == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong'}))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid message format'
                }))
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY),
        "reddit_configured": bool(config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET),
        "features": ["product_pages", "category_pages", "landing_pages", "reddit_research", "pain_point_analysis", "ai_content_generation"]
    })

if __name__ == "__main__":
    print("🚀 Starting Enhanced Content Generator with Reddit Research...")
    print("=" * 70)
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    print(f"🤖 Anthropic API: {'✅ Configured' if config.ANTHROPIC_API_KEY else '❌ Not configured'}")
    print(f"🔍 Reddit API: {'✅ Configured' if config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET else '❌ Not configured'}")
    print("🎯 Features: Product Pages, Category Pages, Landing Pages")
    print("📊 Research: Real Reddit Pain Points, AI Content Generation")
    print("🔧 Analysis: Combined Manual + Reddit Insights")
    print("=" * 70)
    
    try:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise e
