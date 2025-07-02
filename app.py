import os
import sys
# Ensure src directory is on the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Import enhanced agents
from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor
from src.agents.topic_research_agent import AdvancedTopicResearchAgent
from src.agents.improvement_tracking_agent import ContinuousImprovementTracker

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
        """Call Claude API with a user prompt"""
        try:
            user_message = messages[0]["content"] if messages and messages[0].get("role") == "user" else "Please help with this request."
            payload = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": user_message}]}
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.anthropic_headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            return "Demo mode - Claude API unavailable"
        except Exception:
            return "Demo mode - Using fallback content"

# Agents
claude_agent = ClaudeAgent()
reddit_researcher = EnhancedRedditResearcher()
eeat_assessor = EnhancedEEATAssessor()
topic_researcher = AdvancedTopicResearchAgent()
improvement_tracker = ContinuousImprovementTracker()
enhanced_content_generator = None  # Initialized in endpoint

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main input form"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Zee SEO Tool</title></head>
    <body>
        <h1>Zee SEO Tool - Advanced Content Intelligence Platform</h1>
        <form action="/generate-advanced" method="post">
            <!-- Input fields -->
            <label>Topic:<input name="topic" required></label><br>
            <label>Subreddits:<input name="subreddits" required></label><br>
            <label>Industry:<input name="industry" required></label><br>
            <label>Target Audience:<input name="target_audience" required></label><br>
            <label>Business Type:<input name="business_type" required></label><br>
            <label>Unique Value Prop:<textarea name="unique_value_prop" required></textarea></label><br>
            <label>Customer Pain Points:<textarea name="customer_pain_points" required></textarea></label><br>
            <label>Writing Style:<input name="writing_style"></label><br>
            <label>Target Word Count:<input name="target_word_count"></label><br>
            <label>Additional Notes:<textarea name="additional_notes"></textarea></label><br>
            <button type="submit">Generate Report</button>
        </form>
    </body>
    </html>
    """ )

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
    additional_notes: str = Form("")
):
    """Generate advanced content intelligence report"""
    # Context objects
    business_context = {
        'industry': industry,
        'target_audience': target_audience,
        'business_type': business_type,
        'unique_value_prop': unique_value_prop
    }
    human_inputs = {
        'customer_pain_points': customer_pain_points
    }
    ai_instructions = {
        'writing_style': writing_style,
        'target_word_count': target_word_count,
        'additional_notes': additional_notes
    }

    # 1. Reddit research
    sub_list = [s.strip() for s in subreddits.split(',')]
    reddit_insights = reddit_researcher.research_topic_comprehensive(topic, sub_list, max_posts_per_subreddit=15)

    # 2. Topic research
    topic_research = topic_researcher.research_topic_comprehensive(topic, industry, target_audience, business_context)

    # 3. Generate content
    from src.agents.enhanced_content_generator import EnhancedContentGenerator
    enhanced_content_generator = EnhancedContentGenerator(claude_agent)
    generated_content = enhanced_content_generator.generate_content(
        topic, business_context, human_inputs, ai_instructions, reddit_insights, topic_research
    )

    # 4. E-E-A-T assessment
    eeat_assessment = eeat_assessor.assess_comprehensive_eeat(
        generated_content, topic, business_context, human_inputs, reddit_insights
    )

    # 5. Content quality metrics
    word_count = len(generated_content.split())
    content_metrics = {
        'word_count': word_count,
        'readability_score': 85.0,
        'uniqueness_score': 92.0
    }

    # 6. Improvement tracker
    snapshot_id = improvement_tracker.track_analysis(
        topic,
        eeat_assessment['eeat_assessment'],
        eeat_assessment['human_vs_ai_analysis'],
        content_metrics,
        business_context,
        human_inputs
    )
    improvement_report = improvement_tracker.generate_improvement_report(snapshot_id)

    # 7. Render HTML report (simplified)
    html = f"""
    <html><body>
    <h1>Report for {topic}</h1>
    <p><strong>Generated Content:</strong></p><pre>{generated_content}</pre>
    <p><strong>E-E-A-T Score:</strong> {eeat_assessment['eeat_assessment']['overall_score']}</p>
    <p><strong>Improvement Level:</strong> {improvement_report['improvement_summary']['improvement_level']}</p>
    </body></html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
