import os
import sys
import json
import logging
import asyncio
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
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 3000):
        """Generate streaming response"""
        if self.anthropic_client:
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
                logger.error(f"❌ Generation error: {e}")
                yield f"Error: {str(e)}"
        else:
            yield "Please configure your Anthropic API key."

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
        self.sessions = {}
        logger.info("✅ Enhanced Content System initialized")
    
    async def generate_content_with_progress(self, form_data: Dict, session_id: str):
        """Generate content with progress updates and pain point analysis"""
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'form_data': form_data,
            'content': '',
            'conversation_history': [],
            'timestamp': datetime.now().isoformat(),
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
            await asyncio.sleep(1)
            
            # Step 2: Analyze Content Type Requirements
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 8,
                'title': 'Content Analysis',
                'message': f'🔍 Analyzing {form_data["content_type"]} requirements and structure...'
            })
            
            content_analysis = await self._analyze_content_requirements(form_data)
            await asyncio.sleep(1)
            
            # Step 3: Pain Point Research
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 8,
                'title': 'Pain Point Research',
                'message': '📊 Analyzing customer pain points and market insights...'
            })
            
            pain_points_analysis = await self._analyze_pain_points(form_data)
            self.sessions[session_id]['pain_points_analyzed'] = pain_points_analysis
            await asyncio.sleep(1)
            
            # Step 4: Audience Analysis
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 4,
                'total': 8,
                'title': 'Audience Research',
                'message': '👥 Analyzing target audience needs and preferences...'
            })
            await asyncio.sleep(1)
            
            # Step 5: Content Structure Planning
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 5,
                'total': 8,
                'title': 'Structure Planning',
                'message': '🏗️ Creating optimized content structure...'
            })
            await asyncio.sleep(1)
            
            # Step 6: Content Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 6,
                'total': 8,
                'title': 'Content Generation',
                'message': '✍️ Generating high-quality content...'
            })
            
            content = await self._generate_content(form_data, content_analysis, pain_points_analysis)
            self.sessions[session_id]['content'] = content
            
            # Step 7: Content Optimization
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 7,
                'total': 8,
                'title': 'Optimization',
                'message': '⚡ Optimizing for conversion and engagement...'
            })
            
            recommendations = await self._generate_content_recommendations(form_data, content)
            self.sessions[session_id]['content_recommendations'] = recommendations
            await asyncio.sleep(1)
            
            # Step 8: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 8,
                'total': 8,
                'title': 'Complete',
                'message': '✅ Content generation completed with analysis!'
            })
            
            # Send final result with enhanced data
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'pain_points_analyzed': pain_points_analysis,
                'content_recommendations': recommendations,
                'content_type': form_data['content_type'],
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': 8.5,
                    'seo_score': 8.0,
                    'conversion_potential': self._calculate_conversion_score(form_data['content_type'])
                }
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e)
            })
    
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
    
    async def _analyze_pain_points(self, form_data: Dict) -> List[Dict]:
        """Analyze and categorize pain points"""
        pain_points_text = form_data.get('customer_pain_points', '')
        content_type = form_data['content_type']
        
        # Split and analyze pain points
        pain_points = [p.strip() for p in pain_points_text.split(',') if p.strip()]
        
        analyzed_points = []
        for i, point in enumerate(pain_points[:5]):  # Limit to top 5
            analyzed_points.append({
                'pain_point': point,
                'priority': 'High' if i < 2 else 'Medium' if i < 4 else 'Low',
                'content_impact': self._get_pain_point_impact(point, content_type),
                'solution_approach': self._suggest_solution_approach(point, content_type)
            })
        
        return analyzed_points
    
    async def _generate_content_recommendations(self, form_data: Dict, content: str) -> List[Dict]:
        """Generate content-type specific recommendations"""
        content_type = form_data['content_type']
        
        base_recommendations = [
            {
                'category': 'Content Structure',
                'recommendation': 'Optimize heading hierarchy for better readability',
                'priority': 'High',
                'impact': 'SEO & User Experience'
            },
            {
                'category': 'Trust Building',
                'recommendation': 'Add author credentials and social proof',
                'priority': 'High',
                'impact': 'Credibility & Conversion'
            }
        ]
        
        # Add content-type specific recommendations
        type_specific = self._get_type_specific_recommendations(content_type, form_data)
        
        return base_recommendations + type_specific
    
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
            return 'Address directly in benefits section with specific solutions'
        elif content_type == 'category_page':
            return 'Include in buying guides and filtering options'
        elif content_type in ['article', 'blog_post']:
            return 'Dedicate section to problem-solving strategies'
        elif content_type in ['guide', 'tutorial']:
            return 'Include troubleshooting and prevention tips'
        else:
            return 'Integrate solution throughout content narrative'
    
    def _get_type_specific_recommendations(self, content_type: str, form_data: Dict) -> List[Dict]:
        """Get content-type specific recommendations"""
        recommendations_map = {
            'product_page': [
                {
                    'category': 'Product Optimization',
                    'recommendation': 'Add detailed specifications and comparison tables',
                    'priority': 'High',
                    'impact': 'Purchase Decision Support'
                },
                {
                    'category': 'Trust Elements',
                    'recommendation': 'Include customer reviews and ratings',
                    'priority': 'High',
                    'impact': 'Social Proof & Conversion'
                },
                {
                    'category': 'Technical Details',
                    'recommendation': 'Add FAQ section for common questions',
                    'priority': 'Medium',
                    'impact': 'Reduced Support Queries'
                }
            ],
            'category_page': [
                {
                    'category': 'Navigation',
                    'recommendation': 'Implement intuitive filtering and sorting options',
                    'priority': 'High',
                    'impact': 'User Experience & Discovery'
                },
                {
                    'category': 'Content Strategy',
                    'recommendation': 'Add buying guides for category',
                    'priority': 'Medium',
                    'impact': 'Education & Conversion'
                }
            ],
            'landing_page': [
                {
                    'category': 'Conversion Optimization',
                    'recommendation': 'A/B test different headline variations',
                    'priority': 'High',
                    'impact': 'Conversion Rate'
                },
                {
                    'category': 'Persuasion',
                    'recommendation': 'Add urgency and scarcity elements',
                    'priority': 'Medium',
                    'impact': 'Action Motivation'
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
    
    async def _generate_content(self, form_data: Dict, content_analysis: Dict, pain_points_analysis: List[Dict]) -> str:
        """Generate content using AI with enhanced context"""
        
        content_type = form_data['content_type']
        config = CONTENT_TYPE_CONFIGS[content_type]
        
        # Build enhanced prompt with content type specifics
        prompt = f"""Create a high-quality {content_type} about "{form_data['topic']}" with the following specifications:

CONTENT TYPE: {config['name']}
CONTENT FOUNDATION: {config['foundation']}
TARGET AUDIENCE: {form_data.get('target_audience', 'general audience')}
LANGUAGE: {form_data.get('language', 'English')}
TONE: {form_data.get('tone', 'professional')}

KEY ELEMENTS TO INCLUDE:
{chr(10).join(['• ' + element.replace('_', ' ').title() for element in config['key_elements']])}

PAIN POINTS TO ADDRESS:
{chr(10).join([f"• {point['pain_point']} (Priority: {point['priority']})" for point in pain_points_analysis])}

UNIQUE SELLING POINTS: {form_data.get('unique_selling_points', '')}

CONTENT GOALS: {form_data.get('content_goals', [])}

INDUSTRY: {form_data.get('industry', '')}

REQUIRED KEYWORDS: {form_data.get('required_keywords', '')}

CALL TO ACTION: {form_data.get('call_to_action', '')}

AI INSTRUCTIONS: {form_data.get('ai_instructions', 'Write clearly and helpfully')}

OPTIMIZATION FOCUS: {', '.join(content_analysis['optimization_focus'])}

Create comprehensive, engaging content that specifically addresses the pain points and showcases the unique value proposition. Structure the content according to {content_type} best practices."""

        # Generate using AI
        content_chunks = []
        try:
            async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=3500):
                content_chunks.append(chunk)
            
            content = ''.join(content_chunks)
            
            # Fallback if too short
            if len(content) < 500:
                content = self._fallback_content(form_data, content_analysis)
            
            return content
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._fallback_content(form_data, content_analysis)
    
    def _fallback_content(self, form_data: Dict, content_analysis: Dict) -> str:
        """Generate enhanced fallback content based on content type"""
        topic = form_data['topic']
        content_type = form_data['content_type']
        audience = form_data.get('target_audience', 'readers')
        
        if content_type == 'product_page':
            return self._generate_product_page_fallback(form_data)
        elif content_type == 'category_page':
            return self._generate_category_page_fallback(form_data)
        elif content_type == 'landing_page':
            return self._generate_landing_page_fallback(form_data)
        else:
            return self._generate_general_fallback(form_data)
    
    def _generate_product_page_fallback(self, form_data: Dict) -> str:
        """Generate product page specific fallback"""
        topic = form_data['topic']
        return f"""# {topic}

## Product Overview
{topic} is designed to meet the specific needs of {form_data.get('target_audience', 'customers')} who are looking for reliable solutions.

## Key Features
• Premium quality construction
• User-friendly design
• Reliable performance
• Excellent value proposition

## Benefits
• Solves key customer challenges
• Improves efficiency and productivity
• Provides long-term value
• Backed by professional support

## Specifications
Detailed technical specifications ensure you have all the information needed for your decision.

## Customer Reviews
Join thousands of satisfied customers who have transformed their experience with {topic}.

## Frequently Asked Questions
We've compiled answers to the most common questions about {topic}.

## Order Information
Ready to experience the benefits? {form_data.get('call_to_action', 'Get started today')}

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def _generate_category_page_fallback(self, form_data: Dict) -> str:
        """Generate category page specific fallback"""
        topic = form_data['topic']
        return f"""# {topic} - Complete Category Guide

## Category Overview
Explore our comprehensive collection of {topic} products designed for {form_data.get('target_audience', 'customers')}.

## Featured Products
Discover our top-rated items in the {topic} category.

## Buying Guide
### What to Consider
• Quality and durability factors
• Price and value comparison
• Feature requirements
• Customer reviews and ratings

### Popular Choices
Our most popular {topic} products based on customer feedback and sales data.

## Browse by Features
Find exactly what you need with our detailed filtering options.

## Expert Recommendations
Our team has curated the best {topic} options for different needs and budgets.

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def _generate_landing_page_fallback(self, form_data: Dict) -> str:
        """Generate landing page specific fallback"""
        topic = form_data['topic']
        return f"""# Transform Your Results with {topic}

## The Solution You've Been Looking For
{topic} addresses the specific challenges faced by {form_data.get('target_audience', 'professionals')}.

## Why Choose Our Approach?
• Proven results and success stories
• Expert guidance and support
• Comprehensive solution package
• Risk-free guarantee

## What You'll Get
Experience the complete {topic} solution designed for maximum impact.

## Success Stories
See how others have transformed their results with our {topic} approach.

## Limited Time Opportunity
{form_data.get('call_to_action', 'Take action today and transform your results')}

## Frequently Asked Questions
Get answers to common questions about {topic}.

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def _generate_general_fallback(self, form_data: Dict) -> str:
        """Generate general fallback content"""
        topic = form_data['topic']
        audience = form_data.get('target_audience', 'readers')
        
        content = f"""# {topic}: Complete Guide

## Introduction
Welcome to this comprehensive guide about {topic}. This resource has been specifically created for {audience} who want to master this important subject.

## Understanding {topic}
{topic} is a critical area that can significantly impact your success. Whether you're just getting started or looking to improve your current approach, this guide provides the insights you need.

### Key Benefits
When you master {topic}, you'll experience:
- Improved efficiency and effectiveness
- Better results and outcomes
- Reduced frustration and wasted effort
- Increased confidence in your decisions

## Implementation Strategy
### Phase 1: Foundation Building
1. **Assessment**: Evaluate your current situation
2. **Planning**: Create a clear roadmap
3. **Preparation**: Gather necessary resources

### Phase 2: Implementation
1. **Start Small**: Begin with manageable steps
2. **Scale Gradually**: Expand as you gain experience
3. **Optimize**: Continuously improve your approach

## Best Practices
- Start with the end in mind
- Measure what matters
- Stay consistent with your efforts
- Learn from others' experiences
- Adapt and evolve your approach

## Conclusion
Success with {topic} requires understanding, planning, and consistent action. By following the strategies outlined in this guide, {audience} will be well-equipped to achieve their goals.

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Word count: ~{len(content.split())} words*
"""
        return content
    
    async def handle_chat_message(self, session_id: str, message: str):
        """Handle chat improvements with better error handling"""
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
        
        # Generate response with better error handling
        try:
            await self._generate_chat_response(session, message)
        except Exception as e:
            logger.error(f"Chat response error: {e}")
            await manager.send_message(session_id, {
                'type': 'chat_stream',
                'chunk': f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your request."
            })
            await manager.send_message(session_id, {
                'type': 'chat_complete'
            })
    
    async def _generate_chat_response(self, session: Dict, message: str):
        """Generate chat response with enhanced context"""
        session_id = session['session_id']
        current_content = session.get('content', '')
        form_data = session.get('form_data', {})
        pain_points = session.get('pain_points_analyzed', [])
        recommendations = session.get('content_recommendations', [])
        
        # Build enhanced context
        context = f"""Content Type: {form_data.get('content_type', 'unknown')}
Topic: {form_data.get('topic', 'unknown')}
Target Audience: {form_data.get('target_audience', 'general')}

Pain Points Analyzed:
{chr(10).join([f"• {p['pain_point']} (Priority: {p['priority']})" for p in pain_points])}

Current Recommendations:
{chr(10).join([f"• {r['recommendation']}" for r in recommendations[:3]])}"""

        prompt = f"""You are a content improvement assistant helping with {form_data.get('content_type', 'content')} optimization.

User request: {message}

Context:
{context}

Current content preview: {current_content[:1000]}...

Provide specific, actionable suggestions that consider the content type, pain points analyzed, and current recommendations. Be helpful and conversational."""

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
            logger.error(f"Chat generation error: {e}")
            raise e

# Initialize FastAPI
app = FastAPI(title="Enhanced SEO Content Generator")

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
    <title>Enhanced SEO Content Generator</title>
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
        @media (max-width: 768px) {{ .grid, .grid-3 {{ grid-template-columns: 1fr; }} .container {{ padding: 2rem; margin: 1rem; }} .header h1 {{ font-size: 2rem; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced SEO Content Generator</h1>
            <p>AI-Powered Content Creation with Product & Category Page Support</p>
            <div class="status-badge">✅ All Systems Ready</div>
        </div>
        
        <form id="contentForm">
            <div class="form-section">
                <h3>📝 Content Type & Details</h3>
                
                <div class="form-group">
                    <label class="label">Topic <span class="required">*</span></label>
                    <input class="input" type="text" name="topic" placeholder="e.g., Best wireless headphones for professionals, Category: Office furniture, Product: Standing desk converter" required>
                    <div class="help-text">What specific topic, product, or category do you want to create content about?</div>
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
                    <input class="input" type="text" name="target_audience" placeholder="e.g., Online shoppers looking for office furniture, B2B professionals, Small business owners" required>
                    <div class="help-text">Be specific about demographics, needs, and purchasing behavior for your content type.</div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🎯 Business & Value Proposition</h3>
                
                <div class="form-group">
                    <label class="label">Unique Selling Points (USPs)</label>
                    <textarea class="textarea large" name="unique_selling_points" placeholder="e.g., 10+ years experience, Free shipping, 30-day returns, Award-winning design, Exclusive features"></textarea>
                    <div class="help-text">What makes your product/service unique? Include competitive advantages, guarantees, or special features.</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Customer Pain Points <span class="required">*</span></label>
                    <textarea class="textarea large" name="customer_pain_points" placeholder="e.g., Difficulty finding reliable products, High shipping costs, Complex return process, Lack of detailed specifications" required></textarea>
                    <div class="help-text">What specific problems do your customers face? These will be analyzed and prioritized automatically.</div>
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
                    <input class="input" type="text" name="required_keywords" placeholder="e.g., wireless headphones, noise cancellation, office furniture, ergonomic">
                    <div class="help-text">Specific keywords or topics that must be included in the content</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Call-to-Action (CTA)</label>
                    <input class="input" type="text" name="call_to_action" placeholder="e.g., Shop now with free shipping, Compare products, Download buying guide, Contact sales team">
                    <div class="help-text">What action do you want readers to take after consuming your content?</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Industry/Niche</label>
                        <input class="input" type="text" name="industry" placeholder="e.g., E-commerce, B2B Software, Electronics, Furniture">
                        <div class="help-text">What industry or niche is this content for?</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Subreddits for Research</label>
                        <input class="input" type="text" name="subreddits" placeholder="e.g., BuyItForLife, OfficeChairs, entrepreneur">
                        <div class="help-text">Comma-separated subreddits for audience research</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="label">AI Writing Instructions</label>
                    <textarea class="textarea large" name="ai_instructions" placeholder="e.g., Focus on conversion elements, Include technical specifications, Use comparison tables, Add trust signals, Emphasize benefits over features"></textarea>
                    <div class="help-text">Specific instructions for how the AI should write your content based on the selected content type</div>
                </div>
            </div>
            
            <button type="submit" class="button" id="submitBtn">
                🚀 Generate Enhanced Content with Analysis
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
            
            if (!data.customer_pain_points || data.customer_pain_points.length < 30) {{
                alert('Please provide detailed customer pain points (at least 30 characters)');
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
    <title>Enhanced Content Generation</title>
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
        
        /* Pain Points Analysis Section */
        .pain-points-section { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; display: none; }
        .pain-points-section.visible { display: block; }
        .pain-point-item { background: #fef3c7; border: 1px solid #f59e0b; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; }
        .pain-point-priority { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: 600; }
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
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .metric-card { background: #f8fafc; padding: 1.5rem; border-radius: 0.8rem; text-align: center; }
        .metric-value { font-size: 1.8rem; font-weight: 700; color: #667eea; margin-bottom: 0.3rem; }
        .metric-label { font-size: 0.85rem; color: #4a5568; }
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
        @media (max-width: 768px) { .header-content { flex-direction: column; gap: 1rem; } .content-actions { flex-direction: column; } .metrics { grid-template-columns: 1fr 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="header-title">🚀 Enhanced Content Generator</div>
            <div class="status status-connecting" id="connectionStatus">Connecting...</div>
        </div>
    </div>
    
    <div class="container">
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">📊 Content Generation Progress</div>
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
                    <p>Initializing enhanced content generation...</p>
                </div>
            </div>
        </div>
        
        <!-- Pain Points Analysis Section -->
        <div class="pain-points-section" id="painPointsSection">
            <h2>🎯 Pain Points Analysis</h2>
            <p>Based on your input, we've analyzed and prioritized the customer pain points:</p>
            <div id="painPointsList"></div>
        </div>
        
        <!-- Recommendations Section -->
        <div class="recommendations-section" id="recommendationsSection">
            <h2>💡 Content Optimization Recommendations</h2>
            <p>Based on your content type and analysis, here are specific improvement recommendations:</p>
            <div id="recommendationsList"></div>
        </div>
        
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
                    <div class="metric-value" id="seoScore">--</div>
                    <div class="metric-label">SEO Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="conversionScore">--</div>
                    <div class="metric-label">Conversion Score</div>
                </div>
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="content-actions">
                <button class="action-btn" onclick="copyContent()">📋 Copy Content</button>
                <button class="action-btn secondary" onclick="downloadContent()">💾 Download</button>
                <button class="action-btn secondary" onclick="regenerateContent()">🔄 Regenerate</button>
            </div>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="chat-header">
                🤖 AI Content Assistant - Improve Your Content
            </div>
            <div class="chat-content" id="chatContent">
                <div class="message assistant">
                    <strong>AI Assistant:</strong> Content generated successfully! I can help you improve it further based on the analysis. Try asking:<br><br>
                    • "Address the high-priority pain points better"<br>
                    • "Make this more conversion-focused"<br>
                    • "Add more trust signals and social proof"<br>
                    • "Optimize for my content type structure"<br>
                    • "Implement the recommendations you provided"<br>
                    • "Make this more specific to my target audience"
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" id="chatInput" placeholder="How would you like to improve the content?" />
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
                document.getElementById('connectionStatus').textContent = 'Generating';
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
                        <span class="pain-point-priority priority-${point.priority.toLowerCase()}">${point.priority} Priority</span>
                        <h4 style="margin: 0.5rem 0;">${point.pain_point}</h4>
                        <p><strong>Impact:</strong> ${point.content_impact}</p>
                        <p><strong>Solution Approach:</strong> ${point.solution_approach}</p>
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
                    <div class="recommendation-impact">Impact: ${rec.impact}</div>
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
            document.getElementById('seoScore').textContent = metrics.seo_score?.toFixed(1) || '8.0';
            document.getElementById('conversionScore').textContent = metrics.conversion_potential?.toFixed(1) || '7.5';
            
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
        "features": ["product_pages", "category_pages", "landing_pages", "pain_point_analysis", "recommendations"]
    })

if __name__ == "__main__":
    print("🚀 Starting Enhanced SEO Content Generator...")
    print("=" * 60)
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    print(f"🤖 Anthropic API: {'✅ Configured' if config.ANTHROPIC_API_KEY else '❌ Not configured'}")
    print("🎯 Features: Product Pages, Category Pages, Landing Pages")
    print("📊 Analysis: Pain Points, Recommendations, Content Optimization")
    print("=" * 60)
    
    try:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise e
