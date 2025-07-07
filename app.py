import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

# FastAPI and WebSocket imports
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

# Import all your agents with proper error handling
def safe_import(module_path, class_name, alternative_paths=None):
    """Safely import agents with multiple path attempts"""
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

# Import all your agents
AdvancedTopicResearchAgent = safe_import('src.agents.AdvancedTopicResearchAgent', 'AdvancedTopicResearchAgent')
ContentQualityScorer = safe_import('src.agents.content_quality_scorer', 'ContentQualityScorer')
ContentTypeClassifier = safe_import('src.agents.content_type_classifier', 'ContentTypeClassifier')
HumanInputIdentifier = safe_import('src.agents.human_input_identifier', 'HumanInputIdentifier')
EnhancedEEATAssessor = safe_import('src.agents.eeat_assessor', 'EnhancedEEATAssessor')
IntentClassifier = safe_import('src.agents.intent_classifier', 'IntentClassifier')
BusinessContextCollector = safe_import('src.agents.business_context_collector', 'BusinessContextCollector')
FullContentGenerator = safe_import('src.agents.content_generator', 'FullContentGenerator')
EnhancedRedditResearcher = safe_import('src.agents.enhanced_reddit_researcher', 'EnhancedRedditResearcher')
StreamingChatAgent = safe_import('src.agents.streaming_chat', 'StreamingChatAgent')
KnowledgeGraphTrendsAgent = safe_import('src.agents.knowledge_graph_trends_agent', 'KnowledgeGraphTrendsAgent')
JourneyMapper = safe_import('src.agents.journey_mapper', 'JourneyMapper')

# Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    PORT = int(os.getenv("PORT", 8002))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

config = Config()

# Initialize FastAPI
app = FastAPI(title="Zee SEO Tool v5.0 - Real-Time Streaming System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Enhanced LLM Client with Streaming
class StreamingLLMClient:
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
                logger.error(f"❌ Streaming generation error: {e}")
                yield f"Error: {str(e)}"
        else:
            # Fallback non-streaming
            response = f"Response to: {prompt[:100]}..."
            for char in response:
                yield char
                await asyncio.sleep(0.01)

# WebSocket Connection Manager
class ConnectionManager:
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
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Failed to send WebSocket message: {e}")
                self.disconnect(session_id)

# Initialize connection manager
manager = ConnectionManager()

# Advanced Content Analysis System with Real-Time Updates
class ZeeSEOStreamingSystem:
    """Complete system with all agents and real-time streaming"""
    
    def __init__(self):
        self.llm_client = StreamingLLMClient()
        self.sessions = {}
        self.init_all_agents()
    
    def init_all_agents(self):
        """Initialize ALL available agents"""
        self.agents = {}
        
        # Core agents
        agents_to_init = [
            ('topic_research', AdvancedTopicResearchAgent),
            ('reddit_research', EnhancedRedditResearcher),
            ('intent_classifier', IntentClassifier),
            ('content_classifier', ContentTypeClassifier),
            ('human_input', HumanInputIdentifier),
            ('quality_scorer', ContentQualityScorer),
            ('eeat_assessor', EnhancedEEATAssessor),
            ('content_generator', FullContentGenerator),
            ('business_context', BusinessContextCollector),
            ('streaming_chat', StreamingChatAgent),
            ('kg_trends', KnowledgeGraphTrendsAgent),
            ('journey_mapper', JourneyMapper)
        ]
        
        for agent_name, agent_class in agents_to_init:
            if agent_class:
                try:
                    if agent_name == 'streaming_chat':
                        self.agents[agent_name] = agent_class(self.llm_client)
                    elif agent_name == 'reddit_research':
                        self.agents[agent_name] = agent_class()
                    elif agent_name == 'business_context':
                        self.agents[agent_name] = agent_class()
                    elif agent_name == 'kg_trends':
                        self.agents[agent_name] = agent_class(
                            google_api_key=config.GOOGLE_API_KEY,
                            llm_client=self.llm_client
                        )
                    else:
                        self.agents[agent_name] = agent_class(self.llm_client)
                    
                    logger.info(f"✅ {agent_name} initialized")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {agent_name}: {e}")
        
        logger.info(f"🎯 System initialized with {len(self.agents)} active agents")
    
    async def analyze_comprehensive_streaming(self, form_data: Dict[str, str], session_id: str) -> Dict[str, Any]:
        """Run comprehensive analysis with real-time streaming updates"""
        
        topic = form_data['topic']
        
        # Initialize session
        self.sessions[session_id] = {
            'session_id': session_id,
            'form_data': form_data,
            'current_content': '',
            'conversation_history': [],
            'analysis_results': {},
            'live_metrics': {
                'overall_score': 0.0,
                'trust_score': 0.0,
                'quality_score': 0.0,
                'pain_points_count': 0,
                'improvements_applied': 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Send start signal
        await manager.send_message(session_id, {
            'type': 'analysis_start',
            'message': f'🔍 Starting comprehensive analysis for: {topic}'
        })
        
        results = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'form_data': form_data,
            'analysis_stages': {}
        }
        
        # Stage 1: Intent Analysis
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'intent_analysis',
            'message': '🎯 Analyzing search intent and user journey...'
        })
        
        if 'intent_classifier' in self.agents:
            intent_data = self.agents['intent_classifier'].classify_intent(
                topic, form_data.get('target_audience', '')
            )
            results['analysis_stages']['intent'] = intent_data
            
            await manager.send_message(session_id, {
                'type': 'stage_complete',
                'stage': 'intent_analysis',
                'data': intent_data
            })
        
        # Stage 2: Reddit Research (Real-time updates)
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'reddit_research',
            'message': '📱 Discovering relevant subreddits and scraping real posts...'
        })
        
        if 'reddit_research' in self.agents:
            # Get relevant subreddits first
            subreddits = self.agents['reddit_research'].discover_relevant_subreddits(topic)
            
            await manager.send_message(session_id, {
                'type': 'reddit_subreddits',
                'subreddits': subreddits
            })
            
            # Research with progress updates
            reddit_insights = await self._reddit_research_with_updates(topic, subreddits, session_id)
            results['analysis_stages']['reddit_insights'] = reddit_insights
            
            # Update live metrics
            pain_points_count = len(reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {}))
            self.sessions[session_id]['live_metrics']['pain_points_count'] = pain_points_count
            
            await manager.send_message(session_id, {
                'type': 'metrics_update',
                'metrics': self.sessions[session_id]['live_metrics']
            })
        
        # Stage 3: Content Generation with streaming
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'content_generation',
            'message': '✍️ Generating optimized content...'
        })
        
        if 'content_generator' in self.agents:
            generated_content = await self._generate_content_streaming(
                form_data, results['analysis_stages'], session_id
            )
            results['generated_content'] = generated_content
            self.sessions[session_id]['current_content'] = generated_content
        
        # Stage 4: E-E-A-T Assessment
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'eeat_assessment',
            'message': '🔒 Analyzing expertise, experience, authoritativeness, and trust...'
        })
        
        if 'eeat_assessor' in self.agents:
            eeat_assessment = self.agents['eeat_assessor'].assess_comprehensive_eeat(
                content=results.get('generated_content', ''),
                topic=topic,
                industry=form_data.get('industry', ''),
                business_context=form_data,
                author_info=form_data.get('author_credentials', ''),
                target_audience=form_data.get('target_audience', '')
            )
            results['analysis_stages']['eeat_assessment'] = eeat_assessment
            
            # Update trust score
            trust_score = eeat_assessment.get('overall_trust_score', 8.0)
            self.sessions[session_id]['live_metrics']['trust_score'] = trust_score
        
        # Stage 5: Quality Assessment
        if 'quality_scorer' in self.agents:
            quality_score = self.agents['quality_scorer'].score_content_quality(
                content=results.get('generated_content', ''),
                topic=topic,
                target_audience=form_data.get('target_audience', ''),
                business_context=form_data,
                reddit_insights=results['analysis_stages'].get('reddit_insights', {})
            )
            results['analysis_stages']['quality_assessment'] = quality_score
            
            # Update quality score
            q_score = quality_score.get('overall_score', 8.0)
            self.sessions[session_id]['live_metrics']['quality_score'] = q_score
        
        # Calculate final metrics
        metrics = self._calculate_live_metrics(results)
        self.sessions[session_id]['live_metrics'].update(metrics)
        self.sessions[session_id]['analysis_results'] = results
        
        # Send completion
        await manager.send_message(session_id, {
            'type': 'analysis_complete',
            'metrics': self.sessions[session_id]['live_metrics'],
            'message': '✅ Analysis complete! Chat interface is now active.'
        })
        
        return results
    
    async def _reddit_research_with_updates(self, topic: str, subreddits: List[str], session_id: str):
        """Reddit research with real-time progress updates"""
        
        for subreddit in subreddits:
            await manager.send_message(session_id, {
                'type': 'reddit_progress',
                'message': f'🔍 Scraping r/{subreddit}...',
                'subreddit': subreddit
            })
            
            # Simulate some delay for real effect
            await asyncio.sleep(0.5)
        
        # Perform actual research
        reddit_insights = await self.agents['reddit_research'].research_topic_comprehensive(
            topic=topic,
            subreddits=subreddits,
            max_posts_per_subreddit=20
        )
        
        await manager.send_message(session_id, {
            'type': 'reddit_complete',
            'total_posts': reddit_insights.get('research_metadata', {}).get('total_posts_analyzed', 0),
            'pain_points': len(reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {}))
        })
        
        return reddit_insights
    
    async def _generate_content_streaming(self, form_data: Dict, analysis_stages: Dict, session_id: str) -> str:
        """Generate content with streaming output"""
        
        await manager.send_message(session_id, {
            'type': 'content_stream_start'
        })
        
        # Build generation prompt
        reddit_insights = analysis_stages.get('reddit_insights', {})
        pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
        customer_quotes = reddit_insights.get('customer_voice', {}).get('authentic_quotes', [])
        
        prompt = f"""Create comprehensive content for: {form_data['topic']}

Target Audience: {form_data.get('target_audience', '')}
Industry: {form_data.get('industry', '')}
Language: {form_data.get('language', 'British English')}

Key Pain Points to Address:
{json.dumps(pain_points, indent=2)}

Customer Voice:
{chr(10).join(['- "' + quote + '"' for quote in customer_quotes[:5]])}

Unique Value Proposition:
{form_data.get('unique_value_prop', '')}

Create comprehensive, helpful content that directly addresses these real customer pain points."""
        
        content_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=4000):
            content_chunks.append(chunk)
            await manager.send_message(session_id, {
                'type': 'content_stream_chunk',
                'chunk': chunk
            })
        
        complete_content = ''.join(content_chunks)
        
        await manager.send_message(session_id, {
            'type': 'content_stream_complete',
            'content': complete_content
        })
        
        return complete_content
    
    def _calculate_live_metrics(self, results: Dict) -> Dict:
        """Calculate comprehensive live metrics"""
        eeat = results['analysis_stages'].get('eeat_assessment', {})
        quality = results['analysis_stages'].get('quality_assessment', {})
        reddit = results['analysis_stages'].get('reddit_insights', {})
        
        trust_score = eeat.get('overall_trust_score', 8.0)
        quality_score = quality.get('overall_score', 8.0)
        overall_score = (trust_score + quality_score) / 2
        
        return {
            'overall_score': round(overall_score, 1),
            'trust_score': round(trust_score, 1),
            'quality_score': round(quality_score, 1),
            'content_word_count': len(results.get('generated_content', '').split()),
            'improvement_potential': round(10.0 - overall_score, 1)
        }
    
    async def process_chat_message(self, session_id: str, message: str):
        """Process chat message with real-time updates"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        if 'streaming_chat' in self.agents:
            # Process with streaming response
            await self.agents['streaming_chat'].process_message(message, session, manager)
            
            # Check if metrics should be updated
            if any(word in message.lower() for word in ['apply', 'implement', 'update', 'improve']):
                # Simulate improvement application
                session['live_metrics']['improvements_applied'] += 1
                session['live_metrics']['overall_score'] = min(10.0, session['live_metrics']['overall_score'] + 0.2)
                session['live_metrics']['trust_score'] = min(10.0, session['live_metrics']['trust_score'] + 0.1)
                session['live_metrics']['quality_score'] = min(10.0, session['live_metrics']['quality_score'] + 0.1)
                
                await manager.send_message(session_id, {
                    'type': 'metrics_update',
                    'metrics': session['live_metrics']
                })
        
        return {"status": "processed"}

# Initialize the system
zee_system = ZeeSEOStreamingSystem()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced homepage"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool v5.0 - Real-Time Streaming System</title>
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
                max-width: 900px;
                padding: 4rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2rem;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .title {
                font-size: 4rem;
                font-weight: 900;
                margin-bottom: 1rem;
                background: linear-gradient(45deg, #fff, #f0f8ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 1.5rem;
                margin-bottom: 2rem;
                opacity: 0.95;
            }
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
                text-align: left;
            }
            .feature {
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .feature h3 {
                font-size: 1.1rem;
                margin-bottom: 0.5rem;
            }
            .feature p {
                font-size: 0.9rem;
                opacity: 0.9;
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
                margin-top: 2rem;
            }
            .cta-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }
            .agent-status {
                margin-top: 2rem;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 0.5rem;
                font-size: 0.85rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title">🚀 Zee SEO Tool v5.0</h1>
            <p class="subtitle">Real-Time Streaming AI Content Analysis & Generation</p>
            
            <div class="features-grid">
                <div class="feature">
                    <h3>🔴 Live Reddit Scraping</h3>
                    <p>Watch real-time as we scrape actual Reddit posts and extract genuine customer pain points</p>
                </div>
                <div class="feature">
                    <h3>💬 Claude-Style Streaming Chat</h3>
                    <p>Character-by-character streaming responses with intelligent content modification</p>
                </div>
                <div class="feature">
                    <h3>📊 Real-Time Metrics</h3>
                    <p>Trust scores, quality metrics, and pain points update live as you chat and improve content</p>
                </div>
                <div class="feature">
                    <h3>🎯 All Agents Integrated</h3>
                    <p>AdvancedTopicResearch, E-E-A-T Assessment, Quality Scoring, and more working together</p>
                </div>
                <div class="feature">
                    <h3>⚡ WebSocket Technology</h3>
                    <p>Instant updates, live progress tracking, and seamless real-time communication</p>
                </div>
                <div class="feature">
                    <h3>🔧 Professional Interface</h3>
                    <p>Modern, responsive design with live updates and professional data visualization</p>
                </div>
            </div>
            
            <a href="/app" class="cta-button">
                🎬 Start Live Analysis
            </a>
            
            <div class="agent-status">
                <strong>🤖 Active Agents:</strong> AdvancedTopicResearch • EnhancedRedditResearcher • StreamingChat • E-E-A-T Assessor • QualityScorer • ContentGenerator • IntentClassifier • BusinessContext • KnowledgeGraphTrends • JourneyMapper
            </div>
        </div>
    </body>
    </html>
    """)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data['type'] == 'chat_message':
                await zee_system.process_chat_message(session_id, message_data['message'])
            elif message_data['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@app.get("/app", response_class=HTMLResponse)
async def streaming_app_interface():
    """Real-time streaming application interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Live Analysis - Zee SEO Tool v5.0</title>
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
                position: sticky;
                top: 0;
                z-index: 100;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .header-content {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header-title {
                font-size: 1.5rem;
                font-weight: 700;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
                display: grid;
                grid-template-columns: 400px 1fr 350px;
                gap: 2rem;
                min-height: calc(100vh - 100px);
            }
            
            .form-panel {
                background: white;
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
                height: fit-content;
                position: sticky;
                top: 120px;
            }
            
            .main-area {
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }
            
            .metrics-panel {
                background: white;
                border-radius: 1rem;
                padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
                position: sticky;
                top: 120px;
                height: fit-content;
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
                padding: 0.75rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }
            
            .input:focus, .textarea:focus, .select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .textarea {
                resize: vertical;
                min-height: 80px;
            }
            
            .submit-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2rem;
                border: none;
                border-radius: 0.75rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
            }
            
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            }
            
            .submit-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .live-updates {
                background: white;
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
                min-height: 600px;
            }
            
            .update-item {
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #667eea;
                background: #f8fafc;
                font-size: 0.9rem;
            }
            
            .update-item.completed {
                border-left-color: #10b981;
                background: #f0fff4;
            }
            
            .update-item.error {
                border-left-color: #ef4444;
                background: #fef2f2;
            }
            
            .metric {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                margin-bottom: 1rem;
                background: #f8fafc;
                border-radius: 0.5rem;
                border: 1px solid #e2e8f0;
            }
            
            .metric-label {
                font-weight: 600;
                color: #4a5568;
            }
            
            .metric-value {
                font-size: 1.2rem;
                font-weight: 700;
                color: #667eea;
            }
            
            .chat-container {
                background: white;
                border-radius: 1rem;
                border: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                height: 400px;
                margin-top: 1rem;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem;
                border-radius: 1rem 1rem 0 0;
                font-weight: 600;
            }
            
            .chat-content {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
                background: #fafbfc;
            }
            
            .chat-input {
                padding: 1rem;
                border-top: 1px solid #e2e8f0;
                display: flex;
                gap: 0.5rem;
                background: white;
                border-radius: 0 0 1rem 1rem;
            }
            
            .chat-input input {
                flex: 1;
                padding: 0.75rem;
                border: 1px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 0.9rem;
            }
            
            .chat-input button {
                padding: 0.75rem 1rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 0.5rem;
                font-weight: 600;
                cursor: pointer;
            }
            
            .message {
                margin-bottom: 1rem;
                padding: 0.75rem;
                border-radius: 0.5rem;
                font-size: 0.85rem;
                line-height: 1.5;
            }
            
            .message.user {
                background: #667eea;
                color: white;
                margin-left: 2rem;
            }
            
            .message.assistant {
                background: #f0fff4;
                border: 1px solid #86efac;
                color: #065f46;
            }
            
            .streaming-text {
                white-space: pre-wrap;
                font-family: inherit;
            }
            
            .status-indicator {
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.8rem;
                font-weight: 600;
                text-align: center;
                margin-bottom: 1rem;
            }
            
            .status-indicator.analyzing {
                background: #fef3c7;
                color: #92400e;
            }
            
            .status-indicator.ready {
                background: #d1fae5;
                color: #065f46;
            }
            
            @media (max-width: 1200px) {
                .container {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="header-title">🔴 Live Analysis Dashboard</div>
                <div>Status: <span id="connectionStatus">Connecting...</span></div>
            </div>
        </div>
        
        <div class="container">
            <!-- Form Panel -->
            <div class="form-panel">
                <h3 style="margin-bottom: 1.5rem; color: #2d3748;">🎯 Analysis Configuration</h3>
                <form id="analysisForm">
                    <div class="form-group">
                        <label class="label">Topic *</label>
                        <input class="input" type="text" name="topic" 
                               placeholder="e.g., best budget laptops for students" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Target Audience</label>
                        <input class="input" type="text" name="target_audience" 
                               placeholder="e.g., university students aged 18-24">
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Industry</label>
                        <select class="select" name="industry">
                            <option value="Technology">Technology</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Education">Education</option>
                            <option value="Finance">Finance</option>
                            <option value="Marketing">Marketing</option>
                            <option value="E-commerce">E-commerce</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Your Expertise</label>
                        <textarea class="textarea" name="unique_value_prop" 
                                  placeholder="What makes you uniquely qualified to write about this topic?"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Customer Pain Points</label>
                        <textarea class="textarea" name="customer_pain_points" 
                                  placeholder="What problems do your customers face?"></textarea>
                    </div>
                    
                    <button type="submit" class="submit-btn" id="submitBtn">
                        🚀 Start Live Analysis
                    </button>
                </form>
            </div>
            
            <!-- Main Analysis Area -->
            <div class="main-area">
                <div class="live-updates">
                    <h3 style="margin-bottom: 1rem; color: #2d3748;">📊 Live Analysis Progress</h3>
                    <div id="statusIndicator" class="status-indicator analyzing" style="display: none;">
                        🔍 Analysis in progress...
                    </div>
                    <div id="updatesContainer">
                        <div class="update-item">
                            💡 Ready to start analysis. Fill in the form and click "Start Live Analysis"
                        </div>
                    </div>
                </div>
                
                <!-- Chat Interface -->
                <div class="chat-container" id="chatContainer" style="display: none;">
                    <div class="chat-header">
                        🤖 AI Content Assistant - Real-Time Chat
                    </div>
                    <div class="chat-content" id="chatContent">
                        <div class="message assistant">
                            <strong>AI Assistant:</strong> Analysis complete! I can now help you improve your content in real-time. Try asking:<br>
                            • "Make the content more beginner-friendly"<br>
                            • "Add more specific examples"<br>
                            • "Improve the trust score"<br>
                            • "Address the top pain points better"
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chatInput" placeholder="Ask me to improve the content..." />
                        <button onclick="sendChatMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Metrics Panel -->
            <div class="metrics-panel">
                <h3 style="margin-bottom: 1rem; color: #2d3748;">📈 Live Metrics</h3>
                
                <div class="metric">
                    <span class="metric-label">Overall Score</span>
                    <span class="metric-value" id="overallScore">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Trust Score</span>
                    <span class="metric-value" id="trustScore">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Quality Score</span>
                    <span class="metric-value" id="qualityScore">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Pain Points</span>
                    <span class="metric-value" id="painPointsCount">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Word Count</span>
                    <span class="metric-value" id="wordCount">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Improvements</span>
                    <span class="metric-value" id="improvementsCount">0</span>
                </div>
                
                <div style="margin-top: 1.5rem; padding: 1rem; background: #f0fff4; border-radius: 0.5rem; border: 1px solid #86efac;">
                    <div style="font-weight: 600; color: #065f46; margin-bottom: 0.5rem;">🎯 Improvement Potential</div>
                    <div style="font-size: 0.85rem; color: #047857;" id="improvementPotential">Analysis needed</div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let sessionId = 'session_' + Date.now();
            let analysisComplete = false;
            
            // Initialize WebSocket connection
            function initWebSocket() {
                ws = new WebSocket(`ws://localhost:8002/ws/${sessionId}`);
                
                ws.onopen = function() {
                    document.getElementById('connectionStatus').textContent = 'Connected';
                    document.getElementById('connectionStatus').style.color = '#10b981';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function() {
                    document.getElementById('connectionStatus').textContent = 'Disconnected';
                    document.getElementById('connectionStatus').style.color = '#ef4444';
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function handleWebSocketMessage(data) {
                const updatesContainer = document.getElementById('updatesContainer');
                
                switch(data.type) {
                    case 'analysis_start':
                        addUpdateItem(data.message, 'analyzing');
                        document.getElementById('statusIndicator').style.display = 'block';
                        document.getElementById('submitBtn').disabled = true;
                        break;
                        
                    case 'stage_update':
                        addUpdateItem(data.message, 'analyzing');
                        break;
                        
                    case 'reddit_subreddits':
                        addUpdateItem(`🎯 Found relevant subreddits: ${data.subreddits.join(', ')}`, 'analyzing');
                        break;
                        
                    case 'reddit_progress':
                        addUpdateItem(data.message, 'analyzing');
                        break;
                        
                    case 'reddit_complete':
                        addUpdateItem(`✅ Reddit analysis complete: ${data.total_posts} posts, ${data.pain_points} pain points identified`, 'completed');
                        break;
                        
                    case 'content_stream_start':
                        addUpdateItem('✍️ Generating content...', 'analyzing');
                        break;
                        
                    case 'content_stream_chunk':
                        // Handle streaming content display
                        break;
                        
                    case 'content_stream_complete':
                        addUpdateItem('✅ Content generation complete', 'completed');
                        break;
                        
                    case 'metrics_update':
                        updateMetrics(data.metrics);
                        break;
                        
                    case 'analysis_complete':
                        addUpdateItem(data.message, 'completed');
                        document.getElementById('statusIndicator').style.display = 'none';
                        document.getElementById('chatContainer').style.display = 'flex';
                        analysisComplete = true;
                        updateMetrics(data.metrics);
                        break;
                        
                    case 'assistant_stream':
                        appendToChatStream(data.chunk);
                        break;
                        
                    case 'assistant_start':
                        startAssistantMessage();
                        break;
                        
                    case 'assistant_complete':
                        completeAssistantMessage();
                        break;
                }
            }
            
            function addUpdateItem(message, type = 'analyzing') {
                const updatesContainer = document.getElementById('updatesContainer');
                const updateItem = document.createElement('div');
                updateItem.className = `update-item ${type}`;
                updateItem.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}`;
                updatesContainer.appendChild(updateItem);
                updatesContainer.scrollTop = updatesContainer.scrollHeight;
            }
            
            function updateMetrics(metrics) {
                document.getElementById('overallScore').textContent = metrics.overall_score || '--';
                document.getElementById('trustScore').textContent = metrics.trust_score || '--';
                document.getElementById('qualityScore').textContent = metrics.quality_score || '--';
                document.getElementById('painPointsCount').textContent = metrics.pain_points_count || '--';
                document.getElementById('wordCount').textContent = metrics.content_word_count || '--';
                document.getElementById('improvementsCount').textContent = metrics.improvements_applied || '0';
                
                const potential = metrics.improvement_potential || 0;
                document.getElementById('improvementPotential').textContent = 
                    potential > 0 ? `+${potential} points available` : 'Optimized';
            }
            
            let currentAssistantMessage = null;
            
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
            
            function sendChatMessage() {
                const chatInput = document.getElementById('chatInput');
                const message = chatInput.value.trim();
                
                if (!message || !analysisComplete) return;
                
                // Add user message
                const chatContent = document.getElementById('chatContent');
                const userMessage = document.createElement('div');
                userMessage.className = 'message user';
                userMessage.innerHTML = `<strong>You:</strong> ${message}`;
                chatContent.appendChild(userMessage);
                
                // Send via WebSocket
                ws.send(JSON.stringify({
                    type: 'chat_message',
                    message: message
                }));
                
                chatInput.value = '';
                chatContent.scrollTop = chatContent.scrollHeight;
            }
            
            // Form submission
            document.getElementById('analysisForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    const response = await fetch('/analyze-streaming', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ...data, session_id: sessionId })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    
                } catch (error) {
                    addUpdateItem(`❌ Error: ${error.message}`, 'error');
                    document.getElementById('submitBtn').disabled = false;
                }
            });
            
            // Chat input enter key
            document.getElementById('chatInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendChatMessage();
                }
            });
            
            // Initialize on page load
            window.onload = function() {
                initWebSocket();
            };
        </script>
    </body>
    </html>
    """)

@app.post("/analyze-streaming")
async def analyze_streaming_endpoint(request: Request):
    """Start streaming analysis"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        
        # Start analysis in background
        asyncio.create_task(
            zee_system.analyze_comprehensive_streaming(data, session_id)
        )
        
        return JSONResponse({"status": "started", "session_id": session_id})
        
    except Exception as e:
        logger.error(f"Streaming analysis error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/debug/agents")
async def debug_agents():
    """Debug endpoint showing all agent status"""
    agent_status = {}
    
    for agent_name, agent in zee_system.agents.items():
        agent_status[agent_name] = {
            "status": "✅ Active",
            "type": str(type(agent).__name__),
            "module": str(type(agent).__module__)
        }
    
    return JSONResponse({
        "active_agents": agent_status,
        "total_agents": len(zee_system.agents),
        "websocket_manager": "✅ Active",
        "streaming_client": "✅ Active" if zee_system.llm_client.anthropic_client else "🔄 Fallback"
    })

if __name__ == "__main__":
    print("🚀 Starting Zee SEO Tool v5.0 - Real-Time Streaming System...")
    print("=" * 80)
    
    agent_count = len(zee_system.agents)
    print(f"📊 System Status:")
    print(f"   • Total Active Agents: {agent_count}")
    print(f"   • WebSocket Manager: ✅ Ready")
    print(f"   • Streaming LLM: {'✅ Ready' if zee_system.llm_client.anthropic_client else '🔄 Fallback'}")
    print()
    
    print("🎯 Active Agents:")
    for agent_name in zee_system.agents.keys():
        print(f"   • {agent_name}")
    
    print("=" * 80)
    print(f"🌟 Access the application at: http://localhost:{config.PORT}/")
    print(f"🔧 Debug agents at: http://localhost:{config.PORT}/debug/agents")
    print("=" * 80)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=config.PORT)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
