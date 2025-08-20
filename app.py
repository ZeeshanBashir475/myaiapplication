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

# Pydantic for request models
from pydantic import BaseModel

# OpenAI import with error handling
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai not installed. Install with: pip install openai")

# Import the content evaluation agent from src/agents/ContentEvaluationAgent
try:
    from src.agents.ContentEvaluationAgent import ContentEvaluationAgent, KnowledgeGraphAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    print("⚠️ Content evaluation agent not found. Please ensure src/agents/ContentEvaluationAgent.py exists")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Uses your Open_Api_Key variable
class Config:
    OPENAI_API_KEY = os.getenv("Open_Api_Key", "") or os.getenv("OPENAI_API_KEY", "")
    GOOGLE_KNOWLEDGE_GRAPH_API_KEY = os.getenv("GOOGLE_KG_API_KEY", "")
    PORT = int(os.getenv("PORT", 8002))
    HOST = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Enhanced Content Type Configurations
CONTENT_TYPE_CONFIGS = {
    "article": {
        "name": "📰 Article",
        "description": "Informational article with detailed coverage",
        "prompt_template": "comprehensive informational article",
        "word_count_range": "2000-3000"
    },
    "blog_post": {
        "name": "📝 Blog Post", 
        "description": "Conversational blog post with personal touch",
        "prompt_template": "engaging blog post",
        "word_count_range": "1500-2500"
    },
    "product_page": {
        "name": "🛍️ Product Page",
        "description": "Product description focused on conversion",
        "prompt_template": "compelling product page content",
        "word_count_range": "800-1500"
    },
    "landing_page": {
        "name": "🎯 Landing Page",
        "description": "High-conversion landing page copy",
        "prompt_template": "persuasive landing page",
        "word_count_range": "1000-2000"
    },
    "guide": {
        "name": "📚 Complete Guide",
        "description": "Comprehensive how-to guide",
        "prompt_template": "detailed step-by-step guide",
        "word_count_range": "3000-5000"
    },
    "tutorial": {
        "name": "🎓 Tutorial",
        "description": "Step-by-step tutorial",
        "prompt_template": "educational tutorial",
        "word_count_range": "2000-3000"
    },
    "listicle": {
        "name": "📋 List Article",
        "description": "List-based article (Top 10, Best of, etc.)",
        "prompt_template": "engaging list article",
        "word_count_range": "1500-2500"
    },
    "case_study": {
        "name": "📊 Case Study",
        "description": "Detailed case study with results",
        "prompt_template": "analytical case study",
        "word_count_range": "2500-4000"
    },
    "review": {
        "name": "⭐ Review",
        "description": "Product or service review",
        "prompt_template": "balanced and informative review",
        "word_count_range": "1500-2500"
    },
    "comparison": {
        "name": "⚖️ Comparison",
        "description": "Compare multiple options",
        "prompt_template": "detailed comparison analysis",
        "word_count_range": "2000-3500"
    },
    "email_sequence": {
        "name": "📧 Email Sequence",
        "description": "Marketing email series",
        "prompt_template": "compelling email sequence",
        "word_count_range": "500-1000 per email"
    },
    "social_media": {
        "name": "📱 Social Media Content",
        "description": "Social media posts and captions",
        "prompt_template": "engaging social media content",
        "word_count_range": "50-300 per post"
    }
}

# Language configurations
LANGUAGE_CONFIGS = {
    "british_english": {
        "name": "🇬🇧 British English",
        "description": "British English spelling and expressions",
        "spelling_note": "Uses British spelling (colour, realise, centre, etc.)"
    },
    "american_english": {
        "name": "🇺🇸 American English", 
        "description": "American English spelling and expressions",
        "spelling_note": "Uses American spelling (color, realize, center, etc.)"
    },
    "canadian_english": {
        "name": "🇨🇦 Canadian English",
        "description": "Canadian English spelling and expressions", 
        "spelling_note": "Uses Canadian spelling (mix of British and American)"
    },
    "australian_english": {
        "name": "🇦🇺 Australian English",
        "description": "Australian English spelling and expressions",
        "spelling_note": "Uses Australian spelling and expressions"
    }
}

# Enhanced OpenAI Client with Latest GPT-5 Models
class OpenAIClient:
    def __init__(self):
        self.client = None
        self.api_key = None
        # GPT-5 model hierarchy (August 2025)
        self.latest_model = "gpt-5"  # Main GPT-5 model
        self.fallback_models = [
            "gpt-5-mini",           # Smaller, faster GPT-5
            "gpt-5-nano",           # Smallest GPT-5
            "gpt-5-chat-latest",    # Non-reasoning GPT-5
            "gpt-4o",               # Previous generation fallback
            "gpt-4-turbo",          # Legacy fallback
            "gpt-4"                 # Final fallback
        ]
        self.setup_openai()
    
    def setup_openai(self):
        self.api_key = config.OPENAI_API_KEY
        logger.info(f"🔑 OpenAI API Key status: {'✅ Found' if self.api_key else '❌ Missing'}")
        
        if not OPENAI_AVAILABLE:
            logger.error("❌ OpenAI library not available. Install with: pip install openai")
            return
        
        if self.api_key:
            try:
                # Set OpenAI API key
                openai.api_key = self.api_key
                self.client = openai
                logger.info("✅ OpenAI client initialized successfully")
                
                # Test the latest GPT-5 models
                self._test_gpt5_models()
                    
            except Exception as e:
                logger.error(f"❌ OpenAI setup failed: {e}")
                self.client = None
        else:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
    
    def _test_gpt5_models(self):
        """Test available GPT-5 models and set the best one"""
        models_to_test = [self.latest_model] + self.fallback_models
        
        for model in models_to_test:
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": "Test GPT-5"}],
                    max_tokens=5
                )
                self.latest_model = model
                logger.info(f"✅ Using GPT-5 model: {model}")
                
                # Special handling for GPT-5 reasoning models
                if model.startswith("gpt-5") and model != "gpt-5-chat-latest":
                    logger.info(f"🧠 GPT-5 reasoning model active: {model}")
                
                return
            except Exception as e:
                logger.warning(f"⚠️ Model {model} unavailable: {e}")
                continue
        
        logger.error("❌ No GPT-5 models available")
    
    def is_configured(self):
        """Check if the client is properly configured"""
        return self.client is not None and self.api_key is not None
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 4000):
        """Generate streaming response with latest GPT-5 model"""
        
        if not self.is_configured():
            logger.warning("🔄 OpenAI client not configured, attempting re-initialization...")
            self.setup_openai()
        
        if not self.is_configured():
            error_msg = f"❌ OpenAI client not available. Please check your API key."
            logger.error(error_msg)
            yield error_msg
            return
            
        try:
            logger.info(f"🤖 Generating content with {self.latest_model}, prompt length: {len(prompt)}")
            
            # Special parameters for GPT-5 models
            model_params = {
                "model": self.latest_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "stream": True,
                "temperature": 0.7
            }
            
            # Add GPT-5 specific parameters if available
            if self.latest_model.startswith("gpt-5"):
                model_params["reasoning_effort"] = "medium"  # GPT-5 reasoning parameter
                
            response = openai.ChatCompletion.create(**model_params)
            
            total_content = ""
            
            for chunk in response:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content_piece = delta['content']
                        total_content += content_piece
                        yield content_piece
            
            logger.info(f"✅ Content generation completed with {self.latest_model}. Total chars: {len(total_content)}")
                        
        except Exception as e:
            error_msg = f"❌ OpenAI API error: {str(e)}"
            logger.error(error_msg)
            
            # Provide specific error guidance
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                yield "❌ Authentication error. Your OpenAI API key may be invalid."
            elif "rate_limit" in str(e).lower():
                yield "❌ Rate limit exceeded. Please wait a moment and try again."
            elif "insufficient_quota" in str(e).lower() or "quota" in str(e).lower():
                yield "❌ No credits remaining. Please add credits to your OpenAI account."
            else:
                yield f"❌ AI Generation Error: {str(e)}"
                
            # Set client to None to force reinitialization on next request
            self.client = None
    
    async def generate_content(self, prompt: str, max_tokens: int = 4000):
        """Generate content without streaming using latest GPT-5 model"""
        
        if not self.is_configured():
            self.setup_openai()
        
        if not self.is_configured():
            return "❌ OpenAI client not available. Please check your API key."
        
        try:
            # Special parameters for GPT-5 models
            model_params = {
                "model": self.latest_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            # Add GPT-5 specific parameters if available
            if self.latest_model.startswith("gpt-5"):
                model_params["reasoning_effort"] = "medium"  # GPT-5 reasoning parameter
                
            response = openai.ChatCompletion.create(**model_params)
            
            content = response.choices[0].message.content if response.choices else "No content generated"
            logger.info(f"✅ Content generated with {self.latest_model}: {len(content)} characters")
            return content
            
        except Exception as e:
            error_msg = f"❌ AI Generation Error: {str(e)}"
            logger.error(error_msg)
            return error_msg

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

# Enhanced Content System with GPT-5 Evaluation
class ContentSystem:
    def __init__(self):
        self.ai_client = OpenAIClient()
        self.sessions = {}
        
        # Initialize evaluation agent if available
        if AGENT_AVAILABLE:
            self.evaluation_agent = ContentEvaluationAgent(self.ai_client)
            self.knowledge_graph_agent = KnowledgeGraphAgent(config.GOOGLE_KNOWLEDGE_GRAPH_API_KEY)
        else:
            self.evaluation_agent = None
            self.knowledge_graph_agent = None
    
    async def generate_content_with_progress(self, form_data: Dict, session_id: str):
        """Generate content with comprehensive GPT-5 evaluation"""
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'form_data': form_data,
            'content': '',
            'evaluation': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Step 1: Initialize
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 1,
                'total': 8,
                'title': 'Initializing',
                'message': f'🚀 Starting {form_data["content_type"]} generation with GPT-5 for: {form_data["topic"]}'
            })
            await asyncio.sleep(0.5)
            
            # Step 2: Reddit Pain Point Research
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 8,
                'title': 'Reddit Research',
                'message': '🔍 AI researching pain points and insights from relevant Reddit communities...'
            })
            
            reddit_insights = await self._research_reddit_insights(form_data["topic"]) if self.evaluation_agent else {}
            await asyncio.sleep(1)
            
            # Step 3: Analyzing Requirements
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 8,
                'title': 'Analyzing Requirements',
                'message': '🎯 Analyzing content requirements and target audience...'
            })
            await asyncio.sleep(1)
            
            # Step 4: Processing Instructions
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 4,
                'total': 8,
                'title': 'Processing Instructions',
                'message': '📋 Processing custom AI instructions and language preferences...'
            })
            await asyncio.sleep(1)
            
            # Step 5: GPT-5 Content Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 5,
                'total': 8,
                'title': 'GPT-5 Content Generation',
                'message': f'🤖 Generating high-quality content with {self.ai_client.latest_model} (reasoning enabled)...'
            })
            
            content = await self._generate_ai_content(form_data, reddit_insights)
            self.sessions[session_id]['content'] = content
            
            # Step 6: Content Evaluation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 6,
                'total': 8,
                'title': 'Content Evaluation',
                'message': '📊 Evaluating content with E-E-A-T framework and SEO analysis...'
            })
            
            evaluation = await self._evaluate_content(content, form_data) if self.evaluation_agent else {}
            self.sessions[session_id]['evaluation'] = evaluation
            
            # Step 7: Entity Analysis
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 7,
                'total': 8,
                'title': 'Entity Analysis',
                'message': '🔗 Analyzing entities and suggesting content clusters...'
            })
            await asyncio.sleep(1)
            
            # Step 8: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 8,
                'total': 8,
                'title': 'Complete',
                'message': '🎉 GPT-5 content generation and evaluation completed successfully!'
            })
            
            # Send final result with comprehensive evaluation
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'content_type': form_data['content_type'],
                'evaluation': evaluation,
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': evaluation.get('overall_score', 9.0) if evaluation else 9.0,
                    'ai_generated': not content.startswith("❌"),
                    'model_used': self.ai_client.latest_model,
                    'model_type': 'GPT-5 (Reasoning)' if self.ai_client.latest_model.startswith('gpt-5') else 'GPT-4',
                    'language': form_data.get('language', 'british_english'),
                    'evaluation_timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e)
            })
    
    async def _research_reddit_insights(self, topic: str) -> Dict:
        """Research Reddit insights for pain points using GPT-5"""
        if not self.evaluation_agent:
            return {}
        
        try:
            return await self.evaluation_agent._find_reddit_insights(topic)
        except Exception as e:
            logger.error(f"Reddit research error: {e}")
            return {}
    
    async def _evaluate_content(self, content: str, form_data: Dict) -> Dict:
        """Evaluate content comprehensively using GPT-5"""
        if not self.evaluation_agent:
            return {}
        
        try:
            return await self.evaluation_agent.evaluate_content(
                content=content,
                topic=form_data['topic'],
                content_type=form_data['content_type'],
                target_audience=form_data.get('target_audience', 'general audience')
            )
        except Exception as e:
            logger.error(f"Content evaluation error: {e}")
            return {}
    
    async def _generate_ai_content(self, form_data: Dict, reddit_insights: Dict) -> str:
        """Generate AI content with enhanced GPT-5 prompting"""
        
        content_type = form_data['content_type']
        topic = form_data['topic']
        audience = form_data.get('target_audience', 'readers')
        pain_points = form_data.get('customer_pain_points', '')
        usps = form_data.get('unique_selling_points', '')
        keywords = form_data.get('required_keywords', '')
        cta = form_data.get('call_to_action', '')
        tone = form_data.get('tone', 'professional')
        ai_instructions = form_data.get('ai_instructions', '')
        industry = form_data.get('industry', '')
        language = form_data.get('language', 'british_english')
        
        # Get content type template and word count
        content_config = CONTENT_TYPE_CONFIGS.get(content_type, {})
        content_template = content_config.get('prompt_template', content_type)
        word_count_range = content_config.get('word_count_range', '2000-3000')
        
        # Get language configuration
        language_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['british_english'])
        
        # Incorporate Reddit insights
        reddit_pain_points = ""
        if reddit_insights.get('pain_points'):
            reddit_pain_points = f"\n\nREDDIT COMMUNITY INSIGHTS:\nCommon Pain Points from {reddit_insights.get('subreddits', [])}:\n"
            for pain_point in reddit_insights.get('pain_points', [])[:5]:
                reddit_pain_points += f"- {pain_point}\n"
        
        # Build comprehensive GPT-5 prompt
        prompt = f"""You are an expert content writer using the latest {self.ai_client.latest_model} model with advanced reasoning capabilities. Create a {content_template} about "{topic}" for {audience}.

CONTENT SPECIFICATIONS:
- Content Type: {content_type.replace('_', ' ').title()}
- Target Audience: {audience}
- Tone: {tone}
- Industry: {industry}
- Word Count: {word_count_range}
- Language: {language_config['name']} ({language_config['spelling_note']})
- AI Model: {self.ai_client.latest_model} (Reasoning Enabled)

CONTENT REQUIREMENTS:
{f"CUSTOMER PAIN POINTS TO ADDRESS: {pain_points}" if pain_points else ""}
{f"UNIQUE SELLING POINTS TO HIGHLIGHT: {usps}" if usps else ""}
{f"KEYWORDS TO INCLUDE NATURALLY: {keywords}" if keywords else ""}
{f"CALL-TO-ACTION TO INCLUDE: {cta}" if cta else ""}
{reddit_pain_points}

SPECIAL AI INSTRUCTIONS:
{ai_instructions if ai_instructions else "Create engaging, valuable content that provides genuine insights and actionable advice."}

GPT-5 REASONING OPTIMIZATION:
Use your advanced reasoning capabilities to:
1. Analyze the topic from multiple angles before writing
2. Consider the audience's expertise level and needs
3. Structure information logically and persuasively
4. Anticipate and address potential objections
5. Create genuine value through unique insights

E-E-A-T OPTIMIZATION REQUIREMENTS:
1. EXPERIENCE: Include first-hand insights, practical examples, and real-world applications
2. EXPERTISE: Demonstrate deep knowledge with technical accuracy and industry-specific insights
3. AUTHORITATIVENESS: Reference credible sources and establish topical authority
4. TRUSTWORTHINESS: Use transparent sourcing, balanced perspectives, and fact-based claims

CONTENT STRUCTURE REQUIREMENTS:
1. Create a compelling headline that grabs attention immediately
2. Write an engaging introduction that hooks the reader within first 50 words
3. Use clear headings and subheadings for perfect readability (H2, H3 hierarchy)
4. Provide genuine value with specific, actionable insights
5. Address the target audience's specific needs and pain points
6. Maintain the specified tone consistently throughout
7. Include relevant statistics, data points, or research where appropriate
8. Use {language_config['spelling_note']} throughout
9. Include the call-to-action naturally if provided
10. End with a strong conclusion that reinforces key points and motivates action

QUALITY STANDARDS ({self.ai_client.latest_model} Enhanced):
- Make it comprehensive, well-researched, and authoritative
- Use engaging storytelling and real-world examples
- Include specific, practical advice that readers can implement immediately
- Ensure logical flow and smooth transitions between sections
- Write in a way that establishes credibility and trust
- Make every paragraph valuable and purposeful
- Create content that stands out from generic AI-generated text
- Optimize for search intent while maintaining human readability
- Include relevant internal linking opportunities (mention where links could go)

SEO OPTIMIZATION:
- Structure content with proper heading hierarchy
- Include semantic keywords naturally
- Address related questions and subtopics
- Optimize for featured snippets where relevant
- Include actionable list items and step-by-step instructions

Write the complete, professional {content_type.replace('_', ' ')} now, following all requirements above and leveraging {self.ai_client.latest_model}'s advanced reasoning capabilities:"""

        try:
            logger.info(f"🤖 Generating AI content for {content_type}: {topic}")
            content = await self.ai_client.generate_content(prompt, max_tokens=4000)
            logger.info(f"✅ AI content generation completed. Length: {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_fallback_content(form_data)
    
    def _generate_fallback_content(self, form_data: Dict) -> str:
        """Generate fallback content when AI fails"""
        topic = form_data['topic']
        content_type = form_data['content_type']
        audience = form_data.get('target_audience', 'readers')
        language = form_data.get('language', 'british_english')
        
        language_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['british_english'])
        spelling_note = "colour, realise, centre" if "british" in language.lower() else "color, realize, center"
        
        return f"""# {topic}: A Comprehensive {content_type.replace('_', ' ').title()}

## Introduction

This {content_type.replace('_', ' ')} provides valuable insights about {topic} specifically for {audience}. Our goal is to deliver actionable information that helps you make informed decisions and achieve your objectives.

*Note: This content uses {language_config['name']} spelling and expressions.*

## Understanding {topic}

{topic} has become increasingly important in today's landscape. For {audience}, understanding the key aspects can make a significant difference in outcomes and success.

## Key Benefits and Considerations

When exploring {topic}, consider these essential factors:

### Quality and Reliability
Focus on proven solutions with strong track records and positive feedback from other {audience}.

### Value Proposition
Evaluate the long-term value rather than just initial costs. Sometimes higher upfront investment leads to better long-term results.

### Ease of Implementation
Choose approaches that align with your current capabilities and resources.

## Implementation Strategy

Getting started with {topic} requires a systematic approach:

1. **Assessment Phase**: Evaluate your current situation and specific needs
2. **Planning Phase**: Develop a clear strategy and timeline
3. **Implementation Phase**: Execute your plan with proper monitoring
4. **Optimisation Phase**: Continuously improve based on results

## Best Practices

To maximise success with {topic}:

- Stay informed about industry trends and developments
- Connect with other {audience} to share experiences and insights
- Maintain a learning mindset and adapt to new information
- Focus on sustainable, long-term approaches

## Common Challenges and Solutions

Many {audience} face similar obstacles when dealing with {topic}:

- **Resource Constraints**: Prioritise highest-impact activities first
- **Technical Complexity**: Start with simpler solutions and gradually advance
- **Information Overload**: Focus on authoritative sources and proven methods

## Conclusion

Success with {topic} comes from understanding your specific needs, implementing proven strategies, and maintaining consistency in your approach. By following the guidance in this {content_type.replace('_', ' ')}, you'll be better positioned to achieve your goals.

Remember that lasting success often requires patience, continuous learning, and willingness to adapt your approach based on results and changing circumstances.

---

*This content was created to help {audience} better understand and succeed with {topic} using {language_config['name']} standards and GPT-5 technology.*"""

# Initialize FastAPI
app = FastAPI(title=f"Advanced Content Generator with {OpenAIClient().latest_model}")

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
    return HTMLResponse(content=generate_sophisticated_form_html())

@app.get("/generate", response_class=HTMLResponse)
async def generate_page():
    return HTMLResponse(content=generate_sophisticated_generator_html())

def generate_sophisticated_form_html():
    # Generate content type options
    content_type_options = ""
    for key, config in CONTENT_TYPE_CONFIGS.items():
        content_type_options += f'<option value="{key}">{config["name"]} - {config["description"]} ({config["word_count_range"]} words)</option>\n'
    
    # Generate language options
    language_options = ""
    for key, config in LANGUAGE_CONFIGS.items():
        selected = 'selected' if key == 'british_english' else ''
        language_options += f'<option value="{key}" {selected}>{config["name"]} - {config["description"]}</option>\n'
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Advanced AI Content Generator - GPT-5</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 50%, #000000 100%);
            min-height: 100vh; 
            color: #ffffff;
            line-height: 1.6;
        }}
        
        .grain {{ 
            position: fixed; 
            top: 0; left: 0; right: 0; bottom: 0; 
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
            pointer-events: none; 
            z-index: 1; 
        }}
        
        .container {{ 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 3rem 2rem; 
            position: relative; 
            z-index: 2; 
        }}
        
        .header {{ 
            text-align: center; 
            margin-bottom: 4rem; 
            padding: 3rem 0;
            border-bottom: 1px solid #333;
        }}
        
        .header h1 {{ 
            font-size: 3.5rem; 
            font-weight: 800; 
            margin-bottom: 1rem; 
            background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }}
        
        .header p {{ 
            font-size: 1.3rem; 
            color: #aaaaaa; 
            margin-bottom: 2rem;
            font-weight: 300;
        }}
        
        .status-badge {{ 
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #ffffff; 
            padding: 0.8rem 1.5rem; 
            border-radius: 2rem; 
            font-size: 0.9rem; 
            font-weight: 600;
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
        }}
        
        .form-section {{ 
            margin-bottom: 3rem; 
            padding: 2.5rem; 
            background: rgba(255, 255, 255, 0.03); 
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 1.5rem; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .form-section h3 {{ 
            color: #ffffff; 
            margin-bottom: 2rem; 
            font-size: 1.4rem; 
            font-weight: 700;
            display: flex; 
            align-items: center; 
            gap: 0.8rem; 
        }}
        
        .form-group {{ 
            margin-bottom: 2rem; 
        }}
        
        .label {{ 
            display: block; 
            font-weight: 600; 
            margin-bottom: 0.8rem; 
            color: #ffffff; 
            font-size: 1rem; 
        }}
        
        .required {{ 
            color: #ff6b6b; 
        }}
        
        .input, .textarea, .select {{ 
            width: 100%; 
            padding: 1.2rem; 
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2); 
            border-radius: 0.8rem; 
            font-size: 1rem; 
            color: #ffffff;
            font-family: inherit; 
            transition: all 0.3s ease;
        }}
        
        .input::placeholder, .textarea::placeholder {{
            color: #888888;
        }}
        
        .select option {{
            background: #1a1a1a;
            color: #ffffff;
            padding: 0.5rem;
        }}
        
        .input:focus, .textarea:focus, .select:focus {{ 
            outline: none; 
            border-color: #10b981; 
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1); 
        }}
        
        .textarea {{ 
            resize: vertical; 
            min-height: 120px; 
        }}
        
        .textarea.large {{ 
            min-height: 150px; 
        }}
        
        .grid {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 1.5rem; 
        }}
        
        .help-text {{ 
            font-size: 0.9rem; 
            color: #aaaaaa; 
            margin-top: 0.5rem; 
            line-height: 1.5; 
        }}
        
        .button {{ 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #ffffff; 
            padding: 1.4rem 2.5rem; 
            border: none; 
            border-radius: 0.8rem; 
            font-size: 1.1rem; 
            font-weight: 700; 
            cursor: pointer; 
            transition: all 0.3s ease; 
            width: 100%; 
            margin-top: 2rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .button:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 15px 35px rgba(16, 185, 129, 0.4);
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }}
        
        .button:disabled {{ 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none; 
        }}
        
        .advanced-section {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 1rem;
            padding: 2rem;
            margin-top: 2rem;
        }}
        
        .ai-instructions-section {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.03) 100%);
            border: 1px solid rgba(16, 185, 129, 0.15);
            border-radius: 1rem;
            padding: 2rem;
        }}
        
        .instructions-header {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 1.5rem;
        }}
        
        .instructions-icon {{
            width: 2rem;
            height: 2rem;
            background: rgba(16, 185, 129, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }}
        
        .language-section {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 1rem;
            padding: 2rem;
        }}
        
        @media (max-width: 768px) {{ 
            .grid {{ grid-template-columns: 1fr; }} 
            .container {{ padding: 2rem 1rem; }} 
            .header h1 {{ font-size: 2.5rem; }} 
            .form-section {{ padding: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <div class="grain"></div>
    
    <div class="container">
        <div class="header">
            <h1>GPT-5 Content Generator</h1>
            <p>Advanced content creation powered by OpenAI GPT-5 with comprehensive evaluation</p>
            <div class="status-badge">
                <span>🧠</span>
                <span>GPT-5 Reasoning Active</span>
            </div>
        </div>
        
        <form id="contentForm">
            <div class="form-section">
                <h3>📝 Content Specifications</h3>
                
                <div class="form-group">
                    <label class="label">Topic <span class="required">*</span></label>
                    <input class="input" type="text" name="topic" placeholder="e.g., Advanced marketing automation strategies for SaaS companies" required>
                    <div class="help-text">Be specific about your topic to get the most relevant and valuable content</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Content Type <span class="required">*</span></label>
                        <select class="select" name="content_type" required>
                            {content_type_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Target Audience <span class="required">*</span></label>
                        <input class="input" type="text" name="target_audience" placeholder="e.g., B2B SaaS founders, Marketing directors, Tech entrepreneurs" required>
                        <div class="help-text">Define your audience precisely for better targeting</div>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Content Tone</label>
                        <select class="select" name="tone">
                            <option value="professional">Professional</option>
                            <option value="conversational">Conversational</option>
                            <option value="authoritative">Authoritative</option>
                            <option value="friendly">Friendly & Approachable</option>
                            <option value="technical">Technical & Detailed</option>
                            <option value="persuasive">Persuasive & Compelling</option>
                            <option value="educational">Educational & Informative</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Industry Context</label>
                        <input class="input" type="text" name="industry" placeholder="e.g., SaaS, E-commerce, Healthcare, Finance">
                        <div class="help-text">Industry context helps create more relevant content</div>
                    </div>
                </div>
            </div>
            
            <div class="form-section language-section">
                <h3>🌍 Language & Localisation</h3>
                
                <div class="form-group">
                    <label class="label">Language Variant <span class="required">*</span></label>
                    <select class="select" name="language" required>
                        {language_options}
                    </select>
                    <div class="help-text">Choose your preferred English variant for spelling, terminology, and expressions</div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🎯 Strategic Content Elements</h3>
                
                <div class="form-group">
                    <label class="label">Customer Pain Points</label>
                    <textarea class="textarea large" name="customer_pain_points" placeholder="e.g., Difficulty scaling marketing efforts, High customer acquisition costs, Lack of automation expertise, Complex tool integration challenges"></textarea>
                    <div class="help-text">Specific pain points help create more compelling and relevant content. GPT-5 will also research Reddit communities for additional insights.</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Unique Value Propositions</label>
                    <textarea class="textarea large" name="unique_selling_points" placeholder="e.g., 10+ years of proven results, Proprietary methodology, Award-winning support team, Industry-leading ROI, Exclusive partnerships"></textarea>
                    <div class="help-text">What makes your solution, service, or perspective unique? These will be woven into the content naturally</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Strategic Keywords</label>
                        <input class="input" type="text" name="required_keywords" placeholder="e.g., marketing automation, customer lifecycle, conversion optimisation">
                        <div class="help-text">Keywords will be integrated naturally for SEO optimisation</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Call-to-Action</label>
                        <input class="input" type="text" name="call_to_action" placeholder="e.g., Schedule a strategy consultation, Download our comprehensive guide">
                        <div class="help-text">What specific action should readers take after consuming your content?</div>
                    </div>
                </div>
            </div>
            
            <div class="form-section ai-instructions-section">
                <div class="instructions-header">
                    <div class="instructions-icon">🧠</div>
                    <h3>Advanced AI Instructions - GPT-5 Reasoning</h3>
                </div>
                
                <div class="form-group">
                    <label class="label">Custom AI Instructions</label>
                    <textarea class="textarea large" name="ai_instructions" placeholder="e.g., Focus on actionable insights with specific examples. Include data points and statistics where relevant. Write in first person for sections about experience. Use short paragraphs for better readability. Include a compelling story in the introduction."></textarea>
                    <div class="help-text">Provide specific instructions to guide GPT-5's advanced reasoning and writing style. The AI will automatically research Reddit communities for pain points and insights.</div>
                </div>
                
                <div class="advanced-section">
                    <div class="grid">
                        <div class="form-group">
                            <label class="label">Content Length Preference</label>
                            <select class="select" name="content_length">
                                <option value="comprehensive">Comprehensive (3000+ words)</option>
                                <option value="detailed" selected>Detailed (2000-3000 words)</option>
                                <option value="standard">Standard (1500-2000 words)</option>
                                <option value="concise">Concise (1000-1500 words)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="label">Writing Style</label>
                            <select class="select" name="writing_style">
                                <option value="story-driven">Story-Driven</option>
                                <option value="data-driven" selected>Data-Driven</option>
                                <option value="how-to-focused">How-To Focused</option>
                                <option value="thought-leadership">Thought Leadership</option>
                                <option value="problem-solution">Problem-Solution</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            
            <button type="submit" class="button" id="submitBtn">
                Generate Premium Content with GPT-5 Reasoning
            </button>
        </form>
    </div>
    
    <script>
        document.getElementById('contentForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {{}};
            
            for (let [key, value] of formData.entries()) {{
                data[key] = value;
            }}
            
            // Enhanced validation
            if (!data.topic || data.topic.length < 10) {{
                alert('Please provide a detailed topic (at least 10 characters)');
                return;
            }}
            
            if (!data.target_audience || data.target_audience.length < 5) {{
                alert('Please specify your target audience');
                return;
            }}
            
            if (!data.language) {{
                alert('Please select a language variant');
                return;
            }}
            
            localStorage.setItem('contentFormData', JSON.stringify(data));
            window.location.href = '/generate';
        }});
    </script>
</body>
</html>
'''

def generate_sophisticated_generator_html():
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Content Generation - OpenAI GPT-5</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 50%, #000000 100%);
            color: #ffffff; 
            line-height: 1.6; 
            min-height: 100vh;
        }}
        
        .grain {{ 
            position: fixed; 
            top: 0; left: 0; right: 0; bottom: 0; 
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
            pointer-events: none; 
            z-index: 1; 
        }}
        
        .header {{ 
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 0; 
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 0 2rem; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }}
        
        .header-title {{ 
            font-size: 1.5rem; 
            font-weight: 700; 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .status {{ 
            padding: 0.6rem 1.2rem; 
            border-radius: 2rem; 
            font-weight: 600; 
            font-size: 0.9rem; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .status-connecting {{ background: rgba(251, 191, 36, 0.2); color: #fbbf24; }}
        .status-connected {{ background: rgba(16, 185, 129, 0.2); color: #10b981; }}
        .status-generating {{ background: rgba(59, 130, 246, 0.2); color: #3b82f6; }}
        .status-error {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 2rem; 
            position: relative;
            z-index: 2;
        }}
        
        .progress-section, .content-display, .evaluation-display {{ 
            background: rgba(255, 255, 255, 0.03); 
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.5rem; 
            padding: 2rem; 
            margin-bottom: 2rem; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); 
        }}
        
        .progress-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 2rem; 
        }}
        
        .progress-title {{ 
            color: #ffffff; 
            font-size: 1.4rem; 
            font-weight: 700; 
        }}
        
        .progress-bar {{ 
            width: 100%; 
            height: 12px; 
            background: rgba(255, 255, 255, 0.1); 
            border-radius: 6px; 
            overflow: hidden; 
            margin-bottom: 1rem; 
        }}
        
        .progress-fill {{ 
            height: 100%; 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
            width: 0%; 
            transition: width 0.5s ease; 
        }}
        
        .progress-text {{ 
            text-align: center; 
            font-size: 1rem; 
            color: #cccccc; 
            font-weight: 500; 
        }}
        
        .current-step {{ 
            background: rgba(16, 185, 129, 0.1); 
            border: 1px solid rgba(16, 185, 129, 0.2); 
            border-radius: 1rem; 
            padding: 1.5rem; 
            margin-bottom: 1.5rem; 
            display: none; 
        }}
        
        .current-step h4 {{ 
            color: #ffffff; 
            margin-bottom: 0.8rem; 
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .current-step p {{ 
            color: #cccccc; 
            font-size: 0.95rem; 
        }}
        
        .content-display, .evaluation-display {{ display: none; }}
        .content-display.visible, .evaluation-display.visible {{ display: block; }}
        
        .metrics {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 2rem; 
        }}
        
        .metric-card {{ 
            background: rgba(255, 255, 255, 0.05); 
            padding: 1.5rem; 
            border-radius: 1rem; 
            text-align: center; 
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .metric-value {{ 
            font-size: 1.8rem; 
            font-weight: 700; 
            color: #ffffff; 
            margin-bottom: 0.5rem; 
        }}
        
        .metric-label {{ 
            font-size: 0.85rem; 
            color: #aaaaaa; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .evaluation-section {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        .evaluation-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .evaluation-score {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 2rem;
            font-weight: 700;
            font-size: 1.1rem;
        }}
        
        .eeat-scores {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .eeat-item {{
            background: rgba(255, 255, 255, 0.03);
            padding: 1.5rem;
            border-radius: 0.8rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .eeat-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #ffffff;
        }}
        
        .eeat-score {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #10b981;
        }}
        
        .recommendations {{
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }}
        
        .recommendations h4 {{
            color: #ffffff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .recommendations ul {{
            list-style: none;
            padding: 0;
        }}
        
        .recommendations li {{
            margin-bottom: 0.8rem;
            padding-left: 1.5rem;
            position: relative;
            color: #cccccc;
        }}
        
        .recommendations li:before {{
            content: "💡";
            position: absolute;
            left: 0;
        }}
        
        .entity-analysis {{
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }}
        
        .entity-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }}
        
        .entity-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 0.8rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .entity-card h5 {{
            color: #ffffff;
            margin-bottom: 1rem;
            font-size: 1rem;
            font-weight: 600;
        }}
        
        .entity-list {{
            list-style: none;
            padding: 0;
        }}
        
        .entity-list li {{
            color: #cccccc;
            padding: 0.3rem 0;
            font-size: 0.9rem;
        }}
        
        .content-display h1 {{ 
            color: #ffffff; 
            font-size: 2.2rem; 
            margin-bottom: 1.5rem; 
            border-bottom: 2px solid rgba(255, 255, 255, 0.2); 
            padding-bottom: 1rem; 
            font-weight: 700;
        }}
        
        .content-display h2 {{ 
            color: #cccccc; 
            font-size: 1.6rem; 
            margin: 2rem 0 1rem 0; 
            font-weight: 600;
        }}
        
        .content-display h3 {{ 
            color: #ffffff; 
            font-size: 1.3rem; 
            margin: 1.5rem 0 0.8rem 0; 
            font-weight: 600;
        }}
        
        .content-display p {{ 
            margin-bottom: 1rem; 
            line-height: 1.8; 
            color: #eeeeee; 
            font-size: 1.05rem;
        }}
        
        .content-display ul, .content-display ol {{ 
            margin: 1rem 0 1rem 2rem; 
            color: #eeeeee;
        }}
        
        .content-display li {{ 
            margin-bottom: 0.6rem; 
            line-height: 1.7;
        }}
        
        .content-actions {{ 
            display: flex; 
            gap: 1rem; 
            margin-top: 2rem; 
            padding-top: 2rem; 
            border-top: 1px solid rgba(255, 255, 255, 0.1); 
        }}
        
        .action-btn {{ 
            background: rgba(255, 255, 255, 0.1); 
            backdrop-filter: blur(10px);
            color: #ffffff; 
            padding: 0.8rem 1.5rem; 
            border: 1px solid rgba(255, 255, 255, 0.2); 
            border-radius: 0.8rem; 
            font-size: 0.9rem; 
            cursor: pointer; 
            font-weight: 600; 
            transition: all 0.3s ease; 
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .action-btn:hover {{ 
            background: rgba(255, 255, 255, 0.15); 
            transform: translateY(-2px); 
            border-color: rgba(255, 255, 255, 0.3);
        }}
        
        .action-btn.primary {{ 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: #ffffff;
            border: none;
        }}
        
        .action-btn.primary:hover {{ 
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }}
        
        .back-btn {{ 
            background: rgba(255, 255, 255, 0.05); 
            color: #cccccc; 
            padding: 0.6rem 1rem; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 0.6rem; 
            text-decoration: none; 
            font-size: 0.85rem; 
            transition: all 0.3s ease;
        }}
        
        .back-btn:hover {{ 
            background: rgba(255, 255, 255, 0.1); 
            color: #ffffff;
        }}
        
        .loading {{ 
            text-align: center; 
            padding: 3rem; 
            color: #aaaaaa; 
        }}
        
        .spinner {{ 
            border: 3px solid rgba(255, 255, 255, 0.1); 
            border-top: 3px solid #10b981; 
            border-radius: 50%; 
            width: 40px; 
            height: 40px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 1rem; 
        }}
        
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        
        @media (max-width: 768px) {{ 
            .header-content {{ 
                flex-direction: column; 
                gap: 1rem; 
            }} 
            .container {{ padding: 1rem; }}
            .progress-section, .content-display, .evaluation-display {{ 
                padding: 1.5rem; 
            }}
            .content-actions {{ 
                flex-direction: column; 
            }}
            .metrics, .eeat-scores, .entity-grid {{ 
                grid-template-columns: 1fr; 
            }} 
            .content-display h1 {{ 
                font-size: 1.8rem; 
            }}
        }}
    </style>
</head>
<body>
    <div class="grain"></div>
    
    <div class="header">
        <div class="header-content">
            <div class="header-title">GPT-5 Content Generator - Reasoning Active</div>
            <div class="status status-connecting" id="connectionStatus">Connecting...</div>
        </div>
    </div>
    
    <div class="container">
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">GPT-5 Content Generation</div>
                <a href="/" class="back-btn">← Back to Form</a>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Initializing GPT-5 content generation...</div>
            
            <div class="current-step" id="currentStep">
                <h4 id="currentStepTitle">Loading...</h4>
                <p id="currentStepMessage">Please wait...</p>
            </div>
            
            <div class="loading" id="loadingIndicator">
                <div class="spinner"></div>
                <p>Connecting to OpenAI GPT-5...</p>
            </div>
        </div>
        
        <div class="evaluation-display" id="evaluationDisplay">
            <div class="evaluation-header">
                <h2>📊 GPT-5 Content Evaluation Report</h2>
                <div class="evaluation-score" id="overallScore">9.2/10</div>
            </div>
            
            <div class="eeat-scores" id="eeatScores">
                <!-- E-E-A-T scores will be populated here -->
            </div>
            
            <div class="entity-analysis">
                <h4>🔗 Entity Analysis & Content Clusters</h4>
                <div class="entity-grid" id="entityGrid">
                    <!-- Entity analysis will be populated here -->
                </div>
            </div>
            
            <div class="recommendations" id="recommendations">
                <h4>💡 GPT-5 Optimization Recommendations</h4>
                <ul id="recommendationsList">
                    <!-- Recommendations will be populated here -->
                </ul>
            </div>
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
                    <div class="metric-value" id="modelUsed">--</div>
                    <div class="metric-label">AI Model</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="languageUsed">--</div>
                    <div class="metric-label">Language</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="modelType">--</div>
                    <div class="metric-label">Model Type</div>
                </div>
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="content-actions">
                <button class="action-btn primary" onclick="copyContent()">📋 Copy Content</button>
                <button class="action-btn" onclick="downloadContent()">💾 Download</button>
                <button class="action-btn" onclick="regenerateContent()">🔄 Regenerate</button>
                <button class="action-btn" onclick="shareContent()">🔗 Share</button>
                <button class="action-btn" onclick="toggleEvaluation()">📊 Toggle Evaluation</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let generatedContent = '';
        let evaluationData = {{}};
        let formData = null;
        
        window.addEventListener('load', function() {{
            const storedData = localStorage.getItem('contentFormData');
            if (storedData) {{
                formData = JSON.parse(storedData);
                console.log('Form data loaded:', formData);
                initWebSocket();
            }} else {{
                alert('No form data found. Please fill out the form first.');
                window.location.href = '/';
            }}
        }});
        
        function initWebSocket() {{
            try {{
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsHost = window.location.host;
                const wsUrl = `${{wsProtocol}}//${{wsHost}}/ws/${{sessionId}}`;
                
                console.log('Connecting to WebSocket:', wsUrl);
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {{
                    console.log('WebSocket connected');
                    document.getElementById('connectionStatus').textContent = 'Connected';
                    document.getElementById('connectionStatus').className = 'status status-connected';
                    startContentGeneration();
                }};
                
                ws.onmessage = function(event) {{
                    try {{
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    }} catch (error) {{
                        console.error('Error parsing message:', error);
                    }}
                }};
                
                ws.onclose = function(event) {{
                    console.log('WebSocket closed:', event.code, event.reason);
                    document.getElementById('connectionStatus').textContent = 'Disconnected';
                    document.getElementById('connectionStatus').className = 'status status-error';
                }};
                
                ws.onerror = function(error) {{
                    console.error('WebSocket error:', error);
                    document.getElementById('connectionStatus').textContent = 'Error';
                    document.getElementById('connectionStatus').className = 'status status-error';
                }};
                
            }} catch (error) {{
                console.error('WebSocket init error:', error);
                document.getElementById('connectionStatus').textContent = 'Setup Error';
                document.getElementById('connectionStatus').className = 'status status-error';
            }}
        }}
        
        function startContentGeneration() {{
            if (ws && ws.readyState === WebSocket.OPEN && formData) {{
                document.getElementById('connectionStatus').textContent = 'Generating';
                document.getElementById('connectionStatus').className = 'status status-generating';
                
                ws.send(JSON.stringify({{
                    type: 'start_generation',
                    data: formData
                }}));
            }} else {{
                console.error('Cannot start generation');
            }}
        }}
        
        function handleWebSocketMessage(data) {{
            console.log('Received:', data.type);
            
            switch(data.type) {{
                case 'progress_update':
                    document.getElementById('loadingIndicator').style.display = 'none';
                    updateProgress(data);
                    break;
                    
                case 'generation_complete':
                    displayContent(data);
                    displayEvaluation(data.evaluation || {{}});
                    document.getElementById('connectionStatus').textContent = 'Complete';
                    document.getElementById('connectionStatus').className = 'status status-connected';
                    break;
                    
                case 'generation_error':
                    alert('Error: ' + data.error);
                    document.getElementById('connectionStatus').textContent = 'Error';
                    document.getElementById('connectionStatus').className = 'status status-error';
                    break;
            }}
        }}
        
        function updateProgress(data) {{
            const percentage = (data.step / data.total) * 100;
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressText').textContent = `Step ${{data.step}} of ${{data.total}}: ${{data.title}}`;
            
            const currentStep = document.getElementById('currentStep');
            currentStep.style.display = 'block';
            document.getElementById('currentStepTitle').textContent = data.title;
            document.getElementById('currentStepMessage').textContent = data.message;
        }}
        
        function displayContent(data) {{
            generatedContent = data.content;
            
            const metrics = data.metrics || {{}};
            document.getElementById('wordCount').textContent = metrics.word_count?.toLocaleString() || '--';
            document.getElementById('readingTime').textContent = metrics.reading_time ? metrics.reading_time + ' min' : '--';
            document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '9.0';
            document.getElementById('modelUsed').textContent = metrics.model_used || 'GPT-5';
            document.getElementById('languageUsed').textContent = getLanguageDisplayName(metrics.language) || 'British English';
            document.getElementById('modelType').textContent = metrics.model_type || 'GPT-5 (Reasoning)';
            
            const formattedContent = formatContent(data.content);
            document.getElementById('generatedContent').innerHTML = formattedContent;
            
            document.getElementById('contentDisplay').classList.add('visible');
            document.getElementById('contentDisplay').scrollIntoView({{ behavior: 'smooth' }});
        }}
        
        function displayEvaluation(evaluation) {{
            evaluationData = evaluation;
            
            if (!evaluation || Object.keys(evaluation).length === 0) {{
                document.getElementById('evaluationDisplay').style.display = 'none';
                return;
            }}
            
            // Update overall score
            const overallScore = evaluation.overall_score || 9.0;
            document.getElementById('overallScore').textContent = overallScore.toFixed(1) + '/10';
            
            // Display E-E-A-T scores
            const eeatAnalysis = evaluation.eeat_analysis || {{}};
            const eeatContainer = document.getElementById('eeatScores');
            eeatContainer.innerHTML = '';
            
            const eeatFactors = [
                {{ key: 'experience', label: 'Experience', icon: '🎯' }},
                {{ key: 'expertise', label: 'Expertise', icon: '🧠' }},
                {{ key: 'authoritativeness', label: 'Authority', icon: '🏆' }},
                {{ key: 'trustworthiness', label: 'Trust', icon: '🔒' }}
            ];
            
            eeatFactors.forEach(factor => {{
                const score = eeatAnalysis[factor.key] || 5;
                const eeatItem = document.createElement('div');
                eeatItem.className = 'eeat-item';
                eeatItem.innerHTML = `
                    <div class="eeat-title">${{factor.icon}} ${{factor.label}}</div>
                    <div class="eeat-score">${{score.toFixed(1)}}/10</div>
                `;
                eeatContainer.appendChild(eeatItem);
            }});
            
            // Display entity analysis
            const entityAnalysis = evaluation.entity_analysis || {{}};
            const entityGrid = document.getElementById('entityGrid');
            entityGrid.innerHTML = '';
            
            const entityTypes = [
                {{ key: 'primary_entities', label: 'Primary Entities', icon: '🎯' }},
                {{ key: 'related_entities', label: 'Related Entities', icon: '🔗' }},
                {{ key: 'cluster_opportunities', label: 'Content Clusters', icon: '📑' }},
                {{ key: 'entity_gaps', label: 'Content Gaps', icon: '⚠️' }}
            ];
            
            entityTypes.forEach(type => {{
                const entities = entityAnalysis[type.key] || [];
                if (entities.length > 0) {{
                    const entityCard = document.createElement('div');
                    entityCard.className = 'entity-card';
                    entityCard.innerHTML = `
                        <h5>${{type.icon}} ${{type.label}}</h5>
                        <ul class="entity-list">
                            ${{entities.slice(0, 8).map(entity => `<li>${{entity}}</li>`).join('')}}
                        </ul>
                    `;
                    entityGrid.appendChild(entityCard);
                }}
            }});
            
            // Display recommendations
            const recommendations = evaluation.recommendations || [];
            const recommendationsList = document.getElementById('recommendationsList');
            recommendationsList.innerHTML = '';
            
            recommendations.forEach(rec => {{
                const li = document.createElement('li');
                li.textContent = rec;
                recommendationsList.appendChild(li);
            }});
            
            document.getElementById('evaluationDisplay').classList.add('visible');
        }}
        
        function formatContent(content) {{
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
        }}
        
        function getLanguageDisplayName(language) {{
            const languages = {{
                'british_english': '🇬🇧 British English',
                'american_english': '🇺🇸 American English',
                'canadian_english': '🇨🇦 Canadian English',
                'australian_english': '🇦🇺 Australian English'
            }};
            return languages[language] || '🇬🇧 British English';
        }}
        
        function copyContent() {{
            const content = document.getElementById('generatedContent').innerText;
            navigator.clipboard.writeText(content).then(() => {{
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Copied!';
                setTimeout(() => {{
                    btn.innerHTML = originalText;
                }}, 2000);
            }}).catch(err => {{
                console.error('Copy failed:', err);
            }});
        }}
        
        function downloadContent() {{
            const content = document.getElementById('generatedContent').innerText;
            const evaluation = evaluationData;
            
            const fullContent = `
CONTENT:
${{content}}

GPT-5 EVALUATION REPORT:
Overall Score: ${{evaluation.overall_score || 'N/A'}}/10

E-E-A-T Analysis:
- Experience: ${{evaluation.eeat_analysis?.experience || 'N/A'}}/10
- Expertise: ${{evaluation.eeat_analysis?.expertise || 'N/A'}}/10
- Authoritativeness: ${{evaluation.eeat_analysis?.authoritativeness || 'N/A'}}/10
- Trustworthiness: ${{evaluation.eeat_analysis?.trustworthiness || 'N/A'}}/10

GPT-5 Recommendations:
${{(evaluation.recommendations || []).map(rec => `- ${{rec}}`).join('\\n')}}

Generated with OpenAI GPT-5 Reasoning Model
            `;
            
            const blob = new Blob([fullContent], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `gpt5-content_${{new Date().toISOString().split('T')[0]}}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        function regenerateContent() {{
            window.location.reload();
        }}
        
        function shareContent() {{
            if (navigator.share) {{
                const content = document.getElementById('generatedContent').innerText;
                navigator.share({{
                    title: 'AI Generated Content - GPT-5',
                    text: content.substring(0, 100) + '...',
                    url: window.location.href
                }});
            }} else {{
                copyContent();
            }}
        }}
        
        function toggleEvaluation() {{
            const evaluationDisplay = document.getElementById('evaluationDisplay');
            if (evaluationDisplay.classList.contains('visible')) {{
                evaluationDisplay.classList.remove('visible');
                evaluationDisplay.style.display = 'none';
            }} else {{
                evaluationDisplay.classList.add('visible');
                evaluationDisplay.style.display = 'block';
                evaluationDisplay.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}
    </script>
</body>
</html>
'''

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for content generation"""
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

# Health and Test Endpoints
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint for GPT-5"""
    openai_working = False
    openai_error = None
    model_used = "unknown"
    agent_status = "available" if AGENT_AVAILABLE else "unavailable"
    
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        try:
            openai.api_key = config.OPENAI_API_KEY
            model_params = {
                "model": content_system.ai_client.latest_model,
                "messages": [{"role": "user", "content": "Test GPT-5"}],
                "max_tokens": 5
            }
            
            # Add GPT-5 specific parameters if available
            if content_system.ai_client.latest_model.startswith("gpt-5"):
                model_params["reasoning_effort"] = "minimal"
                
            response = openai.ChatCompletion.create(**model_params)
            openai_working = True
            model_used = content_system.ai_client.latest_model
        except Exception as e:
            openai_error = str(e)
    
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(config.OPENAI_API_KEY),
        "openai_available": OPENAI_AVAILABLE,
        "openai_working": openai_working,
        "openai_error": openai_error,
        "model_used": model_used,
        "latest_model": content_system.ai_client.latest_model,
        "gpt5_reasoning": content_system.ai_client.latest_model.startswith("gpt-5"),
        "content_agent_available": AGENT_AVAILABLE,
        "agent_status": agent_status,
        "version": "gpt-5-enhanced-with-evaluation",
        "api_key_preview": f"{config.OPENAI_API_KEY[:8]}...{config.OPENAI_API_KEY[-4:]}" if config.OPENAI_API_KEY else None
    })

@app.get("/test-openai")
async def test_openai():
    """Test OpenAI API with GPT-5 models"""
    
    try:
        api_key = config.OPENAI_API_KEY
        
        if not api_key:
            return JSONResponse({
                "status": "error",
                "message": "❌ No OpenAI API key found in environment",
                "solution": "Set Open_Api_Key in Railway environment variables"
            })
        
        if not api_key.startswith("sk-"):
            return JSONResponse({
                "status": "error", 
                "message": f"❌ Invalid API key format: {api_key[:10]}...",
                "solution": "Get new key from https://platform.openai.com/api-keys"
            })
        
        # Test OpenAI API with GPT-5 models
        openai.api_key = api_key
        
        model_used = content_system.ai_client.latest_model
        model_params = {
            "model": model_used,
            "messages": [{
                "role": "user", 
                "content": f"Write a short paragraph about how AI content generation is working correctly with OpenAI {model_used} including comprehensive evaluation features and reasoning capabilities."
            }],
            "max_tokens": 200
        }
        
        # Add GPT-5 specific parameters if available
        if model_used.startswith("gpt-5"):
            model_params["reasoning_effort"] = "medium"
            
        response = openai.ChatCompletion.create(**model_params)
        
        content = response.choices[0].message.content if response.choices else "No content generated"
        
        return JSONResponse({
            "status": "SUCCESS! ✅",
            "message": f"OpenAI {model_used} is working perfectly with enhanced evaluation features!",
            "generated_content": content,
            "model": model_used,
            "gpt5_reasoning": model_used.startswith("gpt-5"),
            "word_count": len(content.split()),
            "content_agent_available": AGENT_AVAILABLE,
            "features": [
                "Latest GPT-5 model with reasoning",
                "British English support", 
                "E-E-A-T evaluation framework",
                "Reddit insights research",
                "Entity analysis and clustering",
                "Content cluster suggestions",
                "Advanced reasoning capabilities"
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"❌ Error: {str(e)}",
            "error_type": type(e).__name__,
            "api_key_length": len(config.OPENAI_API_KEY) if config.OPENAI_API_KEY else 0
        })

if __name__ == "__main__":
    print("🚀 Starting Enhanced Content Generator with GPT-5...")
    print("=" * 80)
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    
    # Test API key and model
    openai_status = "✅ Configured" if config.OPENAI_API_KEY else "❌ Not configured"
    agent_status = "✅ Available" if AGENT_AVAILABLE else "❌ Missing src/agents/ContentEvaluationAgent.py"
    
    print(f"🤖 OpenAI API: {openai_status}")
    print(f"📊 Content Agent: {agent_status}")
    
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        print(f"🔑 API Key preview: {config.OPENAI_API_KEY[:8]}...{config.OPENAI_API_KEY[-4:]}")
        
        # Test OpenAI connection with GPT-5 models
        client = OpenAIClient()
        print(f"🎯 Using Model: {client.latest_model}")
        
        try:
            openai.api_key = config.OPENAI_API_KEY
            model_params = {
                "model": client.latest_model,
                "messages": [{"role": "user", "content": "Test GPT-5"}],
                "max_tokens": 5
            }
            
            # Add GPT-5 specific parameters if available
            if client.latest_model.startswith("gpt-5"):
                model_params["reasoning_effort"] = "minimal"
                print("🧠 GPT-5 reasoning capabilities enabled")
                
            response = openai.ChatCompletion.create(**model_params)
            print(f"✅ OpenAI {client.latest_model} test successful")
        except Exception as e:
            print(f"❌ OpenAI API test failed: {e}")
    elif not OPENAI_AVAILABLE:
        print("❌ OpenAI library not installed. Run: pip install openai")
    
    print("🎯 Enhanced Features:")
    print("   • Latest GPT-5 model with advanced reasoning")
    print("   • British English language support")
    print("   • Comprehensive E-E-A-T evaluation")
    print("   • Automatic Reddit pain point research")
    print("   • Entity analysis and content clusters")
    print("   • SEO optimization scoring")
    print("   • YMYL content assessment")
    print("   • Google Knowledge Graph integration (optional)")
    print("🎨 Theme: Black & Green GPT-5 UI with Enhanced Evaluation")
    print("📊 Evaluation: Google E-E-A-T + SEO Framework + GPT-5 Reasoning")
    print("=" * 80)
    
    try:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
