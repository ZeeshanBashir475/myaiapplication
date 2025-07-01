import os
from dotenv import load_dotenv
import praw

# Load environment variables
load_dotenv()

# Get values directly
reddit_id = os.getenv("REDDIT_CLIENT_ID")
reddit_secret = os.getenv("REDDIT_CLIENT_SECRET")
user_agent = os.getenv("REDDIT_USER_AGENT", "ContentAgent/1.0")

print(f"Reddit ID: {reddit_id}")
print(f"Reddit Secret exists: {bool(reddit_secret)}")
print(f"User Agent: {user_agent}")

# Test Reddit connection
try:
    reddit = praw.Reddit(
        client_id=reddit_id,
        client_secret=reddit_secret,
        user_agent=user_agent
    )
    print("✅ Reddit client created successfully!")
    
    # Test a simple operation
    subreddit = reddit.subreddit("test")
    print(f"✅ Connected to r/test: {subreddit.display_name}")
    
except Exception as e:
    print(f"❌ Reddit connection failed: {e}")