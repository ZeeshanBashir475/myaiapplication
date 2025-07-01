import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Reddit Configuration
    REDDIT_CLIENT_ID = os.getenv("uAbfdLEeGc9gWYhVVYwEx")
    REDDIT_CLIENT_SECRET = os.getenv("Un0_zbZ1wtONsYAACC7u8qx")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ContentAgent/1.0")
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY = os.getenv("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")
    
    # Default settings
    MAX_REDDIT_POSTS = 20
    MAX_COMMENTS_PER_POST = 10
    MIN_COMMENT_LENGTH = 50

settings = Settings()

# Create an instance - this is what gets imported
settings = Settings()