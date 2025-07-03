import json
import re
from typing import Dict, List, Any, Optional
from collections import Counter
from datetime import datetime
import requests
from src.utils.reddit_client import RedditClient
from src.utils.llm_client import LLMClient

class EnhancedRedditResearcher:
    def __init__(self):
        self.reddit_client = RedditClient()
        self.llm = LLMClient()
        
    def research_topic_comprehensive(self, topic: str, subreddits: List[str], 
                                   max_posts_per_subreddit: int = 15,
                                   social_media_focus: bool = False) -> Dict[str, Any]:
        """Comprehensive Reddit research with deep insight extraction and social media optimization"""
        
        print(f"🔍 Starting comprehensive Reddit research for: {topic}")
        if social_media_focus:
            print("📱 Optimizing for social media content insights...")
        
        all_reddit_data = []
        subreddit_insights = {}
        
        for subreddit in subreddits:
            print(f"📊 Analyzing r/{subreddit}...")
            posts = self.reddit_client.search_subreddit(subreddit, topic, max_posts_per_subreddit)
            
            if posts:
                # Enhanced post analysis
                analyzed_posts = self._analyze_posts_deeply(posts, topic, social_media_focus)
                all_reddit_data.extend(analyzed_posts)
                subreddit_insights[subreddit] = self._analyze_subreddit_specific(
                    analyzed_posts, subreddit, social_media_focus
                )
        
        if not all_reddit_data:
            return self._generate_comprehensive_fallback(topic, social_media_focus)
        
        # Deep analysis of all data
        comprehensive_analysis = self._perform_deep_analysis(all_reddit_data, topic, social_media_focus)
        
        # Combine with subreddit-specific insights
        comprehensive_analysis['subreddit_breakdown'] = subreddit_insights
        
        # Add social media specific insights
        if social_media_focus:
            comprehensive_analysis['social_media_insights'] = self._extract_social_media_insights(
                all_reddit_data, topic
            )
        
        return comprehensive_analysis
    
    def _analyze_posts_deeply(self, posts: List[Dict], topic: str, social_media_focus: bool) -> List[Dict]:
        """Deep analysis of individual posts with enhanced metadata"""
        
        analyzed_posts = []
        
        for post in posts:
            analyzed_post = post.copy()
            
            # Enhanced post analysis
            analyzed_post['engagement_metrics'] = self._calculate_engagement_metrics(post)
            analyzed_post['content_quality'] = self._assess_content_quality(post)
            analyzed_post['emotional_tone'] = self._analyze_emotional_tone(post)
            analyzed_post['viral_potential'] = self._assess_viral_potential(post)
            analyzed_post['topic_relevance'] = self._calculate_topic_relevance(post, topic)
            
            # Social media specific analysis
            if social_media_focus:
                analyzed_post['social_media_fit'] = self._assess_social_media_fit(post)
                analyzed_post['platform_optimization'] = self._suggest_platform_optimization(post)
            
            # Enhanced comment analysis
            if post.get('comments'):
                analyzed_post['comment_insights'] = self._analyze_comments_deeply(
                    post['comments'], topic, social_media_focus
                )
            
            analyzed_posts.append(analyzed_post)
        
        return analyzed_posts
    
    def _calculate_engagement_metrics(self, post: Dict) -> Dict[str, Any]:
        """Calculate comprehensive engagement metrics"""
        
        score = post.get('score', 0)
        num_comments = len(post.get('comments', []))
        
        # Engagement rate calculation
        engagement_rate = (num_comments / max(score, 1)) * 100
        
        # Engagement quality based on comment depth
        avg_comment_length = 0
        if post.get('comments'):
            total_length = sum(len(comment.get('text', '')) for comment in post['comments'])
            avg_comment_length = total_length / len(post['comments'])
        
        return {
            'raw_score': score,
            'comment_count': num_comments,
            'engagement_rate': round(engagement_rate, 2),
            'avg_comment_length': round(avg_comment_length, 1),
            'engagement_quality': 'high' if avg_comment_length > 100 else 'medium' if avg_comment_length > 50 else 'low'
        }
    
    def _assess_content_quality(self, post: Dict) -> Dict[str, Any]:
        """Assess content quality metrics"""
        
        title = post.get('title', '')
        content = post.get('content', '')
        
        # Content metrics
        title_length = len(title)
        content_length = len(content)
        
        # Quality indicators
        has_question = '?' in title or '?' in content
        has_numbers = bool(re.search(r'\d+', title + content))
        has_actionable_words = any(word in (title + content).lower() 
                                 for word in ['how', 'guide', 'tips', 'steps', 'way'])
        
        # Readability score (simple)
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        avg_sentence_length = words / max(sentences, 1)
        
        quality_score = 0
        if has_question: quality_score += 1
        if has_numbers: quality_score += 1
        if has_actionable_words: quality_score += 1
        if 10 <= avg_sentence_length <= 20: quality_score += 1
        if content_length > 100: quality_score += 1
        
        return {
            'title_length': title_length,
            'content_length': content_length,
            'has_question': has_question,
            'has_numbers': has_numbers,
            'has_actionable_words': has_actionable_words,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'quality_score': quality_score,
            'quality_level': 'high' if quality_score >= 4 else 'medium' if quality_score >= 2 else 'low'
        }
    
    def _analyze_emotional_tone(self, post: Dict) -> Dict[str, Any]:
        """Analyze emotional tone of post"""
        
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        # Emotion keywords
        emotions = {
            'excitement': ['amazing', 'awesome', 'incredible', 'fantastic', 'love', 'excited'],
            'frustration': ['frustrated', 'annoying', 'terrible', 'hate', 'awful', 'worst'],
            'curiosity': ['wondering', 'curious', 'question', 'how', 'why', 'what'],
            'urgency': ['urgent', 'asap', 'quickly', 'immediately', 'help', 'need'],
            'satisfaction': ['satisfied', 'happy', 'pleased', 'good', 'great', 'perfect'],
            'confusion': ['confused', 'lost', 'understand', 'unclear', 'complicated']
        }
        
        emotion_scores = {}
        for emotion, keywords in emotions.items():
            score = sum(1 for keyword in keywords if keyword in text)
            emotion_scores[emotion] = score
        
        # Determine dominant emotion
        dominant_emotion = max(emotion_scores, key=emotion_scores.get) if any(emotion_scores.values()) else 'neutral'
        
        return {
            'emotion_scores': emotion_scores,
            'dominant_emotion': dominant_emotion,
            'emotion_intensity': max(emotion_scores.values()) if emotion_scores.values() else 0,
            'emotional_appeal': 'high' if max(emotion_scores.values()) >= 3 else 'medium' if max(emotion_scores.values()) >= 1 else 'low'
        }
    
    def _assess_viral_potential(self, post: Dict) -> Dict[str, Any]:
        """Assess viral potential of content"""
        
        score = post.get('score', 0)
        num_comments = len(post.get('comments', []))
        
        # Viral indicators
        viral_score = 0
        
        # High engagement
        if score > 100: viral_score += 2
        elif score > 50: viral_score += 1
        
        # High comment ratio
        if num_comments > score * 0.1: viral_score += 2
        elif num_comments > score * 0.05: viral_score += 1
        
        # Content factors
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        viral_words = ['shocking', 'amazing', 'unbelievable', 'secret', 'truth', 'exposed', 'viral']
        if any(word in title for word in viral_words): viral_score += 1
        
        # Emotional content
        emotional_tone = self._analyze_emotional_tone(post)
        if emotional_tone['emotion_intensity'] >= 2: viral_score += 1
        
        return {
            'viral_score': viral_score,
            'viral_potential': 'high' if viral_score >= 5 else 'medium' if viral_score >= 3 else 'low',
            'shareability_factors': self._identify_shareability_factors(post)
        }
    
    def _identify_shareability_factors(self, post: Dict) -> List[str]:
        """Identify factors that make content shareable"""
        
        factors = []
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        # Shareability factors
        if any(word in title for word in ['how to', 'guide', 'tips']): 
            factors.append('educational_value')
        if any(word in title for word in ['amazing', 'incredible', 'shocking']): 
            factors.append('emotional_impact')
        if '?' in title: 
            factors.append('curiosity_gap')
        if any(word in content for word in ['story', 'experience', 'happened']): 
            factors.append('narrative_appeal')
        if len(post.get('comments', [])) > 20: 
            factors.append('discussion_starter')
        
        return factors
    
    def _calculate_topic_relevance(self, post: Dict, topic: str) -> float:
        """Calculate how relevant the post is to the topic"""
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        topic_lower = topic.lower()
        
        # Direct mentions
        title_mentions = title.count(topic_lower)
        content_mentions = content.count(topic_lower)
        
        # Related terms (simplified)
        topic_words = topic_lower.split()
        related_score = 0
        for word in topic_words:
            if word in title: related_score += 2
            if word in content: related_score += 1
        
        # Calculate relevance score (0-10)
        relevance_score = min(10, (title_mentions * 3) + (content_mentions * 2) + related_score)
        
        return round(relevance_score, 1)
    
    def _assess_social_media_fit(self, post: Dict) -> Dict[str, Any]:
        """Assess how well content fits different social media platforms"""
        
        title = post.get('title', '')
        content = post.get('content', '')
        
        platform_fits = {
            'facebook': self._assess_facebook_fit(post),
            'instagram': self._assess_instagram_fit(post),
            'twitter': self._assess_twitter_fit(post),
            'linkedin': self._assess_linkedin_fit(post),
            'tiktok': self._assess_tiktok_fit(post)
        }
        
        # Best platform recommendation
        best_platform = max(platform_fits, key=platform_fits.get)
        
        return {
            'platform_scores': platform_fits,
            'best_platform': best_platform,
            'multi_platform_potential': len([p for p in platform_fits.values() if p >= 7])
        }
    
    def _assess_facebook_fit(self, post: Dict) -> float:
        """Assess Facebook fit (0-10)"""
        
        score = 5.0  # Base score
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        # Facebook factors
        if len(content) > 100: score += 1  # Longer content works
        if any(word in title for word in ['family', 'friends', 'community']): score += 1
        if post.get('engagement_metrics', {}).get('comment_count', 0) > 5: score += 1
        if 'story' in content: score += 1
        if '?' in title: score += 0.5  # Questions generate engagement
        
        return min(10.0, score)
    
    def _assess_instagram_fit(self, post: Dict) -> float:
        """Assess Instagram fit (0-10)"""
        
        score = 5.0  # Base score
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        # Instagram factors
        if any(word in title for word in ['beautiful', 'aesthetic', 'visual', 'photo']): score += 2
        if len(title) <= 150: score += 1  # Shorter captions work better
        if any(word in content for word in ['lifestyle', 'inspiration', 'motivation']): score += 1
        if post.get('emotional_tone', {}).get('dominant_emotion') == 'excitement': score += 1
        
        return min(10.0, score)
    
    def _assess_twitter_fit(self, post: Dict) -> float:
        """Assess Twitter fit (0-10)"""
        
        score = 5.0  # Base score
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        # Twitter factors
        if len(title) <= 280: score += 2  # Character limit
        if any(word in title for word in ['breaking', 'news', 'update', 'thread']): score += 1
        if '?' in title: score += 1  # Questions work well
        if any(word in content for word in ['opinion', 'hot take', 'unpopular']): score += 1
        
        return min(10.0, score)
    
    def _assess_linkedin_fit(self, post: Dict) -> float:
        """Assess LinkedIn fit (0-10)"""
        
        score = 5.0  # Base score
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        # LinkedIn factors
        if any(word in title for word in ['professional', 'career', 'business', 'industry']): score += 2
        if any(word in content for word in ['experience', 'lesson', 'advice', 'tips']): score += 1
        if len(content) > 200: score += 1  # Longer content works on LinkedIn
        if 'story' in content: score += 1  # Professional stories
        
        return min(10.0, score)
    
    def _assess_tiktok_fit(self, post: Dict) -> float:
        """Assess TikTok fit (0-10)"""
        
        score = 5.0  # Base score
        
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        
        # TikTok factors
        if any(word in title for word in ['viral', 'trending', 'challenge', 'hack']): score += 2
        if post.get('emotional_tone', {}).get('emotion_intensity', 0) >= 2: score += 1
        if len(title) <= 100: score += 1  # Short and punchy
        if any(word in content for word in ['quick', 'easy', 'seconds', 'minutes']): score += 1
        
        return min(10.0, score)
    
    def _suggest_platform_optimization(self, post: Dict) -> Dict[str, List[str]]:
        """Suggest optimizations for different platforms"""
        
        return {
            'facebook': [
                'Add engaging questions to spark comments',
                'Include personal stories or experiences',
                'Use longer-form content with clear paragraphs',
                'Add call-to-action for sharing'
            ],
            'instagram': [
                'Focus on visual storytelling',
                'Use relevant hashtags',
                'Keep captions concise but engaging',
                'Include lifestyle or inspirational angles'
            ],
            'twitter': [
                'Keep under 280 characters',
                'Use trending hashtags',
                'Create quote-worthy statements',
                'Consider thread format for longer content'
            ],
            'linkedin': [
                'Add professional insights or lessons learned',
                'Include industry-specific context',
                'Share actionable business advice',
                'Use professional tone and formatting'
            ],
            'tiktok': [
                'Focus on quick, actionable tips',
                'Use trending sounds or challenges',
                'Keep content under 60 seconds',
                'Add hook in first 3 seconds'
            ]
        }
    
    def _analyze_comments_deeply(self, comments: List[Dict], topic: str, social_media_focus: bool) -> Dict[str, Any]:
        """Deep analysis of comments with social media insights"""
        
        if not comments:
            return {'total_comments': 0, 'insights': []}
        
        comment_insights = {
            'total_comments': len(comments),
            'avg_comment_length': sum(len(c.get('text', '')) for c in comments) / len(comments),
            'engagement_patterns': self._analyze_engagement_patterns(comments),
            'sentiment_distribution': self._analyze_comment_sentiment(comments),
            'question_types': self._extract_question_types(comments),
            'pain_points_mentioned': self._extract_pain_points(comments),
            'popular_phrases': self._extract_popular_phrases(comments)
        }
        
        if social_media_focus:
            comment_insights['social_media_angles'] = self._extract_social_media_angles(comments)
        
        return comment_insights
    
    def _analyze_engagement_patterns(self, comments: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement patterns in comments"""
        
        # Simple engagement analysis
        short_comments = sum(1 for c in comments if len(c.get('text', '')) < 50)
        long_comments = sum(1 for c in comments if len(c.get('text', '')) > 200)
        
        return {
            'short_comments_ratio': round(short_comments / len(comments), 2),
            'long_comments_ratio': round(long_comments / len(comments), 2),
            'engagement_type': 'high_engagement' if long_comments > short_comments else 'quick_reactions'
        }
    
    def _analyze_comment_sentiment(self, comments: List[Dict]) -> Dict[str, float]:
        """Analyze sentiment distribution in comments"""
        
        positive_words = ['great', 'amazing', 'love', 'excellent', 'perfect', 'awesome']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'worst', 'horrible']
        
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for comment in comments:
            text = comment.get('text', '').lower()
            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)
            
            if pos_score > neg_score:
                sentiment_counts['positive'] += 1
            elif neg_score > pos_score:
                sentiment_counts['negative'] += 1
            else:
                sentiment_counts['neutral'] += 1
        
        total = len(comments)
        return {
            'positive_ratio': round(sentiment_counts['positive'] / total, 2),
            'negative_ratio': round(sentiment_counts['negative'] / total, 2),
            'neutral_ratio': round(sentiment_counts['neutral'] / total, 2)
        }
    
    def _extract_question_types(self, comments: List[Dict]) -> List[str]:
        """Extract common question types from comments"""
        
        questions = []
        for comment in comments:
            text = comment.get('text', '')
            if '?' in text:
                # Extract question sentences
                sentences = text.split('?')
                for sentence in sentences:
                    if sentence.strip():
                        questions.append(sentence.strip() + '?')
        
        return questions[:10]  # Return top 10 questions
    
    def _extract_pain_points(self, comments: List[Dict]) -> List[str]:
        """Extract pain points mentioned in comments"""
        
        pain_indicators = ['problem', 'issue', 'trouble', 'difficult', 'struggling', 'frustrated']
        pain_points = []
        
        for comment in comments:
            text = comment.get('text', '').lower()
            for indicator in pain_indicators:
                if indicator in text:
                    # Extract sentence containing pain point
                    sentences = text.split('.')
                    for sentence in sentences:
                        if indicator in sentence:
                            pain_points.append(sentence.strip())
                            break
        
        return list(set(pain_points))[:5]  # Return top 5 unique pain points
    
    def _extract_popular_phrases(self, comments: List[Dict]) -> List[str]:
        """Extract popular phrases from comments"""
        
        all_text = ' '.join([comment.get('text', '') for comment in comments]).lower()
        words = re.findall(r'\b\w+\b', all_text)
        
        # Get most common phrases (2-3 words)
        phrase_counter = Counter()
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 5:  # Avoid very short phrases
                phrase_counter[phrase] += 1
        
        return [phrase for phrase, count in phrase_counter.most_common(10)]
    
    def _extract_social_media_angles(self, comments: List[Dict]) -> List[str]:
        """Extract social media content angles from comments"""
        
        angles = []
        for comment in comments:
            text = comment.get('text', '').lower()
            
            # Common social media angles
            if 'story' in text or 'experience' in text:
                angles.append('personal_story')
            if 'tip' in text or 'advice' in text:
                angles.append('tips_and_advice')
            if 'question' in text or '?' in text:
                angles.append('question_based')
            if 'list' in text or 'steps' in text:
                angles.append('listicle')
            if 'comparison' in text or 'vs' in text:
                angles.append('comparison')
        
        return list(set(angles))
    
    def _extract_social_media_insights(self, reddit_data: List[Dict], topic: str) -> Dict[str, Any]:
        """Extract insights specifically for social media content creation"""
        
        # Aggregate social media fit scores
        platform_scores = {'facebook': [], 'instagram': [], 'twitter': [], 'linkedin': [], 'tiktok': []}
        
        for post in reddit_data:
            social_fit = post.get('social_media_fit', {})
            platform_scores_post = social_fit.get('platform_scores', {})
            
            for platform, score in platform_scores_post.items():
                platform_scores[platform].append(score)
        
        # Calculate average scores
        avg_platform_scores = {}
        for platform, scores in platform_scores.items():
            avg_platform_scores[platform] = round(sum(scores) / len(scores), 1) if scores else 0
        
        # Best performing content types
        high_viral_posts = [post for post in reddit_data 
                          if post.get('viral_potential', {}).get('viral_potential') == 'high']
        
        # Content format preferences
        content_formats = Counter()
        for post in reddit_data:
            factors = post.get('viral_potential', {}).get('shareability_factors', [])
            content_formats.update(factors)
        
        return {
            'platform_performance': avg_platform_scores,
            'best_platform': max(avg_platform_scores, key=avg_platform_scores.get),
            'viral_content_patterns': self._analyze_viral_patterns(high_viral_posts),
            'preferred_content_formats': dict(content_formats.most_common(5)),
            'optimal_posting_strategy': self._generate_posting_strategy(reddit_data),
            'audience_engagement_preferences': self._analyze_audience_preferences(reddit_data)
        }
    
    def _analyze_viral_patterns(self, viral_posts: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in viral content"""
        
        if not viral_posts:
            return {'patterns': [], 'common_elements': []}
        
        patterns = []
        
        # Analyze titles
        titles = [post.get('title', '') for post in viral_posts]
        title_lengths = [len(title) for title in titles]
        
        # Analyze emotional tones
        dominant_emotions = [post.get('emotional_tone', {}).get('dominant_emotion', 'neutral') 
                           for post in viral_posts]
        emotion_counter = Counter(dominant_emotions)
        
        # Analyze engagement
        avg_engagement = sum(post.get('engagement_metrics', {}).get('engagement_rate', 0) 
                           for post in viral_posts) / len(viral_posts)
        
        return {
            'avg_title_length': round(sum(title_lengths) / len(title_lengths), 1),
            'most_common_emotion': emotion_counter.most_common(1)[0][0] if emotion_counter else 'neutral',
            'avg_engagement_rate': round(avg_engagement, 2),
            'common_elements': self._identify_common_viral_elements(viral_posts)
        }
    
    def _identify_common_viral_elements(self, viral_posts: List[Dict]) -> List[str]:
        """Identify common elements in viral posts"""
        
        elements = []
        
        for post in viral_posts:
            title = post.get('title', '').lower()
            
            # Check for common viral elements
            if 'how' in title: elements.append('how-to format')
            if '?' in title: elements.append('question format')
            if any(word in title for word in ['secret', 'truth', 'revealed']): elements.append('curiosity gap')
            if any(word in title for word in ['amazing', 'incredible', 'shocking']): elements.append('emotional trigger')
            if re.search(r'\d+', title): elements.append('numbers in title')
        
        return list(set(elements))
    
    def _generate_posting_strategy(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Generate optimal posting strategy based on Reddit insights"""
        
        # Analyze successful post characteristics
        high_engagement_posts = [post for post in reddit_data 
                               if post.get('engagement_metrics', {}).get('engagement_rate', 0) > 50]
        
        if not high_engagement_posts:
            return {'strategy': 'focus_on_engagement', 'recommendations': []}
        
        # Common characteristics of successful posts
        successful_lengths = [len(post.get('title', '')) for post in high_engagement_posts]
        avg_successful_length = sum(successful_lengths) / len(successful_lengths)
        
        # Successful emotions
        successful_emotions = [post.get('emotional_tone', {}).get('dominant_emotion', 'neutral') 
                             for post in high_engagement_posts]
        emotion_counter = Counter(successful_emotions)
        
        return {
            'optimal_title_length': f"{int(avg_successful_length - 10)}-{int(avg_successful_length + 10)} characters",
            'best_emotional_tone': emotion_counter.most_common(1)[0][0] if emotion_counter else 'neutral',
            'recommended_formats': self._get_recommended_formats(high_engagement_posts),
            'posting_frequency': 'daily' if len(high_engagement_posts) > 10 else 'weekly',
            'engagement_tactics': self._generate_engagement_tactics(high_engagement_posts)
        }
    
    def _get_recommended_formats(self, successful_posts: List[Dict]) -> List[str]:
        """Get recommended content formats based on successful posts"""
        
        formats = []
        
        for post in successful_posts:
            title = post.get('title', '').lower()
            
            if 'how' in title: formats.append('how-to guides')
            if '?' in title: formats.append('question-based posts')
            if 'list' in title or re.search(r'\d+', title): formats.append('listicles')
            if 'story' in title or 'experience' in title: formats.append('personal stories')
            if 'vs' in title or 'comparison' in title: formats.append('comparisons')
        
        return list(set(formats))
    
    def _generate_engagement_tactics(self, successful_posts: List[Dict]) -> List[str]:
        """Generate engagement tactics based on successful posts"""
        
        tactics = []
        
        # Analyze comment patterns
        for post in successful_posts:
            comments = post.get('comment_insights', {})
            
            if comments.get('question_types'):
                tactics.append('Ask engaging questions')
            if comments.get('engagement_patterns', {}).get('engagement_type') == 'high_engagement':
                tactics.append('Encourage detailed responses')
            if post.get('emotional_tone', {}).get('emotion_intensity', 0) >= 2:
                tactics.append('Use emotional storytelling')
        
        return list(set(tactics)) if tactics else ['Focus on community engagement']
    
    def _analyze_audience_preferences(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Analyze audience preferences from Reddit data"""
        
        preferences = {
            'content_length': 'medium',
            'interaction_style': 'conversational',
            'preferred_topics': [],
            'engagement_triggers': []
        }
        
        # Analyze content length preferences
        high_engagement_posts = [post for post in reddit_data 
                               if post.get('engagement_metrics', {}).get('engagement_rate', 0) > 30]
        
        if high_engagement_posts:
            content_lengths = [post.get('content_quality', {}).get('content_length', 0) 
                             for post in high_engagement_posts]
            avg_length = sum(content_lengths) / len(content_lengths)
            
            if avg_length > 500:
                preferences['content_length'] = 'long'
            elif avg_length > 200:
                preferences['content_length'] = 'medium'
            else:
                preferences['content_length'] = 'short'
        
        # Analyze interaction preferences
        question_posts = [post for post in reddit_data 
                         if post.get('content_quality', {}).get('has_question')]
        
        if len(question_posts) > len(reddit_data) * 0.3:
            preferences['interaction_style'] = 'question-based'
        
        # Extract engagement triggers
        for post in high_engagement_posts:
            emotional_tone = post.get('emotional_tone', {})
            dominant_emotion = emotional_tone.get('dominant_emotion', 'neutral')
            
            if dominant_emotion != 'neutral':
                preferences['engagement_triggers'].append(dominant_emotion)
        
        preferences['engagement_triggers'] = list(set(preferences['engagement_triggers']))
        
        return preferences
    
    def _perform_deep_analysis(self, reddit_data: List[Dict], topic: str, social_media_focus: bool) -> Dict[str, Any]:
        """Enhanced deep analysis with social media focus"""
        
        # Prepare data for LLM analysis
        high_engagement_posts = sorted(reddit_data, key=lambda x: x.get('engagement_metrics', {}).get('engagement_rate', 0), reverse=True)[:10]
        
        analysis_data = {
            'posts': [],
            'comments': [],
            'questions': [],
            'complaints': [],
            'recommendations': [],
            'viral_content': [],
            'social_media_insights': []
        }
        
        for post in high_engagement_posts:
            post_data = {
                'title': post['title'],
                'content': post['content'][:300],
                'engagement_metrics': post.get('engagement_metrics', {}),
                'emotional_tone': post.get('emotional_tone', {}),
                'viral_potential': post.get('viral_potential', {}),
                'social_media_fit': post.get('social_media_fit', {}),
                'subreddit': post.get('subreddit', 'unknown')
            }
            analysis_data['posts'].append(post_data)
            
            # Add viral content if applicable
            if post.get('viral_potential', {}).get('viral_potential') == 'high':
                analysis_data['viral_content'].append({
                    'title': post['title'],
                    'viral_factors': post.get('viral_potential', {}).get('shareability_factors', [])
                })
            
            # Categorize comments with enhanced analysis
            comment_insights = post.get('comment_insights', {})
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
        
        # Enhanced LLM prompt for social media
        prompt = f"""
        Perform deep customer research analysis on Reddit discussions about "{topic}":
        
        Data: {json.dumps(analysis_data, indent=2)}
        
        Social Media Focus: {social_media_focus}
        
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
                "search_intent_phrases": ["phrases indicating search behavior"],
                "social_media_language": ["casual phrases perfect for social media"]
            }},
            "content_opportunity_gaps": {{
                "missing_information": ["info customers can't find"],
                "underserved_questions": ["questions without good answers"],
                "competitive_weaknesses": ["where competitors fail customers"],
                "emerging_trends": ["new patterns in customer needs"],
                "viral_content_opportunities": ["topics with high viral potential"]
            }},
            "authenticity_markers": {{
                "real_customer_quotes": ["5-7 powerful authentic quotes"],
                "specific_use_cases": ["concrete examples customers mention"],
                "failure_stories": ["what went wrong for customers"],
                "success_stories": ["what worked for customers"],
                "viral_success_patterns": ["what made content go viral"]
            }},
            "actionable_content_strategy": {{
                "high_impact_topics": ["content topics with highest engagement potential"],
                "content_formats_preferred": ["formats customers respond to best"],
                "distribution_insights": ["where and how to share content"],
                "timing_patterns": ["when customers are most active/receptive"],
                "social_media_optimization": {{
                    "platform_specific_strategies": ["strategies for each platform"],
                    "viral_content_formulas": ["formulas for creating viral content"],
                    "engagement_hooks": ["opening lines that grab attention"],
                    "call_to_action_strategies": ["effective CTAs for each platform"]
                }}
            }}
        }}
        
        Focus on extracting insights that would be impossible for AI to generate without real customer data.
        Prioritize authenticity, emotional intelligence, and actionable business insights.
        {f"Pay special attention to social media content optimization and viral potential." if social_media_focus else ""}
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            parsed_response = json.loads(response)
            
            # Add quantitative analysis
            parsed_response['quantitative_insights'] = self._calculate_metrics(reddit_data)
            parsed_response['research_quality_score'] = self._assess_research_quality(reddit_data)
            
            # Add social media specific metrics
            if social_media_focus:
                parsed_response['social_media_metrics'] = self._calculate_social_media_metrics(reddit_data)
            
            return parsed_response
            
        except json.JSONDecodeError:
            return self._generate_comprehensive_fallback(topic, social_media_focus)
    
    def _calculate_social_media_metrics(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Calculate social media specific metrics"""
        
        if not reddit_data:
            return {}
        
        # Platform performance metrics
        platform_scores = {'facebook': [], 'instagram': [], 'twitter': [], 'linkedin': [], 'tiktok': []}
        
        for post in reddit_data:
            social_fit = post.get('social_media_fit', {})
            platform_scores_post = social_fit.get('platform_scores', {})
            
            for platform, score in platform_scores_post.items():
                platform_scores[platform].append(score)
        
        # Calculate averages
        avg_platform_scores = {}
        for platform, scores in platform_scores.items():
            avg_platform_scores[platform] = round(sum(scores) / len(scores), 1) if scores else 0
        
        # Viral content metrics
        viral_posts = [post for post in reddit_data 
                      if post.get('viral_potential', {}).get('viral_potential') == 'high']
        
        return {
            'platform_performance': avg_platform_scores,
            'viral_content_ratio': round(len(viral_posts) / len(reddit_data), 2),
            'avg_engagement_rate': round(sum(post.get('engagement_metrics', {}).get('engagement_rate', 0) 
                                          for post in reddit_data) / len(reddit_data), 2),
            'content_quality_distribution': self._calculate_quality_distribution(reddit_data),
            'emotional_engagement_score': self._calculate_emotional_score(reddit_data)
        }
    
    def _calculate_quality_distribution(self, reddit_data: List[Dict]) -> Dict[str, float]:
        """Calculate content quality distribution"""
        
        quality_levels = {'high': 0, 'medium': 0, 'low': 0}
        
        for post in reddit_data:
            quality_level = post.get('content_quality', {}).get('quality_level', 'medium')
            quality_levels[quality_level] += 1
        
        total = len(reddit_data)
        return {
            'high_quality_ratio': round(quality_levels['high'] / total, 2),
            'medium_quality_ratio': round(quality_levels['medium'] / total, 2),
            'low_quality_ratio': round(quality_levels['low'] / total, 2)
        }
    
    def _calculate_emotional_score(self, reddit_data: List[Dict]) -> float:
        """Calculate overall emotional engagement score"""
        
        emotional_scores = []
        
        for post in reddit_data:
            emotional_tone = post.get('emotional_tone', {})
            intensity = emotional_tone.get('emotion_intensity', 0)
            emotional_scores.append(intensity)
        
        return round(sum(emotional_scores) / len(emotional_scores), 2) if emotional_scores else 0
    
    def _generate_comprehensive_fallback(self, topic: str, social_media_focus: bool = False) -> Dict[str, Any]:
        """Enhanced fallback with social media considerations"""
        
        fallback = {
            "pain_point_analysis": {
                "critical_pain_points": [
                    f"Lack of clear guidance on {topic}",
                    f"Too many options for {topic}",
                    f"Difficulty finding reliable {topic} information",
                    f"Overwhelming amount of {topic} content"
                ],
                "emotional_triggers": ["confusion", "overwhelm", "frustration", "urgency"],
                "urgency_indicators": ["need help", "urgent", "asap", "quickly"],
                "financial_impact": ["cost-effective", "budget-friendly", "expensive", "worth it"],
                "time_constraints": ["quick solution", "time-sensitive", "immediate", "fast"]
            },
            "customer_journey_insights": {
                "awareness_stage_questions": [f"What is {topic}?", f"Do I need {topic}?", f"How does {topic} work?"],
                "consideration_stage_concerns": [f"Best {topic} options", f"How to choose {topic}", f"{topic} comparison"],
                "decision_stage_barriers": ["Price concerns", "Trust issues", "Complexity", "Time investment"],
                "post_purchase_issues": ["Implementation challenges", "Support needs", "Results not as expected"]
            },
            "language_intelligence": {
                "customer_vocabulary": [f"{topic} help", f"best {topic}", f"how to {topic}", f"{topic} guide"],
                "technical_vs_layman": "mixed",
                "emotional_language": ["frustrated", "confused", "hopeful", "excited"],
                "search_intent_phrases": [f"find {topic}", f"learn {topic}", f"get {topic}"],
                "social_media_language": [f"anyone else struggling with {topic}?", f"{topic} made easy", f"quick {topic} tip"]
            },
            "content_opportunity_gaps": {
                "missing_information": ["Step-by-step guides", "Real examples", "Cost breakdowns", "Beginner tutorials"],
                "underserved_questions": [f"How to get started with {topic}", f"Common {topic} mistakes", f"{topic} for beginners"],
                "competitive_weaknesses": ["Generic advice", "No real examples", "Poor explanations", "Outdated information"],
                "emerging_trends": ["Increased demand for personalized advice", "Visual learning preferences"],
                "viral_content_opportunities": [f"{topic} myths debunked", f"Surprising {topic} facts", f"{topic} transformation stories"]
            },
            "authenticity_markers": {
                "real_customer_quotes": [
                    f"I'm completely lost with {topic}",
                    f"Need help understanding {topic}",
                    f"Looking for reliable {topic} advice",
                    f"Anyone else find {topic} confusing?",
                    f"Finally figured out {topic}!"
                ],
                "specific_use_cases": [f"Business use of {topic}", f"Personal {topic} needs", f"{topic} for beginners"],
                "failure_stories": ["Chose wrong option", "Wasted money", "Got confused", "Gave up too early"],
                "success_stories": ["Found perfect solution", "Saved time and money", "Finally understood", "Life-changing results"],
                "viral_success_patterns": ["Before/after transformations", "Myth-busting revelations", "Insider secrets"]
            },
            "actionable_content_strategy": {
                "high_impact_topics": [f"Complete {topic} guide", f"{topic} comparison", f"{topic} mistakes to avoid"],
                "content_formats_preferred": ["step-by-step guides", "comparison tables", "video tutorials", "infographics"],
                "distribution_insights": ["Focus on search-driven content", "Share in relevant communities", "Use social media"],
                "timing_patterns": ["Peak interest during business hours", "Weekend engagement for personal topics"]
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
        
        # Add social media specific fallback
        if social_media_focus:
            fallback["actionable_content_strategy"]["social_media_optimization"] = {
                "platform_specific_strategies": [
                    "Facebook: Use storytelling and community engagement",
                    "Instagram: Focus on visual appeal and lifestyle",
                    "Twitter: Share quick tips and join conversations",
                    "LinkedIn: Provide professional insights and advice",
                    "TikTok: Create quick, entertaining tutorials"
                ],
                "viral_content_formulas": [
                    "Problem + Solution + Personal Story",
                    "Myth + Truth + Explanation",
                    "Before + After + Process",
                    "Question + Answer + Call to Action"
                ],
                "engagement_hooks": [
                    f"If you're struggling with {topic}...",
                    f"Here's what nobody tells you about {topic}",
                    f"I wish I knew this {topic} secret earlier",
                    f"Stop doing {topic} wrong"
                ],
                "call_to_action_strategies": [
                    "Ask questions to encourage comments",
                    "Request shares for broader reach",
                    "Create polls for engagement",
                    "Use trending hashtags for visibility"
                ]
            }
            
            fallback["social_media_metrics"] = {
                "platform_performance": {
                    "facebook": 6.0,
                    "instagram": 5.5,
                    "twitter": 6.5,
                    "linkedin": 7.0,
                    "tiktok": 5.0
                },
                "viral_content_ratio": 0.1,
                "avg_engagement_rate": 25.0,
                "content_quality_distribution": {
                    "high_quality_ratio": 0.3,
                    "medium_quality_ratio": 0.5,
                    "low_quality_ratio": 0.2
                },
                "emotional_engagement_score": 2.5
            }
        
        return fallback
    
    # Existing helper methods remain the same
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
    
    def _analyze_subreddit_specific(self, posts: List[Dict], subreddit: str, social_media_focus: bool = False) -> Dict[str, Any]:
        """Enhanced subreddit-specific analysis"""
        
        if not posts:
            return {'post_count': 0, 'insights': 'No posts found'}
        
        total_posts = len(posts)
        total_engagement = sum(post.get('engagement_metrics', {}).get('raw_score', 0) for post in posts)
        
        # Calculate average metrics
        avg_engagement_rate = sum(post.get('engagement_metrics', {}).get('engagement_rate', 0) for post in posts) / total_posts
        avg_quality_score = sum(post.get('content_quality', {}).get('quality_score', 0) for post in posts) / total_posts
        
        # Analyze dominant emotional tone
        emotions = [post.get('emotional_tone', {}).get('dominant_emotion', 'neutral') for post in posts]
        emotion_counter = Counter(emotions)
        dominant_emotion = emotion_counter.most_common(1)[0][0] if emotion_counter else 'neutral'
        
        # Analyze content themes
        themes = []
        for post in posts:
            title = post.get('title', '').lower()
            if 'how' in title: themes.append('how-to')
            if '?' in title: themes.append('question')
            if 'review' in title: themes.append('review')
            if 'advice' in title: themes.append('advice')
            if 'story' in title: themes.append('story')
        
        theme_counter = Counter(themes)
        
        analysis = {
            'post_count': total_posts,
            'total_engagement': total_engagement,
            'avg_engagement_rate': round(avg_engagement_rate, 2),
            'avg_content_quality': round(avg_quality_score, 1),
            'dominant_emotion': dominant_emotion,
            'top_themes': dict(theme_counter.most_common(3)),
            'audience_level': self._determine_audience_level(subreddit, posts),
            'content_style': self._analyze_content_style(posts)
        }
        
        # Add social media insights
        if social_media_focus:
            platform_scores = {}
            for platform in ['facebook', 'instagram', 'twitter', 'linkedin', 'tiktok']:
                scores = [post.get('social_media_fit', {}).get('platform_scores', {}).get(platform, 0) for post in posts]
                platform_scores[platform] = round(sum(scores) / len(scores), 1) if scores else 0
            
            analysis['social_media_performance'] = platform_scores
            analysis['best_social_platform'] = max(platform_scores, key=platform_scores.get)
        
        return analysis
    
    def _determine_audience_level(self, subreddit: str, posts: List[Dict]) -> str:
        """Determine the technical level of the audience"""
        
        # Analyze technical complexity
        technical_score = 0
        beginner_score = 0
        
        for post in posts:
            content_quality = post.get('content_quality', {})
            
            if content_quality.get('avg_sentence_length', 0) > 20:
                technical_score += 1
            if content_quality.get('has_actionable_words'):
                beginner_score += 1
        
        # Subreddit-specific adjustments
        if any(word in subreddit.lower() for word in ['beginner', 'learn', 'help']):
            beginner_score += 5
        if any(word in subreddit.lower() for word in ['advanced', 'pro', 'expert']):
            technical_score += 5
        
        if technical_score > beginner_score * 1.5:
            return 'advanced'
        elif beginner_score > technical_score * 1.5:
            return 'beginner'
        else:
            return 'mixed'
    
    def _analyze_content_style(self, posts: List[Dict]) -> str:
        """Analyze the predominant content style"""
        
        styles = {'formal': 0, 'casual': 0, 'storytelling': 0, 'instructional': 0}
        
        for post in posts:
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            
            # Analyze style indicators
            if any(word in title for word in ['guide', 'tutorial', 'how to', 'steps']):
                styles['instructional'] += 1
            if any(word in title for word in ['story', 'experience', 'happened', 'journey']):
                styles['storytelling'] += 1
            if len(title.split()) > 10 and not any(word in title for word in ['i', 'my', 'me']):
                styles['formal'] += 1
            else:
                styles['casual'] += 1
        
        return max(styles, key=styles.get)
    
    def _calculate_metrics(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Enhanced metrics calculation"""
        
        if not reddit_data:
            return {
                'total_posts_analyzed': 0,
                'total_engagement_score': 0,
                'avg_engagement_per_post': 0,
                'total_comments_analyzed': 0,
                'top_keywords': {},
                'data_freshness_score': 0,
                'content_quality_metrics': {},
                'viral_content_metrics': {}
            }
        
        total_posts = len(reddit_data)
        total_engagement = sum(post.get('engagement_metrics', {}).get('raw_score', 0) for post in reddit_data)
        total_comments = sum(post.get('engagement_metrics', {}).get('comment_count', 0) for post in reddit_data)
        
        # Content quality metrics
        quality_scores = [post.get('content_quality', {}).get('quality_score', 0) for post in reddit_data]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Viral content metrics
        viral_posts = [post for post in reddit_data if post.get('viral_potential', {}).get('viral_potential') == 'high']
        viral_ratio = len(viral_posts) / total_posts if total_posts > 0 else 0
        
        # Extract keywords from titles
        all_titles = ' '.join([post.get('title', '') for post in reddit_data]).lower()
        words = re.findall(r'\b\w+\b', all_titles)
        word_freq = Counter(words)
        top_keywords = dict(word_freq.most_common(20))
        
        return {
            'total_posts_analyzed': total_posts,
            'total_engagement_score': total_engagement,
            'avg_engagement_per_post': round(total_engagement / total_posts, 2) if total_posts > 0 else 0,
            'total_comments_analyzed': total_comments,
            'top_keywords': top_keywords,
            'data_freshness_score': self._calculate_freshness_score(reddit_data),
            'content_quality_metrics': {
                'avg_quality_score': round(avg_quality, 1),
                'high_quality_ratio': round(len([q for q in quality_scores if q >= 4]) / len(quality_scores), 2) if quality_scores else 0
            },
            'viral_content_metrics': {
                'viral_post_ratio': round(viral_ratio, 2),
                'viral_post_count': len(viral_posts),
                'avg_viral_score': round(sum(post.get('viral_potential', {}).get('viral_score', 0) for post in viral_posts) / len(viral_posts), 1) if viral_posts else 0
            }
        }
    
    def _calculate_freshness_score(self, reddit_data: List[Dict]) -> float:
        """Calculate how fresh/recent the data is"""
        # This would ideally use actual post timestamps
        # For now, return a base score based on engagement patterns
        
        if not reddit_data:
            return 0
        
        # Use engagement as a proxy for freshness
        avg_engagement = sum(post.get('engagement_metrics', {}).get('engagement_rate', 0) for post in reddit_data) / len(reddit_data)
        
        # Higher engagement typically indicates fresher, more relevant content
        freshness_score = min(100, avg_engagement * 2)
        
        return round(freshness_score, 1)
    
    def _assess_research_quality(self, reddit_data: List[Dict]) -> Dict[str, Any]:
        """Enhanced research quality assessment"""
        
        if not reddit_data:
            return {
                'overall_score': 0,
                'reliability': 'poor',
                'data_richness': 'insufficient',
                'engagement_quality': 'low'
            }
        
        # Calculate quality factors
        total_posts = len(reddit_data)
        high_engagement_posts = sum(1 for post in reddit_data if post.get('engagement_metrics', {}).get('engagement_rate', 0) > 30)
        high_quality_posts = sum(1 for post in reddit_data if post.get('content_quality', {}).get('quality_score', 0) >= 4)
        
        diverse_sources = len(set(post.get('subreddit', 'unknown') for post in reddit_data))
        total_comments = sum(post.get('engagement_metrics', {}).get('comment_count', 0) for post in reddit_data)
        
        # Calculate component scores
        engagement_score = (high_engagement_posts / total_posts) * 40
        quality_score = (high_quality_posts / total_posts) * 30
        diversity_score = min(diverse_sources * 10, 20)
        depth_score = min((total_comments / total_posts) * 2, 10)
        
        overall_score = engagement_score + quality_score + diversity_score + depth_score
        
        # Determine reliability level
        if overall_score >= 80:
            reliability = 'excellent'
        elif overall_score >= 60:
            reliability = 'good'
        elif overall_score >= 40:
            reliability = 'fair'
        else:
            reliability = 'poor'
        
        # Data richness assessment
        if total_comments > total_posts * 5:
            data_richness = 'very_rich'
        elif total_comments > total_posts * 2:
            data_richness = 'rich'
        elif total_comments > total_posts:
            data_richness = 'moderate'
        else:
            data_richness = 'limited'
        
        return {
            'overall_score': round(overall_score, 1),
            'reliability': reliability,
            'data_richness': data_richness,
            'engagement_quality': 'high' if high_engagement_posts > total_posts * 0.3 else 'medium' if high_engagement_posts > total_posts * 0.1 else 'low',
            'high_engagement_ratio': round(high_engagement_posts / total_posts, 2),
            'high_quality_ratio': round(high_quality_posts / total_posts, 2),
            'source_diversity': diverse_sources,
            'comment_depth_avg': round(total_comments / total_posts, 1)
        }
