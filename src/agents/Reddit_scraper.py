import praw
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


class RedditScraper:
    """
    Scrapes Reddit posts and comments to identify pain points
    """
    
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        """
        Initialize Reddit scraper with API credentials
        
        Your Reddit App Credentials:
        - client_id: C86kxhF5BzNYO84XOY69Pw
        - client_secret: NWqTOqGQB2QA3vEKPWWin_LZAQCwTw
        - redirect_uri: http://localhost:8080
        """
        # Get credentials from environment or parameters
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID', 'C86kxhF5BzNYO84XOY69Pw')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET', 'NWqTOqGQB2QA3vEKPWWin_LZAQCwTw')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'Zeeshan Bashir Pain Point Analyzer v1.0')
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Reddit API credentials are required")
        
        # Initialize Reddit API client
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                redirect_uri='http://localhost:8080'
            )
            logger.info("✅ Reddit API client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Reddit client: {e}")
            raise
    
    def scrape_subreddit(self, subreddit_name: str, limit: int = 100, 
                        time_filter: str = 'week', sort_by: str = 'hot') -> List[Dict]:
        """
        Scrape posts from a subreddit
        
        Args:
            subreddit_name: Name of subreddit (without r/)
            limit: Number of posts to fetch (max 1000)
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
            sort_by: 'hot', 'new', 'top', 'rising'
        
        Returns:
            List of post dictionaries
        """
        try:
            logger.info(f"🔍 Scraping r/{subreddit_name} - {sort_by} posts (limit: {limit})")
            
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Get posts based on sort type
            if sort_by == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort_by == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort_by == 'top':
                submissions = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_by == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.hot(limit=limit)
            
            for submission in submissions:
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                    'url': submission.url,
                    'permalink': f"https://reddit.com{submission.permalink}",
                    'selftext': submission.selftext if submission.selftext else '',
                    'is_self': submission.is_self,
                    'link_flair_text': submission.link_flair_text,
                    'subreddit': subreddit_name,
                    'full_text': f"{submission.title}\n\n{submission.selftext}" if submission.selftext else submission.title
                }
                posts.append(post_data)
            
            logger.info(f"✅ Scraped {len(posts)} posts from r/{subreddit_name}")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Error scraping r/{subreddit_name}: {e}")
            return []
    
    def scrape_post_comments(self, post_id: str = None, post_url: str = None, 
                            limit: int = 500, sort: str = 'top') -> List[Dict]:
        """
        Scrape comments from a specific post
        
        Args:
            post_id: Reddit post ID
            post_url: Full Reddit post URL (alternative to post_id)
            limit: Max comments to fetch
            sort: 'best', 'top', 'new', 'controversial', 'old', 'qa'
        
        Returns:
            List of comment dictionaries
        """
        try:
            # Get submission
            if post_url:
                submission = self.reddit.submission(url=post_url)
            elif post_id:
                submission = self.reddit.submission(id=post_id)
            else:
                raise ValueError("Either post_id or post_url must be provided")
            
            logger.info(f"🔍 Scraping comments from post: {submission.title[:50]}...")
            
            # Sort comments
            submission.comment_sort = sort
            submission.comments.replace_more(limit=0)  # Remove "load more comments"
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                if not isinstance(comment, praw.models.MoreComments):
                    comment_data = {
                        'id': comment.id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'permalink': f"https://reddit.com{comment.permalink}",
                        'is_submitter': comment.is_submitter,
                        'depth': comment.depth
                    }
                    comments.append(comment_data)
            
            logger.info(f"✅ Scraped {len(comments)} comments")
            return comments
            
        except Exception as e:
            logger.error(f"❌ Error scraping comments: {e}")
            return []
    
    def scrape_multiple_subreddits(self, subreddit_names: List[str], 
                                   posts_per_sub: int = 50,
                                   time_filter: str = 'week') -> Dict[str, List[Dict]]:
        """
        Scrape posts from multiple subreddits
        
        Args:
            subreddit_names: List of subreddit names
            posts_per_sub: Posts to fetch from each subreddit
            time_filter: Time filter for 'top' posts
        
        Returns:
            Dictionary mapping subreddit names to lists of posts
        """
        results = {}
        
        for sub_name in subreddit_names:
            logger.info(f"📥 Scraping r/{sub_name}...")
            posts = self.scrape_subreddit(
                subreddit_name=sub_name,
                limit=posts_per_sub,
                time_filter=time_filter,
                sort_by='top'
            )
            results[sub_name] = posts
        
        total_posts = sum(len(posts) for posts in results.values())
        logger.info(f"✅ Total scraped: {total_posts} posts from {len(subreddit_names)} subreddits")
        
        return results
    
    def search_subreddit(self, subreddit_name: str, query: str, 
                        limit: int = 100, time_filter: str = 'all') -> List[Dict]:
        """
        Search for posts in a subreddit matching a query
        
        Args:
            subreddit_name: Subreddit to search
            query: Search query
            limit: Max results
            time_filter: Time filter
        
        Returns:
            List of matching posts
        """
        try:
            logger.info(f"🔍 Searching r/{subreddit_name} for: '{query}'")
            
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            for submission in subreddit.search(query, time_filter=time_filter, limit=limit):
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                    'permalink': f"https://reddit.com{submission.permalink}",
                    'selftext': submission.selftext,
                    'full_text': f"{submission.title}\n\n{submission.selftext}"
                }
                posts.append(post_data)
            
            logger.info(f"✅ Found {len(posts)} posts matching '{query}'")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def get_trending_topics(self, subreddit_name: str, limit: int = 50) -> Dict:
        """
        Get trending topics and common phrases from recent posts
        
        Args:
            subreddit_name: Subreddit to analyze
            limit: Number of recent posts to analyze
        
        Returns:
            Dictionary with trending topics
        """
        posts = self.scrape_subreddit(subreddit_name, limit=limit, sort_by='hot')
        
        # Extract common words/phrases
        all_text = ' '.join([p['full_text'] for p in posts])
        
        # Basic word frequency (you can enhance this)
        words = re.findall(r'\b[a-z]{4,}\b', all_text.lower())
        from collections import Counter
        word_freq = Counter(words).most_common(20)
        
        return {
            'subreddit': subreddit_name,
            'total_posts_analyzed': len(posts),
            'total_comments': sum(p['num_comments'] for p in posts),
            'avg_score': sum(p['score'] for p in posts) / len(posts) if posts else 0,
            'trending_words': word_freq,
            'top_posts': sorted(posts, key=lambda x: x['score'], reverse=True)[:5]
        }
    
    def extract_pain_points_from_text(self, text: str) -> List[str]:
        """
        Basic pain point extraction using regex patterns
        (For advanced extraction, use the PainPointExtractor with AI)
        
        Args:
            text: Text to analyze
        
        Returns:
            List of potential pain points
        """
        pain_indicators = [
            # Problem statements
            r"(?:struggling|problem|issue|challenge|difficult|hard|can't|cannot|unable|fail(?:ed|ing)?)\s+(?:with|to)\s+([^.!?]+)",
            # Questions indicating problems
            r"(?:how do i|how can i|how to)\s+([^?]+)\?",
            # Negative experiences
            r"(?:frustrated|annoyed|hate|dislike|terrible)\s+(?:with|about|that)\s+([^.!?]+)",
            # Lack/Need statements
            r"(?:need|want|looking for|wish)\s+([^.!?]+)",
            # Don't know statements
            r"(?:don't know|unsure|confused)\s+(?:how|about|what)\s+([^.!?]+)"
        ]
        
        pain_points = []
        text_lower = text.lower()
        
        for pattern in pain_indicators:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if len(match) > 10 and len(match) < 150:  # Filter by length
                    pain_points.append(match.strip())
        
        return list(set(pain_points))[:10]  # Return unique, limit 10
    
    def scrape_for_pain_points(self, subreddit_name: str, topic: str = None,
                               posts_limit: int = 50, comments_limit: int = 20) -> Dict:
        """
        Scrape subreddit specifically looking for pain points
        
        Args:
            subreddit_name: Subreddit to scrape
            topic: Optional topic to search for
            posts_limit: Number of posts to scrape
            comments_limit: Number of comments per post
        
        Returns:
            Dictionary with posts, comments, and extracted pain points
        """
        logger.info(f"🎯 Scraping r/{subreddit_name} for pain points...")
        
        # Get posts
        if topic:
            posts = self.search_subreddit(subreddit_name, topic, limit=posts_limit)
        else:
            posts = self.scrape_subreddit(subreddit_name, limit=posts_limit, sort_by='top')
        
        # Get comments from top posts
        all_comments = []
        for post in posts[:10]:  # Get comments from top 10 posts
            comments = self.scrape_post_comments(post_id=post['id'], limit=comments_limit)
            all_comments.extend(comments)
        
        # Extract basic pain points
        pain_points = []
        
        # From posts
        for post in posts:
            pain_points.extend(self.extract_pain_points_from_text(post['full_text']))
        
        # From comments
        for comment in all_comments:
            pain_points.extend(self.extract_pain_points_from_text(comment['body']))
        
        # Deduplicate and rank by frequency
        from collections import Counter
        pain_point_freq = Counter(pain_points)
        ranked_pain_points = [pp for pp, _ in pain_point_freq.most_common(15)]
        
        result = {
            'subreddit': subreddit_name,
            'topic': topic,
            'posts_scraped': len(posts),
            'comments_scraped': len(all_comments),
            'total_engagement': sum(p['score'] for p in posts),
            'posts': posts,
            'comments': all_comments,
            'pain_points_extracted': ranked_pain_points,
            'scraped_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Extracted {len(ranked_pain_points)} pain points from r/{subreddit_name}")
        
        return result
    
    def save_to_json(self, data: Dict, filename: str):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved data to {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving to JSON: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize scraper
    scraper = RedditScraper()
    
    # Test 1: Scrape a subreddit
    print("\n" + "="*80)
    print("TEST 1: Scraping r/entrepreneur")
    print("="*80)
    
    posts = scraper.scrape_subreddit('entrepreneur', limit=10, sort_by='top', time_filter='week')
    print(f"✅ Found {len(posts)} posts")
    if posts:
        print(f"\nTop post: {posts[0]['title']}")
        print(f"Score: {posts[0]['score']}, Comments: {posts[0]['num_comments']}")
    
    # Test 2: Search for specific topic
    print("\n" + "="*80)
    print("TEST 2: Searching for 'starting a business'")
    print("="*80)
    
    results = scraper.search_subreddit('entrepreneur', 'starting a business', limit=5)
    print(f"✅ Found {len(results)} matching posts")
    
    # Test 3: Extract pain points
    print("\n" + "="*80)
    print("TEST 3: Extracting pain points")
    print("="*80)
    
    pain_data = scraper.scrape_for_pain_points('entrepreneur', topic='business ideas', posts_limit=20)
    print(f"✅ Posts: {pain_data['posts_scraped']}")
    print(f"✅ Comments: {pain_data['comments_scraped']}")
    print(f"✅ Pain points found: {len(pain_data['pain_points_extracted'])}")
    
    if pain_data['pain_points_extracted']:
        print("\nTop 5 pain points:")
        for i, pp in enumerate(pain_data['pain_points_extracted'][:5], 1):
            print(f"  {i}. {pp}")
    
    # Save results
    scraper.save_to_json(pain_data, 'reddit_pain_points.json')
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)
