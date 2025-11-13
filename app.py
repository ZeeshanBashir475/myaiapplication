import re
import json
import os
import sys
import logging
import traceback
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add agents directory to path
agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'agents')
if os.path.exists(agents_path):
    if agents_path not in sys.path:
        sys.path.insert(0, agents_path)

# Import OpenAI with latest version support
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI (latest version) imported successfully")
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("❌ OpenAI not available")

# Import agents
RedditScraper = None
SerpAgent = None
CompellingSEOStrategist = None
NLPAgent = None

try:
    from Reddit_scraper import RedditScraper
    logger.info("✅ RedditScraper imported")
except Exception as e:
    logger.error(f"❌ Failed to import RedditScraper: {e}")

try:
    from Serp_agent import SerpAgent
    logger.info("✅ SerpAgent imported")
except Exception as e:
    logger.error(f"❌ Failed to import SerpAgent: {e}")

try:
    from Compelling_seo_strategist import CompellingSEOStrategist
    logger.info("✅ CompellingSEOStrategist imported")
except Exception as e:
    logger.error(f"❌ Failed to import CompellingSEOStrategist: {e}")

try:
    from nlp_agent import NLPAgent
    logger.info("✅ NLPAgent imported")
except Exception as e:
    logger.error(f"❌ Failed to import NLPAgent: {e}")

app = Flask(__name__)
CORS(app)

# Global progress tracking
progress_updates = []

# Initialize NLP Agent globally
nlp_agent = None
try:
    nlp_agent = NLPAgent()
    if nlp_agent and nlp_agent.available:
        logger.info("✅ Global NLP Agent initialized and ready")
except Exception as e:
    logger.error(f"❌ Failed to initialize NLP Agent: {e}")

def add_progress(message: str, percentage: int):
    """Add progress update"""
    global progress_updates
    progress_updates.append({
        "message": message,
        "percentage": percentage,
        "timestamp": datetime.now().isoformat()
    })
    logger.info(f"Progress: {percentage}% - {message}")

class OpenAIClient:
    """Latest OpenAI client (v1.54+)"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('Open_Api_Key')
        self.available = False
        
        if not OPENAI_AVAILABLE:
            logger.warning("⚠️ OpenAI package not available")
            return
            
        if not self.api_key:
            logger.warning("⚠️ No OpenAI API key found")
            return
        
        try:
            logger.info("Creating OpenAI client (latest version)...")
            self.client = OpenAI(api_key=self.api_key)
            
            # Test the client
            logger.info("Testing OpenAI client...")
            models = self.client.models.list()
            logger.info(f"✅ OpenAI client working - {len(models.data)} models available")
            
            self.available = True
            logger.info("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            logger.error(traceback.format_exc())

def analyze_reddit(topic: str, subreddits: List[str]) -> Dict:
    """Analyze Reddit discussions"""
    add_progress("🔍 Searching Reddit discussions...", 10)
    
    pain_points = []
    
    if not RedditScraper:
        logger.warning("Reddit scraper not available - using fallback")
        pain_points = [
            {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100},
            {'pain': f"Understanding the complexities of {topic}", 'subreddit': "general", 'score': 80},
            {'pain': f"Making informed decisions about {topic}", 'subreddit': "general", 'score': 75}
        ]
    else:
        try:
            scraper = RedditScraper()
            for subreddit in subreddits[:5]:
                try:
                    logger.info(f"Scraping r/{subreddit}...")
                    data = scraper.scrape_for_pain_points(subreddit, topic, 10)
                    
                    for post in data.get('posts', [])[:5]:
                        title = post.get('title', '')
                        text = post.get('selftext', '')
                        combined_text = (title + ' ' + text).lower()
                        
                        if any(word in combined_text for word in ['problem', 'issue', 'help', 'struggling', 'frustrated', 'confused', 'difficult']):
                            pain_points.append({
                                'pain': title[:150] if title else "General discussion",
                                'subreddit': f"r/{subreddit}",
                                'score': post.get('score', 0)
                            })
                except Exception as e:
                    logger.error(f"Error scraping r/{subreddit}: {e}")
                    continue
            
            add_progress(f"✓ Found {len(pain_points)} pain points", 20)
        except Exception as e:
            logger.error(f"Reddit analysis error: {e}")
    
    if not pain_points:
        pain_points = [
            {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100},
            {'pain': f"Understanding best practices for {topic}", 'subreddit': "general", 'score': 85}
        ]
    
    return {'pain_points': pain_points[:10]}

def analyze_serp(keyword: str, num_competitors: int = 5, custom_urls: List[str] = None) -> Dict:
    """Analyze SERP results"""
    add_progress("🌐 Analyzing Google search results...", 30)
    
    if not SerpAgent:
        logger.warning("SERP agent not available - using fallback")
        return {
            'top_results': [
                {'title': f"Guide to {keyword}", 'link': '#', 'snippet': 'Comprehensive guide...', 'position': i+1}
                for i in range(num_competitors)
            ],
            'people_also_ask': [
                {'question': f"What is {keyword}?", 'snippet': 'Definition...'},
                {'question': f"How does {keyword} work?", 'snippet': 'Explanation...'}
            ],
            'opportunities': ['Add FAQ section', 'Include examples', 'Add statistics']
        }
    
    try:
        agent = SerpAgent()
        analysis = agent.analyze_keyword(keyword, location="United Kingdom")
        
        # If custom URLs provided, prioritize them
        if custom_urls:
            for i, url in enumerate(custom_urls[:num_competitors]):
                analysis['organic_results'].insert(i, {
                    'title': f"Custom Competitor {i+1}",
                    'link': url,
                    'snippet': 'Custom competitor URL',
                    'position': i+1
                })
        
        add_progress(f"✓ Analyzed {num_competitors} competitors", 40)
        
        return {
            'top_results': analysis['organic_results'][:num_competitors],
            'people_also_ask': analysis.get('people_also_ask', [])[:8],
            'opportunities': analysis.get('content_opportunities', [])[:5]
        }
    except Exception as e:
        logger.error(f"SERP analysis error: {e}")
        return {
            'top_results': [],
            'people_also_ask': [],
            'opportunities': []
        }

def analyze_competitor_nlp(serp_data: Dict) -> Dict:
    """NLP analysis of competitors"""
    if not nlp_agent or not nlp_agent.available:
        return {'competitor_entities': [], 'nlp_available': False}
    
    add_progress("🧠 Analyzing competitor content with NLP...", 35)
    
    try:
        competitor_text = " ".join([r.get('snippet', '') for r in serp_data.get('top_results', [])[:3]])
        
        if not competitor_text.strip():
            return {'competitor_entities': [], 'nlp_available': False}
        
        entities = nlp_agent.extract_entities(competitor_text)
        categories = nlp_agent.get_category(competitor_text)
        sentiment = nlp_agent.get_sentiment(competitor_text)
        
        logger.info(f"✅ Found {len(entities)} competitor entities")
        
        return {
            'competitor_entities': entities[:15],
            'competitor_categories': categories,
            'competitor_sentiment': sentiment,
            'nlp_available': True
        }
    except Exception as e:
        logger.error(f"Competitor NLP error: {e}")
        return {'competitor_entities': [], 'nlp_available': False}

def generate_content(params: Dict, reddit_data: Dict, serp_data: Dict, competitor_nlp: Dict, openai_client: OpenAIClient) -> Dict:
    """Generate SEO content with Writer Agent"""
    add_progress("✍️ Generating article with AI Writer Agent...", 50)
    
    try:
        if CompellingSEOStrategist and openai_client.available:
            strategist = CompellingSEOStrategist(api_key=openai_client.api_key)
            
            if strategist.available:
                logger.info("📝 Using Compelling SEO Strategist")
                
                # Enhance unique insights with NLP data
                unique_insights = params.get('unique_insights', '')
                if competitor_nlp.get('competitor_entities'):
                    top_entities = [e['name'] for e in competitor_nlp['competitor_entities'][:5]]
                    unique_insights += f"\n\nKey entities to cover: {', '.join(top_entities)}"
                
                # Add brand mentions
                if params.get('brand_mentions'):
                    unique_insights += f"\n\nMention these brands: {params['brand_mentions']}"
                
                result = strategist.write_article(
                    main_keyword=params['main_keyword'],
                    secondary_keywords=params.get('secondary_keywords', []),
                    tone=params.get('tone', 'friendly'),
                    target_country=params.get('target_country', 'United Kingdom'),
                    language=params.get('language', 'English'),
                    serp_data=serp_data,
                    reddit_data=reddit_data,
                    unique_insights=unique_insights,
                    title=params.get('title', params['main_keyword']),
                    max_tokens=int(params.get('word_count_goal', 2500) * 1.5)
                )
                
                if result['success']:
                    add_progress("✓ Article generated", 70)
                    return {
                        'content': result['content'],
                        'word_count': result['word_count'],
                        'success': True
                    }
        
        # Fallback
        logger.warning("Using fallback content generation")
        return {
            'content': f"<h1>{params.get('title', params['main_keyword'])}</h1><p>Content generation in progress...</p>",
            'word_count': 0,
            'success': False
        }
        
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        return {'content': f"<h1>Error</h1><p>{str(e)}</p>", 'word_count': 0, 'success': False}

def analyze_article_nlp(content: str, competitor_nlp: Dict) -> Dict:
    """NLP analysis of generated article"""
    if not nlp_agent or not nlp_agent.available:
        return {'nlp_available': False}
    
    add_progress("🧠 Analyzing generated article...", 75)
    
    try:
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        analysis = nlp_agent.analyze_full(clean_text)
        
        entity_coverage = {}
        if competitor_nlp.get('competitor_entities'):
            comp_names = set([e['name'].lower() for e in competitor_nlp['competitor_entities']])
            article_names = set([e['name'].lower() for e in analysis['entities']])
            
            covered = comp_names & article_names
            missing = comp_names - article_names
            
            coverage_score = len(covered) / len(comp_names) if comp_names else 1.0
            
            entity_coverage = {
                'coverage_score': round(coverage_score, 4),
                'coverage_percentage': round(coverage_score * 100, 2),
                'covered_count': len(covered),
                'missing_count': len(missing),
                'missing_entities': list(missing)[:10],
                'grade': get_grade(coverage_score)
            }
        
        return {
            'article_entities': analysis['entities'][:15],
            'article_sentiment': analysis['sentiment'],
            'entity_coverage': entity_coverage,
            'nlp_available': True,
            'stats': analysis['stats']
        }
    except Exception as e:
        logger.error(f"Article NLP error: {e}")
        return {'nlp_available': False}

def get_grade(score: float) -> str:
    if score >= 0.9: return "A+"
    elif score >= 0.8: return "A"
    elif score >= 0.7: return "B"
    elif score >= 0.6: return "C"
    else: return "D"

def calculate_metrics(content: str, params: Dict) -> Dict:
    """Calculate SEO metrics"""
    words = len(content.split())
    kw = params['main_keyword'].lower()
    kw_count = content.lower().count(kw)
    kw_density = (kw_count / words * 100) if words > 0 else 0
    
    seo_score = 50
    if '<h1>' in content: seo_score += 10
    if '<h2>' in content: seo_score += 10
    if kw_count > 0: seo_score += 10
    if words > 2000: seo_score += 20
    
    return {
        'word_count': words,
        'keyword_density': round(kw_density, 2),
        'seo_score': min(100, seo_score)
    }

# HTML Template with comprehensive inputs
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CompellSEO - Professional Content Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .logo { font-size: 36px; font-weight: 900; color: #fff; letter-spacing: -1px; }
        .tagline { font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px; }
        .container { max-width: 1400px; margin: 40px auto; padding: 0 20px; }
        .section { background: #1a1a1a; border-radius: 12px; padding: 40px; margin-bottom: 30px; border: 1px solid #333; }
        .section-title { font-size: 18px; font-weight: 700; color: #667eea; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }
        .section-title i { font-size: 20px; }
        .input-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group.full-width { grid-column: 1 / -1; }
        label { font-size: 12px; font-weight: 600; color: #999; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        input, select, textarea { padding: 12px 16px; border: 2px solid #333; border-radius: 8px; font-size: 14px; font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; transition: all 0.3s; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #667eea; background: #1a1a1a; }
        textarea { resize: vertical; min-height: 100px; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; padding: 18px 40px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.3s; text-transform: uppercase; letter-spacing: 1px; margin-top: 20px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .toggle { display: flex; align-items: center; gap: 10px; }
        .toggle input[type="checkbox"] { width: 50px; height: 26px; }
        .progress-container { background: #1a1a1a; padding: 30px; border-radius: 12px; margin-bottom: 30px; border: 1px solid #333; display: none; }
        .progress-container.active { display: block; }
        .progress-bar { background: #333; height: 40px; border-radius: 20px; overflow: hidden; }
        .progress-fill { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; }
        .progress-text { text-align: center; margin-top: 15px; color: #999; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
        .tabs { background: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #333; display: none; margin-top: 30px; }
        .tabs.active { display: block; }
        .tab-header { display: flex; background: #0a0a0a; flex-wrap: wrap; border-bottom: 2px solid #333; }
        .tab-btn { flex: 1; min-width: 150px; padding: 20px; background: none; border: none; font-weight: 600; color: #999; cursor: pointer; transition: all 0.3s; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 3px solid transparent; }
        .tab-btn.active { color: #667eea; border-bottom-color: #667eea; background: #1a1a1a; }
        .tab-content { display: none; padding: 40px; max-height: 600px; overflow-y: auto; }
        .tab-content.active { display: block; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; text-align: center; }
        .metric-value { font-size: 42px; font-weight: 900; }
        .metric-label { font-size: 11px; margin-top: 10px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px; margin-bottom: 30px; }
        .info-box { background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; padding: 15px; border-radius: 8px; margin-bottom: 20px; color: #ccc; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">WAQZEE CompellSEO</div>
        <div class="tagline">AI-Powered Content Generation with Advanced NLP Analysis</div>
    </div>
    
    <div class="container">
        <!-- Section 1: Core SEO Inputs -->
        <div class="section">
            <h2 class="section-title"><i class="fas fa-search"></i> Core SEO Inputs</h2>
            <div class="input-grid">
                <div class="form-group">
                    <label>Main Keyword *</label>
                    <input type="text" id="mainKeyword" placeholder="how to save money on car insurance UK" required>
                </div>
                <div class="form-group">
                    <label>Article Title</label>
                    <input type="text" id="title" placeholder="10 Proven Ways to Save on Car Insurance">
                </div>
                <div class="form-group">
                    <label>Search Intent</label>
                    <select id="searchIntent">
                        <option value="Informational">Informational</option>
                        <option value="Commercial">Commercial</option>
                        <option value="Transactional">Transactional</option>
                        <option value="Navigational">Navigational</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Target Country</label>
                    <select id="targetCountry">
                        <option value="United Kingdom">United Kingdom</option>
                        <option value="United States">United States</option>
                        <option value="Canada">Canada</option>
                        <option value="Australia">Australia</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Language</label>
                    <select id="language">
                        <option value="English">English</option>
                        <option value="Spanish">Spanish</option>
                        <option value="French">French</option>
                        <option value="German">German</option>
                    </select>
                </div>
                <div class="form-group full-width">
                    <label>Secondary Keywords (comma-separated)</label>
                    <input type="text" id="secondaryKeywords" placeholder="car insurance discounts, cheap insurance UK, best quotes">
                </div>
            </div>
        </div>

        <!-- Section 2: Tone, Style & Persona -->
        <div class="section">
            <h2 class="section-title"><i class="fas fa-palette"></i> Tone, Style & Persona</h2>
            <div class="input-grid">
                <div class="form-group">
                    <label>Tone of Voice</label>
                    <select id="tone">
                        <option value="friendly">Friendly & Conversational</option>
                        <option value="professional">Professional & Expert</option>
                        <option value="bold">Persuasive & Bold</option>
                        <option value="emotional">Authoritative</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Content Type</label>
                    <select id="contentType">
                        <option value="blog">Blog Post</option>
                        <option value="landing">Landing Page</option>
                        <option value="listicle">Listicle</option>
                        <option value="howto">How-to Guide</option>
                    </select>
                </div>
                <div class="form-group full-width">
                    <label>Target Audience</label>
                    <input type="text" id="targetAudience" placeholder="UK car owners, drivers under 30, cost-conscious families">
                </div>
                <div class="form-group full-width">
                    <label>Brand Voice Keywords (Optional)</label>
                    <input type="text" id="brandVoice" placeholder="trustworthy, expert, helpful, local">
                </div>
            </div>
        </div>

        <!-- Section 3: Research & Competitor Data -->
        <div class="section">
            <h2 class="section-title"><i class="fas fa-chart-line"></i> Research & Competitor Data</h2>
            <div class="input-grid">
                <div class="form-group">
                    <label>Number of Competitors to Analyze</label>
                    <select id="numCompetitors">
                        <option value="3">3 Competitors</option>
                        <option value="5" selected>5 Competitors</option>
                        <option value="7">7 Competitors</option>
                        <option value="10">10 Competitors</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Competitor Analysis Depth</label>
                    <select id="analysisDepth">
                        <option value="basic">Basic</option>
                        <option value="advanced" selected>Advanced (with NLP)</option>
                    </select>
                </div>
                <div class="form-group full-width">
                    <label>Subreddits to Search (comma-separated)</label>
                    <input type="text" id="subreddits" placeholder="ukpersonalfinance, CarTalkUK, AskUK" value="ukpersonalfinance, AskUK">
                </div>
                <div class="form-group full-width">
                    <label>Competitor URLs (Optional - one per line)</label>
                    <textarea id="competitorUrls" placeholder="https://www.comparethemarket.com
https://www.moneysupermarket.com"></textarea>
                </div>
            </div>
        </div>

        <!-- Section 4: Unique & Contextual Inputs -->
        <div class="section">
            <h2 class="section-title"><i class="fas fa-lightbulb"></i> Unique Content & Context</h2>
            <div class="input-grid">
                <div class="form-group full-width">
                    <label>Unique Insights & Data</label>
                    <textarea id="uniqueInsights" placeholder="Our data shows 30% of drivers don't compare insurance yearly..."></textarea>
                </div>
                <div class="form-group full-width">
                    <label>Brand or Product Mentions</label>
                    <textarea id="brandMentions" placeholder="Include references to Aviva, Direct Line, MoneySuperMarket"></textarea>
                </div>
                <div class="form-group full-width">
                    <label>Topics to Avoid</label>
                    <textarea id="topicsAvoid" placeholder="Avoid mentioning insurance scams, controversial claims"></textarea>
                </div>
                <div class="form-group full-width">
                    <label>Internal Links (Optional)</label>
                    <textarea id="internalLinks" placeholder="/insurance-guides
/car-tips"></textarea>
                </div>
            </div>
        </div>

        <!-- Section 5: Output Controls -->
        <div class="section">
            <h2 class="section-title"><i class="fas fa-cog"></i> Output Controls</h2>
            <div class="info-box">
                <i class="fas fa-info-circle"></i> Output settings control the format and structure of your generated content.
            </div>
            <div class="input-grid">
                <div class="form-group">
                    <label>Word Count Goal</label>
                    <input type="number" id="wordCountGoal" value="2500" min="500" max="5000" step="100">
                </div>
                <div class="form-group">
                    <label>Output Format</label>
                    <select id="outputFormat">
                        <option value="html" selected>HTML</option>
                        <option value="markdown">Markdown</option>
                        <option value="plain">Plain Text</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Include Tables/FAQs</label>
                    <div class="toggle">
                        <input type="checkbox" id="includeFaqs" checked>
                        <span>Generate FAQ section</span>
                    </div>
                </div>
                <div class="form-group">
                    <label>Generate Meta Tags</label>
                    <div class="toggle">
                        <input type="checkbox" id="generateMeta" checked>
                        <span>Title & description</span>
                    </div>
                </div>
            </div>
            
            <button class="btn" id="generateBtn" onclick="generateContent()">
                <i class="fas fa-magic"></i> Generate SEO Article
            </button>
        </div>

        <!-- Progress Bar -->
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%">0%</div>
            </div>
            <div class="progress-text" id="progressText">Initializing...</div>
        </div>

        <!-- Results Tabs -->
        <div class="tabs" id="resultTabs">
            <div class="tab-header">
                <button class="tab-btn active" onclick="switchTab(event, 'article')">
                    <i class="fas fa-file-alt"></i> Article
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'metrics')">
                    <i class="fas fa-chart-bar"></i> Metrics
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'nlp')">
                    <i class="fas fa-brain"></i> NLP Analysis
                </button>
            </div>
            
            <div class="tab-content active" id="articleTab">
                <div id="articleContent"></div>
            </div>
            
            <div class="tab-content" id="metricsTab">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="wordCount">0</div>
                        <div class="metric-label">Word Count</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="seoScore">0</div>
                        <div class="metric-label">SEO Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="entityCoverage">N/A</div>
                        <div class="metric-label">Entity Coverage</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="sentimentLabel">N/A</div>
                        <div class="metric-label">Sentiment</div>
                    </div>
                </div>
            </div>
            
            <div class="tab-content" id="nlpTab">
                <h3 style="margin-bottom: 20px;">NLP Analysis Results</h3>
                <div id="nlpResults"></div>
            </div>
        </div>
    </div>
    
    <script>
        let progressInterval;
        
        function switchTab(event, tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
        }
        
        async function generateContent() {
            const mainKeyword = document.getElementById('mainKeyword').value.trim();
            if (!mainKeyword) { alert('Please enter a main keyword'); return; }
            
            document.getElementById('progressContainer').classList.add('active');
            document.getElementById('generateBtn').disabled = true;
            
            const data = {
                main_keyword: mainKeyword,
                title: document.getElementById('title').value.trim(),
                secondary_keywords: document.getElementById('secondaryKeywords').value.split(',').map(k => k.trim()).filter(k => k),
                search_intent: document.getElementById('searchIntent').value,
                target_country: document.getElementById('targetCountry').value,
                language: document.getElementById('language').value,
                tone: document.getElementById('tone').value,
                content_type: document.getElementById('contentType').value,
                target_audience: document.getElementById('targetAudience').value,
                brand_voice: document.getElementById('brandVoice').value,
                num_competitors: parseInt(document.getElementById('numCompetitors').value),
                analysis_depth: document.getElementById('analysisDepth').value,
                subreddits: document.getElementById('subreddits').value.split(',').map(s => s.trim()).filter(s => s),
                competitor_urls: document.getElementById('competitorUrls').value.split('\n').map(u => u.trim()).filter(u => u),
                unique_insights: document.getElementById('uniqueInsights').value,
                brand_mentions: document.getElementById('brandMentions').value,
                topics_avoid: document.getElementById('topicsAvoid').value,
                internal_links: document.getElementById('internalLinks').value,
                word_count_goal: parseInt(document.getElementById('wordCountGoal').value),
                output_format: document.getElementById('outputFormat').value,
                include_faqs: document.getElementById('includeFaqs').checked,
                generate_meta: document.getElementById('generateMeta').checked
            };
            
            try {
                startProgressUpdates();
                const response = await fetch('/generate-seo-article', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (result.error) { alert('Error: ' + result.error); return; }
                displayResults(result);
                document.getElementById('resultTabs').classList.add('active');
                document.getElementById('resultTabs').scrollIntoView({ behavior: 'smooth' });
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate content. Check console for details.');
            } finally {
                stopProgressUpdates();
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('progressContainer').classList.remove('active');
            }
        }
        
        function startProgressUpdates() {
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch('/progress');
                    const data = await response.json();
                    if (data.length > 0) {
                        const latest = data[data.length - 1];
                        updateProgress(latest.percentage, latest.message);
                    }
                } catch (e) { console.error('Progress error:', e); }
            }, 1000);
        }
        
        function stopProgressUpdates() {
            if (progressInterval) { clearInterval(progressInterval); }
            updateProgress(100, 'Complete!');
        }
        
        function updateProgress(percentage, text) {
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressFill').textContent = percentage + '%';
            document.getElementById('progressText').textContent = text;
        }
        
        function displayResults(data) {
            document.getElementById('articleContent').innerHTML = data.article.content || '<p>No content generated</p>';
            document.getElementById('wordCount').textContent = data.metrics.word_count || 0;
            document.getElementById('seoScore').textContent = data.metrics.seo_score || 0;
            
            if (data.article_nlp && data.article_nlp.entity_coverage) {
                document.getElementById('entityCoverage').textContent = data.article_nlp.entity_coverage.grade || 'N/A';
            }
            
            if (data.article_nlp && data.article_nlp.article_sentiment) {
                document.getElementById('sentimentLabel').textContent = data.article_nlp.article_sentiment.label.toUpperCase();
            }
            
            let nlpHtml = '<p style="color:#999">NLP analysis complete</p>';
            if (data.article_nlp && data.article_nlp.nlp_available) {
                nlpHtml = `
                    <h4 style="color:#667eea; margin-bottom:15px;">Article Entities (Top 10):</h4>
                    <ul style="color:#ccc; line-height:1.8;">${data.article_nlp.article_entities.slice(0,10).map(e => 
                        `<li><strong>${e.name}</strong> (${e.type}) - Salience: ${e.salience}</li>`
                    ).join('')}</ul>
                    ${data.article_nlp.entity_coverage ? `
                        <h4 style="color:#667eea; margin:25px 0 15px;">Entity Coverage: ${data.article_nlp.entity_coverage.grade} (${data.article_nlp.entity_coverage.coverage_percentage}%)</h4>
                        <p style="color:#ccc;">Missing entities: ${data.article_nlp.entity_coverage.missing_entities.slice(0,5).join(', ')}</p>
                    ` : ''}
                `;
            }
            document.getElementById('nlpResults').innerHTML = nlpHtml;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-seo-article', methods=['POST'])
def generate_seo_article():
    """Generate complete SEO article with comprehensive inputs"""
    global progress_updates
    progress_updates = []
    
    try:
        params = request.get_json()
        logger.info(f"📥 Request for: {params.get('main_keyword')}")
        
        # Initialize OpenAI
        openai_client = OpenAIClient()
        if not openai_client.available:
            return jsonify({"error": "OpenAI API not configured. Please set OPENAI_API_KEY environment variable."}), 500
        
        # 1. Reddit Analysis
        reddit_data = analyze_reddit(
            params['main_keyword'],
            params.get('subreddits', ['askreddit'])
        )
        
        # 2. SERP Analysis
        serp_data = analyze_serp(
            params['main_keyword'],
            params.get('num_competitors', 5),
            params.get('competitor_urls')
        )
        
        # 3. Competitor NLP
        competitor_nlp = {}
        if params.get('analysis_depth') == 'advanced':
            competitor_nlp = analyze_competitor_nlp(serp_data)
        
        # 4. Generate Content
        article_data = generate_content(params, reddit_data, serp_data, competitor_nlp, openai_client)
        
        # 5. Article NLP
        article_nlp = {}
        if params.get('analysis_depth') == 'advanced':
            article_nlp = analyze_article_nlp(article_data['content'], competitor_nlp)
        
        # 6. Calculate Metrics
        metrics = calculate_metrics(article_data['content'], params)
        
        add_progress("✅ Complete!", 100)
        
        result = {
            "inputs": params,
            "reddit_pain_points": reddit_data['pain_points'],
            "serp_summary": {
                "top_results": serp_data['top_results'],
                "people_also_ask": serp_data['people_also_ask']
            },
            "competitor_nlp": competitor_nlp,
            "article": {
                "content": article_data['content']
            },
            "metrics": metrics,
            "article_nlp": article_nlp
        }
        
        logger.info("✅ Article generated successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/progress')
def get_progress():
    global progress_updates
    return jsonify(progress_updates.copy())

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "openai_available": OPENAI_AVAILABLE,
        "reddit_available": RedditScraper is not None,
        "serp_available": SerpAgent is not None,
        "writer_available": CompellingSEOStrategist is not None,
        "nlp_available": nlp_agent.available if nlp_agent else False
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting CompellSEO Platform on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
