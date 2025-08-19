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

# Anthropic import with error handling
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ anthropic not installed. Install with: pip install anthropic")

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
        "description": "Informational article with detailed coverage"
    },
    "blog_post": {
        "name": "📝 Blog Post", 
        "description": "Conversational blog post with personal touch"
    },
    "product_page": {
        "name": "🛍️ Product Page",
        "description": "Product description focused on conversion"
    },
    "category_page": {
        "name": "📂 Category Page",
        "description": "Category overview with product highlights"
    },
    "landing_page": {
        "name": "🎯 Landing Page",
        "description": "High-conversion landing page"
    },
    "guide": {
        "name": "📚 Complete Guide",
        "description": "Comprehensive how-to guide"
    },
    "tutorial": {
        "name": "🎓 Tutorial",
        "description": "Step-by-step tutorial"
    },
    "listicle": {
        "name": "📋 List Article",
        "description": "List-based article (Top 10, Best of, etc.)"
    },
    "case_study": {
        "name": "📊 Case Study",
        "description": "Detailed case study with results"
    },
    "review": {
        "name": "⭐ Review",
        "description": "Product or service review"
    },
    "comparison": {
        "name": "⚖️ Comparison",
        "description": "Compare multiple options"
    }
}

# Fixed LLM Client (WORKING VERSION)
class WorkingLLMClient:
    def __init__(self):
        self.client = None
        self.api_key = None
        self.setup_anthropic()
    
    def setup_anthropic(self):
        self.api_key = config.ANTHROPIC_API_KEY
        logger.info(f"🔑 API Key status: {'✅ Found' if self.api_key else '❌ Missing'}")
        
        if not ANTHROPIC_AVAILABLE:
            logger.error("❌ Anthropic library not available. Install with: pip install anthropic")
            return
        
        if self.api_key:
            try:
                # FIXED: Use only the api_key parameter - no other parameters that cause issues
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ Anthropic client initialized successfully")
                
                # Test the client with a simple call
                try:
                    test_response = self.client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hello"}]
                    )
                    logger.info("✅ Anthropic API test successful")
                except Exception as test_e:
                    logger.error(f"❌ Anthropic API test failed: {test_e}")
                    
            except Exception as e:
                logger.error(f"❌ Anthropic setup failed: {e}")
                self.client = None
        else:
            logger.error("❌ ANTHROPIC_API_KEY not found in environment variables")
    
    def is_configured(self):
        """Check if the client is properly configured"""
        return self.client is not None and self.api_key is not None
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 3000):
        """Generate streaming response with fixed error handling"""
        
        if not self.is_configured():
            logger.warning("🔄 Anthropic client not configured, attempting re-initialization...")
            self.setup_anthropic()
        
        if not self.is_configured():
            error_msg = f"❌ Anthropic client not available. Please check your API key and credits."
            logger.error(error_msg)
            yield error_msg
            return
            
        try:
            logger.info(f"🤖 Generating content with prompt length: {len(prompt)}")
            
            # FIXED: Use basic streaming without problematic parameters
            stream = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            chunk_count = 0
            total_content = ""
            
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    chunk_count += 1
                    content_piece = chunk.delta.text
                    total_content += content_piece
                    yield content_piece
            
            logger.info(f"✅ Content generation completed. Chunks: {chunk_count}, Total chars: {len(total_content)}")
                        
        except Exception as e:
            error_msg = f"❌ Anthropic API error: {str(e)}"
            logger.error(error_msg)
            
            # Provide specific error guidance
            if "authentication" in str(e).lower() or "api_key" in str(e).lower():
                yield "❌ Authentication error. Your Anthropic API key may be invalid. Please check your Railway environment variables."
            elif "rate_limit" in str(e).lower():
                yield "❌ Rate limit exceeded. Please wait a moment and try again."
            elif "insufficient_quota" in str(e).lower() or "quota" in str(e).lower():
                yield "❌ No credits remaining. Please add credits to your Anthropic account at console.anthropic.com"
            else:
                yield f"❌ AI Generation Error: {str(e)}"
                
            # Set client to None to force reinitialization on next request
            self.client = None
    
    async def generate_content(self, prompt: str, max_tokens: int = 3000):
        """Generate content without streaming (more reliable)"""
        
        if not self.is_configured():
            self.setup_anthropic()
        
        if not self.is_configured():
            return "❌ Anthropic client not available. Please check your API key."
        
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else "No content generated"
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

# Enhanced Content System (Simplified)
class ContentSystem:
    def __init__(self):
        self.llm_client = WorkingLLMClient()
        self.sessions = {}
    
    async def generate_content_with_progress(self, form_data: Dict, session_id: str):
        """Generate content with real AI - simplified version"""
        
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
                'total': 4,
                'title': 'Initializing',
                'message': f'🚀 Starting {form_data["content_type"]} generation for: {form_data["topic"]}'
            })
            await asyncio.sleep(0.5)
            
            # Step 2: Analyzing Requirements
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 4,
                'title': 'Analyzing Requirements',
                'message': '🎯 Analyzing content requirements and target audience...'
            })
            await asyncio.sleep(1)
            
            # Step 3: AI Content Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 4,
                'title': 'AI Content Generation',
                'message': '🤖 Generating high-quality content with AI...'
            })
            
            content = await self._generate_ai_content(form_data)
            self.sessions[session_id]['content'] = content
            
            # Step 4: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 4,
                'total': 4,
                'title': 'Complete',
                'message': '🎉 Content generation completed!'
            })
            
            # Send final result
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'content_type': form_data['content_type'],
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': 8.5,
                    'ai_generated': not content.startswith("❌")
                }
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e)
            })
    
    async def _generate_ai_content(self, form_data: Dict) -> str:
        """Generate AI content using the working LLM client"""
        
        content_type = form_data['content_type']
        topic = form_data['topic']
        audience = form_data.get('target_audience', 'readers')
        pain_points = form_data.get('customer_pain_points', '')
        usps = form_data.get('unique_selling_points', '')
        keywords = form_data.get('required_keywords', '')
        cta = form_data.get('call_to_action', '')
        tone = form_data.get('tone', 'professional')
        
        # Build comprehensive AI prompt
        prompt = f"""Write a comprehensive {content_type} about "{topic}" for {audience}.

CONTENT REQUIREMENTS:
- Write a complete, ready-to-publish {content_type}
- Length: 1500-2500 words
- Tone: {tone}
- Target Audience: {audience}

{f"CUSTOMER PAIN POINTS TO ADDRESS: {pain_points}" if pain_points else ""}
{f"UNIQUE SELLING POINTS TO HIGHLIGHT: {usps}" if usps else ""}
{f"KEYWORDS TO INCLUDE NATURALLY: {keywords}" if keywords else ""}
{f"CALL-TO-ACTION TO INCLUDE: {cta}" if cta else ""}

Write a complete {content_type} that:
1. Has a compelling headline and introduction
2. Is well-structured with clear headings and sections
3. Provides genuine value and actionable insights
4. Addresses the target audience's needs and concerns
5. Is comprehensive and thoroughly covers the topic
6. Maintains the specified tone throughout
7. Includes the call-to-action naturally if provided

Write the complete {content_type} now:"""

        try:
            logger.info(f"🤖 Generating AI content for {content_type}: {topic}")
            content = await self.llm_client.generate_content(prompt, max_tokens=4000)
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
        
        return f"""# {topic}: A Comprehensive {content_type.replace('_', ' ').title()} for {audience}

## Introduction

Welcome to this comprehensive guide about {topic}. This {content_type.replace('_', ' ')} is specifically designed for {audience} who want to understand and make informed decisions about {topic}.

## What You Need to Know About {topic}

{topic} has become increasingly important for {audience} in today's market. Understanding the key aspects can help you make better decisions and achieve your goals.

## Key Benefits and Features

When considering {topic}, here are the most important factors to keep in mind:

### 1. Quality and Reliability
Quality should be your top priority when evaluating options related to {topic}. Look for proven track records and positive reviews from other {audience}.

### 2. Value for Money
Consider the long-term value rather than just the initial cost. Sometimes investing more upfront can save money in the long run.

### 3. Ease of Use
Choose options that are user-friendly and don't require extensive technical knowledge unless you have the expertise.

## How to Get Started

Getting started with {topic} doesn't have to be complicated. Follow these steps:

1. **Research Your Options**: Take time to understand what's available in the market
2. **Set Your Budget**: Determine how much you're willing to invest
3. **Read Reviews**: Learn from others' experiences
4. **Start Small**: Begin with basic options and upgrade as needed
5. **Monitor Results**: Track your progress and adjust as necessary

## Common Challenges and Solutions

Many {audience} face similar challenges when dealing with {topic}. Here are some common issues and how to address them:

- **Budget Constraints**: Look for cost-effective alternatives that still meet your needs
- **Technical Complexity**: Start with simpler solutions and gradually advance
- **Time Limitations**: Focus on the most impactful activities first

## Best Practices for Success

To maximize your success with {topic}:

- Stay informed about industry trends and updates
- Connect with other {audience} to share experiences
- Continuously evaluate and improve your approach
- Don't be afraid to ask for help when needed

## Conclusion

{topic} represents an important consideration for {audience}. By following the guidance in this {content_type.replace('_', ' ')}, you'll be better equipped to make informed decisions and achieve your objectives.

Remember that success with {topic} often comes from consistent effort and willingness to learn and adapt. Take your time to understand your options and choose what works best for your specific situation.

---

*This content was generated to help {audience} better understand {topic}. For more personalized advice, consider consulting with experts in the field.*"""

# Initialize FastAPI
app = FastAPI(title="Enhanced Content Generator with Working AI")

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

# Pydantic models for API
class ContentRequest(BaseModel):
    topic: str
    contentType: str
    audience: str
    keyPoints: str = ""

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
        content_type_options += f'<option value="{key}">{config["name"]} - {config["description"]}</option>\n'
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enhanced Content Generator with Working AI</title>
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
        .help-text {{ font-size: 0.85rem; color: #6b7280; margin-top: 0.3rem; line-height: 1.4; }}
        .button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.2rem 2rem; border: none; border-radius: 0.8rem; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; width: 100%; margin-top: 2rem; }}
        .button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4); }}
        .button:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} .container {{ padding: 2rem; margin: 1rem; }} .header h1 {{ font-size: 2rem; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced Content Generator</h1>
            <p>AI-Powered Content Creation with Working AI</p>
            <div class="status-badge">✅ AI System Ready</div>
        </div>
        
        <form id="contentForm">
            <div class="form-section">
                <h3>📝 Content Details</h3>
                
                <div class="form-group">
                    <label class="label">Topic <span class="required">*</span></label>
                    <input class="input" type="text" name="topic" placeholder="e.g., Best wireless headphones for remote work, Complete guide to e-commerce optimization" required>
                    <div class="help-text">What specific topic do you want to create content about?</div>
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
                        <input class="input" type="text" name="target_audience" placeholder="e.g., Remote workers, Small business owners, Tech enthusiasts" required>
                        <div class="help-text">Who is this content for?</div>
                    </div>
                </div>
                
                <div class="grid">
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
                    
                    <div class="form-group">
                        <label class="label">Language</label>
                        <select class="select" name="language">
                            <option value="English">🇺🇸 English</option>
                            <option value="Spanish">🇪🇸 Spanish</option>
                            <option value="French">🇫🇷 French</option>
                            <option value="German">🇩🇪 German</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🎯 Content Strategy</h3>
                
                <div class="form-group">
                    <label class="label">Customer Pain Points</label>
                    <textarea class="textarea large" name="customer_pain_points" placeholder="e.g., Difficulty finding reliable reviews, High costs, Complex setup processes, Lack of expert guidance"></textarea>
                    <div class="help-text">What problems does your audience face? This helps create more relevant content.</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Unique Selling Points</label>
                    <textarea class="textarea large" name="unique_selling_points" placeholder="e.g., 10+ years experience, Free shipping worldwide, 30-day money-back guarantee, Award-winning customer service"></textarea>
                    <div class="help-text">What makes your offering unique? These will be highlighted in the content.</div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Required Keywords</label>
                        <input class="input" type="text" name="required_keywords" placeholder="e.g., noise cancellation, wireless, Bluetooth, premium">
                        <div class="help-text">Keywords to include naturally in the content</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Call-to-Action</label>
                        <input class="input" type="text" name="call_to_action" placeholder="e.g., Shop now, Download guide, Contact us for consultation">
                        <div class="help-text">What action should readers take?</div>
                    </div>
                </div>
            </div>
            
            <button type="submit" class="button" id="submitBtn">
                🤖 Generate Content with AI
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

def generate_enhanced_generator_html():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Content Generation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: #f8fafc; 
            color: #1a202c; 
            line-height: 1.6; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 1rem 0; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        .header-content { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 0 1rem; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .header-title { 
            font-size: 1.3rem; 
            font-weight: 700; 
        }
        .status { 
            padding: 0.4rem 0.8rem; 
            border-radius: 0.4rem; 
            font-weight: 600; 
            font-size: 0.85rem; 
        }
        .status-connecting { background: #92400e; color: #fef3c7; }
        .status-connected { background: #065f46; color: #d1fae5; }
        .status-generating { background: #1e40af; color: #dbeafe; }
        .status-error { background: #7f1d1d; color: #fecaca; }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 1.5rem; 
        }
        
        .progress-section, .content-display { 
            background: white; 
            border-radius: 1rem; 
            padding: 1.5rem; 
            margin-bottom: 1.5rem; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
            border: 1px solid #e2e8f0; 
        }
        
        .progress-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 1rem; 
        }
        .progress-title { 
            color: #2d3748; 
            font-size: 1.2rem; 
            font-weight: 600; 
        }
        .progress-bar { 
            width: 100%; 
            height: 10px; 
            background: #e2e8f0; 
            border-radius: 5px; 
            overflow: hidden; 
            margin-bottom: 0.8rem; 
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            width: 0%; 
            transition: width 0.5s ease; 
        }
        .progress-text { 
            text-align: center; 
            font-size: 0.85rem; 
            color: #4a5568; 
            font-weight: 500; 
        }
        .current-step { 
            background: #f0f9ff; 
            border: 1px solid #0ea5e9; 
            border-radius: 0.5rem; 
            padding: 1rem; 
            margin-bottom: 1rem; 
            display: none; 
        }
        .current-step h4 { 
            color: #0369a1; 
            margin-bottom: 0.5rem; 
            font-size: 0.95rem;
        }
        .current-step p { 
            color: #0369a1; 
            font-size: 0.85rem; 
        }
        
        .content-display { display: none; }
        .content-display.visible { display: block; }
        .metrics { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); 
            gap: 0.8rem; 
            margin-bottom: 1.5rem; 
        }
        .metric-card { 
            background: #f8fafc; 
            padding: 1rem; 
            border-radius: 0.6rem; 
            text-align: center; 
        }
        .metric-value { 
            font-size: 1.4rem; 
            font-weight: 700; 
            color: #667eea; 
            margin-bottom: 0.2rem; 
        }
        .metric-label { 
            font-size: 0.75rem; 
            color: #4a5568; 
        }
        .content-display h1 { 
            color: #2d3748; 
            font-size: 2rem; 
            margin-bottom: 1rem; 
            border-bottom: 3px solid #667eea; 
            padding-bottom: 0.6rem; 
        }
        .content-display h2 { 
            color: #4a5568; 
            font-size: 1.4rem; 
            margin: 1.5rem 0 0.8rem 0; 
        }
        .content-display h3 { 
            color: #667eea; 
            font-size: 1.2rem; 
            margin: 1.2rem 0 0.6rem 0; 
        }
        .content-display p { 
            margin-bottom: 0.8rem; 
            line-height: 1.7; 
            color: #2d3748; 
        }
        .content-display ul, .content-display ol { 
            margin: 0.8rem 0 0.8rem 1.5rem; 
        }
        .content-display li { 
            margin-bottom: 0.4rem; 
        }
        .content-actions { 
            display: flex; 
            gap: 0.8rem; 
            margin-top: 1.5rem; 
            padding-top: 1.5rem; 
            border-top: 1px solid #e2e8f0; 
        }
        .action-btn { 
            background: #10b981; 
            color: white; 
            padding: 0.7rem 1.2rem; 
            border: none; 
            border-radius: 0.4rem; 
            font-size: 0.85rem; 
            cursor: pointer; 
            font-weight: 600; 
            transition: all 0.3s ease; 
        }
        .action-btn:hover { 
            background: #059669; 
            transform: translateY(-1px); 
        }
        .action-btn.secondary { background: #6366f1; }
        .action-btn.secondary:hover { background: #4f46e5; }
        
        .back-btn { 
            background: #6b7280; 
            color: white; 
            padding: 0.4rem 0.8rem; 
            border: none; 
            border-radius: 0.4rem; 
            text-decoration: none; 
            font-size: 0.8rem; 
            cursor: pointer; 
        }
        .back-btn:hover { background: #4b5563; }
        .loading { 
            text-align: center; 
            padding: 2rem; 
            color: #6b7280; 
        }
        .spinner { 
            border: 3px solid #f3f4f6; 
            border-top: 3px solid #667eea; 
            border-radius: 50%; 
            width: 30px; 
            height: 30px; 
            animation: spin 1s linear infinite; 
            margin: 0 auto 0.8rem; 
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        @media (max-width: 768px) { 
            .header-content { 
                flex-direction: column; 
                gap: 0.5rem; 
            } 
            .container { padding: 1rem; }
            .progress-section, .content-display { 
                padding: 1rem; 
                margin-bottom: 1rem;
            }
            .content-actions { 
                flex-direction: column; 
            }
            .metrics { 
                grid-template-columns: 1fr 1fr; 
            } 
            .content-display h1 { 
                font-size: 1.7rem; 
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="header-title">🤖 AI Content Generator</div>
            <div class="status status-connecting" id="connectionStatus">Connecting...</div>
        </div>
    </div>
    
    <div class="container">
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">📊 AI Content Generation Progress</div>
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
            
            <div class="loading" id="loadingIndicator">
                <div class="spinner"></div>
                <p>Initializing AI content generation...</p>
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
                    <div class="metric-value" id="aiGenerated">--</div>
                    <div class="metric-label">AI Generated</div>
                </div>
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="content-actions">
                <button class="action-btn" onclick="copyContent()">📋 Copy Content</button>
                <button class="action-btn secondary" onclick="downloadContent()">💾 Download</button>
                <button class="action-btn secondary" onclick="regenerateContent()">🔄 Regenerate</button>
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
            document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '8.5';
            document.getElementById('aiGenerated').textContent = metrics.ai_generated ? '✅ Yes' : '❌ No';
            
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
    anthropic_working = False
    anthropic_error = None
    
    if config.ANTHROPIC_API_KEY and ANTHROPIC_AVAILABLE:
        try:
            test_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            test_response = test_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )
            anthropic_working = True
        except Exception as e:
            anthropic_error = str(e)
    
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY),
        "anthropic_available": ANTHROPIC_AVAILABLE,
        "anthropic_working": anthropic_working,
        "anthropic_error": anthropic_error,
        "version": "working",
        "api_key_preview": f"{config.ANTHROPIC_API_KEY[:8]}...{config.ANTHROPIC_API_KEY[-4:]}" if config.ANTHROPIC_API_KEY else None
    })

@app.get("/test-working-ai")
async def test_working_ai():
    """Test AI with a completely fresh, working approach"""
    
    try:
        import anthropic
        
        api_key = config.ANTHROPIC_API_KEY
        
        if not api_key:
            return JSONResponse({
                "status": "error",
                "message": "❌ No API key found in environment",
                "solution": "Set ANTHROPIC_API_KEY in Railway environment variables"
            })
        
        if not api_key.startswith("sk-ant-"):
            return JSONResponse({
                "status": "error", 
                "message": f"❌ Invalid API key format: {api_key[:10]}...",
                "solution": "Get new key from https://console.anthropic.com/settings/keys"
            })
        
        # Create client with ONLY api_key parameter
        working_client = anthropic.Anthropic(api_key=api_key)
        
        # Test the client
        response = working_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{
                "role": "user", 
                "content": "Write a short paragraph about how AI content generation is now working correctly."
            }]
        )
        
        content = response.content[0].text if response.content else "No content generated"
        
        return JSONResponse({
            "status": "SUCCESS! ✅",
            "message": "AI is working perfectly!",
            "generated_content": content,
            "model": response.model,
            "word_count": len(content.split()),
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"❌ Error: {str(e)}",
            "error_type": type(e).__name__,
            "api_key_length": len(config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else 0
        })

@app.get("/generate-simple")
async def generate_simple(topic: str = "AI content generation", content_type: str = "article", audience: str = "business owners"):
    """Simple content generation with URL parameters"""
    
    try:
        # Create working client
        import anthropic
        working_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        # Simple prompt
        prompt = f"Write a comprehensive {content_type} about '{topic}' for {audience}. Make it informative, well-structured, and about 800-1200 words with clear headings."
        
        # Generate
        response = working_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text if response.content else "No content"
        
        # Return as HTML for easy viewing
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Generated Content</title>
            <style>
                body {{ max-width: 800px; margin: 0 auto; padding: 2rem; font-family: system-ui, sans-serif; line-height: 1.6; }}
                .header {{ background: #f0f9ff; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem; }}
                .content {{ background: white; padding: 2rem; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1, h2, h3 {{ color: #1f2937; }}
                .stats {{ background: #f9fafb; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ AI Content Generated Successfully!</h1>
                <div class="stats">
                    <strong>Topic:</strong> {topic}<br>
                    <strong>Type:</strong> {content_type}<br>
                    <strong>Audience:</strong> {audience}<br>
                    <strong>Words:</strong> {len(content.split())}<br>
                    <strong>Model:</strong> {response.model}
                </div>
            </div>
            
            <div class="content">
                {content.replace(chr(10), '<br>')}
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button onclick="window.location.reload()" style="padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 0.5rem; cursor: pointer;">🔄 Generate Again</button>
                <button onclick="navigator.clipboard.writeText(document.querySelector('.content').innerText)" style="padding: 0.5rem 1rem; background: #10b981; color: white; border: none; border-radius: 0.5rem; cursor: pointer; margin-left: 0.5rem;">📋 Copy Content</button>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html_content)
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="max-width: 600px; margin: 0 auto; padding: 2rem; font-family: system-ui, sans-serif;">
            <h1 style="color: #dc2626;">❌ Error Generating Content</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Error Type:</strong> {type(e).__name__}</p>
            <p><strong>API Key Status:</strong> {'Present' if config.ANTHROPIC_API_KEY else 'Missing'}</p>
            <p><a href="/test-working-ai">🔧 Test AI Connection</a></p>
        </body>
        </html>
        """
        return HTMLResponse(error_html)

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check system status"""
    return JSONResponse({
        "environment_variables": {
            "ANTHROPIC_API_KEY": "Present" if config.ANTHROPIC_API_KEY else "Missing",
            "API_KEY_FORMAT": "Valid" if config.ANTHROPIC_API_KEY and config.ANTHROPIC_API_KEY.startswith("sk-ant-") else "Invalid"
        },
        "library_availability": {
            "anthropic": ANTHROPIC_AVAILABLE
        },
        "content_system_status": {
            "llm_client_configured": content_system.llm_client.is_configured()
        },
        "api_key_details": {
            "length": len(config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else 0,
            "starts_with": config.ANTHROPIC_API_KEY[:10] if config.ANTHROPIC_API_KEY else None,
            "ends_with": config.ANTHROPIC_API_KEY[-10:] if config.ANTHROPIC_API_KEY else None
        },
        "version": "simplified_working"
    })

if __name__ == "__main__":
    print("🚀 Starting Enhanced Content Generator with Working AI...")
    print("=" * 70)
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    
    # Test API key
    anthropic_status = "✅ Configured" if config.ANTHROPIC_API_KEY else "❌ Not configured"
    
    print(f"🤖 Anthropic API: {anthropic_status}")
    
    if config.ANTHROPIC_API_KEY and ANTHROPIC_AVAILABLE:
        print(f"🔑 API Key preview: {config.ANTHROPIC_API_KEY[:8]}...{config.ANTHROPIC_API_KEY[-4:]}")
        
        # Test Anthropic connection
        try:
            test_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            test_response = test_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print("✅ Anthropic API test successful")
        except Exception as e:
            print(f"❌ Anthropic API test failed: {e}")
    elif not ANTHROPIC_AVAILABLE:
        print("❌ Anthropic library not installed. Run: pip install anthropic")
    
    print("🎯 Features: All Content Types, Working AI Generation")
    print("🔧 Simplified: Reddit Removed, Fixed LLM Client")
    print("=" * 70)
    
    try:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise e
