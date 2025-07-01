import praw
import os
from dotenv import load_dotenv

# Load environment variables directly (this approach works!)
load_dotenv()

class RedditClient:
    def __init__(self):
        # Use the same approach that worked in test_reddit.py
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "ContentAgent/1.0")
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    
    def search_subreddit(self, subreddit_name, query, limit=20):
        """Search for posts in a specific subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            for post in subreddit.search(query, limit=limit, sort='relevance'):
                post_data = {
                    'title': post.title,
                    'content': post.selftext[:1000],
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'url': post.url,
                    'subreddit': subreddit_name,
                    'comments': []
                }
                
                # Get top comments
                try:
                    post.comments.replace_more(limit=0)
                    for comment in post.comments.list()[:10]:
                        if len(comment.body) >= 50:
                            post_data['comments'].append({
                                'text': comment.body[:500],
                                'score': comment.score
                            })
                except:
                    pass
                
                posts.append(post_data)
            
            return posts
        except Exception as e:
            print(f"Error searching Reddit: {str(e)}")
            return []
    
    def get_hot_posts(self, subreddit_name, limit=10):
        """Get hot posts from subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            for post in subreddit.hot(limit=limit):
                posts.append({
                    'title': post.title,
                    'content': post.selftext[:500],
                    'score': post.score,
                    'subreddit': subreddit_name
                })
            
            return posts
        except Exception as e:
            print(f"Error getting hot posts: {str(e)}")
            return []