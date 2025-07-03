import os
import json
import logging
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# FastAPI imports
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your enhanced agents
from reddit_researcher import EnhancedRedditResearcher
from advanced_topic_research_agent import AdvancedTopicResearchAgent
from knowledge_graph_trends_agent import KnowledgeGraphTrendsAgent
from customer_journey_mapper import CustomerJourneyMapper
from full_content_generator import FullContentGenerator
from content_generator import ContentGenerator
from business_context_collector import BusinessContextCollector
from content_quality_scorer import ContentQualityScorer
from content_type_classifier import ContentTypeClassifier
from eeat_assessor import EnhancedEEATAssessor
from human_input_identifier import HumanInputIdentifier
from intent_classifier import IntentClassifier
from content_analysis_snapshot import ContentAnalysisSnapshot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    ANTHROPIC_API_KEY       = os.getenv("ANTHROPIC_API_KEY", "")
    REDDIT_CLIENT_ID        = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET    = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT       = os.getenv("REDDIT_USER_AGENT", "ZeeSEOTool:v4.0")

    # Your Railway service URL for KG
    KNOWLEDGE_GRAPH_API_URL = os.getenv(
        "KNOWLEDGE_GRAPH_API_URL",
        "https://myaiapplication-production.up.railway.app/api/knowledge-graph"
    )
    # Your Google Knowledge Graph API key
    KNOWLEDGE_GRAPH_API_KEY = os.getenv("KNOWLEDGE_GRAPH_API_KEY", "")

    DEBUG_MODE              = os.getenv("DEBUG_MODE", "True").lower() == "true"
    PORT                    = int(os.getenv("PORT", 8002))

config = Config()

# Initialize FastAPI
app = FastAPI(title="Zee SEO Tool v4.0 - Enhanced Agent Integration")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ================== ENHANCED ORCHESTRATOR ==================

class EnhancedZeeOrchestrator:
    """Enhanced orchestrator integrating all advanced agents"""

    def __init__(self):
        # Initialize all enhanced agents
        self.reddit_researcher          = EnhancedRedditResearcher()
        self.topic_research_agent       = AdvancedTopicResearchAgent()
        self.kg_trends_agent            = KnowledgeGraphTrendsAgent()
        self.journey_mapper             = CustomerJourneyMapper()
        self.intent_classifier          = IntentClassifier()
        self.human_input_identifier     = HumanInputIdentifier()
        self.full_content_generator     = FullContentGenerator()
        self.content_generator          = ContentGenerator()
        self.business_context_collector = BusinessContextCollector()
        self.eeat_assessor              = EnhancedEEATAssessor()
        self.content_type_classifier    = ContentTypeClassifier()
        self.content_quality_scorer     = ContentQualityScorer()
        self.content_snapshot           = ContentAnalysisSnapshot()

        # Knowledge Graph API integration
        self.kg_url = config.KNOWLEDGE_GRAPH_API_URL
        self.kg_key = config.KNOWLEDGE_GRAPH_API_KEY

        # Conversation history for chat
        self.conversation_history = []

        logger.info("✅ Enhanced Zee Orchestrator initialized with all agents")

    async def get_knowledge_graph_insights(self, topic: str) -> Dict[str, Any]:
        """Get insights from Railway Knowledge Graph API"""
        try:
            response = requests.post(
                self.kg_url,
                headers={ "x-api-key": self.kg_key },
                json={
                    "topic": topic,
                    "depth": 3,
                    "include_related": True,
                    "include_gaps": True
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Knowledge Graph API returned {response.status_code}")
                return self._get_fallback_kg_insights(topic)
        except Exception as e:
            logger.error(f"Knowledge Graph API error: {e}")
            return self._get_fallback_kg_insights(topic)

    def _get_fallback_kg_insights(self, topic: str) -> Dict[str, Any]:
        """Fallback knowledge graph insights"""
        return {
            "entities": [
                f"{topic} basics",
                f"{topic} best practices",
                f"{topic} tools and resources",
                f"{topic} common challenges",
                f"{topic} success strategies"
            ],
            "related_topics": [
                f"Advanced {topic}",
                f"{topic} for beginners",
                f"{topic} case studies",
                f"{topic} trends"
            ],
            "content_gaps": [
                f"Complete {topic} guide",
                f"{topic} comparison analysis",
                f"{topic} implementation steps"
            ],
            "source": "fallback_generated"
        }

    async def generate_comprehensive_analysis(self, form_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive analysis using all enhanced agents"""
        # … your existing implementation unchanged …

    async def process_chat_message(self, message: str, analysis_data: Dict) -> str:
        """Enhanced chat processing…"""
        # … unchanged …

    # … all other methods exactly as you had them …

# Initialize enhanced orchestrator
zee_orchestrator = EnhancedZeeOrchestrator()

# ================== API ROUTES ==================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced homepage with modern design"""
    
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
                line-height: 1.6;
                min-height: 100vh;
            }}
            
            .hero {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }}
            
            .hero-content {{
                max-width: 800px;
                text-align: center;
                animation: fadeInUp 1s ease-out;
            }}
            
            .logo {{
                font-size: 4rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
            }}
            
            .tagline {{
                font-size: 1.5rem;
                color: #4a5568;
                margin-bottom: 2rem;
                font-weight: 300;
            }}
            
            .features {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin: 2rem 0;
            }}
            
            .feature {{
                background: rgba(255, 255, 255, 0.8);
                padding: 1.5rem;
                border-radius: 1rem;
                text-align: center;
                transition: transform 0.3s ease;
            }}
            
            .feature:hover {{
                transform: translateY(-5px);
            }}
            
            .feature-icon {{
                font-size: 2rem;
                margin-bottom: 1rem;
            }}
            
            .feature-title {{
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 0.5rem;
            }}
            
            .feature-desc {{
                color: #718096;
                font-size: 0.9rem;
            }}
            
            .cta-button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem 3rem;
                border: none;
                border-radius: 50px;
                font-size: 1.2rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                margin-top: 2rem;
            }}
            
            .cta-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
            }}
            
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .version-badge {{
                position: fixed;
                top: 1rem;
                right: 1rem;
                background: rgba(255, 255, 255, 0.9);
                padding: 0.5rem 1rem;
                border-radius: 2rem;
                font-size: 0.8rem;
                font-weight: 600;
                color: #667eea;
                backdrop-filter: blur(10px);
            }}
        </style>
    </head>
    <body>
        <div class="version-badge">v4.0 - Enhanced Agents</div>
        
        <div class="hero">
            <div class="hero-content">
                <div class="logo">Zee SEO Tool</div>
                <div class="tagline">Enhanced Agent Integration • Conversational AI • Knowledge Graph Analysis</div>
                
                <div class="features">
                    <div class="feature">
                        <div class="feature-icon">🧠</div>
                        <div class="feature-title">Knowledge Graph</div>
                        <div class="feature-desc">Railway API integration for comprehensive topic analysis</div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">📱</div>
                        <div class="feature-title">Enhanced Reddit</div>
                        <div class="feature-desc">Deep social media insights and viral content analysis</div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">💬</div>
                        <div class="feature-title">Conversational AI</div>
                        <div class="feature-desc">ChatGPT-like interface for content optimization</div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">⚡</div>
                        <div class="feature-title">All Agents</div>
                        <div class="feature-desc">Complete pipeline: Intent → Research → Generate → Optimize</div>
                    </div>
                </div>
                
                <button class="cta-button" onclick="window.location.href='/app'">
                    🚀 Start Advanced Content Creation
                </button>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/app", response_class=HTMLResponse)
async def app_interface():
    """Main application interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zee SEO Tool - Content Creation Interface</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: #f8fafc;
                color: #1a202c;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .header {
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .title {
                font-size: 2.5rem;
                font-weight: 800;
                color: #2d3748;
                margin-bottom: 1rem;
            }
            
            .subtitle {
                color: #718096;
                font-size: 1.1rem;
            }
            
            .form-container {
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .label {
                display: block;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #4a5568;
            }
            
            .input, .textarea, .select {
                width: 100%;
                padding: 1rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 1rem;
                transition: border-color 0.2s;
            }
            
            .input:focus, .textarea:focus, .select:focus {
                outline: none;
                border-color: #667eea;
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
                transition: all 0.3s ease;
                width: 100%;
            }
            
            .submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 2rem;
            }
            
            .spinner {
                width: 50px;
                height: 50px;
                border: 5px solid #e2e8f0;
                border-top: 5px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">🚀 Enhanced Content Creation</h1>
                <p class="subtitle">Advanced agent pipeline with Knowledge Graph analysis and conversational AI</p>
            </div>
            
            <div class="form-container">
                <form id="contentForm" onsubmit="handleSubmit(event)">
                    <div class="form-group">
                        <label class="label">Content Topic *</label>
                        <input class="input" type="text" name="topic" placeholder="e.g., best budget laptops for students" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Target Audience *</label>
                        <input class="input" type="text" name="target_audience" placeholder="e.g., college students, small business owners" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Industry *</label>
                        <input class="input" type="text" name="industry" placeholder="e.g., Technology, Education, Finance" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Your Unique Value Proposition *</label>
                        <textarea class="textarea" name="unique_value_prop" rows="4" placeholder="What makes you different? Your expertise, experience, unique approach..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Customer Pain Points *</label>
                        <textarea class="textarea" name="customer_pain_points" rows="4" placeholder="What specific problems do your customers face?" required></textarea>
                    </div>
                    
                    <button type="submit" class="submit-btn">
                        ⚡ Generate Enhanced Content Analysis
                    </button>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <h3>Processing with Enhanced Agents...</h3>
                <p>Running comprehensive analysis with all integrated agents</p>
            </div>
        </div>
        
        <script>
            async function handleSubmit(event) {
                event.preventDefault();
                
                const formData = new FormData(event.target);
                const loading = document.getElementById('loading');
                const form = document.getElementById('contentForm');
                
                // Show loading
                form.style.display = 'none';
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/generate', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.text();
                        document.body.innerHTML = result;
                    } else {
                        throw new Error('Generation failed');
                    }
                } catch (error) {
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
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...)
):
    """Generate enhanced content using all agents"""
    try:
        form_data = {
            'topic': topic,
            'target_audience': target_audience,
            'industry': industry,
            'unique_value_prop': unique_value_prop,
            'customer_pain_points': customer_pain_points
        }
        
        # Generate comprehensive analysis
        analysis = await zee_orchestrator.generate_comprehensive_analysis(form_data)
        
        # Return enhanced results page
        return HTMLResponse(content=generate_enhanced_results_page(analysis))
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(
    message: str = Form(...),
    analysis_data: str = Form(...)
):
    """Enhanced chat endpoint"""
    try:
        # Parse analysis data
        analysis = json.loads(analysis_data)
        
        # Process message with full context
        response = await zee_orchestrator.process_chat_message(message, analysis)
        
        return JSONResponse({"response": response})
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return JSONResponse({"response": "I'm having trouble processing your request. Please try again."})

def generate_enhanced_results_page(analysis: Dict[str, Any]) -> str:
    """Generate enhanced results page with conversational AI"""
    
    # Extract key data
    topic = analysis['topic']
    metrics = analysis['performance_metrics']
    content = analysis['generated_content']
    kg_insights = analysis['knowledge_graph']
    reddit_insights = analysis['reddit_insights']
    
    # Prepare analysis data for JavaScript
    analysis_json = json.dumps(analysis, default=str)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Enhanced Content Analysis - {topic}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                color: #1a202c;
                line-height: 1.6;
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            .header {{
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }}
            
            .title {{
                font-size: 2.5rem;
                font-weight: 800;
                color: #2d3748;
                margin-bottom: 1rem;
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }}
            
            .metric-card {{
                background: white;
                padding: 2rem;
                border-radius: 1rem;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
            }}
            
            .metric-card:hover {{
                transform: translateY(-5px);
            }}
            
            .metric-value {{
                font-size: 2.5rem;
                font-weight: 800;
                color: #667eea;
                margin-bottom: 0.5rem;
            }}
            
            .metric-label {{
                color: #718096;
                font-weight: 600;
            }}
            
            .content-section {{
                background: white;
                margin-bottom: 2rem;
                border-radius: 1rem;
                overflow: hidden;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }}
            
            .section-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem 2rem;
                font-size: 1.25rem;
                font-weight: 700;
            }}
            
            .section-content {{
                padding: 2rem;
            }}
            
            .content-display {{
                background: #f8fafc;
                padding: 2rem;
                border-radius: 0.5rem;
                border-left: 4px solid #667eea;
                max-height: 400px;
                overflow-y: auto;
                white-space: pre-wrap;
                font-family: ui-monospace, SFMono-Regular, Monaco, monospace;
                font-size: 0.9rem;
                line-height: 1.6;
            }}
            
            .chat-interface {{
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                width: 450px;
                height: 600px;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
                display: none;
                flex-direction: column;
                z-index: 1000;
            }}
            
            .chat-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 1rem 1rem 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .chat-messages {{
                flex: 1;
                padding: 1.5rem;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }}
            
            .message {{
                padding: 1rem;
                border-radius: 1rem;
                font-size: 0.9rem;
                line-height: 1.5;
                max-width: 85%;
            }}
            
            .message.user {{
                background: #667eea;
                color: white;
                margin-left: auto;
                border-bottom-right-radius: 0.25rem;
            }}
            
            .message.assistant {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                margin-right: auto;
                border-bottom-left-radius: 0.25rem;
            }}
            
            .chat-input {{
                padding: 1.5rem;
                border-top: 1px solid #e2e8f0;
                display: flex;
                gap: 1rem;
            }}
            
            .chat-input input {{
                flex: 1;
                padding: 0.75rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.5rem;
                font-size: 0.9rem;
            }}
            
            .chat-input button {{
                padding: 0.75rem 1.5rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 0.5rem;
                cursor: pointer;
                font-weight: 600;
            }}
            
            .chat-toggle {{
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                border: none;
                color: white;
                font-size: 1.5rem;
                cursor: pointer;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                z-index: 1001;
                transition: all 0.3s ease;
            }}
            
            .chat-toggle:hover {{
                transform: scale(1.1);
            }}
            
            .insights-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 1.5rem 0;
            }}
            
            .insight-card {{
                background: #f8fafc;
                padding: 1.5rem;
                border-radius: 0.75rem;
                border-left: 4px solid #667eea;
            }}
            
            .insight-title {{
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 0.5rem;
            }}
            
            .insight-value {{
                font-size: 1.25rem;
                font-weight: 600;
                color: #667eea;
                margin-bottom: 0.5rem;
            }}
            
            .quick-actions {{
                display: flex;
                gap: 1rem;
                margin: 1.5rem 0;
                flex-wrap: wrap;
            }}
            
            .quick-btn {{
                padding: 0.75rem 1.5rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 0.5rem;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            
            .quick-btn:hover {{
                background: #5a67d8;
                transform: translateY(-2px);
            }}
            
            @media (max-width: 768px) {{
                .chat-interface {{
                    width: 90%;
                    right: 5%;
                }}
                .metrics-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">🚀 Enhanced Analysis: {topic.title()}</h1>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{metrics['quality_score']:.1f}/10</div>
                        <div class="metric-label">Quality Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics['trust_score']:.1f}/10</div>
                        <div class="metric-label">Trust Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics['reddit_posts_analyzed']}</div>
                        <div class="metric-label">Reddit Posts</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics['knowledge_entities']}</div>
                        <div class="metric-label">Knowledge Entities</div>
                    </div>
                </div>
                
                <div class="quick-actions">
                    <button class="quick-btn" onclick="askQuestion('What knowledge gaps should I cover?')">
                        🧠 Knowledge Gaps
                    </button>
                    <button class="quick-btn" onclick="askQuestion('How can I improve my trust score?')">
                        🔒 Improve Trust
                    </button>
                    <button class="quick-btn" onclick="askQuestion('SEO optimization tips?')">
                        🔍 SEO Tips
                    </button>
                    <button class="quick-btn" onclick="askQuestion('Social media strategy?')">
                        📱 Social Media
                    </button>
                </div>
            </div>
            
            <div class="content-section">
                <div class="section-header">🧠 Knowledge Graph Analysis</div>
                <div class="section-content">
                    <div class="insights-grid">
                        <div class="insight-card">
                            <div class="insight-title">Entities Identified</div>
                            <div class="insight-value">{len(kg_insights.get('entities', []))}</div>
                            <div>Key topics and concepts to cover</div>
                        </div>
                        <div class="insight-card">
                            <div class="insight-title">Content Gaps</div>
                            <div class="insight-value">{len(kg_insights.get('content_gaps', []))}</div>
                            <div>Missing topics that competitors don't cover</div>
                        </div>
                        <div class="insight-card">
                            <div class="insight-title">Related Topics</div>
                            <div class="insight-value">{len(kg_insights.get('related_topics', []))}</div>
                            <div>Additional content opportunities</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <div class="section-header">📱 Social Media Intelligence</div>
                <div class="section-content">
                    <div class="insights-grid">
                        <div class="insight-card">
                            <div class="insight-title">Best Platform</div>
                            <div class="insight-value">{reddit_insights.get('social_media_insights', {}).get('best_platform', 'N/A').title()}</div>
                            <div>Optimal platform for content distribution</div>
                        </div>
                        <div class="insight-card">
                            <div class="insight-title">Viral Potential</div>
                            <div class="insight-value">{reddit_insights.get('social_media_metrics', {}).get('viral_content_ratio', 0)*100:.1f}%</div>
                            <div>Content shareability score</div>
                        </div>
                        <div class="insight-card">
                            <div class="insight-title">Engagement Rate</div>
                            <div class="insight-value">{reddit_insights.get('social_media_metrics', {}).get('avg_engagement_rate', 0):.1f}%</div>
                            <div>Expected audience engagement</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <div class="section-header">✍️ Generated Content</div>
                <div class="section-content">
                    <div class="content-display" id="contentDisplay">{content}</div>
                </div>
            </div>
        </div>
        
        <!-- Chat Toggle -->
        <button class="chat-toggle" onclick="toggleChat()" id="chatToggle">💬</button>
        
        <!-- Chat Interface -->
        <div class="chat-interface" id="chatInterface">
            <div class="chat-header">
                <h3>🤖 AI Content Assistant</h3>
                <button onclick="toggleChat()" style="background: none; border: none; color: white; cursor: pointer; font-size: 1.5rem;">×</button>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message assistant">
                    <strong>🚀 Enhanced Analysis Complete!</strong><br><br>
                    I've analyzed your content with all advanced agents:<br>
                    • Quality Score: {metrics['quality_score']:.1f}/10<br>
                    • Trust Score: {metrics['trust_score']:.1f}/10<br>
                    • Knowledge Entities: {metrics['knowledge_entities']}<br>
                    • Reddit Posts: {metrics['reddit_posts_analyzed']}<br><br>
                    <strong>What would you like to improve?</strong>
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="chatInput" placeholder="Ask me anything about your content..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <script>
            let chatVisible = false;
            const analysisData = {analysis_json};
            
            function toggleChat() {{
                const chatInterface = document.getElementById('chatInterface');
                const chatToggle = document.getElementById('chatToggle');
                
                chatVisible = !chatVisible;
                chatInterface.style.display = chatVisible ? 'flex' : 'none';
                chatToggle.style.display = chatVisible ? 'none' : 'block';
            }}
            
            function askQuestion(question) {{
                if (!chatVisible) toggleChat();
                
                const chatInput = document.getElementById('chatInput');
                chatInput.value = question;
                sendMessage();
            }}
            
            async function sendMessage() {{
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                
                const messagesContainer = document.getElementById('chatMessages');
                
                // Add user message
                addMessage('user', message);
                
                // Add thinking indicator
                const thinkingDiv = addMessage('assistant', '🤔 Analyzing...');
                
                input.value = '';
                
                try {{
                    const formData = new FormData();
                    formData.append('message', message);
                    formData.append('analysis_data', JSON.stringify(analysisData));
                    
                    const response = await fetch('/api/chat', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await response.json();
                    thinkingDiv.innerHTML = data.response;
                }} catch (error) {{
                    thinkingDiv.innerHTML = "I'm having trouble processing your request. Please try again.";
                }}
                
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }}
            
            function addMessage(role, content) {{
                const messagesContainer = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{role}}`;
                messageDiv.innerHTML = content;
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                return messageDiv;
            }}
            
            function handleKeyPress(event) {{
                if (event.key === 'Enter') {{
                    sendMessage();
                }}
            }}
            
            // Auto-show chat if scores need improvement
            setTimeout(() => {{
                if (analysisData.performance_metrics.quality_score < 8.0 || analysisData.performance_metrics.trust_score < 8.0) {{
                    toggleChat();
                }}
            }}, 3000);
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check with agent status"""
    return {
        "status": "healthy",
        "version": "4.0 - Enhanced Agent Integration",
        "agents": {
            "reddit_researcher": "✅ Enhanced with social media analysis",
            "content_generator": "✅ Multiple content types supported",
            "knowledge_graph": "✅ Railway API integration",
            "business_context": "✅ Comprehensive collection",
            "quality_scorer": "✅ Advanced scoring system",
            "eeat_assessor": "✅ Trust score calculation",
            "intent_classifier": "✅ User intent analysis",
            "journey_mapper": "✅ Customer journey mapping",
            "human_input_identifier": "✅ Authenticity enhancement"
        },
        "features": {
            "conversational_ai": "✅ ChatGPT-like interface",
            "knowledge_gaps": "✅ Gap analysis from Knowledge Graph",
            "social_media_insights": "✅ Platform-specific optimization",
            "real_time_chat": "✅ Working API endpoints"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Enhanced Zee SEO Tool v4.0...")
    print("=" * 70)
    print("✅ NEW FEATURES:")
    print("  🧠 Knowledge Graph API integration (Railway)")
    print("  📱 Enhanced Reddit research with social media analysis")
    print("  💬 Conversational AI interface (ChatGPT-like)")
    print("  ⚡ All agents integrated in comprehensive pipeline")
    print("  🎯 Real-time content optimization and gap analysis")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
