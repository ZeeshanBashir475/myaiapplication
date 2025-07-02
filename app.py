import os
import sys
# Ensure src directory is on the Python path
dir_path = os.path.dirname(__file__)
sys.path.append(os.path.join(dir_path, "src"))

import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn

# Import enhanced agents (updated module paths)
from src.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.customer_journey_mapper import CustomerJourneyMapper
from src.intent_classifier import IntentClassifier
from src.human_input_identifier import HumanInputIdentifier
from src.full_content_generator import FullContentGenerator
from src.enhanced_eeat_assessor import EnhancedEEATAssessor
from src.content_type_classifier import ContentTypeClassifier
from src.content_quality_scorer import ContentQualityScorer
from src.business_context_collector import BusinessContextCollector
from src.content_analysis_snapshot import ContentAnalysisSnapshot
from src.advanced_topic_research_agent import AdvancedTopicResearchAgent
from src.improvement_tracking_agent import ContinuousImprovementTracker

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
    <html><head><meta charset="UTF-8"><title>Zee SEO Tool</title></head><body>
    <h1>Zee SEO Tool - Advanced Content Intelligence Platform</h1>
    <form action="/generate-advanced" method="post">
        <label>Topic:<input name="topic" required></label><br>
        <label>Subreddits:<input name="subreddits" required></label><br>
        <label>Industry:<input name="industry" required></label><br>
        <label>Audience:<input name="target_audience" required></label><br>
        <label>Business Type:<input name="business_type" required></label><br>
        <label>Unique Value:<textarea name="unique_value_prop" required></textarea></label><br>
        <label>Pain Points:<textarea name="customer_pain_points" required></textarea></label><br>
        <label>Style:<input name="writing_style"></label><br>
        <label>Word Count:<input name="target_word_count"></label><br>
        <label>Notes:<textarea name="additional_notes"></textarea></label><br>
        <button type="submit">Generate Report</button>
    </form></body></html>
    """
)

@app.post("/generate-advanced")
async def generate_advanced_content(
    topic: str = Form(...), subreddits: str = Form(...), industry: str = Form(...),
    target_audience: str = Form(...), business_type: str = Form(...),
    unique_value_prop: str = Form(...), customer_pain_points: str = Form(...),
    writing_style: str = Form(""), target_word_count: str = Form(""),
    additional_notes: str = Form("")
):
    # Business context
    biz_ctx = business_collector.collect(industry, target_audience, business_type, unique_value_prop)
    # Human inputs
    human_inputs = human_input_id.identify(customer_pain_points)
    # Research
    subs = [s.strip() for s in subreddits.split(',')]
    reddit_data = reddit_researcher.research(topic, subs)
    journey = journey_mapper.map_research(reddit_data)
    intents = intent_classifier.classify(topic)
    topic_data = topic_researcher.research(topic, industry, target_audience, biz_ctx)
    # Generate content
    content = content_generator.generate(topic, biz_ctx, human_inputs, intents, additional_notes)
    # Assess
    eeat = eeat_assessor.assess(content, biz_ctx, human_inputs)
    ctype = type_classifier.classify(content)
    quality = quality_scorer.score(content)
    # Take snapshot
    snapshotter.save(topic, content, eeat, quality)
    # Track improvement
    improvement = improvement_tracker.track(topic, eeat)
    # Render response
    html = f"""
    <html><body><h1>Report: {topic}</h1>
    <h2>EEAT Score: {eeat['overall_score']}</h2>
    <h3>Content Type: {ctype}</h3>
    <h3>Quality: {quality['score']}</h3>
    <p>Improvement Level: {improvement['level']}</p>
    <h2>Generated Content</h2><pre>{content}</pre>
    </body></html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
