import re
import json
import os
import openai
from typing import Dict, List
from datetime import datetime
import asyncio
from flask import Flask, request, jsonify, render_template_string
import statistics
from collections import Counter

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
else:
    logger.error(f"Agents folder not found: {agents_path}")

# Try to import agents safely
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

if all([RedditScraper, PainPointExtractor, PainPointHumanizer]):
    logger.info("All agents imported successfully!")
else:
    logger.warning(f"Some agents failed to import")

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
                             content_goal: str, target_geography: str, pain_points: List[str] = None) -> Dict:
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
        
        humanizer = None
        logger.info("Humanizer skipped")
        
        return generation_agent, reddit_scraper, pain_extractor, humanizer
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None, None, None

class ContentMetrics:
    """Calculate SEO and compelling metrics for content"""
    
    @staticmethod
    def calculate(html_content: str, pain_points: List[str] = None) -> Dict:
        """Calculate comprehensive metrics"""
        # Strip HTML tags for analysis
        text = re.sub(r'<[^>]+>', '', html_content)
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        word_count = len(words)
        sentence_count = max(1, len([s for s in sentences if s.strip()]))
        paragraph_count = max(1, len([p for p in paragraphs if p.strip()]))
        
        # Unique words
        unique_words = len(set(w.lower() for w in words))
        
        # Readability
        flesch_kincaid = ContentMetrics.flesch_kincaid(len(words), sentence_count, len([w for w in words if len(w) > 2]))
        
        # Headings
        headings = len(re.findall(r'<h[1-6]>', html_content))
        
        # Lists
        lists = len(re.findall(r'<(ul|ol)>', html_content))
        
        # Pain point coverage
        pain_coverage = 0
        if pain_points:
            text_lower = text.lower()
            matched = sum(1 for p in pain_points if p.lower() in text_lower)
            pain_coverage = (matched / len(pain_points) * 100) if pain_points else 0
        
        # Image tags
        images = len(re.findall(r'<img', html_content))
        
        # Links
        links = len(re.findall(r'<a\s+href', html_content))
        
        # Content structure score
        structure_score = min(100, (headings * 10) + (lists * 5) + (images * 5))
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'unique_words': unique_words,
            'readability_score': max(0, min(100, flesch_kincaid)),
            'headings_count': headings,
            'lists_count': lists,
            'images_count': images,
            'links_count': links,
            'pain_points_addressed': pain_coverage,
            'content_structure_score': structure_score,
            'uniqueness_score': min(100, (unique_words / max(1, word_count)) * 100),
            'engagement_score': min(100, ((lists + images + links) / max(1, word_count)) * 10)
        }
    
    @staticmethod
    def flesch_kincaid(words: int, sentences: int, complex_words: int) -> float:
        """Calculate Flesch-Kincaid Grade Level"""
        if sentences == 0 or words == 0:
            return 0
        return 0.39 * (words / sentences) + 11.8 * (complex_words / words) - 15.59

# PROFESSIONAL BLACK & WHITE HTML TEMPLATE WITH REAL-TIME ANALYSIS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waqzee - Content Generation Tool</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
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
        
        /* Content Grid - 3 columns */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        @media (max-width: 1400px) {
            .content-grid {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        @media (max-width: 900px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Form Section */
        .form-section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #000;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 6px;
            color: #1a1a1a;
        }
        
        input[type="text"],
        input[type="email"],
        select,
        textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            font-size: 13px;
            font-family: inherit;
            transition: border-color 0.2s;
            background: white;
            color: #000;
        }
        
        input:focus,
        select:focus,
        textarea:focus {
            border-color: #000;
            outline: none;
            box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
        }
        
        textarea {
            resize: vertical;
            min-height: 70px;
        }
        
        /* Buttons */
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
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
            padding: 8px 16px;
            width: auto;
            display: inline-block;
            margin-right: 8px;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        /* Status Messages */
        .status-message {
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 16px;
            font-size: 13px;
            display: none;
        }
        
        .status-message.show {
            display: block;
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
        
        /* Pain Points */
        .pain-points-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .pain-point-item {
            padding: 12px;
            background: #fafafa;
            border-left: 3px solid #000;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 13px;
        }
        
        .pain-point-item:last-child {
            margin-bottom: 0;
        }
        
        /* Metrics Grid */
        .metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        
        .metric {
            background: white;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }
        
        .metric-value {
            font-size: 22px;
            font-weight: 700;
            color: #000;
            margin-bottom: 4px;
        }
        
        .metric-label {
            font-size: 11px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric.good .metric-value { color: #1a5f52; }
        .metric.warning .metric-value { color: #8b6f00; }
        .metric.poor .metric-value { color: #8b3333; }
        
        /* Editor */
        .editor-section {
            background: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 0;
            overflow: hidden;
            grid-column: 1 / -1;
        }
        
        .editor-tabs {
            display: flex;
            border-bottom: 1px solid #e0e0e0;
            background: #fafafa;
        }
        
        .editor-tab {
            padding: 12px 20px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            color: #666;
            border-bottom: 2px solid transparent;
        }
        
        .editor-tab.active {
            color: #000;
            border-bottom-color: #000;
        }
        
        .editor-content {
            padding: 20px;
            min-height: 500px;
        }
        
        .ql-toolbar.ql-snow {
            background: transparent;
            border: none;
            border-bottom: 1px solid #e0e0e0;
            padding: 12px 20px;
            margin: 0;
        }
        
        .ql-container.ql-snow {
            border: none;
            font-size: 14px;
            font-family: inherit;
            padding: 20px;
        }
        
        .ql-editor {
            padding: 0;
            min-height: 400px;
        }
        
        /* Code view */
        .code-view {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 12px;
            line-height: 1.5;
            font-family: 'Monaco', 'Courier New', monospace;
        }
        
        .code-view pre {
            margin: 0;
        }
        
        /* Export buttons */
        .export-buttons {
            display: flex;
            gap: 8px;
            margin-top: 16px;
        }
        
        .export-buttons .btn-secondary {
            flex: 1;
            margin: 0;
        }
        
        /* Spinner */
        .spinner {
            width: 30px;
            height: 30px;
            border: 3px solid #e0e0e0;
            border-top: 3px solid #000;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .main {
                padding: 20px;
            }
            
            .page-title {
                font-size: 24px;
            }
            
            .metrics {
                grid-template-columns: 1fr;
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

        <!-- Status Messages -->
        <div id="statusMessage" class="status-message"></div>

        <!-- Content Grid -->
        <div class="content-grid">
            <!-- Column 1: Research Input -->
            <div>
                <div class="form-section">
                    <h4 class="section-title">Reddit Research</h4>
                    
                    <div class="form-group">
                        <label>Subreddit</label>
                        <input type="text" id="reddit_subreddit" placeholder="entrepreneur" value="entrepreneur">
                    </div>
                    
                    <div class="form-group">
                        <label>Topic to Research</label>
                        <input type="text" id="reddit_topic" placeholder="starting a business" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Posts to Analyze</label>
                        <select id="reddit_posts">
                            <option value="25">25 posts</option>
                            <option value="50" selected>50 posts</option>
                            <option value="100">100 posts</option>
                        </select>
                    </div>
                </div>

                <div class="form-section" style="margin-top: 20px;">
                    <h4 class="section-title">Article Details</h4>
                    
                    <div class="form-group">
                        <label>Article Title</label>
                        <input type="text" id="article_title" placeholder="Your article title...">
                    </div>
                    
                    <div class="form-group">
                        <label>English Variant</label>
                        <select id="english_variant">
                            <option value="british">British English</option>
                            <option value="american" selected>American English</option>
                            <option value="australian">Australian English</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Target Audience</label>
                        <input type="text" id="target_audience" placeholder="professionals, entrepreneurs...">
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
                    
                    <div class="form-group">
                        <label>Your Unique Angle</label>
                        <textarea id="unique_angle" placeholder="What makes this stand out? Your expertise?"></textarea>
                    </div>
                    
                    <button class="btn btn-primary" onclick="generateContent()">Generate Content</button>
                </div>
            </div>

            <!-- Column 2: Pain Points & Metrics -->
            <div>
                <div id="painPointsSection" class="pain-points-section" style="display: none;">
                    <h4 class="section-title">Pain Points Identified</h4>
                    <div id="painPointsList"></div>
                </div>

                <div style="margin-top: 20px; display: none;" id="metricsSection">
                    <div class="form-section">
                        <h4 class="section-title">Research Metrics</h4>
                        <div style="font-size: 13px; color: #666;">
                            <p>Posts Analyzed: <strong id="postsCount">0</strong></p>
                            <p>Pain Points Found: <strong id="painPointsCount">0</strong></p>
                            <p>Word Count Generated: <strong id="wordCount">0</strong></p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Column 3: Real-time Analysis -->
            <div>
                <div class="form-section">
                    <h4 class="section-title">Real-time Analysis</h4>
                    <div id="liveMetrics" class="metrics">
                        <div class="metric" title="How easy the content is to read (higher is better)">
                            <div class="metric-value" id="readabilityScore">0</div>
                            <div class="metric-label">Readability</div>
                        </div>
                        <div class="metric" title="Unique words vs total words">
                            <div class="metric-value" id="uniquenessScore">0</div>
                            <div class="metric-label">Uniqueness</div>
                        </div>
                        <div class="metric" title="Percentage of pain points addressed">
                            <div class="metric-value" id="painCoverageScore">0%</div>
                            <div class="metric-label">Pain Coverage</div>
                        </div>
                        <div class="metric" title="Content structure quality">
                            <div class="metric-value" id="structureScore">0</div>
                            <div class="metric-label">Structure</div>
                        </div>
                        <div class="metric" title="Words with images and lists">
                            <div class="metric-value" id="engagementScore">0</div>
                            <div class="metric-label">Engagement</div>
                        </div>
                        <div class="metric" title="Total word count">
                            <div class="metric-value" id="contentWordCount">0</div>
                            <div class="metric-label">Word Count</div>
                        </div>
                    </div>
                </div>

                <div class="form-section" style="margin-top: 20px;">
                    <h4 class="section-title">Quick Tips</h4>
                    <div style="font-size: 13px; line-height: 1.6; color: #666;">
                        <p>Add images to increase engagement</p>
                        <p>Use clear headings to organize content</p>
                        <p>Include lists and bullet points</p>
                        <p>Reference pain points directly</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Editor Section - Full Width -->
        <div id="editorSection" style="display: none;">
            <div class="editor-section">
                <div class="editor-tabs">
                    <button class="editor-tab active" onclick="switchTab('editor')">Editor</button>
                    <button class="editor-tab" onclick="switchTab('code')">HTML Code</button>
                    <button class="editor-tab" onclick="switchTab('preview')">Preview</button>
                </div>

                <!-- Editor Tab -->
                <div id="editorTab" class="editor-content">
                    <div id="editor-toolbar"></div>
                    <div id="editor"></div>
                </div>

                <!-- Code Tab -->
                <div id="codeTab" class="editor-content" style="display: none; background: #1e1e1e;">
                    <div class="code-view">
                        <pre><code id="codeContent" class="language-html"></code></pre>
                    </div>
                    <div class="export-buttons">
                        <button class="btn-secondary" onclick="copyCode()">Copy Code</button>
                        <button class="btn-secondary" onclick="downloadHTML()">Download HTML</button>
                    </div>
                </div>

                <!-- Preview Tab -->
                <div id="previewTab" class="editor-content" style="display: none; background: white;">
                    <div id="previewContent"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Quill Editor -->
    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
        let editor = null;
        let currentPainPoints = [];
        let currentContent = "";

        // Initialize Quill editor
        function initEditor() {
            if (!editor) {
                editor = new Quill('#editor', {
                    theme: 'snow',
                    modules: {
                        toolbar: [
                            ['bold', 'italic', 'underline'],
                            [{ 'header': [1, 2, 3, false] }],
                            ['blockquote', 'code-block'],
                            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                            ['link', 'image'],
                            ['clean']
                        ]
                    },
                    placeholder: 'Start editing your content here...'
                });

                // Real-time analysis on content change
                editor.on('text-change', function() {
                    updateLiveMetrics();
                    updateCodeView();
                });
            }
        }

        function showStatus(message, type = 'loading') {
            const statusEl = document.getElementById('statusMessage');
            statusEl.className = 'status-message show status-' + type;
            statusEl.textContent = message;
            if (type !== 'loading') {
                setTimeout(() => { statusEl.classList.remove('show'); }, 4000);
            }
        }

        async function generateContent() {
            const subreddit = document.getElementById('reddit_subreddit').value;
            const topic = document.getElementById('reddit_topic').value;
            const title = document.getElementById('article_title').value;
            const contentType = document.getElementById('content_type').value;
            const englishVariant = document.getElementById('english_variant').value;

            if (!topic) {
                showStatus('Please enter a topic to research', 'error');
                return;
            }

            if (!title) {
                showStatus('Please enter an article title', 'error');
                return;
            }

            showStatus('Researching Reddit and generating content...', 'loading');

            try {
                const postsLimit = document.getElementById('reddit_posts').value;
                const response = await fetch('/reddit-to-content', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        subreddit,
                        topic,
                        posts_limit: parseInt(postsLimit),
                        content_type: contentType,
                        english_variant: englishVariant,
                        article_title: title
                    })
                });

                const result = await response.json();

                if (result.error) {
                    showStatus('Error: ' + result.error, 'error');
                    return;
                }

                const workflow = result.workflow;
                
                // Display pain points
                if (workflow.step2_pain_points.pain_points.length > 0) {
                    displayPainPoints(workflow.step2_pain_points.pain_points);
                    currentPainPoints = workflow.step2_pain_points.pain_points;
                }

                // Display metrics
                document.getElementById('postsCount').textContent = workflow.step1_reddit.posts_scraped;
                document.getElementById('painPointsCount').textContent = workflow.step2_pain_points.extracted;
                document.getElementById('wordCount').textContent = workflow.step3_content.word_count;
                document.getElementById('metricsSection').style.display = 'block';

                // Load content into editor
                initEditor();
                currentContent = result.final_content;
                editor.root.innerHTML = result.final_content;
                document.getElementById('editorSection').style.display = 'block';

                updateLiveMetrics();
                updateCodeView();
                
                showStatus('Content generated successfully! Now edit and refine it.', 'success');

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
                item.innerHTML = `<strong>${index + 1}.</strong> ${point}`;
                list.appendChild(item);
            });

            section.style.display = 'block';
        }

        function updateLiveMetrics() {
            if (!editor) return;
            
            const htmlContent = editor.root.innerHTML;
            
            fetch('/analyze-metrics', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    content: htmlContent,
                    pain_points: currentPainPoints
                })
            })
            .then(r => r.json())
            .then(data => {
                const m = data.metrics;
                
                // Update metrics display
                document.getElementById('readabilityScore').textContent = Math.round(m.readability_score);
                document.getElementById('uniquenessScore').textContent = Math.round(m.uniqueness_score);
                document.getElementById('painCoverageScore').textContent = Math.round(m.pain_points_addressed) + '%';
                document.getElementById('structureScore').textContent = Math.round(m.content_structure_score);
                document.getElementById('engagementScore').textContent = Math.round(m.engagement_score);
                document.getElementById('contentWordCount').textContent = m.word_count;

                // Color code metrics
                colorMetrics(m);
            })
            .catch(e => console.error('Metrics error:', e));
        }

        function colorMetrics(metrics) {
            const scoreEl = (id, value) => {
                const el = document.getElementById(id).parentElement;
                el.className = 'metric';
                if (value >= 70) el.classList.add('good');
                else if (value >= 50) el.classList.add('warning');
                else el.classList.add('poor');
            };

            scoreEl('readabilityScore', metrics.readability_score);
            scoreEl('uniquenessScore', metrics.uniqueness_score);
            scoreEl('structureScore', metrics.content_structure_score);
            scoreEl('engagementScore', metrics.engagement_score);
        }

        function updateCodeView() {
            if (!editor) return;
            
            const html = editor.root.innerHTML;
            const codeEl = document.getElementById('codeContent');
            codeEl.textContent = html;
            hljs.highlightElement(codeEl);
            document.getElementById('previewContent').innerHTML = html;
        }

        function switchTab(tab) {
            // Hide all tabs
            document.getElementById('editorTab').style.display = 'none';
            document.getElementById('codeTab').style.display = 'none';
            document.getElementById('previewTab').style.display = 'none';

            // Remove active class
            document.querySelectorAll('.editor-tab').forEach(t => t.classList.remove('active'));

            // Show selected tab
            const tabMap = {
                'editor': 'editorTab',
                'code': 'codeTab',
                'preview': 'previewTab'
            };
            document.getElementById(tabMap[tab]).style.display = 'block';
            event.target.classList.add('active');

            if (tab === 'code') {
                updateCodeView();
            }
        }

        function copyCode() {
            const code = document.getElementById('codeContent').textContent;
            navigator.clipboard.writeText(code).then(() => {
                showStatus('Code copied to clipboard!', 'success');
            });
        }

        function downloadHTML() {
            const html = document.getElementById('codeContent').textContent;
            const title = document.getElementById('article_title').value || 'article';
            const blob = new Blob([`<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>${title}</title>
    <style>
        body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
    </style>
</head>
<body>
${html}
</body>
</html>`], { type: 'text/html' });
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = title.replace(/\s+/g, '-').toLowerCase() + '.html';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showStatus('HTML file downloaded!', 'success');
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
        
        if not all([generation_agent, reddit_scraper, pain_extractor]):
            return jsonify({"error": "Failed to initialize agents"}), 500
        
        reddit_data = reddit_scraper.scrape_for_pain_points(subreddit, topic, posts_limit)
        
        logger.info(f"Reddit scraping: {reddit_data.get('posts_scraped', 0)} posts")
        
        pain_analysis = asyncio.run(
            pain_extractor.extract_pain_points_from_posts(reddit_data.get('posts', []), topic, 8)
        )
        
        pain_points = [pp['pain_point'] if isinstance(pp, dict) else pp 
                      for pp in pain_analysis.get('pain_points', [])]
        
        if not pain_points:
            pain_points = reddit_data.get('pain_points_extracted', [])[:8]
        
        # Ensure we have pain points
        if not pain_points:
            pain_points = ["Unable to extract specific pain points - please refine your search"]
        
        content_result = asyncio.run(
            generation_agent.generate_content(
                topic=data.get('article_title', topic),
                content_type=data.get('content_type', 'blog post'),
                target_audience=data.get('target_audience', 'professionals'),
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
                }
            },
            "final_content": content_result['improved_content']
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-metrics', methods=['POST'])
def analyze_metrics():
    """Real-time content analysis"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        pain_points = data.get('pain_points', [])
        
        metrics = ContentMetrics.calculate(content, pain_points)
        
        return jsonify({"metrics": metrics})
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "Waqzee Content Tool",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Waqzee Content Tool on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
