import os
import sys
import json
import logging
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the src directory to Python path
sys.path.append('/app/src')
sys.path.append('/app/src/agents')

# FastAPI imports
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AGENT LOADING WITH DETAILED ERROR REPORTING
agent_status = {}
agent_errors = {}

# Core agents - CRITICAL
try:
    from agents.reddit_researcher import EnhancedRedditResearcher
    agent_status['reddit_researcher'] = 'loaded'
    logger.info("✅ EnhancedRedditResearcher loaded successfully")
except ImportError as e:
    agent_status['reddit_researcher'] = 'failed'
    agent_errors['reddit_researcher'] = str(e)
    logger.error(f"❌ EnhancedRedditResearcher failed: {e}")
    try:
        from src.agents.reddit_researcher import EnhancedRedditResearcher
        agent_status['reddit_researcher'] = 'loaded_alt'
        logger.info("✅ EnhancedRedditResearcher loaded from src path")
    except ImportError as e2:
        agent_status['reddit_researcher'] = 'completely_failed'
        agent_errors['reddit_researcher'] = f"Primary: {e}, Alt: {e2}"
        EnhancedRedditResearcher = None

try:
    from agents.full_content_generator import FullContentGenerator
    agent_status['full_content_generator'] = 'loaded'
    logger.info("✅ FullContentGenerator loaded successfully")
except ImportError as e:
    agent_status['full_content_generator'] = 'failed'
    agent_errors['full_content_generator'] = str(e)
    logger.error(f"❌ FullContentGenerator failed: {e}")
    try:
        from src.agents.full_content_generator import FullContentGenerator
        agent_status['full_content_generator'] = 'loaded_alt'
        logger.info("✅ FullContentGenerator loaded from src path")
    except ImportError as e2:
        agent_status['full_content_generator'] = 'completely_failed'
        agent_errors['full_content_generator'] = f"Primary: {e}, Alt: {e2}"
        FullContentGenerator = None

# Optional agents - Load each one individually and report status
optional_agents = {}
agent_classes = {
    'business_context_collector': 'BusinessContextCollector',
    'content_quality_scorer': 'ContentQualityScorer',
    'content_type_classifier': 'ContentTypeClassifier',
    'eeat_assessor': ['EnhancedEEATAssessor', 'EEATAssessor'],
    'human_input_identifier': 'HumanInputIdentifier',
    'intent_classifier': 'IntentClassifier',
    'journey_mapper': 'JourneyMapper',
    'AdvancedTopicResearchAgent': 'AdvancedTopicResearchAgent',
    'knowledge_graph_trends_agent': 'KnowledgeGraphTrendsAgent',
    'customer_journey_mapper': 'CustomerJourneyMapper',
    'content_generator': 'ContentGenerator',
    'content_analysis_snapshot': 'ContentAnalysisSnapshot'
}

for agent_file, class_names in agent_classes.items():
    try:
        # Try importing from agents folder first
        module = __import__(f'agents.{agent_file}', fromlist=[''])
        
        # Handle multiple possible class names
        if isinstance(class_names, list):
            agent_class = None
            for class_name in class_names:
                if hasattr(module, class_name):
                    agent_class = getattr(module, class_name)
                    break
            if agent_class:
                optional_agents[agent_file] = {'module': module, 'class': agent_class}
                agent_status[agent_file] = 'loaded'
                logger.info(f"✅ {agent_file} loaded successfully")
            else:
                agent_status[agent_file] = 'no_class'
                agent_errors[agent_file] = f"No matching class found: {class_names}"
        else:
            if hasattr(module, class_names):
                agent_class = getattr(module, class_names)
                optional_agents[agent_file] = {'module': module, 'class': agent_class}
                agent_status[agent_file] = 'loaded'
                logger.info(f"✅ {agent_file} loaded successfully")
            else:
                agent_status[agent_file] = 'no_class'
                agent_errors[agent_file] = f"Class {class_names} not found"
                
    except ImportError as e:
        try:
            # Try importing from src.agents folder
            module = __import__(f'src.agents.{agent_file}', fromlist=[''])
            if isinstance(class_names, list):
                agent_class = None
                for class_name in class_names:
                    if hasattr(module, class_name):
                        agent_class = getattr(module, class_name)
                        break
                if agent_class:
                    optional_agents[agent_file] = {'module': module, 'class': agent_class}
                    agent_status[agent_file] = 'loaded_alt'
                    logger.info(f"✅ {agent_file} loaded from src path")
                else:
                    agent_status[agent_file] = 'no_class_alt'
                    agent_errors[agent_file] = f"No matching class in src: {class_names}"
            else:
                if hasattr(module, class_names):
                    agent_class = getattr(module, class_names)
                    optional_agents[agent_file] = {'module': module, 'class': agent_class}
                    agent_status[agent_file] = 'loaded_alt'
                    logger.info(f"✅ {agent_file} loaded from src path")
                else:
                    agent_status[agent_file] = 'no_class_alt'
                    agent_errors[agent_file] = f"Class {class_names} not found in src"
        except ImportError as e2:
            agent_status[agent_file] = 'completely_failed'
            agent_errors[agent_file] = f"Primary: {e}, Alt: {e2}"
            logger.error(f"❌ {agent_file} completely failed to load")

# Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ZeeSEOTool:v4.0")
    KNOWLEDGE_GRAPH_API_URL = os.getenv("KNOWLEDGE_GRAPH_API_URL", "https://myaiapplication-production.up.railway.app/api/knowledge-graph")
    KNOWLEDGE_GRAPH_API_KEY = os.getenv("KNOWLEDGE_GRAPH_API_KEY", "")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
    PORT = int(os.getenv("PORT", 8002))

config = Config()

# Initialize FastAPI
app = FastAPI(title="Zee SEO Tool v4.0 - Enhanced Agent Integration")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Enhanced Orchestrator
class EnhancedZeeOrchestrator:
    def __init__(self):
        self.agents = {}
        self.conversation_history = []
        self.kg_url = config.KNOWLEDGE_GRAPH_API_URL
        self.kg_key = config.KNOWLEDGE_GRAPH_API_KEY
        
        # Initialize core agents
        if EnhancedRedditResearcher:
            self.agents['reddit_researcher'] = EnhancedRedditResearcher()
        if FullContentGenerator:
            self.agents['content_generator'] = FullContentGenerator()
            
        # Initialize optional agents
        for agent_name, agent_info in optional_agents.items():
            try:
                self.agents[agent_name] = agent_info['class']()
                logger.info(f"✅ Initialized {agent_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {agent_name}: {e}")
                agent_errors[f"{agent_name}_init"] = str(e)

    async def get_knowledge_graph_insights(self, topic: str) -> Dict[str, Any]:
        """Get insights from Railway Knowledge Graph API"""
        try:
            headers = {"Content-Type": "application/json"}
            if self.kg_key:
                headers["x-api-key"] = self.kg_key
            
            payload = {
                "topic": topic,
                "depth": 3,
                "include_related": True,
                "include_gaps": True,
                "max_entities": 10
            }
            
            logger.info(f"🧠 Requesting knowledge graph for: {topic}")
            response = requests.post(self.kg_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Knowledge Graph API success - Found {len(result.get('entities', []))} entities")
                return result
            else:
                logger.warning(f"⚠️ Knowledge Graph API returned {response.status_code}: {response.text}")
                return self._get_fallback_kg_insights(topic)
                
        except requests.exceptions.Timeout:
            logger.error("⏰ Knowledge Graph API timeout")
            return self._get_fallback_kg_insights(topic)
        except Exception as e:
            logger.error(f"❌ Knowledge Graph API error: {e}")
            return self._get_fallback_kg_insights(topic)

    def _get_fallback_kg_insights(self, topic: str) -> Dict[str, Any]:
        """Enhanced fallback knowledge graph insights"""
        return {
            "entities": [f"{topic} fundamentals", f"{topic} best practices", f"{topic} implementation guide"],
            "related_topics": [f"Advanced {topic}", f"{topic} for beginners", f"{topic} case studies"],
            "content_gaps": [f"Complete {topic} implementation guide", f"{topic} cost-benefit analysis"],
            "confidence_score": 0.85,
            "source": "enhanced_fallback_generated"
        }

    async def generate_comprehensive_analysis(self, form_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive analysis using all available agents"""
        topic = form_data['topic']
        logger.info(f"🚀 Starting comprehensive analysis for: {topic}")
        
        results = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "agents_used": {},
            "errors": {}
        }
        
        # Business Context
        business_context = {
            'topic': topic,
            'target_audience': form_data.get('target_audience', ''),
            'industry': form_data.get('industry', ''),
            'unique_value_prop': form_data.get('unique_value_prop', ''),
            'customer_pain_points': form_data.get('customer_pain_points', '')
        }
        results['business_context'] = business_context
        
        # Reddit Research
        if 'reddit_researcher' in self.agents:
            try:
                subreddits = self._get_relevant_subreddits(topic)
                reddit_insights = self.agents['reddit_researcher'].research_topic_comprehensive(
                    topic=topic,
                    subreddits=subreddits,
                    max_posts_per_subreddit=15,
                    social_media_focus=True
                )
                results['reddit_insights'] = reddit_insights
                results['agents_used']['reddit_researcher'] = 'success'
                logger.info("✅ Reddit research completed")
            except Exception as e:
                results['errors']['reddit_researcher'] = str(e)
                results['agents_used']['reddit_researcher'] = 'failed'
                logger.error(f"❌ Reddit research failed: {e}")
        else:
            results['errors']['reddit_researcher'] = "Agent not loaded"
            
        # Knowledge Graph Analysis
        try:
            kg_insights = await self.get_knowledge_graph_insights(topic)
            results['knowledge_graph'] = kg_insights
            results['agents_used']['knowledge_graph'] = 'success'
        except Exception as e:
            results['errors']['knowledge_graph'] = str(e)
            results['agents_used']['knowledge_graph'] = 'failed'
            
        # Content Type Classification
        if 'content_type_classifier' in self.agents:
            try:
                content_type = self.agents['content_type_classifier'].classify_content_type(
                    topic=topic,
                    business_context=business_context
                )
                results['content_type'] = content_type
                results['agents_used']['content_type_classifier'] = 'success'
            except Exception as e:
                results['errors']['content_type_classifier'] = str(e)
                results['agents_used']['content_type_classifier'] = 'failed'
                
        # Intent Classification
        if 'intent_classifier' in self.agents:
            try:
                intent_data = self.agents['intent_classifier'].classify_intent(
                    topic=topic,
                    context=business_context
                )
                results['intent_data'] = intent_data
                results['agents_used']['intent_classifier'] = 'success'
            except Exception as e:
                results['errors']['intent_classifier'] = str(e)
                results['agents_used']['intent_classifier'] = 'failed'
                
        # E-E-A-T Assessment
        if 'eeat_assessor' in self.agents:
            try:
                eeat_assessment = self.agents['eeat_assessor'].assess_eeat_opportunity(
                    topic=topic,
                    business_context=business_context,
                    reddit_insights=results.get('reddit_insights', {})
                )
                results['eeat_assessment'] = eeat_assessment
                results['agents_used']['eeat_assessor'] = 'success'
            except Exception as e:
                results['errors']['eeat_assessor'] = str(e)
                results['agents_used']['eeat_assessor'] = 'failed'
                
        # Content Generation
        if 'content_generator' in self.agents:
            try:
                generated_content = self.agents['content_generator'].generate_complete_content(
                    topic=topic,
                    content_type=results.get('content_type', 'comprehensive_guide'),
                    reddit_insights=results.get('reddit_insights', {}),
                    journey_data=results.get('journey_data', {}),
                    business_context=business_context,
                    human_inputs=form_data,
                    eeat_assessment=results.get('eeat_assessment', {})
                )
                results['generated_content'] = generated_content
                results['agents_used']['content_generator'] = 'success'
            except Exception as e:
                results['errors']['content_generator'] = str(e)
                results['agents_used']['content_generator'] = 'failed'
                
        # Content Quality Scoring
        if 'content_quality_scorer' in self.agents and 'generated_content' in results:
            try:
                quality_score = self.agents['content_quality_scorer'].score_content_quality(
                    content=results['generated_content'],
                    topic=topic,
                    reddit_insights=results.get('reddit_insights', {})
                )
                results['quality_assessment'] = quality_score
                results['agents_used']['content_quality_scorer'] = 'success'
            except Exception as e:
                results['errors']['content_quality_scorer'] = str(e)
                results['agents_used']['content_quality_scorer'] = 'failed'
                
        return results

    def _get_relevant_subreddits(self, topic: str) -> List[str]:
        """Get relevant subreddits for topic research"""
        base_subreddits = ["AskReddit", "explainlikeimfive", "LifeProTips", "YouShouldKnow"]
        
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ['tech', 'software', 'ai', 'programming']):
            base_subreddits.extend(["technology", "programming", "MachineLearning", "webdev"])
        elif any(word in topic_lower for word in ['health', 'fitness', 'nutrition']):
            base_subreddits.extend(["health", "fitness", "nutrition", "wellness"])
        elif any(word in topic_lower for word in ['finance', 'money', 'investing']):
            base_subreddits.extend(["personalfinance", "investing", "financialindependence"])
        elif any(word in topic_lower for word in ['marketing', 'seo', 'content']):
            base_subreddits.extend(["marketing", "SEO", "content_marketing", "digital_marketing"])
            
        return list(set(base_subreddits))[:10]

# Initialize orchestrator
zee_orchestrator = EnhancedZeeOrchestrator()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced homepage with detailed agent status"""
    loaded_agents = len([k for k, v in agent_status.items() if v in ['loaded', 'loaded_alt']])
    failed_agents = len([k for k, v in agent_status.items() if 'failed' in v])
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool v4.0 - Enhanced Agent Integration</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #1a202c;
                min-height: 100vh;
                padding: 2rem;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 2rem;
                padding: 3rem;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 3rem;
            }}
            
            .logo {{
                font-size: 4rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
            }}
            
            .subtitle {{
                color: #4a5568;
                font-size: 1.2rem;
                margin-bottom: 2rem;
            }}
            
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            
            .stat-card {{
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            
            .stat-number {{
                font-size: 3rem;
                font-weight: 900;
                color: #667eea;
                margin-bottom: 0.5rem;
            }}
            
            .stat-label {{
                color: #4a5568;
                font-weight: 600;
            }}
            
            .agent-status {{
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 3rem;
            }}
            
            .agent-status h3 {{
                color: #2d3748;
                margin-bottom: 1.5rem;
                font-size: 1.5rem;
            }}
            
            .agent-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
            }}
            
            .agent-item {{
                padding: 1rem;
                border-radius: 0.5rem;
                font-size: 0.9rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .agent-item.loaded {{
                background: #f0fff4;
                border: 1px solid #68d391;
                color: #2f855a;
            }}
            
            .agent-item.failed {{
                background: #fef5e7;
                border: 1px solid #f6ad55;
                color: #c05621;
            }}
            
            .agent-item.critical-failed {{
                background: #fed7d7;
                border: 1px solid #fc8181;
                color: #c53030;
            }}
            
            .cta-button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem 3rem;
                border: none;
                border-radius: 1rem;
                font-size: 1.2rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                margin: 0 auto;
            }}
            
            .cta-button:hover {{
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
            }}
            
            .error-details {{
                background: #fed7d7;
                border: 1px solid #fc8181;
                color: #c53030;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-top: 1rem;
                font-size: 0.8rem;
                max-height: 100px;
                overflow-y: auto;
            }}
            
            .button-container {{
                text-align: center;
                margin-top: 2rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🚀 Zee SEO Tool v4.0</div>
                <p class="subtitle">Enhanced Agent Integration • Knowledge Graph Analysis • Advanced Content Generation</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{loaded_agents}</div>
                    <div class="stat-label">Agents Loaded</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{failed_agents}</div>
                    <div class="stat-label">Failed Agents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(agent_status)}</div>
                    <div class="stat-label">Total Agents</div>
                </div>
            </div>
            
            <div class="agent-status">
                <h3>🤖 Agent Status Report</h3>
                <div class="agent-grid">
                    {self._generate_agent_status_html()}
                </div>
            </div>
            
            <div class="button-container">
                <a href="/app" class="cta-button">
                    🎯 Start Enhanced Content Creation
                </a>
            </div>
        </div>
    </body>
    </html>
    """)

def _generate_agent_status_html():
    """Generate HTML for agent status display"""
    html = ""
    for agent_name, status in agent_status.items():
        if status in ['loaded', 'loaded_alt']:
            html += f'<div class="agent-item loaded">✅ {agent_name.replace("_", " ").title()}<small> ({status})</small></div>'
        elif 'failed' in status:
            is_critical = agent_name in ['reddit_researcher', 'full_content_generator']
            class_name = 'critical-failed' if is_critical else 'failed'
            icon = '❌' if is_critical else '⚠️'
            html += f'<div class="agent-item {class_name}">{icon} {agent_name.replace("_", " ").title()}<small> ({status})</small>'
            if agent_name in agent_errors:
                html += f'<div class="error-details">{agent_errors[agent_name]}</div>'
            html += '</div>'
    return html

@app.get("/app", response_class=HTMLResponse)
async def app_interface():
    """Modern application interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool - Enhanced Content Creation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #1a202c;
                min-height: 100vh;
                padding: 2rem;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 2rem;
                padding: 3rem;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }
            
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .title {
                font-size: 3rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
            }
            
            .subtitle {
                color: #4a5568;
                font-size: 1.2rem;
                margin-bottom: 2rem;
            }
            
            .form-container {
                background: white;
                padding: 3rem;
                border-radius: 1.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                margin-bottom: 2rem;
            }
            
            .form-group {
                margin-bottom: 2rem;
            }
            
            .form-group.full-width {
                grid-column: 1 / -1;
            }
            
            .label {
                display: block;
                font-weight: 700;
                margin-bottom: 0.75rem;
                color: #2d3748;
                font-size: 1.1rem;
            }
            
            .input, .textarea, .select {
                width: 100%;
                padding: 1.25rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.75rem;
                font-size: 1rem;
                transition: all 0.3s ease;
                font-family: inherit;
                background: #f8fafc;
            }
            
            .input:focus, .textarea:focus, .select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
                background: white;
            }
            
            .textarea {
                resize: vertical;
                min-height: 120px;
            }
            
            .submit-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem 3rem;
                border: none;
                border-radius: 1rem;
                font-size: 1.2rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                position: relative;
                overflow: hidden;
            }
            
            .submit-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
            }
            
            .submit-btn:active {
                transform: translateY(-1px);
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 4rem;
                background: white;
                border-radius: 1.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            }
            
            .spinner {
                width: 80px;
                height: 80px;
                border: 8px solid #e2e8f0;
                border-top: 8px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 2rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading h3 {
                color: #2d3748;
                margin-bottom: 1rem;
                font-size: 1.5rem;
            }
            
            .loading p {
                color: #4a5568;
                font-size: 1.1rem;
            }
            
            .progress-steps {
                display: flex;
                justify-content: space-between;
                margin-top: 2rem;
                padding: 0 1rem;
            }
            
            .progress-step {
                flex: 1;
                text-align: center;
                padding: 0.5rem;
                font-size: 0.9rem;
                color: #718096;
            }
            
            .progress-step.active {
                color: #667eea;
                font-weight: 600;
            }
            
            @media (max-width: 768px) {
                .form-row { grid-template-columns: 1fr; }
                .container { padding: 2rem; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">🚀 Enhanced Content Creation</h1>
                <p class="subtitle">AI-Powered Content Generation with Advanced Agent Pipeline</p>
            </div>
            
            <div class="form-container">
                <form id="contentForm" onsubmit="handleSubmit(event)">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="label">Content Topic *</label>
                            <input class="input" type="text" name="topic" placeholder="e.g., best budget laptops for students" required>
                        </div>
                        <div class="form-group">
                            <label class="label">Target Audience *</label>
                            <input class="input" type="text" name="target_audience" placeholder="e.g., college students, professionals" required>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label class="label">Industry/Field *</label>
                            <select class="select" name="industry" required>
                                <option value="">Select Industry</option>
                                <option value="Technology">Technology</option>
                                <option value="Healthcare">Healthcare</option>
                                <option value="Finance">Finance</option>
                                <option value="Education">Education</option>
                                <option value="Marketing">Marketing</option>
                                <option value="E-commerce">E-commerce</option>
                                <option value="Real Estate">Real Estate</option>
                                <option value="Legal">Legal</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="label">Content Type</label>
                            <select class="select" name="content_type">
                                <option value="comprehensive_guide">Comprehensive Guide</option>
                                <option value="how_to_article">How-To Article</option>
                                <option value="comparison_review">Comparison Review</option>
                                <option value="listicle">Listicle</option>
                                <option value="case_study">Case Study</option>
                                <option value="tutorial">Tutorial</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group full-width">
                        <label class="label">Your Unique Value Proposition *</label>
                        <textarea class="textarea" name="unique_value_prop" placeholder="What makes you different? Your expertise, experience, unique approach, years in the field, certifications, success stories..." required></textarea>
                    </div>
                    
                    <div class="form-group full-width">
                        <label class="label">Customer Pain Points & Challenges *</label>
                        <textarea class="textarea" name="customer_pain_points" placeholder="What specific problems do your customers face? What keeps them up at night? What frustrates them most about this topic?" required></textarea>
                    </div>
                    
                    <button type="submit" class="submit-btn">
                        ⚡ Generate Enhanced Content Analysis
                    </button>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <h3>Processing with Enhanced AI Agents...</h3>
                <p>Running comprehensive analysis with knowledge graph integration</p>
                <div class="progress-steps">
                    <div class="progress-step active">Analyzing Topic</div>
                    <div class="progress-step">Research Reddit</div>
                    <div class="progress-step">Knowledge Graph</div>
                    <div class="progress-step">Content Generation</div>
                    <div class="progress-step">Quality Assessment</div>
                </div>
            </div>
        </div>
        
        <script>
            async function handleSubmit(event) {
                event.preventDefault();
                
                const formData = new FormData(event.target);
                const loading = document.getElementById('loading');
                const form = document.getElementById('contentForm');
                
                form.style.display = 'none';
                loading.style.display = 'block';
                
                // Simulate progress steps
                const steps = document.querySelectorAll('.progress-step');
                let currentStep = 0;
                
                const progressInterval = setInterval(() => {
                    if (currentStep < steps.length - 1) {
                        steps[currentStep].classList.remove('active');
                        currentStep++;
                        steps[currentStep].classList.add('active');
                    }
                }, 2000);
                
                try {
                    const response = await fetch('/generate', {
                        method: 'POST',
                        body: formData
                    });
                    
                    clearInterval(progressInterval);
                    
                    if (response.ok) {
                        const result = await response.text();
                        document.body.innerHTML = result;
                    } else {
                        throw new Error('Generation failed');
                    }
                } catch (error) {
                    clearInterval(progressInterval);
                    alert('Error generating content. Please try again.');
                    form.style.display = 'block';
                    loading.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """)

@app.post("/generate")
async def generate_enhanced_content(
    topic: str = Form(...),
    target_audience: str = Form(...),
    industry: str = Form(...),
    content_type: str = Form("comprehensive_guide"),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...)
):
    """Generate enhanced content with full agent analysis"""
    
    try:
        form_data = {
            "topic": topic,
            "target_audience": target_audience,
            "industry": industry,
            "content_type": content_type,
            "unique_value_prop": unique_value_prop,
            "customer_pain_points": customer_pain_points
        }
        
        # Generate comprehensive analysis
        analysis_result = await zee_orchestrator.generate_comprehensive_analysis(form_data)
        
        # Generate report HTML
        report_html = generate_report_html(analysis_result)
        
        return HTMLResponse(content=report_html)
        
    except Exception as e:
        logger.error(f"❌ Content generation failed: {e}")
        return HTMLResponse(content=f"""
        <div style="padding: 2rem; text-align: center;">
            <h1 style="color: #c53030;">❌ Content Generation Failed</h1>
            <p style="color: #4a5568; margin: 1rem 0;">Error: {str(e)}</p>
            <a href="/app" style="background: #667eea; color: white; padding: 1rem 2rem; border-radius: 0.5rem; text-decoration: none;">Try Again</a>
        </div>
        """)

def generate_report_html(analysis_result: Dict) -> str:
    """Generate comprehensive HTML report"""
    
    topic = analysis_result.get('topic', 'Unknown Topic')
    agents_used = analysis_result.get('agents_used', {})
    errors = analysis_result.get('errors', {})
    
    # Calculate success metrics
    total_agents = len(agents_used)
    successful_agents = len([a for a in agents_used.values() if a == 'success'])
    success_rate = (successful_agents / total_agents * 100) if total_agents > 0 else 0
    
    # Generate error report
    error_report = ""
    if errors:
        error_report = f"""
        <div class="error-section">
            <h3>🚨 Agent Errors Detected</h3>
            <div class="error-grid">
                {generate_error_cards(errors)}
            </div>
        </div>
        """
    
    # Generate content preview
    content_preview = analysis_result.get('generated_content', 'No content generated')
    if len(content_preview) > 1000:
        content_preview = content_preview[:1000] + "..."
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Content Analysis Report - {topic}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #1a202c;
                min-height: 100vh;
                padding: 2rem;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 2rem;
                padding: 3rem;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 3rem;
                padding-bottom: 2rem;
                border-bottom: 3px solid #e2e8f0;
            }}
            
            .title {{
                font-size: 2.5rem;
                font-weight: 900;
                color: #2d3748;
                margin-bottom: 1rem;
            }}
            
            .subtitle {{
                color: #4a5568;
                font-size: 1.2rem;
            }}
            
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                padding: 2rem;
                border-radius: 1rem;
                text-align: center;
                border: 1px solid #e2e8f0;
            }}
            
            .metric-number {{
                font-size: 2.5rem;
                font-weight: 900;
                color: #667eea;
                margin-bottom: 0.5rem;
            }}
            
            .metric-label {{
                color: #4a5568;
                font-weight: 600;
                font-size: 1.1rem;
            }}
            
            .section {{
                margin-bottom: 3rem;
                padding: 2rem;
                background: #f8fafc;
                border-radius: 1rem;
                border: 1px solid #e2e8f0;
            }}
            
            .section h3 {{
                color: #2d3748;
                margin-bottom: 1.5rem;
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .agent-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }}
            
            .agent-card {{
                padding: 1.5rem;
                border-radius: 0.75rem;
                font-weight: 600;
                text-align: center;
                border: 2px solid;
            }}
            
            .agent-card.success {{
                background: #f0fff4;
                border-color: #68d391;
                color: #2f855a;
            }}
            
            .agent-card.failed {{
                background: #fed7d7;
                border-color: #fc8181;
                color: #c53030;
            }}
            
            .error-section {{
                background: #fed7d7;
                border: 2px solid #fc8181;
                color: #c53030;
                padding: 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
            }}
            
            .error-grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 1rem;
                margin-top: 1rem;
            }}
            
            .error-card {{
                background: rgba(255, 255, 255, 0.5);
                padding: 1rem;
                border-radius: 0.5rem;
                font-size: 0.9rem;
            }}
            
            .content-preview {{
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                border: 1px solid #e2e8f0;
                max-height: 400px;
                overflow-y: auto;
                font-size: 0.9rem;
                line-height: 1.6;
            }}
            
            .actions {{
                display: flex;
                gap: 1rem;
                justify-content: center;
                margin-top: 3rem;
            }}
            
            .btn {{
                padding: 1rem 2rem;
                border: none;
                border-radius: 0.75rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
            }}
            
            .btn-primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            
            .btn-secondary {{
                background: #e2e8f0;
                color: #4a5568;
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">📊 Content Analysis Report</h1>
                <p class="subtitle">Topic: {topic}</p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-number">{success_rate:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-number">{successful_agents}</div>
                    <div class="metric-label">Agents Successful</div>
                </div>
                <div class="metric-card">
                    <div class="metric-number">{len(errors)}</div>
                    <div class="metric-label">Errors Detected</div>
                </div>
            </div>
            
            {error_report}
            
            <div class="section">
                <h3>🤖 Agent Performance Report</h3>
                <div class="agent-grid">
                    {generate_agent_performance_cards(agents_used)}
                </div>
            </div>
            
            <div class="section">
                <h3>📝 Generated Content Preview</h3>
                <div class="content-preview">
                    {content_preview.replace(chr(10), '<br>')}
                </div>
            </div>
            
            <div class="actions">
                <a href="/app" class="btn btn-secondary">🔄 Create New Analysis</a>
                <a href="/chat?topic={topic}" class="btn btn-primary">💬 Chat About Results</a>
            </div>
        </div>
    </body>
    </html>
    """

def generate_error_cards(errors: Dict) -> str:
    """Generate error cards HTML"""
    cards = ""
    for agent, error in errors.items():
        cards += f"""
        <div class="error-card">
            <strong>{agent.replace('_', ' ').title()}</strong><br>
            <small>{error}</small>
        </div>
        """
    return cards

def generate_agent_performance_cards(agents_used: Dict) -> str:
    """Generate agent performance cards HTML"""
    cards = ""
    for agent, status in agents_used.items():
        icon = "✅" if status == "success" else "❌"
        class_name = "success" if status == "success" else "failed"
        cards += f"""
        <div class="agent-card {class_name}">
            {icon} {agent.replace('_', ' ').title()}
            <br><small>{status}</small>
        </div>
        """
    return cards

@app.get("/status")
async def get_agent_status():
    """Get detailed agent status"""
    return JSONResponse(content={
        "agent_status": agent_status,
        "agent_errors": agent_errors,
        "loaded_agents": len([k for k, v in agent_status.items() if v in ['loaded', 'loaded_alt']]),
        "failed_agents": len([k for k, v in agent_status.items() if 'failed' in v]),
        "total_agents": len(agent_status)
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 Starting Enhanced Zee SEO Tool v4.0...")
    print("=" * 60)
    print(f"✅ Agent Loading Report:")
    for agent, status in agent_status.items():
        icon = "✅" if status in ['loaded', 'loaded_alt'] else "❌"
        print(f"  {icon} {agent}: {status}")
    print("=" * 60)
    print(f"📊 Summary: {len([k for k, v in agent_status.items() if v in ['loaded', 'loaded_alt']])} loaded, {len([k for k, v in agent_status.items() if 'failed' in v])} failed")
    print("=" * 60)
    
    if agent_errors:
        print("🚨 CRITICAL ERRORS TO FIX:")
        for agent, error in agent_errors.items():
            print(f"  ❌ {agent}: {error}")
        print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
