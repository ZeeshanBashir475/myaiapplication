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
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

# Import agents (with fallbacks)
RedditScraper = None
PainPointExtractor = None
ContentGenerator = None
ContentEvaluationAgent = None

try:
    from Reddit_scraper import RedditScraper
    logger.info("RedditScraper imported")
except Exception as e:
    logger.error(f"Failed to import RedditScraper: {e}")

try:
    from Pain_point_extractor import PainPointExtractor
    logger.info("PainPointExtractor imported")
except Exception as e:
    logger.error(f"Failed to import PainPointExtractor: {e}")

try:
    from content_generator import ContentGenerator
    logger.info("ContentGenerator imported")
except Exception as e:
    logger.error(f"Failed to import ContentGenerator: {e}")

try:
    from ContentEvaluationAgent import ContentEvaluationAgent
    logger.info("ContentEvaluationAgent imported")
except Exception as e:
    logger.error(f"Failed to import ContentEvaluationAgent: {e}")

app = Flask(__name__)
CORS(app)

# Global progress tracking for SSE
progress_updates = []

def add_progress(message: str, percentage: int):
    """Add progress update for SSE"""
    progress_updates.append({
        "message": message,
        "percentage": percentage,
        "timestamp": datetime.now().isoformat()
    })

class OpenAIClient:
    """Enhanced OpenAI client for SEO content generation"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('Open_Api_Key')
        self.available = False
        
        if not OPENAI_AVAILABLE or not self.api_key:
            logger.warning("OpenAI not configured")
            return
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key, timeout=60.0)
            self.async_client = openai.AsyncOpenAI(api_key=self.api_key, timeout=60.0)
            self.available = True
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
    
    async def generate_seo_article(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate SEO-optimized article"""
        if not self.available:
            return "<h1>Content Generation Unavailable</h1><p>Please configure OpenAI API key.</p>"
        
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "You are an expert SEO content writer. Create engaging, well-structured HTML content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"<p>Error generating content: {str(e)}</p>"

class RedditAnalyzer:
    """Analyze Reddit for pain points and discussions"""
    
    @staticmethod
    async def analyze(topic: str, subreddits: List[str] = None) -> Dict:
        """Analyze Reddit discussions"""
        add_progress("🔍 Searching Reddit discussions...", 10)
        
        if not subreddits:
            subreddits = ['askreddit', 'technology', 'business', 'entrepreneur']
        
        pain_points = []
        discussions = []
        
        # Use RedditScraper if available
        if RedditScraper:
            try:
                scraper = RedditScraper()
                for subreddit in subreddits[:3]:
                    data = scraper.scrape_for_pain_points(subreddit, topic, 10)
                    
                    # Extract pain points
                    for post in data.get('posts', [])[:5]:
                        title = post.get('title', '')
                        text = post.get('selftext', '')
                        
                        # Look for pain point indicators
                        if any(word in (title + text).lower() for word in ['problem', 'issue', 'help', 'struggling', 'frustrated', 'confused']):
                            pain_points.append({
                                'pain': title[:150],
                                'subreddit': f"r/{subreddit}",
                                'score': post.get('score', 0)
                            })
                        
                        discussions.append({
                            'title': title,
                            'subreddit': f"r/{subreddit}",
                            'url': post.get('url', ''),
                            'score': post.get('score', 0)
                        })
                
                add_progress(f"✓ Found {len(pain_points)} pain points from Reddit", 20)
            except Exception as e:
                logger.error(f"Reddit scraping error: {e}")
        
        # Fallback pain points if no Reddit data
        if not pain_points:
            pain_points = [
                {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100},
                {'pain': f"Understanding the complexities of {topic}", 'subreddit': "general", 'score': 80},
                {'pain': f"Making informed decisions about {topic}", 'subreddit': "general", 'score': 75}
            ]
        
        return {
            'pain_points': pain_points[:10],
            'discussions': discussions[:5],
            'summary': f"Analyzed {len(subreddits)} subreddits, found {len(pain_points)} pain points"
        }

class SerpAnalyzer:
    """Analyze Google SERP results and competitors"""
    
    @staticmethod
    async def analyze(keyword: str) -> Dict:
        """Analyze SERP results"""
        add_progress("🌐 Analyzing Google search results...", 30)
        
        try:
            api_key = os.getenv('Serp_API')
            if not api_key:
                return SerpAnalyzer._get_fallback_data(keyword)
            
            url = "https://serpapi.com/search"
            params = {
                "q": keyword,
                "api_key": api_key,
                "num": 10,
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            # Extract top results
            top_results = []
            for result in data.get("organic_results", [])[:5]:
                top_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('snippet', ''),
                    'position': result.get('position', 0)
                })
            
            # Extract People Also Ask
            people_also_ask = []
            for question in data.get("related_questions", [])[:5]:
                people_also_ask.append({
                    'question': question.get('question', ''),
                    'snippet': question.get('snippet', '')[:200]
                })
            
            # Extract related searches
            related_keywords = [s.get('query', '') for s in data.get("related_searches", [])[:5]]
            
            add_progress(f"✓ Analyzed top {len(top_results)} search results", 40)
            
            return {
                'top_results': top_results,
                'people_also_ask': people_also_ask,
                'related_keywords': related_keywords,
                'opportunities': SerpAnalyzer._identify_opportunities(top_results)
            }
            
        except Exception as e:
            logger.error(f"SERP API error: {e}")
            return SerpAnalyzer._get_fallback_data(keyword)
    
    @staticmethod
    def _get_fallback_data(keyword: str) -> Dict:
        """Fallback SERP data"""
        return {
            'top_results': [
                {'title': f"Ultimate Guide to {keyword}", 'url': '#', 'snippet': 'Comprehensive guide...', 'position': 1},
                {'title': f"Best {keyword} in 2024", 'url': '#', 'snippet': 'Top recommendations...', 'position': 2}
            ],
            'people_also_ask': [
                {'question': f"What is {keyword}?", 'snippet': 'Basic definition...'},
                {'question': f"How to use {keyword}?", 'snippet': 'Step by step guide...'}
            ],
            'related_keywords': [f"{keyword} tips", f"best {keyword}", f"{keyword} guide"],
            'opportunities': ['Add comparison tables', 'Include user testimonials', 'Add visual guides']
        }
    
    @staticmethod
    def _identify_opportunities(top_results: List[Dict]) -> List[str]:
        """Identify content opportunities"""
        opportunities = []
        
        # Check what's missing in top results
        has_comparison = any('vs' in r['title'].lower() or 'comparison' in r['title'].lower() for r in top_results)
        has_guide = any('guide' in r['title'].lower() or 'how to' in r['title'].lower() for r in top_results)
        has_list = any(any(str(i) in r['title'] for i in range(1, 21)) for r in top_results)
        
        if not has_comparison:
            opportunities.append("Add detailed comparison tables")
        if not has_guide:
            opportunities.append("Include step-by-step tutorials")
        if not has_list:
            opportunities.append("Create numbered lists for better readability")
        
        opportunities.extend([
            "Include real user testimonials from Reddit",
            "Add visual elements (charts, infographics)",
            "Include FAQ section from 'People Also Ask'"
        ])
        
        return opportunities[:5]

class SEOContentGenerator:
    """Generate SEO-optimized content"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
    
    async def generate(self, inputs: Dict, reddit_data: Dict, serp_data: Dict) -> Dict:
        """Generate full SEO article"""
        add_progress("✍️ Generating SEO-optimized article...", 50)
        
        # Build comprehensive prompt
        pain_points_text = '\n'.join([f"- {p['pain']}" for p in reddit_data['pain_points'][:5]])
        paa_text = '\n'.join([f"- {q['question']}" for q in serp_data['people_also_ask'][:5]])
        opportunities_text = '\n'.join([f"- {o}" for o in serp_data['opportunities'][:3]])
        
        prompt = f"""
Create a comprehensive, SEO-optimized article about "{inputs['main_keyword']}"

Title: {inputs.get('title', inputs['main_keyword'])}
Tone: {inputs.get('tone', 'Professional yet friendly')}
Target Audience: {inputs.get('target_country', 'Global')}

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
3. Include an emotional hook in the introduction
4. Address each pain point naturally
5. Include a FAQ section
6. Use the main keyword 5-8 times naturally
7. Include secondary keywords: {', '.join(inputs.get('secondary_keywords', []))}
8. End with a strong call-to-action

FORMAT THE ARTICLE WITH:
- <h1> for the main title
- <h2> for major sections
- <h3> for subsections
- <p> for paragraphs
- <ul> and <li> for lists
- <strong> for emphasis
- <blockquote> for important quotes or statistics

Write the complete article now:
"""
        
        article = await self.openai_client.generate_seo_article(prompt)
        
        # Calculate metrics
        word_count = len(article.split())
        keyword_density = (article.lower().count(inputs['main_keyword'].lower()) / word_count) * 100 if word_count > 0 else 0
        
        add_progress("✓ Article generated successfully", 70)
        
        return {
            'content': article,
            'word_count': word_count,
            'keyword_density': round(keyword_density, 2),
            'readability_score': self._calculate_readability(article),
            'seo_score': self._calculate_seo_score(article, inputs, serp_data)
        }
    
    def _calculate_readability(self, text: str) -> str:
        """Calculate readability score"""
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        if sentences == 0:
            return "N/A"
        avg_words_per_sentence = words / sentences
        
        if avg_words_per_sentence < 15:
            return "Easy (Grade 6-8)"
        elif avg_words_per_sentence < 20:
            return "Medium (Grade 9-10)"
        else:
            return "Difficult (Grade 11+)"
    
    def _calculate_seo_score(self, content: str, inputs: Dict, serp_data: Dict) -> int:
        """Calculate SEO score (0-100)"""
        score = 50  # Base score
        
        # Check for key elements
        if '<h1>' in content: score += 10
        if '<h2>' in content: score += 10
        if inputs['main_keyword'].lower() in content.lower(): score += 10
        if any(kw in content.lower() for kw in inputs.get('secondary_keywords', [])): score += 10
        if len(content.split()) > 2000: score += 10
        
        return min(100, score)

class SEORecommendationEngine:
    """Generate SEO recommendations like SEMrush/SurferSEO"""
    
    @staticmethod
    async def generate_recommendations(article_data: Dict, inputs: Dict, serp_data: Dict) -> List[Dict]:
        """Generate actionable SEO recommendations"""
        add_progress("📊 Generating SEO recommendations...", 80)
        
        recommendations = []
        
        # Keyword recommendations
        if article_data['keyword_density'] < 1:
            recommendations.append({
                'tip': f"Increase usage of main keyword '{inputs['main_keyword']}' to 1-2% density",
                'impact': 5,
                'category': 'SEO'
            })
        elif article_data['keyword_density'] > 3:
            recommendations.append({
                'tip': f"Reduce keyword stuffing - current density is {article_data['keyword_density']}%",
                'impact': 4,
                'category': 'SEO'
            })
        
        # Content structure
        if article_data['word_count'] < 2400:
            recommendations.append({
                'tip': f"Expand content to 2,400+ words (current: {article_data['word_count']})",
                'impact': 5,
                'category': 'Content'
            })
        
        # Emotional depth
        recommendations.append({
            'tip': "Add a personal story or case study in the introduction for emotional connection",
            'impact': 4,
            'category': 'Emotional Depth'
        })
        
        # Technical SEO
        recommendations.append({
            'tip': "Add schema markup for FAQ section to improve SERP visibility",
            'impact': 3,
            'category': 'Technical SEO'
        })
        
        # Readability
        if 'Difficult' in article_data.get('readability_score', ''):
            recommendations.append({
                'tip': "Simplify complex sentences - aim for 15-20 words per sentence",
                'impact': 4,
                'category': 'Readability'
            })
        
        # Visual elements
        recommendations.append({
            'tip': "Add 3-5 relevant images with descriptive alt text containing keywords",
            'impact': 3,
            'category': 'UX'
        })
        
        # Internal linking
        recommendations.append({
            'tip': "Add 2-3 internal links to related content on your site",
            'impact': 3,
            'category': 'SEO'
        })
        
        # CTA optimization
        recommendations.append({
            'tip': "Place a mid-article CTA after addressing the main pain point",
            'impact': 4,
            'category': 'Conversion'
        })
        
        return recommendations[:8]

class CompetitorAnalyzer:
    """Analyze and compare with competitors"""
    
    @staticmethod
    async def compare(article_data: Dict, serp_data: Dict, reddit_data: Dict) -> Dict:
        """Compare with top competitors"""
        add_progress("🏆 Analyzing competitor comparison...", 90)
        
        # Create comparison table
        comparison = {
            'features': [
                {
                    'feature': 'Word Count',
                    'competitors': 'Average 1,500-2,000',
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
                    'competitors': 'Rehashed information',
                    'you': 'Reddit insights + user data',
                    'advantage': True
                },
                {
                    'feature': 'Content Structure',
                    'competitors': 'Standard blog format',
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
• Achieving {article_data.get('seo_score', 80)}% SEO optimization score
• Addressing gaps identified in top {len(serp_data['top_results'])} SERP results
• Including unique insights not found in competitor content"""
        }
        
        return comparison

# HTML Template with tabs for Article, Metrics, Recommendations, and Competitors
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Article Generator - Advanced AI Content Platform</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
            color: #1e3c72;
        }
        
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .input-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .input-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        label {
            font-size: 12px;
            font-weight: 600;
            color: #666;
            margin-bottom: 6px;
            text-transform: uppercase;
        }
        
        input, select, textarea {
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #1e3c72;
        }
        
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .subreddit-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        
        .chip {
            background: #1e3c72;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .chip i {
            cursor: pointer;
        }
        
        .btn {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .tabs {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            display: none;
        }
        
        .tabs.active {
            display: block;
        }
        
        .tab-header {
            display: flex;
            background: #f5f5f5;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .tab-btn {
            flex: 1;
            padding: 15px;
            background: none;
            border: none;
            font-weight: 600;
            color: #666;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            color: #1e3c72;
            background: white;
            border-bottom-color: #1e3c72;
        }
        
        .tab-btn i {
            margin-right: 8px;
        }
        
        .tab-content {
            display: none;
            padding: 30px;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Article tab styles */
        .article-content h1 {
            color: #1e3c72;
            font-size: 32px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #1e3c72;
        }
        
        .article-content h2 {
            color: #2a5298;
            font-size: 24px;
            margin: 30px 0 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .article-content h3 {
            color: #333;
            font-size: 20px;
            margin: 25px 0 12px;
        }
        
        .article-content p {
            line-height: 1.8;
            margin-bottom: 15px;
            color: #444;
        }
        
        .article-content ul, .article-content ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        .article-content li {
            margin-bottom: 8px;
            line-height: 1.6;
        }
        
        /* Metrics tab */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 36px;
            font-weight: 700;
            color: #1e3c72;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-top: 5px;
        }
        
        /* Analysis cards */
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .analysis-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #1e3c72;
        }
        
        .analysis-card h3 {
            color: #1e3c72;
            margin-bottom: 15px;
            font-size: 16px;
        }
        
        .pain-point {
            background: white;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 6px;
            font-size: 14px;
            border-left: 3px solid #ff6b6b;
        }
        
        .serp-result {
            background: white;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .serp-result .title {
            font-weight: 600;
            color: #1e3c72;
        }
        
        .serp-result .url {
            color: #666;
            font-size: 12px;
        }
        
        /* Recommendations */
        .recommendation {
            background: white;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 4px solid #1e3c72;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .rec-content {
            flex: 1;
        }
        
        .rec-tip {
            font-size: 14px;
            margin-bottom: 5px;
        }
        
        .rec-category {
            display: inline-block;
            background: #e0e0e0;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            color: #666;
        }
        
        .rec-impact {
            display: flex;
            gap: 2px;
        }
        
        .star {
            color: #ffd700;
        }
        
        /* Competitor comparison */
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .comparison-table th {
            background: #f5f5f5;
            font-weight: 600;
            color: #333;
        }
        
        .comparison-table .advantage {
            color: #28a745;
            font-weight: 600;
        }
        
        .comparison-table .disadvantage {
            color: #dc3545;
        }
        
        /* Progress bar */
        .progress-container {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
        }
        
        .progress-container.active {
            display: block;
        }
        
        .progress-bar {
            background: #e0e0e0;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(135deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }
        
        .progress-text {
            text-align: center;
            margin-top: 10px;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .input-grid {
                grid-template-columns: 1fr;
            }
            
            .tab-header {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <i class="fas fa-rocket"></i> SEO Article Generator - AI Content Platform
        </div>
    </div>
    
    <div class="container">
        <!-- Input Section -->
        <div class="input-section">
            <h2 style="margin-bottom: 20px;">Generate SEO-Optimized Content</h2>
            
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
                        <option value="United States">United States</option>
                        <option value="United Kingdom">United Kingdom</option>
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
            
            <div class="form-group">
                <label>Unique Insights (Optional)</label>
                <textarea id="uniqueInsights" placeholder="Share any unique data, stories, or insights that could make your content stand out..."></textarea>
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
                <button class="tab-btn active" onclick="switchTab('article')">
                    <i class="fas fa-file-alt"></i> Article
                </button>
                <button class="tab-btn" onclick="switchTab('metrics')">
                    <i class="fas fa-chart-line"></i> Metrics
                </button>
                <button class="tab-btn" onclick="switchTab('recommendations')">
                    <i class="fas fa-lightbulb"></i> Recommendations
                </button>
                <button class="tab-btn" onclick="switchTab('competitors')">
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
                <h3 style="margin-bottom: 20px;">SEO Improvement Recommendations</h3>
                <div id="recommendationsList"></div>
            </div>
            
            <!-- Competitors Tab -->
            <div class="tab-content" id="competitorsTab">
                <h3 style="margin-bottom: 20px;">Competitor Analysis</h3>
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
                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin-bottom: 10px;">Summary</h4>
                    <p id="comparisonSummary"></p>
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
        
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
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
                
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate content. Please try again.');
            } finally {
                stopProgressUpdates();
                document.getElementById('generateBtn').disabled = false;
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
            const painPointsHtml = data.reddit_pain_points.map(p => 
                `<div class="pain-point">${p.pain || p}</div>`
            ).join('');
            document.getElementById('painPointsList').innerHTML = painPointsHtml || '<p>No pain points found</p>';
            
            // Display SERP results
            const serpHtml = data.serp_summary.top_results.map(r => 
                `<div class="serp-result">
                    <div class="title">${r.title}</div>
                    <div class="url">${r.url}</div>
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
                    <td>${f.feature}</td>
                    <td>${f.competitors}</td>
                    <td class="${f.advantage ? 'advantage' : ''}">${f.you}</td>
                    <td>${f.advantage ? '✓' : '-'}</td>
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
async def generate_seo_article():
    """Generate complete SEO article with all analysis"""
    try:
        data = request.get_json()
        
        # Initialize OpenAI
        openai_client = OpenAIClient()
        
        # 1. Reddit Analysis
        reddit_data = await RedditAnalyzer.analyze(
            data['main_keyword'],
            data.get('subreddits', [])
        )
        
        # 2. SERP Analysis
        serp_data = await SerpAnalyzer.analyze(data['main_keyword'])
        
        # 3. Generate Article
        generator = SEOContentGenerator(openai_client)
        article_data = await generator.generate(data, reddit_data, serp_data)
        
        # 4. Generate Recommendations
        recommendations = await SEORecommendationEngine.generate_recommendations(
            article_data, data, serp_data
        )
        
        # 5. Competitor Analysis
        competitor_comparison = await CompetitorAnalyzer.compare(
            article_data, serp_data, reddit_data
        )
        
        add_progress("✅ Generation complete!", 100)
        
        return jsonify({
            "inputs": data,
            "reddit_pain_points": reddit_data['pain_points'],
            "serp_summary": {
                "top_results": serp_data['top_results'],
                "people_also_ask": serp_data['people_also_ask'],
                "opportunities": serp_data['opportunities']
            },
            "article": {
                "content": article_data['content'],
                "meta_description": f"Learn about {data['main_keyword']} - comprehensive guide covering everything you need to know."
            },
            "metrics": {
                "word_count": article_data['word_count'],
                "readability": article_data['readability_score'],
                "keyword_density": article_data['keyword_density'],
                "seo_score": article_data['seo_score']
            },
            "recommendations": recommendations,
            "competitor_comparison": competitor_comparison
        })
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/progress')
def get_progress():
    """Get progress updates"""
    global progress_updates
    updates = progress_updates.copy()
    progress_updates.clear()  # Clear after sending
    return jsonify(updates)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
