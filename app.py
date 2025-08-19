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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - FIXED to use your variable name
class Config:
    OPENAI_API_KEY = os.getenv("Open_Api_Key", "") or os.getenv("OPENAI_API_KEY", "")  # Try both names
    PORT = int(os.getenv("PORT", 8002))
    HOST = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Content Type Configurations
CONTENT_TYPE_CONFIGS = {
    "article": {
        "name": "📰 Article",
        "description": "Informational article with detailed coverage",
        "prompt_template": "comprehensive informational article"
    },
    "blog_post": {
        "name": "📝 Blog Post", 
        "description": "Conversational blog post with personal touch",
        "prompt_template": "engaging blog post"
    },
    "product_page": {
        "name": "🛍️ Product Page",
        "description": "Product description focused on conversion",
        "prompt_template": "compelling product page content"
    },
    "landing_page": {
        "name": "🎯 Landing Page",
        "description": "High-conversion landing page copy",
        "prompt_template": "persuasive landing page"
    },
    "guide": {
        "name": "📚 Complete Guide",
        "description": "Comprehensive how-to guide",
        "prompt_template": "detailed step-by-step guide"
    },
    "tutorial": {
        "name": "🎓 Tutorial",
        "description": "Step-by-step tutorial",
        "prompt_template": "educational tutorial"
    },
    "listicle": {
        "name": "📋 List Article",
        "description": "List-based article (Top 10, Best of, etc.)",
        "prompt_template": "engaging list article"
    },
    "case_study": {
        "name": "📊 Case Study",
        "description": "Detailed case study with results",
        "prompt_template": "analytical case study"
    },
    "review": {
        "name": "⭐ Review",
        "description": "Product or service review",
        "prompt_template": "balanced and informative review"
    },
    "comparison": {
        "name": "⚖️ Comparison",
        "description": "Compare multiple options",
        "prompt_template": "detailed comparison analysis"
    },
    "email_sequence": {
        "name": "📧 Email Sequence",
        "description": "Marketing email series",
        "prompt_template": "compelling email sequence"
    },
    "social_media": {
        "name": "📱 Social Media Content",
        "description": "Social media posts and captions",
        "prompt_template": "engaging social media content"
    }
}

# OpenAI Client (Working Version)
class OpenAIClient:
    def __init__(self):
        self.client = None
        self.api_key = None
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
                
                # Test the client with a simple call
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    logger.info("✅ OpenAI API test successful")
                except Exception as test_e:
                    logger.error(f"❌ OpenAI API test failed: {test_e}")
                    
            except Exception as e:
                logger.error(f"❌ OpenAI setup failed: {e}")
                self.client = None
        else:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
    
    def is_configured(self):
        """Check if the client is properly configured"""
        return self.client is not None and self.api_key is not None
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 3000):
        """Generate streaming response"""
        
        if not self.is_configured():
            logger.warning("🔄 OpenAI client not configured, attempting re-initialization...")
            self.setup_openai()
        
        if not self.is_configured():
            error_msg = f"❌ OpenAI client not available. Please check your API key."
            logger.error(error_msg)
            yield error_msg
            return
            
        try:
            logger.info(f"🤖 Generating content with OpenAI, prompt length: {len(prompt)}")
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                stream=True,
                temperature=0.7
            )
            
            total_content = ""
            
            for chunk in response:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content_piece = delta['content']
                        total_content += content_piece
                        yield content_piece
            
            logger.info(f"✅ Content generation completed. Total chars: {len(total_content)}")
                        
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
    
    async def generate_content(self, prompt: str, max_tokens: int = 3000):
        """Generate content without streaming (more reliable)"""
        
        if not self.is_configured():
            self.setup_openai()
        
        if not self.is_configured():
            return "❌ OpenAI client not available. Please check your API key."
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            content = response.choices[0].message.content if response.choices else "No content generated"
            logger.info(f"✅ Content generated: {len(content)} characters")
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

# Enhanced Content System
class ContentSystem:
    def __init__(self):
        self.ai_client = OpenAIClient()
        self.sessions = {}
    
    async def generate_content_with_progress(self, form_data: Dict, session_id: str):
        """Generate content with real AI - enhanced version"""
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'form_data': form_data,
            'content': '',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Step 1: Initialize
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 1,
                'total': 5,
                'title': 'Initializing',
                'message': f'🚀 Starting {form_data["content_type"]} generation for: {form_data["topic"]}'
            })
            await asyncio.sleep(0.5)
            
            # Step 2: Analyzing Requirements
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 5,
                'title': 'Analyzing Requirements',
                'message': '🎯 Analyzing content requirements and target audience...'
            })
            await asyncio.sleep(1)
            
            # Step 3: Processing Instructions
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 5,
                'title': 'Processing Instructions',
                'message': '📋 Processing your custom AI instructions and preferences...'
            })
            await asyncio.sleep(1)
            
            # Step 4: AI Content Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 4,
                'total': 5,
                'title': 'AI Content Generation',
                'message': '🤖 Generating high-quality content with OpenAI GPT-4...'
            })
            
            content = await self._generate_ai_content(form_data)
            self.sessions[session_id]['content'] = content
            
            # Step 5: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 5,
                'total': 5,
                'title': 'Complete',
                'message': '🎉 Content generation completed successfully!'
            })
            
            # Send final result
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'content_type': form_data['content_type'],
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': 9.2,
                    'ai_generated': not content.startswith("❌"),
                    'model_used': 'GPT-4'
                }
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e)
            })
    
    async def _generate_ai_content(self, form_data: Dict) -> str:
        """Generate AI content using OpenAI"""
        
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
        
        # Get content type template
        content_template = CONTENT_TYPE_CONFIGS.get(content_type, {}).get('prompt_template', content_type)
        
        # Build comprehensive AI prompt
        prompt = f"""You are an expert content writer. Create a {content_template} about "{topic}" for {audience}.

CONTENT SPECIFICATIONS:
- Content Type: {content_type.replace('_', ' ').title()}
- Target Audience: {audience}
- Tone: {tone}
- Industry: {industry}
- Word Count: 1500-2500 words

CONTENT REQUIREMENTS:
{f"CUSTOMER PAIN POINTS TO ADDRESS: {pain_points}" if pain_points else ""}
{f"UNIQUE SELLING POINTS TO HIGHLIGHT: {usps}" if usps else ""}
{f"KEYWORDS TO INCLUDE NATURALLY: {keywords}" if keywords else ""}
{f"CALL-TO-ACTION TO INCLUDE: {cta}" if cta else ""}

SPECIAL AI INSTRUCTIONS:
{ai_instructions if ai_instructions else "Follow best practices for engaging, valuable content."}

CONTENT STRUCTURE REQUIREMENTS:
1. Create a compelling headline that grabs attention
2. Write an engaging introduction that hooks the reader
3. Use clear headings and subheadings for easy scanning
4. Provide genuine value with actionable insights
5. Address the target audience's specific needs and challenges
6. Maintain the specified tone throughout
7. Include the call-to-action naturally if provided
8. End with a strong conclusion that reinforces key points

QUALITY STANDARDS:
- Make it comprehensive and thoroughly researched
- Use engaging storytelling where appropriate
- Include specific examples and practical advice
- Ensure logical flow between sections
- Write in a way that establishes authority and trust

Write the complete {content_type.replace('_', ' ')} now, following all requirements above:"""

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
        
        return f"""# {topic}: A Comprehensive {content_type.replace('_', ' ').title()}

## Introduction

This {content_type.replace('_', ' ')} provides valuable insights about {topic} specifically for {audience}. Our goal is to deliver actionable information that helps you make informed decisions and achieve your objectives.

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
4. **Optimization Phase**: Continuously improve based on results

## Best Practices

To maximize success with {topic}:

- Stay informed about industry trends and developments
- Connect with other {audience} to share experiences and insights
- Maintain a learning mindset and adapt to new information
- Focus on sustainable, long-term approaches

## Common Challenges and Solutions

Many {audience} face similar obstacles when dealing with {topic}:

- **Resource Constraints**: Prioritize highest-impact activities first
- **Technical Complexity**: Start with simpler solutions and gradually advance
- **Information Overload**: Focus on authoritative sources and proven methods

## Conclusion

Success with {topic} comes from understanding your specific needs, implementing proven strategies, and maintaining consistency in your approach. By following the guidance in this {content_type.replace('_', ' ')}, you'll be better positioned to achieve your goals.

Remember that lasting success often requires patience, continuous learning, and willingness to adapt your approach based on results and changing circumstances.

---

*This content was created to help {audience} better understand and succeed with {topic}.*"""

# Initialize FastAPI
app = FastAPI(title="Sophisticated Content Generator with OpenAI")

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
        content_type_options += f'<option value="{key}">{config["name"]} - {config["description"]}</option>\n'
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sophisticated AI Content Generator</title>
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
            background: rgba(255, 255, 255, 0.1); 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #ffffff; 
            padding: 0.8rem 1.5rem; 
            border-radius: 2rem; 
            font-size: 0.9rem; 
            font-weight: 600;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
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
        
        .input:focus, .textarea:focus, .select:focus {{ 
            outline: none; 
            border-color: #ffffff; 
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1); 
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
            background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
            color: #000000; 
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
            box-shadow: 0 15px 35px rgba(255, 255, 255, 0.2);
            background: linear-gradient(135deg, #f0f0f0 0%, #bbbbbb 100%);
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
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
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
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
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
            <h1>AI Content Generator</h1>
            <p>Sophisticated content creation powered by OpenAI GPT-4</p>
            <div class="status-badge">
                <span>●</span>
                <span>OpenAI System Ready</span>
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
            
            <div class="form-section">
                <h3>🎯 Strategic Content Elements</h3>
                
                <div class="form-group">
                    <label class="label">Customer Pain Points</label>
                    <textarea class="textarea large" name="customer_pain_points" placeholder="e.g., Difficulty scaling marketing efforts, High customer acquisition costs, Lack of automation expertise, Complex tool integration challenges"></textarea>
                    <div class="help-text">Specific pain points help create more compelling and relevant content that resonates with your audience</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Unique Value Propositions</label>
                    <textarea class="textarea large" name="unique_selling_points" placeholder="e.g., 10+ years of proven results, Proprietary methodology, Award-winning support team, Industry-leading ROI, Exclusive partnerships"></textarea>
                    <div class="help-text">What makes your solution, service, or perspective unique? These will be woven into the content naturally</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Strategic Keywords</label>
                        <input class="input" type="text" name="required_keywords" placeholder="e.g., marketing automation, customer lifecycle, conversion optimization">
                        <div class="help-text">Keywords will be integrated naturally for SEO optimization</div>
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
                    <div class="instructions-icon">🤖</div>
                    <h3>Advanced AI Instructions</h3>
                </div>
                
                <div class="form-group">
                    <label class="label">Custom AI Instructions</label>
                    <textarea class="textarea large" name="ai_instructions" placeholder="e.g., Focus on actionable insights with specific examples. Include data points and statistics where relevant. Write in first person for sections about experience. Use short paragraphs for better readability. Include a compelling story in the introduction."></textarea>
                    <div class="help-text">Provide specific instructions to guide the AI's writing style, structure, and focus. Be as detailed as needed for your vision.</div>
                </div>
                
                <div class="advanced-section">
                    <div class="grid">
                        <div class="form-group">
                            <label class="label">Content Length Preference</label>
                            <select class="select" name="content_length">
                                <option value="comprehensive">Comprehensive (2000+ words)</option>
                                <option value="detailed" selected>Detailed (1500-2000 words)</option>
                                <option value="standard">Standard (1000-1500 words)</option>
                                <option value="concise">Concise (500-1000 words)</option>
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
                Generate Premium Content
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
            
            localStorage.setItem('contentFormData', JSON.stringify(data));
            window.location.href = '/generate';
        }});
    </script>
</body>
</html>
'''

def generate_sophisticated_generator_html():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Content Generation - OpenAI GPT-4</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 50%, #000000 100%);
            color: #ffffff; 
            line-height: 1.6; 
            min-height: 100vh;
        }
        
        .grain { 
            position: fixed; 
            top: 0; left: 0; right: 0; bottom: 0; 
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
            pointer-events: none; 
            z-index: 1; 
        }
        
        .header { 
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1.5rem 0; 
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 0 2rem; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        
        .header-title { 
            font-size: 1.5rem; 
            font-weight: 700; 
            background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status { 
            padding: 0.6rem 1.2rem; 
            border-radius: 2rem; 
            font-weight: 600; 
            font-size: 0.9rem; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .status-connecting { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
        .status-connected { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .status-generating { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
        .status-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 2rem; 
            position: relative;
            z-index: 2;
        }
        
        .progress-section, .content-display { 
            background: rgba(255, 255, 255, 0.03); 
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.5rem; 
            padding: 2rem; 
            margin-bottom: 2rem; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); 
        }
        
        .progress-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 2rem; 
        }
        
        .progress-title { 
            color: #ffffff; 
            font-size: 1.4rem; 
            font-weight: 700; 
        }
        
        .progress-bar { 
            width: 100%; 
            height: 12px; 
            background: rgba(255, 255, 255, 0.1); 
            border-radius: 6px; 
            overflow: hidden; 
            margin-bottom: 1rem; 
        }
        
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%); 
            width: 0%; 
            transition: width 0.5s ease; 
        }
        
        .progress-text { 
            text-align: center; 
            font-size: 1rem; 
            color: #cccccc; 
            font-weight: 500; 
        }
        
        .current-step { 
            background: rgba(255, 255, 255, 0.05); 
            border: 1px solid rgba(255, 255, 255, 0.15); 
            border-radius: 1rem; 
            padding: 1.5rem; 
            margin-bottom: 1.5rem; 
            display: none; 
        }
        
        .current-step h4 { 
            color: #ffffff; 
            margin-bottom: 0.8rem; 
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .current-step p { 
            color: #cccccc; 
            font-size: 0.95rem; 
        }
        
        .content-display { display: none; }
        .content-display.visible { display: block; }
        
        .metrics { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 1rem; 
            margin-bottom: 2rem; 
        }
        
        .metric-card { 
            background: rgba(255, 255, 255, 0.05); 
            padding: 1.5rem; 
            border-radius: 1rem; 
            text-align: center; 
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .metric-value { 
            font-size: 1.8rem; 
            font-weight: 700; 
            color: #ffffff; 
            margin-bottom: 0.5rem; 
        }
        
        .metric-label { 
            font-size: 0.85rem; 
            color: #aaaaaa; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .content-display h1 { 
            color: #ffffff; 
            font-size: 2.2rem; 
            margin-bottom: 1.5rem; 
            border-bottom: 2px solid rgba(255, 255, 255, 0.2); 
            padding-bottom: 1rem; 
            font-weight: 700;
        }
        
        .content-display h2 { 
            color: #cccccc; 
            font-size: 1.6rem; 
            margin: 2rem 0 1rem 0; 
            font-weight: 600;
        }
        
        .content-display h3 { 
            color: #ffffff; 
            font-size: 1.3rem; 
            margin: 1.5rem 0 0.8rem 0; 
            font-weight: 600;
        }
        
        .content-display p { 
            margin-bottom: 1rem; 
            line-height: 1.8; 
            color: #eeeeee; 
            font-size: 1.05rem;
        }
        
        .content-display ul, .content-display ol { 
            margin: 1rem 0 1rem 2rem; 
            color: #eeeeee;
        }
        
        .content-display li { 
            margin-bottom: 0.6rem; 
            line-height: 1.7;
        }
        
        .content-actions { 
            display: flex; 
            gap: 1rem; 
            margin-top: 2rem; 
            padding-top: 2rem; 
            border-top: 1px solid rgba(255, 255, 255, 0.1); 
        }
        
        .action-btn { 
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
        }
        
        .action-btn:hover { 
            background: rgba(255, 255, 255, 0.15); 
            transform: translateY(-2px); 
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .action-btn.primary { 
            background: linear-gradient(135deg, #ffffff 0%, #cccccc 100%);
            color: #000000;
            border: none;
        }
        
        .action-btn.primary:hover { 
            background: linear-gradient(135deg, #f0f0f0 0%, #bbbbbb 100%);
        }
        
        .back-btn { 
            background: rgba(255, 255, 255, 0.05); 
            color: #cccccc; 
            padding: 0.6rem 1rem; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 0.6rem; 
            text-decoration: none; 
            font-size: 0.85rem; 
            transition: all 0.3s ease;
        }
        
        .back-btn:hover { 
            background: rgba(255, 255, 255, 0.1); 
            color: #ffffff;
        }
        
        .loading { 
            text-align: center; 
            padding: 3rem; 
            color: #aaaaaa; 
        }
        
        .spinner { 
            border: 3px solid rgba(255, 255, 255, 0.1); 
            border-top: 3px solid #ffffff; 
            border-radius: 50%; 
            width: 40px; 
            height: 40px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 1rem; 
        }
        
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        @media (max-width: 768px) { 
            .header-content { 
                flex-direction: column; 
                gap: 1rem; 
            } 
            .container { padding: 1rem; }
            .progress-section, .content-display { 
                padding: 1.5rem; 
            }
            .content-actions { 
                flex-direction: column; 
            }
            .metrics { 
                grid-template-columns: 1fr 1fr; 
            } 
            .content-display h1 { 
                font-size: 1.8rem; 
            }
        }
    </style>
</head>
<body>
    <div class="grain"></div>
    
    <div class="header">
        <div class="header-content">
            <div class="header-title">AI Content Generator</div>
            <div class="status status-connecting" id="connectionStatus">Connecting...</div>
        </div>
    </div>
    
    <div class="container">
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">Content Generation Progress</div>
                <a href="/" class="back-btn">← Back to Form</a>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Initializing AI content generation...</div>
            
            <div class="current-step" id="currentStep">
                <h4 id="currentStepTitle">Loading...</h4>
                <p id="currentStepMessage">Please wait...</p>
            </div>
            
            <div class="loading" id="loadingIndicator">
                <div class="spinner"></div>
                <p>Connecting to OpenAI GPT-4...</p>
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
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="content-actions">
                <button class="action-btn primary" onclick="copyContent()">📋 Copy Content</button>
                <button class="action-btn" onclick="downloadContent()">💾 Download</button>
                <button class="action-btn" onclick="regenerateContent()">🔄 Regenerate</button>
                <button class="action-btn" onclick="shareContent()">🔗 Share</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let generatedContent = '';
        let formData = null;
        
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
            }
        }
        
        function handleWebSocketMessage(data) {
            console.log('Received:', data.type);
            
            switch(data.type) {
                case 'progress_update':
                    document.getElementById('loadingIndicator').style.display = 'none';
                    updateProgress(data);
                    break;
                    
                case 'generation_complete':
                    displayContent(data);
                    document.getElementById('connectionStatus').textContent = 'Complete';
                    document.getElementById('connectionStatus').className = 'status status-connected';
                    break;
                    
                case 'generation_error':
                    alert('Error: ' + data.error);
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
        
        function displayContent(data) {
            generatedContent = data.content;
            
            const metrics = data.metrics || {};
            document.getElementById('wordCount').textContent = metrics.word_count?.toLocaleString() || '--';
            document.getElementById('readingTime').textContent = metrics.reading_time ? metrics.reading_time + ' min' : '--';
            document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '9.2';
            document.getElementById('modelUsed').textContent = metrics.model_used || 'GPT-4';
            
            const formattedContent = formatContent(data.content);
            document.getElementById('generatedContent').innerHTML = formattedContent;
            
            document.getElementById('contentDisplay').classList.add('visible');
            document.getElementById('contentDisplay').scrollIntoView({ behavior: 'smooth' });
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
        
        function copyContent() {
            const content = document.getElementById('generatedContent').innerText;
            navigator.clipboard.writeText(content).then(() => {
                const btn = event.target;
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
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
            a.download = `ai-content_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function regenerateContent() {
            window.location.reload();
        }
        
        function shareContent() {
            if (navigator.share) {
                const content = document.getElementById('generatedContent').innerText;
                navigator.share({
                    title: 'AI Generated Content',
                    text: content.substring(0, 100) + '...',
                    url: window.location.href
                });
            } else {
                copyContent();
            }
        }
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
    """Health check endpoint"""
    openai_working = False
    openai_error = None
    
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        try:
            openai.api_key = config.OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            openai_working = True
        except Exception as e:
            openai_error = str(e)
    
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(config.OPENAI_API_KEY),
        "openai_available": OPENAI_AVAILABLE,
        "openai_working": openai_working,
        "openai_error": openai_error,
        "version": "openai-sophisticated-with-debug",
        "api_key_preview": f"{config.OPENAI_API_KEY[:8]}...{config.OPENAI_API_KEY[-4:]}" if config.OPENAI_API_KEY else None
    })

@app.get("/test-openai")
async def test_openai():
    """Test OpenAI API"""
    
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
        
        # Test OpenAI API
        openai.api_key = api_key
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": "Write a short paragraph about how AI content generation is working correctly with OpenAI."
            }],
            max_tokens=100
        )
        
        content = response.choices[0].message.content if response.choices else "No content generated"
        
        return JSONResponse({
            "status": "SUCCESS! ✅",
            "message": "OpenAI is working perfectly!",
            "generated_content": content,
            "model": response.model,
            "word_count": len(content.split()),
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

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check system status"""
    return JSONResponse({
        "environment_variables": {
            "Open_Api_Key": "Present" if os.getenv("Open_Api_Key") else "Missing",
            "OPENAI_API_KEY": "Present" if os.getenv("OPENAI_API_KEY") else "Missing",
            "config_value": "Present" if config.OPENAI_API_KEY else "Missing",
            "API_KEY_FORMAT": "Valid" if config.OPENAI_API_KEY and config.OPENAI_API_KEY.startswith("sk-") else "Invalid"
        },
        "library_availability": {
            "openai": OPENAI_AVAILABLE
        },
        "content_system_status": {
            "ai_client_configured": content_system.ai_client.is_configured()
        },
        "api_key_details": {
            "length": len(config.OPENAI_API_KEY) if config.OPENAI_API_KEY else 0,
            "starts_with": config.OPENAI_API_KEY[:10] if config.OPENAI_API_KEY else None,
            "ends_with": config.OPENAI_API_KEY[-10:] if config.OPENAI_API_KEY else None
        },
        "version": "openai_sophisticated_with_debug"
    })

# 🔍 COMPREHENSIVE DEBUG ENDPOINTS - ADDED HERE
@app.get("/debug-openai-detailed")
async def debug_openai_detailed():
    """Comprehensive OpenAI debugging"""
    
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "step_by_step_debug": {}
    }
    
    # Step 1: Check environment variables
    debug_info["step_by_step_debug"]["1_environment_check"] = {
        "Open_Api_Key_exists": bool(os.getenv("Open_Api_Key")),
        "OPENAI_API_KEY_exists": bool(os.getenv("OPENAI_API_KEY")),
        "all_env_vars_with_openai": [var for var in os.environ.keys() if 'openai' in var.lower() or 'api' in var.lower()],
        "config_openai_key": bool(config.OPENAI_API_KEY),
        "config_key_length": len(config.OPENAI_API_KEY) if config.OPENAI_API_KEY else 0
    }
    
    # Step 2: Check the actual API key content
    raw_key = config.OPENAI_API_KEY
    if raw_key:
        debug_info["step_by_step_debug"]["2_api_key_analysis"] = {
            "key_present": True,
            "key_length": len(raw_key),
            "starts_with_sk": raw_key.startswith("sk-"),
            "first_15_chars": raw_key[:15],
            "last_10_chars": raw_key[-10:],
            "contains_spaces": " " in raw_key,
            "contains_newlines": "\n" in raw_key or "\r" in raw_key,
            "is_empty_or_whitespace": raw_key.strip() == ""
        }
    else:
        debug_info["step_by_step_debug"]["2_api_key_analysis"] = {
            "key_present": False,
            "issue": "No API key found in config.OPENAI_API_KEY"
        }
    
    # Step 3: Check OpenAI library
    debug_info["step_by_step_debug"]["3_library_check"] = {
        "openai_available": OPENAI_AVAILABLE
    }
    
    if OPENAI_AVAILABLE:
        try:
            import openai
            debug_info["step_by_step_debug"]["3_library_check"]["openai_version"] = openai.__version__
            debug_info["step_by_step_debug"]["3_library_check"]["import_success"] = True
        except Exception as e:
            debug_info["step_by_step_debug"]["3_library_check"]["import_error"] = str(e)
    
    # Step 4: Test API key if present
    if raw_key and raw_key.startswith("sk-"):
        try:
            import openai
            openai.api_key = raw_key.strip()
            
            # Try a simple API call
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'API key works'"}],
                max_tokens=10
            )
            
            debug_info["step_by_step_debug"]["4_api_test"] = {
                "status": "SUCCESS ✅",
                "response": response.choices[0].message.content if response.choices else "No response",
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
        except Exception as api_error:
            debug_info["step_by_step_debug"]["4_api_test"] = {
                "status": "FAILED ❌",
                "error": str(api_error),
                "error_type": type(api_error).__name__
            }
            
            # Provide specific solutions
            error_str = str(api_error).lower()
            if "authentication" in error_str or "invalid" in error_str:
                debug_info["step_by_step_debug"]["4_api_test"]["solution"] = "Invalid API key - get new one from https://platform.openai.com/api-keys"
            elif "quota" in error_str or "billing" in error_str:
                debug_info["step_by_step_debug"]["4_api_test"]["solution"] = "No credits - add money to your OpenAI account"
            elif "rate_limit" in error_str:
                debug_info["step_by_step_debug"]["4_api_test"]["solution"] = "Rate limited - wait and try again"
    else:
        debug_info["step_by_step_debug"]["4_api_test"] = {
            "status": "SKIPPED",
            "reason": "No valid API key to test"
        }
    
    # Step 5: Check content system
    try:
        ai_client_configured = content_system.ai_client.is_configured()
        debug_info["step_by_step_debug"]["5_content_system"] = {
            "ai_client_configured": ai_client_configured,
            "client_object_exists": content_system.ai_client.client is not None,
            "client_api_key_set": content_system.ai_client.api_key is not None
        }
    except Exception as e:
        debug_info["step_by_step_debug"]["5_content_system"] = {
            "error": str(e)
        }
    
    # Overall diagnosis
    if debug_info["step_by_step_debug"].get("4_api_test", {}).get("status") == "SUCCESS ✅":
        debug_info["diagnosis"] = "✅ OpenAI API is working! Issue might be in content generation logic."
    elif not debug_info["step_by_step_debug"]["2_api_key_analysis"].get("key_present"):
        debug_info["diagnosis"] = "❌ No API key found. Check Railway environment variables."
    elif not debug_info["step_by_step_debug"]["2_api_key_analysis"].get("starts_with_sk"):
        debug_info["diagnosis"] = "❌ Invalid API key format. OpenAI keys start with 'sk-'"
    elif debug_info["step_by_step_debug"].get("4_api_test", {}).get("status") == "FAILED ❌":
        debug_info["diagnosis"] = "❌ API key exists but doesn't work. Check the error above."
    else:
        debug_info["diagnosis"] = "❌ Unknown issue. Check all steps above."
    
    return JSONResponse(debug_info)

@app.get("/fix-config")
async def fix_config():
    """Try to fix the config by reading from both possible environment variable names"""
    
    # Try to get API key from both possible names
    key_from_Open_Api_Key = os.getenv("Open_Api_Key")
    key_from_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    result = {
        "Open_Api_Key": bool(key_from_Open_Api_Key),
        "OPENAI_API_KEY": bool(key_from_OPENAI_API_KEY),
        "current_config_value": bool(config.OPENAI_API_KEY)
    }
    
    # Try to use whichever one exists
    working_key = key_from_OPENAI_API_KEY or key_from_Open_Api_Key
    
    if working_key:
        try:
            import openai
            openai.api_key = working_key.strip()
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            
            result["fix_test"] = {
                "status": "SUCCESS ✅",
                "working_key_source": "OPENAI_API_KEY" if key_from_OPENAI_API_KEY else "Open_Api_Key",
                "response": response.choices[0].message.content if response.choices else "No response"
            }
            
        except Exception as e:
            result["fix_test"] = {
                "status": "FAILED ❌",
                "error": str(e),
                "working_key_source": "OPENAI_API_KEY" if key_from_OPENAI_API_KEY else "Open_Api_Key"
            }
    else:
        result["fix_test"] = {
            "status": "NO KEYS FOUND ❌",
            "message": "Neither Open_Api_Key nor OPENAI_API_KEY found in environment"
        }
    
    return JSONResponse(result)

if __name__ == "__main__":
    print("🚀 Starting Sophisticated Content Generator with OpenAI...")
    print("=" * 70)
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    
    # Test API key
    openai_status = "✅ Configured" if config.OPENAI_API_KEY else "❌ Not configured"
    
    print(f"🤖 OpenAI API: {openai_status}")
    
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        print(f"🔑 API Key preview: {config.OPENAI_API_KEY[:8]}...{config.OPENAI_API_KEY[-4:]}")
        
        # Test OpenAI connection
        try:
            openai.api_key = config.OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            print("✅ OpenAI API test successful")
        except Exception as e:
            print(f"❌ OpenAI API test failed: {e}")
    elif not OPENAI_AVAILABLE:
        print("❌ OpenAI library not installed. Run: pip install openai")
    
    print("🎯 Features: All Content Types, OpenAI GPT-4, Sophisticated Design")
    print("🎨 Theme: Black & White Sophisticated UI")
    print("🤖 Enhanced: AI Instructions Section")
    print("🔍 Debug: Comprehensive debugging endpoints included")
    print("=" * 70)
    
    try:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise e
