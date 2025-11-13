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

# Import OpenAI - LATEST VERSION
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
    from Nlp_agent import NLPAgent
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
        logger.info("✅ Global NLP Agent initialized")
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
    """OpenAI client with latest API (v1.54+)"""
    
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
            logger.info("Creating OpenAI client...")
            self.client = OpenAI(api_key=self.api_key)
            
            # Test the client
            logger.info("Testing OpenAI client...")
            self.client.models.list()
            
            self.available = True
            logger.info("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            logger.error(traceback.format_exc())
    
    def generate_seo_article(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate SEO-optimized article"""
        if not self.available:
            return "<h1>Content Generation Unavailable</h1><p>OpenAI API key not configured.</p>"
        
        try:
            logger.info("🤖 Calling OpenAI API...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "You are an expert SEO content writer. Create engaging, well-structured HTML content optimized for search engines and user experience."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            content = response.choices[0].message.content
            logger.info(f"✅ Generated {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
            return f"<p>Error: {str(e)}</p>"

def analyze_reddit(topic: str, subreddits: List[str]) -> Dict:
    """Analyze Reddit discussions"""
    add_progress("🔍 Searching Reddit discussions...", 10)
    
    pain_points = []
    
    if not RedditScraper:
        logger.warning("Reddit scraper not available - using fallback")
        pain_points = [
            {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100},
            {'pain': f"Understanding the complexities of {topic}", 'subreddit': "general", 'score': 80}
        ]
    else:
        try:
            scraper = RedditScraper()
            for subreddit in subreddits[:3]:
                try:
                    logger.info(f"Scraping r/{subreddit}...")
                    data = scraper.scrape_for_pain_points(subreddit, topic, 10)
                    
                    for post in data.get('posts', [])[:5]:
                        title = post.get('title', '')
                        text = post.get('selftext', '')
                        combined = (title + ' ' + text).lower()
                        
                        if any(w in combined for w in ['problem', 'issue', 'help', 'struggling']):
                            pain_points.append({
                                'pain': title[:150] if title else "General discussion",
                                'subreddit': f"r/{subreddit}",
                                'score': post.get('score', 0)
                            })
                except Exception as e:
                    logger.error(f"Error scraping r/{subreddit}: {e}")
            
            add_progress(f"✓ Found {len(pain_points)} pain points", 20)
        except Exception as e:
            logger.error(f"Reddit error: {e}")
    
    if not pain_points:
        pain_points = [
            {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100}
        ]
    
    return {'pain_points': pain_points[:10]}

def analyze_serp(keyword: str, num_competitors: int = 5) -> Dict:
    """Analyze SERP results"""
    add_progress("🌐 Analyzing Google search results...", 30)
    
    if not SerpAgent:
        logger.warning("SERP agent not available - using fallback")
        return {
            'top_results': [{'title': f"Guide to {keyword}", 'link': '#', 'snippet': 'Comprehensive guide...', 'position': i+1} for i in range(num_competitors)],
            'people_also_ask': [{'question': f"What is {keyword}?", 'snippet': 'Definition...'}],
            'opportunities': ['Add FAQ section', 'Include examples']
        }
    
    try:
        agent = SerpAgent()
        analysis = agent.analyze_keyword(keyword, location="United Kingdom")
        
        add_progress(f"✓ Analyzed {num_competitors} competitors", 40)
        
        return {
            'top_results': analysis['organic_results'][:num_competitors],
            'people_also_ask': analysis.get('people_also_ask', [])[:5],
            'opportunities': analysis.get('content_opportunities', [])[:5]
        }
    except Exception as e:
        logger.error(f"SERP error: {e}")
        return {
            'top_results': [],
            'people_also_ask': [],
            'opportunities': []
        }

def analyze_competitor_nlp(serp_data: Dict) -> Dict:
    """NLP analysis of competitors"""
    if not nlp_agent or not nlp_agent.available:
        return {'competitor_entities': [], 'nlp_available': False}
    
    add_progress("🧠 Analyzing competitor content...", 35)
    
    try:
        comp_text = " ".join([r.get('snippet', '') for r in serp_data.get('top_results', [])[:3]])
        
        if not comp_text.strip():
            return {'competitor_entities': [], 'nlp_available': False}
        
        entities = nlp_agent.extract_entities(comp_text)
        sentiment = nlp_agent.get_sentiment(comp_text)
        
        logger.info(f"✅ Found {len(entities)} competitor entities")
        
        return {
            'competitor_entities': entities[:15],
            'competitor_sentiment': sentiment,
            'nlp_available': True
        }
    except Exception as e:
        logger.error(f"Competitor NLP error: {e}")
        return {'competitor_entities': [], 'nlp_available': False}

def generate_content(params: Dict, reddit_data: Dict, serp_data: Dict, competitor_nlp: Dict, openai_client: OpenAIClient) -> Dict:
    """Generate SEO content"""
    add_progress("✍️ Generating article...", 50)
    
    try:
        # Try Writer Agent first
        if CompellingSEOStrategist and openai_client.available:
            strategist = CompellingSEOStrategist(api_key=openai_client.api_key)
            
            if strategist.available:
                logger.info("📝 Using Compelling SEO Strategist")
                
                # Enhance insights with NLP data
                unique_insights = params.get('unique_insights', '')
                if competitor_nlp.get('competitor_entities'):
                    top_entities = [e['name'] for e in competitor_nlp['competitor_entities'][:5]]
                    unique_insights += f"\n\nKey entities to cover: {', '.join(top_entities)}"
                
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
                    max_tokens=4000
                )
                
                if result['success']:
                    add_progress("✓ Article generated", 70)
                    return {
                        'content': result['content'],
                        'word_count': result['word_count'],
                        'success': True
                    }
        
        # Fallback to basic generation
        logger.warning("Using fallback generation")
        pain_points_text = '\n'.join([f"- {p.get('pain', '')}" for p in reddit_data['pain_points'][:5]])
        paa_text = '\n'.join([f"- {q['question']}" for q in serp_data['people_also_ask'][:5]])
        
        prompt = f"""
Create a comprehensive, SEO-optimized article about "{params['main_keyword']}"

Title: {params.get('title', params['main_keyword'])}
Tone: {params.get('tone', 'Professional yet friendly')}
Target: {params.get('target_country', 'United Kingdom')}

REDDIT PAIN POINTS:
{pain_points_text}

PEOPLE ALSO ASK:
{paa_text}

USER INSIGHTS:
{params.get('unique_insights', 'None provided')}

Write a complete 2,400+ word article with proper HTML formatting (h1, h2, p, ul, li).
"""
        
        article = openai_client.generate_seo_article(prompt)
        
        add_progress("✓ Article generated", 70)
        
        return {
            'content': article,
            'word_count': len(article.split()),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        return {
            'content': f"<h1>Error</h1><p>{str(e)}</p>",
            'word_count': 0,
            'success': False
        }

def analyze_article_nlp(content: str, competitor_nlp: Dict) -> Dict:
    """NLP analysis of generated article"""
    if not nlp_agent or not nlp_agent.available:
        return {'nlp_available': False}
    
    add_progress("🧠 Analyzing article...", 75)
    
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
            
            grade = "A+" if coverage_score >= 0.9 else "A" if coverage_score >= 0.8 else "B" if coverage_score >= 0.7 else "C" if coverage_score >= 0.6 else "D"
            
            entity_coverage = {
                'coverage_percentage': round(coverage_score * 100, 2),
                'grade': grade,
                'missing_entities': list(missing)[:10]
            }
        
        return {
            'article_entities': analysis['entities'][:15],
            'article_sentiment': analysis['sentiment'],
            'entity_coverage': entity_coverage,
            'nlp_available': True
        }
    except Exception as e:
        logger.error(f"Article NLP error: {e}")
        return {'nlp_available': False}

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
    
    sentences = len(re.split(r'[.!?]+', content))
    avg_words = words / sentences if sentences > 0 else 0
    readability = "Easy" if avg_words < 15 else "Medium" if avg_words < 20 else "Advanced"
    
    return {
        'word_count': words,
        'keyword_density': round(kw_density, 2),
        'seo_score': min(100, seo_score),
        'readability': readability
    }

def generate_recommendations(metrics: Dict, params: Dict, article_nlp: Dict) -> List[Dict]:
    """Generate SEO recommendations"""
    add_progress("📊 Generating recommendations...", 80)
    
    recs = []
    
    if metrics['keyword_density'] < 1:
        recs.append({'tip': f"Increase '{params['main_keyword']}' usage to 1-2%", 'impact': 5, 'category': 'SEO'})
    
    if metrics['word_count'] < 2400:
        recs.append({'tip': f"Expand to 2,400+ words (current: {metrics['word_count']})", 'impact': 5, 'category': 'Content'})
    
    if article_nlp.get('entity_coverage', {}).get('coverage_percentage', 100) < 70:
        recs.append({'tip': "Improve entity coverage - add missing key topics", 'impact': 5, 'category': 'Entity SEO'})
    
    recs.extend([
        {'tip': "Add personal story in intro", 'impact': 4, 'category': 'Engagement'},
        {'tip': "Include schema markup for FAQ", 'impact': 3, 'category': 'Technical SEO'},
        {'tip': "Add 3-5 images with alt text", 'impact': 3, 'category': 'UX'}
    ])
    
    return recs[:8]

def generate_competitor_comparison(metrics: Dict, serp_data: Dict, reddit_data: Dict, article_nlp: Dict) -> Dict:
    """Generate competitor comparison"""
    add_progress("🏆 Analyzing competitors...", 90)
    
    features = [
        {
            'feature': 'Word Count',
            'competitors': '1,500-2,000 avg',
            'you': f"{metrics['word_count']} words",
            'advantage': metrics['word_count'] > 2000
        },
        {
            'feature': 'Emotional Engagement',
            'competitors': 'Generic',
            'you': f"Uses {len(reddit_data['pain_points'])} real pain points",
            'advantage': True
        },
        {
            'feature': 'Keyword Optimization',
            'competitors': 'Basic',
            'you': f"{metrics['keyword_density']}% density",
            'advantage': True
        }
    ]
    
    if article_nlp.get('entity_coverage'):
        coverage = article_nlp['entity_coverage']
        features.append({
            'feature': 'Entity Coverage',
            'competitors': '100% baseline',
            'you': f"{coverage['coverage_percentage']:.0f}% (Grade: {coverage['grade']})",
            'advantage': coverage['coverage_percentage'] >= 80
        })
    
    summary = f"""Your article outperforms competitors by:
• Integrating {len(reddit_data['pain_points'])} real pain points
• Providing {metrics['word_count']} words of coverage
• Achieving {metrics['seo_score']}% SEO score"""
    
    if article_nlp.get('entity_coverage'):
        summary += f"\n• Entity coverage: {article_nlp['entity_coverage']['coverage_percentage']:.0f}% (Grade: {article_nlp['entity_coverage']['grade']})"
    
    return {'features': features, 'summary': summary}

# Keep the exact same HTML template from original (with Waqzee black/white theme)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Article Generator - Waqzee Digital</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', sans-serif; background: #000000; color: #ffffff; min-height: 100vh; line-height: 1.6; }
        .header { background: #ffffff; padding: 20px 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 100; }
        .logo { font-size: 32px; font-weight: 900; color: #000000; letter-spacing: -1px; }
        .logo-subtitle { font-size: 12px; font-weight: 400; color: #666; letter-spacing: 2px; text-transform: uppercase; }
        .container { max-width: 1400px; margin: 40px auto; padding: 0 20px; }
        .input-section { background: #ffffff; color: #000000; padding: 40px; margin-bottom: 40px; box-shadow: 0 10px 40px rgba(255,255,255,0.1); }
        .section-title { font-size: 28px; font-weight: 700; margin-bottom: 30px; color: #000000; text-transform: uppercase; letter-spacing: 1px; }
        .input-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-bottom: 25px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group.full-width { grid-column: 1 / -1; }
        label { font-size: 11px; font-weight: 700; color: #000000; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
        input, select, textarea { padding: 12px 15px; border: 2px solid #000000; font-size: 14px; font-family: 'Roboto', sans-serif; background: #ffffff; color: #000000; transition: all 0.3s; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #666; background: #f5f5f5; }
        textarea { resize: vertical; min-height: 100px; }
        .subreddit-chips { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
        .chip { background: #000000; color: #ffffff; padding: 8px 15px; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 1px; }
        .chip i { cursor: pointer; opacity: 0.7; transition: opacity 0.3s; }
        .chip i:hover { opacity: 1; }
        .btn { background: #000000; color: #ffffff; border: none; padding: 18px 40px; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.3s; text-transform: uppercase; letter-spacing: 2px; font-family: 'Roboto', sans-serif; }
        .btn:hover { background: #333; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .btn:disabled { background: #666; cursor: not-allowed; transform: none; }
        .btn i { margin-right: 10px; }
        .progress-container { background: #ffffff; padding: 30px; margin-bottom: 30px; display: none; }
        .progress-container.active { display: block; }
        .progress-bar { background: #e0e0e0; height: 40px; overflow: hidden; border: 2px solid #000000; }
        .progress-fill { background: #000000; height: 100%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: #ffffff; font-weight: 700; font-size: 14px; letter-spacing: 1px; }
        .progress-text { text-align: center; margin-top: 15px; color: #000000; font-weight: 500; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .tabs { background: #ffffff; overflow: hidden; box-shadow: 0 10px 40px rgba(255,255,255,0.1); display: none; }
        .tabs.active { display: block; }
        .tab-header { display: flex; background: #000000; flex-wrap: wrap; }
        .tab-btn { flex: 1; min-width: 150px; padding: 20px; background: none; border: none; font-weight: 700; color: #ffffff; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.3s; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-family: 'Roboto', sans-serif; }
        .tab-btn.active { background: #ffffff; color: #000000; border-bottom-color: #000000; }
        .tab-btn i { margin-right: 8px; }
        .tab-content { display: none; padding: 40px; max-height: 600px; overflow-y: auto; color: #000000; }
        .tab-content.active { display: block; }
        .article-content h1 { color: #000000; font-size: 36px; font-weight: 900; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #000000; text-transform: uppercase; letter-spacing: -1px; }
        .article-content h2 { color: #000000; font-size: 26px; font-weight: 700; margin: 35px 0 20px; padding-bottom: 10px; border-bottom: 2px solid #e0e0e0; text-transform: uppercase; letter-spacing: 1px; }
        .article-content p { line-height: 1.8; margin-bottom: 18px; color: #333; font-weight: 400; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px; margin-bottom: 35px; }
        .metric-card { background: #000000; color: #ffffff; padding: 30px; text-align: center; border: 2px solid #000000; }
        .metric-value { font-size: 42px; font-weight: 900; color: #ffffff; line-height: 1; }
        .metric-label { font-size: 11px; color: #ffffff; text-transform: uppercase; margin-top: 10px; font-weight: 700; letter-spacing: 1px; }
        .analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; margin-top: 25px; }
        .analysis-card { background: #f5f5f5; padding: 25px; border-left: 4px solid #000000; }
        .analysis-card h3 { color: #000000; margin-bottom: 18px; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
        .pain-point { background: #ffffff; padding: 12px; margin-bottom: 12px; font-size: 13px; border-left: 3px solid #000000; }
        .recommendation { background: #ffffff; padding: 18px; margin-bottom: 18px; border-left: 4px solid #000000; display: flex; justify-content: space-between; align-items: center; }
        .rec-tip { font-size: 14px; margin-bottom: 8px; font-weight: 500; color: #000000; }
        .rec-category { display: inline-block; background: #000000; color: #ffffff; padding: 4px 10px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
        .rec-impact { display: flex; gap: 3px; }
        .star { color: #000000; }
        .comparison-table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        .comparison-table th, .comparison-table td { padding: 15px; text-align: left; border-bottom: 2px solid #e0e0e0; }
        .comparison-table th { background: #000000; color: #ffffff; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }
        .comparison-table .advantage { color: #000000; font-weight: 700; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">WAQZEE</div>
        <div class="logo-subtitle">AI Content Platform</div>
    </div>
    
    <div class="container">
        <div class="input-section">
            <h2 class="section-title">CompellSEO</h2>
            <p>CompellSEO is an AI-powered content optimiSation tool that helps you create SEO-ready articles backed by real-time data. <BR>
It analySes top-ranking competitors, Reddit discussions, and Google NLP insights to show exactly what makes great content perform, then helps you write something better. <BR>

<BR> Get real-time SEO scores, entity coverage, and keyword optimization feedback as you write — just like SurferSEO, but smarter, faster, and uniquely tailored to your niche. <BR> </p>
            <br><br>
            
            <div class="input-grid">
                <div class="form-group">
                    <label>Main Keyword *</label>
                    <input type="text" id="mainKeyword" placeholder="e.g., car insurance UK" required>
                </div>
                <div class="form-group">
                    <label>Article Title *</label>
                    <input type="text" id="title" placeholder="e.g., Complete Guide to Car Insurance">
                </div>
                <div class="form-group">
                    <label>Secondary Keywords</label>
                    <input type="text" id="secondaryKeywords" placeholder="auto insurance, vehicle coverage">
                </div>
                <div class="form-group">
                    <label>Tone of Voice</label>
                    <select id="tone">
                        <option value="friendly">Friendly & Conversational</option>
                        <option value="professional">Professional & Expert</option>
                        <option value="bold">Bold & Persuasive</option>
                        <option value="emotional">Emotional & Empathetic</option>
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
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group full-width">
                <label>Subreddits to Search</label>
                <input type="text" id="subredditInput" placeholder="Enter subreddit and press Enter">
                <div class="subreddit-chips" id="subredditChips">
                    <span class="chip">r/askreddit <i class="fas fa-times" onclick="removeChip(this)"></i></span>
                    <span class="chip">r/technology <i class="fas fa-times" onclick="removeChip(this)"></i></span>
                </div>
            </div>
            
            <div class="form-group full-width">
                <label>Unique Insights (Optional)</label>
                <textarea id="uniqueInsights" placeholder="Share unique data or insights..."></textarea>
            </div>
            
            <button class="btn" id="generateBtn" onclick="generateContent()">
                <i class="fas fa-magic"></i> Generate SEO Article
            </button>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%">0%</div>
            </div>
            <div class="progress-text" id="progressText">Initializing...</div>
        </div>
        
        <div class="tabs" id="resultTabs">
            <div class="tab-header">
                <button class="tab-btn active" onclick="switchTab(event, 'article')">
                    <i class="fas fa-file-alt"></i> Article
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'metrics')">
                    <i class="fas fa-chart-line"></i> Metrics
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'nlp')">
                    <i class="fas fa-brain"></i> NLP Analysis
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'recommendations')">
                    <i class="fas fa-lightbulb"></i> Recommendations
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'competitors')">
                    <i class="fas fa-trophy"></i> Competitors
                </button>
            </div>
            
            <div class="tab-content active" id="articleTab">
                <div class="article-content" id="articleContent"></div>
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
                        <div class="metric-value" id="keywordDensity">0%</div>
                        <div class="metric-label">Keyword Density</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="readability">N/A</div>
                        <div class="metric-label">Readability</div>
                    </div>
                </div>
                
                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h3><i class="fab fa-reddit"></i> Reddit Pain Points</h3>
                        <div id="painPointsList"></div>
                    </div>
                    <div class="analysis-card">
                        <h3><i class="fab fa-google"></i> SERP Results</h3>
                        <div id="serpResultsList"></div>
                    </div>
                    <div class="analysis-card">
                        <h3><i class="fas fa-question-circle"></i> People Also Ask</h3>
                        <div id="paaList"></div>
                    </div>
                </div>
            </div>
            
            <div class="tab-content" id="nlpTab">
                <h3 style="margin-bottom: 20px;">NLP Analysis Results</h3>
                <div id="nlpResults"></div>
            </div>
            
            <div class="tab-content" id="recommendationsTab">
                <h3 style="margin-bottom: 25px;">SEO Recommendations</h3>
                <div id="recommendationsList"></div>
            </div>
            
            <div class="tab-content" id="competitorsTab">
                <h3 style="margin-bottom: 25px;">Competitor Analysis</h3>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>Competitors</th>
                            <th>Your Article</th>
                            <th>Advantage</th>
                        </tr>
                    </thead>
                    <tbody id="comparisonTable"></tbody>
                </table>
                <div style="margin-top: 35px; padding: 25px; background: #f5f5f5; border-left: 4px solid #000000;">
                    <h4 style="margin-bottom: 12px; font-weight: 700;">Summary</h4>
                    <p id="comparisonSummary" style="white-space: pre-line;"></p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let subreddits = ['askreddit', 'technology'];
        let progressInterval;
        
        document.getElementById('subredditInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const value = this.value.trim().replace('r/', '');
                if (value && !subreddits.includes(value)) {
                    subreddits.push(value);
                    updateChips();
                    this.value = '';
                }
            }
        });
        
        function removeChip(el) {
            const chip = el.parentElement;
            const sub = chip.textContent.replace('r/', '').trim();
            subreddits = subreddits.filter(s => s !== sub);
            chip.remove();
        }
        
        function updateChips() {
            document.getElementById('subredditChips').innerHTML = 
                subreddits.map(s => `<span class="chip">r/${s} <i class="fas fa-times" onclick="removeChip(this)"></i></span>`).join('');
        }
        
        function switchTab(event, tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
        }
        
        async function generateContent() {
            const mainKeyword = document.getElementById('mainKeyword').value.trim();
            const title = document.getElementById('title').value.trim();
            if (!mainKeyword || !title) { alert('Please enter keyword and title'); return; }
            
            document.getElementById('progressContainer').classList.add('active');
            document.getElementById('generateBtn').disabled = true;
            
            const data = {
                main_keyword: mainKeyword,
                title: title,
                secondary_keywords: document.getElementById('secondaryKeywords').value.split(',').map(k => k.trim()).filter(k => k),
                tone: document.getElementById('tone').value,
                target_country: document.getElementById('targetCountry').value,
                language: document.getElementById('language').value,
                unique_insights: document.getElementById('uniqueInsights').value,
                subreddits: subreddits
            };
            
            try {
                startProgress();
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
                alert('Failed to generate content');
            } finally {
                stopProgress();
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('progressContainer').classList.remove('active');
            }
        }
        
        function startProgress() {
            progressInterval = setInterval(async () => {
                try {
                    const res = await fetch('/progress');
                    const data = await res.json();
                    if (data.length > 0) {
                        const latest = data[data.length - 1];
                        updateProgress(latest.percentage, latest.message);
                    }
                } catch (e) { }
            }, 1000);
        }
        
        function stopProgress() {
            if (progressInterval) clearInterval(progressInterval);
            updateProgress(100, 'Complete!');
        }
        
        function updateProgress(pct, text) {
            document.getElementById('progressFill').style.width = pct + '%';
            document.getElementById('progressFill').textContent = pct + '%';
            document.getElementById('progressText').textContent = text;
        }
        
        function displayResults(data) {
            document.getElementById('articleContent').innerHTML = data.article.content;
            document.getElementById('wordCount').textContent = data.metrics.word_count;
            document.getElementById('seoScore').textContent = data.metrics.seo_score;
            document.getElementById('keywordDensity').textContent = data.metrics.keyword_density + '%';
            document.getElementById('readability').textContent = data.metrics.readability;
            
            document.getElementById('painPointsList').innerHTML = data.reddit_pain_points.map(p => 
                `<div class="pain-point">${p.pain || p}</div>`
            ).join('');
            
            document.getElementById('serpResultsList').innerHTML = data.serp_summary.top_results.map(r => 
                `<div class="pain-point"><strong>${r.title}</strong></div>`
            ).join('');
            
            document.getElementById('paaList').innerHTML = data.serp_summary.people_also_ask.map(q => 
                `<div class="pain-point">${q.question}</div>`
            ).join('');
            
            let nlpHtml = '<p>NLP analysis complete</p>';
            if (data.article_nlp && data.article_nlp.nlp_available) {
                nlpHtml = `<h4>Article Entities:</h4><ul>` + 
                    data.article_nlp.article_entities.slice(0,10).map(e => `<li>${e.name} (${e.type})</li>`).join('') +
                    `</ul>`;
                if (data.article_nlp.entity_coverage) {
                    nlpHtml += `<h4 style="margin-top:20px;">Entity Coverage: ${data.article_nlp.entity_coverage.grade} (${data.article_nlp.entity_coverage.coverage_percentage}%)</h4>`;
                }
            }
            document.getElementById('nlpResults').innerHTML = nlpHtml;
            
            document.getElementById('recommendationsList').innerHTML = data.recommendations.map(r => 
                `<div class="recommendation">
                    <div>
                        <div class="rec-tip">${r.tip}</div>
                        <span class="rec-category">${r.category}</span>
                    </div>
                    <div class="rec-impact">${'<i class="fas fa-star star"></i>'.repeat(r.impact)}</div>
                </div>`
            ).join('');
            
            document.getElementById('comparisonTable').innerHTML = data.competitor_comparison.features.map(f => 
                `<tr>
                    <td style="font-weight:700;">${f.feature}</td>
                    <td>${f.competitors}</td>
                    <td class="${f.advantage ? 'advantage' : ''}">${f.you}</td>
                    <td style="text-align:center; font-size:18px;">${f.advantage ? '✓' : '—'}</td>
                </tr>`
            ).join('');
            document.getElementById('comparisonSummary').textContent = data.competitor_comparison.summary;
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
    """Generate complete SEO article"""
    global progress_updates
    progress_updates = []
    
    try:
        params = request.get_json()
        logger.info(f"📥 Request for: {params.get('main_keyword')}")
        
        # Initialize OpenAI
        openai_client = OpenAIClient()
        if not openai_client.available:
            return jsonify({"error": "OpenAI API not configured. Set OPENAI_API_KEY in Railway."}), 500
        
        # 1. Reddit Analysis
        reddit_data = analyze_reddit(params['main_keyword'], params.get('subreddits', ['askreddit']))
        
        # 2. SERP Analysis
        serp_data = analyze_serp(params['main_keyword'], 5)
        
        # 3. Competitor NLP (if available)
        competitor_nlp = analyze_competitor_nlp(serp_data)
        
        # 4. Generate Content
        article_data = generate_content(params, reddit_data, serp_data, competitor_nlp, openai_client)
        
        # 5. Article NLP (if available)
        article_nlp = analyze_article_nlp(article_data['content'], competitor_nlp)
        
        # 6. Calculate Metrics
        metrics = calculate_metrics(article_data['content'], params)
        
        # 7. Recommendations
        recommendations = generate_recommendations(metrics, params, article_nlp)
        
        # 8. Competitor Comparison
        competitor_comparison = generate_competitor_comparison(metrics, serp_data, reddit_data, article_nlp)
        
        add_progress("✅ Complete!", 100)
        
        result = {
            "inputs": params,
            "reddit_pain_points": reddit_data['pain_points'],
            "serp_summary": {
                "top_results": serp_data['top_results'],
                "people_also_ask": serp_data['people_also_ask']
            },
            "article": {"content": article_data['content']},
            "metrics": metrics,
            "article_nlp": article_nlp,
            "recommendations": recommendations,
            "competitor_comparison": competitor_comparison
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
