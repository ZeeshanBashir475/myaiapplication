import json
import re
import os
import time
from typing import Dict, List, Any, Optional
from collections import Counter
from datetime import datetime
import logging

# Try to import Reddit dependencies
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logging.warning("PRAW not installed. Install with: pip install praw")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic not installed. Install with: pip install anthropic")

logger = logging.getLogger(__name__)

class EnhancedRedditResearcher:
    """Enhanced Reddit Researcher focused on pain point analysis"""
    
    def __init__(self):
        self.reddit_client = self._initialize_reddit_client()
        self.anthropic_client = self._initialize_anthropic()
        logger.info("✅ Enhanced Reddit Researcher initialized")
        
    def _initialize_reddit_client(self):
        """Initialize Reddit client with fallback data generation"""
        if not PRAW_AVAILABLE:
            logger.warning("PRAW not available, using fallback data generator")
            return None
        
        try:
            # Create Reddit client directly
            reddit_client = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'PainPointBot/1.0')
            )
            
            # Test connection
            test_subreddit = reddit_client.subreddit('test')
            next(test_subreddit.hot(limit=1))
            logger.info("✅ Reddit API connection successful")
            return reddit_client
            
        except Exception as e:
            logger.warning(f"Reddit client initialization failed: {e}")
            return None
    
    def _initialize_anthropic(self):
        """Initialize Anthropic client for enhanced pain point extraction"""
        if not ANTHROPIC_AVAILABLE:
            return None
        
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                return Anthropic(api_key=api_key)
        except Exception as e:
            logger.warning(f"Anthropic client initialization failed: {e}")
        return None
    
    def research_topic_comprehensive(self, topic: str, subreddits: List[str], 
                                   max_posts_per_subreddit: int = 15) -> Dict[str, Any]:
        """Comprehensive Reddit research focused on pain point analysis"""
        
        logger.info(f"🔍 Starting Reddit research for: {topic}")
        
        all_reddit_data = []
        subreddit_insights = {}
        
        for subreddit in subreddits:
            logger.info(f"📊 Analyzing r/{subreddit}...")
            posts = self._search_subreddit(subreddit, topic, max_posts_per_subreddit)
            
            if posts:
                analyzed_posts = self._analyze_posts_for_pain_points(posts, topic)
                all_reddit_data.extend(analyzed_posts)
                subreddit_insights[subreddit] = self._analyze_subreddit_specific(analyzed_posts, subreddit)
        
        if not all_reddit_data:
            return self._generate_fallback_analysis(topic)
        
        # Perform deep pain point analysis
        pain_point_analysis = self._perform_pain_point_analysis(all_reddit_data, topic)
        
        # Add subreddit breakdown
        pain_point_analysis['subreddit_breakdown'] = subreddit_insights
        pain_point_analysis['research_metadata'] = self._calculate_research_metadata(all_reddit_data)
        
        logger.info(f"✅ Completed analysis of {len(all_reddit_data)} posts")
        return pain_point_analysis
    
    def _search_subreddit(self, subreddit: str, topic: str, limit: int = 15) -> List[Dict]:
        """Search subreddit with realistic fallback data"""
        
        if self.reddit_client:
            try:
                # Use real Reddit API
                real_posts = self._extract_real_reddit_posts(subreddit, topic, limit)
                if real_posts:
                    logger.info(f"✅ Found {len(real_posts)} real posts from r/{subreddit}")
                    return real_posts
                else:
                    logger.info(f"No real posts found in r/{subreddit}, using fallback")
            except Exception as e:
                logger.warning(f"Reddit API failed for r/{subreddit}: {e}")
        
        # Generate realistic Reddit posts for analysis (your original fallback)
        return self._generate_realistic_fallback_posts(subreddit, topic, limit)
    
    def _extract_real_reddit_posts(self, subreddit_name: str, topic: str, limit: int) -> List[Dict]:
        """Extract real posts from Reddit using PRAW"""
        
        posts = []
        
        try:
            subreddit = self.reddit_client.subreddit(subreddit_name)
            
            # Try multiple search strategies
            search_methods = [
                ('search', topic, 'relevance'),
                ('search', topic, 'new'),
                ('hot', None, None)
            ]
            
            for method, query, sort in search_methods:
                try:
                    if method == 'search' and query:
                        submissions = subreddit.search(
                            query, 
                            sort=sort, 
                            time_filter='month', 
                            limit=limit
                        )
                    else:
                        submissions = subreddit.hot(limit=limit // 2)
                    
                    for submission in submissions:
                        if len(posts) >= limit:
                            break
                        
                        # Filter low-quality posts
                        if (submission.score < 3 or 
                            len(submission.title) < 15 or
                            submission.over_18):
                            continue
                        
                        # Get comments
                        comments = self._extract_comments_from_submission(submission)
                        
                        post = {
                            'title': submission.title,
                            'content': submission.selftext if submission.is_self else '',
                            'score': submission.score,
                            'subreddit': subreddit_name,
                            'comments': comments,
                            'url': f"https://reddit.com{submission.permalink}",
                            'created_utc': submission.created_utc
                        }
                        
                        posts.append(post)
                    
                    if posts:  # If we found posts, stop trying other methods
                        break
                        
                except Exception as e:
                    logger.warning(f"Search method {method} failed: {e}")
                    continue
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to search r/{subreddit_name}: {e}")
        
        return posts
    
    def _extract_comments_from_submission(self, submission, max_comments: int = 10) -> List[Dict]:
        """Extract comments from Reddit submission"""
        comments = []
        
        try:
            submission.comments.replace_more(limit=0)
            
            for comment in submission.comments.list()[:max_comments]:
                if (hasattr(comment, 'body') and 
                    len(comment.body) > 20 and 
                    comment.score > 1):
                    
                    comments.append({
                        'text': comment.body,
                        'score': comment.score,
                        'author': str(comment.author) if comment.author else 'deleted'
                    })
                    
        except Exception as e:
            logger.warning(f"Failed to extract comments: {e}")
        
        return comments
    
    def _generate_realistic_fallback_posts(self, subreddit: str, topic: str, limit: int) -> List[Dict]:
        """Generate realistic Reddit posts for analysis (your original method)"""
        
        posts = []
        
        # Pain point focused post templates
        pain_point_templates = [
            f"Struggling with {topic} - need help",
            f"Anyone else having issues with {topic}?",
            f"{topic} is so confusing, what am I missing?",
            f"Failed at {topic} multiple times, advice needed",
            f"Why is {topic} so complicated?",
            f"Made a mistake with {topic}, how to fix?",
            f"Overwhelmed by {topic} options",
            f"Is {topic} worth the hassle?",
            f"Common {topic} problems?",
            f"What I wish I knew about {topic}",
            f"Don't make my {topic} mistakes",
            f"How to avoid {topic} pitfalls?",
            f"Frustrated with {topic} results",
            f"Time-consuming {topic} issues",
            f"Budget concerns with {topic}"
        ]
        
        # Pain-focused content templates
        content_templates = [
            f"I've been trying to figure out {topic} for weeks but keep hitting roadblocks. The information online is so scattered and contradictory. Has anyone else experienced this frustration?",
            f"Spent way too much money on the wrong {topic} solution. Wish I had done more research first. What red flags should I have watched for?",
            f"Every expert says something different about {topic}. How do you know who to trust? I'm completely overwhelmed by conflicting advice.",
            f"Made the classic beginner mistake with {topic}. Now I'm stuck and don't know how to move forward. Anyone been in this situation?",
            f"The learning curve for {topic} is steeper than I expected. Feeling like giving up. How did others push through the initial difficulties?",
            f"Hidden costs of {topic} are killing my budget. Why doesn't anyone mention these upfront? What should I budget for realistically?",
            f"Time investment for {topic} is much higher than advertised. How do busy people make this work? Any efficiency tips?",
            f"Customer support for my {topic} solution is terrible. Waiting weeks for responses. How do you get proper help when things go wrong?"
        ]
        
        # Pain point comments
        pain_comment_templates = [
            "Same problem here! Been struggling for months",
            "That's exactly what happened to me. So frustrating!",
            "I made the same mistake. Here's what I learned...",
            "Don't give up! It gets easier after you figure out...",
            "I wasted so much money before finding the right approach",
            "The biggest issue is that nobody explains...",
            "What worked for me was starting with...",
            "Avoid XYZ at all costs. Terrible experience"
        ]
        
        for i in range(min(limit, len(pain_point_templates))):
            # Create realistic posts focused on pain points
            title = pain_point_templates[i]
            content = content_templates[i % len(content_templates)]
            
            # Generate realistic engagement
            score = 15 + (i * 2)  # Realistic scores
            comment_count = 3 + (i % 8)  # 3-10 comments
            
            # Generate pain-focused comments
            comments = []
            for j in range(comment_count):
                comments.append({
                    'text': pain_comment_templates[j % len(pain_comment_templates)],
                    'score': 2 + j,
                    'author': f'user_{j+1}'
                })
            
            post = {
                'title': title,
                'content': content,
                'score': score,
                'subreddit': subreddit,
                'comments': comments,
                'url': f'https://reddit.com/r/{subreddit}/post_{i+1}',
                'created_utc': datetime.now().timestamp() - (i * 3600)
            }
            
            posts.append(post)
        
        logger.info(f"✅ Generated {len(posts)} pain point focused posts for r/{subreddit}")
        return posts
    
    def _analyze_posts_for_pain_points(self, posts: List[Dict], topic: str) -> List[Dict]:
        """Analyze posts specifically for pain points and customer struggles"""
        
        analyzed_posts = []
        
        for post in posts:
            analyzed_post = post.copy()
            
            # Enhanced pain point analysis using Claude if available
            if self.anthropic_client:
                analyzed_post['ai_pain_analysis'] = self._extract_pain_points_with_claude(post, topic)
            
            # Core pain point analysis (your original methods)
            analyzed_post['pain_point_indicators'] = self._identify_pain_points(post)
            analyzed_post['frustration_level'] = self._assess_frustration_level(post)
            analyzed_post['problem_category'] = self._categorize_problem(post, topic)
            analyzed_post['urgency_signals'] = self._detect_urgency_signals(post)
            analyzed_post['cost_concerns'] = self._extract_cost_concerns(post)
            analyzed_post['time_pressure'] = self._identify_time_pressure(post)
            analyzed_post['topic_relevance'] = self._calculate_topic_relevance(post, topic)
            
            # Comment analysis for pain points
            if post.get('comments'):
                analyzed_post['comment_pain_analysis'] = self._analyze_comments_for_pain(post['comments'])
            
            analyzed_posts.append(analyzed_post)
        
        return analyzed_posts
    
    def _extract_pain_points_with_claude(self, post: Dict, topic: str) -> Dict[str, Any]:
        """Extract pain points using Claude API for enhanced analysis"""
        
        try:
            post_text = f"Title: {post.get('title', '')}\nContent: {post.get('content', '')}"
            
            # Add top comments for context
            if post.get('comments'):
                comment_text = "\n".join([f"Comment: {c['text']}" for c in post['comments'][:3]])
                post_text += f"\n\nTop Comments:\n{comment_text}"
            
            prompt = f"""Analyze this Reddit post about {topic} for pain points and frustrations.

Post content:
---
{post_text}
---

Extract specific pain points from this post. For each pain point:
1. Identify the specific problem or frustration
2. Categorize it (confusion, frustration, cost_concern, time_pressure, complexity, poor_support, reliability_issue)
3. Rate intensity 1-10 (10 = extreme pain/frustration)

Return ONLY a JSON array in this format:
[
  {{"text": "specific pain point description", "category": "category_name", "intensity": 7}}
]

If no clear pain points exist, return: []"""

            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=400,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            try:
                pain_points_data = json.loads(response_text)
                return {
                    'claude_pain_points': pain_points_data,
                    'claude_analysis_success': True,
                    'total_ai_pain_points': len(pain_points_data)
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Claude response: {response_text[:100]}")
                return {'claude_analysis_success': False, 'error': 'JSON parse failed'}
                
        except Exception as e:
            logger.warning(f"Claude analysis failed: {e}")
            return {'claude_analysis_success': False, 'error': str(e)}
    
    def _identify_pain_points(self, post: Dict) -> Dict[str, Any]:
        """Identify specific pain points in the post"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        pain_indicators = {
            'confusion': ['confused', 'lost', 'don\'t understand', 'unclear', 'complicated'],
            'frustration': ['frustrated', 'annoying', 'terrible', 'awful', 'hate'],
            'overwhelm': ['overwhelmed', 'too many', 'too much', 'can\'t decide'],
            'time_waste': ['wasted time', 'taking forever', 'slow', 'time consuming'],
            'money_waste': ['wasted money', 'expensive', 'overpriced', 'budget'],
            'complexity': ['too complex', 'difficult', 'hard', 'complicated'],
            'poor_support': ['no support', 'bad service', 'unhelpful', 'ignored'],
            'unreliable': ['doesn\'t work', 'broken', 'unreliable', 'buggy']
        }
        
        detected_pain_points = {}
        pain_score = 0
        
        for category, indicators in pain_indicators.items():
            count = sum(1 for indicator in indicators if indicator in text)
            if count > 0:
                detected_pain_points[category] = count
                pain_score += count
        
        return {
            'detected_pain_points': detected_pain_points,
            'pain_score': pain_score,
            'has_significant_pain': pain_score >= 2
        }
    
    def _assess_frustration_level(self, post: Dict) -> Dict[str, Any]:
        """Assess the level of frustration in the post"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        # Frustration indicators with weights
        frustration_words = {
            'mild': ['annoying', 'bothering', 'slightly', 'bit confused'],
            'moderate': ['frustrated', 'struggling', 'difficult', 'problems'],
            'severe': ['hate', 'terrible', 'awful', 'worst', 'giving up']
        }
        
        frustration_score = 0
        level = 'low'
        
        for severity, words in frustration_words.items():
            count = sum(1 for word in words if word in text)
            if severity == 'mild' and count > 0:
                frustration_score += count * 1
            elif severity == 'moderate' and count > 0:
                frustration_score += count * 2
                level = 'moderate'
            elif severity == 'severe' and count > 0:
                frustration_score += count * 3
                level = 'high'
        
        return {
            'frustration_score': frustration_score,
            'frustration_level': level,
            'emotional_intensity': min(10, frustration_score)
        }
    
    def _categorize_problem(self, post: Dict, topic: str) -> str:
        """Categorize the type of problem mentioned"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        problem_categories = {
            'learning_curve': ['hard to learn', 'difficult', 'steep curve', 'confusing'],
            'cost_issues': ['expensive', 'cost', 'budget', 'money', 'price'],
            'time_constraints': ['no time', 'too long', 'time consuming', 'quick'],
            'complexity': ['complex', 'complicated', 'overwhelming', 'too much'],
            'poor_quality': ['bad quality', 'doesn\'t work', 'broken', 'unreliable'],
            'lack_of_support': ['no help', 'no support', 'bad service', 'ignored'],
            'wrong_choice': ['wrong choice', 'mistake', 'regret', 'should have'],
            'comparison_confusion': ['too many options', 'can\'t decide', 'what to choose']
        }
        
        for category, indicators in problem_categories.items():
            if any(indicator in text for indicator in indicators):
                return category
        
        return 'general_dissatisfaction'
    
    def _detect_urgency_signals(self, post: Dict) -> List[str]:
        """Detect urgency signals in the post"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        urgency_signals = [
            'urgent', 'asap', 'quickly', 'immediately', 'need help now',
            'deadline', 'running out of time', 'emergency', 'critical'
        ]
        
        detected_signals = [signal for signal in urgency_signals if signal in text]
        return detected_signals
    
    def _extract_cost_concerns(self, post: Dict) -> Dict[str, Any]:
        """Extract cost-related concerns"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        cost_indicators = {
            'budget_constraints': ['tight budget', 'can\'t afford', 'too expensive', 'cheap option'],
            'hidden_costs': ['hidden cost', 'unexpected fee', 'additional charge'],
            'value_concerns': ['worth it', 'value for money', 'overpriced', 'ripoff'],
            'comparison_shopping': ['compare prices', 'best deal', 'cheapest', 'most affordable']
        }
        
        detected_concerns = {}
        for category, indicators in cost_indicators.items():
            if any(indicator in text for indicator in indicators):
                detected_concerns[category] = True
        
        return detected_concerns
    
    def _identify_time_pressure(self, post: Dict) -> Dict[str, Any]:
        """Identify time-related pressure points"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        time_indicators = [
            'no time', 'too long', 'time consuming', 'quick solution',
            'fast', 'immediately', 'busy', 'deadline'
        ]
        
        time_pressure_score = sum(1 for indicator in time_indicators if indicator in text)
        
        return {
            'has_time_pressure': time_pressure_score > 0,
            'time_pressure_score': time_pressure_score,
            'urgency_level': 'high' if time_pressure_score >= 3 else 'medium' if time_pressure_score >= 1 else 'low'
        }
    
    def _calculate_topic_relevance(self, post: Dict, topic: str) -> float:
        """Calculate how relevant the post is to the topic"""
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        topic_lower = topic.lower()
        
        # Direct mentions
        title_mentions = title.count(topic_lower)
        content_mentions = content.count(topic_lower)
        
        # Related terms
        topic_words = topic_lower.split()
        related_score = 0
        for word in topic_words:
            if word in title: related_score += 2
            if word in content: related_score += 1
        
        # Calculate relevance score (0-10)
        relevance_score = min(10, (title_mentions * 3) + (content_mentions * 2) + related_score)
        
        return round(relevance_score, 1)
    
    def _analyze_comments_for_pain(self, comments: List[Dict]) -> Dict[str, Any]:
        """Analyze comments specifically for pain points and solutions"""
        
        if not comments:
            return {'total_comments': 0, 'pain_insights': []}
        
        pain_comments = []
        solution_comments = []
        empathy_comments = []
        
        for comment in comments:
            text = comment.get('text', '').lower()
            
            # Identify pain point comments
            if any(word in text for word in ['same problem', 'struggling', 'frustrated', 'issue', 'difficulty']):
                pain_comments.append(comment.get('text', ''))
            
            # Identify solution comments
            if any(word in text for word in ['solution', 'worked for me', 'try this', 'solved', 'fixed']):
                solution_comments.append(comment.get('text', ''))
            
            # Identify empathy/support comments
            if any(word in text for word in ['understand', 'been there', 'feel you', 'same here']):
                empathy_comments.append(comment.get('text', ''))
        
        return {
            'total_comments': len(comments),
            'pain_validation_count': len(pain_comments),
            'solution_offer_count': len(solution_comments),
            'empathy_count': len(empathy_comments),
            'pain_validation_comments': pain_comments[:3],  # Top 3
            'solution_comments': solution_comments[:3],     # Top 3
            'community_support_level': 'high' if len(empathy_comments) > 2 else 'medium' if len(empathy_comments) > 0 else 'low'
        }
    
    def _perform_pain_point_analysis(self, reddit_data: List[Dict], topic: str) -> Dict[str, Any]:
        """Perform comprehensive pain point analysis"""
        
        logger.info("🔬 Performing pain point analysis...")
        
        # Aggregate all pain points
        all_pain_points = []
        frustration_levels = []
        problem_categories = []
        cost_concerns = []
        time_pressures = []
        
        for post in reddit_data:
            # Collect pain points
            pain_indicators = post.get('pain_point_indicators', {})
            detected_pains = pain_indicators.get('detected_pain_points', {})
            all_pain_points.extend(detected_pains.keys())
            
            # Collect frustration data
            frustration = post.get('frustration_level', {})
            frustration_levels.append(frustration.get('frustration_level', 'low'))
            
            # Collect problem categories
            problem_categories.append(post.get('problem_category', 'unknown'))
            
            # Collect cost concerns
            cost_data = post.get('cost_concerns', {})
            cost_concerns.extend(cost_data.keys())
            
            # Collect time pressure data
            time_data = post.get('time_pressure', {})
            if time_data.get('has_time_pressure'):
                time_pressures.append(time_data.get('urgency_level', 'low'))
        
        # Analyze patterns
        pain_point_frequency = Counter(all_pain_points)
        frustration_distribution = Counter(frustration_levels)
        problem_category_distribution = Counter(problem_categories)
        cost_concern_frequency = Counter(cost_concerns)
        time_pressure_distribution = Counter(time_pressures)
        
        # Extract customer language
        customer_quotes = []
        common_phrases = []
        
        for post in reddit_data:
            # Extract authentic quotes
            title = post.get('title', '')
            if len(title) > 20 and any(word in title.lower() for word in ['struggling', 'help', 'confused', 'problem']):
                customer_quotes.append(title)
            
            # Extract phrases from comments
            comment_analysis = post.get('comment_pain_analysis', {})
            pain_comments = comment_analysis.get('pain_validation_comments', [])
            common_phrases.extend(pain_comments)
        
        return {
            'critical_pain_points': {
                'top_pain_points': dict(pain_point_frequency.most_common(8)),
                'frustration_distribution': dict(frustration_distribution),
                'problem_categories': dict(problem_category_distribution.most_common(5)),
                'cost_concerns': dict(cost_concern_frequency.most_common(5)),
                'time_pressure_analysis': dict(time_pressure_distribution)
            },
            'customer_voice': {
                'authentic_quotes': customer_quotes[:10],
                'common_pain_phrases': common_phrases[:8],
                'frustration_language': self._extract_frustration_language(reddit_data),
                'solution_requests': self._extract_solution_requests(reddit_data)
            },
            'emotional_intelligence': {
                'dominant_emotions': self._analyze_emotional_patterns(reddit_data),
                'stress_indicators': self._identify_stress_indicators(reddit_data),
                'support_seeking_behavior': self._analyze_support_seeking(reddit_data)
            },
            'actionable_insights': {
                'content_opportunities': self._identify_content_opportunities(reddit_data, topic),
                'solution_gaps': self._identify_solution_gaps(reddit_data),
                'trust_building_needs': self._identify_trust_needs(reddit_data),
                'education_requirements': self._identify_education_needs(reddit_data)
            }
        }
    
    def _extract_frustration_language(self, reddit_data: List[Dict]) -> List[str]:
        """Extract language that indicates frustration"""
        frustration_phrases = []
        
        for post in reddit_data:
            frustration_data = post.get('frustration_level', {})
            if frustration_data.get('frustration_level') in ['moderate', 'high']:
                title = post.get('title', '')
                if title:
                    frustration_phrases.append(title)
        
        return frustration_phrases[:5]
    
    def _extract_solution_requests(self, reddit_data: List[Dict]) -> List[str]:
        """Extract how customers ask for solutions"""
        solution_requests = []
        
        for post in reddit_data:
            text = post.get('title', '') + ' ' + post.get('content', '')
            if any(word in text.lower() for word in ['help', 'advice', 'solution', 'recommend', 'suggest']):
                solution_requests.append(post.get('title', ''))
        
        return solution_requests[:5]
    
    def _analyze_emotional_patterns(self, reddit_data: List[Dict]) -> Dict[str, int]:
        """Analyze emotional patterns in the data"""
        emotions = []
        
        for post in reddit_data:
            frustration_data = post.get('frustration_level', {})
            level = frustration_data.get('frustration_level', 'low')
            emotions.append(level)
        
        return dict(Counter(emotions))
    
    def _identify_stress_indicators(self, reddit_data: List[Dict]) -> List[str]:
        """Identify indicators of customer stress"""
        stress_indicators = []
        
        for post in reddit_data:
            urgency_signals = post.get('urgency_signals', [])
            time_pressure = post.get('time_pressure', {})
            
            if urgency_signals:
                stress_indicators.extend(urgency_signals)
            
            if time_pressure.get('urgency_level') == 'high':
                stress_indicators.append('high_time_pressure')
        
        return list(set(stress_indicators))[:5]
    
    def _analyze_support_seeking(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Analyze how customers seek support"""
        support_patterns = {
            'asks_questions': 0,
            'shares_struggles': 0,
            'seeks_validation': 0,
            'requests_recommendations': 0
        }
        
        for post in reddit_data:
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            
            if '?' in title:
                support_patterns['asks_questions'] += 1
            if any(word in title for word in ['struggling', 'problem', 'issue']):
                support_patterns['shares_struggles'] += 1
            if any(word in title for word in ['anyone else', 'am i', 'is it just me']):
                support_patterns['seeks_validation'] += 1
            if any(word in title for word in ['recommend', 'suggest', 'advice']):
                support_patterns['requests_recommendations'] += 1
        
        return support_patterns
    
    def _identify_content_opportunities(self, reddit_data: List[Dict], topic: str) -> List[str]:
        """Identify content opportunities based on pain points"""
        opportunities = []
        
        # Analyze most common pain points
        pain_counter = Counter()
        for post in reddit_data:
            pain_data = post.get('pain_point_indicators', {})
            detected_pains = pain_data.get('detected_pain_points', {})
            pain_counter.update(detected_pains.keys())
        
        # Generate content ideas based on pain points
        top_pains = pain_counter.most_common(5)
        for pain, _ in top_pains:
            if pain == 'confusion':
                opportunities.append(f"Clear beginner's guide to {topic}")
            elif pain == 'overwhelm':
                opportunities.append(f"Simple {topic} decision framework")
            elif pain == 'money_waste':
                opportunities.append(f"How to avoid expensive {topic} mistakes")
            elif pain == 'time_waste':
                opportunities.append(f"Quick {topic} implementation guide")
            elif pain == 'complexity':
                opportunities.append(f"{topic} simplified for beginners")
        
        return opportunities
    
    def _identify_solution_gaps(self, reddit_data: List[Dict]) -> List[str]:
        """Identify gaps in available solutions"""
        gaps = []
        
        problem_counter = Counter()
        for post in reddit_data:
            problem_category = post.get('problem_category', 'unknown')
            problem_counter[problem_category] += 1
        
        # Identify most common unresolved problems
        top_problems = problem_counter.most_common(3)
        for problem, count in top_problems:
            if problem == 'learning_curve':
                gaps.append("Beginner-friendly educational content")
            elif problem == 'cost_issues':
                gaps.append("Budget-friendly solution guides")
            elif problem == 'complexity':
                gaps.append("Simplified implementation approaches")
            elif problem == 'comparison_confusion':
                gaps.append("Clear comparison frameworks")
        
        return gaps
    
    def _identify_trust_needs(self, reddit_data: List[Dict]) -> List[str]:
        """Identify trust-building needs"""
        trust_needs = []
        
        # Look for trust-related concerns
        for post in reddit_data:
            text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
            
            if any(word in text for word in ['scam', 'fake', 'trust', 'reliable', 'legit']):
                trust_needs.append("Credibility and trust signals")
            if any(word in text for word in ['review', 'experience', 'testimonial']):
                trust_needs.append("Customer testimonials and reviews")
            if any(word in text for word in ['guarantee', 'refund', 'risk']):
                trust_needs.append("Risk reduction guarantees")
        
        return list(set(trust_needs))[:3]
    
    def _identify_education_needs(self, reddit_data: List[Dict]) -> List[str]:
        """Identify educational content needs"""
        education_needs = []
        
        confusion_count = 0
        basic_question_count = 0
        
        for post in reddit_data:
            pain_data = post.get('pain_point_indicators', {})
            detected_pains = pain_data.get('detected_pain_points', {})
            
            if 'confusion' in detected_pains:
                confusion_count += 1
            
            title = post.get('title', '').lower()
            if any(word in title for word in ['what is', 'how to', 'explain', 'understand']):
                basic_question_count += 1
        
        if confusion_count > len(reddit_data) * 0.3:
            education_needs.append("Clear explanatory content")
        if basic_question_count > len(reddit_data) * 0.2:
            education_needs.append("Foundational education materials")
        
        education_needs.append("Step-by-step tutorials")
        education_needs.append("FAQ addressing common concerns")
        
        return education_needs
    
    def _analyze_subreddit_specific(self, posts: List[Dict], subreddit: str) -> Dict[str, Any]:
        """Analyze subreddit-specific patterns"""
        
        if not posts:
            return {'post_count': 0, 'insights': 'No posts found'}
        
        total_posts = len(posts)
        
        # Calculate pain point concentration
        pain_point_count = sum(1 for post in posts 
                              if post.get('pain_point_indicators', {}).get('has_significant_pain', False))
        
        # Calculate average frustration
        frustration_scores = [post.get('frustration_level', {}).get('frustration_score', 0) for post in posts]
        avg_frustration = sum(frustration_scores) / len(frustration_scores) if frustration_scores else 0
        
        # Dominant problem categories
        problem_categories = [post.get('problem_category', 'unknown') for post in posts]
        category_counter = Counter(problem_categories)
        
        return {
            'post_count': total_posts,
            'pain_point_concentration': round(pain_point_count / total_posts, 2),
            'avg_frustration_score': round(avg_frustration, 1),
            'dominant_problems': dict(category_counter.most_common(3)),
            'audience_pain_level': 'high' if avg_frustration > 5 else 'medium' if avg_frustration > 2 else 'low',
            'support_seeking_intensity': 'high' if pain_point_count > total_posts * 0.6 else 'medium'
        }
    
    def _calculate_research_metadata(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Calculate metadata about the research quality"""
        
        total_posts = len(reddit_data)
        total_comments = sum(post.get('comment_pain_analysis', {}).get('total_comments', 0) for post in reddit_data)
        
        # Calculate quality metrics
        high_relevance_posts = sum(1 for post in reddit_data if post.get('topic_relevance', 0) > 7)
        significant_pain_posts = sum(1 for post in reddit_data 
                                   if post.get('pain_point_indicators', {}).get('has_significant_pain', False))
        
        return {
            'total_posts_analyzed': total_posts,
            'total_comments_analyzed': total_comments,
            'high_relevance_ratio': round(high_relevance_posts / total_posts, 2) if total_posts > 0 else 0,
            'significant_pain_ratio': round(significant_pain_posts / total_posts, 2) if total_posts > 0 else 0,
            'avg_comments_per_post': round(total_comments / total_posts, 1) if total_posts > 0 else 0,
            'research_quality_score': min(100, (high_relevance_posts + significant_pain_posts) * 5),
            'data_richness': 'high' if total_comments > total_posts * 3 else 'medium'
        }
    
    def _generate_fallback_analysis(self, topic: str) -> Dict[str, Any]:
        """Generate fallback analysis when no Reddit data is available"""
        
        return {
            'critical_pain_points': {
                'top_pain_points': {
                    'confusion': 15,
                    'overwhelm': 12,
                    'cost_concerns': 10,
                    'time_waste': 8,
                    'complexity': 7
                },
                'frustration_distribution': {'moderate': 8, 'high': 5, 'low': 3},
                'problem_categories': {
                    'learning_curve': 6,
                    'cost_issues': 4,
                    'complexity': 4,
                    'comparison_confusion': 3
                }
            },
            'customer_voice': {
                'authentic_quotes': [
                    f"So confused about {topic}, where do I even start?",
                    f"Wasted so much money on the wrong {topic} solution",
                    f"Why is {topic} so complicated? Need simple guidance",
                    f"Overwhelming number of {topic} options out there",
                    f"Made every mistake in the book with {topic}"
                ],
                'common_pain_phrases': [
                    "struggling to understand",
                    "too many options",
                    "conflicting information",
                    "waste of money",
                    "more complicated than expected"
                ]
            },
            'emotional_intelligence': {
                'dominant_emotions': {'moderate': 10, 'high': 5, 'low': 3},
                'stress_indicators': ['time_pressure', 'budget_constraints', 'decision_paralysis'],
                'support_seeking_behavior': {
                    'asks_questions': 12,
                    'shares_struggles': 8,
                    'seeks_validation': 6,
                    'requests_recommendations': 10
                }
            },
            'actionable_insights': {
                'content_opportunities': [
                    f"Complete beginner's guide to {topic}",
                    f"How to avoid expensive {topic} mistakes",
                    f"Simple {topic} decision framework",
                    f"Quick {topic} implementation guide"
                ],
                'solution_gaps': [
                    "Beginner-friendly educational content",
                    "Budget-friendly solution guides",
                    "Clear comparison frameworks"
                ],
                'trust_building_needs': [
                    "Customer testimonials and reviews",
                    "Credibility and trust signals",
                    "Risk reduction guarantees"
                ],
                'education_requirements': [
                    "Step-by-step tutorials",
                    "FAQ addressing common concerns",
                    "Clear explanatory content"
                ]
            },
            'research_metadata': {
                'total_posts_analyzed': 0,
                'total_comments_analyzed': 0,
                'research_quality_score': 0,
                'data_source': 'fallback_analysis'
            }
        }
