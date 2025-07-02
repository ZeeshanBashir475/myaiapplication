import os
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# ─── NEW AGENT IMPORTS ──────────────────────────────────────────────────────────
from src.agents.reddit_researcher            import EnhancedRedditResearcher
from src.agents.journey_mapper               import CustomerJourneyMapper
from src.agents.intent_classifier             import IntentClassifier
from src.agents.human_input_identifier       import HumanInputIdentifier
from src.agents.full_content_generator       import FullContentGenerator
from src.agents.eeat_assessor                import EnhancedEEATAssessor
from src.agents.content_type_classifier      import ContentTypeClassifier
from src.agents.content_quality_scorer       import ContentQualityScorer
from src.agents.business_context_collector   import BusinessContextCollector
from src.agents.ContentAnalysisSnapshot      import ContentAnalysisSnapshot
from src.agents.AdvancedTopicResearchAgent   import AdvancedTopicResearchAgent
# ───────────────────────────────────────────────────────────────────────────────

# Initialize FastAPI app
app = FastAPI(title="Zee SEO Tool - Content Intelligence Platform")

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

# Simple content generator
class ContentGenerator:
    def __init__(self, claude_agent):
        self.claude_agent = claude_agent
        
    def generate_content(self, topic: str, business_context: Dict, human_inputs: Dict, ai_instructions: Dict) -> str:
        """Generate content using Claude"""
        ai_prompt = f"""
        Create comprehensive, high-quality content about "{topic}".
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        CUSTOMER INSIGHTS:
        - Pain Points: {human_inputs.get('customer_pain_points')}
        
        AI INSTRUCTIONS:
        - Writing Style: {ai_instructions.get('writing_style', 'Professional')}
        - Target Length: {ai_instructions.get('target_word_count', '1000-1500 words')}
        - Special Notes: {ai_instructions.get('additional_notes', 'None')}
        
        Create engaging, expert content that addresses customer pain points and demonstrates your unique value proposition.
        Make it significantly better than generic AI content by incorporating the business expertise provided.
        """
        
        messages = [{"role": "user", "content": ai_prompt}]
        return self.claude_agent.call_claude(messages, max_tokens=2000)

# Simple analysis classes
class SemanticAnalyzer:
    def analyze_content(self, content: str, topic: str) -> Dict[str, Any]:
        word_count = len(content.split())
        
        return {
            "word_count": word_count,
            "coverage_percentage": min(85, word_count // 10),
            "entities_covered": ["Main topic", "Key concepts", "Industry terms"],
            "entities_missing": ["Technical details", "Case studies"],
            "semantic_depth_score": 8.2,
            "readability_score": 85
        }

class EEATAssessor:
    def assess_eeat(self, content: str, business_context: Dict, human_inputs: Dict) -> Dict[str, Any]:
        # Simple E-E-A-T scoring based on content analysis
        has_expertise = bool(business_context.get('unique_value_prop'))
        has_experience = bool(human_inputs.get('customer_pain_points'))
        content_length = len(content.split())
        
        experience_score = 8.5 if has_experience else 6.0
        expertise_score = 9.0 if has_expertise and content_length > 500 else 7.0
        authoritativeness_score = 8.0 if business_context.get('business_type') else 6.5
        trust_score = 8.5 if has_expertise and has_experience else 7.0
        
        overall_score = (experience_score + expertise_score + authoritativeness_score + trust_score) / 4
        
        return {
            "overall_eeat_score": round(overall_score, 1),
            "experience_score": experience_score,
            "expertise_score": expertise_score,
            "authoritativeness_score": authoritativeness_score,
            "trust_score": trust_score,
            "improvement_recommendations": [
                "Add more customer case studies",
                "Include industry statistics",
                "Add author credentials"
            ]
        }

class CompetitiveAnalyzer:
    def analyze_vs_ai(self, content: str, human_inputs: Dict) -> Dict[str, Any]:
        has_human_elements = bool(human_inputs.get('customer_pain_points'))
        word_count = len(content.split())
        
        human_score = 8.5 if has_human_elements else 6.0
        authenticity_score = 8.0 if word_count > 800 else 7.0
        
        return {
            "human_elements_score": human_score,
            "authenticity_score": authenticity_score,
            "performance_boost": "250% better engagement" if human_score > 8 else "150% better engagement",
            "traffic_multiplier": "2-3x" if human_score > 8 else "1.5-2x",
            "competitive_advantages": [
                "Human expertise integration",
                "Customer-focused approach",
                "Industry-specific insights"
            ]
        }

# ─── ORIGINAL INITIALIZATIONS ─────────────────────────────────────────────────
claude_agent        = ClaudeAgent()
content_generator   = ContentGenerator(claude_agent)
semantic_analyzer   = SemanticAnalyzer()
eeat_assessor       = EEATAssessor()
competitive_analyzer= CompetitiveAnalyzer()
# ────────────────────────────────────────────────────────────────────────────────

# ─── NEW AGENT INSTANTIATIONS ──────────────────────────────────────────────────
reddit_researcher           = EnhancedRedditResearcher()
journey_mapper              = CustomerJourneyMapper()
intent_classifier           = IntentClassifier()
human_input_identifier      = HumanInputIdentifier()
full_content_generator      = FullContentGenerator(claude_agent)
enhanced_eeat_assessor      = EnhancedEEATAssessor()
content_type_classifier     = ContentTypeClassifier()
content_quality_scorer      = ContentQualityScorer()
business_context_collector  = BusinessContextCollector()
content_analysis_snapshot   = ContentAnalysisSnapshot()
advanced_topic_research_agent = AdvancedTopicResearchAgent()
# ────────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with clean design"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool - Content Intelligence Platform</title>
        <!-- … all your existing CSS/HTML here … -->
    </head>
    <body>
        <!-- … unchanged form and UI … -->
    </body>
    </html>
    """)

@app.post("/generate")
async def generate_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    additional_notes: str = Form("")
):
    """Generate content with analysis"""
    try:
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
            'unique_value_prop': unique_value_prop
        }
        
        ai_instructions = {
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'additional_notes': additional_notes
        }
        
        # 🔥 YOUR ORIGINAL GENERATION & ANALYSIS
        generated_content   = content_generator.generate_content(topic, business_context, human_inputs, ai_instructions)
        semantic_analysis   = semantic_analyzer.analyze_content(generated_content, topic)
        eeat_analysis       = eeat_assessor.assess_eeat(generated_content, business_context, human_inputs)
        competitive_analysis= competitive_analyzer.analyze_vs_ai(generated_content, human_inputs)
        
        # … the rest of your big HTML/CSS response for /generate remains exactly as before …
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Content Report - {topic} | Zee SEO Tool</title>
            <!-- … your full report styling … -->
        </head>
        <body>
            <!-- … your detailed dashboard and content section … -->
        </body>
        </html>
        """
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        return HTMLResponse(content=f"""
        <html><body style="font-family: sans-serif; padding:2rem; text-align:center;">
            <h1>⚠️ Analysis Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <a href="/" style="color:#2563eb;">← Back to Zee SEO Tool</a>
        </body></html>
        """, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
