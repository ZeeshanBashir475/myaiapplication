import re
import json
import os
import sys
import logging
import traceback
import asyncio
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
import requests
import time
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add agents directory to path
agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'agents')
if os.path.exists(agents_path):
    if agents_path not in sys.path:
        sys.path.insert(0, agents_path)

# Import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI imported successfully")
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("❌ OpenAI not available")

# Import agents
RedditScraper = None
PainPointExtractor = None
SerpAgent = None

try:
    from Reddit_scraper import RedditScraper
    logger.info("✅ RedditScraper imported")
except Exception as e:
    logger.error(f"❌ Failed to import RedditScraper: {e}")

try:
    from Pain_point_extractor import PainPointExtractor
    logger.info("✅ PainPointExtractor imported")
except Exception as e:
    logger.error(f"❌ Failed to import PainPointExtractor: {e}")

try:
    from Serp_agent import SerpAgent
    logger.info("✅ SerpAgent imported")
except Exception as e:
    logger.error(f"❌ Failed to import SerpAgent: {e}")

app = Flask(__name__)
CORS(app)

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=3)

# Global progress tracking
progress_updates = []

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
    """Enhanced OpenAI client"""
    
    def __init__(self):
        # Check both possible env variable names
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('Open_Api_Key')
        self.available = False
        
        if not OPENAI_AVAILABLE:
            logger.warning("⚠️ OpenAI package not available")
            return
            
        if not self.api_key:
            logger.warning("⚠️ No OpenAI API key found in environment variables")
            logger.info("Checked: OPENAI_API_KEY and Open_Api_Key")
            return
        
        try:
            # Minimal OpenAI client - ONLY api_key
            logger.info(f"Creating OpenAI client...")
            logger.info(f"API Key found: {self.api_key[:15]}...")
            
            # Try creating client with minimal parameters
            self.client = openai.OpenAI(api_key=self.api_key)
            
            # Test the client
            logger.info("Testing OpenAI client...")
            test_response = self.client.models.list()
            logger.info(f"✅ OpenAI client test successful - found {len(test_response.data)} models")
            
            self.available = True
            logger.info("✅ OpenAI client initialized and tested successfully")
            
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
    
    def generate_seo_article(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate SEO-optimized article (synchronous)"""
        if not self.available:
            error_msg = "<h1>Content Generation Unavailable</h1><p>OpenAI API key not configured. Please check your Railway environment variables.</p>"
            logger.error("Cannot generate content - OpenAI not available")
            return error_msg
        
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
            logger.info(f"✅ Generated content ({len(content)} characters)")
            return content
        except openai.APIError as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return f"<p>OpenAI API Error: {str(e)}</p>"
        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
            logger.error(traceback.format_exc())
            return f"<p>Error generating content: {str(e)}</p>"

def run_async(coro):
    """Helper to run async functions synchronously"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def analyze_reddit(topic: str, subreddits: List[str]) -> Dict:
    """Analyze Reddit discussions (synchronous wrapper)"""
    add_progress("🔍 Searching Reddit discussions...", 10)
    
    pain_points = []
    discussions = []
    
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
            for subreddit in subreddits[:3]:
                try:
                    logger.info(f"Scraping r/{subreddit}...")
                    data = scraper.scrape_for_pain_points(subreddit, topic, 10)
                    
                    # Extract pain points from the data
                    for post in data.get('posts', [])[:5]:
                        title = post.get('title', '')
                        text = post.get('selftext', '')
                        combined_text = (title + ' ' + text).lower()
                        
                        # Look for pain point indicators
                        if any(word in combined_text for word in ['problem', 'issue', 'help', 'struggling', 'frustrated', 'confused', 'difficult']):
                            pain_points.append({
                                'pain': title[:150] if title else "General discussion",
                                'subreddit': f"r/{subreddit}",
                                'score': post.get('score', 0)
                            })
                        
                        discussions.append({
                            'title': title,
                            'subreddit': f"r/{subreddit}",
                            'url': post.get('permalink', ''),
                            'score': post.get('score', 0)
                        })
                except Exception as e:
                    logger.error(f"Error scraping r/{subreddit}: {e}")
                    continue
            
            add_progress(f"✓ Found {len(pain_points)} pain points from Reddit", 20)
        except Exception as e:
            logger.error(f"Reddit analysis error: {e}")
            logger.error(traceback.format_exc())
    
    # Fallback if no pain points found
    if not pain_points:
        pain_points = [
            {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100},
            {'pain': f"Understanding best practices for {topic}", 'subreddit': "general", 'score': 85},
            {'pain': f"Getting started with {topic}", 'subreddit': "general", 'score': 75}
        ]
    
    return {
        'pain_points': pain_points[:10],
        'discussions': discussions[:5],
        'summary': f"Analyzed {len(subreddits)} subreddits, found {len(pain_points)} pain points"
    }

def analyze_serp(keyword: str) -> Dict:
    """Analyze SERP results (synchronous)"""
    add_progress("🌐 Analyzing Google search results...", 30)
    
    if not SerpAgent:
        logger.warning("SERP agent not available - using fallback")
        return get_fallback_serp_data(keyword)
    
    try:
        agent = SerpAgent()
        analysis = agent.analyze_keyword(keyword, location="United Kingdom")
        
        add_progress(f"✓ Analyzed top {len(analysis['organic_results'])} search results", 40)
        
        return {
            'top_results': analysis['organic_results'][:5],
            'people_also_ask': analysis['people_also_ask'][:5],
            'related_keywords': analysis['related_searches'][:5],
            'opportunities': analysis['content_opportunities'][:5]
        }
    except Exception as e:
        logger.error(f"SERP analysis error: {e}")
        logger.error(traceback.format_exc())
        return get_fallback_serp_data(keyword)

def get_fallback_serp_data(keyword: str) -> Dict:
    """Fallback SERP data"""
    return {
        'top_results': [
            {'title': f"Complete Guide to {keyword}", 'link': '#', 'snippet': 'Comprehensive guide covering all aspects...', 'position': 1},
            {'title': f"Best {keyword} in 2024", 'link': '#', 'snippet': 'Top recommendations and reviews...', 'position': 2},
            {'title': f"How to Use {keyword}", 'link': '#', 'snippet': 'Step-by-step tutorial...', 'position': 3}
        ],
        'people_also_ask': [
            {'question': f"What is {keyword}?", 'snippet': 'Definition and overview...'},
            {'question': f"How does {keyword} work?", 'snippet': 'Explanation of functionality...'},
            {'question': f"Is {keyword} worth it?", 'snippet': 'Value analysis...'}
        ],
        'related_keywords': [f"{keyword} guide", f"best {keyword}", f"{keyword} tips"],
        'opportunities': [
            'Add detailed comparison tables',
            'Include FAQ section',
            'Add visual guides and infographics',
            'Include real user testimonials',
            'Add 2024 updates and trends'
        ]
    }

def generate_seo_content(inputs: Dict, reddit_data: Dict, serp_data: Dict, openai_client: OpenAIClient) -> Dict:
    """Generate SEO content (synchronous)"""
    add_progress("✍️ Generating SEO-optimized article...", 50)
    
    # Build comprehensive prompt
    pain_points_text = '\n'.join([f"- {p.get('pain', '')}" for p in reddit_data['pain_points'][:5]])
    paa_text = '\n'.join([f"- {q['question']}" for q in serp_data['people_also_ask'][:5]])
    opportunities_text = '\n'.join([f"- {o}" for o in serp_data['opportunities'][:3]])
    
    prompt = f"""
Create a comprehensive, SEO-optimized article about "{inputs['main_keyword']}"

Title: {inputs.get('title', inputs['main_keyword'])}
Tone: {inputs.get('tone', 'Professional yet friendly')}
Target Audience: {inputs.get('target_country', 'United Kingdom')}

REDDIT PAIN POINTS TO ADDRESS:
{pain_points_text}

PEOPLE ALSO ASK (Include in FAQ):
{paa_text}

CONTENT OPPORTUNITIES:
{opportunities_text}

USER'S UNIQUE INSIGHTS:
{inputs.get('unique_insights', 'No additional insights provided')}

REQUIREMENTS:
1. Write 2,400-3,600 words
2. Use proper HTML formatting (h1, h2, h3, p, ul, li, strong)
3. Include an emotional hook in the introduction that addresses real user pain points
4. Address each pain point naturally throughout the content
5. Include a comprehensive FAQ section answering the PAA questions
6. Use the main keyword "{inputs['main_keyword']}" 5-8 times naturally
7. Include secondary keywords: {', '.join(inputs.get('secondary_keywords', [])[:3])}
8. End with a strong call-to-action
9. Include comparison tables or lists where appropriate
10. Add section for 2024 updates and latest trends

FORMAT THE ARTICLE WITH:
- <h1> for the main title only
- <h2> for major sections
- <h3> for subsections
- <p> for paragraphs with good spacing
- <ul> and <li> for lists
- <strong> for key emphasis
- <blockquote> for important quotes or statistics

Make the content engaging, scannable, and optimized for both search engines and users.

Write the complete article now:
"""
    
    try:
        article = openai_client.generate_seo_article(prompt)
        
        # Calculate metrics
        word_count = len(article.split())
        keyword_density = (article.lower().count(inputs['main_keyword'].lower()) / word_count) * 100 if word_count > 0 else 0
        
        add_progress("✓ Article generated successfully", 70)
        
        return {
            'content': article,
            'word_count': word_count,
            'keyword_density': round(keyword_density, 2),
            'readability_score': calculate_readability(article),
            'seo_score': calculate_seo_score(article, inputs, serp_data)
        }
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        logger.error(traceback.format_exc())
        return {
            'content': f"<h1>Error Generating Content</h1><p>Failed to generate article: {str(e)}</p><p>Please check your OpenAI API configuration.</p>",
            'word_count': 0,
            'keyword_density': 0,
            'readability_score': 'N/A',
            'seo_score': 0
        }

def calculate_readability(text: str) -> str:
    """Calculate readability score"""
    sentences = len(re.split(r'[.!?]+', text))
    words = len(text.split())
    if sentences == 0:
        return "N/A"
    avg_words_per_sentence = words / sentences
    
    if avg_words_per_sentence < 15:
        return "Easy"
    elif avg_words_per_sentence < 20:
        return "Medium"
    else:
        return "Advanced"

def calculate_seo_score(content: str, inputs: Dict, serp_data: Dict) -> int:
    """Calculate SEO score (0-100)"""
    score = 50  # Base score
    
    if '<h1>' in content: score += 10
    if '<h2>' in content: score += 10
    if inputs['main_keyword'].lower() in content.lower(): score += 10
    if any(kw.lower() in content.lower() for kw in inputs.get('secondary_keywords', [])): score += 10
    if len(content.split()) > 2000: score += 10
    
    return min(100, score)

def generate_recommendations(article_data: Dict, inputs: Dict, serp_data: Dict) -> List[Dict]:
    """Generate SEO recommendations"""
    add_progress("📊 Generating SEO recommendations...", 80)
    
    recommendations = []
    
    # Keyword recommendations
    if article_data['keyword_density'] < 1:
        recommendations.append({
            'tip': f"Increase '{inputs['main_keyword']}' usage to 1-2% density",
            'impact': 5,
            'category': 'SEO'
        })
    elif article_data['keyword_density'] > 3:
        recommendations.append({
            'tip': f"Reduce keyword density from {article_data['keyword_density']}%",
            'impact': 4,
            'category': 'SEO'
        })
    
    if article_data['word_count'] < 2400:
        recommendations.append({
            'tip': f"Expand to 2,400+ words (current: {article_data['word_count']})",
            'impact': 5,
            'category': 'Content'
        })
    
    recommendations.extend([
        {'tip': "Add personal story in intro for emotional connection", 'impact': 4, 'category': 'Engagement'},
        {'tip': "Include schema markup for FAQ section", 'impact': 3, 'category': 'Technical SEO'},
        {'tip': "Add 3-5 optimized images with alt text", 'impact': 3, 'category': 'UX'},
        {'tip': "Add 2-3 internal links to related content", 'impact': 3, 'category': 'SEO'},
        {'tip': "Place mid-article CTA after main pain point", 'impact': 4, 'category': 'Conversion'}
    ])
    
    return recommendations[:8]

def generate_competitor_comparison(article_data: Dict, serp_data: Dict, reddit_data: Dict) -> Dict:
    """Generate competitor comparison"""
    add_progress("🏆 Analyzing competitor comparison...", 90)
    
    comparison = {
        'features': [
            {
                'feature': 'Word Count',
                'competitors': '1,500-2,000 avg',
                'you': f"{article_data['word_count']} words",
                'advantage': article_data['word_count'] > 2000
            },
            {
                'feature': 'Emotional Engagement',
                'competitors': 'Generic content',
                'you': f"Uses {len(reddit_data['pain_points'])} real pain points",
                'advantage': True
            },
            {
                'feature': 'Keyword Optimization',
                'competitors': 'Basic optimization',
                'you': f"{article_data['keyword_density']}% density + LSI keywords",
                'advantage': True
            },
            {
                'feature': 'Unique Insights',
                'competitors': 'Rehashed info',
                'you': 'Reddit insights + user data',
                'advantage': True
            },
            {
                'feature': 'Content Structure',
                'competitors': 'Standard blog',
                'you': 'FAQ + Tables + Examples',
                'advantage': True
            },
            {
                'feature': 'Readability',
                'competitors': 'Variable',
                'you': article_data.get('readability_score', 'Optimized'),
                'advantage': True
            }
        ],
        'summary': f"""Your article outperforms competitors by:
• Integrating {len(reddit_data['pain_points'])} real user pain points from Reddit
• Providing {article_data['word_count']} words of comprehensive coverage
• Achieving {article_data.get('seo_score', 80)}% SEO optimisation score
• Addressing gaps in top {len(serp_data['top_results'])} SERP results
• Including unique insights not found in competitor content"""
    }
    
    return comparison

# HTML Template with Waqzee Black/White Theme
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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Roboto', sans-serif;
            background: #000000;
            color: #ffffff;
            min-height: 100vh;
            line-height: 1.6;
        }
        
        /* Header */
        .header {
            background: #ffffff;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-size: 32px;
            font-weight: 900;
            color: #000000;
            letter-spacing: -1px;
        }
        
        .logo-subtitle {
            font-size: 12px;
            font-weight: 400;
            color: #666;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        
        /* Container */
        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        /* Input Section */
        .input-section {
            background: #ffffff;
            color: #000000;
            border-radius: 0;
            padding: 40px;
            margin-bottom: 40px;
            box-shadow: 0 10px 40px rgba(255,255,255,0.1);
        }
        
        .section-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 30px;
            color: #000000;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .input-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 25px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        label {
            font-size: 11px;
            font-weight: 700;
            color: #000000;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        input, select, textarea {
            padding: 12px 15px;
            border: 2px solid #000000;
            border-radius: 0;
            font-size: 14px;
            font-family: 'Roboto', sans-serif;
            background: #ffffff;
            color: #000000;
            transition: all 0.3s;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #666;
            background: #f5f5f5;
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .subreddit-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 12px;
        }
        
        .chip {
            background: #000000;
            color: #ffffff;
            padding: 8px 15px;
            border-radius: 0;
            font-size: 12px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .chip i {
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.3s;
        }
        
        .chip i:hover {
            opacity: 1;
        }
        
        .btn {
            background: #000000;
            color: #ffffff;
            border: none;
            padding: 18px 40px;
            border-radius: 0;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-family: 'Roboto', sans-serif;
        }
        
        .btn:hover {
            background: #333;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .btn:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn i {
            margin-right: 10px;
        }
        
        /* Progress Bar */
        .progress-container {
            background: #ffffff;
            padding: 30px;
            border-radius: 0;
            margin-bottom: 30px;
            display: none;
        }
        
        .progress-container.active {
            display: block;
        }
        
        .progress-bar {
            background: #e0e0e0;
            height: 40px;
            border-radius: 0;
            overflow: hidden;
            border: 2px solid #000000;
        }
        
        .progress-fill {
            background: #000000;
            height: 100%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 1px;
        }
        
        .progress-text {
            text-align: center;
            margin-top: 15px;
            color: #000000;
            font-weight: 500;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Tabs */
        .tabs {
            background: #ffffff;
            border-radius: 0;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(255,255,255,0.1);
            display: none;
        }
        
        .tabs.active {
            display: block;
        }
        
        .tab-header {
            display: flex;
            background: #000000;
            flex-wrap: wrap;
        }
        
        .tab-btn {
            flex: 1;
            min-width: 150px;
            padding: 20px;
            background: none;
            border: none;
            font-weight: 700;
            color: #ffffff;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-family: 'Roboto', sans-serif;
        }
        
        .tab-btn.active {
            background: #ffffff;
            color: #000000;
            border-bottom-color: #000000;
        }
        
        .tab-btn i {
            margin-right: 8px;
        }
        
        .tab-content {
            display: none;
            padding: 40px;
            max-height: 600px;
            overflow-y: auto;
            color: #000000;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Article Content */
        .article-content h1 {
            color: #000000;
            font-size: 36px;
            font-weight: 900;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #000000;
            text-transform: uppercase;
            letter-spacing: -1px;
        }
        
        .article-content h2 {
            color: #000000;
            font-size: 26px;
            font-weight: 700;
            margin: 35px 0 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .article-content h3 {
            color: #333;
            font-size: 20px;
            font-weight: 700;
            margin: 28px 0 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .article-content p {
            line-height: 1.8;
            margin-bottom: 18px;
            color: #333;
            font-weight: 400;
        }
        
        .article-content ul, .article-content ol {
            margin: 18px 0;
            padding-left: 35px;
        }
        
        .article-content li {
            margin-bottom: 10px;
            line-height: 1.7;
        }
        
        /* Metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            margin-bottom: 35px;
        }
        
        .metric-card {
            background: #000000;
            color: #ffffff;
            padding: 30px;
            border-radius: 0;
            text-align: center;
            border: 2px solid #000000;
        }
        
        .metric-value {
            font-size: 42px;
            font-weight: 900;
            color: #ffffff;
            line-height: 1;
        }
        
        .metric-label {
            font-size: 11px;
            color: #ffffff;
            text-transform: uppercase;
            margin-top: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        
        /* Analysis Cards */
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 25px;
            margin-top: 25px;
        }
        
        .analysis-card {
            background: #f5f5f5;
            padding: 25px;
            border-radius: 0;
            border-left: 4px solid #000000;
        }
        
        .analysis-card h3 {
            color: #000000;
            margin-bottom: 18px;
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .pain-point, .serp-result {
            background: #ffffff;
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 0;
            font-size: 13px;
            border-left: 3px solid #000000;
        }
        
        /* Recommendations */
        .recommendation {
            background: #ffffff;
            padding: 18px;
            margin-bottom: 18px;
            border-radius: 0;
            border-left: 4px solid #000000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .rec-content {
            flex: 1;
        }
        
        .rec-tip {
            font-size: 14px;
            margin-bottom: 8px;
            font-weight: 500;
            color: #000000;
        }
        
        .rec-category {
            display: inline-block;
            background: #000000;
            color: #ffffff;
            padding: 4px 10px;
            border-radius: 0;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .rec-impact {
            display: flex;
            gap: 3px;
        }
        
        .star {
            color: #000000;
        }
        
        /* Competitor Table */
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 25px;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .comparison-table th {
            background: #000000;
            color: #ffffff;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1px;
        }
        
        .comparison-table .advantage {
            color: #000000;
            font-weight: 700;
        }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .header {
                padding: 15px 20px;
            }
            
            .logo {
                font-size: 24px;
            }
            
            .input-section {
                padding: 25px 20px;
            }
            
            .section-title {
                font-size: 22px;
            }
            
            .input-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .tab-header {
                flex-direction: column;
            }
            
            .tab-btn {
                border-left: 3px solid transparent;
                border-bottom: none;
            }
            
            .tab-btn.active {
                border-left-color: #000000;
            }
            
            .article-content h1 {
                font-size: 28px;
            }
            
            .article-content h2 {
                font-size: 22px;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .analysis-grid {
                grid-template-columns: 1fr;
            }
            
            .comparison-table {
                font-size: 12px;
            }
            
            .comparison-table th,
            .comparison-table td {
                padding: 10px;
            }
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #000000;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #333;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">WAQZEE</div>
        <div class="logo-subtitle">AI Content Platform</div>
    </div>
    
    <div class="container">
        <!-- Input Section -->
        <div class="input-section">
            <h2 class="section-title">CompellSEO</h2>
            <p> CompellSEO is an AI-powered content generator that creates compelling, keyword-optimised articles tailored to your audience’s pain points and tone of voice. It analyses SERPs and competitors, helping you craft content that not only ranks higher but also connects with readers on a human level.</p>
<br> <br>            
            <div class="input-grid">
                <div class="form-group">
                    <label>Main Keyword *</label>
                    <input type="text" id="mainKeyword" placeholder="e.g., eco-friendly detergent" required>
                </div>
                
                <div class="form-group">
                    <label>Article Title *</label>
                    <input type="text" id="title" placeholder="e.g., The Ultimate Guide to Eco-Friendly Detergents">
                </div>
                
                <div class="form-group">
                    <label>Secondary Keywords</label>
                    <input type="text" id="secondaryKeywords" placeholder="biodegradable soap, green cleaning">
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
                        <option value="Global">Global</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Language</label>
                    <select id="language">
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label>Subreddits to Search</label>
                <input type="text" id="subredditInput" placeholder="Enter subreddit name and press Enter">
                <div class="subreddit-chips" id="subredditChips">
                    <span class="chip">r/askreddit <i class="fas fa-times" onclick="removeChip(this)"></i></span>
                    <span class="chip">r/technology <i class="fas fa-times" onclick="removeChip(this)"></i></span>
                </div>
            </div>
            
            <div class="form-group" style="margin-top: 25px;">
                <label>Unique Insights (Optional)</label>
                <textarea id="uniqueInsights" placeholder="Share any unique data, stories, or insights that could make your content stand out..."></textarea>
            </div>
            
            <button class="btn" id="generateBtn" onclick="generateContent()" style="margin-top: 30px;">
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
                    <i class="fas fa-chart-line"></i> Metrics
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'recommendations')">
                    <i class="fas fa-lightbulb"></i> Recommendations
                </button>
                <button class="tab-btn" onclick="switchTab(event, 'competitors')">
                    <i class="fas fa-trophy"></i> Competitors
                </button>
            </div>
            
            <!-- Article Tab -->
            <div class="tab-content active" id="articleTab">
                <div class="article-content" id="articleContent"></div>
            </div>
            
            <!-- Metrics Tab -->
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
                        <h3><i class="fab fa-google"></i> SERP Analysis</h3>
                        <div id="serpResultsList"></div>
                    </div>
                    <div class="analysis-card">
                        <h3><i class="fas fa-question-circle"></i> People Also Ask</h3>
                        <div id="paaList"></div>
                    </div>
                </div>
            </div>
            
            <!-- Recommendations Tab -->
            <div class="tab-content" id="recommendationsTab">
                <h3 style="margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px;">SEO Improvement Recommendations</h3>
                <div id="recommendationsList"></div>
            </div>
            
            <!-- Competitors Tab -->
            <div class="tab-content" id="competitorsTab">
                <h3 style="margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px;">Competitor Analysis</h3>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>Top Competitors</th>
                            <th>Your Article</th>
                            <th>Advantage</th>
                        </tr>
                    </thead>
                    <tbody id="comparisonTable"></tbody>
                </table>
                <div style="margin-top: 35px; padding: 25px; background: #f5f5f5; border-radius: 0; border-left: 4px solid #000000;">
                    <h4 style="margin-bottom: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Summary</h4>
                    <p id="comparisonSummary" style="white-space: pre-line;"></p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let subreddits = ['askreddit', 'technology'];
        let progressInterval;
        
        // Handle Enter key for subreddit input
        document.getElementById('subredditInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addSubreddit();
            }
        });
        
        function addSubreddit() {
            const input = document.getElementById('subredditInput');
            const value = input.value.trim().replace('r/', '').replace('/r/', '');
            
            if (value && !subreddits.includes(value)) {
                subreddits.push(value);
                updateSubredditChips();
                input.value = '';
            }
        }
        
        function removeChip(element) {
            const chip = element.parentElement;
            const subreddit = chip.textContent.replace('r/', '').trim();
            subreddits = subreddits.filter(s => s !== subreddit);
            chip.remove();
        }
        
        function updateSubredditChips() {
            const container = document.getElementById('subredditChips');
            container.innerHTML = subreddits.map(s => 
                `<span class="chip">r/${s} <i class="fas fa-times" onclick="removeChip(this)"></i></span>`
            ).join('');
        }
        
        function switchTab(event, tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName + 'Tab').classList.add('active');
        }
        
        async function generateContent() {
            const mainKeyword = document.getElementById('mainKeyword').value.trim();
            const title = document.getElementById('title').value.trim();
            
            if (!mainKeyword || !title) {
                alert('Please enter both main keyword and title');
                return;
            }
            
            // Show progress
            document.getElementById('progressContainer').classList.add('active');
            document.getElementById('generateBtn').disabled = true;
            
            // Prepare data
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
                // Start progress updates
                startProgressUpdates();
                
                const response = await fetch('/generate-seo-article', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.error) {
                    alert('Error: ' + result.error);
                    return;
                }
                
                // Display results
                displayResults(result);
                
                // Show tabs
                document.getElementById('resultTabs').classList.add('active');
                
                // Scroll to results
                document.getElementById('resultTabs').scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate content. Please try again.');
            } finally {
                stopProgressUpdates();
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('progressContainer').classList.remove('active');
            }
        }
        
        function startProgressUpdates() {
            let progress = 0;
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch('/progress');
                    const data = await response.json();
                    
                    if (data.length > 0) {
                        const latest = data[data.length - 1];
                        updateProgress(latest.percentage, latest.message);
                    }
                } catch (e) {
                    console.error('Progress update error:', e);
                }
            }, 1000);
        }
        
        function stopProgressUpdates() {
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            updateProgress(100, 'Complete!');
        }
        
        function updateProgress(percentage, text) {
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressFill').textContent = percentage + '%';
            document.getElementById('progressText').textContent = text;
        }
        
        function displayResults(data) {
            // Display article
            document.getElementById('articleContent').innerHTML = data.article.content || '<p>No content generated</p>';
            
            // Display metrics
            document.getElementById('wordCount').textContent = data.metrics.word_count || 0;
            document.getElementById('seoScore').textContent = data.metrics.seo_score || 0;
            document.getElementById('keywordDensity').textContent = (data.metrics.keyword_density || 0) + '%';
            document.getElementById('readability').textContent = data.metrics.readability || 'N/A';
            
            // Display Reddit pain points
            const painPointsHtml = data.reddit_pain_points.slice(0, 10).map(p => 
                `<div class="pain-point">${p.pain || p}</div>`
            ).join('');
            document.getElementById('painPointsList').innerHTML = painPointsHtml || '<p>No pain points found</p>';
            
            // Display SERP results
            const serpHtml = data.serp_summary.top_results.map(r => 
                `<div class="serp-result">
                    <div style="font-weight: 700; margin-bottom: 5px;">${r.title}</div>
                    <div style="font-size: 11px; color: #666;">${r.link}</div>
                </div>`
            ).join('');
            document.getElementById('serpResultsList').innerHTML = serpHtml || '<p>No SERP results</p>';
            
            // Display People Also Ask
            const paaHtml = data.serp_summary.people_also_ask.map(q => 
                `<div class="serp-result">${q.question}</div>`
            ).join('');
            document.getElementById('paaList').innerHTML = paaHtml || '<p>No questions found</p>';
            
            // Display recommendations
            const recHtml = data.recommendations.map(r => 
                `<div class="recommendation">
                    <div class="rec-content">
                        <div class="rec-tip">${r.tip}</div>
                        <span class="rec-category">${r.category}</span>
                    </div>
                    <div class="rec-impact">
                        ${Array(r.impact).fill('<i class="fas fa-star star"></i>').join('')}
                    </div>
                </div>`
            ).join('');
            document.getElementById('recommendationsList').innerHTML = recHtml || '<p>No recommendations</p>';
            
            // Display competitor comparison
            const comparisonHtml = data.competitor_comparison.features.map(f => 
                `<tr>
                    <td style="font-weight: 700;">${f.feature}</td>
                    <td>${f.competitors}</td>
                    <td class="${f.advantage ? 'advantage' : ''}">${f.you}</td>
                    <td style="text-align: center; font-size: 18px;">${f.advantage ? '✓' : '—'}</td>
                </tr>`
            ).join('');
            document.getElementById('comparisonTable').innerHTML = comparisonHtml;
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
    """Generate complete SEO article with all analysis"""
    global progress_updates
    progress_updates = []  # Reset progress
    
    try:
        data = request.get_json()
        logger.info(f"📥 Received request for keyword: {data.get('main_keyword')}")
        
        # Initialize OpenAI with detailed logging
        logger.info("🔧 Initializing OpenAI client...")
        openai_client = OpenAIClient()
        logger.info(f"🔧 OpenAI client available: {openai_client.available}")
        
        if not openai_client.available:
            error_msg = "OpenAI API not configured. Please set the OPENAI_API_KEY or Open_Api_Key environment variable in Railway."
            logger.error(f"❌ {error_msg}")
            return jsonify({"error": error_msg}), 500
        
        logger.info("✅ OpenAI client initialized successfully")
        
        # 1. Reddit Analysis
        add_progress("Starting Reddit analysis...", 5)
        reddit_data = analyze_reddit(
            data['main_keyword'],
            data.get('subreddits', ['askreddit', 'technology'])
        )
        
        # 2. SERP Analysis
        add_progress("Starting SERP analysis...", 25)
        serp_data = analyze_serp(data['main_keyword'])
        
        # 3. Generate Article
        add_progress("Generating article...", 45)
        article_data = generate_seo_content(data, reddit_data, serp_data, openai_client)
        
        # 4. Generate Recommendations
        add_progress("Generating recommendations...", 75)
        recommendations = generate_recommendations(article_data, data, serp_data)
        
        # 5. Competitor Analysis
        add_progress("Analyzing competitors...", 85)
        competitor_comparison = generate_competitor_comparison(
            article_data, serp_data, reddit_data
        )
        
        add_progress("✅ Generation complete!", 100)
        
        result = {
            "inputs": data,
            "reddit_pain_points": reddit_data['pain_points'],
            "serp_summary": {
                "top_results": serp_data['top_results'],
                "people_also_ask": serp_data['people_also_ask'],
                "opportunities": serp_data['opportunities']
            },
            "article": {
                "content": article_data['content'],
                "meta_description": f"Comprehensive guide about {data['main_keyword']} - everything you need to know."
            },
            "metrics": {
                "word_count": article_data['word_count'],
                "readability": article_data['readability_score'],
                "keyword_density": article_data['keyword_density'],
                "seo_score": article_data['seo_score']
            },
            "recommendations": recommendations,
            "competitor_comparison": competitor_comparison
        }
        
        logger.info("✅ Successfully generated complete SEO article")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Generation error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Failed to generate content: {str(e)}. Please check your API keys and try again."
        }), 500

@app.route('/progress')
def get_progress():
    """Get progress updates"""
    global progress_updates
    updates = progress_updates.copy()
    return jsonify(updates)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "openai_available": OPENAI_AVAILABLE,
        "reddit_scraper_available": RedditScraper is not None,
        "serp_agent_available": SerpAgent is not None
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting Waqzee SEO Article Generator on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
