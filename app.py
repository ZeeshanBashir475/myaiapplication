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
                    {"role": "system", "content": "You are an expert SEO content writer. Create engaging, well-structured HTML content using natural 'you' tone. Sound like a real person, not a bot. Blend authenticity with expert insight. Avoid filler transitions like 'in this article' or 'as we discussed'. Use data, examples, and emotional framing. Every major section should connect to a user benefit or pain relief."},
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
        raw_posts = []
        
        # Use RedditScraper if available
        if RedditScraper:
            try:
                scraper = RedditScraper()
                for subreddit in subreddits[:3]:
                    data = scraper.scrape_for_pain_points(subreddit, topic, 15)
                    
                    # Extract pain points using the extractor agent if available
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
                
                # Use PainPointHumanizer if available to make pain points more natural
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

class SerpAnalyzer:
    """Enhanced SERP analyzer with comprehensive competitor analysis"""
    
    @staticmethod
    async def analyze(keyword: str) -> Dict:
        """Comprehensive SERP analysis matching workflow requirements"""
        add_progress("🌐 Analyzing Google search results...", 30)
        
        try:
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
                "gl": "us",  # Geolocation
                "hl": "en"   # Language
            }
            
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
                
                # Analyze what this result does well and what it misses
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
            
            # Extract related searches/keywords
            related_keywords = []
            for search in data.get("related_searches", [])[:8]:
                related_keywords.append(search.get('query', ''))
            
            # Identify comprehensive opportunities
            opportunities = SerpAnalyzer._identify_comprehensive_opportunities(
                top_results, 
                people_also_ask, 
                related_keywords,
                keyword
            )
            
            # Generate competitive gaps analysis
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
        
        # Identify weaknesses/gaps
        weakness = []
        if not any(word in combined for word in ['example', 'case study', 'story']):
            weakness.append("No real examples or case studies")
        if not any(word in combined for word in ['why', 'because', 'reason']):
            weakness.append("Missing deeper 'why' explanations")
        if len(snippet) < 100:
            weakness.append("Limited preview/thin content indication")
        if not any(word in combined for word in ['comparison', 'vs', 'versus', 'compared']):
            weakness.append("No comparison content")
        if not any(word in combined for word in ['user', 'customer', 'people', 'real']):
            weakness.append("Lacks user perspective")
        if position > 3:
            weakness.append("Lower ranking indicates potential SEO gaps")
        
        # Estimate characteristics
        has_list = any(str(i) in title for i in range(1, 21))
        has_howto = 'how to' in combined or 'how-to' in combined
        has_comparison = any(word in combined for word in ['vs', 'versus', 'comparison', 'compared to'])
        
        # Estimate word count based on title complexity and snippet
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
        
        # Check what's missing in top results
        has_comparison = any(r['has_comparison'] for r in top_results)
        has_guide = any(r['has_howto'] for r in top_results)
        has_list = any(r['has_list'] for r in top_results)
        has_emotional = any(any(word in r['title'].lower() for word in ['story', 'real', 'experience', 'struggle']) 
                           for r in top_results)
        has_data = any(any(word in r['title'].lower() for word in ['statistics', 'data', 'research', 'study']) 
                      for r in top_results)
        
        # Opportunity 1: Content format gaps
        if not has_comparison:
            opportunities.append("Add detailed comparison tables - none in top 5")
        if not has_guide:
            opportunities.append("Include comprehensive step-by-step guide with visuals")
        if not has_list:
            opportunities.append("Create numbered actionable lists for better scannability")
        
        # Opportunity 2: Emotional and user-centric gaps
        if not has_emotional:
            opportunities.append("Include real user stories/testimonials from Reddit - major differentiator")
        
        # Opportunity 3: Authority and data gaps  
        if not has_data:
            opportunities.append("Add statistics, research findings, or proprietary data")
        
        # Opportunity 4: FAQ opportunities from PAA
        if paa and len(paa) >= 3:
            opportunities.append(f"Create comprehensive FAQ section - {len(paa)} 'People Also Ask' questions to address")
        
        # Opportunity 5: Visual content gaps
        opportunities.append("Add visual elements: infographics, charts, comparison tables with data")
        
        # Opportunity 6: Related keyword integration
        if related_keywords and len(related_keywords) >= 3:
            opportunities.append(f"Target {len(related_keywords)} related keywords for broader reach")
        
        # Opportunity 7: Content depth
        avg_estimate = "1,500-2,000"  # Based on typical top results
        opportunities.append(f"Competitors average {avg_estimate} words - aim for 2,400-3,600 for dominance")
        
        # Opportunity 8: Specific weaknesses from competitor analysis
        common_weaknesses = []
        for result in top_results[:3]:
            if "No real examples" in result['weakness']:
                common_weaknesses.append("examples")
            if "No comparison" in result['weakness']:
                common_weaknesses.append("comparisons")
            if "Lacks user perspective" in result['weakness']:
                common_weaknesses.append("user insights")
        
        if common_weaknesses:
            unique_weaknesses = list(set(common_weaknesses))
            opportunities.append(f"Top competitors lack: {', '.join(unique_weaknesses)} - capitalize on this")
        
        return opportunities[:10]  # Return top 10 opportunities
    
    @staticmethod
    def _identify_competitive_gaps(top_results: List[Dict], keyword: str) -> Dict:
        """Identify specific competitive gaps for strategic advantage"""
        gaps = {
            'content_format_gaps': [],
            'user_engagement_gaps': [],
            'seo_gaps': [],
            'authority_gaps': []
        }
        
        # Content format analysis
        list_count = sum(1 for r in top_results if r['has_list'])
        howto_count = sum(1 for r in top_results if r['has_howto'])
        comparison_count = sum(1 for r in top_results if r['has_comparison'])
        
        if list_count < 2:
            gaps['content_format_gaps'].append("Limited list-based content in top results")
        if howto_count < 2:
            gaps['content_format_gaps'].append("Few comprehensive how-to guides")
        if comparison_count == 0:
            gaps['content_format_gaps'].append("No comparison content - major opportunity")
        
        # User engagement gaps
        user_focused = sum(1 for r in top_results 
                          if any(word in r['title'].lower() + r['snippet'].lower() 
                                for word in ['user', 'real', 'experience', 'story', 'testimonial']))
        if user_focused < 2:
            gaps['user_engagement_gaps'].append("Minimal real user perspectives or testimonials")
        
        # SEO gaps (based on titles and snippets)
        keyword_in_title = sum(1 for r in top_results if keyword.lower() in r['title'].lower())
        if keyword_in_title < 4:
            gaps['seo_gaps'].append(f"Only {keyword_in_title}/5 top results have exact keyword in title")
        
        # Authority gaps
        has_author = sum(1 for r in top_results 
                        if any(word in r['snippet'].lower() for word in ['expert', 'author', 'by ', 'written']))
        if has_author < 2:
            gaps['authority_gaps'].append("Limited author expertise signals in top results")
        
        return gaps
    
    @staticmethod
    def _get_fallback_data(keyword: str) -> Dict:
        """Enhanced fallback SERP data"""
        return {
            'top_results': [
                {
                    'title': f"Ultimate Guide to {keyword} [2024]", 
                    'url': '#', 
                    'snippet': 'Comprehensive guide covering everything about ' + keyword,
                    'position': 1,
                    'does_well': ["Comprehensive coverage", "Current content"],
                    'weakness': "No real examples or user perspective",
                    'word_count_estimate': "2,000-2,500",
                    'has_list': False,
                    'has_howto': True,
                    'has_comparison': False
                },
                {
                    'title': f"Top 10 {keyword} Tips", 
                    'url': '#', 
                    'snippet': 'Discover the best tips and tricks for ' + keyword,
                    'position': 2,
                    'does_well': ["List-based structure", "Actionable tips"],
                    'weakness': "Too commercial, lacks depth",
                    'word_count_estimate': "1,200-1,500",
                    'has_list': True,
                    'has_howto': False,
                    'has_comparison': False
                },
                {
                    'title': f"How to Master {keyword}", 
                    'url': '#', 
                    'snippet': 'Step-by-step guide to becoming proficient with ' + keyword,
                    'position': 3,
                    'does_well': ["Instructional approach", "Clear structure"],
                    'weakness': "Generic content, no unique insights",
                    'word_count_estimate': "1,800-2,200",
                    'has_list': False,
                    'has_howto': True,
                    'has_comparison': False
                }
            ],
            'people_also_ask': [
                {'question': f"What is {keyword}?", 'snippet': f'{keyword} is a topic that many people want to understand better...'},
                {'question': f"How to use {keyword}?", 'snippet': 'Step by step guide to using ' + keyword + ' effectively...'},
                {'question': f"Why is {keyword} important?", 'snippet': f'{keyword} matters because it impacts...'},
                {'question': f"What are the benefits of {keyword}?", 'snippet': 'The main advantages include...'},
                {'question': f"How much does {keyword} cost?", 'snippet': 'Pricing varies depending on...'}
            ],
            'related_keywords': [
                f"{keyword} guide",
                f"best {keyword}",
                f"{keyword} tips",
                f"how to {keyword}",
                f"{keyword} for beginners",
                f"{keyword} examples"
            ],
            'opportunities': [
                "Add detailed comparison tables - none in top results",
                "Include real user testimonials from Reddit",
                "Add visual guides and infographics",
                "Create comprehensive FAQ section",
                "Include proprietary data or research",
                "Add step-by-step tutorials with screenshots",
                "Target long-tail related keywords"
            ],
            'gaps_analysis': {
                'content_format_gaps': ["Limited list-based content", "No comparison content"],
                'user_engagement_gaps': ["Minimal real user perspectives"],
                'seo_gaps': ["Keyword optimization opportunities"],
                'authority_gaps': ["Limited author expertise signals"]
            },
            'total_results': 'Fallback mode',
            'search_time': 'N/A'
        }

class SEOContentGenerator:
    """Generate SEO-optimized content"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
    
    async def generate(self, inputs: Dict, reddit_data: Dict, serp_data: Dict) -> Dict:
        """Generate full SEO article matching workflow requirements"""
        add_progress("✍️ Generating SEO-optimized article...", 50)
        
        # Build comprehensive prompt based on workflow
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
SEO Gaps: {', '.join(gaps.get('seo_gaps', []))}
Authority Gaps: {', '.join(gaps.get('authority_gaps', []))}
"""
        
        prompt = f"""
Create a comprehensive, SEO-optimized article about "{inputs['main_keyword']}"

ARTICLE DETAILS:
Title: {inputs.get('title', inputs['main_keyword'])}
Main Keyword: {inputs['main_keyword']}
Secondary Keywords: {', '.join(inputs.get('secondary_keywords', []))}
Tone: {inputs.get('tone', 'Professional yet friendly')}
Target Audience: {inputs.get('target_country', 'Global')}

REDDIT PAIN POINTS TO ADDRESS (Make these emotional hooks throughout):
{pain_points_text}

COMPETITOR ANALYSIS (Top 3 Results):
{competitor_analysis}

{gaps_text}

PEOPLE ALSO ASK (Must include in FAQ section):
{paa_text}

CONTENT OPPORTUNITIES TO IMPLEMENT:
{opportunities_text}

USER'S UNIQUE INSIGHTS (Integrate naturally):
{inputs.get('unique_insights', 'No additional insights provided - focus on Reddit pain points and SERP gaps')}

CRITICAL WRITING REQUIREMENTS:
1. Write 2,400-3,600 words (aim for 2,800+ to beat competitors)
2. Start with an EMOTIONAL HOOK - choose one:
   - A powerful question that triggers curiosity
   - A relatable story from Reddit pain points
   - A surprising statistic
   - An emotional setup that connects with reader struggles
3. Use natural "you" tone throughout - sound like a real person, NOT a bot
4. Address each Reddit pain point naturally in the content
5. Include ALL People Also Ask questions in a dedicated FAQ section
6. Use main keyword 5-8 times naturally throughout
7. Integrate secondary keywords: {', '.join(inputs.get('secondary_keywords', []))} 
8. Add comparison tables where competitors lack them
9. Include real user quotes from Reddit (paraphrased from pain points)
10. NO filler transitions like "in this article" or "as we discussed"
11. Every section must connect to a user benefit or pain relief
12. End with a strong, actionable call-to-action

CONTENT STRUCTURE (Use proper HTML):
<h1>Main Title (Include main keyword)</h1>

<div class="intro">
[Emotional hook - 2-3 paragraphs that immediately connect with reader's pain]
[Brief preview of what they'll learn and why it matters]
</div>

<h2>Section 1: [Address major pain point]</h2>
[3-4 paragraphs with examples]
[Include a real Reddit quote]

<h2>Section 2: [Cover opportunity from SERP gaps]</h2>
[Use comparison table if competitors lack it]

<h2>Section 3: [Address another pain point]</h2>
[Case study or example]

[Continue with 4-6 more H2 sections covering:
- How-to guidance
- Common mistakes
- Best practices
- Real examples
- Unique insights user provided]

<h2>Frequently Asked Questions</h2>
[Include ALL People Also Ask questions as H3 subsections]
<h3>Question 1</h3>
<p>Answer...</p>

<h2>Conclusion</h2>
[Summarize key takeaways]
[Strong call-to-action]

HTML FORMATTING RULES:
- Use <h1> for main title (only once)
- Use <h2> for major sections (6-8 sections)
- Use <h3> for subsections and FAQs
- Use <p> for all paragraphs
- Use <ul> and <li> for bulleted lists (use sparingly)
- Use <ol> and <li> for numbered lists
- Use <strong> for key emphasis (don't overuse)
- Use <blockquote> for Reddit quotes or important callouts
- Use <table> for comparison data

TONE GUIDELINES:
- Conversational but authoritative
- Use "you" and "your" frequently
- Include rhetorical questions
- Show empathy for pain points
- Be specific with examples
- Avoid jargon unless you explain it
- Use active voice
- Write like you're helping a friend

Write the complete article NOW. Make it exceptional:
"""
        
        # Generate article
        article = await self.openai_client.generate_seo_article(prompt, max_tokens=4000)
        
        # Calculate comprehensive metrics
        word_count = len(article.split())
        keyword_density = (article.lower().count(inputs['main_keyword'].lower()) / word_count) * 100 if word_count > 0 else 0
        
        # Count secondary keyword usage
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
    
    def _calculate_readability(self, text: str) -> str:
        """Calculate readability score"""
        # Remove HTML tags for accurate word count
        clean_text = re.sub(r'<[^>]+>', '', text)
        sentences = len(re.split(r'[.!?]+', clean_text))
        words = len(clean_text.split())
        
        if sentences == 0:
            return "N/A"
        
        avg_words_per_sentence = words / sentences
        
        if avg_words_per_sentence < 15:
            return "Easy (Grade 6-8)"
        elif avg_words_per_sentence < 20:
            return "Medium (Grade 9-10)"
        else:
            return "Complex (Grade 11+)"
    
    def _calculate_seo_score(self, content: str, inputs: Dict, serp_data: Dict) -> int:
        """Calculate comprehensive SEO score (0-100)"""
        score = 0
        
        # Structure checks (40 points max)
        if '<h1>' in content: score += 10
        h2_count = content.count('<h2>')
        if h2_count >= 5: score += 10
        elif h2_count >= 3: score += 5
        if '<h3>' in content: score += 5
        if 'FAQ' in content or 'Frequently Asked Questions' in content: score += 10
        if '<table>' in content: score += 5
        
        # Keyword optimization (30 points max)
        main_keyword_lower = inputs['main_keyword'].lower()
        content_lower = content.lower()
        
        if main_keyword_lower in content_lower:
            keyword_count = content_lower.count(main_keyword_lower)
            if 5 <= keyword_count <= 12: score += 15
            elif keyword_count > 0: score += 8
        
        # Secondary keywords
        secondary_keywords = inputs.get('secondary_keywords', [])
        if secondary_keywords:
            found_secondary = sum(1 for kw in secondary_keywords if kw.lower() in content_lower)
            score += min(15, found_secondary * 5)
        
        # Content quality (30 points max)
        word_count = len(content.split())
        if word_count >= 2400: score += 15
        elif word_count >= 1800: score += 10
        elif word_count >= 1200: score += 5
        
        # Has lists
        if '<ul>' in content or '<ol>' in content: score += 5
        
        # Has blockquotes (user testimonials)
        if '<blockquote>' in content: score += 5
        
        # Has strong emphasis
        if '<strong>' in content: score += 5
        
        return min(100, score)
    
    def _calculate_emotional_score(self, content: str, reddit_data: Dict) -> int:
        """Calculate emotional resonance score"""
        score = 0
        content_lower = content.lower()
        
        # Check if pain points are addressed
        pain_points = reddit_data.get('pain_points', [])
        for pain in pain_points[:5]:
            pain_text = pain.get('pain', '').lower()
            # Check if key words from pain point appear in content
            pain_words = [w for w in pain_text.split() if len(w) > 4]
            if pain_words and any(word in content_lower for word in pain_words[:3]):
                score += 10
        
        # Emotional indicators
        emotional_words = ['struggle', 'frustrated', 'worried', 'confused', 'challenge', 
                          'breakthrough', 'success', 'relief', 'peace of mind']
        emotional_count = sum(1 for word in emotional_words if word in content_lower)
        score += min(30, emotional_count * 5)
        
        # Question usage (engagement)
        question_count = content.count('?')
        score += min(20, question_count * 2)
        
        return min(100, score)

class SEORecommendationEngine:
    """Generate SEO recommendations like SEMrush/SurferSEO"""
    
    @staticmethod
    async def generate_recommendations(article_data: Dict, inputs: Dict, 
                                      serp_data: Dict, reddit_data: Dict) -> List[Dict]:
        """Generate actionable SEO recommendations"""
        add_progress("📊 Generating SEO recommendations...", 80)
        
        recommendations = []
        
        # Keyword recommendations
        if article_data['keyword_density'] < 1:
            recommendations.append({
                'tip': f"Increase usage of main keyword '{inputs['main_keyword']}' to 1-2% density (currently {article_data['keyword_density']}%)",
                'impact': 5,
                'category': 'SEO'
            })
        elif article_data['keyword_density'] > 3:
            recommendations.append({
                'tip': f"Reduce keyword stuffing - current density is {article_data['keyword_density']}% (aim for 1-2%)",
                'impact': 4,
                'category': 'SEO'
            })
        else:
            recommendations.append({
                'tip': f"Keyword density is optimal at {article_data['keyword_density']}% - maintain this balance",
                'impact': 3,
                'category': 'SEO'
            })
        
        # Secondary keyword usage
        if article_data.get('secondary_keyword_count', 0) < len(inputs.get('secondary_keywords', [])):
            recommendations.append({
                'tip': f"Integrate more secondary keywords - currently using {article_data.get('secondary_keyword_count', 0)} out of {len(inputs.get('secondary_keywords', []))} provided",
                'impact': 4,
                'category': 'SEO'
            })
        
        # Content length recommendations
        if article_data['word_count'] < 2400:
            recommendations.append({
                'tip': f"Expand content to 2,400+ words (current: {article_data['word_count']}) to match top competitors",
                'impact': 5,
                'category': 'Content'
            })
        elif article_data['word_count'] > 3600:
            recommendations.append({
                'tip': f"Consider breaking this {article_data['word_count']}-word article into a series or adding a table of contents",
                'impact': 3,
                'category': 'UX'
            })
        
        # Emotional depth recommendations
        emotional_score = article_data.get('emotional_score', 50)
        if emotional_score < 60:
            recommendations.append({
                'tip': "Add more emotional hooks - include a personal story or Reddit user quote in the introduction",
                'impact': 5,
                'category': 'Emotional Depth'
            })
            recommendations.append({
                'tip': f"Address more Reddit pain points in the content - currently scoring {emotional_score}/100 on emotional resonance",
                'impact': 4,
                'category': 'Emotional Depth'
            })
        
        # SERP-based recommendations
        if serp_data.get('gaps_analysis'):
            gaps = serp_data['gaps_analysis']
            
            if gaps.get('content_format_gaps'):
                recommendations.append({
                    'tip': f"Add missing content formats: {', '.join(gaps['content_format_gaps'][:2])}",
                    'impact': 5,
                    'category': 'Content'
                })
            
            if gaps.get('user_engagement_gaps'):
                recommendations.append({
                    'tip': "Increase user engagement with real testimonials, case studies, or Reddit quotes",
                    'impact': 4,
                    'category': 'Emotional Depth'
                })
        
        # Technical SEO
        recommendations.append({
            'tip': "Add schema markup (FAQ schema, Article schema) to improve SERP visibility",
            'impact': 4,
            'category': 'Technical SEO'
        })
        
        # Readability
        readability = article_data.get('readability_score', '')
        if 'Complex' in readability:
            recommendations.append({
                'tip': "Simplify complex sentences - aim for 15-20 words per sentence for better readability",
                'impact': 4,
                'category': 'Readability'
            })
        
        # Visual elements
        recommendations.append({
            'tip': "Add 4-6 relevant images with descriptive alt text containing target keywords",
            'impact': 4,
            'category': 'UX'
        })
        
        # Internal linking
        recommendations.append({
            'tip': "Add 3-5 internal links to related content on your site to improve site architecture",
            'impact': 3,
            'category': 'SEO'
        })
        
        # External authority
        recommendations.append({
            'tip': "Add 2-3 authoritative external links to credible sources (research papers, gov sites)",
            'impact': 3,
            'category': 'Authority'
        })
        
        # CTA optimization
        recommendations.append({
            'tip': "Place a mid-article CTA after addressing the main pain point (around 40% scroll depth)",
            'impact': 4,
            'category': 'Conversion'
        })
        
        # Content freshness
        recommendations.append({
            'tip': f"Update content every 3-6 months with latest data and examples to maintain rankings",
            'impact': 3,
            'category': 'SEO'
        })
        
        # Sort by impact and return top recommendations
        recommendations.sort(key=lambda x: x['impact'], reverse=True)
        return recommendations[:12]

class CompetitorAnalyzer:
    """Analyze and compare with competitors"""
    
    @staticmethod
    async def compare(article_data: Dict, serp_data: Dict, reddit_data: Dict, inputs: Dict) -> Dict:
        """Compare with top competitors"""
        add_progress("🏆 Analyzing competitor comparison...", 90)
        
        # Get competitor averages
        top_results = serp_data.get('top_results', [])
        competitor_avg_words = 1800  # Default estimate
        
        if top_results:
            # Estimate average from word count estimates
            word_estimates = []
            for result in top_results[:3]:
                estimate = result.get('word_count_estimate', '1,500-2,000')
                # Extract average from range
                nums = re.findall(r'\d+', estimate.replace(',', ''))
                if len(nums) >= 2:
                    avg = (int(nums[0]) + int(nums[1])) // 2
                    word_estimates.append(avg)
            if word_estimates:
                competitor_avg_words = sum(word_estimates) // len(word_estimates)
        
        # Create comparison table
        comparison = {
            'features': [
                {
                    'feature': 'Word Count',
                    'competitors': f'Average {competitor_avg_words:,} words',
                    'you': f"{article_data['word_count']:,} words",
                    'advantage': article_data['word_count'] > competitor_avg_words
                },
                {
                    'feature': 'Emotional Engagement',
                    'competitors': 'Generic content, no user perspective',
                    'you': f"Uses {len(reddit_data['pain_points'])} real Reddit pain points",
                    'advantage': True
                },
                {
                    'feature': 'Keyword Optimization',
                    'competitors': 'Basic keyword usage',
                    'you': f"{article_data['keyword_density']}% main + {article_data.get('secondary_keyword_count', 0)} secondary keywords",
                    'advantage': article_data['keyword_density'] >= 1 and article_data['keyword_density'] <= 2.5
                },
                {
                    'feature': 'Unique Insights',
                    'competitors': 'Rehashed information',
                    'you': 'Reddit insights + SERP gap analysis + user data',
                    'advantage': True
                },
                {
                    'feature': 'Content Structure',
                    'competitors': 'Standard blog format',
                    'you': 'FAQ + Tables + Examples + Reddit quotes',
                    'advantage': True
                },
                {
                    'feature': 'Readability',
                    'competitors': 'Variable, often complex',
                    'you': article_data.get('readability_score', 'Optimized'),
                    'advantage': 'Easy' in article_data.get('readability_score', '') or 'Medium' in article_data.get('readability_score', '')
                },
                {
                    'feature': 'SEO Score',
                    'competitors': '60-75/100 (estimated)',
                    'you': f"{article_data.get('seo_score', 80)}/100",
                    'advantage': article_data.get('seo_score', 80) > 75
                },
                {
                    'feature': 'Emotional Resonance',
                    'competitors': 'Low, generic tone',
                    'you': f"{article_data.get('emotional_score', 70)}/100",
                    'advantage': article_data.get('emotional_score', 70) > 60
                }
            ],
            'summary': f"""Your article outperforms competitors in multiple key areas:

• **Emotional Connection**: Integrates {len(reddit_data['pain_points'])} real user pain points from Reddit, creating authentic emotional hooks that competitors lack

• **Content Depth**: {article_data['word_count']:,} words of comprehensive coverage vs. competitor average of ~{competitor_avg_words:,} words

• **SEO Optimization**: Achieving {article_data.get('seo_score', 80)}/100 SEO score with optimal keyword density of {article_data['keyword_density']}%

• **Competitive Gaps Addressed**: Successfully addresses {len(serp_data.get('opportunities', []))} opportunities identified in top {len(top_results)} SERP results

• **Unique Value**: Combines Reddit authenticity, SERP research, and {('user-provided insights' if inputs.get('unique_insights') else 'data-driven analysis')} that competitors don't have

• **User Experience**: {article_data.get('readability_score', 'Optimized')} readability makes complex topics accessible

**Competitive Advantage**: Your content differentiates through emotional storytelling, comprehensive research, and addressing real user pain points - not just SEO-optimized fluff."""
        }
        
        return comparison

# HTML Template (same as before, no changes needed to the frontend)
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
        
        .article-content blockquote {
            border-left: 4px solid #1e3c72;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
        }
        
        .article-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .article-content table th,
        .article-content table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        .article-content table th {
            background: #f5f5f5;
            font-weight: 600;
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
                flex-wrap: wrap;
            }
            
            .tab-btn {
                flex: 1 1 50%;
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
                    <div class="metric-card">
                        <div class="metric-value" id="emotionalScore">0</div>
                        <div class="metric-label">Emotional Score</div>
                    </div>
                </div>
                
                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h3><i class="fab fa-reddit"></i> Reddit Pain Points</h3>
                        <div id="painPointsList"></div>
                    </div>
                    <div class="analysis-card">
                        <h3><i class="fab fa-google"></i> Top SERP Results</h3>
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
                    <div id="comparisonSummary" style="white-space: pre-wrap;"></div>
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
            event.target.closest('.tab-btn').classList.add('active');
            
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
            document.getElementById('resultTabs').classList.remove('active');
            
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
            document.getElementById('wordCount').textContent = (data.metrics.word_count || 0).toLocaleString();
            document.getElementById('seoScore').textContent = data.metrics.seo_score || 0;
            document.getElementById('keywordDensity').textContent = (data.metrics.keyword_density || 0) + '%';
            document.getElementById('readability').textContent = data.metrics.readability || 'N/A';
            document.getElementById('emotionalScore').textContent = data.metrics.emotional_score || 0;
            
            // Display Reddit pain points
            const painPointsHtml = data.reddit_pain_points.map(p => 
                `<div class="pain-point">${typeof p === 'string' ? p : p.pain} ${p.subreddit ? `<small>(${p.subreddit})</small>` : ''}</div>`
            ).join('');
            document.getElementById('painPointsList').innerHTML = painPointsHtml || '<p>No pain points found</p>';
            
            // Display SERP results
            const serpHtml = data.serp_summary.top_results.map(r => 
                `<div class="serp-result">
                    <div class="title">${r.title}</div>
                    <div class="url">${r.url}</div>
                    <small>Strength: ${Array.isArray(r.does_well) ? r.does_well.join(', ') : r.does_well}</small><br>
                    <small>Weakness: ${r.weakness}</small>
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
        
        # Clear previous progress
        global progress_updates
        progress_updates = []
        
        # Initialize OpenAI
        openai_client = OpenAIClient()
        
        # 1. Reddit Analysis
        reddit_data = await RedditAnalyzer.analyze(
            data['main_keyword'],
            data.get('subreddits', [])
        )
        
        # 2. SERP Analysis (Enhanced)
        serp_data = await SerpAnalyzer.analyze(data['main_keyword'])
        
        # 3. Generate Article
        generator = SEOContentGenerator(openai_client)
        article_data = await generator.generate(data, reddit_data, serp_data)
        
        # 4. Generate Recommendations
        recommendations = await SEORecommendationEngine.generate_recommendations(
            article_data, data, serp_data, reddit_data
        )
        
        # 5. Competitor Analysis
        competitor_comparison = await CompetitorAnalyzer.compare(
            article_data, serp_data, reddit_data, data
        )
        
        add_progress("✅ Generation complete!", 100)
        
        return jsonify({
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
                "meta_description": f"Learn about {data['main_keyword']} - comprehensive guide covering everything you need to know."
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
