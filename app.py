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

try:
    from Reddit_scraper import RedditScraper
    from Pain_point_extractor import PainPointExtractor
    from Pain_point_humanizer import PainPointHumanizer
except ImportError as e:
    print(f"Warning: Could not import agents: {e}")
    RedditScraper = None
    PainPointExtractor = None
    PainPointHumanizer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class OpenAIClient:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
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
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return f"Error: {str(e)}"

class ContentGenerationAgent:
    def __init__(self, openai_client):
        self.openai_client = openai_client
        if PainPointHumanizer:
            self.humanizer = PainPointHumanizer(openai_client)
        else:
            self.humanizer = None
    
    async def generate_content(self, topic: str, content_type: str, target_audience: str,
                             primary_keywords: List[str], search_intent: str, brand_voice: str,
                             content_goal: str, target_geography: str, user_input: str = "",
                             analyze_serps: bool = True, pain_points: List[str] = None) -> Dict:
        pain_points_str = '\n'.join([f"• {p}" for p in (pain_points or [])])
        
        prompt = f"""Create a {content_type} about "{topic}" for {target_audience}.
Address these pain points:
{pain_points_str}

Write in {brand_voice} voice, approximately 2000 words."""
        
        content = await self.openai_client.generate_content(prompt, 4000)
        
        if self.humanizer:
            analysis = self.humanizer.analyze_content(content, pain_points or [])
            improved = content
            if analysis.get('overall_assessment', {}).get('score', 0) < 70:
                improved = await self.humanizer.generate_enhanced_version(content, analysis)
        else:
            analysis = {"overall_assessment": {"score": 75, "human_score": 70}}
            improved = content
        
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
            openai_client = OpenAIClient(model="gpt-4o-mini")
        except:
            try:
                openai_client = OpenAIClient(model="gpt-4o")
            except:
                openai_client = OpenAIClient(model="gpt-3.5-turbo")
        
        generation_agent = ContentGenerationAgent(openai_client)
        reddit_scraper = RedditScraper() if RedditScraper else None
        pain_extractor = PainPointExtractor(openai_client) if PainPointExtractor else None
        humanizer = PainPointHumanizer(openai_client) if PainPointHumanizer else None
        
        return generation_agent, reddit_scraper, pain_extractor, humanizer
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        return None, None, None, None

# COMPLETE HTML TEMPLATE WITH WAQZEE NAVIGATION
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waqzee - Pain Point Content Writing Tool</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: #f5f5f5;
        }
        
        /* Waqzee Navigation Header */
        .waqzee-header {
            background: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .header-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 80px;
        }
        
        .waqzee-logo {
            height: 50px;
            width: auto;
        }
        
        .main-nav {
            display: flex;
            align-items: center;
            gap: 40px;
            list-style: none;
        }
        
        .main-nav a {
            text-decoration: none;
            color: #2c3e50;
            font-weight: 500;
            font-size: 16px;
            transition: color 0.3s;
        }
        
        .main-nav a:hover {
            color: #667eea;
        }
        
        .main-nav a.active {
            color: #667eea;
            font-weight: 600;
        }
        
        .cta-button {
            background: linear-gradient(45deg, #2c3e50, #34495e);
            color: white !important;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(44, 62, 80, 0.3);
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(44, 62, 80, 0.4);
        }
        
        .mobile-menu-btn {
            display: none;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #2c3e50;
        }
        
        @media (max-width: 968px) {
            .main-nav {
                position: fixed;
                top: 80px;
                left: -100%;
                width: 100%;
                height: calc(100vh - 80px);
                background: white;
                flex-direction: column;
                padding: 40px;
                gap: 30px;
                transition: left 0.3s;
            }
            
            .main-nav.active {
                left: 0;
            }
            
            .mobile-menu-btn {
                display: block;
            }
        }
        
        /* Main Content */
        .main-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: calc(100vh - 80px);
            padding: 40px 20px;
        }
        
        .container { 
            max-width: 1200px;
            margin: 0 auto;
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.2); 
        }
        
        .page-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 3px solid #667eea;
        }
        
        .page-header h1 { 
            color: #667eea;
            font-size: 2.5em; 
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.2em;
            font-weight: 500;
        }
        
        .badge {
            display: inline-block;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin: 10px 5px;
        }
        
        .section {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            border-left: 5px solid #667eea;
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .form-row { 
            display: flex; 
            gap: 20px; 
            margin-bottom: 20px; 
        }
        
        .form-col { 
            flex: 1; 
        }
        
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: #555;
            font-size: 0.95em;
        }
        
        input, textarea, select { 
            width: 100%; 
            padding: 12px 16px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 14px; 
            transition: all 0.3s;
            font-family: inherit;
        }
        
        input:focus, textarea:focus, select:focus { 
            border-color: #667eea; 
            outline: none; 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); 
        }
        
        button { 
            width: 100%;
            padding: 16px 24px; 
            border: none; 
            border-radius: 12px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: 600; 
            transition: all 0.3s;
            font-family: inherit;
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5); 
        }
        
        .loading { 
            display: none; 
            text-align: center; 
            padding: 50px; 
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5); 
            border-radius: 15px; 
            margin-top: 30px;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .success { 
            background: linear-gradient(135deg, #e8f5e8, #c8e6c9); 
            color: #2e7d32; 
            padding: 25px; 
            border-radius: 12px; 
            margin: 20px 0; 
            border-left: 5px solid #4caf50;
        }
        
        .error { 
            background: linear-gradient(135deg, #ffebee, #ffcdd2); 
            color: #d32f2f; 
            padding: 25px; 
            border-radius: 12px; 
            margin: 20px 0; 
            border-left: 5px solid #f44336;
        }
        
        .content-display {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-top: 20px;
            border: 2px solid #e1e5e9;
            max-height: 600px;
            overflow-y: auto;
            line-height: 1.8;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .feature-item {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s;
        }
        
        .feature-item:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        @media (max-width: 768px) {
            .header-container { height: 70px; }
            .waqzee-logo { height: 40px; }
            .form-row { flex-direction: column; }
            .stat-grid { grid-template-columns: 1fr; }
            .page-header h1 { font-size: 1.8em; }
        }
    </style>
</head>
<body>
    <!-- Waqzee Navigation Header -->
    <header class="waqzee-header">
        <div class="header-container">
            <a href="https://waqzee.com/">
                <img src="https://waqzee.com/wp-content/uploads/2025/07/cropped-waqzee-marketing-agency.png" 
                     alt="Waqzee Digital" class="waqzee-logo">
            </a>
            
            <nav>
                <ul class="main-nav" id="mainNav">
                    <li><a href="https://waqzee.com/">Home</a></li>
                    <li><a href="https://waqzee.com/about/">About</a></li>
                    <li><a href="https://waqzee.com/service/">Service</a></li>
                    <li><a href="https://waqzee.com/contact/">Contact</a></li>
                    <li><a href="https://waqzee.com/blog/">Blog</a></li>
                    <li><a href="/tools" class="active">Tools</a></li>
                    <li><a href="https://waqzee.com/free-plan/" class="cta-button">Free Marketing Plan</a></li>
                </ul>
            </nav>
            
            <button class="mobile-menu-btn" onclick="toggleMenu()">
                <i class="fas fa-bars"></i>
            </button>
        </div>
    </header>

    <!-- Main Content -->
    <div class="main-content">
        <div class="container">
            <div class="page-header">
                <h1>Pain Point Content Writing Tool</h1>
                <p class="subtitle">Transform Reddit Insights into Compelling Content</p>
                <div>
                    <span class="badge">🤖 AI-Powered</span>
                    <span class="badge">📱 Reddit Integration</span>
                    <span class="badge">✍️ Human Quality</span>
                </div>
            </div>

            <!-- Features -->
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-icon">📥</div>
                    <h3>Reddit Scraping</h3>
                    <p>Extract real pain points from any subreddit</p>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🎯</div>
                    <h3>Pain Point Analysis</h3>
                    <p>AI identifies and categorizes problems</p>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">✍️</div>
                    <h3>Content Generation</h3>
                    <p>Creates articles addressing all pain points</p>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">💫</div>
                    <h3>Humanization</h3>
                    <p>Ensures content sounds authentic</p>
                </div>
            </div>

            <!-- Reddit Workflow -->
            <div class="section">
                <h2>🚀 Complete Workflow: Reddit → Content</h2>
                <p style="margin-bottom: 25px; color: #666;">Scrape Reddit, extract pain points, generate content - all in one click!</p>
                
                <div class="form-row">
                    <div class="form-col">
                        <label for="reddit_subreddit">📱 Subreddit (without r/):</label>
                        <input type="text" id="reddit_subreddit" placeholder="entrepreneur" value="entrepreneur">
                    </div>
                    <div class="form-col">
                        <label for="reddit_topic">🎯 Topic/Keyword:</label>
                        <input type="text" id="reddit_topic" placeholder="starting a business" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-col">
                        <label for="reddit_posts">📊 Posts to Analyze:</label>
                        <select id="reddit_posts">
                            <option value="25">25 posts (faster)</option>
                            <option value="50" selected>50 posts (recommended)</option>
                            <option value="100">100 posts (comprehensive)</option>
                        </select>
                    </div>
                    <div class="form-col">
                        <label for="reddit_content_type">📝 Content Type:</label>
                        <select id="reddit_content_type">
                            <option value="blog post" selected>Blog Post</option>
                            <option value="guide">Complete Guide</option>
                            <option value="article">Article</option>
                        </select>
                    </div>
                </div>
                
                <button type="button" onclick="runRedditWorkflow()">
                    🚀 Run Complete Workflow
                </button>
                
                <div id="workflowResults"></div>
            </div>

            <!-- Quick Generation -->
            <div class="section">
                <h2>✍️ Quick Content Generation</h2>
                <p style="margin-bottom: 25px; color: #666;">Generate content without Reddit scraping (faster)</p>
                
                <div class="form-row">
                    <div class="form-col">
                        <label for="topic">🎯 Topic:</label>
                        <input type="text" id="topic" placeholder="Email Marketing Tips">
                    </div>
                    <div class="form-col">
                        <label for="content_type">📝 Type:</label>
                        <select id="content_type">
                            <option value="blog post">Blog Post</option>
                            <option value="guide">Guide</option>
                        </select>
                    </div>
                </div>
                
                <button type="button" onclick="generateContent()">
                    ✍️ Generate Content
                </button>
            </div>

            <div id="loading" class="loading">
                <div class="spinner"></div>
                <h3>🤖 Waqzee AI Working...</h3>
                <p>This may take 60-90 seconds</p>
            </div>

            <div id="results" style="display: none;">
                <div id="resultContent"></div>
            </div>
        </div>
    </div>

    <script>
        function toggleMenu() {
            document.getElementById('mainNav').classList.toggle('active');
        }
        
        async function runRedditWorkflow() {
            const subreddit = document.getElementById('reddit_subreddit').value;
            const topic = document.getElementById('reddit_topic').value;
            const posts_limit = document.getElementById('reddit_posts').value;
            const content_type = document.getElementById('reddit_content_type').value;
            
            if (!topic) {
                alert('⚠️ Please enter a topic!');
                return;
            }
            
            document.getElementById('workflowResults').innerHTML = `
                <div class="loading" style="display: block;">
                    <div class="spinner"></div>
                    <h3>🤖 Running Waqzee Workflow...</h3>
                    <p>Scraping r/${subreddit}...</p>
                </div>
            `;
            
            try {
                const response = await fetch('/reddit-to-content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        subreddit: subreddit,
                        topic: topic,
                        posts_limit: parseInt(posts_limit),
                        content_type: content_type
                    })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    document.getElementById('workflowResults').innerHTML = `
                        <div class="error">
                            <h4>❌ Error</h4>
                            <p>${result.error}</p>
                        </div>
                    `;
                    return;
                }
                
                const workflow = result.workflow;
                
                document.getElementById('workflowResults').innerHTML = `
                    <div class="success">
                        <h3>✅ Workflow Completed!</h3>
                        <div class="stat-grid">
                            <div class="stat-card">
                                <div class="stat-value">${workflow.step1_reddit.posts_scraped}</div>
                                <div class="stat-label">Posts</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${workflow.step2_pain_points.extracted}</div>
                                <div class="stat-label">Pain Points</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${workflow.step3_content.word_count}</div>
                                <div class="stat-label">Words</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="content-display">
                        <h4 style="color: #667eea;">📄 Generated Content:</h4>
                        <div style="white-space: pre-wrap; margin-top: 20px;">
                            ${result.final_content}
                        </div>
                    </div>
                `;
                
            } catch (error) {
                document.getElementById('workflowResults').innerHTML = `
                    <div class="error">
                        <h4>❌ Request Failed</h4>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        async function generateContent() {
            const topic = document.getElementById('topic').value;
            const content_type = document.getElementById('content_type').value;
            
            if (!topic) {
                alert('⚠️ Please enter a topic!');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            try {
                const response = await fetch('/generate-content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        topic: topic,
                        content_type: content_type
                    })
                });
                
                const result = await response.json();
                document.getElementById('loading').style.display = 'none';
                
                if (result.error) {
                    document.getElementById('resultContent').innerHTML = `
                        <div class="error">
                            <h4>❌ Error</h4>
                            <p>${result.error}</p>
                        </div>
                    `;
                } else {
                    document.getElementById('resultContent').innerHTML = `
                        <div class="success">
                            <h3>✅ Content Generated!</h3>
                        </div>
                        <div class="content-display">
                            <h4 style="color: #667eea;">📄 Your Content:</h4>
                            <div style="white-space: pre-wrap; margin-top: 20px;">
                                ${result.content}
                            </div>
                        </div>
                    `;
                }
                
                document.getElementById('results').style.display = 'block';
                
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('resultContent').innerHTML = `
                    <div class="error">
                        <h4>❌ Failed</h4>
                        <p>${error.message}</p>
                    </div>
                `;
                document.getElementById('results').style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
@app.route('/tools')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/reddit-to-content', methods=['POST'])
def reddit_to_content():
    try:
        data = request.get_json()
        subreddit = data.get('subreddit', 'entrepreneur')
        topic = data.get('topic')
        posts_limit = int(data.get('posts_limit', 50))
        
        if not topic:
            return jsonify({"error": "Topic required"}), 400
        
        generation_agent, reddit_scraper, pain_extractor, _ = create_agents()
        
        if not reddit_scraper:
            # Show detailed error with file check
            import os
            agents_path = os.path.join(os.path.dirname(__file__), 'src', 'agents')
            error_msg = f"Reddit scraper not available.\n\n"
            error_msg += f"Looking for: Reddit_scraper.py in {agents_path}\n\n"
            
            if os.path.exists(agents_path):
                files = os.listdir(agents_path)
                error_msg += f"Files found in src/agents/: {', '.join(files)}\n\n"
                error_msg += "Please ensure files are named:\n"
                error_msg += "- Reddit_scraper.py (capital R, underscore)\n"
                error_msg += "- Pain_point_extractor.py (capital P, underscore)\n"
                error_msg += "- Pain_point_humanizer.py (capital P, underscore)"
            else:
                error_msg += f"Folder {agents_path} does not exist!\n"
                error_msg += "Please create src/agents/ folder and add the files."
            
            return jsonify({"error": error_msg}), 500
        
        if not all([generation_agent, reddit_scraper, pain_extractor]):
            return jsonify({"error": "Failed to initialize agents"}), 500
        
        reddit_data = reddit_scraper.scrape_for_pain_points(subreddit, topic, posts_limit)
        
        pain_analysis = asyncio.run(
            pain_extractor.extract_pain_points_from_posts(reddit_data['posts'], topic, 8)
        )
        
        pain_points = [pp['pain_point'] if isinstance(pp, dict) else pp 
                      for pp in pain_analysis.get('pain_points', [])]
        
        if not pain_points:
            pain_points = reddit_data.get('pain_points_extracted', [])[:8]
        
        content_result = asyncio.run(
            generation_agent.generate_content(
                topic=topic,
                content_type=data.get('content_type', 'blog post'),
                target_audience='professionals',
                primary_keywords=[topic],
                search_intent='informational',
                brand_voice='friendly',
                content_goal='education',
                target_geography='global',
                pain_points=pain_points
            )
        )
        
        return jsonify({
            "success": True,
            "workflow": {
                "step1_reddit": {
                    "posts_scraped": reddit_data.get('posts_scraped', len(reddit_data.get('posts', []))),
                    "comments_scraped": reddit_data.get('comments_scraped', 0)
                },
                "step2_pain_points": {
                    "extracted": len(pain_points),
                    "pain_points": pain_points
                },
                "step3_content": {
                    "word_count": len(content_result['improved_content'].split())
                },
                "step4_humanization": content_result.get('humanization_analysis', {}).get('overall_assessment', {})
            },
            "final_content": content_result['improved_content'],
            "reddit_sources": [
                {'title': p.get('title', ''), 'url': p.get('permalink', ''), 'score': p.get('score', 0)}
                for p in reddit_data.get('posts', [])[:5]
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in reddit_to_content: {e}")
        import traceback
        return jsonify({
            "error": str(e),
            "details": traceback.format_exc()
        }), 500

@app.route('/generate-content', methods=['POST'])
def generate_content_simple():
    try:
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({"error": "Topic required"}), 400
        
        generation_agent, _, _, _ = create_agents()
        if not generation_agent:
            return jsonify({"error": "Failed to initialize"}), 500
        
        result = asyncio.run(generation_agent.generate_content(
            topic=topic,
            content_type=data.get('content_type', 'blog post'),
            target_audience='professionals',
            primary_keywords=[topic],
            search_intent='informational',
            brand_voice='friendly',
            content_goal='education',
            target_geography='global'
        ))
        
        return jsonify({
            "success": True,
            "content": result.get('improved_content', result.get('generated_content', ''))
        })
        
    except Exception as e:
        logger.error(f"Error in generate_content: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "Waqzee Pain Point Content Tool",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/debug')
def debug():
    """Debug route to check file structure"""
    import os
    
    debug_info = {
        "current_dir": os.getcwd(),
        "app_file_location": __file__,
        "files_in_current_dir": os.listdir('.') if os.path.exists('.') else [],
    }
    
    # Check src/agents folder
    agents_path = os.path.join(os.path.dirname(__file__), 'src', 'agents')
    if os.path.exists(agents_path):
        debug_info["agents_folder_exists"] = True
        debug_info["agents_path"] = agents_path
        debug_info["files_in_agents"] = os.listdir(agents_path)
    else:
        debug_info["agents_folder_exists"] = False
        debug_info["agents_path"] = agents_path
    
    # Check if modules loaded
    debug_info["modules_loaded"] = {
        "RedditScraper": RedditScraper is not None,
        "PainPointExtractor": PainPointExtractor is not None,
        "PainPointHumanizer": PainPointHumanizer is not None
    }
    
    return jsonify(debug_info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting Waqzee Content Tool on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
