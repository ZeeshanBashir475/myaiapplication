import re
import json
import logging
import os
import openai
from typing import Dict, List
from datetime import datetime
import asyncio
from flask import Flask, request, jsonify, render_template_string
import statistics

# Import from src/agents folder
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'agents'))

# Note: These will be imported from your src/agents/ folder
# Make sure the file names match exactly:
# - Reddit_scraper.py
# - Pain_point_extractor.py  
# - Pain_point_humanizer.py

try:
    from Reddit_scraper import RedditScraper
    from Pain_point_extractor import PainPointExtractor
    from Pain_point_humanizer import PainPointHumanizer
except ImportError as e:
    print(f"Warning: Could not import agents from src/agents/: {e}")
    print("Make sure files exist in src/agents/ folder")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class OpenAIClient:
    def __init__(self, api_key: str = None, model: str = "gpt-4.1-mini"):
        if api_key is None:
            api_key = os.getenv('Open_Api_Key')
            if not api_key:
                raise ValueError("No API key found")
        
        self.api_key = api_key.strip()
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        self.async_client = openai.AsyncOpenAI(api_key=self.api_key)
    
    async def generate_content(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=120.0
            )
            return response.choices[0].message.content
        except:
            return "Error generating content"

class ContentGenerationAgent:
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.humanizer = PainPointHumanizer(openai_client)
    
    async def generate_content(self, topic: str, content_type: str, target_audience: str,
                             primary_keywords: List[str], search_intent: str, brand_voice: str,
                             content_goal: str, target_geography: str, user_input: str = "",
                             analyze_serps: bool = True, pain_points: List[str] = None) -> Dict:
        pain_points_str = '\\n'.join([f"• {p}" for p in (pain_points or [])])
        
        prompt = f"""Create a {content_type} about "{topic}" for {target_audience}.
Address these pain points:
{pain_points_str}

Write in {brand_voice} voice, approximately 2000 words."""
        
        content = await self.openai_client.generate_content(prompt, 4000)
        analysis = self.humanizer.analyze_content(content, pain_points or [])
        
        improved = content
        if analysis['overall_assessment']['score'] < 70:
            improved = await self.humanizer.generate_enhanced_version(content, analysis)
        
        return {
            "generated_content": content,
            "improved_content": improved,
            "humanization_analysis": analysis,
            "model_used": self.openai_client.model
        }

def create_agents():
    try:
        api_key = os.getenv('Open_Api_Key')
        if not api_key:
            return None, None, None, None
        
        try:
            openai_client = OpenAIClient(model="gpt-4.1-mini")
        except:
            openai_client = OpenAIClient(model="gpt-4o")
        
        generation_agent = ContentGenerationAgent(openai_client)
        reddit_scraper = RedditScraper()
        pain_extractor = PainPointExtractor(openai_client)
        humanizer = PainPointHumanizer(openai_client)
        
        return generation_agent, reddit_scraper, pain_extractor, humanizer
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        return None, None, None, None

HTML_TEMPLATE = """[HTML content continues in next file - too long for one command]"""

@app.route('/')
@app.route('/tools')
def index():
    return "Waqzee Content Tool - Use API endpoints"

@app.route('/reddit-to-content', methods=['POST'])
def reddit_to_content():
    try:
        data = request.get_json()
        subreddit = data.get('subreddit', 'entrepreneur')
        topic = data.get('topic')
        
        if not topic:
            return jsonify({"error": "Topic required"}), 400
        
        generation_agent, reddit_scraper, pain_extractor, _ = create_agents()
        if not all([generation_agent, reddit_scraper, pain_extractor]):
            return jsonify({"error": "Failed to initialize"}), 500
        
        reddit_data = reddit_scraper.scrape_for_pain_points(subreddit, topic, 50)
        pain_analysis = asyncio.run(
            pain_extractor.extract_pain_points_from_posts(reddit_data['posts'], topic, 8)
        )
        
        pain_points = [pp['pain_point'] if isinstance(pp, dict) else pp 
                      for pp in pain_analysis.get('pain_points', [])]
        
        content_result = asyncio.run(
            generation_agent.generate_content(
                topic=topic, content_type='blog post', target_audience='professionals',
                primary_keywords=[topic], search_intent='informational',
                brand_voice='friendly', content_goal='education',
                target_geography='global', pain_points=pain_points
            )
        )
        
        return jsonify({
            "success": True,
            "workflow": {
                "step1_reddit": {"posts_scraped": reddit_data['posts_scraped']},
                "step2_pain_points": {"extracted": len(pain_points), "pain_points": pain_points},
                "step3_content": {"word_count": len(content_result['improved_content'].split())},
                "step4_humanization": content_result['humanization_analysis']['overall_assessment']
            },
            "final_content": content_result['improved_content'],
            "reddit_sources": [
                {'title': p['title'], 'url': p['permalink'], 'score': p['score']}
                for p in reddit_data['posts'][:5]
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "Waqzee Content Tool"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
