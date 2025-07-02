import json
import re
from typing import Dict, List, Any
from collections import Counter
from src.utils.reddit_client import RedditClient
from src.utils.llm_client import LLMClient

class EnhancedRedditResearcher:
    def __init__(self):
        self.reddit_client = RedditClient()
        self.llm = LLMClient()
        
    def research_topic_comprehensive(self, topic: str, subreddits: List[str], max_posts_per_subreddit: int = 15) -> Dict[str, Any]:
        """Comprehensive Reddit research with deep insight extraction"""
        
        print(f"🔍 Starting comprehensive Reddit research for: {topic}")
        
        all_reddit_data = []
        subreddit_insights = {}
        
        for subreddit in subreddits:
            print(f"📊 Analyzing r/{subreddit}...")
            posts = self.reddit_client.search_subreddit(subreddit, topic, max_posts_per_subreddit)
            
            if posts:
                all_reddit_data.extend(posts)
                subreddit_insights[subreddit] = self._analyze_subreddit_specific(posts, subreddit)
        
        if not all_reddit_data:
            return self._generate_comprehensive_fallback(topic)
        
        # Deep analysis of all data
        comprehensive_analysis = self._perform_deep_analysis(all_reddit_data, topic)
        
        # Combine with subreddit-specific insights
        comprehensive_analysis['subreddit_breakdown'] = subreddit_insights
        
        return comprehensive_analysis
    
    def _analyze_subreddit_specific(self, posts: List[Dict], subreddit: str) -> Dict[str, Any]:
        """Analyze posts specific to each subreddit"""
        
        total_posts = len(posts)
        total_engagement = sum(post.get('score', 0) for post in posts)
        
        # Extract titles and content for analysis
        all_text = []
        for post in posts:
            all_text.append(post.get('title', ''))
            all_text.append(post.get('content', ''))
            
            # Add comments
            for comment in post.get('comments', []):
                all_text.append(comment.get('text', ''))
        
        combined_text = ' '.join(all_text).lower()
        
        return {
            'post_count': total_posts,
            'total_engagement': total_engagement,
            'avg_engagement': total_engagement / total_posts if total_posts > 0 else 0,
            'community_sentiment': self._analyze_sentiment(combined_text),
            'key_themes': self._extract_themes(combined_text),
            'audience_level': self._determine_audience_level(subreddit, combined_text)
        }
    
    def _perform_deep_analysis(self, reddit_data: List[Dict], topic: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of all Reddit data"""
        
        # Prepare data for LLM analysis
        high_engagement_posts = sorted(reddit_data, key=lambda x: x.get('score', 0), reverse=True)[:10]
        
        analysis_data = {
            'posts': [],
            'comments': [],
            'questions': [],
            'complaints': [],
            'recommendations': []
        }
        
        for post in high_engagement_posts:
            post_data = {
                'title': post['title'],
                'content': post['content'][:300],
                'score': post['score'],
                'subreddit': post.get('subreddit', 'unknown')
            }
            analysis_data['posts'].append(post_data)
            
            # Categorize comments
            for comment in post.get('comments', [])[:5]:
                comment_text = comment.get('text', '')
                if self._is_question(comment_text):
                    analysis_data['questions'].append(comment_text[:200])
                elif self._is_complaint(comment_text):
                    analysis_data['complaints'].append(comment_text[:200])
                elif self._is_recommendation(comment_text):
                    analysis_data['recommendations'].append(comment_text[:200])
                else:
                    analysis_data['comments'].append(comment_text[:200])
        
        prompt = f"""
        Perform deep customer research analysis on Reddit discussions about "{topic}":
        
        Data: {json.dumps(analysis_data, indent=2)}
        
        Provide comprehensive analysis in JSON format:
        {{
            "pain_point_analysis": {{
                "critical_pain_points": ["ranked by frequency and intensity"],
                "emotional_triggers": ["what makes customers frustrated/excited"],
                "urgency_indicators": ["signals of immediate need"],
                "financial_impact": ["cost-related concerns mentioned"],
                "time_constraints": ["time-related pressure points"]
            }},
            "customer_journey_insights": {{
                "awareness_stage_questions": ["what do customers ask when learning"],
                "consideration_stage_concerns": ["evaluation criteria and comparisons"],
                "decision_stage_barriers": ["what stops customers from choosing"],
                "post_purchase_issues": ["problems after buying/using"]
            }},
            "language_intelligence": {{
                "customer_vocabulary": ["exact phrases customers use"],
                "technical_vs_layman": "technical|mixed|layman terms predominant",
                "emotional_language": ["emotionally charged words used"],
                "search_intent_phrases": ["phrases indicating search behavior"]
            }},
            "content_opportunity_gaps": {{
                "missing_information": ["info customers can't find"],
                "underserved_questions": ["questions without good answers"],
                "competitive_weaknesses": ["where competitors fail customers"],
                "emerging_trends": ["new patterns in customer needs"]
            }},
            "authenticity_markers": {{
                "real_customer_quotes": ["3-5 powerful authentic quotes"],
                "specific_use_cases": ["concrete examples customers mention"],
                "failure_stories": ["what went wrong for customers"],
                "success_stories": ["what worked for customers"]
            }},
            "actionable_content_strategy": {{
                "high_impact_topics": ["content topics with highest engagement potential"],
                "content_formats_preferred": ["formats customers respond to best"],
                "distribution_insights": ["where and how to share content"],
                "timing_patterns": ["when customers are most active/receptive"]
            }}
        }}
        
        Focus on extracting insights that would be impossible for AI to generate without real customer data.
        Prioritize authenticity, emotional intelligence, and actionable business insights.
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            parsed_response = json.loads(response)
            
            # Add quantitative analysis
            parsed_response['quantitative_insights'] = self._calculate_metrics(reddit_data)
            parsed_response['research_quality_score'] = self._assess_research_quality(reddit_data)
            
            return parsed_response
            
        except json.JSONDecodeError:
            return self._generate_comprehensive_fallback(topic)
    
    def _calculate_metrics(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Calculate quantitative metrics from Reddit data"""
        
        total_posts = len(reddit_data)
        total_engagement = sum(post.get('score', 0) for post in reddit_data)
        
        # Calculate sentiment distribution
        all_text = []
        for post in reddit_data:
            all_text.extend([post.get('title', ''), post.get('content', '')])
            for comment in post.get('comments', []):
                all_text.append(comment.get('text', ''))
        
        # Word frequency analysis
        word_freq = Counter()
        for text in all_text:
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq.update(words)
        
        return {
            'total_posts_analyzed': total_posts,
            'total_engagement_score': total_engagement,
            'avg_engagement_per_post': total_engagement / total_posts if total_posts > 0 else 0,
            'total_comments_analyzed': sum(len(post.get('comments', [])) for post in reddit_data),
            'top_keywords': dict(word_freq.most_common(20)),
            'data_freshness_score': self._calculate_freshness_score(reddit_data)
        }
    
    def _assess_research_quality(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Assess the quality and reliability of research data"""
        
        if not reddit_data:
            return {'overall_score': 0, 'reliability': 'poor'}
        
        # Calculate quality factors
        high_engagement_posts = sum(1 for post in reddit_data if post.get('score', 0) > 10)
        diverse_sources = len(set(post.get('subreddit', 'unknown') for post in reddit_data))
        comment_depth = sum(len(post.get('comments', [])) for post in reddit_data)
        
        quality_score = min(100, (
            (high_engagement_posts / len(reddit_data)) * 40 +
            min(diverse_sources * 20, 40) +
            min(comment_depth / len(reddit_data) * 20, 20)
        ))
        
        reliability = 'excellent' if quality_score > 80 else 'good' if quality_score > 60 else 'fair' if quality_score > 40 else 'poor'
        
        return {
            'overall_score': round(quality_score, 1),
            'reliability': reliability,
            'high_engagement_ratio': round(high_engagement_posts / len(reddit_data), 2),
            'source_diversity': diverse_sources,
            'comment_depth_avg': round(comment_depth / len(reddit_data), 1)
        }
    
    def _is_question(self, text: str) -> bool:
        """Detect if text contains a question"""
        question_indicators = ['?', 'how', 'what', 'when', 'where', 'why', 'which', 'who']
        return any(indicator in text.lower() for indicator in question_indicators)
    
    def _is_complaint(self, text: str) -> bool:
        """Detect if text contains a complaint"""
        complaint_indicators = ['terrible', 'awful', 'worst', 'hate', 'disappointed', 'frustrated', 'broken', 'useless']
        return any(indicator in text.lower() for indicator in complaint_indicators)
    
    def _is_recommendation(self, text: str) -> bool:
        """Detect if text contains a recommendation"""
        rec_indicators = ['recommend', 'suggest', 'try', 'best', 'love', 'amazing', 'perfect', 'works great']
        return any(indicator in text.lower() for indicator in rec_indicators)
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis"""
        positive_words = ['good', 'great', 'amazing', 'love', 'excellent', 'perfect', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'useless']
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from text"""
        # Simple theme extraction based on common patterns
        themes = []
        
        if 'price' in text or 'cost' in text or 'expensive' in text:
            themes.append('pricing_concerns')
        if 'quality' in text or 'durability' in text:
            themes.append('quality_focus')
        if 'support' in text or 'help' in text or 'service' in text:
            themes.append('support_needs')
        if 'feature' in text or 'functionality' in text:
            themes.append('feature_requests')
        
        return themes or ['general_discussion']
    
    def _determine_audience_level(self, subreddit: str, text: str) -> str:
        """Determine the technical level of the audience"""
        technical_indicators = ['API', 'configure', 'implementation', 'architecture', 'protocol']
        beginner_indicators = ['how to', 'getting started', 'beginner', 'simple', 'easy']
        
        tech_score = sum(1 for indicator in technical_indicators if indicator.lower() in text)
        beginner_score = sum(1 for indicator in beginner_indicators if indicator.lower() in text)
        
        if tech_score > beginner_score * 2:
            return 'technical'
        elif beginner_score > tech_score * 2:
            return 'beginner'
        else:
            return 'mixed'
    
    def _calculate_freshness_score(self, reddit_data: List[Dict]) -> float:
        """Calculate how fresh/recent the data is"""
        # This would ideally use actual post timestamps
        # For now, return a base score
        return 85.0  # Placeholder
    
    def _generate_comprehensive_fallback(self, topic: str) -> Dict[str, Any]:
        """Comprehensive fallback when Reddit research fails"""
        return {
            "pain_point_analysis": {
                "critical_pain_points": [
                    f"Lack of clear guidance on {topic}",
                    f"Too many options for {topic}",
                    f"Difficulty finding reliable {topic} information"
                ],
                "emotional_triggers": ["confusion", "overwhelm", "frustration"],
                "urgency_indicators": ["need help", "urgent", "asap"],
                "financial_impact": ["cost-effective", "budget-friendly", "expensive"],
                "time_constraints": ["quick solution", "time-sensitive", "immediate"]
            },
            "customer_journey_insights": {
                "awareness_stage_questions": [f"What is {topic}?", f"Do I need {topic}?"],
                "consideration_stage_concerns": [f"Best {topic} options", f"How to choose {topic}"],
                "decision_stage_barriers": ["Price concerns", "Trust issues", "Complexity"],
                "post_purchase_issues": ["Implementation challenges", "Support needs"]
            },
            "language_intelligence": {
                "customer_vocabulary": [f"{topic} help", f"best {topic}", f"how to {topic}"],
                "technical_vs_layman": "mixed",
                "emotional_language": ["frustrated", "confused", "hopeful"],
                "search_intent_phrases": [f"find {topic}", f"learn {topic}", f"get {topic}"]
            },
            "content_opportunity_gaps": {
                "missing_information": ["Step-by-step guides", "Real examples", "Cost breakdowns"],
                "underserved_questions": [f"How to get started with {topic}", f"Common {topic} mistakes"],
                "competitive_weaknesses": ["Generic advice", "No real examples", "Poor explanations"],
                "emerging_trends": ["Increased demand for personalized advice"]
            },
            "authenticity_markers": {
                "real_customer_quotes": [
                    f"I'm completely lost with {topic}",
                    f"Need help understanding {topic}",
                    f"Looking for reliable {topic} advice"
                ],
                "specific_use_cases": [f"Business use of {topic}", f"Personal {topic} needs"],
                "failure_stories": ["Chose wrong option", "Wasted money", "Got confused"],
                "success_stories": ["Found perfect solution", "Saved time and money"]
            },
            "actionable_content_strategy": {
                "high_impact_topics": [f"Complete {topic} guide", f"{topic} comparison", f"{topic} mistakes to avoid"],
                "content_formats_preferred": ["step-by-step guides", "comparison tables", "video tutorials"],
                "distribution_insights": ["Focus on search-driven content", "Share in relevant communities"],
                "timing_patterns": ["Peak interest during business hours"]
            },
            "quantitative_insights": {
                "total_posts_analyzed": 0,
                "total_engagement_score": 0,
                "avg_engagement_per_post": 0,
                "total_comments_analyzed": 0,
                "top_keywords": {},
                "data_freshness_score": 0
            },
            "research_quality_score": {
                "overall_score": 0,
                "reliability": "fallback_data",
                "high_engagement_ratio": 0,
                "source_diversity": 0,
                "comment_depth_avg": 0
            },
            "subreddit_breakdown": {}
        }
