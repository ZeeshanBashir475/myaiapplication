import re
import json
import os
import sys
import logging
import traceback
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
PainPointHumanizer = None
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
    from Pain_point_humanizer import PainPointHumanizer
    logger.info("PainPointHumanizer imported")
except Exception as e:
    logger.error(f"Failed to import PainPointHumanizer: {e}")

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
    logger.info(f"Progress: {percentage}% - {message}")

class OpenAIClient:
    """Enhanced OpenAI client for SEO content generation"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('Open_Api_Key')
        self.available = False
        
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available")
            return
            
        if not self.api_key:
            logger.error("OpenAI API key not found in environment variables")
            return
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key, timeout=90.0)
            self.available = True
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
    
    def generate_seo_article(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate SEO-optimized article (synchronous)"""
        if not self.available:
            error_msg = "OpenAI not available. Please configure OPENAI_API_KEY or Open_Api_Key environment variable."
            logger.error(error_msg)
            return f"<h1>Content Generation Unavailable</h1><p>{error_msg}</p>"
        
        try:
            logger.info("Starting OpenAI article generation...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "You are an expert SEO content writer. Create engaging, well-structured HTML content using natural 'you' tone. Sound like a real person, not a bot. Blend authenticity with expert insight. Avoid filler transitions like 'in this article' or 'as we discussed'. Use data, examples, and emotional framing. Every major section should connect to a user benefit or pain relief."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            logger.info("OpenAI article generation completed")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Generation error: {e}")
            logger.error(traceback.format_exc())
            return f"<p>Error generating content: {str(e)}</p>"

class RedditAnalyzer:
    """Analyze Reddit for pain points and discussions"""
    
    @staticmethod
    def analyze(topic: str, subreddits: List[str] = None) -> Dict:
        """Analyze Reddit discussions (synchronous)"""
        try:
            add_progress("🔍 Searching Reddit discussions...", 10)
            
            if not subreddits:
                subreddits = ['askreddit', 'technology', 'business', 'entrepreneur']
            
            pain_points = []
            discussions = []
            raw_posts = []
            
            # Use RedditScraper if available
            if RedditScraper:
                try:
                    scraper = RedditScraper()
                    for subreddit in subreddits[:3]:
                        logger.info(f"Scraping r/{subreddit} for topic: {topic}")
                        data = scraper.scrape_for_pain_points(subreddit, topic, 15)
                        
                        # Extract pain points
                        for post in data.get('posts', [])[:10]:
                            title = post.get('title', '')
                            text = post.get('selftext', '')
                            combined_text = f"{title} {text}"
                            
                            raw_posts.append({
                                'title': title,
                                'text': text,
                                'subreddit': subreddit,
                                'score': post.get('score', 0),
                                'url': post.get('url', '')
                            })
                            
                            # Look for pain point indicators
                            pain_indicators = ['problem', 'issue', 'help', 'struggling', 'frustrated', 
                                             'confused', 'difficult', 'challenge', 'worried', 'concern',
                                             'doesn\'t work', 'can\'t figure', 'need advice', 'stuck']
                            
                            if any(word in combined_text.lower() for word in pain_indicators):
                                pain_points.append({
                                    'pain': title[:200] if len(title) > 200 else title,
                                    'subreddit': f"r/{subreddit}",
                                    'score': post.get('score', 0),
                                    'context': text[:300] if text else ''
                                })
                            
                            discussions.append({
                                'title': title,
                                'subreddit': f"r/{subreddit}",
                                'url': post.get('url', ''),
                                'score': post.get('score', 0),
                                'snippet': text[:200] if text else ''
                            })
                    
                    # Use PainPointExtractor if available
                    if PainPointExtractor and raw_posts:
                        try:
                            extractor = PainPointExtractor()
                            extracted_points = extractor.extract_pain_points(raw_posts)
                            if extracted_points:
                                pain_points.extend(extracted_points[:10])
                        except Exception as e:
                            logger.error(f"PainPointExtractor error: {e}")
                    
                    # Use PainPointHumanizer if available
                    if PainPointHumanizer and pain_points:
                        try:
                            humanizer = PainPointHumanizer()
                            pain_points = humanizer.humanize_pain_points(pain_points)
                        except Exception as e:
                            logger.error(f"PainPointHumanizer error: {e}")
                    
                    add_progress(f"✓ Found {len(pain_points)} pain points from Reddit", 20)
                except Exception as e:
                    logger.error(f"Reddit scraping error: {e}")
                    logger.error(traceback.format_exc())
            
            # Fallback pain points if no Reddit data
            if not pain_points:
                logger.info("Using fallback pain points")
                pain_points = [
                    {'pain': f"Finding reliable information about {topic}", 'subreddit': "general", 'score': 100},
                    {'pain': f"Understanding the complexities of {topic}", 'subreddit': "general", 'score': 80},
                    {'pain': f"Making informed decisions about {topic}", 'subreddit': "general", 'score': 75},
                    {'pain': f"Comparing different options for {topic}", 'subreddit': "general", 'score': 70},
                    {'pain': f"Getting started with {topic}", 'subreddit': "general", 'score': 65}
                ]
            
            return {
                'pain_points': sorted(pain_points, key=lambda x: x.get('score', 0), reverse=True)[:10],
                'discussions': discussions[:8],
                'summary': f"Analyzed {len(subreddits)} subreddits, found {len(pain_points)} pain points from {len(raw_posts)} posts"
            }
        except Exception as e:
            logger.error(f"Reddit analysis failed: {e}")
            logger.error(traceback.format_exc())
            return {
                'pain_points': [{'pain': f"General questions about {topic}", 'subreddit': "general", 'score': 50}],
                'discussions': [],
                'summary': "Reddit analysis unavailable"
            }

class SerpAnalyzer:
    """Enhanced SERP analyzer with comprehensive competitor analysis"""
    
    @staticmethod
    def analyze(keyword: str) -> Dict:
        """Comprehensive SERP analysis (synchronous)"""
        try:
            add_progress("🌐 Analyzing Google search results...", 30)
            
            api_key = os.getenv('Serp_API')
            if not api_key:
                logger.warning("SERP API key not found, using fallback data")
                return SerpAnalyzer._get_fallback_data(keyword)
            
            url = "https://serpapi.com/search"
            params = {
                "q": keyword,
                "api_key": api_key,
                "num": 10,
                "engine": "google",
                "gl": "us",
                "hl": "en"
            }
            
            logger.info(f"Making SERP API request for keyword: {keyword}")
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"SERP API returned status {response.status_code}")
                return SerpAnalyzer._get_fallback_data(keyword)
            
            data = response.json()
            
            # Extract top 5 results with detailed analysis
            top_results = []
            for i, result in enumerate(data.get("organic_results", [])[:5]):
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                url_link = result.get('link', '')
                position = result.get('position', i + 1)
                
                analysis = SerpAnalyzer._analyze_competitor(title, snippet, url_link, position)
                
                top_results.append({
                    'title': title,
                    'url': url_link,
                    'snippet': snippet,
                    'position': position,
                    'does_well': analysis['does_well'],
                    'weakness': analysis['weakness'],
                    'word_count_estimate': analysis['word_count_estimate'],
                    'has_list': analysis['has_list'],
                    'has_howto': analysis['has_howto'],
                    'has_comparison': analysis['has_comparison']
                })
            
            # Extract People Also Ask
            people_also_ask = []
            for question in data.get("related_questions", [])[:8]:
                people_also_ask.append({
                    'question': question.get('question', ''),
                    'snippet': question.get('snippet', '')[:250],
                    'title': question.get('title', ''),
                    'link': question.get('link', '')
                })
            
            # Extract related searches
            related_keywords = []
            for search in data.get("related_searches", [])[:8]:
                related_keywords.append(search.get('query', ''))
            
            # Identify opportunities
            opportunities = SerpAnalyzer._identify_comprehensive_opportunities(
                top_results, 
                people_also_ask, 
                related_keywords,
                keyword
            )
            
            # Generate gaps analysis
            gaps_analysis = SerpAnalyzer._identify_competitive_gaps(top_results, keyword)
            
            add_progress(f"✓ Analyzed top {len(top_results)} search results", 40)
            
            return {
                'top_results': top_results,
                'people_also_ask': people_also_ask,
                'related_keywords': related_keywords,
                'opportunities': opportunities,
                'gaps_analysis': gaps_analysis,
                'total_results': data.get('search_information', {}).get('total_results', 'Unknown'),
                'search_time': data.get('search_information', {}).get('time_taken_displayed', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"SERP API error: {e}")
            logger.error(traceback.format_exc())
            return SerpAnalyzer._get_fallback_data(keyword)
    
    @staticmethod
    def _analyze_competitor(title: str, snippet: str, url: str, position: int) -> Dict:
        """Analyze individual competitor result"""
        combined = f"{title} {snippet}".lower()
        
        # Determine what they do well
        does_well = []
        if any(word in combined for word in ['guide', 'complete', 'ultimate', 'comprehensive']):
            does_well.append("Comprehensive coverage")
        if any(word in combined for word in ['2024', '2025', 'latest', 'new']):
            does_well.append("Current/timely content")
        if any(str(i) in title for i in range(1, 21)):
            does_well.append("List-based structure")
        if 'how to' in combined or 'step' in combined:
            does_well.append("Instructional approach")
        if any(word in combined for word in ['best', 'top', 'review']):
            does_well.append("Product recommendations")
        
        # Identify weaknesses
        weakness = []
        if not any(word in combined for word in ['example', 'case study', 'story']):
            weakness.append("No real examples or case studies")
        if not any(word in combined for word in ['why', 'because', 'reason']):
            weakness.append("Missing deeper 'why' explanations")
        if len(snippet) < 100:
            weakness.append("Limited preview/thin content")
        if not any(word in combined for word in ['comparison', 'vs', 'versus', 'compared']):
            weakness.append("No comparison content")
        if not any(word in combined for word in ['user', 'customer', 'people', 'real']):
            weakness.append("Lacks user perspective")
        
        has_list = any(str(i) in title for i in range(1, 21))
        has_howto = 'how to' in combined or 'how-to' in combined
        has_comparison = any(word in combined for word in ['vs', 'versus', 'comparison', 'compared to'])
        
        word_count_estimate = "1,500-2,000"
        if 'guide' in combined or 'ultimate' in combined or 'complete' in combined:
            word_count_estimate = "2,500-3,500"
        elif has_list:
            word_count_estimate = "1,000-1,500"
        
        return {
            'does_well': does_well if does_well else ["Standard SEO optimization"],
            'weakness': weakness[0] if weakness else "Generic content approach",
            'word_count_estimate': word_count_estimate,
            'has_list': has_list,
            'has_howto': has_howto,
            'has_comparison': has_comparison
        }
    
    @staticmethod
    def _identify_comprehensive_opportunities(top_results: List[Dict], paa: List[Dict], 
                                            related_keywords: List[str], main_keyword: str) -> List[str]:
        """Identify comprehensive content opportunities"""
        opportunities = []
        
        has_comparison = any(r['has_comparison'] for r in top_results)
        has_guide = any(r['has_howto'] for r in top_results)
        has_list = any(r['has_list'] for r in top_results)
        
        if not has_comparison:
            opportunities.append("Add detailed comparison tables - none in top 5")
        if not has_guide:
            opportunities.append("Include comprehensive step-by-step guide")
        if not has_list:
            opportunities.append("Create numbered actionable lists")
        
        opportunities.append("Include real user stories/testimonials from Reddit")
        opportunities.append("Add statistics or proprietary data")
        
        if paa and len(paa) >= 3:
            opportunities.append(f"Create FAQ section with {len(paa)} 'People Also Ask' questions")
        
        opportunities.append("Add visual elements: charts, infographics, comparison tables")
        
        if related_keywords and len(related_keywords) >= 3:
            opportunities.append(f"Target {len(related_keywords)} related keywords")
        
        opportunities.append("Aim for 2,400-3,600 words to dominate SERP")
        opportunities.append("Use emotional hooks from user pain points")
        
        return opportunities[:10]
    
    @staticmethod
    def _identify_competitive_gaps(top_results: List[Dict], keyword: str) -> Dict:
        """Identify specific competitive gaps"""
        gaps = {
            'content_format_gaps': [],
            'user_engagement_gaps': [],
            'seo_gaps': [],
            'authority_gaps': []
        }
        
        list_count = sum(1 for r in top_results if r['has_list'])
        howto_count = sum(1 for r in top_results if r['has_howto'])
        comparison_count = sum(1 for r in top_results if r['has_comparison'])
        
        if list_count < 2:
            gaps['content_format_gaps'].append("Limited list-based content")
        if howto_count < 2:
            gaps['content_format_gaps'].append("Few how-to guides")
        if comparison_count == 0:
            gaps['content_format_gaps'].append("No comparison content")
        
        user_focused = sum(1 for r in top_results 
                          if any(word in r['title'].lower() + r['snippet'].lower() 
                                for word in ['user', 'real', 'experience', 'story']))
        if user_focused < 2:
            gaps['user_engagement_gaps'].append("Minimal real user perspectives")
        
        keyword_in_title = sum(1 for r in top_results if keyword.lower() in r['title'].lower())
        if keyword_in_title < 4:
            gaps['seo_gaps'].append(f"Only {keyword_in_title}/5 have exact keyword in title")
        
        has_author = sum(1 for r in top_results 
                        if any(word in r['snippet'].lower() for word in ['expert', 'author', 'by ']))
        if has_author < 2:
            gaps['authority_gaps'].append("Limited author expertise signals")
        
        return gaps
    
    @staticmethod
    def _get_fallback_data(keyword: str) -> Dict:
        """Enhanced fallback SERP data"""
        logger.info("Using fallback SERP data")
        return {
            'top_results': [
                {
                    'title': f"Ultimate Guide to {keyword}", 
                    'url': '#', 
                    'snippet': 'Comprehensive guide covering everything about ' + keyword,
                    'position': 1,
                    'does_well': ["Comprehensive coverage"],
                    'weakness': "No real examples",
                    'word_count_estimate': "2,000-2,500",
                    'has_list': False,
                    'has_howto': True,
                    'has_comparison': False
                },
                {
                    'title': f"Top 10 {keyword}", 
                    'url': '#', 
                    'snippet': 'Best tips for ' + keyword,
                    'position': 2,
                    'does_well': ["List-based structure"],
                    'weakness': "Lacks depth",
                    'word_count_estimate': "1,200-1,500",
                    'has_list': True,
                    'has_howto': False,
                    'has_comparison': False
                }
            ],
            'people_also_ask': [
                {'question': f"What is {keyword}?", 'snippet': 'Definition...'},
                {'question': f"How to use {keyword}?", 'snippet': 'Guide...'},
                {'question': f"Why is {keyword} important?", 'snippet': 'Benefits...'}
            ],
            'related_keywords': [f"{keyword} guide", f"best {keyword}", f"{keyword} tips"],
            'opportunities': [
                "Add comparison tables",
                "Include user testimonials",
                "Create FAQ section",
                "Add visual guides"
            ],
            'gaps_analysis': {
                'content_format_gaps': ["Limited comparisons"],
                'user_engagement_gaps': ["Minimal user perspectives"],
                'seo_gaps': ["Keyword opportunities"],
                'authority_gaps': ["Limited expertise signals"]
            },
            'total_results': 'Fallback mode',
            'search_time': 'N/A'
        }

class SEOContentGenerator:
    """Generate SEO-optimized content"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
    
    def generate(self, inputs: Dict, reddit_data: Dict, serp_data: Dict) -> Dict:
        """Generate full SEO article (synchronous)"""
        try:
            add_progress("✍️ Generating SEO-optimized article...", 50)
            
            # Build comprehensive prompt
            pain_points_text = '\n'.join([f"- {p.get('pain', '')} (from r/{p.get('subreddit', 'reddit')})" 
                                          for p in reddit_data['pain_points'][:8]])
            
            paa_text = '\n'.join([f"- {q['question']}" for q in serp_data['people_also_ask'][:8]])
            
            opportunities_text = '\n'.join([f"- {o}" for o in serp_data['opportunities'][:5]])
            
            competitor_analysis = '\n'.join([
                f"Position {r['position']}: {r['title']}\n  Strength: {', '.join(r['does_well'])}\n  Weakness: {r['weakness']}"
                for r in serp_data['top_results'][:3]
            ])
            
            gaps_text = ""
            if serp_data.get('gaps_analysis'):
                gaps = serp_data['gaps_analysis']
                gaps_text = f"""
COMPETITIVE GAPS TO EXPLOIT:
Content Format Gaps: {', '.join(gaps.get('content_format_gaps', []))}
User Engagement Gaps: {', '.join(gaps.get('user_engagement_gaps', []))}
"""
            
            prompt = f"""
Create a comprehensive, SEO-optimized article about "{inputs['main_keyword']}"

ARTICLE DETAILS:
Title: {inputs.get('title', inputs['main_keyword'])}
Main Keyword: {inputs['main_keyword']}
Secondary Keywords: {', '.join(inputs.get('secondary_keywords', []))}
Tone: {inputs.get('tone', 'Friendly')}
Target Audience: {inputs.get('target_country', 'Global')}

REDDIT PAIN POINTS TO ADDRESS:
{pain_points_text}

COMPETITOR ANALYSIS:
{competitor_analysis}

{gaps_text}

PEOPLE ALSO ASK (Include in FAQ):
{paa_text}

CONTENT OPPORTUNITIES:
{opportunities_text}

USER'S UNIQUE INSIGHTS:
{inputs.get('unique_insights', 'Focus on comprehensive coverage')}

REQUIREMENTS:
1. Write 2,400-3,600 words
2. Start with emotional hook (question, story, or stat)
3. Use natural "you" tone - sound like a real person
4. Address each pain point naturally
5. Include FAQ section with PAA questions
6. Use main keyword 5-8 times naturally
7. Integrate secondary keywords naturally
8. Add comparison tables if competitors lack them
9. Include real user perspectives
10. End with strong CTA

HTML STRUCTURE:
<h1>Main Title</h1>
<p>Emotional introduction...</p>
<h2>Section addressing pain point 1</h2>
<p>Content...</p>
[Continue with 5-7 more H2 sections]
<h2>Frequently Asked Questions</h2>
<h3>Question from PAA</h3>
<p>Answer...</p>
<h2>Conclusion</h2>
<p>Summary and CTA</p>

Write the complete article now:
"""
            
            # Generate article
            logger.info("Calling OpenAI to generate article")
            article = self.openai_client.generate_seo_article(prompt, max_tokens=4000)
            
            if not article or len(article) < 100:
                raise Exception("Generated article is too short or empty")
            
            # Calculate metrics
            word_count = len(article.split())
            keyword_density = (article.lower().count(inputs['main_keyword'].lower()) / word_count) * 100 if word_count > 0 else 0
            secondary_keyword_count = sum(article.lower().count(kw.lower()) for kw in inputs.get('secondary_keywords', []))
            
            add_progress("✓ Article generated successfully", 70)
            
            return {
                'content': article,
                'word_count': word_count,
                'keyword_density': round(keyword_density, 2),
                'secondary_keyword_count': secondary_keyword_count,
                'readability_score': self._calculate_readability(article),
                'seo_score': self._calculate_seo_score(article, inputs, serp_data),
                'emotional_score': self._calculate_emotional_score(article, reddit_data)
            }
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _calculate_readability(self, text: str) -> str:
        """Calculate readability score"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        sentences = len(re.split(r'[.!?]+', clean_text))
        words = len(clean_text.split())
        
        if sentences == 0:
            return "N/A"
        
        avg_words = words / sentences
        
        if avg_words < 15:
            return "Easy (Grade 6-8)"
        elif avg_words < 20:
            return "Medium (Grade 9-10)"
        else:
            return "Complex (Grade 11+)"
    
    def _calculate_seo_score(self, content: str, inputs: Dict, serp_data: Dict) -> int:
        """Calculate SEO score"""
        score = 0
        
        if '<h1>' in content: score += 10
        h2_count = content.count('<h2>')
        if h2_count >= 5: score += 10
        elif h2_count >= 3: score += 5
        if '<h3>' in content: score += 5
        if 'FAQ' in content: score += 10
        if '<table>' in content: score += 5
        
        content_lower = content.lower()
        main_keyword_lower = inputs['main_keyword'].lower()
        
        if main_keyword_lower in content_lower:
            keyword_count = content_lower.count(main_keyword_lower)
            if 5 <= keyword_count <= 12: score += 15
            elif keyword_count > 0: score += 8
        
        secondary_keywords = inputs.get('secondary_keywords', [])
        if secondary_keywords:
            found = sum(1 for kw in secondary_keywords if kw.lower() in content_lower)
            score += min(15, found * 5)
        
        word_count = len(content.split())
        if word_count >= 2400: score += 15
        elif word_count >= 1800: score += 10
        elif word_count >= 1200: score += 5
        
        if '<ul>' in content or '<ol>' in content: score += 5
        if '<blockquote>' in content: score += 5
        if '<strong>' in content: score += 5
        
        return min(100, score)
    
    def _calculate_emotional_score(self, content: str, reddit_data: Dict) -> int:
        """Calculate emotional score"""
        score = 0
        content_lower = content.lower()
        
        pain_points = reddit_data.get('pain_points', [])
        for pain in pain_points[:5]:
            pain_text = pain.get('pain', '').lower()
            pain_words = [w for w in pain_text.split() if len(w) > 4]
            if pain_words and any(word in content_lower for word in pain_words[:3]):
                score += 10
        
        emotional_words = ['struggle', 'frustrated', 'worried', 'confused', 'challenge']
        emotional_count = sum(1 for word in emotional_words if word in content_lower)
        score += min(30, emotional_count * 5)
        
        question_count = content.count('?')
        score += min(20, question_count * 2)
        
        return min(100, score)

class SEORecommendationEngine:
    """Generate SEO recommendations"""
    
    @staticmethod
    def generate_recommendations(article_data: Dict, inputs: Dict, 
                                      serp_data: Dict, reddit_data: Dict) -> List[Dict]:
        """Generate recommendations (synchronous)"""
        try:
            add_progress("📊 Generating SEO recommendations...", 80)
            
            recommendations = []
            
            # Keyword density
            if article_data['keyword_density'] < 1:
                recommendations.append({
                    'tip': f"Increase main keyword '{inputs['main_keyword']}' to 1-2% density (currently {article_data['keyword_density']}%)",
                    'impact': 5,
                    'category': 'SEO'
                })
            elif article_data['keyword_density'] > 3:
                recommendations.append({
                    'tip': f"Reduce keyword density from {article_data['keyword_density']}% to 1-2%",
                    'impact': 4,
                    'category': 'SEO'
                })
            
            # Content length
            if article_data['word_count'] < 2400:
                recommendations.append({
                    'tip': f"Expand to 2,400+ words (currently {article_data['word_count']})",
                    'impact': 5,
                    'category': 'Content'
                })
            
            # Emotional depth
            if article_data.get('emotional_score', 50) < 60:
                recommendations.append({
                    'tip': "Add more emotional hooks from Reddit pain points",
                    'impact': 5,
                    'category': 'Emotional Depth'
                })
            
            # SERP gaps
            if serp_data.get('gaps_analysis'):
                gaps = serp_data['gaps_analysis']
                if gaps.get('content_format_gaps'):
                    recommendations.append({
                        'tip': f"Address format gaps: {', '.join(gaps['content_format_gaps'][:2])}",
                        'impact': 5,
                        'category': 'Content'
                    })
            
            # Technical SEO
            recommendations.append({
                'tip': "Add schema markup (FAQ, Article) for better SERP visibility",
                'impact': 4,
                'category': 'Technical SEO'
            })
            
            # Visuals
            recommendations.append({
                'tip': "Add 4-6 images with keyword-rich alt text",
                'impact': 4,
                'category': 'UX'
            })
            
            # Internal links
            recommendations.append({
                'tip': "Include 3-5 internal links to related content",
                'impact': 3,
                'category': 'SEO'
            })
            
            # External links
            recommendations.append({
                'tip': "Add 2-3 authoritative external links",
                'impact': 3,
                'category': 'Authority'
            })
            
            # CTA
            recommendations.append({
                'tip': "Place mid-article CTA after main pain point",
                'impact': 4,
                'category': 'Conversion'
            })
            
            # Readability
            if 'Complex' in article_data.get('readability_score', ''):
                recommendations.append({
                    'tip': "Simplify sentences to 15-20 words average",
                    'impact': 4,
                    'category': 'Readability'
                })
            
            recommendations.sort(key=lambda x: x['impact'], reverse=True)
            return recommendations[:12]
        except Exception as e:
            logger.error(f"Recommendations generation failed: {e}")
            return [{'tip': 'Error generating recommendations', 'impact': 1, 'category': 'Error'}]

class CompetitorAnalyzer:
    """Analyze and compare with competitors"""
    
    @staticmethod
    def compare(article_data: Dict, serp_data: Dict, reddit_data: Dict, inputs: Dict) -> Dict:
        """Compare with competitors (synchronous)"""
        try:
            add_progress("🏆 Analyzing competitor comparison...", 90)
            
            top_results = serp_data.get('top_results', [])
            competitor_avg_words = 1800
            
            if top_results:
                word_estimates = []
                for result in top_results[:3]:
                    estimate = result.get('word_count_estimate', '1,500-2,000')
                    nums = re.findall(r'\d+', estimate.replace(',', ''))
                    if len(nums) >= 2:
                        avg = (int(nums[0]) + int(nums[1])) // 2
                        word_estimates.append(avg)
                if word_estimates:
                    competitor_avg_words = sum(word_estimates) // len(word_estimates)
            
            comparison = {
                'features': [
                    {
                        'feature': 'Word Count',
                        'competitors': f'~{competitor_avg_words:,} words',
                        'you': f"{article_data['word_count']:,} words",
                        'advantage': article_data['word_count'] > competitor_avg_words
                    },
                    {
                        'feature': 'Emotional Engagement',
                        'competitors': 'Generic content',
                        'you': f"{len(reddit_data['pain_points'])} real pain points",
                        'advantage': True
                    },
                    {
                        'feature': 'Keyword Optimization',
                        'competitors': 'Basic',
                        'you': f"{article_data['keyword_density']}% density",
                        'advantage': 1 <= article_data['keyword_density'] <= 2.5
                    },
                    {
                        'feature': 'Unique Insights',
                        'competitors': 'Rehashed info',
                        'you': 'Reddit + SERP analysis',
                        'advantage': True
                    },
                    {
                        'feature': 'SEO Score',
                        'competitors': '60-75/100',
                        'you': f"{article_data.get('seo_score', 80)}/100",
                        'advantage': article_data.get('seo_score', 80) > 75
                    }
                ],
                'summary': f"""Your article outperforms competitors:
• {len(reddit_data['pain_points'])} real user pain points from Reddit
• {article_data['word_count']:,} words vs ~{competitor_avg_words:,} average
• {article_data.get('seo_score', 80)}/100 SEO optimization
• Addresses gaps in top {len(top_results)} SERP results"""
            }
            
            return comparison
        except Exception as e:
            logger.error(f"Competitor comparison failed: {e}")
            return {
                'features': [],
                'summary': 'Comparison unavailable'
            }

# [HTML_TEMPLATE remains the same - keeping the original frontend code]
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
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); min-height: 100vh; }
        .header { background: rgba(255, 255, 255, 0.95); padding: 20px 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { font-size: 24px; font-weight: 700; color: #1e3c72; }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .input-section { background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .input-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-size: 12px; font-weight: 600; color: #666; margin-bottom: 6px; text-transform: uppercase; }
        input, select, textarea { padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #1e3c72; }
        textarea { resize: vertical; min-height: 100px; }
        .subreddit-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .chip { background: #1e3c72; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; display: inline-flex; align-items: center; gap: 5px; }
        .chip i { cursor: pointer; }
        .btn { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; border: none; padding: 14px 30px; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .tabs { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 5px 20px rgba(0,0,0,0.1); display: none; }
        .tabs.active { display: block; }
        .tab-header { display: flex; background: #f5f5f5; border-bottom: 2px solid #e0e0e0; }
        .tab-btn { flex: 1; padding: 15px; background: none; border: none; font-weight: 600; color: #666; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.3s; }
        .tab-btn.active { color: #1e3c72; background: white; border-bottom-color: #1e3c72; }
        .tab-btn i { margin-right: 8px; }
        .tab-content { display: none; padding: 30px; max-height: 600px; overflow-y: auto; }
        .tab-content.active { display: block; }
        .article-content h1 { color: #1e3c72; font-size: 32px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid #1e3c72; }
        .article-content h2 { color: #2a5298; font-size: 24px; margin: 30px 0 15px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }
        .article-content h3 { color: #333; font-size: 20px; margin: 25px 0 12px; }
        .article-content p { line-height: 1.8; margin-bottom: 15px; color: #444; }
        .article-content ul, .article-content ol { margin: 15px 0; padding-left: 30px; }
        .article-content li { margin-bottom: 8px; line-height: 1.6; }
        .article-content blockquote { border-left: 4px solid #1e3c72; padding-left: 20px; margin: 20px 0; font-style: italic; color: #555; }
        .article-content table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .article-content table th, .article-content table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .article-content table th { background: #f5f5f5; font-weight: 600; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 12px; text-align: center; }
        .metric-value { font-size: 36px; font-weight: 700; color: #1e3c72; }
        .metric-label { font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px; }
        .analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .analysis-card { background: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 4px solid #1e3c72; }
        .analysis-card h3 { color: #1e3c72; margin-bottom: 15px; font-size: 16px; }
        .pain-point { background: white; padding: 10px; margin-bottom: 10px; border-radius: 6px; font-size: 14px; border-left: 3px solid #ff6b6b; }
        .serp-result { background: white; padding: 10px; margin-bottom: 10px; border-radius: 6px; font-size: 14px; }
        .serp-result .title { font-weight: 600; color: #1e3c72; }
        .serp-result .url { color: #666; font-size: 12px; }
        .recommendation { background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #1e3c72; display: flex; justify-content: space-between; align-items: center; }
        .rec-content { flex: 1; }
        .rec-tip { font-size: 14px; margin-bottom: 5px; }
        .rec-category { display: inline-block; background: #e0e0e0; padding: 3px 8px; border-radius: 12px; font-size: 11px; color: #666; }
        .rec-impact { display: flex; gap: 2px; }
        .star { color: #ffd700; }
        .comparison-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .comparison-table th, .comparison-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        .comparison-table th { background: #f5f5f5; font-weight: 600; color: #333; }
        .comparison-table .advantage { color: #28a745; font-weight: 600; }
        .comparison-table .disadvantage { color: #dc3545; }
        .progress-container { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; display: none; }
        .progress-container.active { display: block; }
        .progress-bar { background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden; }
        .progress-fill { background: linear-gradient(135deg, #667eea, #764ba2); height: 100%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; }
        .progress-text { text-align: center; margin-top: 10px; color: #666; }
        @media (max-width: 768px) { .input-grid { grid-template-columns: 1fr; } .tab-header { flex-wrap: wrap; } .tab-btn { flex: 1 1 50%; } }
    </style>
</head>
<body>
    <div class="header"><div class="logo"><i class="fas fa-rocket"></i> SEO Article Generator - AI Content Platform</div></div>
    <div class="container">
        <div class="input-section">
            <h2 style="margin-bottom: 20px;">Generate SEO-Optimized Content</h2>
            <div class="input-grid">
                <div class="form-group"><label>Main Keyword *</label><input type="text" id="mainKeyword" placeholder="e.g., eco-friendly detergent" required></div>
                <div class="form-group"><label>Article Title *</label><input type="text" id="title" placeholder="e.g., The Ultimate Guide"></div>
                <div class="form-group"><label>Secondary Keywords</label><input type="text" id="secondaryKeywords" placeholder="keyword1, keyword2"></div>
                <div class="form-group"><label>Tone of Voice</label><select id="tone"><option value="friendly">Friendly & Conversational</option><option value="professional">Professional & Expert</option><option value="bold">Bold & Persuasive</option><option value="emotional">Emotional & Empathetic</option></select></div>
                <div class="form-group"><label>Target Country</label><select id="targetCountry"><option value="United States">United States</option><option value="United Kingdom">United Kingdom</option><option value="Canada">Canada</option><option value="Australia">Australia</option><option value="Global">Global</option></select></div>
                <div class="form-group"><label>Language</label><select id="language"><option value="en">English</option><option value="es">Spanish</option><option value="fr">French</option><option value="de">German</option></select></div>
            </div>
            <div class="form-group"><label>Subreddits to Search</label><input type="text" id="subredditInput" placeholder="Enter subreddit and press Enter"><div class="subreddit-chips" id="subredditChips"><span class="chip">r/askreddit <i class="fas fa-times" onclick="removeChip(this)"></i></span><span class="chip">r/technology <i class="fas fa-times" onclick="removeChip(this)"></i></span></div></div>
            <div class="form-group"><label>Unique Insights (Optional)</label><textarea id="uniqueInsights" placeholder="Share unique data or insights..."></textarea></div>
            <button class="btn" id="generateBtn" onclick="generateContent()"><i class="fas fa-magic"></i> Generate SEO Article</button>
        </div>
        <div class="progress-container" id="progressContainer"><div class="progress-bar"><div class="progress-fill" id="progressFill" style="width: 0%">0%</div></div><div class="progress-text" id="progressText">Initializing...</div></div>
        <div class="tabs" id="resultTabs">
            <div class="tab-header">
                <button class="tab-btn active" onclick="switchTab(event, 'article')"><i class="fas fa-file-alt"></i> Article</button>
                <button class="tab-btn" onclick="switchTab(event, 'metrics')"><i class="fas fa-chart-line"></i> Metrics</button>
                <button class="tab-btn" onclick="switchTab(event, 'recommendations')"><i class="fas fa-lightbulb"></i> Recommendations</button>
                <button class="tab-btn" onclick="switchTab(event, 'competitors')"><i class="fas fa-trophy"></i> Competitors</button>
            </div>
            <div class="tab-content active" id="articleTab"><div class="article-content" id="articleContent"></div></div>
            <div class="tab-content" id="metricsTab">
                <div class="metrics-grid">
                    <div class="metric-card"><div class="metric-value" id="wordCount">0</div><div class="metric-label">Word Count</div></div>
                    <div class="metric-card"><div class="metric-value" id="seoScore">0</div><div class="metric-label">SEO Score</div></div>
                    <div class="metric-card"><div class="metric-value" id="keywordDensity">0%</div><div class="metric-label">Keyword Density</div></div>
                    <div class="metric-card"><div class="metric-value" id="readability">N/A</div><div class="metric-label">Readability</div></div>
                    <div class="metric-card"><div class="metric-value" id="emotionalScore">0</div><div class="metric-label">Emotional Score</div></div>
                </div>
                <div class="analysis-grid">
                    <div class="analysis-card"><h3><i class="fab fa-reddit"></i> Reddit Pain Points</h3><div id="painPointsList"></div></div>
                    <div class="analysis-card"><h3><i class="fab fa-google"></i> Top SERP Results</h3><div id="serpResultsList"></div></div>
                    <div class="analysis-card"><h3><i class="fas fa-question-circle"></i> People Also Ask</h3><div id="paaList"></div></div>
                </div>
            </div>
            <div class="tab-content" id="recommendationsTab"><h3 style="margin-bottom: 20px;">SEO Improvement Recommendations</h3><div id="recommendationsList"></div></div>
            <div class="tab-content" id="competitorsTab"><h3 style="margin-bottom: 20px;">Competitor Analysis</h3><table class="comparison-table"><thead><tr><th>Feature</th><th>Top Competitors</th><th>Your Article</th><th>Advantage</th></tr></thead><tbody id="comparisonTable"></tbody></table><div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;"><h4 style="margin-bottom: 10px;">Summary</h4><div id="comparisonSummary" style="white-space: pre-wrap;"></div></div></div>
        </div>
    </div>
    <script>
        let subreddits = ['askreddit', 'technology']; let progressInterval;
        document.getElementById('subredditInput').addEventListener('keypress', function(e) { if (e.key === 'Enter') { addSubreddit(); } });
        function addSubreddit() { const input = document.getElementById('subredditInput'); const value = input.value.trim().replace('r/', '').replace('/r/', ''); if (value && !subreddits.includes(value)) { subreddits.push(value); updateSubredditChips(); input.value = ''; } }
        function removeChip(element) { const chip = element.parentElement; const subreddit = chip.textContent.replace('r/', '').trim(); subreddits = subreddits.filter(s => s !== subreddit); chip.remove(); }
        function updateSubredditChips() { const container = document.getElementById('subredditChips'); container.innerHTML = subreddits.map(s => `<span class="chip">r/${s} <i class="fas fa-times" onclick="removeChip(this)"></i></span>`).join(''); }
        function switchTab(event, tabName) { document.querySelectorAll('.tab-btn').forEach(btn => { btn.classList.remove('active'); }); event.target.closest('.tab-btn').classList.add('active'); document.querySelectorAll('.tab-content').forEach(content => { content.classList.remove('active'); }); document.getElementById(tabName + 'Tab').classList.add('active'); }
        async function generateContent() { const mainKeyword = document.getElementById('mainKeyword').value.trim(); const title = document.getElementById('title').value.trim(); if (!mainKeyword || !title) { alert('Please enter both main keyword and title'); return; } document.getElementById('progressContainer').classList.add('active'); document.getElementById('generateBtn').disabled = true; document.getElementById('resultTabs').classList.remove('active'); const data = { main_keyword: mainKeyword, title: title, secondary_keywords: document.getElementById('secondaryKeywords').value.split(',').map(k => k.trim()).filter(k => k), tone: document.getElementById('tone').value, target_country: document.getElementById('targetCountry').value, language: document.getElementById('language').value, unique_insights: document.getElementById('uniqueInsights').value, subreddits: subreddits }; try { startProgressUpdates(); const response = await fetch('/generate-seo-article', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }); const result = await response.json(); if (result.error) { alert('Error: ' + result.error); return; } displayResults(result); document.getElementById('resultTabs').classList.add('active'); } catch (error) { console.error('Error:', error); alert('Failed to generate content. Please try again.'); } finally { stopProgressUpdates(); document.getElementById('generateBtn').disabled = false; } }
        function startProgressUpdates() { progressInterval = setInterval(async () => { try { const response = await fetch('/progress'); const data = await response.json(); if (data.length > 0) { const latest = data[data.length - 1]; updateProgress(latest.percentage, latest.message); } } catch (e) { console.error('Progress update error:', e); } }, 1000); }
        function stopProgressUpdates() { if (progressInterval) { clearInterval(progressInterval); progressInterval = null; } updateProgress(100, 'Complete!'); }
        function updateProgress(percentage, text) { document.getElementById('progressFill').style.width = percentage + '%'; document.getElementById('progressFill').textContent = percentage + '%'; document.getElementById('progressText').textContent = text; }
        function displayResults(data) { document.getElementById('articleContent').innerHTML = data.article.content || '<p>No content generated</p>'; document.getElementById('wordCount').textContent = (data.metrics.word_count || 0).toLocaleString(); document.getElementById('seoScore').textContent = data.metrics.seo_score || 0; document.getElementById('keywordDensity').textContent = (data.metrics.keyword_density || 0) + '%'; document.getElementById('readability').textContent = data.metrics.readability || 'N/A'; document.getElementById('emotionalScore').textContent = data.metrics.emotional_score || 0; const painPointsHtml = data.reddit_pain_points.map(p => `<div class="pain-point">${typeof p === 'string' ? p : p.pain} ${p.subreddit ? `<small>(${p.subreddit})</small>` : ''}</div>`).join(''); document.getElementById('painPointsList').innerHTML = painPointsHtml || '<p>No pain points found</p>'; const serpHtml = data.serp_summary.top_results.map(r => `<div class="serp-result"><div class="title">${r.title}</div><div class="url">${r.url}</div><small>Strength: ${Array.isArray(r.does_well) ? r.does_well.join(', ') : r.does_well}</small><br><small>Weakness: ${r.weakness}</small></div>`).join(''); document.getElementById('serpResultsList').innerHTML = serpHtml || '<p>No SERP results</p>'; const paaHtml = data.serp_summary.people_also_ask.map(q => `<div class="serp-result">${q.question}</div>`).join(''); document.getElementById('paaList').innerHTML = paaHtml || '<p>No questions found</p>'; const recHtml = data.recommendations.map(r => `<div class="recommendation"><div class="rec-content"><div class="rec-tip">${r.tip}</div><span class="rec-category">${r.category}</span></div><div class="rec-impact">${Array(r.impact).fill('<i class="fas fa-star star"></i>').join('')}</div></div>`).join(''); document.getElementById('recommendationsList').innerHTML = recHtml || '<p>No recommendations</p>'; const comparisonHtml = data.competitor_comparison.features.map(f => `<tr><td>${f.feature}</td><td>${f.competitors}</td><td class="${f.advantage ? 'advantage' : ''}">${f.you}</td><td>${f.advantage ? '✓' : '-'}</td></tr>`).join(''); document.getElementById('comparisonTable').innerHTML = comparisonHtml; document.getElementById('comparisonSummary').textContent = data.competitor_comparison.summary; }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-seo-article', methods=['POST'])
def generate_seo_article():
    """Generate complete SEO article with all analysis (synchronous)"""
    try:
        logger.info("=== Starting SEO article generation ===")
        data = request.get_json()
        logger.info(f"Received request for keyword: {data.get('main_keyword')}")
        
        # Clear previous progress
        global progress_updates
        progress_updates = []
        
        add_progress("🚀 Starting generation process...", 5)
        
        # Initialize OpenAI
        openai_client = OpenAIClient()
        if not openai_client.available:
            return jsonify({"error": "OpenAI client not available. Please check your API key."}), 500
        
        # 1. Reddit Analysis
        logger.info("Step 1: Reddit Analysis")
        reddit_data = RedditAnalyzer.analyze(
            data['main_keyword'],
            data.get('subreddits', [])
        )
        
        # 2. SERP Analysis
        logger.info("Step 2: SERP Analysis")
        serp_data = SerpAnalyzer.analyze(data['main_keyword'])
        
        # 3. Generate Article
        logger.info("Step 3: Content Generation")
        generator = SEOContentGenerator(openai_client)
        article_data = generator.generate(data, reddit_data, serp_data)
        
        # 4. Generate Recommendations
        logger.info("Step 4: Recommendations")
        recommendations = SEORecommendationEngine.generate_recommendations(
            article_data, data, serp_data, reddit_data
        )
        
        # 5. Competitor Analysis
        logger.info("Step 5: Competitor Comparison")
        competitor_comparison = CompetitorAnalyzer.compare(
            article_data, serp_data, reddit_data, data
        )
        
        add_progress("✅ Generation complete!", 100)
        
        result = {
            "inputs": data,
            "reddit_pain_points": reddit_data['pain_points'],
            "serp_summary": {
                "top_results": serp_data['top_results'],
                "people_also_ask": serp_data['people_also_ask'],
                "related_keywords": serp_data['related_keywords'],
                "opportunities": serp_data['opportunities'],
                "gaps_analysis": serp_data.get('gaps_analysis', {})
            },
            "article": {
                "content": article_data['content'],
                "meta_description": f"Learn about {data['main_keyword']} - comprehensive guide."
            },
            "metrics": {
                "word_count": article_data['word_count'],
                "readability": article_data['readability_score'],
                "keyword_density": article_data['keyword_density'],
                "seo_score": article_data['seo_score'],
                "emotional_score": article_data.get('emotional_score', 0)
            },
            "recommendations": recommendations,
            "competitor_comparison": competitor_comparison
        }
        
        logger.info("=== Generation completed successfully ===")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500

@app.route('/progress')
def get_progress():
    """Get progress updates"""
    global progress_updates
    updates = progress_updates.copy()
    progress_updates.clear()
    return jsonify(updates)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
