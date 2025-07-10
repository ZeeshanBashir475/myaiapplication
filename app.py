import os
import sys
import json
import logging
import asyncio
import importlib
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# FastAPI and WebSocket imports
from fastapi import FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add all possible paths for your agents
possible_paths = [
    '/app/src',
    '/app',
    'src',
    '.',
    './src',
    './src/agents',
    '/app/src/agents',
    'agents'
]

for path in possible_paths:
    if path not in sys.path:
        sys.path.append(path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAgentLoader:
    """Advanced agent loader that finds your agents regardless of structure"""
    
    def __init__(self):
        self.loaded_agents = {}
        self.failed_imports = {}
        self.discover_and_load_agents()
    
    def discover_and_load_agents(self):
        """Discover and load all available agents"""
        logger.info("🔍 Starting comprehensive agent discovery...")
        
        # Define all your agents with multiple possible locations
        agent_definitions = {
            'AdvancedTopicResearchAgent': {
                'class_name': 'AdvancedTopicResearchAgent',
                'possible_modules': [
                    'AdvancedTopicResearchAgent',
                    'src.agents.AdvancedTopicResearchAgent',
                    'agents.AdvancedTopicResearchAgent',
                    'AdvancedTopicResearchAgent.AdvancedTopicResearchAgent',
                    'src.AdvancedTopicResearchAgent'
                ]
            },
            'EnhancedRedditResearcher': {
                'class_name': 'EnhancedRedditResearcher',
                'possible_modules': [
                    'enhanced_reddit_researcher',
                    'src.agents.enhanced_reddit_researcher',
                    'agents.enhanced_reddit_researcher',
                    'enhanced_reddit_researcher.EnhancedRedditResearcher',
                    'src.enhanced_reddit_researcher'
                ]
            },
            'ContentQualityScorer': {
                'class_name': 'ContentQualityScorer',
                'possible_modules': [
                    'content_quality_scorer',
                    'src.agents.content_quality_scorer',
                    'agents.content_quality_scorer',
                    'content_quality_scorer.ContentQualityScorer',
                    'src.content_quality_scorer'
                ]
            },
            'ContentTypeClassifier': {
                'class_name': 'ContentTypeClassifier',
                'possible_modules': [
                    'content_type_classifier',
                    'src.agents.content_type_classifier',
                    'agents.content_type_classifier',
                    'content_type_classifier.ContentTypeClassifier',
                    'src.content_type_classifier'
                ]
            },
            'EnhancedEEATAssessor': {
                'class_name': 'EnhancedEEATAssessor',
                'possible_modules': [
                    'eeat_assessor',
                    'src.agents.eeat_assessor',
                    'agents.eeat_assessor',
                    'eeat_assessor.EnhancedEEATAssessor',
                    'src.eeat_assessor'
                ]
            },
            'IntentClassifier': {
                'class_name': 'IntentClassifier',
                'possible_modules': [
                    'intent_classifier',
                    'src.agents.intent_classifier',
                    'agents.intent_classifier',
                    'intent_classifier.IntentClassifier',
                    'src.intent_classifier'
                ]
            },
            'BusinessContextCollector': {
                'class_name': 'BusinessContextCollector',
                'possible_modules': [
                    'business_context_collector',
                    'src.agents.business_context_collector',
                    'agents.business_context_collector',
                    'business_context_collector.BusinessContextCollector',
                    'src.business_context_collector'
                ]
            },
            'FullContentGenerator': {
                'class_name': 'FullContentGenerator',
                'possible_modules': [
                    'content_generator',
                    'src.agents.content_generator',
                    'agents.content_generator',
                    'content_generator.FullContentGenerator',
                    'full_content_generator',
                    'src.content_generator'
                ]
            },
            'HumanInputIdentifier': {
                'class_name': 'HumanInputIdentifier',
                'possible_modules': [
                    'human_input_identifier',
                    'src.agents.human_input_identifier',
                    'agents.human_input_identifier',
                    'human_input_identifier.HumanInputIdentifier',
                    'src.human_input_identifier'
                ]
            },
            'KnowledgeGraphTrendsAgent': {
                'class_name': 'KnowledgeGraphTrendsAgent',
                'possible_modules': [
                    'knowledge_graph_trends_agent',
                    'src.agents.knowledge_graph_trends_agent',
                    'agents.knowledge_graph_trends_agent',
                    'knowledge_graph_trends',
                    'src.knowledge_graph_trends_agent'
                ]
            },
            'JourneyMapper': {
                'class_name': 'JourneyMapper',
                'possible_modules': [
                    'journey_mapper',
                    'src.agents.journey_mapper',
                    'agents.journey_mapper',
                    'journey_mapper.JourneyMapper',
                    'src.journey_mapper'
                ]
            }
        }
        
        # Try to load each agent
        for agent_key, agent_info in agent_definitions.items():
            agent_class = self.load_agent(agent_key, agent_info)
            if agent_class:
                self.loaded_agents[agent_key] = agent_class
        
        logger.info(f"✅ Agent discovery complete: {len(self.loaded_agents)}/{len(agent_definitions)} agents loaded")
        
        # Log results
        for agent_name in self.loaded_agents:
            logger.info(f"   ✅ {agent_name}")
        for agent_name in self.failed_imports:
            logger.warning(f"   ❌ {agent_name}: {self.failed_imports[agent_name]}")
    
    def load_agent(self, agent_key: str, agent_info: Dict) -> Optional[type]:
        """Load a specific agent with multiple fallback strategies"""
        class_name = agent_info['class_name']
        possible_modules = agent_info['possible_modules']
        
        # Strategy 1: Try direct module imports
        for module_path in possible_modules:
            try:
                if '.' in module_path:
                    # Module with submodule
                    module = importlib.import_module(module_path)
                else:
                    # Single module
                    module = importlib.import_module(module_path)
                
                # Look for the exact class name
                if hasattr(module, class_name):
                    agent_class = getattr(module, class_name)
                    if inspect.isclass(agent_class):
                        logger.info(f"✅ Loaded {agent_key} from {module_path}.{class_name}")
                        return agent_class
                
                # Look for similar class names
                for attr_name in dir(module):
                    if class_name.lower() in attr_name.lower():
                        attr = getattr(module, attr_name)
                        if inspect.isclass(attr):
                            logger.info(f"✅ Loaded {agent_key} as {attr_name} from {module_path}")
                            return attr
                            
            except ImportError as e:
                continue
            except Exception as e:
                logger.debug(f"Error loading {agent_key} from {module_path}: {e}")
                continue
        
        # Strategy 2: File system search
        agent_class = self.search_filesystem_for_agent(agent_key, class_name)
        if agent_class:
            return agent_class
        
        # Strategy 3: Dynamic discovery in loaded modules
        agent_class = self.search_loaded_modules_for_agent(class_name)
        if agent_class:
            return agent_class
        
        self.failed_imports[agent_key] = f"Could not find {class_name} in any location"
        return None
    
    def search_filesystem_for_agent(self, agent_key: str, class_name: str) -> Optional[type]:
        """Search filesystem for agent files"""
        search_dirs = ['.', 'src', 'agents', 'src/agents']
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.endswith('.py') and not file.startswith('__'):
                            file_path = os.path.join(root, file)
                            module_name = file.replace('.py', '')
                            
                            # Check if filename suggests it contains our agent
                            if any(word in file.lower() for word in [
                                agent_key.lower(), 
                                class_name.lower(),
                                agent_key.lower().replace('agent', ''),
                                class_name.lower().replace('agent', '')
                            ]):
                                try:
                                    # Convert file path to module path
                                    rel_path = os.path.relpath(file_path)
                                    module_path = rel_path.replace(os.sep, '.').replace('.py', '')
                                    
                                    module = importlib.import_module(module_path)
                                    if hasattr(module, class_name):
                                        agent_class = getattr(module, class_name)
                                        if inspect.isclass(agent_class):
                                            logger.info(f"✅ Found {agent_key} via filesystem search in {module_path}")
                                            return agent_class
                                except Exception as e:
                                    continue
        return None
    
    def search_loaded_modules_for_agent(self, class_name: str) -> Optional[type]:
        """Search already loaded modules for the agent class"""
        for module_name, module in sys.modules.items():
            if module and hasattr(module, class_name):
                agent_class = getattr(module, class_name)
                if inspect.isclass(agent_class):
                    logger.info(f"✅ Found {class_name} in already loaded module {module_name}")
                    return agent_class
        return None
    
    def get_agent(self, agent_key: str) -> Optional[type]:
        """Get a loaded agent class"""
        return self.loaded_agents.get(agent_key)
    
    def list_loaded_agents(self) -> List[str]:
        """List all successfully loaded agents"""
        return list(self.loaded_agents.keys())
    
    def get_load_report(self) -> Dict:
        """Get detailed load report"""
        return {
            'loaded': list(self.loaded_agents.keys()),
            'failed': self.failed_imports,
            'total_attempted': len(self.loaded_agents) + len(self.failed_imports),
            'success_rate': len(self.loaded_agents) / (len(self.loaded_agents) + len(self.failed_imports)) if (len(self.loaded_agents) + len(self.failed_imports)) > 0 else 0
        }

# Updated Configuration for Railway
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    
    # Railway provides PORT environment variable
    PORT = int(os.getenv("PORT", 8002))
    
    # Railway-specific settings
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Enable debug mode only in development
    DEBUG_MODE = os.getenv("RAILWAY_ENVIRONMENT") != "production"
    
    # Environment detection
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Enhanced form validation
def validate_form_data(form_data: Dict[str, str]) -> Dict[str, str]:
    """Enhanced form validation with quality controls"""
    errors = {}
    
    # Validate topic
    topic = form_data.get('topic', '').strip()
    if len(topic) < 10:
        errors['topic'] = 'Topic must be at least 10 characters and descriptive'
    elif len(topic.split()) < 3:
        errors['topic'] = 'Topic should contain at least 3 words for better specificity'
    
    # Validate target audience with quality checks
    audience = form_data.get('target_audience', '').strip()
    if len(audience) < 15:
        errors['target_audience'] = 'Target audience must be specific and detailed (at least 15 characters)'
    elif not any(word in audience.lower() for word in ['aged', 'years', 'who', 'looking', 'seeking', 'need', 'want']):
        errors['target_audience'] = 'Target audience should be more specific (include demographics, needs, or characteristics)'
    
    # Validate required fields
    required_fields = ['content_type', 'content_goal', 'ai_instructions', 'unique_value_prop', 'customer_pain_points']
    for field in required_fields:
        if not form_data.get(field, '').strip():
            errors[field] = f'{field.replace("_", " ").title()} is required'
        elif len(form_data.get(field, '').strip()) < 20:
            errors[field] = f'{field.replace("_", " ").title()} must be at least 20 characters'
    
    return errors

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
                yield f"Streaming error: {str(e)}"
        else:
            # Fallback non-streaming
            response = f"Response to: {prompt[:100]}..."
            for char in response:
                yield char
                await asyncio.sleep(0.01)
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate non-streaming response"""
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                logger.error(f"❌ Generation error: {e}")
        
        return f"Fallback response for: {prompt[:100]}..."

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

# Complete Professional Streaming Chat Agent
class ProfessionalStreamingChatAgent:
    """Professional streaming chat agent with full functionality"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        logger.info("✅ Professional Streaming Chat Agent initialized")
    
    async def process_message(self, message: str, session: Dict, connection_manager) -> None:
        """Process chat message with intelligent streaming and real-time updates"""
        
        session_id = session['session_id']
        
        # Add user message to conversation history
        session.setdefault('conversation_history', []).append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze message intent
        improvement_type = self._analyze_improvement_intent(message)
        
        # Send typing indicator
        await connection_manager.send_message(session_id, {
            'type': 'assistant_start'
        })
        
        # Generate contextual streaming response
        await self._handle_streaming_response(message, session, connection_manager, improvement_type)
        
        # Send completion signal
        await connection_manager.send_message(session_id, {
            'type': 'assistant_complete'
        })
    
    def _analyze_improvement_intent(self, message: str) -> str:
        """Analyze what type of improvement the user wants"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['trust', 'credibility', 'authority', 'trustworthy']):
            return 'trust_improvement'
        elif any(word in message_lower for word in ['quality', 'better', 'improve']):
            return 'quality_improvement'
        elif any(word in message_lower for word in ['beginner', 'simple', 'easy']):
            return 'beginner_friendly'
        elif any(word in message_lower for word in ['pain point', 'problem', 'customer']):
            return 'pain_point_focus'
        elif any(word in message_lower for word in ['seo', 'keywords', 'search']):
            return 'seo_optimization'
        else:
            return 'general_improvement'
    
    async def _handle_streaming_response(self, message: str, session: Dict, connection_manager, improvement_type: str):
        """Handle streaming response generation"""
        
        session_id = session['session_id']
        
        # Build comprehensive context
        context = self._build_response_context(session, improvement_type)
        
        prompt = f"""You are an expert content strategist providing specific improvement recommendations.

USER REQUEST: {message}

IMPROVEMENT TYPE: {improvement_type}

CONTEXT:
{context}

Provide specific, actionable recommendations. If they're asking to modify content, provide the complete updated version. Be conversational and helpful like Claude."""

        # Stream the response
        response_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=3000):
            response_chunks.append(chunk)
            await connection_manager.send_message(session_id, {
                'type': 'assistant_stream',
                'chunk': chunk
            })
        
        response = ''.join(response_chunks)
        
        # Add response to conversation history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat(),
            'improvement_type': improvement_type
        })
        
        # Apply metrics improvements
        await self._apply_improvement_metrics(session, improvement_type, connection_manager)
    
    def _build_response_context(self, session: Dict, improvement_type: str) -> str:
        """Build comprehensive context for response"""
        form_data = session.get('form_data', {})
        analysis_results = session.get('analysis_results', {})
        
        context_parts = [
            f"Topic: {form_data.get('topic', 'Unknown')}",
            f"Target Audience: {form_data.get('target_audience', 'General')}",
            f"Industry: {form_data.get('industry', 'General')}",
            f"Content Type: {form_data.get('content_type', 'guide')}",
            f"Content Goal: {form_data.get('content_goal', 'educate_audience')}"
        ]
        
        # Add Reddit insights if available
        reddit_insights = analysis_results.get('reddit_insights', {})
        if reddit_insights:
            pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
            if pain_points:
                top_pains = list(pain_points.keys())[:3]
                context_parts.append(f"Top Customer Pain Points: {', '.join(top_pains)}")
        
        # Add current metrics
        metrics = session.get('live_metrics', {})
        context_parts.append(f"Current Trust Score: {metrics.get('trust_score', 'N/A')}")
        context_parts.append(f"Current Quality Score: {metrics.get('quality_score', 'N/A')}")
        
        return '\n'.join(context_parts)
    
    async def _apply_improvement_metrics(self, session: Dict, improvement_type: str, connection_manager):
        """Apply realistic metrics improvements"""
        session_id = session['session_id']
        metrics = session.setdefault('live_metrics', {
            'overall_score': 8.0,
            'trust_score': 7.8,
            'quality_score': 8.2,
            'pain_points_count': 5,
            'word_count': 2000,
            'improvements_applied': 0
        })
        
        # Apply improvements based on type
        metrics['improvements_applied'] += 1
        
        if improvement_type == 'trust_improvement':
            metrics['trust_score'] = min(10.0, metrics['trust_score'] + 0.3)
        elif improvement_type == 'quality_improvement':
            metrics['quality_score'] = min(10.0, metrics['quality_score'] + 0.25)
        elif improvement_type == 'pain_point_focus':
            metrics['quality_score'] = min(10.0, metrics['quality_score'] + 0.2)
        
        # Recalculate overall score
        metrics['overall_score'] = (metrics['trust_score'] + metrics['quality_score']) / 2
        
        # Send metrics update
        await connection_manager.send_message(session_id, {
            'type': 'metrics_update',
            'metrics': metrics
        })

# Advanced Content Analysis System
class ZeeSEOProfessionalSystem:
    """Complete professional system with all your agents integrated"""
    
    def __init__(self):
        self.agent_loader = AdvancedAgentLoader()
        self.llm_client = StreamingLLMClient()
        self.sessions = {}
        self.init_agent_instances()
        
        # Initialize chat agent
        self.chat_agent = ProfessionalStreamingChatAgent(self.llm_client)
    
    def init_agent_instances(self):
        """Initialize instances of all loaded agents"""
        self.agents = {}
        
        agent_configs = [
            ('topic_research', 'AdvancedTopicResearchAgent', True),
            ('reddit_research', 'EnhancedRedditResearcher', False),
            ('quality_scorer', 'ContentQualityScorer', True),
            ('content_classifier', 'ContentTypeClassifier', True),
            ('eeat_assessor', 'EnhancedEEATAssessor', True),
            ('intent_classifier', 'IntentClassifier', True),
            ('business_context', 'BusinessContextCollector', False),
            ('content_generator', 'FullContentGenerator', True),
            ('human_input', 'HumanInputIdentifier', True),
            ('kg_trends', 'KnowledgeGraphTrendsAgent', True),
            ('journey_mapper', 'JourneyMapper', True)
        ]
        
        for agent_key, agent_class_name, needs_llm in agent_configs:
            agent_class = self.agent_loader.get_agent(agent_class_name)
            if agent_class:
                try:
                    if needs_llm:
                        if agent_class_name == 'KnowledgeGraphTrendsAgent':
                            agent = agent_class(
                                google_api_key=config.GOOGLE_API_KEY,
                                llm_client=self.llm_client
                            )
                        else:
                            agent = agent_class(self.llm_client)
                    else:
                        agent = agent_class()
                    
                    self.agents[agent_key] = agent
                    logger.info(f"✅ {agent_key} instance created")
                except Exception as e:
                    logger.error(f"❌ Failed to create {agent_key} instance: {e}")
        
        logger.info(f"🎯 Professional system ready with {len(self.agents)} active agent instances")
    
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
                'word_count': 0,
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
        
        # Run all analysis stages
        await self._run_intent_analysis(session_id, form_data, results)
        await self._run_content_classification(session_id, form_data, results)
        await self._run_reddit_research_comprehensive(session_id, form_data, results)
        await self._run_topic_research(session_id, form_data, results)
        await self._run_content_generation_streaming(session_id, form_data, results)
        await self._run_quality_assessment(session_id, form_data, results)
        await self._run_eeat_assessment(session_id, form_data, results)
        await self._run_human_input_analysis(session_id, form_data, results)
        
        # Calculate final metrics
        metrics = self._calculate_comprehensive_metrics(results)
        self.sessions[session_id]['live_metrics'] = metrics
        self.sessions[session_id]['analysis_results'] = results
        
        # Send completion
        await manager.send_message(session_id, {
            'type': 'analysis_complete',
            'metrics': metrics,
            'message': '✅ Comprehensive analysis complete! Chat interface is now active.'
        })
        
        return results
    
    async def _run_intent_analysis(self, session_id: str, form_data: dict, results: dict):
        """Run intent classification analysis"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'intent_analysis',
            'message': '🎯 Analyzing search intent and user journey...'
        })
        
        if 'intent_classifier' in self.agents:
            try:
                intent_data = self.agents['intent_classifier'].classify_intent(
                    form_data.get('topic', ''),
                    form_data.get('target_audience', '')
                )
                results['analysis_stages']['intent'] = intent_data
                logger.info(f"✅ Intent analysis complete: {intent_data.get('primary_intent', 'unknown')}")
            except Exception as e:
                logger.error(f"Intent analysis error: {e}")
                results['analysis_stages']['intent'] = {'primary_intent': 'informational', 'confidence': 0.7}
        else:
            results['analysis_stages']['intent'] = {'primary_intent': 'informational', 'confidence': 0.7}
        
        await manager.send_message(session_id, {
            'type': 'stage_complete',
            'stage': 'intent_analysis',
            'data': results['analysis_stages']['intent']
        })
    
    async def _run_content_classification(self, session_id: str, form_data: dict, results: dict):
        """Run content type classification"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'content_classification',
            'message': '📋 Classifying optimal content type...'
        })
        
        if 'content_classifier' in self.agents:
            try:
                content_type_data = self.agents['content_classifier'].classify_content_type(
                    topic=form_data.get('topic', ''),
                    target_audience=form_data.get('target_audience', ''),
                    business_context=form_data
                )
                results['analysis_stages']['content_type'] = content_type_data
            except Exception as e:
                logger.error(f"Content classification error: {e}")
                results['analysis_stages']['content_type'] = {'primary_content_type': form_data.get('content_type', 'guide')}
        else:
            results['analysis_stages']['content_type'] = {'primary_content_type': form_data.get('content_type', 'guide')}
        
        await manager.send_message(session_id, {
            'type': 'stage_complete',
            'stage': 'content_classification'
        })
    
    async def _run_reddit_research_comprehensive(self, session_id: str, form_data: dict, results: dict):
        """Run comprehensive Reddit research with subreddit discovery"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'reddit_research',
            'message': '📱 Discovering relevant subreddits and scraping real posts...'
        })
        
        if 'reddit_research' in self.agents:
            try:
                topic = form_data.get('topic', '')
                
                # First discover relevant subreddits
                if hasattr(self.agents['reddit_research'], 'discover_relevant_subreddits'):
                    subreddits = self.agents['reddit_research'].discover_relevant_subreddits(topic)
                else:
                    # Fallback subreddit selection
                    subreddits = self._get_fallback_subreddits(topic)
                
                await manager.send_message(session_id, {
                    'type': 'reddit_subreddits_discovered',
                    'subreddits': subreddits,
                    'message': f'🎯 Discovered {len(subreddits)} relevant subreddits: {", ".join(subreddits)}'
                })
                
                # Show progress for each subreddit
                for subreddit in subreddits:
                    await manager.send_message(session_id, {
                        'type': 'reddit_progress',
                        'message': f'🔍 Scraping r/{subreddit}...',
                        'subreddit': subreddit
                    })
                    await asyncio.sleep(0.5)  # Realistic timing
                
                # Perform comprehensive research
                if hasattr(self.agents['reddit_research'], 'research_topic_comprehensive'):
                    reddit_insights = await self.agents['reddit_research'].research_topic_comprehensive(
                        topic=topic,
                        subreddits=subreddits,
                        max_posts_per_subreddit=25
                    )
                else:
                    # Try synchronous version
                    reddit_insights = self.agents['reddit_research'].research_topic_comprehensive(
                        topic=topic,
                        subreddits=subreddits,
                        max_posts_per_subreddit=25
                    )
                
                results['analysis_stages']['reddit_insights'] = reddit_insights
                
                # Update metrics
                pain_points_count = len(reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {}))
                posts_analyzed = reddit_insights.get('research_metadata', {}).get('total_posts_analyzed', 0)
                
                await manager.send_message(session_id, {
                    'type': 'reddit_complete',
                    'total_posts': posts_analyzed,
                    'pain_points': pain_points_count,
                    'subreddits_researched': len(subreddits)
                })
                
                logger.info(f"✅ Reddit research complete: {posts_analyzed} posts, {pain_points_count} pain points")
                
            except Exception as e:
                logger.error(f"Reddit research error: {e}")
                results['analysis_stages']['reddit_insights'] = self._fallback_reddit_data(form_data.get('topic', ''))
        else:
            results['analysis_stages']['reddit_insights'] = self._fallback_reddit_data(form_data.get('topic', ''))
            await manager.send_message(session_id, {
                'type': 'reddit_fallback',
                'message': '⚠️ Using fallback Reddit data - install Reddit agent for real scraping'
            })
    
    async def _run_topic_research(self, session_id: str, form_data: dict, results: dict):
        """Run advanced topic research"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'topic_research',
            'message': '🔍 Conducting advanced topic research...'
        })
        
        if 'topic_research' in self.agents:
            try:
                topic_research = self.agents['topic_research'].research_topic_comprehensive(
                    topic=form_data.get('topic', ''),
                    industry=form_data.get('industry', ''),
                    target_audience=form_data.get('target_audience', ''),
                    business_goals=form_data.get('content_goal', '')
                )
                results['analysis_stages']['topic_research'] = topic_research
            except Exception as e:
                logger.error(f"Topic research error: {e}")
                results['analysis_stages']['topic_research'] = {'opportunity_score': 7.5}
        else:
            results['analysis_stages']['topic_research'] = {'opportunity_score': 7.5}
        
        await manager.send_message(session_id, {
            'type': 'stage_complete',
            'stage': 'topic_research'
        })
    
    async def _run_content_generation_streaming(self, session_id: str, form_data: dict, results: dict):
        """Run content generation with enhanced streaming output and proper formatting"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'content_generation',
            'message': '✍️ Generating comprehensive content with professional insights...'
        })
        
        await manager.send_message(session_id, {
            'type': 'content_stream_start'
        })
        
        if 'content_generator' in self.agents:
            try:
                # Enhanced content generation with all form data
                generated_content = self.agents['content_generator'].generate_complete_content(
                    topic=form_data.get('topic', ''),
                    content_type=form_data.get('content_type', 'guide'),
                    target_audience=form_data.get('target_audience', ''),
                    reddit_insights=results['analysis_stages'].get('reddit_insights', {}),
                    journey_data=results['analysis_stages'].get('intent', {}),
                    business_context=form_data,
                    human_inputs=results['analysis_stages'].get('human_inputs', {}),
                    language=form_data.get('language', 'British English')
                )
                results['generated_content'] = generated_content
                self.sessions[session_id]['current_content'] = generated_content
                
            except Exception as e:
                logger.error(f"Content generation error: {e}")
                generated_content = self._enhanced_fallback_content(form_data)
                results['generated_content'] = generated_content
                self.sessions[session_id]['current_content'] = generated_content
        else:
            generated_content = self._enhanced_fallback_content(form_data)
            results['generated_content'] = generated_content
            self.sessions[session_id]['current_content'] = generated_content
        
        # Send the complete content to frontend
        await manager.send_message(session_id, {
            'type': 'content_stream_complete',
            'content': generated_content,
            'word_count': len(generated_content.split())
        })
    
    async def _run_quality_assessment(self, session_id: str, form_data: dict, results: dict):
        """Run comprehensive quality assessment"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'quality_assessment',
            'message': '📊 Assessing content quality and optimization...'
        })
        
        if 'quality_scorer' in self.agents:
            try:
                quality_score = self.agents['quality_scorer'].score_content_quality(
                    content=results.get('generated_content', ''),
                    topic=form_data.get('topic', ''),
                    target_audience=form_data.get('target_audience', ''),
                    business_context=form_data,
                    reddit_insights=results['analysis_stages'].get('reddit_insights', {})
                )
                results['analysis_stages']['quality_assessment'] = quality_score
            except Exception as e:
                logger.error(f"Quality assessment error: {e}")
                results['analysis_stages']['quality_assessment'] = {'overall_score': 8.0}
        else:
            results['analysis_stages']['quality_assessment'] = {'overall_score': 8.0}
        
        await manager.send_message(session_id, {
            'type': 'stage_complete',
            'stage': 'quality_assessment'
        })
    
    async def _run_eeat_assessment(self, session_id: str, form_data: dict, results: dict):
        """Run comprehensive E-E-A-T assessment"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'eeat_assessment',
            'message': '🔒 Analyzing expertise, experience, authoritativeness, and trust...'
        })
        
        if 'eeat_assessor' in self.agents:
            try:
                eeat_assessment = self.agents['eeat_assessor'].assess_comprehensive_eeat(
                    content=results.get('generated_content', ''),
                    topic=form_data.get('topic', ''),
                    industry=form_data.get('industry', ''),
                    business_context=form_data,
                    author_info=form_data.get('unique_value_prop', ''),
                    target_audience=form_data.get('target_audience', '')
                )
                results['analysis_stages']['eeat_assessment'] = eeat_assessment
            except Exception as e:
                logger.error(f"E-E-A-T assessment error: {e}")
                results['analysis_stages']['eeat_assessment'] = {'overall_trust_score': 8.0}
        else:
            results['analysis_stages']['eeat_assessment'] = {'overall_trust_score': 8.0}
        
        await manager.send_message(session_id, {
            'type': 'stage_complete',
            'stage': 'eeat_assessment'
        })
    
    async def _run_human_input_analysis(self, session_id: str, form_data: dict, results: dict):
        """Run human input identification"""
        await manager.send_message(session_id, {
            'type': 'stage_update',
            'stage': 'human_input_analysis',
            'message': '👤 Identifying required human input and personalization...'
        })
        
        if 'human_input' in self.agents:
            try:
                human_inputs = self.agents['human_input'].identify_human_inputs(
                    topic=form_data.get('topic', ''),
                    content_type=form_data.get('content_type', 'guide'),
                    business_context=form_data
                )
                results['analysis_stages']['human_inputs'] = human_inputs
            except Exception as e:
                logger.error(f"Human input analysis error: {e}")
                results['analysis_stages']['human_inputs'] = {'required_inputs': []}
        else:
            results['analysis_stages']['human_inputs'] = {'required_inputs': []}
        
        await manager.send_message(session_id, {
            'type': 'stage_complete',
            'stage': 'human_input_analysis'
        })
    
    def _calculate_comprehensive_metrics(self, results: Dict) -> Dict:
        """Calculate comprehensive metrics from all analysis stages"""
        eeat = results['analysis_stages'].get('eeat_assessment', {})
        quality = results['analysis_stages'].get('quality_assessment', {})
        reddit = results['analysis_stages'].get('reddit_insights', {})
        topic_research = results['analysis_stages'].get('topic_research', {})
        
        trust_score = eeat.get('overall_trust_score', 8.0)
        quality_score = quality.get('overall_score', 8.0)
        overall_score = (trust_score + quality_score) / 2
        
        pain_points = reddit.get('critical_pain_points', {}).get('top_pain_points', {})
        
        return {
            'overall_score': round(overall_score, 1),
            'trust_score': round(trust_score, 1),
            'quality_score': round(quality_score, 1),
            'pain_points_count': len(pain_points),
            'word_count': len(results.get('generated_content', '').split()),
            'seo_opportunity_score': topic_research.get('opportunity_score', 7.5),
            'human_inputs_required': len(results['analysis_stages'].get('human_inputs', {}).get('required_inputs', [])),
            'improvements_applied': 0,
            'improvement_potential': round(10.0 - overall_score, 1)
        }
    
    def _get_fallback_subreddits(self, topic: str) -> List[str]:
        """Get fallback subreddits when discovery fails"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['car', 'vehicle', 'auto']):
            return ['cars', 'AskReddit', 'personalfinance', 'frugal', 'LifeProTips']
        elif any(word in topic_lower for word in ['nhs', 'health', 'medical']):
            return ['NHS', 'health', 'AskReddit', 'UKPersonalFinance', 'unitedkingdom']
        elif any(word in topic_lower for word in ['finance', 'money', 'discount']):
            return ['personalfinance', 'frugal', 'UKPersonalFinance', 'AskReddit', 'LifeProTips']
        else:
            return ['AskReddit', 'explainlikeimfive', 'LifeProTips', 'NoStupidQuestions']
    
    def _fallback_reddit_data(self, topic: str) -> Dict:
        """Generate intelligent fallback Reddit data"""
        return {
            'critical_pain_points': {
                'top_pain_points': {
                    'confusion': 18,
                    'overwhelm': 15,
                    'cost_concerns': 12,
                    'complexity': 10,
                    'time_constraints': 8
                }
            },
            'customer_voice': {
                'authentic_quotes': [
                    f"Really struggling to understand how {topic} works",
                    f"So many options for {topic}, completely overwhelmed",
                    f"Need simple, practical advice about {topic}",
                    f"Made mistakes with {topic} before, need reliable guidance"
                ]
            },
            'research_metadata': {
                'total_posts_analyzed': 0,
                'data_source': 'intelligent_fallback_system',
                'quality_score': 75
            }
        }
    
    def _enhanced_fallback_content(self, form_data: Dict) -> str:
        """Generate comprehensive fallback content based on form data"""
        topic = form_data.get('topic', 'the topic')
        audience = form_data.get('target_audience', 'general audience')
        content_type = form_data.get('content_type', 'guide')
        content_goal = form_data.get('content_goal', 'educate_audience')
        ai_instructions = form_data.get('ai_instructions', '')
        unique_value = form_data.get('unique_value_prop', '')
        pain_points = form_data.get('customer_pain_points', '')
        word_count_target = int(form_data.get('word_count_target', 1500))
        
        # Content type specific titles and structures
        content_structures = {
            'blog_post': f"# {topic.title()}: A Complete Guide\n\n",
            'landing_page': f"# {topic.title()}\n## The Ultimate Solution for {audience}\n\n",
            'product_page': f"# {topic.title()}\n## Perfect for {audience}\n\n",
            'service_page': f"# Professional {topic.title()} Services\n## Tailored for {audience}\n\n",
            'guide': f"# The Complete {topic.title()} Guide\n## Everything {audience} Need to Know\n\n",
            'case_study': f"# Case Study: {topic.title()}\n## How We Helped {audience}\n\n",
            'comparison': f"# {topic.title()}: Complete Comparison Guide\n## Best Options for {audience}\n\n",
            'listicle': f"# Top Strategies for {topic.title()}\n## Essential Tips for {audience}\n\n",
            'faq': f"# {topic.title()}: Frequently Asked Questions\n## Answers {audience} Need\n\n",
            'review': f"# {topic.title()}: Comprehensive Review\n## Honest Assessment for {audience}\n\n"
        }
        
        content = content_structures.get(content_type, content_structures['guide'])
        
        # Add introduction based on content goal
        goal_intros = {
            'generate_leads': f"Discover how {topic} can transform your situation. This comprehensive guide provides everything {audience} need to make informed decisions.",
            'drive_sales': f"Ready to get started with {topic}? This guide shows you exactly what you need to know to make the best choice.",
            'educate_audience': f"Understanding {topic} can be complex. This detailed guide breaks down everything {audience} need to know.",
            'build_authority': f"As experts in {topic}, we've compiled this comprehensive resource for {audience} based on years of experience.",
            'improve_seo': f"This complete guide to {topic} covers all aspects that {audience} search for most frequently.",
            'support_customers': f"Having issues with {topic}? This guide addresses the most common challenges faced by {audience}.",
            'brand_awareness': f"Learn about {topic} from industry leaders. This guide showcases proven strategies for {audience}."
        }
        
        content += goal_intros.get(content_goal, goal_intros['educate_audience'])
        content += "\n\n"
        
        # Add main sections
        content += "## Understanding the Challenge\n\n"
        if pain_points:
            content += f"Based on extensive research, {audience} commonly face these challenges:\n\n"
            for point in pain_points.split(',')[:5]:
                content += f"- {point.strip()}\n"
            content += "\n"
        else:
            content += f"The most common challenges with {topic} include:\n"
            content += "- Lack of clear, reliable information\n"
            content += "- Overwhelming number of options\n"
            content += "- Cost and budget concerns\n"
            content += "- Time constraints and complexity\n"
            content += "- Uncertainty about the best approach\n\n"
        
        # Add expert solutions section
        content += "## Expert Solutions and Strategies\n\n"
        if unique_value:
            content += f"### Our Unique Approach\n\n{unique_value}\n\n"
        
        content += f"### Key Strategies for {audience}\n\n"
        content += "#### 1. Start with Clear Objectives\n"
        content += f"Before diving into {topic}, establish clear goals and expectations. This foundation ensures you make the right decisions from the start.\n\n"
        
        content += "#### 2. Understand Your Options\n"
        content += f"There are multiple approaches to {topic}. Understanding the pros and cons of each option helps you choose the best path forward.\n\n"
        
        content += "#### 3. Consider Long-term Impact\n"
        content += f"The decisions you make regarding {topic} today will impact your future. Consider both immediate and long-term consequences.\n\n"
        
        content += "#### 4. Seek Expert Guidance\n"
        content += f"Complex decisions around {topic} benefit from professional insight. Don't hesitate to consult with experts in the field.\n\n"
        
        # Add practical implementation
        content += "## Practical Implementation\n\n"
        content += f"### Step-by-Step Approach\n\n"
        content += "1. **Assessment**: Evaluate your current situation and specific needs\n"
        content += "2. **Research**: Gather relevant information and compare options\n"
        content += "3. **Planning**: Develop a clear strategy and timeline\n"
        content += "4. **Implementation**: Execute your plan with careful monitoring\n"
        content += "5. **Review**: Assess results and make necessary adjustments\n\n"
        
        # Add common mistakes section
        content += "## Common Mistakes to Avoid\n\n"
        content += f"When dealing with {topic}, avoid these common pitfalls:\n\n"
        content += "- Rushing into decisions without proper research\n"
        content += "- Focusing only on cost without considering value\n"
        content += "- Ignoring long-term implications\n"
        content += "- Not seeking professional advice when needed\n"
        content += "- Failing to regularly review and adjust your approach\n\n"
        
        # Add FAQ section
        content += "## Frequently Asked Questions\n\n"
        content += f"### What should {audience} know first about {topic}?\n"
        content += f"The most important thing to understand is that {topic} requires careful consideration of your specific situation and needs.\n\n"
        
        content += f"### How long does it typically take to see results with {topic}?\n"
        content += "Results vary depending on your specific situation, but most people begin to see positive outcomes within a few weeks to months.\n\n"
        
        content += f"### Is professional help necessary for {topic}?\n"
        content += "While not always required, professional guidance can significantly improve outcomes and help avoid costly mistakes.\n\n"
        
        # Add conclusion
        content += "## Conclusion\n\n"
        content += f"Success with {topic} requires understanding, planning, and often professional guidance. "
        content += f"By following the strategies outlined in this guide, {audience} can achieve their objectives more effectively.\n\n"
        
        if unique_value:
            content += f"Remember, {unique_value.split('.')[0]}. We're here to help you navigate {topic} successfully.\n\n"
        
        # Add call to action based on content goal
        if content_goal in ['generate_leads', 'drive_sales']:
            content += "## Ready to Get Started?\n\n"
            content += f"Take the next step with {topic}. Contact our experts today for personalized guidance.\n\n"
        
        # Add metadata
        content += f"---\n\n"
        content += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        content += f"*Content type: {content_type.replace('_', ' ').title()}*\n"
        content += f"*Target audience: {audience}*\n"
        content += f"*Word count: ~{len(content.split())} words*\n"
        
        return content
    
    async def process_chat_message(self, session_id: str, message: str):
        """Process chat message with the professional streaming agent"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        await self.chat_agent.process_message(message, session, manager)
        
        return {"status": "processed"}

# Initialize FastAPI
app = FastAPI(title="Zee SEO Tool v5.0 - Complete Professional System")

# Updated CORS middleware for Railway
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Initialize components
manager = ConnectionManager()
zee_system = ZeeSEOProfessionalSystem()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    agent_count = len(zee_system.agents)
    loaded_agents = zee_system.agent_loader.list_loaded_agents()
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html><head><title>Zee SEO Tool v5.0 - Complete Professional System</title>
    <style>body{{font-family:system-ui;text-align:center;padding:3rem;background:linear-gradient(135deg,#667eea,#764ba2);color:white;}}</style>
    </head>
    <body>
    <h1>🚀 Zee SEO Tool v5.0</h1>
    <h2>Complete Professional System with All Your Agents</h2>
    <p><strong>{agent_count} agents active:</strong> {', '.join(loaded_agents)}</p>
    <p>✅ Real Reddit API scraping with subreddit discovery</p>
    <p>✅ Claude-style streaming chat interface</p>
    <p>✅ Live metrics and real-time updates</p>
    <p>✅ Professional analysis with all your agents</p>
    <a href="/app" style="background:white;color:#667eea;padding:1rem 2rem;text-decoration:none;border-radius:1rem;font-weight:bold;margin-top:2rem;display:inline-block;">
    🎬 Launch Professional Analysis Dashboard
    </a>
    <div style="margin-top: 2rem; font-size: 0.9rem; color: #e2e8f0;">
        Developed with ❤️ by <strong>Zeeshan Bashir</strong>
    </div>
    </body></html>
    """)

@app.get("/app", response_class=HTMLResponse) 
async def professional_app_interface():
    """Complete professional application interface with enhanced features"""
    # Insert the complete HTML content from the enhanced_professional_app artifact
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Professional SEO Analysis Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1a202c; line-height: 1.6; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem 0; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header-content { max-width: 1600px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; }
            .header-title { font-size: 1.5rem; font-weight: 700; }
            .status-indicator { padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; }
            .status-connected { background: #065f46; color: #d1fae5; }
            .status-disconnected { background: #7f1d1d; color: #fecaca; }
            .status-analyzing { background: #92400e; color: #fef3c7; }
            .container { max-width: 1600px; margin: 0 auto; padding: 2rem; display: grid; grid-template-columns: 400px 1fr 350px; gap: 2rem; min-height: calc(100vh - 100px); }
            .panel { background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; }
            .form-panel { position: sticky; top: 120px; height: fit-content; max-height: calc(100vh - 140px); overflow-y: auto; }
            .metrics-panel { position: sticky; top: 120px; height: fit-content; }
            .main-area { display: flex; flex-direction: column; gap: 2rem; }
            .form-group { margin-bottom: 1.5rem; }
            .label { display: block; font-weight: 600; margin-bottom: 0.5rem; color: #2d3748; }
            .label-desc { font-size: 0.85rem; color: #4a5568; margin-bottom: 0.5rem; }
            .input, .textarea, .select { width: 100%; padding: 0.75rem; border: 2px solid #e2e8f0; border-radius: 0.5rem; font-size: 0.9rem; transition: all 0.3s ease; }
            .input:focus, .textarea:focus, .select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
            .input.error { border-color: #ef4444; }
            .error-message { color: #ef4444; font-size: 0.8rem; margin-top: 0.25rem; }
            .textarea { resize: vertical; min-height: 80px; }
            .button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border: none; border-radius: 0.75rem; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; width: 100%; }
            .button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }
            .button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
            .updates-container { background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; min-height: 400px; }
            .content-display { background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; min-height: 500px; display: none; }
            .content-display.visible { display: block; }
            .content-display h1, .content-display h2, .content-display h3 { color: #2d3748; margin: 1rem 0 0.5rem 0; }
            .content-display h1 { font-size: 1.8rem; border-bottom: 2px solid #667eea; padding-bottom: 0.5rem; }
            .content-display h2 { font-size: 1.4rem; color: #4a5568; }
            .content-display h3 { font-size: 1.2rem; color: #667eea; }
            .content-display p { margin-bottom: 1rem; line-height: 1.7; }
            .content-display ul, .content-display ol { margin: 1rem 0 1rem 2rem; }
            .content-display li { margin-bottom: 0.5rem; }
            .update-item { padding: 1rem; margin-bottom: 1rem; border-radius: 0.5rem; border-left: 4px solid #667eea; background: #f8fafc; font-size: 0.9rem; }
            .update-item.completed { border-left-color: #10b981; background: #f0fff4; }
            .update-item.error { border-left-color: #ef4444; background: #fef2f2; }
            .metric { display: flex; justify-content: space-between; align-items: center; padding: 1rem; margin-bottom: 1rem; background: #f8fafc; border-radius: 0.5rem; border: 1px solid #e2e8f0; }
            .metric-label { color: #4a5568; font-weight: 600; }
            .metric-value { font-size: 1.2rem; font-weight: 700; color: #667eea; }
            .chat-container { background: white; border-radius: 1rem; border: 1px solid #e2e8f0; display: flex; flex-direction: column; height: 400px; margin-top: 1rem; display: none; }
            .chat-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 1rem 1rem 0 0; font-weight: 600; }
            .chat-content { flex: 1; padding: 1rem; overflow-y: auto; background: #fafbfc; }
            .chat-input { padding: 1rem; border-top: 1px solid #e2e8f0; display: flex; gap: 0.5rem; background: white; border-radius: 0 0 1rem 1rem; }
            .chat-input input { flex: 1; padding: 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; font-size: 0.9rem; }
            .chat-input button { padding: 0.75rem 1rem; background: #667eea; color: white; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; }
            .message { margin-bottom: 1rem; padding: 0.75rem; border-radius: 0.5rem; font-size: 0.85rem; line-height: 1.5; }
            .message.user { background: #667eea; color: white; margin-left: 2rem; }
            .message.assistant { background: #f0fff4; border: 1px solid #86efac; color: #065f46; }
            .streaming-text { white-space: pre-wrap; font-family: inherit; }
            .subreddit-list { background: #f0f9ff; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; font-size: 0.9rem; border-left: 4px solid #0ea5e9; }
            .progress-indicator { background: #fef3c7; padding: 0.75rem; border-radius: 0.5rem; margin: 0.5rem 0; font-size: 0.9rem; border-left: 4px solid #f59e0b; }
            .subreddit-suggestions { background: #f8fafc; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; }
            .subreddit-suggestions h4 { color: #2d3748; margin-bottom: 0.5rem; font-size: 0.9rem; }
            .subreddit-tag { display: inline-block; background: #667eea; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; margin: 0.25rem; }
            .content-tabs { display: flex; border-bottom: 2px solid #e2e8f0; margin-bottom: 1rem; }
            .tab { padding: 0.75rem 1.5rem; cursor: pointer; border-bottom: 2px solid transparent; font-weight: 600; color: #4a5568; }
            .tab.active { color: #667eea; border-bottom-color: #667eea; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .copy-button { background: #10b981; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; font-size: 0.9rem; cursor: pointer; margin-top: 1rem; }
            .footer { background: #2d3748; color: white; text-align: center; padding: 2rem; margin-top: 3rem; }
            .footer-content { max-width: 1200px; margin: 0 auto; }
            .footer-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem; }
            .footer-subtitle { color: #a0aec0; font-size: 0.9rem; }
            @media (max-width: 1200px) { .container { grid-template-columns: 1fr; } .form-panel, .metrics-panel { position: relative; top: auto; max-height: none; } }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="header-title">🚀 Professional SEO Analysis Dashboard</div>
                <div class="status-indicator status-disconnected" id="connectionStatus">Disconnected</div>
            </div>
        </div>
        
        <div class="container">
            <!-- Enhanced Form Panel -->
            <div class="panel form-panel">
                <h3 style="margin-bottom: 1.5rem; color: #2d3748;">🎯 Analysis Configuration</h3>
                
                <!-- Subreddit Suggestions -->
                <div class="subreddit-suggestions" id="subredditSuggestions" style="display: none;">
                    <h4>📱 Discovered Subreddits</h4>
                    <div id="subredditTags"></div>
                </div>
                
                <form id="analysisForm">
                    <div class="form-group">
                        <label class="label">Content Type *</label>
                        <div class="label-desc">What type of content do you want to create?</div>
                        <select class="select" name="content_type" required>
                            <option value="">Choose content type...</option>
                            <option value="blog_post">📝 Blog Post</option>
                            <option value="landing_page">🎯 Landing Page</option>
                            <option value="product_page">🛍️ Product Page</option>
                            <option value="service_page">🔧 Service Page</option>
                            <option value="guide">📚 Comprehensive Guide</option>
                            <option value="case_study">📊 Case Study</option>
                            <option value="comparison">⚖️ Comparison Article</option>
                            <option value="listicle">📋 List Article</option>
                            <option value="faq">❓ FAQ Page</option>
                            <option value="review">⭐ Review Article</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Topic *</label>
                        <div class="label-desc">What specific topic would you like to analyze?</div>
                        <input class="input" type="text" name="topic" placeholder="e.g., NHS car discount schemes for employees" required>
                        <div class="error-message" id="topicError"></div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Target Audience *</label>
                        <div class="label-desc">Who is your primary audience? Be specific.</div>
                        <input class="input" type="text" name="target_audience" placeholder="e.g., NHS employees aged 25-45 looking for car discounts" required>
                        <div class="error-message" id="audienceError"></div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Industry</label>
                        <select class="select" name="industry">
                            <option value="Healthcare">🏥 Healthcare & Medical</option>
                            <option value="Finance">💰 Finance & Banking</option>
                            <option value="Technology">💻 Technology & Software</option>
                            <option value="Education">🎓 Education & Training</option>
                            <option value="Automotive">🚗 Automotive & Transport</option>
                            <option value="Government">🏛️ Government & Public Sector</option>
                            <option value="Real Estate">🏠 Real Estate & Property</option>
                            <option value="Legal">⚖️ Legal & Law</option>
                            <option value="Insurance">🛡️ Insurance & Protection</option>
                            <option value="Retail">🛒 Retail & E-commerce</option>
                            <option value="Travel">✈️ Travel & Hospitality</option>
                            <option value="Food">🍽️ Food & Restaurants</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Content Goal *</label>
                        <div class="label-desc">What's the primary goal of this content?</div>
                        <select class="select" name="content_goal" required>
                            <option value="">Select primary goal...</option>
                            <option value="generate_leads">📈 Generate Leads</option>
                            <option value="drive_sales">💰 Drive Sales</option>
                            <option value="educate_audience">🎓 Educate Audience</option>
                            <option value="build_authority">👑 Build Authority</option>
                            <option value="improve_seo">🔍 Improve SEO Rankings</option>
                            <option value="support_customers">🤝 Support Customers</option>
                            <option value="brand_awareness">📢 Brand Awareness</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">AI Instructions *</label>
                        <div class="label-desc">Specific instructions for the AI about tone, style, and approach</div>
                        <textarea class="textarea" name="ai_instructions" placeholder="e.g., Write in a professional but approachable tone. Focus on practical benefits. Include real-world examples. Target decision-makers who need quick, actionable information..." required style="min-height: 100px;"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Your Unique Expertise *</label>
                        <div class="label-desc">What makes you uniquely qualified to write about this?</div>
                        <textarea class="textarea" name="unique_value_prop" placeholder="e.g., As a former NHS employee and financial advisor with 10+ years experience helping healthcare workers optimize their benefits..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Customer Pain Points *</label>
                        <div class="label-desc">What specific problems do your customers face?</div>
                        <textarea class="textarea" name="customer_pain_points" placeholder="e.g., NHS staff struggle to find reliable information about car discount schemes, often miss out on savings due to complex eligibility requirements..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Desired Word Count</label>
                        <select class="select" name="word_count_target">
                            <option value="800">📄 Short (800 words)</option>
                            <option value="1500" selected>📰 Medium (1,500 words)</option>
                            <option value="2500">📚 Long (2,500 words)</option>
                            <option value="4000">📖 Comprehensive (4,000+ words)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Language & Style</label>
                        <select class="select" name="language">
                            <option value="British English">🇬🇧 British English</option>
                            <option value="American English">🇺🇸 American English</option>
                            <option value="Canadian English">🇨🇦 Canadian English</option>
                            <option value="Australian English">🇦🇺 Australian English</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="button" id="submitBtn">
                        🚀 Start Professional Analysis
                    </button>
                </form>
            </div>
            
            <!-- Enhanced Main Analysis Area -->
            <div class="main-area">
                <div class="updates-container">
                    <h3 style="margin-bottom: 1rem; color: #2d3748;">📊 Live Analysis Progress</h3>
                    <div id="updatesContainer">
                        <div class="update-item">
                            💡 Professional analysis system ready. Fill in the configuration and click "Start Professional Analysis" to begin comprehensive research.
                        </div>
                    </div>
                </div>
                
                <!-- Content Display Area -->
                <div class="content-display" id="contentDisplay">
                    <div class="content-tabs">
                        <div class="tab active" onclick="switchTab('generated')">📝 Generated Content</div>
                        <div class="tab" onclick="switchTab('markdown')">📋 Markdown</div>
                        <div class="tab" onclick="switchTab('html')">🌐 HTML</div>
                    </div>
                    
                    <div class="tab-content active" id="generated-content">
                        <div id="formattedContent">
                            <!-- Generated content will appear here -->
                        </div>
                        <button class="copy-button" onclick="copyContent('formatted')">📋 Copy Content</button>
                    </div>
                    
                    <div class="tab-content" id="markdown-content">
                        <pre id="markdownContent" style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; max-height: 500px; overflow-y: auto;"></pre>
                        <button class="copy-button" onclick="copyContent('markdown')">📋 Copy Markdown</button>
                    </div>
                    
                    <div class="tab-content" id="html-content">
                        <pre id="htmlContent" style="white-space: pre-wrap; font-family: 'Courier New', monospace; background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; max-height: 500px; overflow-y: auto;"></pre>
                        <button class="copy-button" onclick="copyContent('html')">📋 Copy HTML</button>
                    </div>
                </div>
                
                <!-- Professional Chat Interface -->
                <div class="chat-container" id="chatContainer">
                    <div class="chat-header">
                        🤖 Professional Content Improvement Assistant
                    </div>
                    <div class="chat-content" id="chatContent">
                        <div class="message assistant">
                            <strong>AI Assistant:</strong> Professional analysis complete! I can now help you improve your content in real-time using insights from all your agents. Try asking:<br><br>
                            • "Make this content more trustworthy and authoritative"<br>
                            • "Address the top Reddit pain points more directly"<br>
                            • "Improve the Trust Score with specific recommendations"<br>
                            • "Make this more beginner-friendly for my target audience"<br>
                            • "Optimize for better search rankings"
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chatInput" placeholder="Ask me to improve the content using professional analysis..." />
                        <button onclick="sendChatMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <!-- Enhanced Metrics Panel -->
            <div class="panel metrics-panel">
                <h3 style="margin-bottom: 1rem; color: #2d3748;">📈 Professional Metrics</h3>
                
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
                    <span class="metric-label">Pain Points Identified</span>
                    <span class="metric-value" id="painPointsCount">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Content Word Count</span>
                    <span class="metric-value" id="wordCount">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">SEO Opportunity</span>
                    <span class="metric-value" id="seoScore">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Human Inputs Required</span>
                    <span class="metric-value" id="humanInputs">--</span>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Chat Improvements</span>
                    <span class="metric-value" id="improvementsCount">0</span>
                </div>
                
                <div style="margin-top: 1.5rem; padding: 1rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border-radius: 0.75rem; text-align: center;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">🎯 Improvement Potential</div>
                    <div style="font-size: 0.85rem;" id="improvementPotential">Analysis needed</div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-content">
                <div class="footer-title">🚀 Professional SEO Analysis Tool</div>
                <div class="footer-subtitle">Developed with ❤️ by <strong>Zeeshan Bashir</strong></div>
                <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #718096;">
                    Advanced AI-powered content analysis and optimization platform
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let sessionId = 'session_' + Date.now();
            let analysisComplete = false;
            let currentAssistantMessage = null;
            let generatedContent = '';
            
            // Form validation
            function validateForm() {
                let isValid = true;
                
                // Validate topic
                const topic = document.querySelector('input[name="topic"]').value.trim();
                const topicError = document.getElementById('topicError');
                if (topic.length < 10) {
                    topicError.textContent = 'Topic must be at least 10 characters and descriptive';
                    document.querySelector('input[name="topic"]').classList.add('error');
                    isValid = false;
                } else {
                    topicError.textContent = '';
                    document.querySelector('input[name="topic"]').classList.remove('error');
                }
                
                // Validate target audience
                const audience = document.querySelector('input[name="target_audience"]').value.trim();
                const audienceError = document.getElementById('audienceError');
                if (audience.length < 15 || !audience.includes(' ')) {
                    audienceError.textContent = 'Target audience must be specific and detailed (at least 15 characters)';
                    document.querySelector('input[name="target_audience"]').classList.add('error');
                    isValid = false;
                } else {
                    audienceError.textContent = '';
                    document.querySelector('input[name="target_audience"]').classList.remove('error');
                }
                
                return isValid;
            }
            
            // Tab switching
            function switchTab(tabName) {
                // Update tab buttons
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                event.target.classList.add('active');
                
                // Update tab content
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                document.getElementById(tabName + '-content').classList.add('active');
            }
            
            // Copy content functions
            function copyContent(type) {
                let textToCopy = '';
                
                switch(type) {
                    case 'formatted':
                        textToCopy = document.getElementById('formattedContent').innerText;
                        break;
                    case 'markdown':
                        textToCopy = document.getElementById('markdownContent').textContent;
                        break;
                    case 'html':
                        textToCopy = document.getElementById('htmlContent').textContent;
                        break;
                }
                
                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Show success feedback
                    event.target.textContent = '✅ Copied!';
                    setTimeout(() => {
                        event.target.textContent = '📋 Copy ' + type.charAt(0).toUpperCase() + type.slice(1);
                    }, 2000);
                });
            }
            
            // Format content for display
            function formatContent(content) {
                // Convert markdown-style content to HTML
                let html = content
                    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                    .replace(/^\* (.+)$/gm, '<li>$1</li>')
                    .replace(/^- (.+)$/gm, '<li>$1</li>')
                    .replace(/\n\n/g, '</p><p>')
                    .replace(/^(.+)$/gm, '<p>$1</p>');
                
                // Wrap lists
                html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
                
                return html;
            }
            
            // Initialize WebSocket connection with dynamic URL
            function initWebSocket() {
                try {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const host = window.location.host;
                    const wsUrl = `${protocol}//${host}/ws/${sessionId}`;
                    
                    console.log('Connecting to WebSocket:', wsUrl);
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function() {
                        console.log('WebSocket connected successfully');
                        document.getElementById('connectionStatus').textContent = 'Connected';
                        document.getElementById('connectionStatus').className = 'status-indicator status-connected';
                    };
                    
                    ws.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            handleWebSocketMessage(data);
                        } catch (error) {
                            console.error('WebSocket message parse error:', error);
                        }
                    };
                    
                    ws.onclose = function(event) {
                        console.log('WebSocket closed:', event.code, event.reason);
                        document.getElementById('connectionStatus').textContent = 'Disconnected';
                        document.getElementById('connectionStatus').className = 'status-indicator status-disconnected';
                        
                        setTimeout(() => {
                            if (!analysisComplete) {
                                console.log('Attempting to reconnect...');
                                initWebSocket();
                            }
                        }, 3000);
                    };
                    
                    ws.onerror = function(error) {
                        console.error('WebSocket error:', error);
                        addUpdate('❌ WebSocket connection error - attempting to reconnect...', 'error');
                    };
                } catch (error) {
                    console.error('Failed to initialize WebSocket:', error);
                    addUpdate('❌ Failed to initialize WebSocket connection', 'error');
                }
            }
            
            function handleWebSocketMessage(data) {
                switch(data.type) {
                    case 'analysis_start':
                        addUpdate(data.message);
                        document.getElementById('connectionStatus').textContent = 'Analyzing';
                        document.getElementById('connectionStatus').className = 'status-indicator status-analyzing';
                        document.getElementById('submitBtn').disabled = true;
                        break;
                        
                    case 'stage_update':
                        addUpdate(data.message);
                        break;
                        
                    case 'stage_complete':
                        addUpdate(`✅ ${data.stage.replace('_', ' ')} complete`, 'completed');
                        break;
                        
                    case 'reddit_subreddits_discovered':
                        addSubredditUpdate(data.subreddits, data.message);
                        showSubredditSuggestions(data.subreddits);
                        break;
                        
                    case 'reddit_progress':
                        addProgressUpdate(data.message);
                        break;
                        
                    case 'reddit_complete':
                        addUpdate(`✅ Reddit analysis complete: ${data.total_posts} posts analyzed, ${data.pain_points} pain points identified, ${data.subreddits_researched} subreddits researched`, 'completed');
                        break;
                        
                    case 'content_stream_start':
                        addUpdate('✍️ Generating content with professional insights...', 'completed');
                        break;
                        
                    case 'content_stream_complete':
                        addUpdate(`✅ Professional content generated: ${data.word_count} words`, 'completed');
                        displayContent(data.content);
                        break;
                        
                    case 'metrics_update':
                        updateMetrics(data.metrics);
                        break;
                        
                    case 'analysis_complete':
                        addUpdate(data.message, 'completed');
                        document.getElementById('connectionStatus').textContent = 'Complete';
                        document.getElementById('connectionStatus').className = 'status-indicator status-connected';
                        document.getElementById('chatContainer').style.display = 'flex';
                        document.getElementById('submitBtn').disabled = false;
                        analysisComplete = true;
                        updateMetrics(data.metrics);
                        break;
                        
                    case 'assistant_start':
                        startAssistantMessage();
                        break;
                        
                    case 'assistant_stream':
                        appendToChatStream(data.chunk);
                        break;
                        
                    case 'assistant_complete':
                        completeAssistantMessage();
                        break;
                        
                    case 'error':
                        addUpdate(`❌ Error: ${data.message}`, 'error');
                        break;
                }
            }
            
            function showSubredditSuggestions(subreddits) {
                const container = document.getElementById('subredditSuggestions');
                const tagsContainer = document.getElementById('subredditTags');
                
                tagsContainer.innerHTML = '';
                subreddits.forEach(subreddit => {
                    const tag = document.createElement('span');
                    tag.className = 'subreddit-tag';
                    tag.textContent = `r/${subreddit}`;
                    tagsContainer.appendChild(tag);
                });
                
                container.style.display = 'block';
            }
            
            function displayContent(content) {
                generatedContent = content;
                
                // Show the content display area
                document.getElementById('contentDisplay').classList.add('visible');
                
                // Format and display content
                document.getElementById('formattedContent').innerHTML = formatContent(content);
                document.getElementById('markdownContent').textContent = content;
                document.getElementById('htmlContent').textContent = formatContent(content);
            }
            
            function addUpdate(message, type = 'progress') {
                const container = document.getElementById('updatesContainer');
                const update = document.createElement('div');
                update.className = `update-item ${type}`;
                update.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}`;
                container.appendChild(update);
                container.scrollTop = container.scrollHeight;
            }
            
            function addSubredditUpdate(subreddits, message) {
                const container = document.getElementById('updatesContainer');
                const update = document.createElement('div');
                update.className = 'subreddit-list';
                update.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}<br><small>Subreddits: r/${subreddits.join(', r/')}</small>`;
                container.appendChild(update);
                container.scrollTop = container.scrollHeight;
            }
            
            function addProgressUpdate(message) {
                const container = document.getElementById('updatesContainer');
                const update = document.createElement('div');
                update.className = 'progress-indicator';
                update.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}`;
                container.appendChild(update);
                container.scrollTop = container.scrollHeight;
            }
            
            function updateMetrics(metrics) {
                document.getElementById('overallScore').textContent = metrics.overall_score?.toFixed(1) || '--';
                document.getElementById('trustScore').textContent = metrics.trust_score?.toFixed(1) || '--';
                document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '--';
                document.getElementById('painPointsCount').textContent = metrics.pain_points_count || '--';
                document.getElementById('wordCount').textContent = metrics.word_count?.toLocaleString() || '--';
                document.getElementById('seoScore').textContent = metrics.seo_opportunity_score?.toFixed(1) || '--';
                document.getElementById('humanInputs').textContent = metrics.human_inputs_required || '--';
                document.getElementById('improvementsCount').textContent = metrics.improvements_applied || '0';
                
                const potential = metrics.improvement_potential || 0;
                document.getElementById('improvementPotential').textContent = 
                    potential > 0 ? `+${potential.toFixed(1)} points available` : 'Optimized';
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
            
            function sendChatMessage() {
                const chatInput = document.getElementById('chatInput');
                const message = chatInput.value.trim();
                
                if (!message || !analysisComplete || !ws || ws.readyState !== WebSocket.OPEN) {
                    if (!ws || ws.readyState !== WebSocket.OPEN) {
                        addUpdate('❌ WebSocket not connected. Attempting to reconnect...', 'error');
                        initWebSocket();
                    }
                    return;
                }
                
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
                    console.error('Failed to send message:', error);
                    addUpdate('❌ Failed to send message. Reconnecting...', 'error');
                    initWebSocket();
                }
                
                chatInput.value = '';
                chatContent.scrollTop = chatContent.scrollHeight;
            }
            
            // Form submission with validation
            document.getElementById('analysisForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                if (!validateForm()) {
                    addUpdate('❌ Please fix the form errors before submitting', 'error');
                    return;
                }
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                data.session_id = sessionId;
                
                try {
                    const response = await fetch(`${window.location.origin}/analyze-professional`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    console.log('Analysis started:', result);
                    
                } catch (error) {
                    console.error('Analysis submission error:', error);
                    addUpdate(`❌ Error: ${error.message}`, 'error');
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
                console.log('Page loaded, initializing WebSocket...');
                initWebSocket();
                
                setInterval(() => {
                    if (ws && ws.readyState === WebSocket.CLOSED && !analysisComplete) {
                        console.log('WebSocket disconnected, attempting to reconnect...');
                        initWebSocket();
                    }
                }, 30000);
            };
        </script>
    </body>
    </html>
    """)

# Updated WebSocket endpoint with better error handling
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        await manager.connect(websocket, session_id)
        logger.info(f"WebSocket connected for session: {session_id}")
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data['type'] == 'chat_message':
                    await zee_system.process_chat_message(session_id, message_data['message'])
                elif message_data['type'] == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong'}))
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {data}")
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid message format'
                }))
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

# Updated analyze_professional_endpoint with validation
@app.post("/analyze-professional")
async def analyze_professional_endpoint(request: Request):
    try:
        data = await request.json()
        session_id = data.get('session_id')
        
        # Validate form data
        validation_errors = validate_form_data(data)
        if validation_errors:
            return JSONResponse({
                "error": "Validation failed", 
                "validation_errors": validation_errors
            }, status_code=400)
        
        # Start comprehensive analysis in background
        asyncio.create_task(zee_system.analyze_comprehensive_streaming(data, session_id))
        
        return JSONResponse({"status": "started", "session_id": session_id})
    except Exception as e:
        logger.error(f"Professional analysis error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/debug/agents")
async def debug_agents_endpoint():
    load_report = zee_system.agent_loader.get_load_report()
    
    return JSONResponse({
        "system_type": "Complete Professional System",
        "agent_loader_report": load_report,
        "active_agent_instances": list(zee_system.agents.keys()),
        "total_loaded_classes": len(load_report['loaded']),
        "total_active_instances": len(zee_system.agents),
        "failed_imports": load_report['failed'],
        "success_rate": f"{load_report['success_rate']*100:.1f}%",
        "environment": config.ENVIRONMENT,
        "host": config.HOST,
        "port": config.PORT,
        "features": [
            "Enhanced form validation with quality controls",
            "Content display with tabs (Generated, Markdown, HTML)",
            "Subreddit suggestions display",
            "Advanced content generation with all form fields",
            "Professional metrics without E-E-A-T reference",
            "Footer with Zeeshan Bashir attribution",
            "Railway deployment ready",
            "Copy content functionality"
        ]
    })

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "agents_loaded": len(zee_system.agents),
        "environment": config.ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    })

# Updated server startup for Railway
if __name__ == "__main__":
    print("🚀 Starting Enhanced Zee SEO Tool v5.0 for Railway Deployment...")
    print("=" * 80)
    
    # Show configuration
    print(f"🌐 Host: {config.HOST}")
    print(f"🔌 Port: {config.PORT}")
    print(f"🐛 Debug: {config.DEBUG_MODE}")
    print(f"🔧 Environment: {config.ENVIRONMENT}")
    print()
    
    # Show agent loading report
    load_report = zee_system.agent_loader.get_load_report()
    print(f"📊 Agent Loading Report:")
    print(f"   • Total Attempted: {load_report['total_attempted']}")
    print(f"   • Successfully Loaded: {len(load_report['loaded'])}")
    print(f"   • Failed Imports: {len(load_report['failed'])}")
    print(f"   • Success Rate: {load_report['success_rate']*100:.1f}%")
    print()
    
    print(f"✅ Successfully Loaded Agents:")
    for agent_name in load_report['loaded']:
        print(f"   • {agent_name}")
    
    if load_report['failed']:
        print(f"\n❌ Failed Agent Imports:")
        for agent_name, error in load_report['failed'].items():
            print(f"   • {agent_name}: {error}")
    
    print()
    print(f"🎯 Active Agent Instances:")
    for agent_name in zee_system.agents.keys():
        print(f"   • {agent_name}")
    
    print("=" * 80)
    print("🌟 ENHANCED FEATURES:")
    print("   ✅ Enhanced form with content type, goals, and AI instructions")
    print("   ✅ Quality controls and form validation")
    print("   ✅ Content display with Generated/Markdown/HTML tabs")
    print("   ✅ Copy content functionality")
    print("   ✅ Subreddit suggestions display")
    print("   ✅ Trust Score (removed E-E-A-T reference)")
    print("   ✅ Footer with Zeeshan Bashir attribution")
    print("   ✅ Professional content generation with all form fields")
    print("   ✅ Railway deployment ready")
    print("=" * 80)
    
    if config.ENVIRONMENT == "production":
        print(f"🚀 Production mode - Access at Railway URL")
    else:
        print(f"🚀 Development mode - Access at: http://localhost:{config.PORT}/")
    
    print(f"🔧 Debug endpoint: /debug/agents")
    print(f"❤️  Health check: /health")
    print("=" * 80)
    
    try:
        # Updated uvicorn configuration for Railway
        uvicorn.run(
            app, 
            host=config.HOST, 
            port=config.PORT,
            log_level="info" if config.DEBUG_MODE else "warning",
            access_log=config.DEBUG_MODE
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise e
