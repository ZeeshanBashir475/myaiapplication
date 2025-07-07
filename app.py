# 🚀 ZEE SEO TOOL v5.0 - MAIN APP.PY FILE
# Replace your existing app.py with this entire file

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# FastAPI imports
from fastapi import FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add src to path
sys.path.append('/app/src')
sys.path.append('/app')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import your actual AI agents with corrected paths and fallbacks
def safe_import(module_path, class_name, alternative_paths=None):
    """Safely import agents with multiple path attempts and proper error handling"""
    paths_to_try = [module_path]
    if alternative_paths:
        paths_to_try.extend(alternative_paths)
    
    for path in paths_to_try:
        try:
            module = __import__(path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            logger.info(f"✅ Successfully imported {class_name} from {path}")
            return agent_class
        except ImportError as e:
            logger.warning(f"⚠️ Failed to import {class_name} from {path}: {e}")
            continue
        except Exception as e:
            logger.warning(f"⚠️ Error importing {class_name} from {path}: {e}")
            continue
    
    logger.error(f"❌ Could not import {class_name} from any path")
    return None

# Import your fixed agents
from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.agents.streaming_chat import StreamingChatAgent

# Try to import other agents
AdvancedTopicResearchAgent = safe_import(
    'src.agents.AdvancedTopicResearchAgent', 
    'AdvancedTopicResearchAgent',
    ['src.agents.advanced_topic_research', 'agents.AdvancedTopicResearchAgent', 'AdvancedTopicResearchAgent']
)

ContentQualityScorer = safe_import(
    'src.agents.content_quality_scorer', 
    'ContentQualityScorer',
    ['src.agents.ContentQualityScorer', 'agents.content_quality_scorer']
)

ContentTypeClassifier = safe_import(
    'src.agents.content_type_classifier', 
    'ContentTypeClassifier',
    ['src.agents.ContentTypeClassifier', 'agents.content_type_classifier']
)

HumanInputIdentifier = safe_import(
    'src.agents.human_input_identifier', 
    'HumanInputIdentifier',
    ['src.agents.HumanInputIdentifier', 'agents.human_input_identifier']
)

EnhancedEEATAssessor = safe_import(
    'src.agents.eeat_assessor', 
    'EnhancedEEATAssessor',
    ['src.agents.EnhancedEEATAssessor', 'agents.eeat_assessor']
)

IntentClassifier = safe_import(
    'src.agents.intent_classifier', 
    'IntentClassifier',
    ['src.agents.IntentClassifier', 'agents.intent_classifier']
)

BusinessContextCollector = safe_import(
    'src.agents.business_context_collector', 
    'BusinessContextCollector',
    ['src.agents.BusinessContextCollector', 'agents.business_context_collector']
)

FullContentGenerator = safe_import(
    'src.agents.content_generator', 
    'FullContentGenerator',
    ['src.agents.FullContentGenerator', 'agents.content_generator']
)

# Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ZeeSEOTool/1.0")
    PORT = int(os.getenv("PORT", 8002))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

config = Config()

# Initialize FastAPI
app = FastAPI(title="Zee SEO Tool v5.0 - Real Reddit + Streaming Chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Enhanced LLM Client
class EnhancedLLMClient:
    """Enhanced LLM client with streaming support"""
    
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
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 2000):
        """Generate streaming response like Claude"""
        if self.anthropic_client:
            try:
                with self.anthropic_client.messages.stream(
                    model="claude-3-sonnet-20240229",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        yield text
            except Exception as e:
                logger.error(f"❌ Anthropic streaming error: {e}")
                yield f"Error: {str(e)}"
        else:
            yield "AI service not available. Please check API keys."
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate non-streaming response"""
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                logger.error(f"❌ Anthropic generation error: {e}")
                return f"Error: {str(e)}"
        return "AI service not available."

# WebSocket Connection Manager
class ConnectionManager:
    """Manage WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"✅ WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"❌ WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except:
                self.disconnect(session_id)

# Advanced Content Analysis System (Updated)
class ZeeSEOAdvancedSystem:
    """Advanced content analysis system with streaming chat"""
    
    def __init__(self):
        self.llm_client = EnhancedLLMClient()
        self.connection_manager = ConnectionManager()
        self.sessions = {}
        self.init_agents()
    
    def init_agents(self):
        """Initialize all available agents"""
        self.agents = {}
        
        # Initialize REAL Reddit researcher
        try:
            self.agents['reddit_research'] = EnhancedRedditResearcher()
            logger.info("✅ Real Reddit Researcher initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Reddit Researcher: {e}")
        
        # Initialize Streaming Chat Agent
        try:
            self.agents['streaming_chat'] = StreamingChatAgent(self.llm_client)
            logger.info("✅ Streaming Chat Agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Streaming Chat: {e}")
        
        # Initialize other agents with safe imports
        if AdvancedTopicResearchAgent:
            try:
                self.agents['topic_research'] = AdvancedTopicResearchAgent(self.llm_client)
                logger.info("✅ AdvancedTopicResearchAgent initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AdvancedTopicResearchAgent: {e}")
        
        if IntentClassifier:
            try:
                self.agents['intent_classifier'] = IntentClassifier(self.llm_client)
                logger.info("✅ IntentClassifier initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize IntentClassifier: {e}")
        
        if ContentTypeClassifier:
            try:
                self.agents['content_classifier'] = ContentTypeClassifier(self.llm_client)
                logger.info("✅ ContentTypeClassifier initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ContentTypeClassifier: {e}")
        
        if HumanInputIdentifier:
            try:
                self.agents['human_input'] = HumanInputIdentifier(self.llm_client)
                logger.info("✅ HumanInputIdentifier initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize HumanInputIdentifier: {e}")
        
        if ContentQualityScorer:
            try:
                self.agents['quality_scorer'] = ContentQualityScorer(self.llm_client)
                logger.info("✅ ContentQualityScorer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ContentQualityScorer: {e}")
        
        if EnhancedEEATAssessor:
            try:
                self.agents['eeat_assessor'] = EnhancedEEATAssessor(self.llm_client)
                logger.info("✅ EnhancedEEATAssessor initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize EnhancedEEATAssessor: {e}")
        
        if FullContentGenerator:
            try:
                self.agents['content_generator'] = FullContentGenerator(self.llm_client)
                logger.info("✅ FullContentGenerator initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize FullContentGenerator: {e}")
        
        if BusinessContextCollector:
            try:
                self.agents['business_context'] = BusinessContextCollector()
                logger.info("✅ BusinessContextCollector initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize BusinessContextCollector: {e}")
        
        logger.info(f"🎯 System initialized with {len(self.agents)} active agents")
    
    async def start_analysis(self, form_data: Dict, session_id: str):
        """Start comprehensive analysis with REAL Reddit research"""
        
        logger.info(f"🚀 Starting analysis for session: {session_id}")
        
        # Initialize session
        session = {
            'session_id': session_id,
            'form_data': form_data,
            'conversation_history': [],
            'current_content': '',
            'analysis_results': {},
            'created_at': datetime.now().isoformat()
        }
        self.sessions[session_id] = session
        
        # Send status updates
        await self.connection_manager.send_message(session_id, {
            'type': 'status',
            'message': '🔍 Starting REAL Reddit research...'
        })
        
        # REAL Reddit Research
        if 'reddit_research' in self.agents:
            reddit_data = await self.agents['reddit_research'].research_topic_comprehensive(
                topic=form_data['topic'],
                subreddits=['AskReddit', 'explainlikeimfive', 'LifeProTips'],  # Will auto-discover more
                max_posts_per_subreddit=20
            )
            session['analysis_results']['reddit_insights'] = reddit_data
            
            posts_analyzed = reddit_data.get('research_metadata', {}).get('total_posts_analyzed', 0)
            await self.connection_manager.send_message(session_id, {
                'type': 'status',
                'message': f"✅ Analyzed {posts_analyzed} real Reddit posts"
            })
        else:
            await self.connection_manager.send_message(session_id, {
                'type': 'status',
                'message': '⚠️ Reddit researcher not available, using fallback'
            })
        
        # Run other analysis stages
        await self._run_analysis_stages(session, session_id)
        
        # Generate content
        await self.connection_manager.send_message(session_id, {
            'type': 'status',
            'message': '✍️ Generating content based on real pain points...'
        })
        
        content = await self._generate_streaming_content(form_data, session['analysis_results'], session_id)
        session['current_content'] = content
        
        # Send completion
        await self.connection_manager.send_message(session_id, {
            'type': 'analysis_complete',
            'content': content,
            'reddit_insights': session['analysis_results'].get('reddit_insights', {}),
            'session_id': session_id
        })
    
    async def _run_analysis_stages(self, session: Dict, session_id: str):
        """Run all analysis stages"""
        
        form_data = session['form_data']
        topic = form_data['topic']
        
        # Stage 1: Intent Analysis
        if 'intent_classifier' in self.agents:
            try:
                intent_data = self.agents['intent_classifier'].classify_intent(
                    topic, form_data.get('target_audience', '')
                )
                session['analysis_results']['intent'] = intent_data
            except Exception as e:
                logger.error(f"Intent classification failed: {e}")
        
        # Stage 2: Content Type Classification
        if 'content_classifier' in self.agents:
            try:
                content_type_data = self.agents['content_classifier'].classify_content_type(
                    topic=topic,
                    target_audience=form_data.get('target_audience', ''),
                    business_context=form_data
                )
                session['analysis_results']['content_type'] = content_type_data
            except Exception as e:
                logger.error(f"Content classification failed: {e}")
        
        # Stage 3: Topic Research
        if 'topic_research' in self.agents:
            try:
                topic_research = self.agents['topic_research'].research_topic_comprehensive(
                    topic=topic,
                    industry=form_data.get('industry', ''),
                    target_audience=form_data.get('target_audience', ''),
                    business_goals=form_data.get('business_goals', '')
                )
                session['analysis_results']['topic_research'] = topic_research
            except Exception as e:
                logger.error(f"Topic research failed: {e}")
        
        # Stage 4: Human Input Identification
        if 'human_input' in self.agents:
            try:
                human_inputs = self.agents['human_input'].identify_human_inputs(
                    topic=topic,
                    content_type=session['analysis_results'].get('content_type', {}).get('primary_content_type', 'guide'),
                    business_context=form_data
                )
                session['analysis_results']['human_inputs'] = human_inputs
            except Exception as e:
                logger.error(f"Human input identification failed: {e}")
    
    async def _generate_streaming_content(self, form_data: Dict, analysis_results: Dict, session_id: str) -> str:
        """Generate content with streaming output"""
        
        topic = form_data['topic']
        reddit_insights = analysis_results.get('reddit_insights', {})
        pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
        customer_quotes = reddit_insights.get('customer_voice', {}).get('authentic_quotes', [])
        
        prompt = f"""Create comprehensive content about "{topic}" based on REAL Reddit research.

REAL PAIN POINTS DISCOVERED:
{json.dumps(pain_points, indent=2)}

AUTHENTIC CUSTOMER QUOTES:
{chr(10).join(['- "' + quote + '"' for quote in customer_quotes[:5]])}

USER CONTEXT:
- Target Audience: {form_data.get('target_audience', '')}
- Unique Value Prop: {form_data.get('unique_value_prop', '')}
- Customer Pain Points: {form_data.get('customer_pain_points', '')}

Create content that:
1. Directly addresses the REAL pain points found in Reddit research
2. Uses authentic customer language from the quotes
3. Provides specific solutions to the most common problems
4. Builds trust through expertise and experience
5. Is written in {form_data.get('language', 'British English')}

Make it comprehensive (2000-3000 words) and genuinely helpful."""

        # Stream the content generation
        content_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=4000):
            content_chunks.append(chunk)
            await self.connection_manager.send_message(session_id, {
                'type': 'content_stream',
                'chunk': chunk
            })
        
        return ''.join(content_chunks)
    
    async def process_chat_message(self, session_id: str, message: str):
        """Process chat message using streaming chat agent"""
        
        if session_id not in self.sessions:
            await self.connection_manager.send_message(session_id, {
                'type': 'error',
                'message': 'Session not found'
            })
            return
        
        session = self.sessions[session_id]
        
        # Use streaming chat agent
        if 'streaming_chat' in self.agents:
            await self.agents['streaming_chat'].process_message(
                message=message,
                session=session,
                connection_manager=self.connection_manager
            )
        else:
            # Fallback response
            await self.connection_manager.send_message(session_id, {
                'type': 'assistant_start'
            })
            
            fallback_response = f"I understand you want to: {message}\n\nUnfortunately, the streaming chat agent is not available. Please check your agent imports."
            
            for char in fallback_response:
                await self.connection_manager.send_message(session_id, {
                    'type': 'assistant_stream',
                    'chunk': char
                })
                await asyncio.sleep(0.05)
            
            await self.connection_manager.send_message(session_id, {
                'type': 'assistant_complete'
            })

# Initialize the system
zee_system = ZeeSEOAdvancedSystem()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced homepage"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool v5.0 - Real Reddit + Streaming Chat</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                text-align: center;
                max-width: 800px;
                padding: 4rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 1.5rem;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .title {
                font-size: 3.5rem;
                font-weight: 900;
                margin-bottom: 1rem;
                background: linear-gradient(45deg, #fff, #f0f8ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 1.4rem;
                margin-bottom: 2rem;
                opacity: 0.95;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin: 2rem 0;
                text-align: left;
            }
            .feature {
                padding: 1rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 0.5rem;
                font-size: 0.9rem;
            }
            .cta-button {
                background: white;
                color: #667eea;
                padding: 1.5rem 3rem;
                border: none;
                border-radius: 1rem;
                font-size: 1.3rem;
                font-weight: 700;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
                margin-top: 1rem;
            }
            .cta-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title">🎯 Zee SEO Tool v5.0</h1>
            <p class="subtitle">Real Reddit Research + Claude-style Streaming Chat</p>
            
            <div class="features">
                <div class="feature">🔥 REAL Reddit Scraping<br><small>Actual PRAW API calls, not fake data</small></div>
                <div class="feature">💬 Claude-style Chat<br><small>Streaming responses, real-time updates</small></div>
                <div class="feature">🔄 Live Content Updates<br><small>Modify content through conversation</small></div>
                <div class="feature">🧠 AI Pain Point Analysis<br><small>Extract real customer problems</small></div>
                <div class="feature">⚡ WebSocket Streaming<br><small>Real-time, responsive interface</small></div>
                <div class="feature">🎨 Conversational Content<br><small>Iterate and improve naturally</small></div>
            </div>
            
            <a href="/app" class="cta-button">
                🚀 Start Real Analysis
            </a>
        </div>
    </body>
    </html>
    """)

@app.get("/app", response_class=HTMLResponse)
async def app_interface():
    """Streaming chat interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool v5.0 - Real Analysis</title>
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
                padding: 1.5rem 0;
                text-align: center;
            }
            
            .container {
                max-width: 800px;
                margin: 2rem auto;
                padding: 0 2rem;
            }
            
            .form-card {
                background: white;
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .label {
                display: block;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #2d3748;
            }
            
            .input, .textarea, .select {
                width: 100%;
                padding: 1rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 1rem;
                transition: border-color 0.3s ease;
            }
            
            .input:focus, .textarea:focus, .select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .textarea {
                min-height: 120px;
                resize: vertical;
            }
            
            .submit-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2rem;
                border: none;
                border-radius: 0.5rem;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: transform 0.2s ease;
            }
            
            .submit-btn:hover {
                transform: translateY(-2px);
            }
            
            .submit-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            /* Chat Interface */
            .chat-container {
                display: none;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                height: 80vh;
                display: flex;
                flex-direction: column;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem;
                border-radius: 1rem 1rem 0 0;
                font-weight: 600;
            }
            
            .chat-messages {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
                background: #fafbfc;
            }
            
            .message {
                margin-bottom: 1rem;
                padding: 1rem;
                border-radius: 0.75rem;
                max-width: 80%;
                word-wrap: break-word;
            }
            
            .message.user {
                background: #667eea;
                color: white;
                margin-left: auto;
            }
            
            .message.assistant {
                background: white;
                color: #1a202c;
                border: 1px solid #e2e8f0;
            }
            
            .message.system {
                background: #f0fff4;
                color: #065f46;
                border: 1px solid #86efac;
                text-align: center;
                margin: 0 auto;
            }
            
            .chat-input-container {
                padding: 1rem;
                border-top: 1px solid #e2e8f0;
                background: white;
                border-radius: 0 0 1rem 1rem;
            }
            
            .chat-input-wrapper {
                display: flex;
                gap: 0.5rem;
            }
            
            .chat-input {
                flex: 1;
                padding: 0.75rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 1rem;
            }
            
            .chat-send-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 0.5rem;
                font-weight: 600;
                cursor: pointer;
            }
            
            .content-display {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 0.5rem;
                padding: 1.5rem;
                margin: 1rem 0;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .reddit-insights {
                background: #f0f9ff;
                border: 1px solid #0ea5e9;
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 1rem 0;
            }
            
            .typing-indicator {
                display: none;
                color: #4a5568;
                font-style: italic;
                padding: 0.5rem;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Real Reddit Research + Streaming Chat</h1>
            <p>Analyze real customer pain points with Claude-style conversation</p>
        </div>
        
        <div class="container">
            <!-- Form Interface -->
            <div id="formContainer" class="form-card">
                <h2 style="margin-bottom: 1.5rem;">Start Your Analysis</h2>
                <form id="analysisForm">
                    <div class="form-group">
                        <label class="label">Topic *</label>
                        <input class="input" name="topic" type="text" 
                               placeholder="e.g., 'best budget laptops for university students'" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Target Audience *</label>
                        <input class="input" name="target_audience" type="text" 
                               placeholder="e.g., 'university students aged 18-24'" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Your Unique Value Proposition *</label>
                        <textarea class="textarea" name="unique_value_prop" required
                                  placeholder="What makes you uniquely qualified? Include credentials, experience, special knowledge..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Customer Pain Points You Address *</label>
                        <textarea class="textarea" name="customer_pain_points" required
                                  placeholder="What specific problems do your customers face that you solve?"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Language</label>
                        <select class="select" name="language">
                            <option value="British English">British English</option>
                            <option value="American English">American English</option>
                            <option value="International English">International English</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="submit-btn" id="submitBtn">
                        🚀 Start Real Reddit Analysis
                    </button>
                </form>
            </div>
            
            <!-- Chat Interface (Hidden Initially) -->
            <div id="chatContainer" class="chat-container" style="display: none;">
                <div class="chat-header">
                    <span id="chatTitle">🤖 AI Content Assistant</span>
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <!-- Messages will be added here -->
                </div>
                
                <div class="chat-input-container">
                    <div class="typing-indicator" id="typingIndicator">AI is typing...</div>
                    <div class="chat-input-wrapper">
                        <input type="text" class="chat-input" id="chatInput" 
                               placeholder="Ask me to modify the content or answer questions...">
                        <button class="chat-send-btn" id="sendBtn">Send</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let websocket = null;
            let sessionId = null;
            let currentContent = '';
            
            // Form submission
            document.getElementById('analysisForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                // Generate session ID
                sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                
                // Switch to chat interface
                document.getElementById('formContainer').style.display = 'none';
                document.getElementById('chatContainer').style.display = 'flex';
                
                // Connect WebSocket
                connectWebSocket(sessionId);
                
                // Start analysis
                addSystemMessage('🚀 Starting real Reddit analysis...');
                
                try {
                    const response = await fetch('/start-analysis', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ...data, session_id: sessionId })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Analysis failed to start');
                    }
                } catch (error) {
                    addSystemMessage(`❌ Error: ${error.message}`);
                }
            });
            
            // WebSocket connection
            function connectWebSocket(sessionId) {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
                
                websocket = new WebSocket(wsUrl);
                
                websocket.onopen = () => {
                    console.log('WebSocket connected');
                };
                
                websocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                websocket.onclose = () => {
                    console.log('WebSocket disconnected');
                };
                
                websocket.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    addSystemMessage('❌ Connection error. Please refresh the page.');
                };
            }
            
            // Handle WebSocket messages
            let currentAssistantMessage = null;
            
            function handleWebSocketMessage(data) {
                switch (data.type) {
                    case 'status':
                        addSystemMessage(data.message);
                        break;
                        
                    case 'content_stream':
                        appendToCurrentMessage(data.chunk);
                        break;
                        
                    case 'analysis_complete':
                        currentContent = data.content;
                        addSystemMessage('✅ Analysis complete! Content generated based on real Reddit research.');
                        displayContent(data.content);
                        displayRedditInsights(data.reddit_insights);
                        addSystemMessage('💬 You can now chat with me to modify the content. Try asking: "Make it more beginner-friendly" or "Add more examples"');
                        break;
                        
                    case 'assistant_start':
                        startAssistantMessage();
                        break;
                        
                    case 'assistant_stream':
                        appendToCurrentMessage(data.chunk);
                        break;
                        
                    case 'assistant_complete':
                        completeAssistantMessage();
                        break;
                        
                    case 'content_update_start':
                        addSystemMessage('🔄 Updating content...');
                        break;
                        
                    case 'content_update_stream':
                        updateContentDisplay(data.chunk);
                        break;
                        
                    case 'content_updated':
                        currentContent = data.content;
                        addSystemMessage('✅ Content updated successfully!');
                        break;
                        
                    case 'error':
                        addSystemMessage(`❌ Error: ${data.message}`);
                        break;
                }
            }
            
            // Chat functions
            function addMessage(content, type) {
                const messagesContainer = document.getElementById('chatMessages');
                const message = document.createElement('div');
                message.className = `message ${type}`;
                message.innerHTML = content;
                messagesContainer.appendChild(message);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                return message;
            }
            
            function addSystemMessage(content) {
                addMessage(content, 'system');
            }
            
            function addUserMessage(content) {
                addMessage(content, 'user');
            }
            
            function startAssistantMessage() {
                currentAssistantMessage = addMessage('', 'assistant');
                document.getElementById('typingIndicator').style.display = 'block';
            }
            
            function appendToCurrentMessage(chunk) {
                if (currentAssistantMessage) {
                    currentAssistantMessage.innerHTML += chunk;
                    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
                }
            }
            
            function completeAssistantMessage() {
                currentAssistantMessage = null;
                document.getElementById('typingIndicator').style.display = 'none';
            }
            
            function displayContent(content) {
                const contentDiv = document.createElement('div');
                contentDiv.className = 'content-display';
                contentDiv.innerHTML = `<strong>📄 Generated Content:</strong><br><br>${content}`;
                document.getElementById('chatMessages').appendChild(contentDiv);
                document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
            }
            
            function displayRedditInsights(insights) {
                const painPoints = insights.critical_pain_points?.top_pain_points || {};
                const quotes = insights.customer_voice?.authentic_quotes || [];
                const metadata = insights.research_metadata || {};
                
                let insightsHtml = `<strong>🔍 Reddit Research Insights:</strong><br><br>`;
                insightsHtml += `<strong>Posts Analyzed:</strong> ${metadata.total_posts_analyzed || 0}<br>`;
                insightsHtml += `<strong>Data Source:</strong> ${metadata.data_source || 'Unknown'}<br><br>`;
                
                if (Object.keys(painPoints).length > 0) {
                    insightsHtml += `<strong>Top Pain Points:</strong><br>`;
                    Object.entries(painPoints).slice(0, 5).forEach(([pain, count]) => {
                        insightsHtml += `• ${pain.replace(/_/g, ' ')}: ${count} mentions<br>`;
                    });
                    insightsHtml += `<br>`;
                }
                
                if (quotes.length > 0) {
                    insightsHtml += `<strong>Customer Quotes:</strong><br>`;
                    quotes.slice(0, 3).forEach(quote => {
                        insightsHtml += `• "${quote}"<br>`;
                    });
                }
                
                const insightsDiv = document.createElement('div');
                insightsDiv.className = 'reddit-insights';
                insightsDiv.innerHTML = insightsHtml;
                document.getElementById('chatMessages').appendChild(insightsDiv);
                document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
            }
            
            function updateContentDisplay(chunk) {
                const contentDisplays = document.querySelectorAll('.content-display');
                if (contentDisplays.length > 0) {
                    const lastDisplay = contentDisplays[contentDisplays.length - 1];
                    lastDisplay.innerHTML += chunk;
                }
            }
            
            // Send chat message
            function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                
                if (!message || !websocket) return;
                
                addUserMessage(message);
                input.value = '';
                
                websocket.send(JSON.stringify({
                    type: 'chat_message',
                    message: message
                }));
            }
            
            // Event listeners
            document.getElementById('sendBtn').addEventListener('click', sendMessage);
            document.getElementById('chatInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """)

@app.post("/start-analysis")
async def start_analysis(request: Request):
    """Start comprehensive analysis"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Start analysis in background
        asyncio.create_task(zee_system.start_analysis(data, session_id))
        
        return {"status": "started", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Analysis start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await zee_system.connection_manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('type') == 'chat_message':
                await zee_system.process_chat_message(session_id, data.get('message', ''))
                
    except WebSocketDisconnect:
        zee_system.connection_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        zee_system.connection_manager.disconnect(session_id)

@app.get("/debug/agents")
async def debug_agents():
    """Debug endpoint to show agent status"""
    agent_status = {}
    
    for agent_name, agent in zee_system.agents.items():
        agent_status[agent_name] = f"✅ {type(agent).__name__}"
    
    return JSONResponse({
        "active_agents": agent_status,
        "total_agents": len(zee_system.agents),
        "reddit_configured": bool(config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY)
    })

if __name__ == "__main__":
    print("🚀 Starting Zee SEO Tool v5.0 - Real Reddit + Streaming Chat...")
    print("=" * 80)
    
    # Check Reddit credentials
    if config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET:
        print("✅ Reddit credentials configured")
    else:
        print("❌ Reddit credentials missing - set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
    
    # Check Anthropic credentials
    if config.ANTHROPIC_API_KEY:
        print("✅ Anthropic API key configured")
    else:
        print("❌ Anthropic API key missing - set ANTHROPIC_API_KEY")
    
    print("=" * 80)
    print(f"🌟 Access the application at: http://localhost:{config.PORT}/")
    print(f"🔧 Debug agent status at: http://localhost:{config.PORT}/debug/agents")
    print("=" * 80)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=config.PORT, log_level="info")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
