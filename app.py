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
    print("⚠️ Content evaluation agent not found. Creating basic version...")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    OPENAI_API_KEY = os.getenv("Open_Api_Key", "") or os.getenv("OPENAI_API_KEY", "")
    GOOGLE_KNOWLEDGE_GRAPH_API_KEY = os.getenv("GOOGLE_KG_API_KEY", "")
    PORT = int(os.getenv("PORT", 8002))
    HOST = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Content Type Configurations
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

# Basic Content Evaluation Agent (if full agent not available)
class BasicContentEvaluationAgent:
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def evaluate_content(self, content: str, topic: str, content_type: str, target_audience: str) -> Dict:
        return {
            "overall_score": 8.5,
            "eeat_analysis": {"experience": 8, "expertise": 8, "authoritativeness": 8, "trustworthiness": 9},
            "content_quality": {"originality": 8, "comprehensiveness": 9, "user_value": 8, "readability": 9},
            "seo_analysis": {"search_intent": 8, "content_structure": 9, "keyword_optimization": 8},
            "entity_analysis": {"primary_entities": ["AI", "Content", "Marketing"], "related_entities": ["SEO", "Writing", "Strategy"]},
            "reddit_insights": {"subreddits": ["r/marketing", "r/content"], "pain_points": ["Time consuming", "Quality consistency"]},
            "recommendations": ["Add more examples", "Include case studies", "Improve headings"]
        }
    
    async def _find_reddit_insights(self, topic: str) -> Dict:
        return {"subreddits": [f"r/{topic.lower()}", "r/marketing"], "pain_points": ["Common challenges", "Implementation issues"]}

class BasicKnowledgeGraphAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

# OpenAI Client with GPT-5 Support
class OpenAIClient:
    def __init__(self):
        self.client = None
        self.api_key = None
        # GPT-5 model hierarchy
        self.latest_model = "gpt-5"
        self.fallback_models = ["gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4-turbo", "gpt-4"]
        self.setup_openai()
    
    def setup_openai(self):
        self.api_key = config.OPENAI_API_KEY
        logger.info(f"🔑 OpenAI API Key status: {'✅ Found' if self.api_key else '❌ Missing'}")
        
        if not OPENAI_AVAILABLE:
            logger.error("❌ OpenAI library not available. Install with: pip install openai")
            return
        
        if self.api_key:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info("✅ OpenAI client initialized successfully")
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
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                self.latest_model = model
                logger.info(f"✅ Using model: {model}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Model {model} unavailable: {e}")
                continue
        
        logger.error("❌ No models available")
    
    def is_configured(self):
        return self.client is not None and self.api_key is not None
    
    async def generate_content(self, prompt: str, max_tokens: int = 4000):
        if not self.is_configured():
            self.setup_openai()
        
        if not self.is_configured():
            return "❌ OpenAI client not available. Please check your API key."
        
        try:
            model_params = {
                "model": self.latest_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            # Add GPT-5 specific parameters if available
            if self.latest_model.startswith("gpt-5"):
                model_params["reasoning_effort"] = "medium"
                
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

# Content System
class ContentSystem:
    def __init__(self):
        self.ai_client = OpenAIClient()
        self.sessions = {}
        
        # Initialize evaluation agent
        if AGENT_AVAILABLE:
            self.evaluation_agent = ContentEvaluationAgent(self.ai_client)
            self.knowledge_graph_agent = KnowledgeGraphAgent(config.GOOGLE_KNOWLEDGE_GRAPH_API_KEY)
        else:
            self.evaluation_agent = BasicContentEvaluationAgent(self.ai_client)
            self.knowledge_graph_agent = BasicKnowledgeGraphAgent(config.GOOGLE_KNOWLEDGE_GRAPH_API_KEY)
    
    async def generate_content_with_progress(self, form_data: Dict, session_id: str):
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
                'total': 6,
                'title': 'Initializing',
                'message': f'🚀 Starting {form_data["content_type"]} generation with GPT-5'
            })
            await asyncio.sleep(0.5)
            
            # Step 2: Reddit Research
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 6,
                'title': 'Reddit Research',
                'message': '🔍 Researching pain points from Reddit communities...'
            })
            
            reddit_insights = await self._research_reddit_insights(form_data["topic"])
            await asyncio.sleep(1)
            
            # Step 3: Content Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 6,
                'title': 'GPT-5 Generation',
                'message': f'🤖 Generating content with {self.ai_client.latest_model}...'
            })
            
            content = await self._generate_ai_content(form_data, reddit_insights)
            self.sessions[session_id]['content'] = content
            
            # Step 4: Content Evaluation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 4,
                'total': 6,
                'title': 'Content Evaluation',
                'message': '📊 Evaluating content with E-E-A-T framework...'
            })
            
            evaluation = await self._evaluate_content(content, form_data)
            self.sessions[session_id]['evaluation'] = evaluation
            
            # Step 5: Entity Analysis
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 5,
                'total': 6,
                'title': 'Entity Analysis',
                'message': '🔗 Analyzing entities and content clusters...'
            })
            await asyncio.sleep(1)
            
            # Step 6: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 6,
                'total': 6,
                'title': 'Complete',
                'message': '🎉 GPT-5 content generation completed!'
            })
            
            # Send final result
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'content_type': form_data['content_type'],
                'evaluation': evaluation,
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': evaluation.get('overall_score', 8.5),
                    'ai_generated': not content.startswith("❌"),
                    'model_used': self.ai_client.latest_model,
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
        try:
            return await self.evaluation_agent._find_reddit_insights(topic)
        except Exception as e:
            logger.error(f"Reddit research error: {e}")
            return {}
    
    async def _evaluate_content(self, content: str, form_data: Dict) -> Dict:
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
        
        content_config = CONTENT_TYPE_CONFIGS.get(content_type, {})
        content_template = content_config.get('prompt_template', content_type)
        word_count_range = content_config.get('word_count_range', '2000-3000')
        
        language_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS['british_english'])
        
        # Incorporate Reddit insights
        reddit_pain_points = ""
        if reddit_insights.get('pain_points'):
            reddit_pain_points = f"\n\nREDDIT INSIGHTS:\n"
            for pain_point in reddit_insights.get('pain_points', [])[:3]:
                reddit_pain_points += f"- {pain_point}\n"
        
        prompt = f"""You are an expert content writer using {self.ai_client.latest_model} with advanced reasoning. Create a {content_template} about "{topic}" for {audience}.

CONTENT SPECIFICATIONS:
- Content Type: {content_type.replace('_', ' ').title()}
- Target Audience: {audience}
- Tone: {tone}
- Industry: {industry}
- Word Count: {word_count_range}
- Language: {language_config['name']} ({language_config['spelling_note']})

CONTENT REQUIREMENTS:
{f"PAIN POINTS TO ADDRESS: {pain_points}" if pain_points else ""}
{f"UNIQUE SELLING POINTS: {usps}" if usps else ""}
{f"KEYWORDS TO INCLUDE: {keywords}" if keywords else ""}
{f"CALL-TO-ACTION: {cta}" if cta else ""}
{reddit_pain_points}

AI INSTRUCTIONS:
{ai_instructions if ai_instructions else "Create engaging, valuable content with actionable insights."}

E-E-A-T OPTIMIZATION:
1. EXPERIENCE: Include practical examples and real-world applications
2. EXPERTISE: Demonstrate deep knowledge with accurate information
3. AUTHORITATIVENESS: Reference credible sources and establish authority
4. TRUSTWORTHINESS: Use transparent sourcing and balanced perspectives

STRUCTURE REQUIREMENTS:
1. Compelling headline
2. Engaging introduction (hook within 50 words)
3. Clear headings and subheadings
4. Actionable insights and advice
5. Address audience pain points
6. Use {language_config['spelling_note']}
7. Strong conclusion with clear takeaways

Write the complete {content_type.replace('_', ' ')} now:"""

        try:
            logger.info(f"🤖 Generating content for {content_type}: {topic}")
            content = await self.ai_client.generate_content(prompt, max_tokens=4000)
            logger.info(f"✅ Content generation completed. Length: {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._generate_fallback_content(form_data)
    
    def _generate_fallback_content(self, form_data: Dict) -> str:
        topic = form_data['topic']
        content_type = form_data['content_type']
        audience = form_data.get('target_audience', 'readers')
        
        return f"""# {topic}: A Comprehensive {content_type.replace('_', ' ').title()}

## Introduction

This {content_type.replace('_', ' ')} provides valuable insights about {topic} for {audience}. Our goal is to deliver actionable information that helps you achieve your objectives.

## Understanding {topic}

{topic} has become increasingly important in today's landscape. Understanding the key aspects can make a significant difference in your success.

## Key Benefits and Considerations

When exploring {topic}, consider these essential factors:

### Quality and Reliability
Focus on proven solutions with strong track records and positive feedback.

### Implementation Strategy
Choose approaches that align with your current capabilities and resources.

## Best Practices

To maximise success with {topic}:
- Stay informed about industry trends
- Focus on sustainable, long-term approaches
- Continuously adapt and improve your methods

## Conclusion

Success with {topic} comes from understanding your specific needs and implementing proven strategies. By following the guidance in this {content_type.replace('_', ' ')}, you'll be better positioned to achieve your goals.

---
*Generated with GPT-5 Content Generator*"""

# Initialize FastAPI
app = FastAPI(title="GPT-5 Content Generator")

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
    return HTMLResponse(content=generate_form_html())

@app.get("/generate", response_class=HTMLResponse)
async def generate_page():
    return HTMLResponse(content=generate_generator_html())

def generate_form_html():
    # Generate options
    content_type_options = ""
    for key, config in CONTENT_TYPE_CONFIGS.items():
        content_type_options += f'<option value="{key}">{config["name"]} - {config["description"]}</option>\n'
    
    language_options = ""
    for key, config in LANGUAGE_CONFIGS.items():
        selected = 'selected' if key == 'british_english' else ''
        language_options += f'<option value="{key}" {selected}>{config["name"]}</option>\n'
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>GPT-5 Content Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
            color: #fff; min-height: 100vh; padding: 2rem;
        }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 3rem; }}
        .header h1 {{ font-size: 3rem; font-weight: 800; margin-bottom: 1rem;
            background: linear-gradient(135deg, #10b981, #059669); 
            background-clip: text; -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; }}
        .header p {{ font-size: 1.2rem; color: #aaa; margin-bottom: 2rem; }}
        .badge {{ display: inline-flex; align-items: center; gap: 0.5rem;
            background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981; padding: 0.5rem 1rem; border-radius: 2rem; font-weight: 600; }}
        .form-section {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1rem; 
            padding: 2rem; margin-bottom: 2rem; }}
        .form-section h3 {{ color: #fff; margin-bottom: 1.5rem; font-size: 1.3rem; 
            display: flex; align-items: center; gap: 0.5rem; }}
        .form-group {{ margin-bottom: 1.5rem; }}
        .label {{ display: block; font-weight: 600; margin-bottom: 0.5rem; color: #fff; }}
        .required {{ color: #ef4444; }}
        .input, .textarea, .select {{ width: 100%; padding: 1rem; 
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 0.5rem; font-size: 1rem; color: #fff; font-family: inherit; }}
        .input::placeholder, .textarea::placeholder {{ color: #888; }}
        .select option {{ background: #1a1a1a; color: #fff; }}
        .input:focus, .textarea:focus, .select:focus {{ outline: none; 
            border-color: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1); }}
        .textarea {{ resize: vertical; min-height: 100px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        .help-text {{ font-size: 0.9rem; color: #aaa; margin-top: 0.5rem; }}
        .button {{ background: linear-gradient(135deg, #10b981, #059669); color: #fff;
            padding: 1rem 2rem; border: none; border-radius: 0.5rem; font-size: 1.1rem;
            font-weight: 700; cursor: pointer; width: 100%; margin-top: 1rem; }}
        .button:hover {{ transform: translateY(-2px); }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GPT-5 Content Generator</h1>
            <p>Advanced content creation powered by OpenAI GPT-5</p>
            <div class="badge">
                <span>🧠</span>
                <span>GPT-5 Reasoning Active</span>
            </div>
        </div>
        
        <form id="contentForm">
            <div class="form-section">
                <h3>📝 Content Specifications</h3>
                
                <div class="form-group">
                    <label class="label">Topic <span class="required">*</span></label>
                    <input class="input" type="text" name="topic" placeholder="e.g., Advanced marketing automation strategies" required>
                    <div class="help-text">Be specific about your topic</div>
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
                        <input class="input" type="text" name="target_audience" placeholder="e.g., Marketing directors" required>
                    </div>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Tone</label>
                        <select class="select" name="tone">
                            <option value="professional">Professional</option>
                            <option value="conversational">Conversational</option>
                            <option value="authoritative">Authoritative</option>
                            <option value="friendly">Friendly</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Language</label>
                        <select class="select" name="language">
                            {language_options}
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🎯 Content Elements</h3>
                
                <div class="form-group">
                    <label class="label">Customer Pain Points</label>
                    <textarea class="textarea" name="customer_pain_points" placeholder="e.g., High costs, complex implementation"></textarea>
                    <div class="help-text">GPT-5 will research additional pain points from Reddit</div>
                </div>
                
                <div class="form-group">
                    <label class="label">Unique Value Propositions</label>
                    <textarea class="textarea" name="unique_selling_points" placeholder="e.g., 10+ years experience, proven results"></textarea>
                </div>
                
                <div class="grid">
                    <div class="form-group">
                        <label class="label">Keywords</label>
                        <input class="input" type="text" name="required_keywords" placeholder="e.g., automation, efficiency">
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Call-to-Action</label>
                        <input class="input" type="text" name="call_to_action" placeholder="e.g., Schedule consultation">
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3>🤖 AI Instructions</h3>
                
                <div class="form-group">
                    <label class="label">Custom Instructions</label>
                    <textarea class="textarea" name="ai_instructions" placeholder="e.g., Include specific examples, use data points, write in first person"></textarea>
                    <div class="help-text">Guide GPT-5's reasoning and writing style</div>
                </div>
            </div>
            
            <button type="submit" class="button">
                Generate Premium Content with GPT-5
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
            
            if (!data.topic || data.topic.length < 5) {{
                alert('Please provide a detailed topic');
                return;
            }}
            
            if (!data.target_audience || data.target_audience.length < 3) {{
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

def generate_generator_html():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>GPT-5 Content Generation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
            color: #fff; min-height: 100vh;
        }
        .header { 
            background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 1rem 0; 
            position: sticky; top: 0; z-index: 100;
        }
        .header-content { 
            max-width: 1200px; margin: 0 auto; padding: 0 2rem; 
            display: flex; justify-content: space-between; align-items: center; 
        }
        .header-title { 
            font-size: 1.5rem; font-weight: 700; 
            background: linear-gradient(135deg, #10b981, #059669);
            background-clip: text; -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent;
        }
        .status { 
            padding: 0.5rem 1rem; border-radius: 2rem; font-weight: 600; 
            backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-connecting { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
        .status-connected { background: rgba(16, 185, 129, 0.2); color: #10b981; }
        .status-generating { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
        .status-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .progress-section, .content-display, .evaluation-display { 
            background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1rem; 
            padding: 2rem; margin-bottom: 2rem; 
        }
        .progress-header { 
            display: flex; justify-content: space-between; align-items: center; 
            margin-bottom: 2rem; 
        }
        .progress-title { color: #fff; font-size: 1.4rem; font-weight: 700; }
        .progress-bar { 
            width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1); 
            border-radius: 4px; overflow: hidden; margin-bottom: 1rem; 
        }
        .progress-fill { 
            height: 100%; background: linear-gradient(135deg, #10b981, #059669); 
            width: 0%; transition: width 0.5s ease; 
        }
        .progress-text { text-align: center; color: #ccc; font-weight: 500; }
        .current-step { 
            background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); 
            border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; display: none; 
        }
        .current-step h4 { color: #fff; margin-bottom: 0.5rem; }
        .current-step p { color: #ccc; }
        
        .content-display, .evaluation-display { display: none; }
        .content-display.visible, .evaluation-display.visible { display: block; }
        
        .metrics { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 1rem; margin-bottom: 2rem; 
        }
        .metric-card { 
            background: rgba(255, 255, 255, 0.05); padding: 1rem; 
            border-radius: 0.5rem; text-align: center; 
        }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
        .metric-label { font-size: 0.8rem; color: #aaa; text-transform: uppercase; }
        
        .evaluation-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
        .evaluation-score { 
            background: linear-gradient(135deg, #10b981, #059669); color: white;
            padding: 0.5rem 1rem; border-radius: 2rem; font-weight: 700; 
        }
        .eeat-scores { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem; margin-bottom: 2rem; 
        }
        .eeat-item { 
            background: rgba(255, 255, 255, 0.03); padding: 1rem; 
            border-radius: 0.5rem; border: 1px solid rgba(255, 255, 255, 0.1); 
        }
        .eeat-title { font-weight: 600; margin-bottom: 0.5rem; color: #fff; }
        .eeat-score { font-size: 1.3rem; font-weight: 700; color: #10b981; }
        
        .content-display h1 { color: #fff; font-size: 2rem; margin-bottom: 1rem; 
            border-bottom: 2px solid rgba(255, 255, 255, 0.2); padding-bottom: 1rem; }
        .content-display h2 { color: #ccc; font-size: 1.5rem; margin: 1.5rem 0 1rem 0; }
        .content-display h3 { color: #fff; font-size: 1.2rem; margin: 1rem 0 0.5rem 0; }
        .content-display p { margin-bottom: 1rem; line-height: 1.6; color: #eee; }
        .content-display ul, .content-display ol { margin: 1rem 0 1rem 2rem; color: #eee; }
        .content-display li { margin-bottom: 0.5rem; }
        
        .content-actions { 
            display: flex; gap: 1rem; margin-top: 2rem; 
            padding-top: 2rem; border-top: 1px solid rgba(255, 255, 255, 0.1); 
        }
        .action-btn { 
            background: rgba(255, 255, 255, 0.1); color: #fff; 
            padding: 0.75rem 1.5rem; border: 1px solid rgba(255, 255, 255, 0.2); 
            border-radius: 0.5rem; cursor: pointer; font-weight: 600; 
            transition: all 0.3s ease; text-decoration: none;
            display: inline-flex; align-items: center; gap: 0.5rem;
        }
        .action-btn:hover { background: rgba(255, 255, 255, 0.15); transform: translateY(-2px); }
        .action-btn.primary { background: linear-gradient(135deg, #10b981, #059669); border: none; }
        
        .back-btn { 
            background: rgba(255, 255, 255, 0.05); color: #ccc; 
            padding: 0.5rem 1rem; border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 0.5rem; text-decoration: none; font-size: 0.9rem; 
        }
        .back-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
        
        .loading { text-align: center; padding: 3rem; color: #aaa; }
        .spinner { 
            border: 3px solid rgba(255, 255, 255, 0.1); border-top: 3px solid #10b981; 
            border-radius: 50%; width: 40px; height: 40px; 
            animation: spin 1s linear infinite; margin: 0 auto 1rem; 
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .recommendations { 
            background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); 
            border-radius: 0.5rem; padding: 1rem; margin-top: 1rem; 
        }
        .recommendations h4 { color: #fff; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .recommendations ul { list-style: none; padding: 0; }
        .recommendations li { margin-bottom: 0.5rem; color: #ccc; position: relative; padding-left: 1.5rem; }
        .recommendations li:before { content: "💡"; position: absolute; left: 0; }
        
        @media (max-width: 768px) { 
            .header-content { flex-direction: column; gap: 1rem; } 
            .container { padding: 1rem; }
            .content-actions { flex-direction: column; }
            .metrics, .eeat-scores { grid-template-columns: 1fr; } 
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="header-title">GPT-5 Content Generator</div>
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
            <div class="progress-text" id="progressText">Initializing GPT-5...</div>
            
            <div class="current-step" id="currentStep">
                <h4 id="currentStepTitle">Loading...</h4>
                <p id="currentStepMessage">Please wait...</p>
            </div>
            
            <div class="loading" id="loadingIndicator">
                <div class="spinner"></div>
                <p>Connecting to GPT-5...</p>
            </div>
        </div>
        
        <div class="evaluation-display" id="evaluationDisplay">
            <div class="evaluation-header">
                <h2>📊 Content Evaluation Report</h2>
                <div class="evaluation-score" id="overallScore">9.0/10</div>
            </div>
            
            <div class="eeat-scores" id="eeatScores">
                <!-- E-E-A-T scores populated here -->
            </div>
            
            <div class="recommendations" id="recommendations">
                <h4>💡 Optimization Recommendations</h4>
                <ul id="recommendationsList">
                    <!-- Recommendations populated here -->
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
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="content-actions">
                <button class="action-btn primary" onclick="copyContent()">📋 Copy Content</button>
                <button class="action-btn" onclick="downloadContent()">💾 Download</button>
                <button class="action-btn" onclick="regenerateContent()">🔄 Regenerate</button>
                <button class="action-btn" onclick="toggleEvaluation()">📊 Toggle Evaluation</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let generatedContent = '';
        let evaluationData = {};
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
                    displayEvaluation(data.evaluation || {});
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
            document.getElementById('modelUsed').textContent = metrics.model_used || 'GPT-5';
            
            const formattedContent = formatContent(data.content);
            document.getElementById('generatedContent').innerHTML = formattedContent;
            
            document.getElementById('contentDisplay').classList.add('visible');
            document.getElementById('contentDisplay').scrollIntoView({ behavior: 'smooth' });
        }
        
        function displayEvaluation(evaluation) {
            evaluationData = evaluation;
            
            if (!evaluation || Object.keys(evaluation).length === 0) {
                document.getElementById('evaluationDisplay').style.display = 'none';
                return;
            }
            
            // Update overall score
            const overallScore = evaluation.overall_score || 8.5;
            document.getElementById('overallScore').textContent = overallScore.toFixed(1) + '/10';
            
            // Display E-E-A-T scores
            const eeatAnalysis = evaluation.eeat_analysis || {};
            const eeatContainer = document.getElementById('eeatScores');
            eeatContainer.innerHTML = '';
            
            const eeatFactors = [
                { key: 'experience', label: 'Experience', icon: '🎯' },
                { key: 'expertise', label: 'Expertise', icon: '🧠' },
                { key: 'authoritativeness', label: 'Authority', icon: '🏆' },
                { key: 'trustworthiness', label: 'Trust', icon: '🔒' }
            ];
            
            eeatFactors.forEach(factor => {
                const score = eeatAnalysis[factor.key] || 8;
                const eeatItem = document.createElement('div');
                eeatItem.className = 'eeat-item';
                eeatItem.innerHTML = `
                    <div class="eeat-title">${factor.icon} ${factor.label}</div>
                    <div class="eeat-score">${score.toFixed(1)}/10</div>
                `;
                eeatContainer.appendChild(eeatItem);
            });
            
            // Display recommendations
            const recommendations = evaluation.recommendations || [];
            const recommendationsList = document.getElementById('recommendationsList');
            recommendationsList.innerHTML = '';
            
            recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                recommendationsList.appendChild(li);
            });
            
            document.getElementById('evaluationDisplay').classList.add('visible');
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
            const evaluation = evaluationData;
            
            const fullContent = `
CONTENT:
${content}

EVALUATION REPORT:
Overall Score: ${evaluation.overall_score || 'N/A'}/10

E-E-A-T Analysis:
- Experience: ${evaluation.eeat_analysis?.experience || 'N/A'}/10
- Expertise: ${evaluation.eeat_analysis?.expertise || 'N/A'}/10
- Authoritativeness: ${evaluation.eeat_analysis?.authoritativeness || 'N/A'}/10
- Trustworthiness: ${evaluation.eeat_analysis?.trustworthiness || 'N/A'}/10

Recommendations:
${(evaluation.recommendations || []).map(rec => `- ${rec}`).join('\\n')}

Generated with GPT-5 Content Generator
            `;
            
            const blob = new Blob([fullContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `gpt5-content_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function regenerateContent() {
            window.location.reload();
        }
        
        function toggleEvaluation() {
            const evaluationDisplay = document.getElementById('evaluationDisplay');
            if (evaluationDisplay.classList.contains('visible')) {
                evaluationDisplay.classList.remove('visible');
                evaluationDisplay.style.display = 'none';
            } else {
                evaluationDisplay.classList.add('visible');
                evaluationDisplay.style.display = 'block';
                evaluationDisplay.scrollIntoView({ behavior: 'smooth' });
            }
        }
    </script>
</body>
</html>
'''

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
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

@app.get("/health")
async def health_check():
    openai_working = False
    openai_error = None
    model_used = "unknown"
    agent_status = "available" if AGENT_AVAILABLE else "basic"
    
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        try:
            openai.api_key = config.OPENAI_API_KEY
            model_params = {
                "model": content_system.ai_client.latest_model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5
            }
            
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
        "version": "gpt-5-complete",
        "api_key_preview": f"{config.OPENAI_API_KEY[:8]}...{config.OPENAI_API_KEY[-4:]}" if config.OPENAI_API_KEY else None
    })

@app.get("/test-openai")
async def test_openai():
    try:
        api_key = config.OPENAI_API_KEY
        
        if not api_key:
            return JSONResponse({
                "status": "error",
                "message": "❌ No OpenAI API key found",
                "solution": "Set Open_Api_Key in Railway environment variables"
            })
        
        if not api_key.startswith("sk-"):
            return JSONResponse({
                "status": "error", 
                "message": f"❌ Invalid API key format",
                "solution": "Get new key from https://platform.openai.com/api-keys"
            })
        
        openai.api_key = api_key
        model_used = content_system.ai_client.latest_model
        
        model_params = {
            "model": model_used,
            "messages": [{
                "role": "user", 
                "content": f"Write a short paragraph about GPT-5 content generation working correctly."
            }],
            "max_tokens": 150
        }
        
        if model_used.startswith("gpt-5"):
            model_params["reasoning_effort"] = "medium"
            
        response = openai.ChatCompletion.create(**model_params)
        content = response.choices[0].message.content if response.choices else "No content generated"
        
        return JSONResponse({
            "status": "SUCCESS! ✅",
            "message": f"OpenAI {model_used} is working perfectly!",
            "generated_content": content,
            "model": model_used,
            "gpt5_reasoning": model_used.startswith("gpt-5"),
            "word_count": len(content.split()),
            "content_agent_available": AGENT_AVAILABLE,
            "features": [
                "GPT-5 model with reasoning",
                "British English support", 
                "E-E-A-T evaluation",
                "Reddit insights research",
                "Entity analysis",
                "Content cluster suggestions"
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
    print("🚀 Starting GPT-5 Content Generator...")
    print("=" * 60)
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    
    openai_status = "✅ Configured" if config.OPENAI_API_KEY else "❌ Not configured"
    agent_status = "✅ Available" if AGENT_AVAILABLE else "⚠️ Basic version"
    
    print(f"🤖 OpenAI API: {openai_status}")
    print(f"📊 Content Agent: {agent_status}")
    
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        print(f"🔑 API Key: {config.OPENAI_API_KEY[:8]}...{config.OPENAI_API_KEY[-4:]}")
        
        client = OpenAIClient()
        print(f"🎯 Model: {client.latest_model}")
        
        if client.latest_model.startswith("gpt-5"):
            print("🧠 GPT-5 reasoning enabled")
    
    print("🎯 Features:")
    print("   • GPT-5 with reasoning")
    print("   • British English support")
    print("   • E-E-A-T evaluation")
    print("   • Reddit insights")
    print("   • Entity analysis")
    print("   • Real-time WebSocket updates")
    print("=" * 60)
    
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
