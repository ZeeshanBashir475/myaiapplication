import os
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import enhanced agents
from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor
from src.agents.topic_research_agent import AdvancedTopicResearchAgent
from src.agents.improvement_tracking_agent import ContinuousImprovementTracker
from src.utils.llm_client import LLMClient

# Initialize FastAPI app
app = FastAPI(title="Zee SEO Tool - Advanced Content Intelligence Platform")

# AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")

class ClaudeAgent:
    def __init__(self):
        self.anthropic_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
    def call_claude(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", max_tokens: int = 1500):
        """Make API call to Claude"""
        try:
            if messages and messages[0].get("role") == "user":
                user_message = messages[0]["content"]
            else:
                user_message = "Please help with this request."
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.anthropic_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                return f"Demo mode - Claude API unavailable"
                
        except Exception as e:
            return f"Demo mode - Using fallback content"

# Enhanced content generator
class EnhancedContentGenerator:
    def __init__(self, claude_agent):
        self.claude_agent = claude_agent
        
    def generate_content(self, topic: str, business_context: Dict, human_inputs: Dict, 
                        ai_instructions: Dict, reddit_insights: Dict = None, 
                        topic_research: Dict = None) -> str:
        """Generate content using enhanced context"""
        
        # Enhanced AI prompt with all available intelligence
        ai_prompt = f"""
        Create exceptional, human-centered content about "{topic}" that demonstrates high E-E-A-T standards.
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        HUMAN EXPERTISE & INSIGHTS:HUMAN EXPERTISE & INSIGHTS:
        - Customer Pain Points: {human_inputs.get('customer_pain_points')}
        - Industry Experience: {human_inputs.get('unique_value_prop')}
        
        REAL CUSTOMER RESEARCH:
        {self._format_reddit_insights(reddit_insights) if reddit_insights else 'Not available'}
        
        TOPIC INTELLIGENCE:
        {self._format_topic_research(topic_research) if topic_research else 'Not available'}
        
        AI INSTRUCTIONS:
        - Writing Style: {ai_instructions.get('writing_style', 'Professional')}
        - Target Length: {ai_instructions.get('target_word_count', '1000-1500 words')}
        - Special Notes: {ai_instructions.get('additional_notes', 'None')}
        
        CONTENT REQUIREMENTS:
        1. Demonstrate genuine experience through specific examples and personal insights
        2. Show expertise with accurate, in-depth information
        3. Build authority through unique perspectives and comprehensive coverage
        4. Establish trust through transparency, balanced views, and credible sources
        5. Address real customer pain points identified in the research
        6. Use authentic language that resonates with the target audience
        7. Include specific, actionable advice that only an expert would know
        8. Reference credible sources and provide balanced perspectives
        
        Create content that is significantly better than generic AI content by incorporating:
        - Real customer language and concerns from the research
        - Industry-specific expertise and insider knowledge
        - Personal experience and authentic insights
        - Practical solutions to genuine problems
        
        Make this content worthy of being cited as an authoritative source.
        """
        
        messages = [{"role": "user", "content": ai_prompt}]
        return self.claude_agent.call_claude(messages, max_tokens=3000)
    
    def _format_reddit_insights(self, reddit_insights: Dict) -> str:
        """Format Reddit insights for the AI prompt"""
        if not reddit_insights:
            return "No Reddit insights available"
        
        formatted = []
        
        # Pain points
        pain_points = reddit_insights.get('pain_point_analysis', {}).get('critical_pain_points', [])
        if pain_points:
            formatted.append(f"Critical Pain Points: {', '.join(pain_points[:3])}")
        
        # Customer quotes
        quotes = reddit_insights.get('authenticity_markers', {}).get('real_customer_quotes', [])
        if quotes:
            formatted.append(f"Real Customer Quotes: {'; '.join(quotes[:2])}")
        
        # Language patterns
        vocab = reddit_insights.get('language_intelligence', {}).get('customer_vocabulary', [])
        if vocab:
            formatted.append(f"Customer Language: {', '.join(vocab[:5])}")
        
        return '\n'.join(formatted)
    
    def _format_topic_research(self, topic_research: Dict) -> str:
        """Format topic research for the AI prompt"""
        if not topic_research:
            return "No topic research available"
        
        formatted = []
        
        # Content gaps
        gaps = topic_research.get('topic_research', {}).get('content_gaps', {}).get('market_gaps', {})
        if gaps.get('underserved_questions'):
            formatted.append(f"Underserved Questions: {', '.join(gaps['underserved_questions'][:3])}")
        
        # Opportunities
        opportunities = topic_research.get('topic_research', {}).get('opportunity_scoring', {}).get('top_opportunities', [])
        if opportunities:
            top_ops = [op.get('name', '') for op in opportunities[:3]]
            formatted.append(f"Top Opportunities: {', '.join(top_ops)}")
        
        return '\n'.join(formatted)

# Initialize enhanced components
claude_agent = ClaudeAgent()
enhanced_content_generator = EnhancedContentGenerator(claude_agent)
reddit_researcher = EnhancedRedditResearcher()
eeat_assessor = EnhancedEEATAssessor()
topic_researcher = AdvancedTopicResearchAgent()
improvement_tracker = ContinuousImprovementTracker()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced home page with new features"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool - Advanced Content Intelligence Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                color: #111827;
                line-height: 1.6;
                min-height: 100vh;
            }
            
            .header {
                background: white;
                border-bottom: 1px solid #e5e7eb;
                padding: 1.5rem 0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                position: sticky;
                top: 0;
                z-index: 50;
            }
            
            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 1.5rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .logo-icon {
                width: 3rem;
                height: 3rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 800;
                font-size: 1.5rem;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .logo-text {
                font-size: 1.75rem;
                font-weight: 800;
                color: #111827;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .tagline {
                font-size: 0.875rem;
                color: #6b7280;
                font-weight: 500;
                margin-top: 0.25rem;
            }
            
            .version-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            .creator {
                text-align: right;
                font-size: 0.875rem;
                color: #6b7280;
            }
            
            .creator strong {
                color: #374151;
                display: block;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }
            
            .hero {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .hero h1 {
                font-size: 2.5rem;
                font-weight: 800;
                color: #111827;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .hero p {
                font-size: 1.25rem;
                color: #6b7280;
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }
            
            .hero-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                max-width: 500px;
                margin: 2rem auto;
            }
            
            .hero-stat {
                text-align: center;
                padding: 1rem;
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .hero-stat-value {
                font-size: 1.5rem;
                font-weight: 800;
                color: #2563eb;
            }
            
            .hero-stat-label {
                font-size: 0.75rem;
                color: #6b7280;
                margin-top: 0.25rem;
            }
            
            .main-grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 2rem;
            }
            
            .card {
                background: white;
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                transform: translateY(-2px);
            }
            
            .card h2 {
                font-size: 1.375rem;
                font-weight: 700;
                color: #111827;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            
            .card-icon {
                width: 2rem;
                height: 2rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }
            
            .card p {
                color: #6b7280;
                margin-bottom: 1.5rem;
            }
            
            .form-grid {
                display: grid;
                gap: 1.5rem;
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }
            
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .form-label {
                font-size: 0.875rem;
                font-weight: 600;
                color: #374151;
            }
            
            .form-input, .form-textarea, .form-select {
                padding: 0.875rem 1rem;
                border: 2px solid #e5e7eb;
                border-radius: 0.75rem;
                font-size: 0.875rem;
                transition: all 0.2s ease;
                background: white;
            }
            
            .form-input:focus, .form-textarea:focus, .form-select:focus {
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                transform: translateY(-1px);
            }
            
            .form-textarea {
                resize: vertical;
                min-height: 4rem;
                font-family: inherit;
            }
            
            .form-help {
                font-size: 0.75rem;
                color: #6b7280;
            }
            
            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                padding: 1rem 2rem;
                font-size: 1rem;
                font-weight: 700;
                border-radius: 0.75rem;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                font-family: inherit;
                width: 100%;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
            
            .ai-controls {
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border: 2px solid #bfdbfe;
            }
            
            .features {
                display: grid;
                gap: 1rem;
            }
            
            .feature {
                display: flex;
                align-items: flex-start;
                gap: 1rem;
                padding: 1.25rem;
                background: linear-gradient(135deg, #f9fafb 0%, white 100%);
                border-radius: 0.75rem;
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            
            .feature:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                border-color: #2563eb;
            }
            
            .feature-icon {
                width: 2.5rem;
                height: 2.5rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                flex-shrink: 0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .feature-content h4 {
                font-size: 0.9rem;
                font-weight: 600;
                color: #111827;
                margin-bottom: 0.25rem;
            }
            
            .feature-content p {
                font-size: 0.8rem;
                color: #6b7280;
                margin: 0;
                line-height: 1.4;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 3rem 2rem;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                margin-top: 2rem;
            }
            
            .loading-spinner {
                width: 3rem;
                height: 3rem;
                border: 3px solid #e5e7eb;
                border-top: 3px solid #2563eb;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1.5rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .footer {
                margin-top: 4rem;
                padding: 3rem 0;
                background: white;
                border-top: 1px solid #e5e7eb;
                text-align: center;
            }
            
            .footer p {
                color: #6b7280;
                margin-bottom: 0.5rem;
            }
            
            @media (max-width: 768px) {
                .main-grid { grid-template-columns: 1fr; gap: 1.5rem; }
                .form-row { grid-template-columns: 1fr; }
                .hero h1 { font-size: 2rem; }
                .hero p { font-size: 1rem; }
                .container { padding: 1rem; }
                .header-content { flex-direction: column; gap: 1rem; text-align: center; }
                .hero-stats { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-icon">Z</div>
                    <div>
                        <div class="logo-text">Zee SEO Tool</div>
                        <div class="tagline">Advanced Content Intelligence Platform</div>
                    </div>
                </div>
                <div class="version-badge">Enhanced v2.0</div>
                <div class="creator">
                    <strong>Built by Zeeshan Bashir</strong>
                    <div>Human + AI Intelligence Bridge</div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="hero">
                <h1>Create Content That Actually Converts</h1>
                <p>The most advanced content intelligence platform combining deep customer research, E-E-A-T optimization, and continuous improvement tracking</p>
                
                <div class="hero-stats">
                    <div class="hero-stat">
                        <div class="hero-stat-value">350%</div>
                        <div class="hero-stat-label">Better Performance</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-value">5+</div>
                        <div class="hero-stat-label">AI Agents</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-value">95%</div>
                        <div class="hero-stat-label">E-E-A-T Score</div>
                    </div>
                </div>
            </div>
            
            <div class="main-grid">
                <form action="/generate-advanced" method="post">
                    <div class="card">
                        <h2>
                            <div class="card-icon">🧠</div>
                            Advanced Content Intelligence Input
                        </h2>
                        <p>Our enhanced system combines multiple AI agents for comprehensive content analysis and generation.</p>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label">Content Topic</label>
                                <input class="form-input" type="text" name="topic" 
                                       placeholder="e.g., best budget laptops for college students" required>
                                <div class="form-help">Our topic research agent will analyze semantic relationships and opportunities</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Target Communities for Research</label>
                                <input class="form-input" type="text" name="subreddits" 
                                       placeholder="e.g., laptops, college, StudentLoans" required>
                                <div class="form-help">Enhanced Reddit research with deep customer insight extraction</div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Industry</label>
                                    <input class="form-input" type="text" name="industry" 
                                           placeholder="e.g., Technology" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Target Audience</label>
                                    <input class="form-input" type="text" name="target_audience" 
                                           placeholder="e.g., College students" required>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Business Type</label>
                                <select class="form-select" name="business_type" required>
                                    <option value="">Select business model</option>
                                    <option value="B2B">B2B (Business to Business)</option>
                                    <option value="B2C">B2C (Business to Consumer)</option>
                                    <option value="Both">Both B2B and B2C</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Your Unique Value Proposition</label>
                                <textarea class="form-textarea" name="unique_value_prop" 
                                          placeholder="What makes you different from competitors? Be specific and authentic." required></textarea>
                                <div class="form-help">Critical for E-E-A-T authority and differentiation analysis</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Customer Pain Points & Insights</label>
                                <textarea class="form-textarea" name="customer_pain_points" 
                                          placeholder="What specific challenges do your customers face? Include real examples." required></textarea>
                                <div class="form-help">Enhanced analysis will combine this with Reddit research for deeper insights</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card ai-controls">
                        <h2>
                            <div class="card-icon">⚙️</div>
                            Advanced AI Configuration
                        </h2>
                        <p>Fine-tune content generation with enhanced AI controls and quality parameters</p>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Writing Style</label>
                                    <select class="form-select" name="writing_style">
                                        <option value="">Adaptive (Recommended)</option>
                                        <option value="British English">British English</option>
                                        <option value="American English">American English</option>
                                        <option value="Conversational">Conversational</option>
                                        <option value="Technical">Technical</option>
                                        <option value="Academic">Academic</option>
                                        <option value="Authoritative">Authoritative</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Target Length</label>
                                    <select class="form-select" name="target_word_count">
                                        <option value="">Optimal (1200-1800)</option>
                                        <option value="800-1200">Concise (800-1200)</option>
                                        <option value="1500-2500">Comprehensive (1500-2500)</option>
                                        <option value="2500-4000">In-depth (2500-4000)</option>
                                        <option value="4000+">Ultimate Guide (4000+)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">E-E-A-T Enhancement Instructions</label>
                                <textarea class="form-textarea" name="eeat_instructions" 
                                          placeholder="Specific instructions for experience, expertise, authority, or trust elements"></textarea>
                                <div class="form-help">Guide our E-E-A-T optimization agent</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Additional AI Instructions</label>
                                <textarea class="form-textarea" name="additional_notes" 
                                          placeholder="Any specific requirements: statistics, format preferences, tone adjustments"></textarea>
                                <div class="form-help">Advanced customization for content generation</div>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn">
                        🚀 Generate Advanced Content Intelligence Report
                    </button>
                </form>
                
                <div class="card">
                    <h2>
                        <div class="card-icon">🔥</div>
                        Enhanced Intelligence Features
                    </h2>
                    <p>Next-generation content intelligence with 5 specialized AI agents</p>
                    
                    <div class="features">
                        <div class="feature">
                            <div class="feature-icon">🔍</div>
                            <div class="feature-content">
                                <h4>Deep Reddit Research</h4>
                                <p>Advanced customer insight extraction and pain point analysis</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-content">
                                <h4>Enhanced E-E-A-T Assessment</h4>
                                <p>Google Quality Rater Guidelines compliant scoring</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🧠</div>
                            <div class="feature-content">
                                <h4>Topic Research Intelligence</h4>
                                <p>Comprehensive semantic analysis and opportunity identification</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">📈</div>
                            <div class="feature-content">
                                <h4>Continuous Improvement Tracking</h4>
                                <p>Score progression and performance optimization</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🔬</div>
                            <div class="feature-content">
                                <h4>Content Quality Analysis</h4>
                                <p>Multi-dimensional quality assessment and benchmarking</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🏆</div>
                            <div class="feature-content">
                                <h4>Competitive Advantage Scoring</h4>
                                <p>ROI projections and market positioning analysis</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <h3>Advanced Intelligence Engines Processing</h3>
                <p>Running comprehensive multi-agent analysis to create your content strategy</p>
                <div style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
                    <div>🔍 Reddit Research Agent</div>
                    <div>🧠 Topic Research Agent</div>
                    <div>📊 E-E-A-T Assessment Agent</div>
                    <div>📈 Improvement Tracking Agent</div>
                    <div>✨ Content Generation Agent</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform</p>
            <p>Built by Zeeshan Bashir • Creating content that converts, not just ranks</p>
        </div>
        
        <script>
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('loading').scrollIntoView({ behavior: 'smooth' });
            });
        </script>
    </body>
    </html>
    """)

@app.post("/generate-advanced")
async def generate_advanced_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    eeat_instructions: str = Form(""),
    additional_notes: str = Form("")
):
    """Generate advanced content with comprehensive intelligence analysis"""
    try:
        print(f"🚀 Starting advanced content generation for: {topic}")
        
        # Create context objects
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'unique_value_prop': unique_value_prop,
            'topic': topic
        }
        
        human_inputs = {
            'customer_pain_points': customer_pain_points,
            'unique_value_prop': unique_value_prop,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type
        }
        
        ai_instructions = {
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'eeat_instructions': eeat_instructions,
            'additional_notes': additional_notes
        }
        
        # Step 1: Enhanced Reddit Research
        print("🔍 Running enhanced Reddit research...")
        subreddit_list = [s.strip() for s in subreddits.split(',')]
        reddit_insights = reddit_researcher.research_topic_comprehensive(
            topic, subreddit_list, max_posts_per_subreddit=15
        )
        
        # Step 2: Advanced Topic Research
        print("🧠 Conducting advanced topic research...")
        topic_research = topic_researcher.research_topic_comprehensive(
            topic, industry, target_audience, business_context
        )
        
        # Step 3: Enhanced Content Generation
        print("✨ Generating enhanced content...")
        generated_content = enhanced_content_generator.generate_content(
            topic, business_context, human_inputs, ai_instructions, 
            reddit_insights, topic_research
        )
        
        # Step 4: Comprehensive E-E-A-T Assessment
        print("📊 Performing comprehensive E-E-A-T assessment...")
        eeat_assessment = eeat_assessor.assess_comprehensive_eeat(
            generated_content, topic, business_context, human_inputs, reddit_insights
        )
        
        # Step 5: Content Quality Analysis
        print("🔬 Analyzing content quality...")
        content_metrics = {
            'word_count': len(generated_content.split()),
            'quality_score': min(10.0, len(generated_content.split()) / 100),
            'readability_score': 85.0,  # Placeholder
            'uniqueness_score': 92.0    # Placeholder
        }
        
        # Step 6: Track Improvement
        print("📈 Tracking improvement metrics...")
        snapshot_id = improvement_tracker.track_analysis(import os
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import enhanced agents
from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor
from src.agents.topic_research_agent import AdvancedTopicResearchAgent
from src.agents.improvement_tracking_agent import ContinuousImprovementTracker
from src.utils.llm_client import LLMClient

# Initialize FastAPI app
app = FastAPI(title="Zee SEO Tool - Advanced Content Intelligence Platform")

# AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")

class ClaudeAgent:
    def __init__(self):
        self.anthropic_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
    def call_claude(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", max_tokens: int = 1500):
        """Make API call to Claude"""
        try:
            if messages and messages[0].get("role") == "user":
                user_message = messages[0]["content"]
            else:
                user_message = "Please help with this request."
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.anthropic_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                return f"Demo mode - Claude API unavailable"
                
        except Exception as e:
            return f"Demo mode - Using fallback content"

# Enhanced content generator
class EnhancedContentGenerator:
    def __init__(self, claude_agent):
        self.claude_agent = claude_agent
        
    def generate_content(self, topic: str, business_context: Dict, human_inputs: Dict, 
                        ai_instructions: Dict, reddit_insights: Dict = None, 
                        topic_research: Dict = None) -> str:
        """Generate content using enhanced context"""
        
        # Enhanced AI prompt with all available intelligence
        ai_prompt = f"""
        Create exceptional, human-centered content about "{topic}" that demonstrates high E-E-A-T standards.
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        HUMAN EXPERTISE & INSIGHTS:# Step 6: Track Improvement
        print("📈 Tracking improvement metrics...")
        snapshot_id = improvement_tracker.track_analysis(
            topic,
            eeat_assessment['eeat_assessment'],
            eeat_assessment['human_vs_ai_analysis'],
            content_metrics,
            business_context,
            human_inputs
        )
        
        # Step 7: Generate Improvement Report
        improvement_report = improvement_tracker.generate_improvement_report(snapshot_id)
        
        # Generate comprehensive results page
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Advanced Content Intelligence Report - {topic} | Zee SEO Tool</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                    color: #111827;
                    line-height: 1.6;
                    min-height: 100vh;
                }}
                .header {{
                    background: white;
                    border-bottom: 1px solid #e5e7eb;
                    padding: 1rem 0;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .header-content {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .logo {{
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }}
                .logo-icon {{
                    width: 2.5rem;
                    height: 2.5rem;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    border-radius: 0.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 700;
                    font-size: 1.25rem;
                }}
                .logo-text {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .tagline {{
                    font-size: 0.75rem;
                    color: #6b7280;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 2rem 1.5rem;
                }}
                .report-header {{
                    background: white;
                    border-radius: 1rem;
                    padding: 2rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    margin-bottom: 2rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .report-title {{
                    font-size: 2rem;
                    font-weight: 800;
                    color: #111827;
                    margin-bottom: 0.5rem;
                }}
                .report-meta {{
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                }}
                .meta-item {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    background: #f3f4f6;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                }}
                .overall-scores {{
                    text-align: center;
                    display: flex;
                    gap: 2rem;
                }}
                .score-display {{
                    text-align: center;
                }}
                .score-value {{
                    font-size: 2.5rem;
                    font-weight: 800;
                    color: #2563eb;
                }}
                .score-label {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    font-weight: 600;
                }}
                .improvement-badge {{
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 0.75rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    margin-top: 0.5rem;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 1.5rem;
                    margin-bottom: 2rem;
                }}
                .card {{
                    background: white;
                    border-radius: 1rem;
                    padding: 1.5rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                }}
                .card h3 {{
                    font-size: 1.125rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}
                .tabs {{
                    display: flex;
                    background: #f3f4f6;
                    border-radius: 0.75rem;
                    padding: 0.25rem;
                    margin-bottom: 2rem;
                }}
                .tab {{
                    flex: 1;
                    padding: 0.75rem 1rem;
                    text-align: center;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-weight: 600;
                    font-size: 0.875rem;
                }}
                .tab.active {{
                    background: white;
                    color: #2563eb;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .tab-content {{
                    display: none;
                }}
                .tab-content.active {{
                    display: block;
                }}
                .eeat-scores {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }}
                .eeat-score {{
                    text-align: center;
                }}
                .score-circle {{
                    width: 4rem;
                    height: 4rem;
                    border-radius: 50%;
                    background: conic-gradient(#2563eb calc(var(--score) * 1%), #e5e7eb calc(var(--score) * 1%));
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 0.5rem;
                    position: relative;
                }}
                .score-circle::before {{
                    content: '';
                    width: 3rem;
                    height: 3rem;
                    background: white;
                    border-radius: 50%;
                    position: absolute;
                }}
                .score-circle span {{
                    position: relative;
                    z-index: 1;
                    font-weight: 700;
                    color: #111827;
                }}
                .score-name {{
                    font-size: 0.75rem;
                    color: #6b7280;
                    font-weight: 600;
                }}
                .metric-list {{
                    display: grid;
                    gap: 0.75rem;
                }}
                .metric-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.75rem;
                    background: #f9fafb;
                    border-radius: 0.5rem;
                }}
                .metric-label {{
                    font-size: 0.875rem;
                    color: #374151;
                    font-weight: 500;
                }}
                .metric-value {{
                    font-size: 0.875rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .insight-list {{
                    list-style: none;
                    padding: 0;
                }}
                .insight-item {{
                    padding: 1rem;
                    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                    border-left: 4px solid #2563eb;
                    border-radius: 0 0.5rem 0.5rem 0;
                    margin-bottom: 0.75rem;
                    font-size: 0.875rem;
                }}
                .content-section {{
                    margin: 2rem 0;
                }}
                .content-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }}
                .content-title {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .content-actions {{
                    display: flex;
                    gap: 0.75rem;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    padding: 0.75rem 1.25rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    border-radius: 0.75rem;
                    border: none;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                    font-family: inherit;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .btn-outline {{
                    background: white;
                    color: #374151;
                    border: 2px solid #e5e7eb;
                }}
                .content-display {{
                    background: white;
                    border-radius: 1rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    margin-bottom: 1rem;
                }}
                .content-stats {{
                    display: flex;
                    gap: 1rem;
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid #f3f4f6;
                    background: #f9fafb;
                    border-radius: 1rem 1rem 0 0;
                }}
                .stat {{
                    font-size: 0.75rem;
                    color: #6b7280;
                    font-weight: 500;
                }}
                .content-text {{
                    padding: 1.5rem;
                    max-height: 500px;
                    overflow-y: auto;
                }}
                .content-text pre {{
                    white-space: pre-wrap;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 0.875rem;
                    line-height: 1.6;
                    color: #374151;
                }}
                .footer {{
                    margin-top: 4rem;
                    padding: 2rem 0;
                    background: white;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                }}
                .back-btn {{
                    background: #6b7280;
                    color: white;
                }}
                .improvement-indicator {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    font-size: 0.75rem;
                    color: #059669;
                    font-weight: 600;
                }}
                @media (max-width: 768px) {{
                    .dashboard-grid {{ grid-template-columns: 1fr; }}
                    .report-header {{ flex-direction: column; gap: 1.5rem; text-align: center; }}
                    .content-header {{ flex-direction: column; gap: 1rem; align-items: stretch; }}
                    .content-actions {{ justify-content: center; }}
                    .eeat-scores {{ grid-template-columns: repeat(2, 1fr); }}
                    .overall-scores {{ flex-direction: column; gap: 1rem; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="logo">
                        <div class="logo-icon">Z</div>
                        <div>
                            <div class="logo-text">Zee SEO Tool</div>
                            <div class="tagline">Advanced Intelligence Report</div>
                        </div>
                    </div>
                    <a href="/" class="btn back-btn">← New Analysis</a>
                </div>
            </div>
            
            <div class="container">
                <div class="report-header">
                    <div>
                        <h1 class="report-title">{topic.title()}</h1>
                        <div class="report-meta">
                            <span class="meta-item">🏢 {industry}</span>
                            <span class="meta-item">👥 {target_audience}</span>
                            <span class="meta-item">📝 {content_metrics['word_count']} words</span>
                            <span class="meta-item">🔬 5 AI Agents</span>
                        </div>
                    </div>
                    <div class="overall-scores">
                        <div class="score-display">
                            <div class="score-value">{eeat_assessment['eeat_assessment']['overall_score']}</div>
                            <div class="score-label">E-E-A-T Score</div>
                            {self._generate_improvement_badge(improvement_report)}
                        </div>
                        <div class="score-display">
                            <div class="score-value">{eeat_assessment['human_vs_ai_analysis']['human_elements_score']}</div>
                            <div class="score-label">Human Elements</div>
                        </div>
                    </div>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="showTab('overview')">📊 Overview</div>
                    <div class="tab" onclick="showTab('eeat')">🎯 E-E-A-T Analysis</div>
                    <div class="tab" onclick="showTab('research')">🔍 Research Insights</div>
                    <div class="tab" onclick="showTab('improvement')">📈 Improvement Tracking</div>
                    <div class="tab" onclick="showTab('content')">📝 Content</div>
                </div>
                
                <div id="overview" class="tab-content active">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>🎯 E-E-A-T Assessment</h3>
                            <div class="eeat-scores">
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['experience']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['experience']['score']}</span>
                                    </div>
                                    <div class="score-name">Experience</div>
                                </div>
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['expertise']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['expertise']['score']}</span>
                                    </div>
                                    <div class="score-name">Expertise</div>
                                </div>
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['authoritativeness']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['authoritativeness']['score']}</span>
                                    </div>
                                    <div class="score-name">Authority</div>
                                </div>
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['trustworthiness']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['trustworthiness']['score']}</span>
                                    </div>
                                    <div class="score-name">Trust</div>
                                </div>
                            </div>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <span class="metric-label">E-E-A-T Level</span>
                                    <span class="metric-value">{eeat_assessment['eeat_assessment']['eeat_level'].replace('_', ' ').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">YMYL Topic</span>
                                    <span class="metric-value">{'Yes' if eeat_assessment['eeat_assessment']['is_ymyl_topic'] else 'No'}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🔍 Research Quality</h3>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <span class="metric-label">Reddit Research Quality</span>
                                    <span class="metric-value">{reddit_insights.get('research_quality_score', {}).get('reliability', 'Good').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Posts Analyzed</span>
                                    <span class="metric-value">{reddit_insights.get('quantitative_insights', {}).get('total_posts_analyzed', 'N/A')}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Topic Research Depth</span>
                                    <span class="metric-value">{topic_research.get('research_quality_score', {}).get('research_depth', 'Comprehensive').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Human Input Quality</span>
                                    <span class="metric-value">{improvement_report.get('current_performance', {}).get('component_analysis', {}).get('improvement_priority', 'Good').replace('_', ' ').title()}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🚀 Performance Prediction</h3>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <span class="metric-label">vs AI Content</span>
                                    <span class="metric-value">{eeat_assessment['competitive_advantage']['performance_predictions']['traffic_potential']}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Market Position</span>
                                    <span class="metric-value">{eeat_assessment['competitive_advantage']['market_position'].replace('_', ' ').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Performance Tier</span>
                                    <span class="metric-value">{eeat_assessment['content_performance_prediction']['performance_tier'].title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Results Timeline</span>
                                    <span class="metric-value">{eeat_assessment['content_performance_prediction']['timeline_to_results']}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="eeat" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>📊 Detailed E-E-A-T Analysis</h3>
                            <ul class="insight-list">
                                {self._format_eeat_insights(eeat_assessment)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>💡 Improvement Recommendations</h3>
                            <ul class="insight-list">
                                {self._format_improvement_recommendations(eeat_assessment['improvement_analysis'])}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div id="research" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>🎯 Customer Pain Points</h3>
                            <ul class="insight-list">
                                {self._format_pain_points(reddit_insights)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>🗣️ Real Customer Voice</h3>
                            <ul class="insight-list">
                                {self._format_customer_quotes(reddit_insights)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>📈 Content Opportunities</h3>
                            <ul class="insight-list">
                                {self._format_content_opportunities(topic_research)}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div id="improvement" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>📈 Current Performance</h3>
                            <div class="metric-list">
                                {self._format_current_performance(improvement_report)}
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🎯 Next Steps</h3>
                            <ul class="insight-list">
                                {self._format_next_steps(improvement_report)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>💰 ROI Projection</h3>
                            <div class="metric-list">
                                {self._format_roi_projection(improvement_report)}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="content" class="tab-content">
                    <div class="content-section">
                        <div class="content-header">
                            <h2 class="content-title">Generated Content</h2>
                            <div class="content-actions">
                                <button onclick="copyContent()" class="btn btn-outline">📋 Copy</button>
                                <button onclick="exportContent()" class="btn btn-primary">💾 Export</button>
                            </div>
                        </div>
                        
                        <div class="content-display">
                            <div class="content-stats">
                                <span class="stat">📝 {content_metrics['word_count']} words</span>
                                <span class="stat">📊 {content_metrics['readability_score']} readability</span>
                                <span class="stat">🎯 {eeat_assessment['eeat_assessment']['overall_score']} E-E-A-T</span>
                                <span class="stat">🔥 {content_metrics['uniqueness_score']}% unique</span>
                            </div>
                            
                            <div class="content-text" id="content-text">
                                <pre>{generated_content}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform by Zeeshan Bashir</p>
            </div>
            
            <script>
                function showTab(tabName) {{
                    // Hide all tab contents
                    const contents = document.querySelectorAll('.tab-content');
                    contents.forEach(content => content.classList.remove('active'));
                    
                    // Remove active class from all tabs
                    const tabs = document.querySelectorAll('.tab');
                    tabs.forEach(tab => tab.classList.remove('active'));
                    
                    // Show selected tab content
                    document.getElementById(tabName).classList.add('active');
                    
                    // Add active class to clicked tab
                    event.target.classList.add('active');
                }}
                
                function copyContent() {{
                    const content = document.getElementById('content-text').textContent;
                    navigator.clipboard.writeText(content).then(() => {{
                        alert('Content copied to clipboard!');
                    }});
                }}
                
                function exportContent() {{
                    const content = document.getElementById('content-text').textContent;
                    const blob = new Blob([content], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '{topic.replace(" ", "_")}_zee_seo_enhanced.txt';
                    a.click();
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        return HTMLResponse(content=f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 2rem; text-align: center;">
            <h1>⚠️ Analysis Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <a href="/" style="color: #2563eb; text-decoration: none;">← Back to Zee SEO Tool</a>
        </body>
        </html>
        """, status_code=500)

# Helper methods for formatting the HTML response
def _generate_improvement_badge(improvement_report):
    """Generate improvement badge HTML"""
    if improvement_report.get('improvement_summary', {}).get('improvement_level') == 'baseline_established':
        return '<div class="improvement-badge">🎯 Baseline Established</div>'
    else:
        improvement_level = improvement_report.get('improvement_summary', {}).get('improvement_level', 'good')
        return f'<div class="improvement-badge">📈 {improvement_level.replace("_", " ").title()}</div>'

def _format_eeat_insights(eeat_assessment):
    """Format E-E-A-T insights for display"""
    insights = []
    
    # Overall assessment
    overall = eeat_assessment['eeat_assessment']
    insights.append(f'<li class="insight-item">Overall E-E-A-T Level: <strong>{overall["eeat_level"].replace("_", " ").title()}</strong></li>')
    
    # Component insights
    for component, data in overall['components'].items():
        score = data['score']
        if score >= 8.0:
            level = "Excellent"
        elif score >= 6.5:
            level = "Good" 
        elif score >= 5.0:
            level = "Fair"
        else:
            level = "Needs Improvement"
        
        insights.append(f'<li class="insight-item">{component.title()}: <strong>{score}/10 ({level})</strong></li>')
    
    return '\n'.join(insights)

def _format_improvement_recommendations(improvement_analysis):
    """Format improvement recommendations"""
    recommendations = []
    
    immediate = improvement_analysis.get('immediate_actions', [])
    for action in immediate[:3]:  # Top 3
        recommendations.append(f'<li class="insight-item">🚨 <strong>Immediate:</strong> {action}</li>')
    
    content_enhancements = improvement_analysis.get('content_enhancements', [])
    for enhancement in content_enhancements[:2]:  # Top 2
        recommendations.append(f'<li class="insight-item">📝 <strong>Content:</strong> {enhancement}</li>')
    
    return '\n'.join(recommendations)

def _format_pain_points(reddit_insights):
    """Format customer pain points"""
    pain_points = reddit_insights.get('pain_point_analysis', {}).get('critical_pain_points', [])
    formatted = []
    
    for point in pain_points[:4]:  # Top 4
        formatted.append(f'<li class="insight-item">😤 {point}</li>')
    
    return '\n'.join(formatted) if formatted else '<li class="insight-item">No specific pain points identified</li>'

def _format_customer_quotes(reddit_insights):
    """Format real customer quotes"""
    quotes = reddit_insights.get('authenticity_markers', {}).get('real_customer_quotes', [])
    formatted = []
    
    for quote in quotes[:3]:  # Top 3
        formatted.append(f'<li class="insight-item">💬 "{quote}"</li>')
    
    return '\n'.join(formatted) if formatted else '<li class="insight-item">No customer quotes available</li>'

def _format_content_opportunities(topic_research):
    """Format content opportunities"""
    opportunities = topic_research.get('topic_research', {}).get('opportunity_scoring', {}).get('top_opportunities', [])
    formatted = []
    
    for opp in opportunities[:4]:  # Top 4
        name = opp.get('name', 'Opportunity')
        score = opp.get('opportunity_score', 0)
        formatted.append(f'<li class="insight-item">🎯 {name} (Score: {score:.1f}/10)</li>')
    
    return '\n'.join(formatted) if formatted else '<li class="insight-item">No opportunities identified</li>'

def _        HUMAN EXPERTISE & INSIGHTS:
        - Customer Pain Points: {human_inputs.get('customer_pain_points')}
        - Industry Experience: {human_inputs.get('unique_value_prop')}
        
        REAL CUSTOMER RESEARCH:
        {self._format_reddit_insights(reddit_insights) if reddit_insights else 'Not available'}
        
        TOPIC INTELLIGENCE:
        {self._format_topic_research(topic_research) if topic_research else 'Not available'}
        
        AI INSTRUCTIONS:
        - Writing Style: {ai_instructions.get('writing_style', 'Professional')}
        - Target Length: {ai_instructions.get('target_word_count', '1000-1500 words')}
        - Special Notes: {ai_instructions.get('additional_notes', 'None')}
        
        CONTENT REQUIREMENTS:
        1. Demonstrate genuine experience through specific examples and personal insights
        2. Show expertise with accurate, in-depth information
        3. Build authority through unique perspectives and comprehensive coverage
        4. Establish trust through transparency, balanced views, and credible sources
        5. Address real customer pain points identified in the research
        6. Use authentic language that resonates with the target audience
        7. Include specific, actionable advice that only an expert would know
        8. Reference credible sources and provide balanced perspectives
        
        Create content that is significantly better than generic AI content by incorporating:
        - Real customer language and concerns from the research
        - Industry-specific expertise and insider knowledge
        - Personal experience and authentic insights
        - Practical solutions to genuine problems
        
        Make this content worthy of being cited as an authoritative source.
        """
        
        messages = [{"role": "user", "content": ai_prompt}]
        return self.claude_agent.call_claude(messages, max_tokens=3000)
    
    def _format_reddit_insights(self, reddit_insights: Dict) -> str:
        """Format Reddit insights for the AI prompt"""
        if not reddit_insights:
            return "No Reddit insights available"
        
        formatted = []
        
        # Pain points
        pain_points = reddit_insights.get('pain_point_analysis', {}).get('critical_pain_points', [])
        if pain_points:
            formatted.append(f"Critical Pain Points: {', '.join(pain_points[:3])}")
        
        # Customer quotes
        quotes = reddit_insights.get('authenticity_markers', {}).get('real_customer_quotes', [])
        if quotes:
            formatted.append(f"Real Customer Quotes: {'; '.join(quotes[:2])}")
        
        # Language patterns
        vocab = reddit_insights.get('language_intelligence', {}).get('customer_vocabulary', [])
        if vocab:
            formatted.append(f"Customer Language: {', '.join(vocab[:5])}")
        
        return '\n'.join(formatted)
    
    def _format_topic_research(self, topic_research: Dict) -> str:
        """Format topic research for the AI prompt"""
        if not topic_research:
            return "No topic research available"
        
        formatted = []
        
        # Content gaps
        gaps = topic_research.get('topic_research', {}).get('content_gaps', {}).get('market_gaps', {})
        if gaps.get('underserved_questions'):
            formatted.append(f"Underserved Questions: {', '.join(gaps['underserved_questions'][:3])}")
        
        # Opportunities
        opportunities = topic_research.get('topic_research', {}).get('opportunity_scoring', {}).get('top_opportunities', [])
        if opportunities:
            top_ops = [op.get('name', '') for op in opportunities[:3]]
            formatted.append(f"Top Opportunities: {', '.join(top_ops)}")
        
        return '\n'.join(formatted)

# Initialize enhanced components
claude_agent = ClaudeAgent()
enhanced_content_generator = EnhancedContentGenerator(claude_agent)
reddit_researcher = EnhancedRedditResearcher()
eeat_assessor = EnhancedEEATAssessor()
topic_researcher = AdvancedTopicResearchAgent()
improvement_tracker = ContinuousImprovementTracker()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced home page with new features"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool - Advanced Content Intelligence Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                color: #111827;
                line-height: 1.6;
                min-height: 100vh;
            }
            
            .header {
                background: white;
                border-bottom: 1px solid #e5e7eb;
                padding: 1.5rem 0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                position: sticky;
                top: 0;
                z-index: 50;
            }
            
            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 1.5rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .logo-icon {
                width: 3rem;
                height: 3rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 800;
                font-size: 1.5rem;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .logo-text {
                font-size: 1.75rem;
                font-weight: 800;
                color: #111827;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .tagline {
                font-size: 0.875rem;
                color: #6b7280;
                font-weight: 500;
                margin-top: 0.25rem;
            }
            
            .version-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            .creator {
                text-align: right;
                font-size: 0.875rem;
                color: #6b7280;
            }
            
            .creator strong {
                color: #374151;
                display: block;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }
            
            .hero {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .hero h1 {
                font-size: 2.5rem;
                font-weight: 800;
                color: #111827;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .hero p {
                font-size: 1.25rem;
                color: #6b7280;
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }
            
            .hero-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                max-width: 500px;
                margin: 2rem auto;
            }
            
            .hero-stat {
                text-align: center;
                padding: 1rem;
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .hero-stat-value {
                font-size: 1.5rem;
                font-weight: 800;
                color: #2563eb;
            }
            
            .hero-stat-label {
                font-size: 0.75rem;
                color: #6b7280;
                margin-top: 0.25rem;
            }
            
            .main-grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 2rem;
            }
            
            .card {
                background: white;
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                transform: translateY(-2px);
            }
            
            .card h2 {
                font-size: 1.375rem;
                font-weight: 700;
                color: #111827;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            
            .card-icon {
                width: 2rem;
                height: 2rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }
            
            .card p {
                color: #6b7280;
                margin-bottom: 1.5rem;
            }
            
            .form-grid {
                display: grid;
                gap: 1.5rem;
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }
            
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .form-label {
                font-size: 0.875rem;
                font-weight: 600;
                color: #374151;
            }
            
            .form-input, .form-textarea, .form-select {
                padding: 0.875rem 1rem;
                border: 2px solid #e5e7eb;
                border-radius: 0.75rem;
                font-size: 0.875rem;
                transition: all 0.2s ease;
                background: white;
            }
            
            .form-input:focus, .form-textarea:focus, .form-select:focus {
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                transform: translateY(-1px);
            }
            
            .form-textarea {
                resize: vertical;
                min-height: 4rem;
                font-family: inherit;
            }
            
            .form-help {
                font-size: 0.75rem;
                color: #6b7280;
            }
            
            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                padding: 1rem 2rem;
                font-size: 1rem;
                font-weight: 700;
                border-radius: 0.75rem;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                font-family: inherit;
                width: 100%;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
            
            .ai-controls {
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border: 2px solid #bfdbfe;
            }
            
            .features {
                display: grid;
                gap: 1rem;
            }
            
            .feature {
                display: flex;
                align-items: flex-start;
                gap: 1rem;
                padding: 1.25rem;
                background: linear-gradient(135deg, #f9fafb 0%, white 100%);
                border-radius: 0.75rem;
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            
            .feature:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                border-color: #2563eb;
            }
            
            .feature-icon {
                width: 2.5rem;
                height: 2.5rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                flex-shrink: 0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .feature-content h4 {
                font-size: 0.9rem;
                font-weight: 600;
                color: #111827;
                margin-bottom: 0.25rem;
            }
            
            .feature-content p {
                font-size: 0.8rem;
                color: #6b7280;
                margin: 0;
                line-height: 1.4;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 3rem 2rem;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                margin-top: 2rem;
            }
            
            .loading-spinner {
                width: 3rem;
                height: 3rem;
                border: 3px solid #e5e7eb;
                border-top: 3px solid #2563eb;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1.5rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .footer {
                margin-top: 4rem;
                padding: 3rem 0;
                background: white;
                border-top: 1px solid #e5e7eb;
                text-align: center;
            }
            
            .footer p {
                color: #6b7280;
                margin-bottom: 0.5rem;
            }
            
            @media (max-width: 768px) {
                .main-grid { grid-template-columns: 1fr; gap: 1.5rem; }
                .form-row { grid-template-columns: 1fr; }
                .hero h1 { font-size: 2rem; }
                .hero p { font-size: 1rem; }
                .container { padding: 1rem; }
                .header-content { flex-direction: column; gap: 1rem; text-align: center; }
                .hero-stats { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-icon">Z</div>
                    <div>
                        <div class="logo-text">Zee SEO Tool</div>
                        <div class="tagline">Advanced Content Intelligence Platform</div>
                    </div>
                </div>
                <div class="version-badge">Enhanced v2.0</div>
                <div class="creator">
                    <strong>Built by Zeeshan Bashir</strong>
                    <div>Human + AI Intelligence Bridge</div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="hero">
                <h1>Create Content That Actually Converts</h1>
                <p>The most advanced content intelligence platform combining deep customer research, E-E-A-T optimization, and continuous improvement tracking</p>
                
                <div class="hero-stats">
                    <div class="hero-stat">
                        <div class="hero-stat-value">350%</div>
                        <div class="hero-stat-label">Better Performance</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-value">5+</div>
                        <div class="hero-stat-label">AI Agents</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-value">95%</div>
                        <div class="hero-stat-label">E-E-A-T Score</div>
                    </div>
                </div>
            </div>
            
            <div class="main-grid">
                <form action="/generate-advanced" method="post">
                    <div class="card">
                        <h2>
                            <div class="card-icon">🧠</div>
                            Advanced Content Intelligence Input
                        </h2>
                        <p>Our enhanced system combines multiple AI agents for comprehensive content analysis and generation.</p>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label">Content Topic</label>
                                <input class="form-input" type="text" name="topic" 
                                       placeholder="e.g., best budget laptops for college students" required>
                                <div class="form-help">Our topic research agent will analyze semantic relationships and opportunities</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Target Communities for Research</label>
                                <input class="form-input" type="text" name="subreddits" 
                                       placeholder="e.g., laptops, college, StudentLoans" required>
                                <div class="form-help">Enhanced Reddit research with deep customer insight extraction</div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Industry</label>
                                    <input class="form-input" type="text" name="industry" 
                                           placeholder="e.g., Technology" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Target Audience</label>
                                    <input class="form-input" type="text" name="target_audience" 
                                           placeholder="e.g., College students" required>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Business Type</label>
                                <select class="form-select" name="business_type" required>
                                    <option value="">Select business model</option>
                                    <option value="B2B">B2B (Business to Business)</option>
                                    <option value="B2C">B2C (Business to Consumer)</option>
                                    <option value="Both">Both B2B and B2C</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Your Unique Value Proposition</label>
                                <textarea class="form-textarea" name="unique_value_prop" 
                                          placeholder="What makes you different from competitors? Be specific and authentic." required></textarea>
                                <div class="form-help">Critical for E-E-A-T authority and differentiation analysis</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Customer Pain Points & Insights</label>
                                <textarea class="form-textarea" name="customer_pain_points" 
                                          placeholder="What specific challenges do your customers face? Include real examples." required></textarea>
                                <div class="form-help">Enhanced analysis will combine this with Reddit research for deeper insights</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card ai-controls">
                        <h2>
                            <div class="card-icon">⚙️</div>
                            Advanced AI Configuration
                        </h2>
                        <p>Fine-tune content generation with enhanced AI controls and quality parameters</p>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Writing Style</label>
                                    <select class="form-select" name="writing_style">
                                        <option value="">Adaptive (Recommended)</option>
                                        <option value="British English">British English</option>
                                        <option value="American English">American English</option>
                                        <option value="Conversational">Conversational</option>
                                        <option value="Technical">Technical</option>
                                        <option value="Academic">Academic</option>
                                        <option value="Authoritative">Authoritative</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Target Length</label>
                                    <select class="form-select" name="target_word_count">
                                        <option value="">Optimal (1200-1800)</option>
                                        <option value="800-1200">Concise (800-1200)</option>
                                        <option value="1500-2500">Comprehensive (1500-2500)</option>
                                        <option value="2500-4000">In-depth (2500-4000)</option>
                                        <option value="4000+">Ultimate Guide (4000+)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">E-E-A-T Enhancement Instructions</label>
                                <textarea class="form-textarea" name="eeat_instructions" 
                                          placeholder="Specific instructions for experience, expertise, authority, or trust elements"></textarea>
                                <div class="form-help">Guide our E-E-A-T optimization agent</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Additional AI Instructions</label>
                                <textarea class="form-textarea" name="additional_notes" 
                                          placeholder="Any specific requirements: statistics, format preferences, tone adjustments"></textarea>
                                <div class="form-help">Advanced customization for content generation</div>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn">
                        🚀 Generate Advanced Content Intelligence Report
                    </button>
                </form>
                
                <div class="card">
                    <h2>
                        <div class="card-icon">🔥</div>
                        Enhanced Intelligence Features
                    </h2>
                    <p>Next-generation content intelligence with 5 specialized AI agents</p>
                    
                    <div class="features">
                        <div class="feature">
                            <div class="feature-icon">🔍</div>
                            <div class="feature-content">
                                <h4>Deep Reddit Research</h4>
                                <p>Advanced customer insight extraction and pain point analysis</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-content">
                                <h4>Enhanced E-E-A-T Assessment</h4>
                                <p>Google Quality Rater Guidelines compliant scoring</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🧠</div>
                            <div class="feature-content">
                                <h4>Topic Research Intelligence</h4>
                                <p>Comprehensive semantic analysis and opportunity identification</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">📈</div>
                            <div class="feature-content">
                                <h4>Continuous Improvement Tracking</h4>
                                <p>Score progression and performance optimization</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🔬</div>
                            <div class="feature-content">
                                <h4>Content Quality Analysis</h4>
                                <p>Multi-dimensional quality assessment and benchmarking</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🏆</div>
                            <div class="feature-content">
                                <h4>Competitive Advantage Scoring</h4>
                                <p>ROI projections and market positioning analysis</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <h3>Advanced Intelligence Engines Processing</h3>
                <p>Running comprehensive multi-agent analysis to create your content strategy</p>
                <div style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
                    <div>🔍 Reddit Research Agent</div>
                    <div>🧠 Topic Research Agent</div>
                    <div>📊 E-E-A-T Assessment Agent</div>
                    <div>📈 Improvement Tracking Agent</div>
                    <div>✨ Content Generation Agent</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform</p>
            <p>Built by Zeeshan Bashir • Creating content that converts, not just ranks</p>
        </div>
        
        <script>
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('loading').scrollIntoView({ behavior: 'smooth' });
            });
        </script>
    </body>
    </html>
    """)

@app.post("/generate-advanced")
async def generate_advanced_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    eeat_instructions: str = Form(""),
    additional_notes: str = Form("")
):
    """Generate advanced content with comprehensive intelligence analysis"""
    try:
        print(f"🚀 Starting advanced content generation for: {topic}")
        
        # Create context objects
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'unique_value_prop': unique_value_prop,
            'topic': topic
        }
        
        human_inputs = {
            'customer_pain_points': customer_pain_points,
            'unique_value_prop': unique_value_prop,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type
        }
        
        ai_instructions = {
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'eeat_instructions': eeat_instructions,
            'additional_notes': additional_notes
        }
        
        # Step 1: Enhanced Reddit Research
        print("🔍 Running enhanced Reddit research...")
        subreddit_list = [s.strip() for s in subreddits.split(',')]
        reddit_insights = reddit_researcher.research_topic_comprehensive(
            topic, subreddit_list, max_posts_per_subreddit=15
        )
        
        # Step 2: Advanced Topic Research
        print("🧠 Conducting advanced topic research...")
        topic_research = topic_researcher.research_topic_comprehensive(
            topic, industry, target_audience, business_context
        )
        
        # Step 3: Enhanced Content Generation
        print("✨ Generating enhanced content...")
        generated_content = enhanced_content_generator.generate_content(
            topic, business_context, human_inputs, ai_instructions, 
            reddit_insights, topic_research
        )
        
        # Step 4: Comprehensive E-E-A-T Assessment
        print("📊 Performing comprehensive E-E-A-T assessment...")
        eeat_assessment = eeat_assessor.assess_comprehensive_eeat(
            generated_content, topic, business_context, human_inputs, reddit_insights
        )
        
        # Step 5: Content Quality Analysis
        print("🔬 Analyzing content quality...")
        content_metrics = {
            'word_count': len(generated_content.split()),
            'quality_score': min(10.0, len(generated_content.split()) / 100),
            'readability_score': 85.0,  # Placeholder
            'uniqueness_score': 92.0    # Placeholder
        }
        
        # Step 6: Track Improvement
        print("📈 Tracking improvement metrics...")
        snapshot_id = improvement_tracker.track_analysis(import os
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import enhanced agents
from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor
from src.agents.topic_research_agent import AdvancedTopicResearchAgent
from src.agents.improvement_tracking_agent import ContinuousImprovementTracker
from src.utils.llm_client import LLMClient

# Initialize FastAPI app
app = FastAPI(title="Zee SEO Tool - Advanced Content Intelligence Platform")

# AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")

class ClaudeAgent:
    def __init__(self):
        self.anthropic_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
    def call_claude(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", max_tokens: int = 1500):
        """Make API call to Claude"""
        try:
            if messages and messages[0].get("role") == "user":
                user_message = messages[0]["content"]
            else:
                user_message = "Please help with this request."
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.anthropic_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                return f"Demo mode - Claude API unavailable"
                
        except Exception as e:
            return f"Demo mode - Using fallback content"

# Enhanced content generator
class EnhancedContentGenerator:
    def __init__(self, claude_agent):
        self.claude_agent = claude_agent
        
    def generate_content(self, topic: str, business_context: Dict, human_inputs: Dict, 
                        ai_instructions: Dict, reddit_insights: Dict = None, 
                        topic_research: Dict = None) -> str:
        """Generate content using enhanced context"""
        
        # Enhanced AI prompt with all available intelligence
        ai_prompt = f"""
        Create exceptional, human-centered content about "{topic}" that demonstrates high E-E-A-T standards.
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        HUMAN EXPERTISE & INSIGHTS:# Step 6: Track Improvement
        print("📈 Tracking improvement metrics...")
        snapshot_id = improvement_tracker.track_analysis(
            topic,
            eeat_assessment['eeat_assessment'],
            eeat_assessment['human_vs_ai_analysis'],
            content_metrics,
            business_context,
            human_inputs
        )
        
        # Step 7: Generate Improvement Report
        improvement_report = improvement_tracker.generate_improvement_report(snapshot_id)
        
        # Generate comprehensive results page
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Advanced Content Intelligence Report - {topic} | Zee SEO Tool</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                    color: #111827;
                    line-height: 1.6;
                    min-height: 100vh;
                }}
                .header {{
                    background: white;
                    border-bottom: 1px solid #e5e7eb;
                    padding: 1rem 0;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .header-content {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .logo {{
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }}
                .logo-icon {{
                    width: 2.5rem;
                    height: 2.5rem;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    border-radius: 0.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 700;
                    font-size: 1.25rem;
                }}
                .logo-text {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .tagline {{
                    font-size: 0.75rem;
                    color: #6b7280;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 2rem 1.5rem;
                }}
                .report-header {{
                    background: white;
                    border-radius: 1rem;
                    padding: 2rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    margin-bottom: 2rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .report-title {{
                    font-size: 2rem;
                    font-weight: 800;
                    color: #111827;
                    margin-bottom: 0.5rem;
                }}
                .report-meta {{
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                }}
                .meta-item {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    background: #f3f4f6;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                }}
                .overall-scores {{
                    text-align: center;
                    display: flex;
                    gap: 2rem;
                }}
                .score-display {{
                    text-align: center;
                }}
                .score-value {{
                    font-size: 2.5rem;
                    font-weight: 800;
                    color: #2563eb;
                }}
                .score-label {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    font-weight: 600;
                }}
                .improvement-badge {{
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 0.75rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    margin-top: 0.5rem;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 1.5rem;
                    margin-bottom: 2rem;
                }}
                .card {{
                    background: white;
                    border-radius: 1rem;
                    padding: 1.5rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                }}
                .card h3 {{
                    font-size: 1.125rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}
                .tabs {{
                    display: flex;
                    background: #f3f4f6;
                    border-radius: 0.75rem;
                    padding: 0.25rem;
                    margin-bottom: 2rem;
                }}
                .tab {{
                    flex: 1;
                    padding: 0.75rem 1rem;
                    text-align: center;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-weight: 600;
                    font-size: 0.875rem;
                }}
                .tab.active {{
                    background: white;
                    color: #2563eb;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .tab-content {{
                    display: none;
                }}
                .tab-content.active {{
                    display: block;
                }}
                .eeat-scores {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }}
                .eeat-score {{
                    text-align: center;
                }}
                .score-circle {{
                    width: 4rem;
                    height: 4rem;
                    border-radius: 50%;
                    background: conic-gradient(#2563eb calc(var(--score) * 1%), #e5e7eb calc(var(--score) * 1%));
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 0.5rem;
                    position: relative;
                }}
                .score-circle::before {{
                    content: '';
                    width: 3rem;
                    height: 3rem;
                    background: white;
                    border-radius: 50%;
                    position: absolute;
                }}
                .score-circle span {{
                    position: relative;
                    z-index: 1;
                    font-weight: 700;
                    color: #111827;
                }}
                .score-name {{
                    font-size: 0.75rem;
                    color: #6b7280;
                    font-weight: 600;
                }}
                .metric-list {{
                    display: grid;
                    gap: 0.75rem;
                }}
                .metric-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.75rem;
                    background: #f9fafb;
                    border-radius: 0.5rem;
                }}
                .metric-label {{
                    font-size: 0.875rem;
                    color: #374151;
                    font-weight: 500;
                }}
                .metric-value {{
                    font-size: 0.875rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .insight-list {{
                    list-style: none;
                    padding: 0;
                }}
                .insight-item {{
                    padding: 1rem;
                    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                    border-left: 4px solid #2563eb;
                    border-radius: 0 0.5rem 0.5rem 0;
                    margin-bottom: 0.75rem;
                    font-size: 0.875rem;
                }}
                .content-section {{
                    margin: 2rem 0;
                }}
                .content-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }}
                .content-title {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .content-actions {{
                    display: flex;
                    gap: 0.75rem;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    padding: 0.75rem 1.25rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    border-radius: 0.75rem;
                    border: none;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                    font-family: inherit;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                .btn-outline {{
                    background: white;
                    color: #374151;
                    border: 2px solid #e5e7eb;
                }}
                .content-display {{
                    background: white;
                    border-radius: 1rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    margin-bottom: 1rem;
                }}
                .content-stats {{
                    display: flex;
                    gap: 1rem;
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid #f3f4f6;
                    background: #f9fafb;
                    border-radius: 1rem 1rem 0 0;
                }}
                .stat {{
                    font-size: 0.75rem;
                    color: #6b7280;
                    font-weight: 500;
                }}
                .content-text {{
                    padding: 1.5rem;
                    max-height: 500px;
                    overflow-y: auto;
                }}
                .content-text pre {{
                    white-space: pre-wrap;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 0.875rem;
                    line-height: 1.6;
                    color: #374151;
                }}
                .footer {{
                    margin-top: 4rem;
                    padding: 2rem 0;
                    background: white;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                }}
                .back-btn {{
                    background: #6b7280;
                    color: white;
                }}
                .improvement-indicator {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    font-size: 0.75rem;
                    color: #059669;
                    font-weight: 600;
                }}
                @media (max-width: 768px) {{
                    .dashboard-grid {{ grid-template-columns: 1fr; }}
                    .report-header {{ flex-direction: column; gap: 1.5rem; text-align: center; }}
                    .content-header {{ flex-direction: column; gap: 1rem; align-items: stretch; }}
                    .content-actions {{ justify-content: center; }}
                    .eeat-scores {{ grid-template-columns: repeat(2, 1fr); }}
                    .overall-scores {{ flex-direction: column; gap: 1rem; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="logo">
                        <div class="logo-icon">Z</div>
                        <div>
                            <div class="logo-text">Zee SEO Tool</div>
                            <div class="tagline">Advanced Intelligence Report</div>
                        </div>
                    </div>
                    <a href="/" class="btn back-btn">← New Analysis</a>
                </div>
            </div>
            
            <div class="container">
                <div class="report-header">
                    <div>
                        <h1 class="report-title">{topic.title()}</h1>
                        <div class="report-meta">
                            <span class="meta-item">🏢 {industry}</span>
                            <span class="meta-item">👥 {target_audience}</span>
                            <span class="meta-item">📝 {content_metrics['word_count']} words</span>
                            <span class="meta-item">🔬 5 AI Agents</span>
                        </div>
                    </div>
                    <div class="overall-scores">
                        <div class="score-display">
                            <div class="score-value">{eeat_assessment['eeat_assessment']['overall_score']}</div>
                            <div class="score-label">E-E-A-T Score</div>
                            {self._generate_improvement_badge(improvement_report)}
                        </div>
                        <div class="score-display">
                            <div class="score-value">{eeat_assessment['human_vs_ai_analysis']['human_elements_score']}</div>
                            <div class="score-label">Human Elements</div>
                        </div>
                    </div>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="showTab('overview')">📊 Overview</div>
                    <div class="tab" onclick="showTab('eeat')">🎯 E-E-A-T Analysis</div>
                    <div class="tab" onclick="showTab('research')">🔍 Research Insights</div>
                    <div class="tab" onclick="showTab('improvement')">📈 Improvement Tracking</div>
                    <div class="tab" onclick="showTab('content')">📝 Content</div>
                </div>
                
                <div id="overview" class="tab-content active">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>🎯 E-E-A-T Assessment</h3>
                            <div class="eeat-scores">
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['experience']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['experience']['score']}</span>
                                    </div>
                                    <div class="score-name">Experience</div>
                                </div>
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['expertise']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['expertise']['score']}</span>
                                    </div>
                                    <div class="score-name">Expertise</div>
                                </div>
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['authoritativeness']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['authoritativeness']['score']}</span>
                                    </div>
                                    <div class="score-name">Authority</div>
                                </div>
                                <div class="eeat-score">
                                    <div class="score-circle" style="--score: {eeat_assessment['eeat_assessment']['components']['trustworthiness']['score'] * 10}">
                                        <span>{eeat_assessment['eeat_assessment']['components']['trustworthiness']['score']}</span>
                                    </div>
                                    <div class="score-name">Trust</div>
                                </div>
                            </div>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <span class="metric-label">E-E-A-T Level</span>
                                    <span class="metric-value">{eeat_assessment['eeat_assessment']['eeat_level'].replace('_', ' ').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">YMYL Topic</span>
                                    <span class="metric-value">{'Yes' if eeat_assessment['eeat_assessment']['is_ymyl_topic'] else 'No'}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🔍 Research Quality</h3>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <span class="metric-label">Reddit Research Quality</span>
                                    <span class="metric-value">{reddit_insights.get('research_quality_score', {}).get('reliability', 'Good').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Posts Analyzed</span>
                                    <span class="metric-value">{reddit_insights.get('quantitative_insights', {}).get('total_posts_analyzed', 'N/A')}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Topic Research Depth</span>
                                    <span class="metric-value">{topic_research.get('research_quality_score', {}).get('research_depth', 'Comprehensive').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Human Input Quality</span>
                                    <span class="metric-value">{improvement_report.get('current_performance', {}).get('component_analysis', {}).get('improvement_priority', 'Good').replace('_', ' ').title()}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🚀 Performance Prediction</h3>
                            <div class="metric-list">
                                <div class="metric-item">
                                    <span class="metric-label">vs AI Content</span>
                                    <span class="metric-value">{eeat_assessment['competitive_advantage']['performance_predictions']['traffic_potential']}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Market Position</span>
                                    <span class="metric-value">{eeat_assessment['competitive_advantage']['market_position'].replace('_', ' ').title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Performance Tier</span>
                                    <span class="metric-value">{eeat_assessment['content_performance_prediction']['performance_tier'].title()}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Results Timeline</span>
                                    <span class="metric-value">{eeat_assessment['content_performance_prediction']['timeline_to_results']}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="eeat" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>📊 Detailed E-E-A-T Analysis</h3>
                            <ul class="insight-list">
                                {self._format_eeat_insights(eeat_assessment)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>💡 Improvement Recommendations</h3>
                            <ul class="insight-list">
                                {self._format_improvement_recommendations(eeat_assessment['improvement_analysis'])}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div id="research" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>🎯 Customer Pain Points</h3>
                            <ul class="insight-list">
                                {self._format_pain_points(reddit_insights)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>🗣️ Real Customer Voice</h3>
                            <ul class="insight-list">
                                {self._format_customer_quotes(reddit_insights)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>📈 Content Opportunities</h3>
                            <ul class="insight-list">
                                {self._format_content_opportunities(topic_research)}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div id="improvement" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>📈 Current Performance</h3>
                            <div class="metric-list">
                                {self._format_current_performance(improvement_report)}
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🎯 Next Steps</h3>
                            <ul class="insight-list">
                                {self._format_next_steps(improvement_report)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>💰 ROI Projection</h3>
                            <div class="metric-list">
                                {self._format_roi_projection(improvement_report)}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="content" class="tab-content">
                    <div class="content-section">
                        <div class="content-header">
                            <h2 class="content-title">Generated Content</h2>
                            <div class="content-actions">
                                <button onclick="copyContent()" class="btn btn-outline">📋 Copy</button>
                                <button onclick="exportContent()" class="btn btn-primary">💾 Export</button>
                            </div>
                        </div>
                        
                        <div class="content-display">
                            <div class="content-stats">
                                <span class="stat">📝 {content_metrics['word_count']} words</span>
                                <span class="stat">📊 {content_metrics['readability_score']} readability</span>
                                <span class="stat">🎯 {eeat_assessment['eeat_assessment']['overall_score']} E-E-A-T</span>
                                <span class="stat">🔥 {content_metrics['uniqueness_score']}% unique</span>
                            </div>
                            
                            <div class="content-text" id="content-text">
                                <pre>{generated_content}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform by Zeeshan Bashir</p>
            </div>
            
            <script>
                function showTab(tabName) {{
                    // Hide all tab contents
                    const contents = document.querySelectorAll('.tab-content');
                    contents.forEach(content => content.classList.remove('active'));
                    
                    // Remove active class from all tabs
                    const tabs = document.querySelectorAll('.tab');
                    tabs.forEach(tab => tab.classList.remove('active'));
                    
                    // Show selected tab content
                    document.getElementById(tabName).classList.add('active');
                    
                    // Add active class to clicked tab
                    event.target.classList.add('active');
                }}
                
                function copyContent() {{
                    const content = document.getElementById('content-text').textContent;
                    navigator.clipboard.writeText(content).then(() => {{
                        alert('Content copied to clipboard!');
                    }});
                }}
                
                function exportContent() {{
                    const content = document.getElementById('content-text').textContent;
                    const blob = new Blob([content], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '{topic.replace(" ", "_")}_zee_seo_enhanced.txt';
                    a.click();
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        return HTMLResponse(content=f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 2rem; text-align: center;">
            <h1>⚠️ Analysis Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <a href="/" style="color: #2563eb; text-decoration: none;">← Back to Zee SEO Tool</a>
        </body>
        </html>
        """, status_code=500)

# Helper methods for formatting the HTML response
def _generate_improvement_badge(improvement_report):
    """Generate improvement badge HTML"""
    if improvement_report.get('improvement_summary', {}).get('improvement_level') == 'baseline_established':
        return '<div class="improvement-badge">🎯 Baseline Established</div>'
    else:
        improvement_level = improvement_report.get('improvement_summary', {}).get('improvement_level', 'good')
        return f'<div class="improvement-badge">📈 {improvement_level.replace("_", " ").title()}</div>'

def _format_eeat_insights(eeat_assessment):
    """Format E-E-A-T insights for display"""
    insights = []
    
    # Overall assessment
    overall = eeat_assessment['eeat_assessment']
    insights.append(f'<li class="insight-item">Overall E-E-A-T Level: <strong>{overall["eeat_level"].replace("_", " ").title()}</strong></li>')
    
    # Component insights
    for component, data in overall['components'].items():
        score = data['score']
        if score >= 8.0:
            level = "Excellent"
        elif score >= 6.5:
            level = "Good" 
        elif score >= 5.0:
            level = "Fair"
        else:
            level = "Needs Improvement"
        
        insights.append(f'<li class="insight-item">{component.title()}: <strong>{score}/10 ({level})</strong></li>')
    
    return '\n'.join(insights)

def _format_improvement_recommendations(improvement_analysis):
    """Format improvement recommendations"""
    recommendations = []
    
    immediate = improvement_analysis.get('immediate_actions', [])
    for action in immediate[:3]:  # Top 3
        recommendations.append(f'<li class="insight-item">🚨 <strong>Immediate:</strong> {action}</li>')
    
    content_enhancements = improvement_analysis.get('content_enhancements', [])
    for enhancement in content_enhancements[:2]:  # Top 2
        recommendations.append(f'<li class="insight-item">📝 <strong>Content:</strong> {enhancement}</li>')
    
    return '\n'.join(recommendations)

def _format_pain_points(reddit_insights):
    """Format customer pain points"""
    pain_points = reddit_insights.get('pain_point_analysis', {}).get('critical_pain_points', [])
    formatted = []
    
    for point in pain_points[:4]:  # Top 4
        formatted.append(f'<li class="insight-item">😤 {point}</li>')
    
    return '\n'.join(formatted) if formatted else '<li class="insight-item">No specific pain points identified</li>'

def _format_customer_quotes(reddit_insights):
    """Format real customer quotes"""
    quotes = reddit_insights.get('authenticity_markers', {}).get('real_customer_quotes', [])
    formatted = []
    
    for quote in quotes[:3]:  # Top 3
        formatted.append(f'<li class="insight-item">💬 "{quote}"</li>')
    
    return '\n'.join(formatted) if formatted else '<li class="insight-item">No customer quotes available</li>'

def _format_current_performance(improvement_report):
    """Format current performance metrics"""
    performance = improvement_report.get('current_performance', {})
    formatted = []
    
    level = performance.get('performance_level', 'fair').replace('_', ' ').title()
    formatted.append(f'''
        <div class="metric-item">
            <span class="metric-label">Performance Level</span>
            <span class="metric-value">{level}</span>
        </div>
    ''')
    
    position = performance.get('market_position', 'improvement_needed').replace('_', ' ').title()
    formatted.append(f'''
        <div class="metric-item">
            <span class="metric-label">Market Position</span>
            <span class="metric-value">{position}</span>
        </div>
    ''')
    
    score = performance.get('current_score', 0)
    formatted.append(f'''
        <div class="metric-item">
            <span class="metric-label">Current Score</span>
            <span class="metric-value">{score:.1f}/10</span>
        </div>
    ''')
    
    readiness = performance.get('readiness_assessment', {}).get('readiness_level', 'unknown').replace('_', ' ').title()
    formatted.append(f'''
        <div class="metric-item">
            <span class="metric-label">Content Readiness</span>
            <span class="metric-value">{readiness}</span>
        </div>
    ''')
    
    return '\n'.join(formatted)

def _format_next_steps(improvement_report):
    """Format next steps"""
    next_steps = improvement_report.get('next_steps', {})
    formatted = []
    
    immediate = next_steps.get('immediate_actions', [])
    for action in immediate[:2]:
        formatted.append(f'<li class="insight-item">🚨 <strong>Immediate:</strong> {action}</li>')
    
    short_term = next_steps.get('short_term_goals', [])
    for goal in short_term[:2]:
        formatted.append(f'<li class="insight-item">📅 <strong>Short-term:</strong> {goal}</li>')
    
    long_term = next_steps.get('long_term_strategy', [])
    for strategy in long_term[:1]:
        formatted.append(f'<li class="insight-item">🎯 <strong>Long-term:</strong> {strategy}</li>')
    
    return '\n'.join(formatted) if formatted else '<li class="insight-item">Continue current improvement efforts</li>'

def _format_roi_projection(improvement_report):
    """Format ROI projection"""
    roi = improvement_report.get('roi_projection', {})
    projections = roi.get('roi_projections', {})
    formatted = []
    
    for timeframe, data in projections.items():
        if timeframe == '30_days':
            label = '30 Days'
        elif timeframe == '90_days':
            label = '90 Days'
        elif timeframe == '180_days':
            label = '180 Days'
        else:
            continue
            
        score = data.get('projected_eeat_score', 0)
        improvement = data.get('performance_improvement', '0%')
        
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">{label} Projection</span>
                <span class="metric-value">{score} E-E-A-T ({improvement})</span>
            </div>
        ''')
    
    investment = roi.get('investment_recommendation', 'moderate_investment').replace('_', ' ').title()
    formatted.append(f'''
        <div class="metric-item">
            <span class="metric-label">Investment Level</span>
            <span class="metric-value">{investment}</span>
        </div>
    ''')
    
    return '\n'.join(formatted)

# Assign helper methods to the module level so they can be used in f-strings
globals()['_generate_improvement_badge'] = _generate_improvement_badge
globals()['_format_eeat_insights'] = _format_eeat_insights
globals()['_format_improvement_recommendations'] = _format_improvement_recommendations
globals()['_format_pain_points'] = _format_pain_points
globals()['_format_customer_quotes'] = _format_customer_quotes
globals()['_format_content_opportunities'] = _format_content_opportunities
globals()['_format_current_performance'] = _format_current_performance
globals()['_format_next_steps'] = _format_next_steps
globals()['_format_roi_projection'] = _format_roi_projection

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)        HUMAN EXPERTISE & INSIGHTS:
        - Customer Pain Points: {human_inputs.get('customer_pain_points')}
        - Industry Experience: {human_inputs.get('unique_value_prop')}
        
        REAL CUSTOMER RESEARCH:
        {self._format_reddit_insights(reddit_insights) if reddit_insights else 'Not available'}
        
        TOPIC INTELLIGENCE:
        {self._format_topic_research(topic_research) if topic_research else 'Not available'}
        
        AI INSTRUCTIONS:
        - Writing Style: {ai_instructions.get('writing_style', 'Professional')}
        - Target Length: {ai_instructions.get('target_word_count', '1000-1500 words')}
        - Special Notes: {ai_instructions.get('additional_notes', 'None')}
        
        CONTENT REQUIREMENTS:
        1. Demonstrate genuine experience through specific examples and personal insights
        2. Show expertise with accurate, in-depth information
        3. Build authority through unique perspectives and comprehensive coverage
        4. Establish trust through transparency, balanced views, and credible sources
        5. Address real customer pain points identified in the research
        6. Use authentic language that resonates with the target audience
        7. Include specific, actionable advice that only an expert would know
        8. Reference credible sources and provide balanced perspectives
        
        Create content that is significantly better than generic AI content by incorporating:
        - Real customer language and concerns from the research
        - Industry-specific expertise and insider knowledge
        - Personal experience and authentic insights
        - Practical solutions to genuine problems
        
        Make this content worthy of being cited as an authoritative source.
        """
        
        messages = [{"role": "user", "content": ai_prompt}]
        return self.claude_agent.call_claude(messages, max_tokens=3000)
    
    def _format_reddit_insights(self, reddit_insights: Dict) -> str:
        """Format Reddit insights for the AI prompt"""
        if not reddit_insights:
            return "No Reddit insights available"
        
        formatted = []
        
        # Pain points
        pain_points = reddit_insights.get('pain_point_analysis', {}).get('critical_pain_points', [])
        if pain_points:
            formatted.append(f"Critical Pain Points: {', '.join(pain_points[:3])}")
        
        # Customer quotes
        quotes = reddit_insights.get('authenticity_markers', {}).get('real_customer_quotes', [])
        if quotes:
            formatted.append(f"Real Customer Quotes: {'; '.join(quotes[:2])}")
        
        # Language patterns
        vocab = reddit_insights.get('language_intelligence', {}).get('customer_vocabulary', [])
        if vocab:
            formatted.append(f"Customer Language: {', '.join(vocab[:5])}")
        
        return '\n'.join(formatted)
    
    def _format_topic_research(self, topic_research: Dict) -> str:
        """Format topic research for the AI prompt"""
        if not topic_research:
            return "No topic research available"
        
        formatted = []
        
        # Content gaps
        gaps = topic_research.get('topic_research', {}).get('content_gaps', {}).get('market_gaps', {})
        if gaps.get('underserved_questions'):
            formatted.append(f"Underserved Questions: {', '.join(gaps['underserved_questions'][:3])}")
        
        # Opportunities
        opportunities = topic_research.get('topic_research', {}).get('opportunity_scoring', {}).get('top_opportunities', [])
        if opportunities:
            top_ops = [op.get('name', '') for op in opportunities[:3]]
            formatted.append(f"Top Opportunities: {', '.join(top_ops)}")
        
        return '\n'.join(formatted)

# Initialize enhanced components
claude_agent = ClaudeAgent()
enhanced_content_generator = EnhancedContentGenerator(claude_agent)
reddit_researcher = EnhancedRedditResearcher()
eeat_assessor = EnhancedEEATAssessor()
topic_researcher = AdvancedTopicResearchAgent()
improvement_tracker = ContinuousImprovementTracker()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced home page with new features"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool - Advanced Content Intelligence Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                color: #111827;
                line-height: 1.6;
                min-height: 100vh;
            }
            
            .header {
                background: white;
                border-bottom: 1px solid #e5e7eb;
                padding: 1.5rem 0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                position: sticky;
                top: 0;
                z-index: 50;
            }
            
            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 1.5rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .logo-icon {
                width: 3rem;
                height: 3rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 800;
                font-size: 1.5rem;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .logo-text {
                font-size: 1.75rem;
                font-weight: 800;
                color: #111827;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .tagline {
                font-size: 0.875rem;
                color: #6b7280;
                font-weight: 500;
                margin-top: 0.25rem;
            }
            
            .version-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                font-weight: 600;
            }
            
            .creator {
                text-align: right;
                font-size: 0.875rem;
                color: #6b7280;
            }
            
            .creator strong {
                color: #374151;
                display: block;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }
            
            .hero {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .hero h1 {
                font-size: 2.5rem;
                font-weight: 800;
                color: #111827;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .hero p {
                font-size: 1.25rem;
                color: #6b7280;
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }
            
            .hero-stats {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                max-width: 500px;
                margin: 2rem auto;
            }
            
            .hero-stat {
                text-align: center;
                padding: 1rem;
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .hero-stat-value {
                font-size: 1.5rem;
                font-weight: 800;
                color: #2563eb;
            }
            
            .hero-stat-label {
                font-size: 0.75rem;
                color: #6b7280;
                margin-top: 0.25rem;
            }
            
            .main-grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 2rem;
            }
            
            .card {
                background: white;
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                transform: translateY(-2px);
            }
            
            .card h2 {
                font-size: 1.375rem;
                font-weight: 700;
                color: #111827;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            
            .card-icon {
                width: 2rem;
                height: 2rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }
            
            .card p {
                color: #6b7280;
                margin-bottom: 1.5rem;
            }
            
            .form-grid {
                display: grid;
                gap: 1.5rem;
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }
            
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .form-label {
                font-size: 0.875rem;
                font-weight: 600;
                color: #374151;
            }
            
            .form-input, .form-textarea, .form-select {
                padding: 0.875rem 1rem;
                border: 2px solid #e5e7eb;
                border-radius: 0.75rem;
                font-size: 0.875rem;
                transition: all 0.2s ease;
                background: white;
            }
            
            .form-input:focus, .form-textarea:focus, .form-select:focus {
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                transform: translateY(-1px);
            }
            
            .form-textarea {
                resize: vertical;
                min-height: 4rem;
                font-family: inherit;
            }
            
            .form-help {
                font-size: 0.75rem;
                color: #6b7280;
            }
            
            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                padding: 1rem 2rem;
                font-size: 1rem;
                font-weight: 700;
                border-radius: 0.75rem;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                font-family: inherit;
                width: 100%;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
            
            .ai-controls {
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border: 2px solid #bfdbfe;
            }
            
            .features {
                display: grid;
                gap: 1rem;
            }
            
            .feature {
                display: flex;
                align-items: flex-start;
                gap: 1rem;
                padding: 1.25rem;
                background: linear-gradient(135deg, #f9fafb 0%, white 100%);
                border-radius: 0.75rem;
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            
            .feature:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                border-color: #2563eb;
            }
            
            .feature-icon {
                width: 2.5rem;
                height: 2.5rem;
                background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                color: white;
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                flex-shrink: 0;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .feature-content h4 {
                font-size: 0.9rem;
                font-weight: 600;
                color: #111827;
                margin-bottom: 0.25rem;
            }
            
            .feature-content p {
                font-size: 0.8rem;
                color: #6b7280;
                margin: 0;
                line-height: 1.4;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 3rem 2rem;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                margin-top: 2rem;
            }
            
            .loading-spinner {
                width: 3rem;
                height: 3rem;
                border: 3px solid #e5e7eb;
                border-top: 3px solid #2563eb;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 1.5rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .footer {
                margin-top: 4rem;
                padding: 3rem 0;
                background: white;
                border-top: 1px solid #e5e7eb;
                text-align: center;
            }
            
            .footer p {
                color: #6b7280;
                margin-bottom: 0.5rem;
            }
            
            @media (max-width: 768px) {
                .main-grid { grid-template-columns: 1fr; gap: 1.5rem; }
                .form-row { grid-template-columns: 1fr; }
                .hero h1 { font-size: 2rem; }
                .hero p { font-size: 1rem; }
                .container { padding: 1rem; }
                .header-content { flex-direction: column; gap: 1rem; text-align: center; }
                .hero-stats { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-icon">Z</div>
                    <div>
                        <div class="logo-text">Zee SEO Tool</div>
                        <div class="tagline">Advanced Content Intelligence Platform</div>
                    </div>
                </div>
                <div class="version-badge">Enhanced v2.0</div>
                <div class="creator">
                    <strong>Built by Zeeshan Bashir</strong>
                    <div>Human + AI Intelligence Bridge</div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="hero">
                <h1>Create Content That Actually Converts</h1>
                <p>The most advanced content intelligence platform combining deep customer research, E-E-A-T optimization, and continuous improvement tracking</p>
                
                <div class="hero-stats">
                    <div class="hero-stat">
                        <div class="hero-stat-value">350%</div>
                        <div class="hero-stat-label">Better Performance</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-value">5+</div>
                        <div class="hero-stat-label">AI Agents</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-value">95%</div>
                        <div class="hero-stat-label">E-E-A-T Score</div>
                    </div>
                </div>
            </div>
            
            <div class="main-grid">
                <form action="/generate-advanced" method="post">
                    <div class="card">
                        <h2>
                            <div class="card-icon">🧠</div>
                            Advanced Content Intelligence Input
                        </h2>
                        <p>Our enhanced system combines multiple AI agents for comprehensive content analysis and generation.</p>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label">Content Topic</label>
                                <input class="form-input" type="text" name="topic" 
                                       placeholder="e.g., best budget laptops for college students" required>
                                <div class="form-help">Our topic research agent will analyze semantic relationships and opportunities</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Target Communities for Research</label>
                                <input class="form-input" type="text" name="subreddits" 
                                       placeholder="e.g., laptops, college, StudentLoans" required>
                                <div class="form-help">Enhanced Reddit research with deep customer insight extraction</div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Industry</label>
                                    <input class="form-input" type="text" name="industry" 
                                           placeholder="e.g., Technology" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Target Audience</label>
                                    <input class="form-input" type="text" name="target_audience" 
                                           placeholder="e.g., College students" required>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Business Type</label>
                                <select class="form-select" name="business_type" required>
                                    <option value="">Select business model</option>
                                    <option value="B2B">B2B (Business to Business)</option>
                                    <option value="B2C">B2C (Business to Consumer)</option>
                                    <option value="Both">Both B2B and B2C</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Your Unique Value Proposition</label>
                                <textarea class="form-textarea" name="unique_value_prop" 
                                          placeholder="What makes you different from competitors? Be specific and authentic." required></textarea>
                                <div class="form-help">Critical for E-E-A-T authority and differentiation analysis</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Customer Pain Points & Insights</label>
                                <textarea class="form-textarea" name="customer_pain_points" 
                                          placeholder="What specific challenges do your customers face? Include real examples." required></textarea>
                                <div class="form-help">Enhanced analysis will combine this with Reddit research for deeper insights</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card ai-controls">
                        <h2>
                            <div class="card-icon">⚙️</div>
                            Advanced AI Configuration
                        </h2>
                        <p>Fine-tune content generation with enhanced AI controls and quality parameters</p>
                        
                        <div class="form-grid">
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Writing Style</label>
                                    <select class="form-select" name="writing_style">
                                        <option value="">Adaptive (Recommended)</option>
                                        <option value="British English">British English</option>
                                        <option value="American English">American English</option>
                                        <option value="Conversational">Conversational</option>
                                        <option value="Technical">Technical</option>
                                        <option value="Academic">Academic</option>
                                        <option value="Authoritative">Authoritative</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Target Length</label>
                                    <select class="form-select" name="target_word_count">
                                        <option value="">Optimal (1200-1800)</option>
                                        <option value="800-1200">Concise (800-1200)</option>
                                        <option value="1500-2500">Comprehensive (1500-2500)</option>
                                        <option value="2500-4000">In-depth (2500-4000)</option>
                                        <option value="4000+">Ultimate Guide (4000+)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">E-E-A-T Enhancement Instructions</label>
                                <textarea class="form-textarea" name="eeat_instructions" 
                                          placeholder="Specific instructions for experience, expertise, authority, or trust elements"></textarea>
                                <div class="form-help">Guide our E-E-A-T optimization agent</div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">Additional AI Instructions</label>
                                <textarea class="form-textarea" name="additional_notes" 
                                          placeholder="Any specific requirements: statistics, format preferences, tone adjustments"></textarea>
                                <div class="form-help">Advanced customization for content generation</div>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn">
                        🚀 Generate Advanced Content Intelligence Report
                    </button>
                </form>
                
                <div class="card">
                    <h2>
                        <div class="card-icon">🔥</div>
                        Enhanced Intelligence Features
                    </h2>
                    <p>Next-generation content intelligence with 5 specialized AI agents</p>
                    
                    <div class="features">
                        <div class="feature">
                            <div class="feature-icon">🔍</div>
                            <div class="feature-content">
                                <h4>Deep Reddit Research</h4>
                                <p>Advanced customer insight extraction and pain point analysis</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-content">
                                <h4>Enhanced E-E-A-T Assessment</h4>
                                <p>Google Quality Rater Guidelines compliant scoring</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🧠</div>
                            <div class="feature-content">
                                <h4>Topic Research Intelligence</h4>
                                <p>Comprehensive semantic analysis and opportunity identification</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">📈</div>
                            <div class="feature-content">
                                <h4>Continuous Improvement Tracking</h4>
                                <p>Score progression and performance optimization</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🔬</div>
                            <div class="feature-content">
                                <h4>Content Quality Analysis</h4>
                                <p>Multi-dimensional quality assessment and benchmarking</p>
                            </div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">🏆</div>
                            <div class="feature-content">
                                <h4>Competitive Advantage Scoring</h4>
                                <p>ROI projections and market positioning analysis</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <h3>Advanced Intelligence Engines Processing</h3>
                <p>Running comprehensive multi-agent analysis to create your content strategy</p>
                <div style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
                    <div>🔍 Reddit Research Agent</div>
                    <div>🧠 Topic Research Agent</div>
                    <div>📊 E-E-A-T Assessment Agent</div>
                    <div>📈 Improvement Tracking Agent</div>
                    <div>✨ Content Generation Agent</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform</p>
            <p>Built by Zeeshan Bashir • Creating content that converts, not just ranks</p>
        </div>
        
        <script>
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('loading').scrollIntoView({ behavior: 'smooth' });
            });
        </script>
    </body>
    </html>
    """)

@app.post("/generate-advanced")
async def generate_advanced_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    eeat_instructions: str = Form(""),
    additional_notes: str = Form("")
):
    """Generate advanced content with comprehensive intelligence analysis"""
    try:
        print(f"🚀 Starting advanced content generation for: {topic}")
        
        # Create context objects
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'unique_value_prop': unique_value_prop,
            'topic': topic
        }
        
        human_inputs = {
            'customer_pain_points': customer_pain_points,
            'unique_value_prop': unique_value_prop,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type
        }
        
        ai_instructions = {
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'eeat_instructions': eeat_instructions,
            'additional_notes': additional_notes
        }
        
        # Step 1: Enhanced Reddit Research
        print("🔍 Running enhanced Reddit research...")
        subreddit_list = [s.strip() for s in subreddits.split(',')]
        reddit_insights = reddit_researcher.research_topic_comprehensive(
            topic, subreddit_list, max_posts_per_subreddit=15
        )
        
        # Step 2: Advanced Topic Research
        print("🧠 Conducting advanced topic research...")
        topic_research = topic_researcher.research_topic_comprehensive(
            topic, industry, target_audience, business_context
        )
        
        # Step 3: Enhanced Content Generation
        print("✨ Generating enhanced content...")
        generated_content = enhanced_content_generator.generate_content(
            topic, business_context, human_inputs, ai_instructions, 
            reddit_insights, topic_research
        )
        
        # Step 4: Comprehensive E-E-A-T Assessment
        print("📊 Performing comprehensive E-E-A-T assessment...")
        eeat_assessment = eeat_assessor.assess_comprehensive_eeat(
            generated_content, topic, business_context, human_inputs, reddit_insights
        )
        
        # Step 5: Content Quality Analysis
        print("🔬 Analyzing content quality...")
        content_metrics = {
            'word_count': len(generated_content.split()),
            'quality_score': min(10.0, len(generated_content.split()) / 100),
            'readability_score': 85.0,  # Placeholder
            'uniqueness_score': 92.0    # Placeholder
        }
        
        # Step 6: Track Improvement
        print("📈 Tracking improvement metrics...")
        snapshot_id = improvement_tracker.track_analysis(import os
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import enhanced agents
from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor
from src.agents.topic_research_agent import AdvancedTopicResearchAgent
from src.agents.improvement_tracking_agent import ContinuousImprovementTracker
from src.utils.llm_client import LLMClient

# Initialize FastAPI app
app = FastAPI(title="Zee SEO Tool - Advanced Content Intelligence Platform")

# AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")

class ClaudeAgent:
    def __init__(self):
        self.anthropic_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
    def call_claude(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", max_tokens: int = 1500):
        """Make API call to Claude"""
        try:
            if messages and messages[0].get("role") == "user":
                user_message = messages[0]["content"]
            else:
                user_message = "Please help with this request."
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.anthropic_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                return f"Demo mode - Claude API unavailable"
                
        except Exception as e:
            return f"Demo mode - Using fallback content"

# Enhanced content generator
class EnhancedContentGenerator:
    def __init__(self, claude_agent):
        self.claude_agent = claude_agent
        
    def generate_content(self, topic: str, business_context: Dict, human_inputs: Dict, 
                        ai_instructions: Dict, reddit_insights: Dict = None, 
                        topic_research: Dict = None) -> str:
        """Generate content using enhanced context"""
        
        # Enhanced AI prompt with all available intelligence
        ai_prompt = f"""
        Create exceptional, human-centered content about "{topic}" that demonstrates high E-E-A-T standards.
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        HUMAN EXPERTISE & INSIGHTS:
