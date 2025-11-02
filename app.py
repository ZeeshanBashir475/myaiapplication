import re
import json
import os
import openai
from typing import Dict, List
from datetime import datetime
import asyncio
from flask import Flask, request, jsonify, render_template_string
import statistics

# Setup logging FIRST
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting Waqzee Content Tool...")

# Add src/agents to path
import sys
agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'agents')
if os.path.exists(agents_path):
    if agents_path not in sys.path:
        sys.path.insert(0, agents_path)
        logger.info(f"Added to Python path: {agents_path}")
    logger.info(f"Files in agents folder: {os.listdir(agents_path)}")
else:
    logger.error(f"Agents folder not found: {agents_path}")

# Try to import agents safely - each import is independent
RedditScraper = None
PainPointExtractor = None  
PainPointHumanizer = None

try:
    from Reddit_scraper import RedditScraper
    logger.info("RedditScraper imported successfully")
except Exception as e:
    logger.error(f"Failed to import RedditScraper: {e}")

try:
    from Pain_point_extractor import PainPointExtractor
    logger.info("PainPointExtractor imported successfully")
except Exception as e:
    logger.error(f"Failed to import PainPointExtractor: {e}")

try:
    from Pain_point_humanizer import PainPointHumanizer
    logger.info("PainPointHumanizer imported successfully")
except Exception as e:
    logger.error(f"Failed to import PainPointHumanizer: {e}")

# Check import status
if all([RedditScraper, PainPointExtractor, PainPointHumanizer]):
    logger.info("All agents imported successfully!")
else:
    logger.warning(f"Some agents failed to import: Reddit={RedditScraper is not None}, Extractor={PainPointExtractor is not None}, Humanizer={PainPointHumanizer is not None}")

app = Flask(__name__)

class OpenAIClient:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        if api_key is None:
            api_key = os.getenv('Open_Api_Key')
            if not api_key:
                raise ValueError("No OpenAI API key found")
        
        self.api_key = api_key.strip()
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key, timeout=60.0)
        self.async_client = openai.AsyncOpenAI(api_key=self.api_key, timeout=60.0)
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
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
            logger.error(f"OpenAI generation error: {e}")
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
            try:
                analysis = self.humanizer.analyze_content(content, pain_points or [])
                improved = content
                if analysis.get('overall_assessment', {}).get('score', 0) < 70:
                    improved = await self.humanizer.generate_enhanced_version(content, analysis)
            except Exception as e:
                logger.error(f"Humanization error: {e}")
                analysis = {"overall_assessment": {"score": 75, "human_score": 70}}
                improved = content
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
            logger.error("No OpenAI API key found")
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
        
        # Skip humanizer for now - it has errors
        humanizer = None
        logger.info("Humanizer skipped (has import errors)")
        
        return generation_agent, reddit_scraper, pain_extractor, humanizer
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None, None, None

# PROFESSIONAL BLACK & WHITE HTML TEMPLATE
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waqzee - Content Generation Tool</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
            background: #f9f9f9;
            color: #1a1a1a;
        }
        
        /* Header */
        .header {
            background: white;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .header-content {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
            color: #000;
        }
        
        .nav a {
            text-decoration: none;
            color: #666;
            margin: 0 20px;
            font-size: 14px;
            font-weight: 500;
            transition: color 0.2s;
        }
        
        .nav a:hover, .nav a.active {
            color: #000;
        }
        
        /* Main Container */
        .main {
            max-width: 1600px;
            margin: 0 auto;
            padding: 40px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
            color: #000;
        }
        
        .page-subtitle {
            font-size: 16px;
            color: #666;
            margin-bottom: 40px;
        }
        
        /* Content Grid */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-bottom: 40px;
        }
        
        @media (max-width: 1200px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Form Sections */
        .form-section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #000;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group:last-child {
            margin-bottom: 0;
        }
        
        label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
            color: #1a1a1a;
        }
        
        input[type="text"],
        input[type="email"],
        select,
        textarea {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
            background: white;
            color: #000;
        }
        
        input[type="text"]:focus,
        input[type="email"]:focus,
        select:focus,
        textarea:focus {
            border-color: #000;
            outline: none;
            box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
        }
        
        textarea {
            resize: vertical;
            min-height: 80px;
        }
        
        /* Buttons */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
            width: 100%;
        }
        
        .btn-primary {
            background: #000;
            color: white;
        }
        
        .btn-primary:hover {
            background: #333;
        }
        
        .btn-primary:active {
            transform: scale(0.98);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #000;
            border: 1px solid #e0e0e0;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        /* Status Messages */
        .status-message {
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .status-success {
            background: #f0f9f7;
            color: #1a5f52;
            border: 1px solid #d0e8e3;
        }
        
        .status-error {
            background: #fef0f0;
            color: #8b3333;
            border: 1px solid #f0d0d0;
        }
        
        .status-loading {
            background: #f5f5f5;
            color: #666;
            border: 1px solid #e0e0e0;
        }
        
        /* Pain Points Display */
        .pain-points-section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            margin-bottom: 40px;
        }
        
        .pain-point-item {
            padding: 16px;
            background: #fafafa;
            border-left: 3px solid #000;
            margin-bottom: 12px;
            border-radius: 4px;
        }
        
        .pain-point-item:last-child {
            margin-bottom: 0;
        }
        
        .pain-point-text {
            font-size: 14px;
            color: #1a1a1a;
            font-weight: 500;
            margin-bottom: 6px;
        }
        
        .pain-point-meta {
            font-size: 12px;
            color: #999;
        }
        
        /* Editor */
        .editor-section {
            background: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 0;
            overflow: hidden;
        }
        
        .editor-header {
            padding: 20px 30px;
            border-bottom: 1px solid #e0e0e0;
            background: #fafafa;
        }
        
        .editor-header h3 {
            font-size: 16px;
            font-weight: 600;
            color: #000;
        }
        
        .editor-toolbar {
            padding: 15px 30px;
            background: #fafafa;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .ql-toolbar.ql-snow {
            background: transparent;
            border: none;
            padding: 0;
        }
        
        .ql-toolbar button:hover,
        .ql-toolbar button.ql-active,
        .ql-toolbar button:focus,
        .ql-toolbar button:active {
            color: #000;
        }
        
        .ql-toolbar.ql-snow .ql-picker-label {
            color: #666;
        }
        
        .editor-content {
            padding: 30px;
            min-height: 600px;
        }
        
        .ql-container.ql-snow {
            border: none;
            font-size: 14px;
            font-family: inherit;
        }
        
        .ql-editor {
            padding: 0;
            min-height: 400px;
        }
        
        .ql-editor.ql-blank::before {
            color: #ccc;
            font-size: 14px;
        }
        
        /* Metrics */
        .metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: #000;
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Loading Spinner */
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #e0e0e0;
            border-top: 3px solid #000;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics {
                grid-template-columns: 1fr;
            }
            
            .main {
                padding: 20px;
            }
            
            .page-title {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <div class="logo">Waqzee</div>
            <nav class="nav">
                <a href="https://waqzee.com/">Home</a>
                <a href="https://waqzee.com/about/">About</a>
                <a href="https://waqzee.com/service/">Services</a>
                <a href="/tools" class="active">Tools</a>
            </nav>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main">
        <h1 class="page-title">Content Generation Tool</h1>
        <p class="page-subtitle">Create compelling content informed by real user research</p>

        <!-- Content Grid -->
        <div class="content-grid">
            <!-- Left Column: Form -->
            <div>
                <!-- Reddit Research Section -->
                <div class="form-section">
                    <h4 class="section-title">Research from Reddit</h4>
                    
                    <div class="form-group">
                        <label>Subreddit</label>
                        <input type="text" id="reddit_subreddit" placeholder="entrepreneur" value="entrepreneur">
                    </div>
                    
                    <div class="form-group">
                        <label>Topic to Search</label>
                        <input type="text" id="reddit_topic" placeholder="starting a business" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Number of Posts</label>
                        <select id="reddit_posts">
                            <option value="25">25 posts</option>
                            <option value="50" selected>50 posts</option>
                            <option value="100">100 posts</option>
                        </select>
                    </div>
                    
                    <button class="btn btn-primary" onclick="runRedditResearch()">Research on Reddit</button>
                </div>

                <!-- Article Details Section -->
                <div class="form-section" style="margin-top: 20px;">
                    <h4 class="section-title">Article Details</h4>
                    
                    <div class="form-group">
                        <label>Article Title</label>
                        <input type="text" id="article_title" placeholder="e.g., How to Start Your First Business in 30 Days">
                    </div>
                    
                    <div class="form-group">
                        <label>What Do You Already Know?</label>
                        <textarea id="existing_knowledge" placeholder="Share your existing knowledge, expertise, or data on this topic..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>What Makes This Unique?</label>
                        <textarea id="unique_angle" placeholder="What's your unique perspective or approach? What will make this stand out?"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Content Type</label>
                        <select id="content_type">
                            <option value="blog post">Blog Post</option>
                            <option value="guide">Complete Guide</option>
                            <option value="tutorial">Tutorial</option>
                            <option value="case study">Case Study</option>
                        </select>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateContent()">Generate Content</button>
                </div>
            </div>

            <!-- Right Column: Pain Points & Editor -->
            <div>
                <!-- Pain Points Display -->
                <div id="painPointsSection" class="pain-points-section" style="display: none;">
                    <h4 class="section-title">Pain Points Identified</h4>
                    <div id="painPointsList"></div>
                </div>

                <!-- Metrics -->
                <div id="metricsSection" class="metrics" style="display: none;">
                    <div class="metric">
                        <div class="metric-value" id="postsCount">0</div>
                        <div class="metric-label">Posts Analyzed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="painPointsCount">0</div>
                        <div class="metric-label">Pain Points</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="wordCount">0</div>
                        <div class="metric-label">Word Count</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Editor Section -->
        <div id="editorSection" style="display: none;">
            <div class="editor-section">
                <div class="editor-header">
                    <h3>Edit Your Content</h3>
                </div>
                <div class="editor-toolbar" id="editor-toolbar"></div>
                <div class="editor-content">
                    <div id="editor"></div>
                </div>
                <div style="padding: 20px 30px; border-top: 1px solid #e0e0e0; background: #fafafa;">
                    <button class="btn btn-primary" onclick="saveContent()">Save & Export</button>
                </div>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="statusMessage" style="display: none;"></div>
    </div>

    <!-- Quill Editor -->
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
        let editor = null;
        let currentContent = "";

        // Initialize Quill editor (lazy load)
        function initEditor() {
            if (!editor) {
                editor = new Quill('#editor', {
                    theme: 'snow',
                    modules: {
                        toolbar: [
                            ['bold', 'italic', 'underline'],
                            ['blockquote', 'code-block'],
                            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                            [{ 'header': [1, 2, 3, false] }],
                            ['link'],
                            ['clean']
                        ]
                    },
                    placeholder: 'Start editing...'
                });
            }
        }

        function showStatus(message, type) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.className = 'status-message status-' + type;
            statusEl.textContent = message;
            statusEl.style.display = 'block';
            if (type !== 'loading') {
                setTimeout(() => { statusEl.style.display = 'none'; }, 5000);
            }
        }

        async function runRedditResearch() {
            const subreddit = document.getElementById('reddit_subreddit').value;
            const topic = document.getElementById('reddit_topic').value;
            const posts_limit = document.getElementById('reddit_posts').value;

            if (!topic) {
                showStatus('Please enter a topic', 'error');
                return;
            }

            showStatus('Researching Reddit...', 'loading');

            try {
                const response = await fetch('/reddit-to-content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ subreddit, topic, posts_limit: parseInt(posts_limit), content_type: 'blog post' })
                });

                const result = await response.json();

                if (result.error) {
                    showStatus('Error: ' + result.error, 'error');
                    return;
                }

                // Display pain points
                const workflow = result.workflow;
                displayPainPoints(workflow.step2_pain_points.pain_points);
                displayMetrics(workflow);

                // Set title suggestion
                document.getElementById('article_title').value = `Guide to: ${topic}`;

                showStatus('Reddit research complete. Now review pain points and customize your article.', 'success');

            } catch (error) {
                showStatus('Failed: ' + error.message, 'error');
            }
        }

        function displayPainPoints(painPoints) {
            const section = document.getElementById('painPointsSection');
            const list = document.getElementById('painPointsList');
            list.innerHTML = '';

            painPoints.forEach((point, index) => {
                const item = document.createElement('div');
                item.className = 'pain-point-item';
                item.innerHTML = `
                    <div class="pain-point-text">${point}</div>
                    <div class="pain-point-meta">Pain Point ${index + 1} of ${painPoints.length}</div>
                `;
                list.appendChild(item);
            });

            section.style.display = 'block';
        }

        function displayMetrics(workflow) {
            document.getElementById('postsCount').textContent = workflow.step1_reddit.posts_scraped;
            document.getElementById('painPointsCount').textContent = workflow.step2_pain_points.extracted;
            document.getElementById('wordCount').textContent = workflow.step3_content.word_count;
            document.getElementById('metricsSection').style.display = 'grid';
        }

        async function generateContent() {
            const title = document.getElementById('article_title').value;
            const contentType = document.getElementById('content_type').value;
            const existingKnowledge = document.getElementById('existing_knowledge').value;
            const uniqueAngle = document.getElementById('unique_angle').value;

            if (!title) {
                showStatus('Please enter an article title', 'error');
                return;
            }

            showStatus('Generating content...', 'loading');

            try {
                const response = await fetch('/generate-content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ topic: title, content_type: contentType })
                });

                const result = await response.json();

                if (result.error) {
                    showStatus('Error: ' + result.error, 'error');
                    return;
                }

                // Load content into editor
                initEditor();
                currentContent = result.content;
                editor.root.innerHTML = result.content;
                document.getElementById('editorSection').style.display = 'block';

                showStatus('Content generated! Now you can edit it in the editor below.', 'success');

            } catch (error) {
                showStatus('Failed: ' + error.message, 'error');
            }
        }

        function saveContent() {
            const content = editor.root.innerHTML;
            const title = document.getElementById('article_title').value || 'article';
            const blob = new Blob([`<html><body>${content}</body></html>`], { type: 'text/html' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = title.replace(/\s+/g, '-').toLowerCase() + '.html';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showStatus('Content saved and downloaded!', 'success');
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
            return jsonify({"error": "Reddit scraper not available. The agent files may not be properly imported. Check Railway logs for details."}), 500
        
        if not all([generation_agent, reddit_scraper, pain_extractor]):
            return jsonify({"error": "Failed to initialize agents"}), 500
        
        reddit_data = reddit_scraper.scrape_for_pain_points(subreddit, topic, posts_limit)
        
        logger.info(f"Reddit scraping complete: {reddit_data.get('posts_scraped', 0)} posts found")
        
        pain_analysis = asyncio.run(
            pain_extractor.extract_pain_points_from_posts(reddit_data['posts'], topic, 8)
        )
        
        pain_points = [pp['pain_point'] if isinstance(pp, dict) else pp 
                      for pp in pain_analysis.get('pain_points', [])]
        
        if not pain_points:
            pain_points = reddit_data.get('pain_points_extracted', [])[:8]
        
        content_result = asyncio.run(
            generation_agent.generate_content(
                topic=topic, content_type=data.get('content_type', 'blog post'),
                target_audience='professionals', primary_keywords=[topic],
                search_intent='informational', brand_voice='friendly',
                content_goal='education', target_geography='global',
                pain_points=pain_points
            )
        )
        
        return jsonify({
            "success": True,
            "workflow": {
                "step1_reddit": {
                    "posts_scraped": reddit_data.get('posts_scraped', 0),
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
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

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
            topic=topic, content_type=data.get('content_type', 'blog post'),
            target_audience='professionals', primary_keywords=[topic],
            search_intent='informational', brand_voice='friendly',
            content_goal='education', target_geography='global'
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
        "service": "Waqzee Content Tool",
        "timestamp": datetime.now().isoformat(),
        "agents_loaded": {
            "reddit": RedditScraper is not None,
            "extractor": PainPointExtractor is not None,
            "humanizer": PainPointHumanizer is not None
        }
    })

@app.route('/debug')
def debug():
    """Debug route to check file structure"""
    import os
    
    debug_info = {
        "current_dir": os.getcwd(),
        "app_file_location": os.path.abspath(__file__),
        "python_version": sys.version,
    }
    
    # Check src/agents folder
    agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'agents')
    if os.path.exists(agents_path):
        debug_info["agents_folder_exists"] = True
        debug_info["agents_path"] = agents_path
        try:
            debug_info["files_in_agents"] = os.listdir(agents_path)
        except:
            debug_info["files_in_agents"] = "Error reading directory"
    else:
        debug_info["agents_folder_exists"] = False
        debug_info["agents_path"] = agents_path
    
    # Check if modules loaded
    debug_info["modules_loaded"] = {
        "RedditScraper": RedditScraper is not None,
        "PainPointExtractor": PainPointExtractor is not None,
        "PainPointHumanizer": PainPointHumanizer is not None
    }
    
    # Check environment variables
    debug_info["environment"] = {
        "REDDIT_CLIENT_ID": "present" if os.getenv('REDDIT_CLIENT_ID') else "missing",
        "REDDIT_CLIENT_SECRET": "present" if os.getenv('REDDIT_CLIENT_SECRET') else "missing",
        "REDDIT_USER_AGENT": "present" if os.getenv('REDDIT_USER_AGENT') else "missing",
        "Open_Api_Key": "present" if os.getenv('Open_Api_Key') else "missing"
    }
    
    return jsonify(debug_info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Waqzee Content Tool on port {port}")
    logger.info(f"Agents status: Reddit={RedditScraper is not None}, Extractor={PainPointExtractor is not None}, Humanizer={PainPointHumanizer is not None}")
    app.run(host="0.0.0.0", port=port, debug=False)
