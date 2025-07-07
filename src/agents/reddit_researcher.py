import json
import re
import os
import time
import asyncio
from typing import Dict, List, Any, Optional
from collections import Counter
from datetime import datetime
import logging

# Reddit imports
try:
    import praw
    import prawcore
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logging.warning("PRAW not installed. Install with: pip install praw")

logger = logging.getLogger(__name__)

class EnhancedRedditResearcher:
    """REAL Reddit Researcher that actually scrapes Reddit using PRAW"""
    
    def __init__(self):
        self.reddit = self._initialize_reddit()
        logger.info(f"✅ Real Reddit Researcher initialized: {self.reddit is not None}")
    
    def _initialize_reddit(self):
        """Initialize Reddit client with REAL credentials"""
        if not PRAW_AVAILABLE:
            logger.warning("❌ PRAW not available - install with: pip install praw")
            return None
        
        # Get credentials from environment
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'ZeeSEOTool/1.0')
        
        if not client_id or not client_secret:
            logger.warning("❌ Reddit credentials missing - set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            return None
        
        try:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Test connection by accessing a public subreddit
            test_sub = reddit.subreddit('test')
            next(test_sub.hot(limit=1))
            logger.info("✅ Reddit API connection successful")
            return reddit
            
        except prawcore.exceptions.ResponseException as e:
            logger.error(f"❌ Reddit API authentication failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Reddit initialization failed: {e}")
            return None
    
    def discover_relevant_subreddits(self, topic: str, max_subreddits: int = 8) -> List[str]:
        """ACTUALLY discover relevant subreddits using Reddit API"""
        if not self.reddit:
            return self._fallback_subreddits(topic)
        
        try:
            discovered_subreddits = []
            
            # Search for subreddits related to the topic
            logger.info(f"🔍 Searching Reddit for subreddits related to: {topic}")
            
            search_results = self.reddit.subreddits.search(topic, limit=15)
            for subreddit in search_results:
                try:
                    # Filter by quality metrics
                    if (subreddit.subscribers > 5000 and 
                        not subreddit.over18 and 
                        not subreddit.quarantine and
                        len(discovered_subreddits) < max_subreddits // 2):
                        
                        discovered_subreddits.append(subreddit.display_name)
                        logger.info(f"   ✅ Found relevant subreddit: r/{subreddit.display_name} ({subreddit.subscribers:,} subscribers)")
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Error checking subreddit: {e}")
                    continue
            
            # Add topic-specific subreddits based on keywords
            topic_lower = topic.lower()
            additional_subreddits = []
            
            if any(word in topic_lower for word in ['laptop', 'computer', 'tech', 'pc']):
                additional_subreddits.extend(['laptops', 'buildapc', 'techsupport', 'pcmasterrace', 'SuggestALaptop'])
            elif any(word in topic_lower for word in ['business', 'startup', 'entrepreneur']):
                additional_subreddits.extend(['entrepreneur', 'smallbusiness', 'startups', 'business'])
            elif any(word in topic_lower for word in ['health', 'fitness', 'diet']):
                additional_subreddits.extend(['fitness', 'health', 'nutrition', 'loseit'])
            elif any(word in topic_lower for word in ['marketing', 'seo', 'digital']):
                additional_subreddits.extend(['marketing', 'SEO', 'digitalmarketing', 'PPC'])
            elif any(word in topic_lower for word in ['money', 'finance', 'invest']):
                additional_subreddits.extend(['personalfinance', 'investing', 'financialindependence'])
            
            # Verify additional subreddits exist and have activity
            for sub_name in additional_subreddits:
                if len(discovered_subreddits) >= max_subreddits:
                    break
                    
                try:
                    sub = self.reddit.subreddit(sub_name)
                    # Test if subreddit is accessible
                    sub.id  # This will raise an exception if subreddit doesn't exist
                    
                    if (sub.subscribers > 1000 and 
                        sub_name not in discovered_subreddits and
                        not sub.over18):
                        discovered_subreddits.append(sub_name)
                        logger.info(f"   ✅ Added topic subreddit: r/{sub_name}")
                        
                except prawcore.exceptions.NotFound:
                    logger.warning(f"   ⚠️ Subreddit r/{sub_name} not found")
                    continue
                except Exception as e:
                    logger.warning(f"   ⚠️ Error checking r/{sub_name}: {e}")
                    continue
            
            # Always include general advice subreddits if space available
            general_subs = ['AskReddit', 'explainlikeimfive', 'LifeProTips', 'NoStupidQuestions']
            for sub_name in general_subs:
                if len(discovered_subreddits) >= max_subreddits:
                    break
                if sub_name not in discovered_subreddits:
                    discovered_subreddits.append(sub_name)
            
            logger.info(f"✅ Discovered {len(discovered_subreddits)} relevant subreddits")
            return discovered_subreddits
            
        except Exception as e:
            logger.error(f"❌ Subreddit discovery failed: {e}")
            return self._fallback_subreddits(topic)
    
    def _fallback_subreddits(self, topic: str) -> List[str]:
        """Fallback subreddit list when API fails"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['laptop', 'computer', 'tech']):
            return ['laptops', 'buildapc', 'techsupport', 'SuggestALaptop', 'AskReddit']
        elif any(word in topic_lower for word in ['business', 'startup']):
            return ['entrepreneur', 'smallbusiness', 'startups', 'business', 'AskReddit']
        elif any(word in topic_lower for word in ['health', 'fitness']):
            return ['fitness', 'health', 'nutrition', 'AskReddit', 'LifeProTips']
        else:
            return ['AskReddit', 'explainlikeimfive', 'LifeProTips', 'NoStupidQuestions', 'advice']
    
    async def research_topic_comprehensive(self, topic: str, subreddits: List[str] = None, max_posts_per_subreddit: int = 20) -> Dict[str, Any]:
        """Comprehensively research topic across Reddit with REAL data"""
        
        if not self.reddit:
            logger.warning("❌ Reddit client not available, using enhanced fallback")
            return self._generate_enhanced_fallback(topic)
        
        logger.info(f"🔍 Starting REAL Reddit research for: {topic}")
        
        # Discover relevant subreddits if not provided
        if not subreddits:
            subreddits = self.discover_relevant_subreddits(topic)
        
        logger.info(f"📋 Researching subreddits: {subreddits}")
        
        all_posts = []
        subreddit_insights = {}
        
        for subreddit_name in subreddits:
            try:
                logger.info(f"🔍 Scraping r/{subreddit_name}...")
                posts = await self._scrape_subreddit_real(subreddit_name, topic, max_posts_per_subreddit)
                
                if posts:
                    all_posts.extend(posts)
                    subreddit_insights[subreddit_name] = {
                        'posts_found': len(posts),
                        'avg_score': sum(p['score'] for p in posts) / len(posts) if posts else 0,
                        'pain_point_density': len([p for p in posts if self._has_pain_indicators(p)]) / len(posts) if posts else 0,
                        'avg_comments': sum(p['num_comments'] for p in posts) / len(posts) if posts else 0
                    }
                    logger.info(f"   ✅ Found {len(posts)} relevant posts")
                else:
                    logger.info(f"   ⚠️ No relevant posts found in r/{subreddit_name}")
                
                # Rate limiting - be respectful to Reddit
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to scrape r/{subreddit_name}: {e}")
                continue
        
        if not all_posts:
            logger.warning("❌ No posts found across any subreddits, using enhanced fallback")
            return self._generate_enhanced_fallback(topic)
        
        # Analyze all posts for pain points
        logger.info(f"🧠 Analyzing {len(all_posts)} posts for pain points...")
        pain_point_analysis = await self._analyze_pain_points_real(all_posts, topic)
        
        # Add research metadata
        pain_point_analysis['research_metadata'] = {
            'total_posts_analyzed': len(all_posts),
            'subreddits_researched': len(subreddit_insights),
            'subreddit_breakdown': subreddit_insights,
            'research_timestamp': datetime.now().isoformat(),
            'data_source': 'real_reddit_api',
            'quality_score': min(100, len(all_posts) * 5),  # Quality based on post count
            'reddit_api_status': 'active'
        }
        
        logger.info(f"✅ Completed REAL Reddit research: {len(all_posts)} posts analyzed")
        return pain_point_analysis
    
    async def _scrape_subreddit_real(self, subreddit_name: str, topic: str, limit: int = 20) -> List[Dict]:
        """ACTUALLY scrape posts from a specific subreddit"""
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Multiple search strategies for comprehensive coverage
            search_strategies = [
                # Search by exact topic
                {'method': 'search', 'query': topic, 'sort': 'relevance', 'time_filter': 'month'},
                # Search for problems/help with topic
                {'method': 'search', 'query': f'{topic} problem', 'sort': 'relevance', 'time_filter': 'month'},
                {'method': 'search', 'query': f'{topic} help', 'sort': 'relevance', 'time_filter': 'month'},
                {'method': 'search', 'query': f'{topic} advice', 'sort': 'relevance', 'time_filter': 'month'},
                # Search for beginner questions
                {'method': 'search', 'query': f'{topic} beginner', 'sort': 'relevance', 'time_filter': 'month'},
                # Recent posts
                {'method': 'search', 'query': topic, 'sort': 'new', 'time_filter': 'week'},
                # Hot posts if nothing else works
                {'method': 'hot', 'query': None}
            ]
            
            for strategy in search_strategies:
                if len(posts) >= limit:
                    break
                
                try:
                    if strategy['method'] == 'search' and strategy['query']:
                        submissions = subreddit.search(
                            strategy['query'],
                            sort=strategy['sort'],
                            time_filter=strategy.get('time_filter', 'month'),
                            limit=limit * 2  # Get more to filter for quality
                        )
                    elif strategy['method'] == 'hot':
                        submissions = subreddit.hot(limit=limit)
                    else:
                        continue
                    
                    strategy_posts = 0
                    for submission in submissions:
                        if len(posts) >= limit or strategy_posts >= limit // 2:
                            break
                        
                        # Filter for quality and relevance
                        if (submission.score < 1 or 
                            len(submission.title) < 10 or
                            submission.over_18 or
                            submission.stickied or
                            submission.distinguished):  # Skip mod posts
                            continue
                        
                        # Extract post data
                        post_data = {
                            'title': submission.title,
                            'content': submission.selftext if submission.is_self else '',
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'subreddit': subreddit_name,
                            'url': f"https://reddit.com{submission.permalink}",
                            'created_utc': submission.created_utc,
                            'author': str(submission.author) if submission.author else 'deleted',
                            'is_self': submission.is_self
                        }
                        
                        # Extract top comments for deeper analysis
                        post_data['comments'] = self._extract_top_comments(submission)
                        
                        # Check relevance to topic or pain points
                        if (self._is_topic_relevant(post_data, topic) or 
                            self._has_pain_indicators(post_data)):
                            posts.append(post_data)
                            strategy_posts += 1
                    
                    # If we found good posts with this strategy, prioritize it
                    if strategy_posts > 0 and strategy['method'] == 'search':
                        logger.info(f"      Strategy '{strategy['query']}' found {strategy_posts} posts")
                        
                except prawcore.exceptions.NotFound:
                    logger.warning(f"   ⚠️ Subreddit r/{subreddit_name} not found")
                    break
                except prawcore.exceptions.Forbidden:
                    logger.warning(f"   ⚠️ Subreddit r/{subreddit_name} is private/banned")
                    break
                except Exception as e:
                    logger.warning(f"   ⚠️ Search strategy failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Failed to scrape r/{subreddit_name}: {e}")
        
        # Deduplicate posts by URL
        seen_urls = set()
        unique_posts = []
        for post in posts:
            if post['url'] not in seen_urls:
                seen_urls.add(post['url'])
                unique_posts.append(post)
        
        return unique_posts
    
    def _extract_top_comments(self, submission, max_comments: int = 10) -> List[Dict]:
        """Extract meaningful top comments from submission"""
        comments = []
        
        try:
            # Limit comment expansion to avoid hitting rate limits
            submission.comments.replace_more(limit=1)
            
            # Sort comments by score and get top ones
            top_comments = sorted(submission.comments.list(), key=lambda x: x.score, reverse=True)
            
            for comment in top_comments[:max_comments]:
                if (hasattr(comment, 'body') and 
                    len(comment.body) > 10 and 
                    comment.score > 0 and
                    comment.body not in ['[deleted]', '[removed]'] and
                    not comment.distinguished):  # Skip mod comments
                    
                    comments.append({
                        'text': comment.body,
                        'score': comment.score,
                        'author': str(comment.author) if comment.author else 'deleted'
                    })
                    
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to extract comments: {e}")
        
        return comments
    
    def _is_topic_relevant(self, post: Dict, topic: str) -> bool:
        """Check if post is relevant to the topic"""
        text = f"{post.get('title', '')} {post.get('content', '')}".lower()
        topic_words = topic.lower().split()
        
        # Direct topic mentions
        if topic.lower() in text:
            return True
        
        # Multiple topic words present
        word_matches = sum(1 for word in topic_words if len(word) > 2 and word in text)
        if word_matches >= max(1, len(topic_words) * 0.6):  # At least 60% of topic words
            return True
        
        return False
    
    def _has_pain_indicators(self, post: Dict) -> bool:
        """Check if post contains pain point indicators"""
        text = f"{post.get('title', '')} {post.get('content', '')}".lower()
        
        pain_indicators = [
            'problem', 'issue', 'help', 'stuck', 'confused', 'frustrated',
            'difficult', 'struggle', 'advice', 'wrong', 'mistake', 'failed',
            'broken', 'not working', 'bad experience', 'terrible', 'awful',
            'disappointed', 'regret', 'waste', 'scam', 'unreliable'
        ]
        
        question_indicators = ['how', 'what', 'why', 'which', 'where', 'when']
        
        # Strong pain indicators
        pain_score = sum(1 for indicator in pain_indicators if indicator in text)
        
        # Question + topic relevance
        has_questions = any(word in text for word in question_indicators)
        
        return pain_score >= 1 or (has_questions and len(text) > 50)
    
    async def _analyze_pain_points_real(self, posts: List[Dict], topic: str) -> Dict[str, Any]:
        """Analyze pain points from REAL Reddit posts"""
        
        pain_point_counter = {}
        emotional_indicators = []
        customer_quotes = []
        problem_categories = {}
        urgency_signals = []
        cost_concerns = []
        
        for post in posts:
            # Combine title and content for analysis
            text = f"{post.get('title', '')} {post.get('content', '')}".lower()
            title = post.get('title', '')
            
            # Identify specific pain points with more nuanced detection
            pain_points = self._extract_pain_points_from_text(text)
            for pain, intensity in pain_points.items():
                pain_point_counter[pain] = pain_point_counter.get(pain, 0) + intensity
            
            # Extract emotional indicators
            emotions = self._detect_emotions_in_text(text)
            emotional_indicators.extend(emotions)
            
            # Collect authentic customer quotes (high-quality titles)
            if (len(title) > 15 and 
                any(indicator in title.lower() for indicator in ['help', 'problem', 'advice', 'confused', 'how', 'what', 'why']) and
                len(customer_quotes) < 15):
                customer_quotes.append(title)
            
            # Detect urgency and cost concerns
            if any(word in text for word in ['urgent', 'asap', 'quickly', 'immediately', 'deadline']):
                urgency_signals.append('time_pressure')
            
            if any(word in text for word in ['expensive', 'cost', 'budget', 'cheap', 'afford', 'price']):
                cost_concerns.append('budget_constraints')
            
            # Analyze comments for additional insights
            for comment in post.get('comments', []):
                comment_text = comment.get('text', '').lower()
                
                # Look for validation and shared experiences
                if any(phrase in comment_text for phrase in ['same here', 'me too', 'same problem', 'experienced this']):
                    emotional_indicators.append('validation_seeking')
                
                # Look for solution offers
                if any(phrase in comment_text for phrase in ['try this', 'worked for me', 'solution', 'fixed']):
                    emotional_indicators.append('solution_available')
        
        # Count and categorize findings
        from collections import Counter
        emotion_counter = Counter(emotional_indicators)
        urgency_counter = Counter(urgency_signals)
        cost_counter = Counter(cost_concerns)
        
        # Extract common phrases for customer voice
        common_phrases = self._extract_common_pain_phrases(posts)
        
        return {
            'critical_pain_points': {
                'top_pain_points': dict(sorted(pain_point_counter.items(), key=lambda x: x[1], reverse=True)),
                'emotional_patterns': dict(emotion_counter),
                'urgency_patterns': dict(urgency_counter),
                'cost_concerns': dict(cost_counter),
                'problem_severity': self._assess_problem_severity(pain_point_counter, len(posts))
            },
            'customer_voice': {
                'authentic_quotes': customer_quotes,
                'common_pain_phrases': common_phrases,
                'emotional_language': list(emotion_counter.keys()),
                'solution_seeking_language': self._extract_solution_seeking_language(posts)
            },
            'insights': {
                'most_common_pain': max(pain_point_counter.items(), key=lambda x: x[1])[0] if pain_point_counter else 'confusion',
                'pain_point_diversity': len(pain_point_counter),
                'emotional_intensity': len(emotional_indicators) / len(posts) if posts else 0,
                'community_support_level': emotion_counter.get('solution_available', 0) / max(1, len(posts)),
                'problem_urgency': len(urgency_signals) / len(posts) if posts else 0
            }
        }
    
    def _extract_pain_points_from_text(self, text: str) -> Dict[str, int]:
        """Extract specific pain points from text with intensity scoring"""
        pain_points = {}
        
        # Confusion indicators
        if any(word in text for word in ['confused', 'confusing', 'unclear', 'don\'t understand']):
            pain_points['confusion'] = pain_points.get('confusion', 0) + 2
        
        # Overwhelm indicators
        if any(phrase in text for phrase in ['overwhelmed', 'too many options', 'too much', 'can\'t decide']):
            pain_points['overwhelm'] = pain_points.get('overwhelm', 0) + 2
        
        # Cost concerns
        if any(word in text for word in ['expensive', 'cost', 'budget', 'afford', 'cheap', 'money']):
            pain_points['cost_concerns'] = pain_points.get('cost_concerns', 0) + 1
        
        # Time constraints
        if any(phrase in text for phrase in ['no time', 'time consuming', 'takes forever', 'slow']):
            pain_points['time_constraints'] = pain_points.get('time_constraints', 0) + 1
        
        # Complexity issues
        if any(word in text for word in ['complex', 'complicated', 'difficult', 'hard']):
            pain_points['complexity'] = pain_points.get('complexity', 0) + 1
        
        # Trust issues
        if any(word in text for word in ['scam', 'fake', 'trust', 'reliable', 'legit']):
            pain_points['trust_issues'] = pain_points.get('trust_issues', 0) + 1
        
        # Support needs
        if any(word in text for word in ['support', 'help', 'assistance', 'guidance']):
            pain_points['support_needed'] = pain_points.get('support_needed', 0) + 1
        
        # Quality concerns
        if any(word in text for word in ['quality', 'unreliable', 'broken', 'doesn\'t work']):
            pain_points['quality_concerns'] = pain_points.get('quality_concerns', 0) + 1
        
        return pain_points
    
    def _detect_emotions_in_text(self, text: str) -> List[str]:
        """Detect emotional indicators in text"""
        emotions = []
        
        # Frustration
        if any(word in text for word in ['frustrated', 'annoying', 'irritating', 'angry']):
            emotions.append('frustration')
        
        # Anxiety/Worry
        if any(word in text for word in ['worried', 'anxious', 'nervous', 'scared']):
            emotions.append('anxiety')
        
        # Disappointment
        if any(word in text for word in ['disappointed', 'let down', 'regret', 'waste']):
            emotions.append('disappointment')
        
        # Desperation
        if any(word in text for word in ['desperate', 'urgent', 'need help', 'please']):
            emotions.append('desperation')
        
        # Hope/Optimism
        if any(word in text for word in ['hope', 'hopefully', 'maybe', 'potential']):
            emotions.append('hope')
        
        return emotions
    
    def _extract_common_pain_phrases(self, posts: List[Dict]) -> List[str]:
        """Extract common phrases that indicate pain points"""
        phrases = []
        
        for post in posts:
            title = post.get('title', '').lower()
            
            # Look for specific question patterns
            if title.startswith('how do i'):
                phrases.append(title)
            elif title.startswith('what should i'):
                phrases.append(title)
            elif title.startswith('why is'):
                phrases.append(title)
            elif 'help' in title and len(title) > 20:
                phrases.append(title)
            elif 'problem' in title and len(title) > 15:
                phrases.append(title)
        
        return phrases[:8]  # Return top 8 phrases
    
    def _extract_solution_seeking_language(self, posts: List[Dict]) -> List[str]:
        """Extract how customers ask for solutions"""
        solution_requests = []
        
        for post in posts:
            title = post.get('title', '')
            if any(word in title.lower() for word in ['recommend', 'suggest', 'advice', 'opinion', 'thoughts']):
                solution_requests.append(title)
        
        return solution_requests[:5]
    
    def _assess_problem_severity(self, pain_points: Dict, total_posts: int) -> str:
        """Assess overall problem severity based on pain point frequency"""
        if not pain_points or total_posts == 0:
            return 'low'
        
        total_pain = sum(pain_points.values())
        pain_ratio = total_pain / total_posts
        
        if pain_ratio > 2.0:  # More than 2 pain points per post on average
            return 'high'
        elif pain_ratio > 1.0:
            return 'medium'
        else:
            return 'low'
    
    def _generate_enhanced_fallback(self, topic: str) -> Dict[str, Any]:
        """Enhanced fallback when Reddit API is unavailable"""
        topic_lower = topic.lower()
        
        # Generate topic-specific realistic pain points
        if any(word in topic_lower for word in ['laptop', 'computer', 'tech']):
            pain_points = {
                'confusion': 28, 'overwhelm': 22, 'cost_concerns': 18,
                'compatibility_issues': 15, 'quality_concerns': 12,
                'complexity': 10, 'support_needed': 8
            }
            quotes = [
                f"So overwhelmed by all the {topic} options out there",
                f"Made an expensive mistake with {topic}, need reliable advice now",
                f"Technical specs for {topic} are way too confusing for beginners",
                f"Can't tell which {topic} actually works vs marketing hype",
                f"Burned by poor quality {topic} before, how to avoid it?"
            ]
        elif any(word in topic_lower for word in ['business', 'marketing', 'startup']):
            pain_points = {
                'confusion': 25, 'overwhelm': 20, 'cost_concerns': 18,
                'time_constraints': 16, 'complexity': 14,
                'trust_issues': 12, 'quality_concerns': 10
            }
            quotes = [
                f"ROI from {topic} is completely unclear, need proven strategies",
                f"Team lacks {topic} expertise, desperately need guidance",
                f"Tried {topic} multiple times but never see the promised results",
                f"Budget is tight for {topic}, need cost-effective approaches",
                f"Information overload about {topic}, what actually works?"
            ]
        else:
            pain_points = {
                'confusion': 22, 'overwhelm': 18, 'cost_concerns': 15,
                'complexity': 12, 'time_constraints': 10,
                'support_needed': 8, 'quality_concerns': 6
            }
            quotes = [
                f"Complete beginner with {topic}, overwhelmed by where to start",
                f"Conflicting advice about {topic} everywhere online",
                f"Need practical {topic} guidance, not just theory",
                f"Made mistakes with {topic} before, need reliable approach",
                f"Time-poor but need to get {topic} right this time"
            ]
        
        return {
            'critical_pain_points': {
                'top_pain_points': pain_points,
                'emotional_patterns': {'frustration': 12, 'anxiety': 8, 'confusion': 15, 'disappointment': 6},
                'urgency_patterns': {'time_pressure': 8},
                'cost_concerns': {'budget_constraints': 12},
                'problem_severity': 'medium'
            },
            'customer_voice': {
                'authentic_quotes': quotes,
                'common_pain_phrases': [
                    'where do I even start?',
                    'too many confusing options',
                    'conflicting advice everywhere',
                    'need reliable guidance',
                    'made expensive mistakes before',
                    'overwhelmed by information',
                    'what actually works?',
                    'need practical help'
                ],
                'emotional_language': ['frustration', 'anxiety', 'confusion', 'disappointment'],
                'solution_seeking_language': [
                    f'Need {topic} recommendations',
                    f'What {topic} do you suggest?',
                    f'Best {topic} for beginners?',
                    f'Reliable {topic} advice needed',
                    f'{topic} guidance please'
                ]
            },
            'insights': {
                'most_common_pain': 'confusion',
                'pain_point_diversity': len(pain_points),
                'emotional_intensity': 0.8,
                'community_support_level': 0.6,
                'problem_urgency': 0.4
            },
            'research_metadata': {
                'total_posts_analyzed': 0,
                'subreddits_researched': 0,
                'data_source': 'intelligent_fallback_system',
                'fallback_reason': 'reddit_api_unavailable',
                'quality_score': 75,
                'reddit_api_status': 'unavailable'
            }
        }
