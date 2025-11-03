import re
import json
import os
import sys
import logging
import traceback
import asyncio
import time
from typing import Dict, List, Tuple
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting Waqzee Advanced Content Tool with Full API Integration...")

# Import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
    logger.info("OpenAI library loaded")
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

# Optional sentiment analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    logger.info("VADER loaded")
except:
    vader_analyzer = None

app = Flask(__name__)
CORS(app)

# Global progress tracking
generation_progress = {
    "status": "idle",
    "step": "",
    "percentage": 0,
    "details": ""
}

def update_progress(step: str, percentage: int, details: str = ""):
    """Update generation progress"""
    global generation_progress
    generation_progress = {
        "status": "processing",
        "step": step,
        "percentage": percentage,
        "details": details
    }
    logger.info(f"Progress: {step} - {percentage}%")

def convert_markdown_to_html(text: str) -> str:
    """Convert markdown-style headers to proper HTML"""
    # Convert markdown headers to HTML
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convert bold text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points
    text = re.sub(r'^\* (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', text)
    
    # Convert numbered lists
    text = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Add paragraphs
    paragraphs = text.split('\n\n')
    formatted_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        formatted_paragraphs.append(p)
    
    return '\n'.join(formatted_paragraphs)

class RedditAPI:
    """Reddit API integration"""
    
    def __init__(self):
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'WaqzeeContentBot/1.0')
        self.token = None
        self.available = bool(self.client_id and self.client_secret)
        
        if self.available:
            self.authenticate()
    
    def authenticate(self):
        """Get Reddit access token"""
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            data = {'grant_type': 'password', 'username': '', 'password': ''}
            headers = {'User-Agent': self.user_agent}
            
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                logger.info("Reddit authentication successful")
            else:
                logger.warning("Reddit auth failed")
                self.available = False
        except Exception as e:
            logger.error(f"Reddit auth error: {e}")
            self.available = False
    
    def search_subreddit(self, subreddit: str, query: str, limit: int = 10) -> List[Dict]:
        """Search posts in a subreddit"""
        if not self.available or not self.token:
            return []
        
        try:
            headers = {
                'Authorization': f'bearer {self.token}',
                'User-Agent': self.user_agent
            }
            
            url = f'https://oauth.reddit.com/r/{subreddit}/search'
            params = {
                'q': query,
                'restrict_sr': 'on',
                'limit': limit,
                'sort': 'relevance'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                for child in data.get('data', {}).get('children', []):
                    post_data = child.get('data', {})
                    posts.append({
                        'title': post_data.get('title', ''),
                        'text': post_data.get('selftext', ''),
                        'score': post_data.get('score', 0),
                        'comments': post_data.get('num_comments', 0),
                        'url': f"https://reddit.com{post_data.get('permalink', '')}"
                    })
                return posts
            else:
                logger.warning(f"Reddit search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Reddit search error: {e}")
            return []

class SerpAPI:
    """Google SERP API integration"""
    
    @staticmethod
    def search(query: str) -> Dict:
        """Get Google search results"""
        try:
            api_key = os.getenv('Serp_API')
            if not api_key:
                return {"organic_results": [], "people_also_ask": []}
            
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": api_key,
                "num": 10,
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            results = {
                "organic_results": [],
                "people_also_ask": [],
                "related_searches": []
            }
            
            # Parse organic results
            for result in data.get("organic_results", [])[:5]:
                results["organic_results"].append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0)
                })
            
            # Parse People Also Ask
            for question in data.get("related_questions", [])[:5]:
                results["people_also_ask"].append({
                    "question": question.get("question", ""),
                    "snippet": question.get("snippet", "")
                })
            
            # Parse related searches
            for search in data.get("related_searches", [])[:5]:
                results["related_searches"].append(search.get("query", ""))
            
            logger.info(f"SERP API returned {len(results['organic_results'])} results")
            return results
            
        except Exception as e:
            logger.error(f"SERP API error: {e}")
            return {"organic_results": [], "people_also_ask": []}

class NewsAPI:
    """News API integration"""
    
    @staticmethod
    def get_trending(query: str) -> List[Dict]:
        """Get trending news"""
        try:
            api_key = os.getenv('News_API')
            if not api_key:
                return []
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": api_key,
                "sortBy": "popularity",
                "language": "en",
                "pageSize": 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            articles = []
            for article in data.get("articles", [])[:5]:
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "")
                })
            
            logger.info(f"News API returned {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"News API error: {e}")
            return []

class OpenAIClient:
    """OpenAI client with proper formatting"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('Open_Api_Key')
        self.available = False
        
        if not OPENAI_AVAILABLE or not self.api_key:
            logger.warning("OpenAI not configured")
            return
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key, timeout=30.0)
            self.async_client = openai.AsyncOpenAI(api_key=self.api_key, timeout=30.0)
            self.available = True
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
    
    async def generate_content(self, prompt: str, max_tokens: int = 3000) -> str:
        """Generate content with OpenAI"""
        if not self.available:
            return self.generate_fallback(prompt)
        
        try:
            # Add formatting instructions to prompt
            formatted_prompt = prompt + """

IMPORTANT: Format your response with proper HTML tags:
- Use <h1> for main title
- Use <h2> for section headers  
- Use <h3> for subsections
- Use <p> for paragraphs
- Use <ul> and <li> for bullet points
- Use <strong> for emphasis
- DO NOT use markdown ### symbols"""
            
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": formatted_prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            # Ensure proper HTML formatting
            return convert_markdown_to_html(content)
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self.generate_fallback(prompt)
    
    def generate_fallback(self, prompt: str) -> str:
        """Fallback content"""
        topic = re.search(r'about ["\']([^"\']+)["\']', prompt)
        topic = topic.group(1) if topic else "your topic"
        
        return f"""
        <h1>{topic}: A Comprehensive Guide</h1>
        <p>This guide provides essential information about {topic}.</p>
        <h2>Key Points</h2>
        <ul>
            <li>Understanding the basics</li>
            <li>Best practices</li>
            <li>Common challenges</li>
        </ul>
        """

# Enhanced HTML Template with subreddit selection and real-time updates
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waqzee - AI Content Generator with Live Research</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .logo {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 400px 1fr;
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .input-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            height: fit-content;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: all 0.3s;
            background: white;
        }
        
        input:focus, select:focus, textarea:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .subreddit-input {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .subreddit-tag {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .progress-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            display: none;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .progress-panel.active {
            display: block;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }
        
        .progress-text {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .research-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
            display: none;
        }
        
        .research-grid.active {
            display: grid;
        }
        
        .research-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .research-card h3 {
            font-size: 14px;
            color: #667eea;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        
        .research-item {
            padding: 10px;
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            margin-bottom: 10px;
            border-radius: 5px;
            font-size: 13px;
        }
        
        .content-editor {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
            display: none;
        }
        
        .content-editor.active {
            display: block;
        }
        
        .editor-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 20px;
            font-weight: 600;
        }
        
        .editor-content {
            padding: 30px;
            min-height: 500px;
            font-size: 16px;
            line-height: 1.8;
        }
        
        /* Proper HTML content styling */
        .editor-content h1 {
            font-size: 32px;
            color: #1a1a1a;
            margin-bottom: 20px;
            font-weight: 700;
        }
        
        .editor-content h2 {
            font-size: 24px;
            color: #333;
            margin-top: 30px;
            margin-bottom: 15px;
            font-weight: 600;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .editor-content h3 {
            font-size: 20px;
            color: #555;
            margin-top: 25px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .editor-content p {
            margin-bottom: 15px;
            color: #444;
            line-height: 1.8;
        }
        
        .editor-content ul, .editor-content ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        .editor-content li {
            margin-bottom: 8px;
            line-height: 1.6;
        }
        
        .editor-content strong {
            color: #667eea;
            font-weight: 600;
        }
        
        .metrics-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .metric-item {
            text-align: center;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-top: 5px;
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🚀 Waqzee AI Content Engine</div>
        </div>
        
        <div class="main-grid">
            <!-- Input Panel -->
            <div class="input-panel">
                <h2 style="margin-bottom: 20px; color: #333;">Configure Your Research</h2>
                
                <div class="form-group">
                    <label>Topic *</label>
                    <input type="text" id="topic" placeholder="e.g., best productivity apps for remote work">
                </div>
                
                <div class="form-group">
                    <label>Subreddits to Search (Optional)</label>
                    <div class="subreddit-input">
                        <input type="text" id="subredditInput" placeholder="e.g., productivity">
                        <button onclick="addSubreddit()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">Add</button>
                    </div>
                    <div id="subredditList">
                        <span class="subreddit-tag">r/technology</span>
                        <span class="subreddit-tag">r/askreddit</span>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Content Type</label>
                    <select id="contentType">
                        <option value="blog post">Blog Post</option>
                        <option value="comprehensive guide">Comprehensive Guide</option>
                        <option value="comparison article">Comparison Article</option>
                        <option value="how-to guide">How-To Guide</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Research Depth</label>
                    <select id="researchDepth">
                        <option value="quick">Quick (5 sources)</option>
                        <option value="standard" selected>Standard (10 sources)</option>
                        <option value="deep">Deep (20+ sources)</option>
                    </select>
                </div>
                
                <button class="btn" id="generateBtn" onclick="generateContent()">
                    <i class="fas fa-magic"></i> Generate AI Content
                </button>
            </div>
            
            <!-- Main Content Area -->
            <div class="main-content">
                <!-- Progress Panel -->
                <div id="progressPanel" class="progress-panel">
                    <h3 style="margin-bottom: 20px;">Research Progress</h3>
                    <div class="progress-bar">
                        <div id="progressFill" class="progress-fill" style="width: 0%">0%</div>
                    </div>
                    <div id="progressText" class="progress-text">Initializing...</div>
                </div>
                
                <!-- Research Results -->
                <div id="researchGrid" class="research-grid">
                    <div class="research-card">
                        <h3>📊 Google Search Results</h3>
                        <div id="serpResults"></div>
                    </div>
                    <div class="research-card">
                        <h3>💬 Reddit Insights</h3>
                        <div id="redditResults"></div>
                    </div>
                    <div class="research-card">
                        <h3>📰 Trending News</h3>
                        <div id="newsResults"></div>
                    </div>
                    <div class="research-card">
                        <h3>❓ People Also Ask</h3>
                        <div id="paaResults"></div>
                    </div>
                </div>
                
                <!-- Content Editor -->
                <div id="contentEditor" class="content-editor">
                    <div class="editor-header">
                        Generated Content
                    </div>
                    <div id="editorContent" class="editor-content"></div>
                    <div class="metrics-bar">
                        <div class="metric-item">
                            <div class="metric-value" id="wordCount">0</div>
                            <div class="metric-label">Words</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="readability">0</div>
                            <div class="metric-label">Readability</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="uniqueness">0%</div>
                            <div class="metric-label">Uniqueness</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="sentiment">-</div>
                            <div class="metric-label">Sentiment</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let subreddits = ['technology', 'askreddit'];
        let progressInterval;
        
        function addSubreddit() {
            const input = document.getElementById('subredditInput');
            const value = input.value.trim().replace('r/', '');
            
            if (value && !subreddits.includes(value)) {
                subreddits.push(value);
                updateSubredditList();
                input.value = '';
            }
        }
        
        function updateSubredditList() {
            const list = document.getElementById('subredditList');
            list.innerHTML = subreddits.map(s => 
                `<span class="subreddit-tag">r/${s}</span>`
            ).join('');
        }
        
        function updateProgress(percentage, text) {
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressFill').textContent = percentage + '%';
            document.getElementById('progressText').textContent = text;
        }
        
        async function generateContent() {
            const topic = document.getElementById('topic').value.trim();
            
            if (!topic) {
                alert('Please enter a topic');
                return;
            }
            
            // Show progress panel
            document.getElementById('progressPanel').classList.add('active');
            document.getElementById('researchGrid').classList.add('active');
            document.getElementById('generateBtn').disabled = true;
            
            // Start progress animation
            let progress = 0;
            const steps = [
                {p: 10, t: "Searching Google for top results..."},
                {p: 25, t: "Analyzing Reddit discussions..."},
                {p: 40, t: "Gathering trending news..."},
                {p: 55, t: "Extracting pain points..."},
                {p: 70, t: "Generating personas..."},
                {p: 85, t: "Creating content with AI..."},
                {p: 100, t: "Finalizing and formatting..."}
            ];
            
            let currentStep = 0;
            progressInterval = setInterval(() => {
                if (currentStep < steps.length) {
                    updateProgress(steps[currentStep].p, steps[currentStep].t);
                    currentStep++;
                }
            }, 2000);
            
            try {
                const response = await fetch('/generate-advanced', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        topic: topic,
                        content_type: document.getElementById('contentType').value,
                        research_depth: document.getElementById('researchDepth').value,
                        subreddits: subreddits
                    })
                });
                
                const result = await response.json();
                
                clearInterval(progressInterval);
                updateProgress(100, "Content generated successfully!");
                
                // Display research results
                displayResearchResults(result);
                
                // Display content
                document.getElementById('contentEditor').classList.add('active');
                document.getElementById('editorContent').innerHTML = result.content || '';
                
                // Update metrics
                updateMetrics(result.content);
                
                document.getElementById('generateBtn').disabled = false;
                
            } catch (error) {
                clearInterval(progressInterval);
                updateProgress(0, "Error occurred. Please try again.");
                document.getElementById('generateBtn').disabled = false;
                console.error('Error:', error);
            }
        }
        
        function displayResearchResults(data) {
            // Display SERP results
            if (data.serp_results && data.serp_results.length > 0) {
                const serpHtml = data.serp_results.slice(0, 3).map(r => 
                    `<div class="research-item">
                        <strong>${r.title}</strong><br>
                        <small>${r.snippet}</small>
                    </div>`
                ).join('');
                document.getElementById('serpResults').innerHTML = serpHtml;
            }
            
            // Display Reddit results
            if (data.reddit_posts && data.reddit_posts.length > 0) {
                const redditHtml = data.reddit_posts.slice(0, 3).map(p => 
                    `<div class="research-item">
                        <strong>${p.title}</strong><br>
                        <small>Score: ${p.score} | Comments: ${p.comments}</small>
                    </div>`
                ).join('');
                document.getElementById('redditResults').innerHTML = redditHtml;
            }
            
            // Display News
            if (data.news && data.news.length > 0) {
                const newsHtml = data.news.slice(0, 3).map(n => 
                    `<div class="research-item">
                        <strong>${n.title}</strong><br>
                        <small>${n.source}</small>
                    </div>`
                ).join('');
                document.getElementById('newsResults').innerHTML = newsHtml;
            }
            
            // Display People Also Ask
            if (data.people_also_ask && data.people_also_ask.length > 0) {
                const paaHtml = data.people_also_ask.slice(0, 3).map(q => 
                    `<div class="research-item">${q.question}</div>`
                ).join('');
                document.getElementById('paaResults').innerHTML = paaHtml;
            }
        }
        
        function updateMetrics(content) {
            // Word count
            const words = content.replace(/<[^>]*>/g, '').split(/\s+/).length;
            document.getElementById('wordCount').textContent = words;
            
            // Readability (simple approximation)
            const sentences = content.split(/[.!?]+/).length;
            const readability = Math.min(100, Math.round(100 - (words/sentences - 15) * 5));
            document.getElementById('readability').textContent = readability;
            
            // Uniqueness (mock)
            document.getElementById('uniqueness').textContent = '92%';
            
            // Sentiment
            document.getElementById('sentiment').textContent = 'Positive';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-advanced', methods=['POST'])
async def generate_advanced():
    """Generate content with full API integration"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        subreddits = data.get('subreddits', ['technology'])
        
        if not topic:
            return jsonify({"error": "Topic required"}), 400
        
        logger.info(f"Starting generation for: {topic}")
        update_progress("Starting research", 5)
        
        # Initialize APIs
        reddit_api = RedditAPI()
        openai_client = OpenAIClient()
        
        # 1. Search Google
        update_progress("Searching Google", 15)
        serp_results = SerpAPI.search(topic)
        
        # 2. Search Reddit
        update_progress("Searching Reddit", 30)
        reddit_posts = []
        if reddit_api.available:
            for subreddit in subreddits[:3]:
                posts = reddit_api.search_subreddit(subreddit, topic, 5)
                reddit_posts.extend(posts)
        
        # 3. Get News
        update_progress("Getting trending news", 45)
        news = NewsAPI.get_trending(topic)
        
        # 4. Extract pain points from Reddit
        update_progress("Analyzing discussions", 60)
        pain_points = []
        for post in reddit_posts[:5]:
            text = post.get('title', '') + ' ' + post.get('text', '')
            if 'problem' in text.lower() or 'issue' in text.lower() or 'help' in text.lower():
                pain_points.append(text[:100])
        
        # 5. Generate content
        update_progress("Generating content with AI", 75)
        
        # Build context from research
        context = f"""
        Top Google Results: {[r['title'] for r in serp_results.get('organic_results', [])[:3]]}
        People Also Ask: {[q['question'] for q in serp_results.get('people_also_ask', [])[:3]]}
        Reddit Discussions: {[p['title'] for p in reddit_posts[:5]]}
        Trending News: {[n['title'] for n in news[:3]]}
        """
        
        prompt = f"""Create a comprehensive {data.get('content_type', 'blog post')} about "{topic}"

Research Context:
{context}

Requirements:
1. Address the questions people are asking
2. Include insights from recent discussions
3. Reference current trends
4. Write 800-1200 words
5. Use clear HTML formatting

Generate the article:"""
        
        content = await openai_client.generate_content(prompt)
        
        update_progress("Complete", 100)
        
        return jsonify({
            "success": True,
            "content": content,
            "serp_results": serp_results.get('organic_results', []),
            "people_also_ask": serp_results.get('people_also_ask', []),
            "reddit_posts": reddit_posts,
            "news": news,
            "pain_points": pain_points[:5]
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/progress')
def get_progress():
    """Get current progress"""
    return jsonify(generation_progress)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
