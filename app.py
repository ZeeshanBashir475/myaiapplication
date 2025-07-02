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
                
        except Exception:
            return f"Demo mode - Using fallback content"

# Enhanced content generator
class EnhancedContentGenerator:
    def __init__(self, claude_agent):
        self.claude_agent = claude_agent
        
    def generate_content(self, topic: str, business_context: Dict, human_inputs: Dict, 
                        ai_instructions: Dict, reddit_insights: Dict = None, 
                        topic_research: Dict = None) -> str:
        """Generate content using enhanced context"""
        
        ai_prompt = f"""
        Create exceptional, human-centered content about \"{topic}\" that demonstrates high E-E-A-T standards.
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        HUMAN EXPERTISE & INSIGHTS:
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
        if not reddit_insights:
            return "No Reddit insights available"
        formatted = []
        pain_points = reddit_insights.get('pain_point_analysis', {}).get('critical_pain_points', [])
        if pain_points:
            formatted.append(f"Critical Pain Points: {', '.join(pain_points[:3])}")
        quotes = reddit_insights.get('authenticity_markers', {}).get('real_customer_quotes', [])
        if quotes:
            formatted.append(f"Real Customer Quotes: {'; '.join(quotes[:2])}")
        vocab = reddit_insights.get('language_intelligence', {}).get('customer_vocabulary', [])
        if vocab:
            formatted.append(f"Customer Language: {', '.join(vocab[:5])}")
        return '\n'.join(formatted)
    
    def _format_topic_research(self, topic_research: Dict) -> str:
        if not topic_research:
            return "No topic research available"
        formatted = []
        gaps = topic_research.get('topic_research', {}).get('content_gaps', {}).get('market_gaps', {})
        if gaps.get('underserved_questions'):
            formatted.append(f"Underserved Questions: {', '.join(gaps['underserved_questions'][:3])}")
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
    # ... (omitted for brevity, include your full HTML content here) ...
    return HTMLResponse(content="<html>...Your full HTML here...</html>")

@app.post("/generate-advanced")
async def generate_advanced_content(...):
    # Endpoint logic unchanged, combine all steps as in your initial code
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
