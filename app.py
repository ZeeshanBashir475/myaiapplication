import os
import sys
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Ensure src/agents directory is on the Python path
base_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(base_dir, "src", "agents"))

# Import all agent classes
from enhanced_reddit_researcher import EnhancedRedditResearcher
from journey_mapper import CustomerJourneyMapper
from intent_classifier import IntentClassifier
from human_input_identifier import HumanInputIdentifier
from full_content_generator import FullContentGenerator
from eeat_assessor import EnhancedEEATAssessor
from content_type_classifier import ContentTypeClassifier
from content_quality_scorer import ContentQualityScorer
from business_context_collector import BusinessContextCollector
from content_analysis_snapshot import ContentAnalysisSnapshot
from AdvancedTopicResearchAgent import AdvancedTopicResearchAgent
from improvement_tracking_agent import ContinuousImprovementTracker

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

    def call_claude(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", max_tokens: int = 1500) -> str:
        try:
            user_message = messages[0]["content"] if messages and messages[0].get("role") == "user" else "Please help with this request."
            payload = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": user_message}]}
            resp = requests.post("https://api.anthropic.com/v1/messages", headers=self.anthropic_headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()["content"][0]["text"]
            return "Demo mode - Claude API unavailable"
        except Exception:
            return "Demo mode - Using fallback content"

# Initialize agents
claude_agent = ClaudeAgent()
reddit_researcher = EnhancedRedditResearcher()
journey_mapper = CustomerJourneyMapper()
intent_classifier = IntentClassifier()
human_input_id = HumanInputIdentifier()
content_generator = FullContentGenerator(claude_agent)
eeat_assessor = EnhancedEEATAssessor()
type_classifier = ContentTypeClassifier()
quality_scorer = ContentQualityScorer()
business_collector = BusinessContextCollector()
snapshotter = ContentAnalysisSnapshot()
topic_researcher = AdvancedTopicResearchAgent()
improvement_tracker = ContinuousImprovementTracker()

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Zee SEO Tool - Advanced Content Intelligence Platform</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%); color: #111827; line-height: 1.6; min-height: 100vh; }
        .header { background: white; border-bottom: 1px solid #e5e7eb; padding: 1.5rem 0; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); position: sticky; top: 0; z-index: 50; }
        .header-content { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; display: flex; align-items: center; justify-content: space-between; }
        .logo { display: flex; align-items: center; gap: 1rem; }
        .logo-icon { width: 3rem; height: 3rem; background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .logo-text { font-size: 1.75rem; font-weight: 800; color: #111827; background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tagline { font-size: 0.875rem; color: #6b7280; font-weight: 500; margin-top: 0.25rem; }
        .version-badge { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; }
        .creator { text-align: right; font-size: 0.875rem; color: #6b7280; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
        .hero { text-align: center; margin-bottom: 3rem; }
        .hero h1 { font-size: 2.5rem; font-weight: 800; color: #111827; margin-bottom: 1rem; line-height: 1.2; }
        .hero p { font-size: 1.25rem; color: #6b7280; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto; }
        .main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; }
        .card, .card.ai-controls, .card.features { background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #f3f4f6; transition: all 0.3s ease; }
        .card:hover, .card.ai-controls:hover, .card.features:hover { transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
        .form-group { margin-bottom: 1rem; }
        .form-label { display: block; font-size: 0.875rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem; }
        .form-input, .form-textarea, .form-select { width: 100%; padding: 0.875rem 1rem; border: 2px solid #e5e7eb; border-radius: 0.75rem; background: white; font-size: 0.875rem; transition: all 0.2s ease; }
        .btn { display: inline-flex; align-items: center; padding: 1rem 2rem; font-size: 1rem; font-weight: 700; border-radius: 0.75rem; border: none; cursor: pointer; background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); color: white; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-icon">Z</div>
                <div class="logo-text">Zee SEO Tool</div>
            </div>
            <div class="version-badge">v2.0</div>
            <div class="creator"><strong>Built by Zeeshan Bashir</strong></div>
        </div>
    </div>
    <div class="container">
        <div class="hero">
            <h1>Create Content That Actually Converts</h1>
            <p>Advanced Content Intelligence Platform combining deep research, E-E-A-T optimization, and continuous improvement</p>
        </div>
        <div class="main-grid">
            <form action="/generate-advanced" method="post">
                <div class="card">
                    <h2>🧠 Advanced Input</h2>
                    <div class="form-group"><label class="form-label">Topic<input class="form-input" type="text" name="topic" required></label></div>
                    <div class="form-group"><label class="form-label">Subreddits<input class="form-input" type="text" name="subreddits" required></label></div>
                    <div class="form-group"><label class="form-label">Industry<input class="form-input" type="text" name="industry" required></label></div>
                    <div class="form-group"><label class="form-label">Audience<input class="form-input" type="text" name="target_audience" required></label></div>
                    <div class="form-group"><label class="form-label">Business Type<select class="form-select" name="business_type" required><option value="B2B">B2B</option><option value="B2C">B2C</option></select></label></div>
                    <div class="form-group"><label class="form-label">Unique Value<textarea class="form-textarea" name="unique_value_prop" required></textarea></label></div>
                    <div class="form-group"><label class="form-label">Pain Points<textarea class="form-textarea" name="customer_pain_points" required></textarea></label></div>
                </div>
                <div class="card ai-controls">
                    <h2>⚙️ AI Settings</h2>
                    <div class="form-group"><label class="form-label">Writing Style<select class="form-select" name="writing_style"><option value="">Adaptive</option><option value="Conversational">Conversational</option></select></label></div>
                    <div class="form-group"><label class="form-label">Word Count<select class="form-select" name="target_word_count"><option value="">Optimal</option><option value="1500-2500">1500-2500</option></select></label></div>
                    <div class="form-group"><label class="form-label">Additional Notes<textarea class="form-textarea" name="additional_notes"></textarea></label></div>
                </div>
                <button type="submit" class="btn">🚀 Generate Report</button>
            </form>
        </div>
    </div>
</body>
</html>
    """
)

@app.post("/generate-advanced", response_class=HTMLResponse)
async def generate_advanced_content(
    topic: str = Form(...), subreddits: str = Form(...), industry: str = Form(...),
    target_audience: str = Form(...), business_type: str = Form(...),
    unique_value_prop: str = Form(...), customer_pain_points: str = Form(...),
    writing_style: str = Form(""), target_word_count: str = Form(""),
    additional_notes: str = Form("")
):
    try:
        biz_ctx = business_collector.collect(industry, target_audience, business_type, unique_value_prop)
        human_inputs = human_input_id.identify(customer_pain_points)
        subs = [s.strip() for s in subreddits.split(',')]
        reddit_data = reddit_researcher.research(topic, subs)
        journey = journey_mapper.map_research(reddit_data)
        intents = intent_classifier.classify(topic)
        topic_data = topic_researcher.research(topic, industry, target_audience, biz_ctx)
        content = content_generator.generate(topic, biz_ctx, human_inputs, intents, additional_notes)
        eeat = eeat_assessor.assess(content, biz_ctx, human_inputs)
        ctype = type_classifier.classify(content)
        quality = quality_scorer.score(content)
        snapshotter.save(topic, content, eeat, quality)
        improvement = improvement_tracker.track(topic, eeat)
        html = f"""
        <!DOCTYPE html>
        <html><head><title>Report - {topic}</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>
        <h1>Report: {topic}</h1>
        <h2>EEAT: {eeat['overall_score']}</h2>
        <h3>Content Type: {ctype}</h3>
        <h3>Quality Score: {quality['score']}</h3>
        <h3>Improvement Level: {improvement['level']}</h3>
        <pre>{content}</pre>
        </body></html>
        """
        return HTMLResponse(html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
