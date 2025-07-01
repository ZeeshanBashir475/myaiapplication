import json
from src.utils.reddit_client import RedditClient
from src.utils.llm_client import LLMClient

class RedditResearcher:
    def __init__(self):
        self.reddit_client = RedditClient()
        self.llm = LLMClient()
    
    def research_topic(self, topic, subreddits, max_posts_per_subreddit=10):
        """Research topic across multiple subreddits"""
        all_reddit_data = []
        
        for subreddit in subreddits:
            print(f"Researching r/{subreddit}...")
            posts = self.reddit_client.search_subreddit(subreddit, topic, max_posts_per_subreddit)
            all_reddit_data.extend(posts)
        
        if not all_reddit_data:
            return self._generate_fallback_insights(topic)
        
        return self._analyze_reddit_data(all_reddit_data, topic)
    
    def _analyze_reddit_data(self, reddit_data, topic):
        """Analyze Reddit data to extract customer insights"""
        
        # Prepare data for analysis
        posts_summary = []
        comments_summary = []
        
        for post in reddit_data[:15]:  # Limit to prevent token overflow
            posts_summary.append({
                'title': post['title'],
                'content': post['content'][:200],
                'score': post['score']
            })
            
            for comment in post['comments'][:3]:  # Top 3 comments per post
                comments_summary.append({
                    'text': comment['text'][:200],
                    'score': comment['score']
                })
        
        prompt = f"""
        Analyze these Reddit discussions about "{topic}" and extract customer insights:
        
        Posts: {json.dumps(posts_summary, indent=2)}
        
        Comments: {json.dumps(comments_summary, indent=2)}
        
        Provide analysis in JSON format:
        {{
            "customer_voice": {{
                "common_language": ["phrases customers actually use"],
                "frequent_questions": ["actual questions being asked"],
                "pain_points": ["problems mentioned repeatedly"],
                "positive_mentions": ["what customers like/praise"],
                "negative_mentions": ["complaints and frustrations"]
            }},
            "sentiment_analysis": {{
                "overall_sentiment": "positive|neutral|negative",
                "emotional_indicators": ["frustrated", "excited", "confused"],
                "urgency_signals": ["words indicating urgency or importance"]
            }},
            "content_gaps": ["missing information customers are seeking"],
            "actionable_insights": ["specific insights for content creation"],
            "authentic_quotes": ["2-3 powerful customer quotes to use"]
        }}
        
        Focus on extracting the authentic voice of real customers, their exact language, and genuine concerns.
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            return json.loads(response)
        except:
            return self._generate_fallback_insights(topic)
    
    def _generate_fallback_insights(self, topic):
        """Fallback insights if Reddit research fails"""
        return {
            "customer_voice": {
                "common_language": [f"How to {topic}", f"Best {topic}", f"{topic} help"],
                "frequent_questions": [f"What is {topic}?", f"How does {topic} work?"],
                "pain_points": ["Lack of clear information", "Too many options"],
                "positive_mentions": ["Helpful solutions", "Easy to understand"],
                "negative_mentions": ["Confusing information", "Too complex"]
            },
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "emotional_indicators": ["curious", "seeking help"],
                "urgency_signals": ["need", "help", "urgent"]
            },
            "content_gaps": ["Clear explanations needed"],
            "actionable_insights": ["Create educational content"],
            "authentic_quotes": [f"I need help with {topic}", f"Looking for {topic} advice"]
        }