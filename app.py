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
CompellingSEOStrategist = None
NLPAgent = None

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

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=3)

# Global progress tracking
progress_updates = []

# Initialize NLP Agent globally
nlp_agent = None
try:
    nlp_agent = NLPAgent()
    if nlp_agent.available:
        logger.info("✅ Global NLP Agent initialized and ready")
    else:
        logger.warning("⚠️ NLP Agent initialized but not available (check credentials)")
except Exception as e:
    logger.error(f"❌ Failed to initialize global NLP Agent: {e}")

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
            logger.info(f"Creating OpenAI client...")
            logger.info(f"API Key found: {self.api_key[:15]}...")
            
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

def analyze_competitor_content_nlp(serp_data: Dict) -> Dict:
    """
    Use NLP Agent to analyze competitor content and extract insights.
    
    Args:
        serp_data: SERP analysis results
        
    Returns:
        Dictionary with NLP analysis of competitors
    """
    if not nlp_agent or not nlp_agent.available:
        logger.warning("NLP Agent not available - skipping competitor NLP analysis")
        return {
            'competitor_entities': [],
            'competitor_categories': [],
            'competitor_sentiment': {'score': 0, 'magnitude': 0, 'label': 'neutral'},
            'nlp_available': False
        }
    
    add_progress("🧠 Analyzing competitor content with NLP...", 35)
    
    try:
        # Combine top competitor snippets for analysis
        competitor_text = " ".join([
            result.get('snippet', '') 
            for result in serp_data.get('top_results', [])[:3]
        ])
        
        if not competitor_text.strip():
            logger.warning("No competitor text available for NLP analysis")
            return {
                'competitor_entities': [],
                'competitor_categories': [],
                'competitor_sentiment': {'score': 0, 'magnitude': 0, 'label': 'neutral'},
                'nlp_available': True
            }
        
        # Analyze competitor content
        entities = nlp_agent.extract_entities(competitor_text)
        categories = nlp_agent.get_category(competitor_text)
        sentiment = nlp_agent.get_sentiment(competitor_text)
        
        logger.info(f"✅ NLP analysis found {len(entities)} entities, {len(categories)} categories")
        
        return {
            'competitor_entities': entities[:15],  # Top 15 entities
            'competitor_categories': categories,
            'competitor_sentiment': sentiment,
            'nlp_available': True,
            'entity_summary': {
                'total_entities': len(entities),
                'top_entities': [e['name'] for e in entities[:5]],
                'entity_types': list(set([e['type'] for e in entities]))
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Competitor NLP analysis error: {e}")
        return {
            'competitor_entities': [],
            'competitor_categories': [],
            'competitor_sentiment': {'score': 0, 'magnitude': 0, 'label': 'neutral'},
            'nlp_available': False,
            'error': str(e)
        }

def generate_seo_content(inputs: Dict, reddit_data: Dict, serp_data: Dict, competitor_nlp: Dict, openai_client: OpenAIClient) -> Dict:
    """Generate SEO content using the Compelling SEO Strategist agent"""
    add_progress("✍️ Generating SEO-optimized article with Compelling SEO Strategist...", 50)
    
    try:
        # Initialize the Compelling SEO Strategist
        if CompellingSEOStrategist:
            strategist = CompellingSEOStrategist(api_key=openai_client.api_key)
            
            if strategist.available:
                logger.info("📝 Using Compelling SEO Strategist for content generation")
                
                # Enhance unique insights with competitor entity data
                enhanced_insights = inputs.get('unique_insights', '')
                if competitor_nlp.get('nlp_available') and competitor_nlp.get('entity_summary'):
                    entity_note = f"\n\nNote: Top competitors are covering these key entities: {', '.join(competitor_nlp['entity_summary']['top_entities'][:5])}. Consider including these where relevant."
                    enhanced_insights += entity_note
                
                # Use the new agent to write the article
                result = strategist.write_article(
                    main_keyword=inputs['main_keyword'],
                    secondary_keywords=inputs.get('secondary_keywords', []),
                    tone=inputs.get('tone', 'friendly'),
                    target_country=inputs.get('target_country', 'United Kingdom'),
                    language=inputs.get('language', 'en'),
                    serp_data=serp_data,
                    reddit_data=reddit_data,
                    unique_insights=enhanced_insights,
                    title=inputs.get('title', inputs['main_keyword']),
                    max_tokens=4000
                )
                
                if result['success']:
                    article_content = result['content']
                    word_count = result['word_count']
                    
                    # Calculate metrics
                    keyword_density = (article_content.lower().count(inputs['main_keyword'].lower()) / word_count) * 100 if word_count > 0 else 0
                    
                    add_progress("✓ Article generated successfully with enhanced quality", 70)
                    
                    return {
                        'content': article_content,
                        'word_count': word_count,
                        'keyword_density': round(keyword_density, 2),
                        'readability_score': calculate_readability(article_content),
                        'seo_score': calculate_seo_score(article_content, inputs, serp_data),
                        'length_strategy': result.get('length_strategy', {})
                    }
                else:
                    logger.warning("⚠️ Compelling SEO Strategist failed, falling back to basic generation")
            else:
                logger.warning("⚠️ Compelling SEO Strategist not available, using fallback")
        else:
            logger.warning("⚠️ CompellingSEOStrategist not imported, using fallback")
        
        # Fallback to basic generation
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

Write a complete 2,400-3,600 word article using proper HTML formatting.
"""
        
        article = openai_client.generate_seo_article(prompt) if hasattr(openai_client, 'generate_seo_article') else "<h1>Error</h1><p>Content generation unavailable</p>"
        
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
            'content': f"<h1>Error Generating Content</h1><p>Failed to generate article: {str(e)}</p>",
            'word_count': 0,
            'keyword_density': 0,
            'readability_score': 'N/A',
            'seo_score': 0
        }

def analyze_generated_content_nlp(article_content: str, competitor_nlp: Dict) -> Dict:
    """
    Use NLP Agent to analyze the generated article and compare with competitors.
    
    Args:
        article_content: Generated article HTML
        competitor_nlp: Competitor NLP analysis results
        
    Returns:
        Dictionary with NLP analysis and comparison
    """
    if not nlp_agent or not nlp_agent.available:
        logger.warning("NLP Agent not available - skipping article NLP analysis")
        return {
            'article_entities': [],
            'article_categories': [],
            'article_sentiment': {'score': 0, 'magnitude': 0, 'label': 'neutral'},
            'entity_coverage': {},
            'nlp_available': False
        }
    
    add_progress("🧠 Analyzing generated article with NLP...", 75)
    
    try:
        # Strip HTML tags for cleaner analysis
        import re
        clean_text = re.sub(r'<[^>]+>', ' ', article_content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Analyze the article
        article_analysis = nlp_agent.analyze_full(clean_text, doc_type="PLAIN_TEXT")
        
        # Compare with competitor entities if available
        entity_coverage = {}
        if competitor_nlp.get('competitor_entities'):
            competitor_entity_names = set([e['name'].lower() for e in competitor_nlp['competitor_entities']])
            article_entity_names = set([e['name'].lower() for e in article_analysis['entities']])
            
            covered = competitor_entity_names & article_entity_names
            missing = competitor_entity_names - article_entity_names
            
            coverage_score = len(covered) / len(competitor_entity_names) if competitor_entity_names else 1.0
            
            entity_coverage = {
                'coverage_score': round(coverage_score, 4),
                'coverage_percentage': round(coverage_score * 100, 2),
                'covered_count': len(covered),
                'missing_count': len(missing),
                'missing_entities': list(missing)[:10],
                'grade': _get_coverage_grade(coverage_score)
            }
        
        logger.info(f"✅ Article NLP analysis complete - {len(article_analysis['entities'])} entities found")
        
        return {
            'article_entities': article_analysis['entities'][:15],
            'article_categories': article_analysis['categories'],
            'article_sentiment': article_analysis['sentiment'],
            'entity_coverage': entity_coverage,
            'nlp_available': True,
            'stats': article_analysis['stats']
        }
        
    except Exception as e:
        logger.error(f"❌ Article NLP analysis error: {e}")
        return {
            'article_entities': [],
            'article_categories': [],
            'article_sentiment': {'score': 0, 'magnitude': 0, 'label': 'neutral'},
            'entity_coverage': {},
            'nlp_available': False,
            'error': str(e)
        }

def _get_coverage_grade(score: float) -> str:
    """Get letter grade for coverage score"""
    if score >= 0.9:
        return "A+"
    elif score >= 0.8:
        return "A"
    elif score >= 0.7:
        return "B"
    elif score >= 0.6:
        return "C"
    else:
        return "D"

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

def generate_recommendations(article_data: Dict, inputs: Dict, serp_data: Dict, article_nlp: Dict) -> List[Dict]:
    """Generate SEO recommendations including NLP insights"""
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
    
    # NLP-based recommendations
    if article_nlp.get('nlp_available') and article_nlp.get('entity_coverage'):
        coverage = article_nlp['entity_coverage']
        if coverage['coverage_percentage'] < 70:
            recommendations.append({
                'tip': f"Entity coverage is {coverage['coverage_percentage']:.0f}% - add mentions of: {', '.join(coverage['missing_entities'][:3])}",
                'impact': 5,
                'category': 'Entity SEO'
            })
    
    if article_nlp.get('article_sentiment', {}).get('label') == 'negative':
        recommendations.append({
            'tip': "Article has negative tone - consider rewriting for more positive/neutral sentiment",
            'impact': 4,
            'category': 'Tone'
        })
    
    recommendations.extend([
        {'tip': "Add personal story in intro for emotional connection", 'impact': 4, 'category': 'Engagement'},
        {'tip': "Include schema markup for FAQ section", 'impact': 3, 'category': 'Technical SEO'},
        {'tip': "Add 3-5 optimized images with alt text", 'impact': 3, 'category': 'UX'},
        {'tip': "Add 2-3 internal links to related content", 'impact': 3, 'category': 'SEO'}
    ])
    
    return recommendations[:8]

def generate_competitor_comparison(article_data: Dict, serp_data: Dict, reddit_data: Dict, article_nlp: Dict) -> Dict:
    """Generate competitor comparison including NLP insights"""
    add_progress("🏆 Analyzing competitor comparison...", 90)
    
    features = [
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
        }
    ]
    
    # Add NLP comparison if available
    if article_nlp.get('nlp_available') and article_nlp.get('entity_coverage'):
        coverage = article_nlp['entity_coverage']
        features.append({
            'feature': 'Entity Coverage',
            'competitors': '100% (baseline)',
            'you': f"{coverage['coverage_percentage']:.0f}% coverage (Grade: {coverage['grade']})",
            'advantage': coverage['coverage_percentage'] >= 80
        })
    
    features.extend([
        {
            'feature': 'Unique Insights',
            'competitors': 'Rehashed info',
            'you': 'Reddit insights + NLP analysis',
            'advantage': True
        },
        {
            'feature': 'Content Structure',
            'competitors': 'Standard blog',
            'you': 'FAQ + Tables + Examples',
            'advantage': True
        }
    ])
    
    summary_parts = [
        f"• Integrating {len(reddit_data['pain_points'])} real user pain points from Reddit",
        f"• Providing {article_data['word_count']} words of comprehensive coverage",
        f"• Achieving {article_data.get('seo_score', 80)}% SEO optimisation score"
    ]
    
    if article_nlp.get('entity_coverage'):
        summary_parts.append(f"• Entity coverage: {article_nlp['entity_coverage']['coverage_percentage']:.0f}% (Grade: {article_nlp['entity_coverage']['grade']})")
    
    summary_parts.append(f"• Addressing gaps in top {len(serp_data['top_results'])} SERP results")
    
    comparison = {
        'features': features,
        'summary': "Your article outperforms competitors by:\n" + "\n".join(summary_parts)
    }
    
    return comparison

# HTML Template (keeping existing design)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CompellSEO - AI Content Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', sans-serif; background: #000; color: #fff; min-height: 100vh; line-height: 1.6; }
        .header { background: #fff; padding: 20px 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 100; }
        .logo { font-size: 32px; font-weight: 900; color: #000; letter-spacing: -1px; }
        .logo-subtitle { font-size: 12px; font-weight: 400; color: #666; letter-spacing: 2px; text-transform: uppercase; }
        .container { max-width: 1400px; margin: 40px auto; padding: 0 20px; }
        .input-section { background: #fff; color: #000; padding: 40px; margin-bottom: 40px; box-shadow: 0 10px 40px rgba(255,255,255,0.1); }
        .section-title { font-size: 28px; font-weight: 700; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 1px; }
        .input-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-bottom: 25px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-size: 11px; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
        input, select, textarea { padding: 12px 15px; border: 2px solid #000; font-size: 14px; font-family: 'Roboto', sans-serif; background: #fff; color: #000; transition: all 0.3s; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #666; background: #f5f5f5; }
        textarea { resize: vertical; min-height: 100px; }
        .btn { background: #000; color: #fff; border: none; padding: 18px 40px; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.3s; text-transform: uppercase; letter-spacing: 2px; font-family: 'Roboto', sans-serif; }
        .btn:hover { background: #333; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .btn:disabled { background: #666; cursor: not-allowed; transform: none; }
        .progress-container { background: #fff; padding: 30px; margin-bottom: 30px; display: none; }
        .progress-container.active { display: block; }
        .progress-bar { background: #e0e0e0; height: 40px; overflow: hidden; border: 2px solid #000; }
        .progress-fill { background: #000; height: 100%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 14px; letter-spacing: 1px; }
        .progress-text { text-align: center; margin-top: 15px; color: #000; font-weight: 500; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        .tabs { background: #fff; overflow: hidden; box-shadow: 0 10px 40px rgba(255,255,255,0.1); display: none; }
        .tabs.active { display: block; }
        .tab-header { display: flex; background: #000; flex-wrap: wrap; }
        .tab-btn { flex: 1; min-width: 150px; padding: 20px; background: none; border: none; font-weight: 700; color: #fff; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.3s; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-family: 'Roboto', sans-serif; }
        .tab-btn.active { background: #fff; color: #000; border-bottom-color: #000; }
        .tab-content { display: none; padding: 40px; max-height: 600px; overflow-y: auto; color: #000; }
        .tab-content.active { display: block; }
        .article-content h1 { color: #000; font-size: 36px; font-weight: 900; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 3px solid #000; text-transform: uppercase; letter-spacing: -1px; }
        .article-content h2 { color: #000; font-size: 26px; font-weight: 700; margin: 35px 0 20px; padding-bottom: 10px; border-bottom: 2px solid #e0e0e0; text-transform: uppercase; letter-spacing: 1px; }
        .article-content p { line-height: 1.8; margin-bottom: 18px; color: #333; font-weight: 400; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px; margin-bottom: 35px; }
        .metric-card { background: #000; color: #fff; padding: 30px; text-align: center; border: 2px solid #000; }
        .metric-value { font-size: 42px; font-weight: 900; color: #fff; line-height: 1; }
        .metric-label { font-size: 11px; color: #fff; text-transform: uppercase; margin-top: 10px; font-weight: 700; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">WAQZEE</div>
        <div class="logo-subtitle">CompellSEO Platform</div>
    </div>
    <div class="container">
        <div class="input-section">
            <h2 class="section-title">CompellSEO</h2>
            <p>AI-powered content generator with advanced NLP analysis. Creates compelling, keyword-optimised articles with entity coverage scoring and sentiment analysis.</p>
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
                <h3>NLP Analysis Results</h3>
                <div id="nlpResults"></div>
            </div>
        </div>
    </div>
    <script>
        async function generateContent() {
            const mainKeyword = document.getElementById('mainKeyword').value.trim();
            const title = document.getElementById('title').value.trim();
            if (!mainKeyword || !title) { alert('Please enter both main keyword and title'); return; }
            
            document.getElementById('progressContainer').classList.add('active');
            document.getElementById('generateBtn').disabled = true;
            
            const data = {
                main_keyword: mainKeyword,
                title: title,
                secondary_keywords: document.getElementById('secondaryKeywords').value.split(',').map(k => k.trim()).filter(k => k),
                tone: document.getElementById('tone').value,
                subreddits: ['askreddit', 'technology']
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
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate content');
            } finally {
                stopProgressUpdates();
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('progressContainer').classList.remove('active');
            }
        }
        
        let progressInterval;
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
            if (progressInterval) { clearInterval(progressInterval); progressInterval = null; }
            updateProgress(100, 'Complete!');
        }
        
        function updateProgress(percentage, text) {
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressFill').textContent = percentage + '%';
            document.getElementById('progressText').textContent = text;
        }
        
        function switchTab(event, tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
        }
        
        function displayResults(data) {
            document.getElementById('articleContent').innerHTML = data.article.content || '<p>No content generated</p>';
            document.getElementById('wordCount').textContent = data.metrics.word_count || 0;
            document.getElementById('seoScore').textContent = data.metrics.seo_score || 0;
            
            if (data.article_nlp && data.article_nlp.entity_coverage) {
                document.getElementById('entityCoverage').textContent = data.article_nlp.entity_coverage.grade || 'N/A';
            }
            
            if (data.article_nlp && data.article_nlp.article_sentiment) {
                document.getElementById('sentimentLabel').textContent = data.article_nlp.article_sentiment.label.toUpperCase() || 'N/A';
            }
            
            let nlpHtml = '<p>NLP analysis complete</p>';
            if (data.article_nlp && data.article_nlp.nlp_available) {
                nlpHtml = `
                    <h4>Article Entities (Top 10):</h4>
                    <ul>${data.article_nlp.article_entities.slice(0,10).map(e => `<li>${e.name} (${e.type}) - Salience: ${e.salience}</li>`).join('')}</ul>
                    ${data.article_nlp.entity_coverage ? `<h4>Entity Coverage: ${data.article_nlp.entity_coverage.grade} (${data.article_nlp.entity_coverage.coverage_percentage}%)</h4>` : ''}
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
    """Generate complete SEO article with NLP analysis"""
    global progress_updates
    progress_updates = []
    
    try:
        data = request.get_json()
        logger.info(f"📥 Received request for keyword: {data.get('main_keyword')}")
        
        # Initialize OpenAI
        openai_client = OpenAIClient()
        if not openai_client.available:
            return jsonify({"error": "OpenAI API not configured"}), 500
        
        # 1. Reddit Analysis
        reddit_data = analyze_reddit(
            data['main_keyword'],
            data.get('subreddits', ['askreddit', 'technology'])
        )
        
        # 2. SERP Analysis
        serp_data = analyze_serp(data['main_keyword'])
        
        # 3. NLP Analysis of Competitors
        competitor_nlp = analyze_competitor_content_nlp(serp_data)
        
        # 4. Generate Article
        article_data = generate_seo_content(data, reddit_data, serp_data, competitor_nlp, openai_client)
        
        # 5. NLP Analysis of Generated Article
        article_nlp = analyze_generated_content_nlp(article_data['content'], competitor_nlp)
        
        # 6. Generate Recommendations
        recommendations = generate_recommendations(article_data, data, serp_data, article_nlp)
        
        # 7. Competitor Comparison
        competitor_comparison = generate_competitor_comparison(
            article_data, serp_data, reddit_data, article_nlp
        )
        
        add_progress("✅ Generation complete!", 100)
        
        result = {
            "inputs": data,
            "reddit_pain_points": reddit_data['pain_points'],
            "serp_summary": {
                "top_results": serp_data['top_results'],
                "people_also_ask": serp_data['people_also_ask']
            },
            "competitor_nlp": competitor_nlp,
            "article": {
                "content": article_data['content']
            },
            "metrics": {
                "word_count": article_data['word_count'],
                "seo_score": article_data['seo_score'],
                "keyword_density": article_data['keyword_density']
            },
            "article_nlp": article_nlp,
            "recommendations": recommendations,
            "competitor_comparison": competitor_comparison
        }
        
        logger.info("✅ Successfully generated complete SEO article with NLP analysis")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Generation error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/progress')
def get_progress():
    """Get progress updates"""
    global progress_updates
    return jsonify(progress_updates.copy())

@app.route('/analyze-nlp', methods=['POST'])
def analyze_nlp_endpoint():
    """Standalone NLP analysis endpoint"""
    if not nlp_agent or not nlp_agent.available:
        return jsonify({"error": "NLP Agent not available"}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        analysis = nlp_agent.analyze_full(text)
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"NLP analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "openai_available": OPENAI_AVAILABLE,
        "reddit_scraper_available": RedditScraper is not None,
        "serp_agent_available": SerpAgent is not None,
        "writer_agent_available": CompellingSEOStrategist is not None,
        "nlp_agent_available": nlp_agent.available if nlp_agent else False
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting CompellSEO Platform on port {port}")
    logger.info(f"   • Writer Agent: {'✅' if CompellingSEOStrategist else '❌'}")
    logger.info(f"   • NLP Agent: {'✅' if nlp_agent and nlp_agent.available else '❌'}")
    app.run(host="0.0.0.0", port=port, debug=False)
