import os
import json
import requests
import re
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime

# Conditional Reddit import - prevents crashes if not installed
try:
    import praw
    PRAW_AVAILABLE = True
    print("✅ PRAW (Reddit API) library loaded successfully")
except ImportError:
    PRAW_AVAILABLE = False
    print("⚠️ PRAW not available - Reddit research will use simulation mode")

# Initialize FastAPI app
app = FastAPI(title="Zee SEO Tool - AI Content Creation Agent")

# AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")

# Reddit API Configuration from Railway
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET") 
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ZeeSEOTool/1.0 by ZeeshanBashir")

class AIAgent:
    def __init__(self):
        self.anthropic_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
    def call_ai(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", max_tokens: int = 1000):
        """Make API call to AI"""
        try:
            if messages and messages[0].get("role") == "user":
                user_message = messages[0]["content"]
            else:
                user_message = "Please help with this request."
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=self.anthropic_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                return f"Using demo mode - AI API Error: {response.status_code}"
                
        except Exception as e:
            return f"Using demo mode - AI Error: {str(e)}"

class IntentClassifier:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def classify_intent(self, topic: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze this content topic and classify the user intent: "{topic}"
        
        Respond with JSON format only:
        {{
            "primary_intent": "informational/commercial/transactional/navigational",
            "search_stage": "awareness/consideration/decision",
            "target_audience": "describe the likely audience",
            "content_complexity": "beginner/intermediate/advanced",
            "urgency_level": "low/medium/high"
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.ai_agent.call_ai(messages)
        
        try:
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
            
        return {
            "primary_intent": "informational",
            "search_stage": "consideration", 
            "target_audience": "general audience",
            "content_complexity": "intermediate",
            "urgency_level": "medium"
        }

class JourneyMapper:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def map_customer_journey(self, topic: str, intent_data: Dict) -> Dict[str, Any]:
        prompt = f"""
        For the topic "{topic}" with intent "{intent_data.get('primary_intent', 'informational')}", 
        map the customer journey stage and identify key pain points.
        
        Respond with JSON format only:
        {{
            "primary_stage": "awareness/consideration/decision/retention",
            "key_pain_points": ["pain point 1", "pain point 2", "pain point 3"],
            "customer_questions": ["question 1", "question 2", "question 3"],
            "emotional_state": "describe customer emotions",
            "next_actions": ["action 1", "action 2"]
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.ai_agent.call_ai(messages)
        
        try:
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
            
        return {
            "primary_stage": "consideration",
            "key_pain_points": ["Uncertainty about options", "Budget constraints", "Time limitations"],
            "customer_questions": ["Is this right for me?", "How much does it cost?", "How long will it take?"],
            "emotional_state": "Cautiously optimistic but seeking validation",
            "next_actions": ["Research more options", "Compare prices", "Read reviews"]
        }

class RedditAPIClient:
    def __init__(self):
        """Initialize Reddit API client with Railway environment variables - SAFE VERSION"""
        self.reddit = None
        self.praw_available = PRAW_AVAILABLE
        
        if not PRAW_AVAILABLE:
            print("⚠️ PRAW library not available - using simulation mode")
            return
            
        try:
            if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET]):
                print("⚠️ Reddit API credentials not found in Railway environment")
                return
            
            print(f"🔗 Initializing Reddit API client...")
            
            # Initialize PRAW Reddit instance
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT,
                check_for_async=False
            )
            
            # Test the connection
            self._test_connection()
            print("✅ Reddit API connection successful!")
            
        except Exception as e:
            print(f"❌ Reddit API initialization failed: {str(e)}")
            self.reddit = None
            
    def _test_connection(self):
        """Test Reddit API connection"""
        try:
            if self.reddit:
                subreddit = self.reddit.subreddit('test')
                subreddit.display_name
        except Exception as e:
            raise Exception(f"Reddit API connection test failed: {str(e)}")
    
    def research_topic(self, topic: str, subreddits: List[str]) -> Dict[str, Any]:
        """Research topic using real Reddit API or fallback to simulation"""
        if not self.reddit or not self.praw_available:
            return self._simulate_reddit_research(topic, subreddits)
        
        try:
            print(f"🔍 Searching Reddit for insights on: {topic}")
            
            insights = {
                'customer_voice': {
                    'common_language': [],
                    'frequent_questions': [],
                    'complaints': [],
                    'recommendations': []
                },
                'trending_discussions': [],
                'sentiment_analysis': 'neutral',
                'community_size': '0',
                'authenticity_markers': [],
                'real_experiences': []
            }
            
            # Search across provided subreddits
            for subreddit_name in subreddits[:3]:
                try:
                    subreddit_insights = self._search_subreddit(subreddit_name, topic, limit=10)
                    insights = self._merge_insights(insights, subreddit_insights)
                except Exception as e:
                    print(f"⚠️ Error searching r/{subreddit_name}: {str(e)}")
                    continue
            
            # Calculate authenticity score
            insights['authenticity_score'] = self._calculate_authenticity_score(insights)
            insights['insight_quality'] = self._assess_insight_quality(insights)
            
            return insights
            
        except Exception as e:
            print(f"❌ Reddit search failed: {str(e)}")
            return self._simulate_reddit_research(topic, subreddits)
    
    def _search_subreddit(self, subreddit_name: str, topic: str, limit: int) -> Dict[str, Any]:
        """Search a specific subreddit for insights"""
        try:
            if not self.reddit:
                return self._empty_insights()
                
            subreddit = self.reddit.subreddit(subreddit_name)
            
            insights = self._empty_insights()
            
            # Search recent posts
            for submission in subreddit.search(topic, time_filter='month', limit=limit):
                post_insights = self._analyze_post(submission)
                insights = self._merge_post_insights(insights, post_insights)
                
                # Analyze top comments
                submission.comments.replace_more(limit=0)
                for comment in submission.comments[:2]:
                    comment_insights = self._analyze_comment(comment)
                    insights = self._merge_post_insights(insights, comment_insights)
            
            return insights
            
        except Exception as e:
            return self._empty_insights()
    
    def _analyze_post(self, submission) -> Dict[str, Any]:
        """Analyze a Reddit post for insights"""
        insights = self._empty_insights()
        
        text = f"{submission.title} {submission.selftext}".lower()
        
        # Extract insights
        if len(text) > 20:
            insights['customer_voice']['common_language'].append(text[:100] + '...')
        
        if '?' in text:
            questions = [q.strip() + '?' for q in text.split('?') if q.strip()]
            insights['customer_voice']['frequent_questions'].extend(questions[:2])
        
        complaint_words = ['problem', 'issue', 'terrible', 'awful', 'frustrated', 'annoying']
        if any(word in text for word in complaint_words):
            insights['customer_voice']['complaints'].append(text[:150] + '...')
        
        rec_words = ['recommend', 'suggest', 'try', 'use', 'works well']
        if any(word in text for word in rec_words):
            insights['customer_voice']['recommendations'].append(text[:150] + '...')
        
        auth_markers = ['personally', 'in my experience', 'i found', 'this happened to me']
        for marker in auth_markers:
            if marker in text:
                insights['authenticity_markers'].append({
                    'marker': marker,
                    'context': text[max(0, text.find(marker)-50):text.find(marker)+100]
                })
        
        if any(phrase in text for phrase in ['i ', 'my ', 'me ', 'i\'ve', 'i\'m']):
            insights['real_experiences'].append({
                'experience': text[:200] + '...' if len(text) > 200 else text,
                'score': submission.score,
                'subreddit': submission.subreddit.display_name
            })
        
        return insights
    
    def _analyze_comment(self, comment) -> Dict[str, Any]:
        """Analyze a Reddit comment for insights"""
        if hasattr(comment, 'body'):
            class MockSubmission:
                def __init__(self, comment):
                    self.title = ""
                    self.selftext = comment.body
                    self.score = comment.score
                    self.subreddit = comment.subreddit
            
            return self._analyze_post(MockSubmission(comment))
        
        return self._empty_insights()
    
    def _empty_insights(self) -> Dict:
        """Return empty insights structure"""
        return {
            'customer_voice': {'common_language': [], 'frequent_questions': [], 'complaints': [], 'recommendations': []},
            'trending_discussions': [],
            'authenticity_markers': [],
            'real_experiences': []
        }
    
    def _merge_insights(self, main_insights: Dict, new_insights: Dict) -> Dict:
        """Merge insights from different sources"""
        for key in ['trending_discussions', 'authenticity_markers', 'real_experiences']:
            if key in main_insights and key in new_insights:
                main_insights[key].extend(new_insights[key])
        
        if 'customer_voice' in new_insights:
            for voice_key in ['common_language', 'frequent_questions', 'complaints', 'recommendations']:
                if voice_key in new_insights['customer_voice']:
                    main_insights['customer_voice'][voice_key].extend(new_insights['customer_voice'][voice_key])
        
        return main_insights
    
    def _merge_post_insights(self, main_insights: Dict, post_insights: Dict) -> Dict:
        """Merge insights from a single post"""
        return self._merge_insights(main_insights, post_insights)
    
    def _calculate_authenticity_score(self, insights: Dict) -> float:
        """Calculate authenticity score based on insights"""
        score = 0.0
        score += min(3.0, len(insights.get('authenticity_markers', [])) * 0.5)
        score += min(3.0, len(insights.get('real_experiences', [])) * 0.3)
        total_voice_items = sum(len(insights.get('customer_voice', {}).get(key, [])) for key in ['common_language', 'frequent_questions', 'complaints', 'recommendations'])
        score += min(4.0, total_voice_items * 0.1)
        return min(10.0, score)
    
    def _assess_insight_quality(self, insights: Dict) -> str:
        """Assess the quality of insights gathered"""
        total_insights = (
            len(insights.get('authenticity_markers', [])) +
            len(insights.get('real_experiences', [])) +
            sum(len(insights.get('customer_voice', {}).get(key, [])) for key in ['common_language', 'frequent_questions', 'complaints', 'recommendations'])
        )
        
        if total_insights >= 20:
            return 'excellent'
        elif total_insights >= 10:
            return 'good'
        elif total_insights >= 5:
            return 'fair'
        else:
            return 'limited'
    
    def _simulate_reddit_research(self, topic: str, subreddits: List[str]) -> Dict[str, Any]:
        """Enhanced simulation when Reddit API is unavailable"""
        topic_lower = topic.lower()
        
        if 'budget' in topic_lower or 'cheap' in topic_lower:
            common_language = ["budget-friendly", "affordable", "bang for buck", "cost-effective", "worth the money"]
            complaints = ["Too expensive", "Hidden costs", "Not worth the price"]
        elif 'laptop' in topic_lower or 'computer' in topic_lower:
            common_language = ["reliable", "fast performance", "good specs", "lightweight", "battery life"]
            complaints = ["Slow performance", "Short battery life", "Too heavy"]
        else:
            common_language = ["user-friendly", "reliable", "good value", "recommended", "works well"]
            complaints = ["Confusing setup", "Poor support", "Disappointing quality"]
        
        return {
            "customer_voice": {
                "common_language": common_language,
                "frequent_questions": [
                    f"Anyone tried this for {topic}?", 
                    "Is it legit?", 
                    "Better alternatives?",
                    "Worth the price?",
                    "Any issues I should know about?"
                ],
                "complaints": complaints,
                "recommendations": [
                    "Start with basics", 
                    "Read reviews first", 
                    "Compare multiple options",
                    "Check warranty terms"
                ]
            },
            "trending_discussions": [
                f"Best {topic} for beginners", 
                f"{topic} price comparison",
                f"Common {topic} mistakes to avoid"
            ],
            "sentiment_analysis": "cautiously positive",
            "community_size": f"Simulated analysis for {', '.join(subreddits)}",
            "authenticity_score": 3.5,
            "insight_quality": "simulated_enhanced",
            "real_experiences": [
                {
                    "experience": f"Used this for {topic} and had good results...",
                    "score": 15,
                    "subreddit": subreddits[0] if subreddits else "general"
                }
            ],
            "authenticity_markers": [
                {
                    "marker": "personally",
                    "context": f"Personally, I found this approach to {topic} worked well..."
                }
            ]
        }

class ContentTypeClassifier:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def classify_content_type(self, topic: str, intent_data: Dict, business_context: Dict) -> Dict[str, Any]:
        prompt = f"""
        Given topic "{topic}", intent "{intent_data.get('primary_intent')}", and business type "{business_context.get('business_type')}", 
        recommend the best content type.
        
        Respond with JSON format only:
        {{
            "primary_recommendation": {{
                "type": "blog_post/guide/comparison/case_study/faq",
                "reasoning": "why this type works best"
            }},
            "alternative_types": ["type1", "type2"],
            "content_length": "short/medium/long",
            "tone": "formal/casual/technical"
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.ai_agent.call_ai(messages)
        
        try:
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
            
        return {
            "primary_recommendation": {
                "type": "comprehensive_guide",
                "reasoning": "Best for informational intent and building authority"
            },
            "alternative_types": ["blog_post", "comparison"],
            "content_length": "long",
            "tone": "professional"
        }

class TrustScoreAssessor:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
        # YMYL topics requiring higher Trust standards
        self.ymyl_topics = [
            'finance', 'health', 'medical', 'legal', 'investment', 'insurance',
            'taxes', 'retirement', 'medication', 'surgery', 'diet', 'nutrition',
            'safety', 'parenting', 'relationships', 'government', 'news'
        ]
        
    def assess_content_trust_requirements(self, topic: str, content_type: str, business_context: Dict, human_inputs: Dict, reddit_insights: Dict) -> Dict[str, Any]:
        """Enhanced Trust Score assessment with proper calculation"""
        
        # Determine if this is YMYL content
        is_ymyl = self._is_ymyl_topic(topic, business_context.get('industry', ''))
        
        # Individual Trust component assessments
        experience_score = self._assess_experience(human_inputs, reddit_insights, is_ymyl)
        expertise_score = self._assess_expertise(business_context, human_inputs, is_ymyl)
        authoritativeness_score = self._assess_authoritativeness(business_context, human_inputs)
        trustworthiness_score = self._assess_trustworthiness(business_context, human_inputs, is_ymyl)
        
        # Calculate overall Trust score with proper weighting
        overall_score = self._calculate_overall_trust_score(
            experience_score, expertise_score, authoritativeness_score, trustworthiness_score, is_ymyl
        )
        
        # Determine Trust level
        trust_level = self._determine_trust_level(overall_score)
        
        return {
            "overall_trust_score": round(overall_score, 1),
            "trust_level": trust_level,
            "is_ymyl_topic": is_ymyl,
            "experience_score": experience_score,
            "expertise_score": expertise_score,
            "authoritativeness_score": authoritativeness_score,
            "trustworthiness_score": trustworthiness_score,
            "improvement_areas": self._get_improvement_areas(experience_score, expertise_score, authoritativeness_score, trustworthiness_score),
            "trust_elements_to_include": ["Author bio", "Citations", "Customer reviews", "Industry statistics", "Honest disclaimers"]
        }
    
    def _is_ymyl_topic(self, topic: str, industry: str) -> bool:
        """Determine if topic/industry is YMYL"""
        topic_lower = topic.lower()
        industry_lower = industry.lower()
        return any(ymyl in topic_lower or ymyl in industry_lower for ymyl in self.ymyl_topics)
    
    def _assess_experience(self, human_inputs: Dict, reddit_insights: Dict, is_ymyl: bool) -> float:
        """Assess Experience component"""
        score = 3.0
        
        customer_insights = human_inputs.get('customer_insights', {})
        if customer_insights.get('success_story'):
            score += 2.0
        if customer_insights.get('customer_pain_points'):
            score += 1.5
        
        if reddit_insights:
            if reddit_insights.get('authenticity_score', 0) > 5.0:
                score += 1.5
            if len(reddit_insights.get('real_experiences', [])) > 0:
                score += 1.0
        
        if is_ymyl and score < 6.0:
            score *= 0.8
        
        return min(10.0, score)
    
    def _assess_expertise(self, business_context: Dict, human_inputs: Dict, is_ymyl: bool) -> float:
        """Assess Expertise component"""
        score = 4.0
        
        if business_context.get('industry'):
            score += 2.0
        if business_context.get('unique_value_prop'):
            score += 1.5
        
        business_expertise = human_inputs.get('business_expertise', {})
        if business_expertise.get('industry_knowledge'):
            score += 1.0
        if len(human_inputs.get('customer_insights', {}).get('customer_pain_points', '')) > 100:
            score += 1.0
        
        if is_ymyl:
            if score < 7.0:
                score *= 0.8
        
        return min(10.0, score)
    
    def _assess_authoritativeness(self, business_context: Dict, human_inputs: Dict) -> float:
        """Assess Authoritativeness component"""
        score = 3.5
        
        if business_context.get('business_type'):
            score += 0.5
        if business_context.get('unique_value_prop'):
            score += 2.0
        if business_context.get('industry'):
            score += 1.0
        
        if human_inputs.get('customer_insights', {}).get('success_story'):
            score += 1.5
        if len(human_inputs.get('customer_insights', {}).get('frequent_questions', '')) > 50:
            score += 1.0
        
        return min(10.0, score)
    
    def _assess_trustworthiness(self, business_context: Dict, human_inputs: Dict, is_ymyl: bool) -> float:
        """Assess Trustworthiness component"""
        score = 4.0
        
        if business_context.get('unique_value_prop'):
            score += 2.0
        if business_context.get('brand_voice'):
            score += 1.0
        
        customer_insights = human_inputs.get('customer_insights', {})
        if customer_insights.get('success_story'):
            score += 1.5
        if customer_insights.get('customer_pain_points'):
            score += 1.0
        
        if is_ymyl:
            if score < 7.0:
                score *= 0.7
        else:
            score += 0.5
        
        return min(10.0, score)
    
    def _calculate_overall_trust_score(self, experience: float, expertise: float, authoritativeness: float, trustworthiness: float, is_ymyl: bool) -> float:
        """Calculate overall Trust score with proper weighting"""
        
        if is_ymyl:
            weights = {'trust': 0.4, 'expertise': 0.3, 'experience': 0.15, 'authority': 0.15}
        else:
            weights = {'trust': 0.35, 'experience': 0.25, 'expertise': 0.2, 'authority': 0.2}
        
        overall = (
            experience * weights['experience'] +
            expertise * weights['expertise'] +
            authoritativeness * weights['authority'] +
            trustworthiness * weights['trust']
        )
        
        return overall
    
    def _determine_trust_level(self, score: float) -> str:
        """Determine Trust level based on score"""
        if score >= 8.5:
            return 'very_high'
        elif score >= 7.0:
            return 'high'
        elif score >= 5.0:
            return 'moderate'
        elif score >= 3.0:
            return 'lacking'
        else:
            return 'lowest'
    
    def _get_improvement_areas(self, exp: float, expert: float, auth: float, trust: float) -> List[str]:
        """Get improvement recommendations"""
        improvements = []
        
        if exp < 6.0:
            improvements.append("Add more personal experience stories and customer success cases")
        if expert < 6.0:
            improvements.append("Increase industry expertise demonstration and technical accuracy")
        if auth < 6.0:
            improvements.append("Build stronger brand authority and thought leadership")
        if trust < 7.0:
            improvements.append("Enhance transparency and credibility signals")
        
        return improvements or ["Strong trust foundation - focus on optimization"]

class ContentQualityScorer:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def score_content_quality(self, content: str, topic: str, business_context: Dict, 
                            human_inputs: Dict, trust_assessment: Dict) -> Dict[str, Any]:
        """Score content quality using Trust Score correlation"""
        
        word_count = len(content.split())
        has_headings = content.count('#') > 3 or content.count('\n\n') > 5
        mentions_business = business_context.get('unique_value_prop', '').lower() in content.lower()
        addresses_pain_points = any(pain.lower() in content.lower() 
                                  for pain in human_inputs.get('customer_insights', {}).get('customer_pain_points', '').split(',')
                                  if pain.strip())
        
        content_score = 8.5 if word_count > 500 else 6.0
        structure_score = 9.0 if has_headings else 7.0
        relevance_score = 9.5 if mentions_business and addresses_pain_points else 7.5
        
        trust_score = trust_assessment.get('overall_trust_score', 7.0)
        
        overall_score = (
            content_score * 0.3 + 
            structure_score * 0.2 + 
            relevance_score * 0.2 + 
            trust_score * 0.3
        )
        
        if overall_score >= 8.5:
            performance = "High performance expected - Zee SEO Tool creates 5x better content than standard AI"
            traffic_multiplier = "4-6x"
        elif overall_score >= 7.5:
            performance = "Good performance expected - Zee SEO Tool drives 3x better engagement"
            traffic_multiplier = "2-4x"
        else:
            performance = "Standard performance - Zee SEO Tool provides solid content foundation"
            traffic_multiplier = "1-2x"
            
        return {
            "overall_quality_score": round(overall_score, 1),
            "content_score": content_score,
            "structure_score": structure_score,
            "relevance_score": relevance_score,
            "trust_score": trust_score,
            "performance_prediction": performance,
            "traffic_multiplier_estimate": traffic_multiplier,
            "trust_correlation": f"Quality score aligns with trust score of {trust_score:.1f}/10",
            "critical_improvements": [
                "Zee SEO Tool's advanced reasoning provides deeper customer understanding",
                "Superior context awareness creates more relevant content", 
                "Enhanced business intelligence integration",
                f"Trust-optimized content with {trust_assessment.get('trust_level', 'moderate')} trust level"
            ]
        }

class ContentGenerator:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def generate_complete_content(self, topic: str, content_type: str, reddit_insights: Dict, 
                                journey_data: Dict, business_context: Dict, human_inputs: Dict, 
                                trust_assessment: Dict, ai_instructions: Dict) -> str:
        
        # Build AI instructions prompt
        ai_prompt_additions = []
        
        if ai_instructions.get('writing_style'):
            ai_prompt_additions.append(f"Writing style: {ai_instructions['writing_style']}")
            
        if ai_instructions.get('target_word_count'):
            ai_prompt_additions.append(f"Target word count: {ai_instructions['target_word_count']} words")
            
        if ai_instructions.get('language_preference'):
            ai_prompt_additions.append(f"Language preference: {ai_instructions['language_preference']}")
            
        if ai_instructions.get('additional_notes'):
            ai_prompt_additions.append(f"Additional instructions: {ai_instructions['additional_notes']}")
        
        ai_instructions_text = "\n".join(ai_prompt_additions) if ai_prompt_additions else ""
        
        # Reddit insights integration
        reddit_language = reddit_insights.get('customer_voice', {}).get('common_language', [])
        reddit_questions = reddit_insights.get('customer_voice', {}).get('frequent_questions', [])
        reddit_complaints = reddit_insights.get('customer_voice', {}).get('complaints', [])
        
        prompt = f"""
        Create a comprehensive, high-quality {content_type} about "{topic}".
        
        BUSINESS CONTEXT:
        - Industry: {business_context.get('industry')}
        - Target Audience: {business_context.get('target_audience')}
        - Business Type: {business_context.get('business_type')}
        - Brand Voice: {business_context.get('brand_voice')}
        - Unique Value Prop: {business_context.get('unique_value_prop')}
        
        CUSTOMER INSIGHTS:
        - Pain Points: {human_inputs.get('customer_insights', {}).get('customer_pain_points')}
        - Common Questions: {human_inputs.get('customer_insights', {}).get('frequent_questions')}
        - Success Story: {human_inputs.get('customer_insights', {}).get('success_story')}
        
        REDDIT RESEARCH:
        - Customer Language: {', '.join(reddit_language[:5])}
        - Community Questions: {', '.join(reddit_questions[:3])}
        - Common Complaints: {', '.join(reddit_complaints[:3])}
        - Authenticity Score: {reddit_insights.get('authenticity_score', 'N/A')}/10
        - Research Quality: {reddit_insights.get('insight_quality', 'N/A')}
        
        TRUST SCORE REQUIREMENTS:
        - Overall Trust Score: {trust_assessment.get('overall_trust_score')}/10
        - Trust Level: {trust_assessment.get('trust_level')}
        - YMYL Topic: {trust_assessment.get('is_ymyl_topic')}
        - Improvement Areas: {', '.join(trust_assessment.get('improvement_areas', []))}
        
        AI WRITING INSTRUCTIONS:
        {ai_instructions_text}
        
        REQUIREMENTS:
        1. Follow the AI writing instructions above carefully
        2. Include Trust Score optimization elements (expertise, authority, trustworthiness)
        3. Use authentic customer language from Reddit research
        4. Address specific pain points and complaints mentioned
        5. Include your unique value proposition naturally
        6. Write in {business_context.get('brand_voice', 'professional')} tone
        7. Structure with clear headings and subheadings
        8. Include actionable advice and real solutions
        9. Add credibility signals and honest disclaimers
        10. End with a compelling call-to-action
        
        Generate comprehensive, helpful content that demonstrates expertise and builds trust.
        Focus on providing real value to {business_context.get('target_audience', 'your audience')}.
        Include authentic voice elements from Reddit research to make it more relatable.
        """
        
        messages = [{"role": "user", "content": prompt}]
        return self.ai_agent.call_ai(messages, max_tokens=2500)

# Initialize Components
ai_agent = AIAgent()
intent_classifier = IntentClassifier(ai_agent)
journey_mapper = JourneyMapper(ai_agent)
reddit_researcher = RedditAPIClient()
content_type_classifier = ContentTypeClassifier(ai_agent)
trust_assessor = TrustScoreAssessor(ai_agent)
content_generator = ContentGenerator(ai_agent)
quality_scorer = ContentQualityScorer(ai_agent)

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with YOUR ORIGINAL design and AI dialogue window"""
    
    # Check Reddit API status
    reddit_status = "🟢 Connected" if reddit_researcher.reddit else "🟡 Simulation Mode"
    reddit_note = "Real API" if reddit_researcher.reddit else "Enhanced Simulation"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zee SEO Tool - AI Content Creation That Bridges Human & AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }}
            
            .logo {{
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .tagline {{
                font-size: 20px;
                opacity: 0.9;
                margin-bottom: 5px;
            }}
            
            .subtitle {{
                font-size: 16px;
                opacity: 0.8;
                font-style: italic;
            }}
            
            .status-badge {{
                background: rgba(255,255,255,0.2);
                padding: 8px 15px;
                border-radius: 20px;
                display: inline-block;
                margin-top: 10px;
                font-size: 14px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                position: relative;
            }}
            
            .ai-badge {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 12px 25px;
                border-radius: 25px;
                display: inline-block;
                margin-bottom: 25px;
                font-weight: bold;
                font-size: 16px;
            }}
            
            .ai-assistant-btn {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                border-radius: 50%;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
                z-index: 1000;
                transition: transform 0.3s ease;
            }}
            
            .ai-assistant-btn:hover {{
                transform: scale(1.1);
            }}
            
            .ai-dialogue {{
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                z-index: 999;
                display: none;
                flex-direction: column;
                overflow: hidden;
            }}
            
            .ai-dialogue-header {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 15px 20px;
                font-weight: bold;
                display: flex;
                justify-content: between;
                align-items: center;
            }}
            
            .ai-dialogue-close {{
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                margin-left: auto;
            }}
            
            .ai-dialogue-body {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }}
            
            .ai-suggestion {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #8B5CF6;
            }}
            
            .ai-suggestion h4 {{
                color: #8B5CF6;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            
            .ai-suggestion p {{
                font-size: 13px;
                line-height: 1.4;
                color: #666;
            }}
            
            .form-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }}
            
            .form-section {{
                background-color: #f8f9fa;
                padding: 25px;
                border-radius: 15px;
                border-left: 5px solid #8B5CF6;
            }}
            
            .form-group {{ 
                margin-bottom: 20px; 
            }}
            
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                font-weight: 600; 
                color: #333;
                font-size: 14px;
            }}
            
            input, textarea, select {{ 
                width: 100%; 
                padding: 12px 15px; 
                border: 2px solid #e1e5e9; 
                border-radius: 8px; 
                font-size: 14px;
                transition: border-color 0.3s ease;
            }}
            
            textarea {{
                resize: vertical;
                min-height: 80px;
            }}
            
            input:focus, textarea:focus, select:focus {{
                border-color: #8B5CF6;
                outline: none;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
            }}
            
            .submit-section {{
                grid-column: 1 / -1;
                text-align: center;
                margin-top: 20px;
            }}
            
            button {{ 
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white; 
                padding: 18px 40px; 
                border: none; 
                border-radius: 50px; 
                cursor: pointer; 
                font-size: 18px;
                font-weight: bold;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                min-width: 300px;
            }}
            
            button:hover {{ 
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3);
            }}
            
            .section-title {{
                color: #8B5CF6;
                border-bottom: 2px solid #8B5CF6;
                padding-bottom: 10px;
                margin-bottom: 20px;
                font-size: 18px;
                font-weight: 600;
            }}
            
            .help-text {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
                font-style: italic;
            }}
            
            .features {{
                background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 30px;
                grid-column: 1 / -1;
            }}
            
            .features h3 {{
                margin-bottom: 15px;
                font-size: 20px;
            }}
            
            .features ul {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                list-style: none;
            }}
            
            .features li {{
                padding: 5px 0;
                border-left: 3px solid rgba(255,255,255,0.3);
                padding-left: 15px;
            }}
            
            .ai-controls {{
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border: 2px solid #0ea5e9;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            
            .ai-controls .section-title {{
                color: #0ea5e9;
                border-bottom-color: #0ea5e9;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 2px solid #e1e5e9;
                color: #666;
            }}
            
            .creator-info {{
                background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                margin-top: 20px;
            }}
            
            .creator-info h4 {{
                color: #8B5CF6;
                margin-bottom: 10px;
            }}
            
            #loading {{
                display: none;
                text-align: center;
                margin-top: 20px;
                padding: 30px;
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border-radius: 15px;
                border: 2px solid #8B5CF6;
            }}
            
            .loading-animation {{
                font-size: 24px;
                margin-bottom: 15px;
            }}
            
            @media (max-width: 768px) {{
                .form-grid {{
                    grid-template-columns: 1fr;
                    gap: 20px;
                }}
                
                .features ul {{
                    grid-template-columns: 1fr;
                }}
                
                .container {{
                    padding: 20px;
                }}
                
                .ai-dialogue {{
                    width: 300px;
                    right: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">⚡ ZEE SEO TOOL</div>
            <div class="tagline">AI Content Creation That Bridges Human & AI</div>
            <div class="subtitle">Built by Zeeshan Bashir • Effective Content That Works</div>
            <div class="status-badge">Reddit: {reddit_status} ({reddit_note}) | Trust Score: ✅ Active | Railway: ✅ Deployed</div>
        </div>
        
        <div class="container">
            <div class="ai-badge">🤖 Powered by Advanced AI + Reddit Research + Trust Score Optimization</div>
            
            <form action="/generate" method="post">
                <div class="form-grid">
                    <div class="features">
                        <h3>🚀 Zee SEO Tool Features:</h3>
                        <ul>
                            <li>✅ Advanced AI reasoning</li>
                            <li>✅ Reddit research ({reddit_note})</li>
                            <li>✅ Customer journey mapping</li>
                            <li>✅ Trust Score optimization</li>
                            <li>✅ Human-AI content bridging</li>
                            <li>✅ Performance prediction analytics</li>
                        </ul>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">📝 Content Topic & Research</h3>
                        
                        <div class="form-group">
                            <label for="topic">Content Topic:</label>
                            <input type="text" id="topic" name="topic" 
                                   placeholder="e.g., best budget laptops for college students" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="subreddits">Target Subreddits (comma-separated):</label>
                            <input type="text" id="subreddits" name="subreddits" 
                                   placeholder="e.g., laptops, college, StudentLoans" required>
                            <div class="help-text">Reddit communities will be analyzed for authentic insights ({reddit_note})</div>
                        </div>
                    </div>
                    
                    <div class="form-section ai-controls">
                        <h3 class="section-title">🤖 AI Writing Instructions</h3>
                        
                        <div class="form-group">
                            <label for="writing_style">Writing Style:</label>
                            <select id="writing_style" name="writing_style">
                                <option value="">Default</option>
                                <option value="British English">British English</option>
                                <option value="American English">American English</option>
                                <option value="Conversational">Conversational</option>
                                <option value="Academic">Academic</option>
                                <option value="Journalistic">Journalistic</option>
                                <option value="Marketing Copy">Marketing Copy</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="target_word_count">Target Word Count:</label>
                            <select id="target_word_count" name="target_word_count">
                                <option value="">Default (800-1200)</option>
                                <option value="500-700">Short (500-700 words)</option>
                                <option value="800-1200">Medium (800-1200 words)</option>
                                <option value="1500-2000">Long (1500-2000 words)</option>
                                <option value="2500+">Very Long (2500+ words)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="language_preference">Language Preference:</label>
                            <select id="language_preference" name="language_preference">
                                <option value="">Default</option>
                                <option value="UK English with British spelling">UK English (colour, realise, etc.)</option>
                                <option value="US English with American spelling">US English (color, realize, etc.)</option>
                                <option value="Simple language for beginners">Simple Language</option>
                                <option value="Technical language for experts">Technical Language</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="additional_notes">Additional AI Instructions:</label>
                            <textarea id="additional_notes" name="additional_notes" 
                                      placeholder="e.g., Include statistics, Add comparison tables, Focus on benefits, Use bullet points, etc."></textarea>
                            <div class="help-text">Specific instructions for the AI about how to write your content</div>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">🏢 Your Business Context</h3>
                        
                        <div class="form-group">
                            <label for="industry">Industry:</label>
                            <input type="text" id="industry" name="industry" 
                                   placeholder="e.g., Technology, Healthcare, Finance" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="target_audience">Target Audience:</label>
                            <input type="text" id="target_audience" name="target_audience" 
                                   placeholder="e.g., College students, Small business owners" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="business_type">Business Type:</label>
                            <select id="business_type" name="business_type" required>
                                <option value="">Select...</option>
                                <option value="B2B">B2B (Business to Business)</option>
                                <option value="B2C">B2C (Business to Consumer)</option>
                                <option value="Both">Both B2B and B2C</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="content_goal">Content Goal:</label>
                            <textarea id="content_goal" name="content_goal" 
                                      placeholder="e.g., Educate customers, Generate leads, Build trust" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="unique_value_prop">What makes you different?</label>
                            <textarea id="unique_value_prop" name="unique_value_prop" 
                                      placeholder="e.g., 24/7 support, 10 years experience, patented technology" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="brand_voice">Brand Voice:</label>
                            <select id="brand_voice" name="brand_voice" required>
                                <option value="">Select...</option>
                                <option value="Professional">Professional</option>
                                <option value="Casual">Casual & Friendly</option>
                                <option value="Technical">Technical & Expert</option>
                                <option value="Empathetic">Empathetic & Caring</option>
                                <option value="Bold">Bold & Confident</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3 class="section-title">👥 Customer Insights</h3>
                        
                        <div class="form-group">
                            <label for="customer_pain_points">Customer's Biggest Challenges:</label>
                            <textarea id="customer_pain_points" name="customer_pain_points" 
                                      placeholder="e.g., Limited budget, Too many options, Lack of time" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="frequent_questions">Most Common Customer Questions:</label>
                            <textarea id="frequent_questions" name="frequent_questions" 
                                      placeholder="e.g., How much does it cost? Is it reliable? How long does it take?" required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="success_story">Customer Success Story (Optional):</label>
                            <textarea id="success_story" name="success_story" 
                                      placeholder="e.g., Helped a customer save 50% on costs, reduced their time by 3 hours daily"></textarea>
                            <div class="help-text">Adds authenticity and builds trust in your content</div>
                        </div>
                    </div>
                    
                    <div class="submit-section">
                        <button type="submit">🚀 Generate High-Performance Content with Zee SEO Tool</button>
                    </div>
                </div>
            </form>
            
            <div id="loading">
                <div class="loading-animation">🤖 ⚡ 🧠</div>
                <h3>Zee SEO Tool is crafting your content...</h3>
                <p>AI is analyzing your inputs, mapping customer journey, researching Reddit insights, calculating Trust Score, and generating high-performance content that bridges human expertise with AI intelligence.</p>
                <p><em>This advanced analysis takes 30-60 seconds for maximum quality</em></p>
            </div>
            
            <div class="footer">
                <div class="creator-info">
                    <h4>🛠️ Built by Zeeshan Bashir</h4>
                    <p><strong>Mission:</strong> To create effective content that cuts the bridge between human creativity and AI efficiency. Zee SEO Tool combines the best of both worlds - human insight and AI power - to produce content that truly performs.</p>
                    <p><strong>Purpose:</strong> Helping businesses create content that doesn't just rank, but converts and builds genuine connections with their audience.</p>
                    <p><strong>Railway Status:</strong> ✅ Deployed & Optimized • Reddit: {reddit_status} • Trust Score: ✅ Active</p>
                </div>
            </div>
        </div>
        
        <!-- AI Assistant Button -->
        <button class="ai-assistant-btn" onclick="toggleAIDialogue()">🤖</button>
        
        <!-- AI Dialogue Window -->
        <div class="ai-dialogue" id="aiDialogue">
            <div class="ai-dialogue-header">
                <span>💡 AI Content Assistant</span>
                <button class="ai-dialogue-close" onclick="toggleAIDialogue()">×</button>
            </div>
            <div class="ai-dialogue-body">
                <div class="ai-suggestion">
                    <h4>🎯 Content Strategy Tip</h4>
                    <p>Start with your customer's biggest pain point. This creates immediate relevance and engagement.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>📊 Trust Score Boost</h4>
                    <p>Include specific numbers, examples, or case studies in your content to improve your Trust Score significantly.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>🔍 Reddit Research Power</h4>
                    <p>Choose subreddits where your target audience actually hangs out for more authentic insights.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>✍️ Writing Style Guide</h4>
                    <p>Match your brand voice with your audience: Technical for experts, Conversational for general audience.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>📈 Performance Prediction</h4>
                    <p>Content with strong customer insights typically gets 3-5x better engagement than generic content.</p>
                </div>
                
                <div class="ai-suggestion">
                    <h4>🚀 Quick Win</h4>
                    <p>Fill out the "Success Story" field - it dramatically improves your content's authenticity and Trust Score.</p>
                </div>
            </div>
        </div>
        
        <script>
            function toggleAIDialogue() {{
                const dialogue = document.getElementById('aiDialogue');
                if (dialogue.style.display === 'none' || dialogue.style.display === '') {{
                    dialogue.style.display = 'flex';
                }} else {{
                    dialogue.style.display = 'none';
                }}
            }}
            
            document.querySelector('form').addEventListener('submit', function() {{
                document.getElementById('loading').style.display = 'block';
                document.querySelector('.container').scrollIntoView({{ behavior: 'smooth' }});
            }});
            
            // Auto-show AI dialogue on first visit
            setTimeout(() => {{
                if (!localStorage.getItem('aiDialogueShown')) {{
                    toggleAIDialogue();
                    localStorage.setItem('aiDialogueShown', 'true');
                }}
            }}, 3000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Keep the same generate_content function but update references
@app.post("/generate")
async def generate_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    language_preference: str = Form(""),
    additional_notes: str = Form(""),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    content_goal: str = Form(...),
    unique_value_prop: str = Form(...),
    brand_voice: str = Form(...),
    customer_pain_points: str = Form(...),
    frequent_questions: str = Form(...),
    success_story: str = Form("")
):
    """Generate enhanced content with YOUR ORIGINAL design preserved"""
    try:
        # Parse subreddits
        target_subreddits = [s.strip() for s in subreddits.split(',') if s.strip()]
        
        # Create business context from form inputs
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'content_goal': content_goal,
            'unique_value_prop': unique_value_prop,
            'brand_voice': brand_voice
        }
        
        # Create human inputs from form
        human_inputs = {
            'customer_insights': {
                'customer_pain_points': customer_pain_points,
                'frequent_questions': frequent_questions,
                'success_story': success_story
            },
            'business_expertise': {
                'unique_value_prop': unique_value_prop,
                'industry_knowledge': f"Expert in {industry}",
                'target_audience_understanding': target_audience
            }
        }
        
        # Create AI instructions from form
        ai_instructions = {
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'language_preference': language_preference,
            'additional_notes': additional_notes
        }
        
        # ZEE SEO TOOL AI PROCESSING PIPELINE
        print(f"🚀 Zee SEO Tool starting analysis for: {topic}")
        
        # Step 1: Intent Classification
        print("🔍 Zee SEO Tool: Running intent classification...")
        intent_data = intent_classifier.classify_intent(topic)
        
        # Step 2: Customer Journey Mapping
        print("🗺️ Zee SEO Tool: Mapping customer journey...")
        journey_data = journey_mapper.map_customer_journey(topic, intent_data)
        
        # Step 3: Reddit Research
        print("📱 Zee SEO Tool: Researching Reddit for authentic insights...")
        reddit_insights = reddit_researcher.research_topic(topic, target_subreddits)
        
        # Step 4: Content Type Classification
        print("📝 Zee SEO Tool: Classifying optimal content type...")
        content_type_data = content_type_classifier.classify_content_type(topic, intent_data, business_context)
        chosen_content_type = content_type_data.get('primary_recommendation', {}).get('type', 'comprehensive_guide')
        
        # Step 5: Trust Score Assessment
        print("⭐ Zee SEO Tool: Calculating Trust Score...")
        trust_assessment = trust_assessor.assess_content_trust_requirements(
            topic, chosen_content_type, business_context, human_inputs, reddit_insights
        )
        
        # Step 6: Generate Complete Content
        print("✍️ Zee SEO Tool: Generating content with Trust Score optimization...")
        complete_content = content_generator.generate_complete_content(
            topic, chosen_content_type, reddit_insights, journey_data, 
            business_context, human_inputs, trust_assessment, ai_instructions
        )
        
        # Step 7: Score Content Quality
        print("📊 Zee SEO Tool: Scoring content quality...")
        quality_score = quality_scorer.score_content_quality(
            complete_content, topic, business_context, human_inputs, trust_assessment
        )
        
        # Extract key metrics
        trust_score = trust_assessment.get('overall_trust_score', 'N/A')
        trust_level = trust_assessment.get('trust_level', 'N/A')
        overall_quality = quality_score.get('overall_quality_score', 'N/A')
        performance_prediction = quality_score.get('performance_prediction', 'N/A')
        traffic_multiplier = quality_score.get('traffic_multiplier_estimate', 'N/A')
        reddit_quality = reddit_insights.get('insight_quality', 'N/A')
        reddit_auth_score = reddit_insights.get('authenticity_score', 'N/A')
        
        # Determine Reddit status for display
        reddit_status_display = "Live API" if reddit_researcher.reddit else "Enhanced Simulation"
        
        print("✅ Zee SEO Tool: Processing complete!")
        
        # Generate results page with YOUR ORIGINAL styling
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zee SEO Tool Results - {topic}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    line-height: 1.6;
                }}
                
                .header {{
                    text-align: center;
                    color: white;
                    margin-bottom: 30px;
                }}
                
                .logo {{
                    font-size: 42px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                
                .tagline {{
                    font-size: 18px;
                    opacity: 0.9;
                }}
                
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                
                .results-header {{
                    background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                
                .ai-badge {{
                    background: rgba(255,255,255,0.2);
                    padding: 8px 20px;
                    border-radius: 20px;
                    display: inline-block;
                    margin-bottom: 15px;
                    font-weight: bold;
                }}
                
                .content-wrapper {{
                    padding: 40px;
                }}
                
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                
                .metric-card {{
                    background: linear-gradient(135deg, #8B5CF6, #A855F7);
                    color: white;
                    padding: 25px;
                    border-radius: 15px;
                    text-align: center;
                    transform: translateY(0);
                    transition: transform 0.3s ease;
                }}
                
                .metric-card:hover {{
                    transform: translateY(-5px);
                }}
                
                .metric-value {{
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }}
                
                .metric-label {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                
                .section {{
                    margin: 40px 0;
                    padding: 25px;
                    border-left: 5px solid #8B5CF6;
                    background-color: #f8f9fa;
                    border-radius: 0 15px 15px 0;
                }}
                
                .content-box {{
                    background-color: white;
                    padding: 25px;
                    border-radius: 12px;
                    border: 1px solid #e1e5e9;
                    margin: 20px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }}
                
                .back-btn {{
                    display: inline-block;
                    padding: 12px 25px;
                    background: linear-gradient(135deg, #6c757d, #495057);
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    margin-bottom: 20px;
                    transition: transform 0.3s ease;
                }}
                
                .back-btn:hover {{
                    transform: translateY(-2px);
                }}
                
                .highlight {{
                    background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                    padding: 20px;
                    border-radius: 12px;
                    border-left: 4px solid #ffc107;
                    margin: 20px 0;
                }}
                
                pre {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    white-space: pre-wrap;
                    overflow-x: auto;
                    border-left: 4px solid #8B5CF6;
                    font-family: 'Courier New', monospace;
                }}
                
                .reddit-section {{
                    background: linear-gradient(135deg, #fee2e2, #fca5a5);
                    padding: 20px;
                    border-radius: 12px;
                    border-left: 4px solid #ef4444;
                    margin: 20px 0;
                }}
                
                .trust-score-section {{
                    background: linear-gradient(135deg, #fef3c7, #fbbf24);
                    padding: 20px;
                    border-radius: 12px;
                    border-left: 4px solid #f59e0b;
                    margin: 20px 0;
                }}
                
                .zee-footer {{
                    background: linear-gradient(135deg, #1f2937, #374151);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }}
                
                .zee-footer h3 {{
                    color: #8B5CF6;
                    margin-bottom: 15px;
                    font-size: 24px;
                }}
                
                .zee-footer p {{
                    margin-bottom: 10px;
                    opacity: 0.9;
                }}
                
                @media (max-width: 768px) {{
                    .metrics-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .content-wrapper {{
                        padding: 20px;
                    }}
                    
                    .logo {{
                        font-size: 32px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">⚡ ZEE SEO TOOL</div>
                <div class="tagline">Your High-Performance Content is Ready!</div>
            </div>
            
            <div class="container">
                <div class="results-header">
                    <div class="ai-badge">🤖 Generated by Zee SEO Tool</div>
                    <h1>🎉 Your Trust-Optimized Content Strategy</h1>
                    <p><strong>Topic:</strong> {topic}</p>
                    <p><strong>Content Type:</strong> {chosen_content_type.replace('_', ' ').title()}</p>
                    <p><strong>Word Count:</strong> {len(complete_content.split())} words</p>
                </div>
                
                <div class="content-wrapper">
                    <a href="/" class="back-btn">← Create Another Zee SEO Strategy</a>
                    
                    <div class="section">
                        <h2>📊 Zee SEO Tool Performance Metrics</h2>
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{trust_score}/10</div>
                                <div class="metric-label">Trust Score</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{overall_quality}/10</div>
                                <div class="metric-label">Quality Score</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{traffic_multiplier}</div>
                                <div class="metric-label">Traffic Multiplier</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{reddit_auth_score}/10</div>
                                <div class="metric-label">Reddit Authenticity</div>
                            </div>
                        </div>
                        <div class="highlight">
                            <strong>🚀 Zee SEO Tool Performance Prediction:</strong> {performance_prediction}
                        </div>
                    </div>

                    <div class="trust-score-section">
                        <h3>🔒 Trust Score Analysis</h3>
                        <p><strong>Overall Trust Score:</strong> {trust_score}/10 ({trust_level.replace('_', ' ').title()})</p>
                        <p><strong>YMYL Topic:</strong> {'Yes' if trust_assessment.get('is_ymyl_topic') else 'No'}</p>
                        <p><strong>Component Scores:</strong></p>
                        <ul>
                            <li>Experience: {trust_assessment.get('experience_score', 'N/A')}/10</li>
                            <li>Expertise: {trust_assessment.get('expertise_score', 'N/A')}/10</li>
                            <li>Authoritativeness: {trust_assessment.get('authoritativeness_score', 'N/A')}/10</li>
                            <li>Trustworthiness: {trust_assessment.get('trustworthiness_score', 'N/A')}/10</li>
                        </ul>
                    </div>

                    <div class="reddit-section">
                        <h3>📱 Reddit Research Results</h3>
                        <p><strong>Research Mode:</strong> {reddit_status_display}</p>
                        <p><strong>Research Quality:</strong> {reddit_quality.title()}</p>
                        <p><strong>Authenticity Score:</strong> {reddit_auth_score}/10</p>
                        <p><strong>Communities Analyzed:</strong> {', '.join(target_subreddits)}</p>
                        <p><strong>Status:</strong> {'🟢 Live API Connected' if reddit_researcher.reddit else '🟡 Enhanced Simulation Mode'}</p>
                    </div>

                    <div class="section">
                        <h2>✍️ Your High-Performance Content</h2>
                        <div class="content-box">
                            <div class="ai-badge" style="color: #8B5CF6; background: rgba(139, 92, 246, 0.1);">🤖 Generated by Zee SEO Tool</div>
                            <h3>Your Trust-Optimized {chosen_content_type.replace('_', ' ').title()}</h3>
                            <p><strong>Generated Word Count:</strong> {len(complete_content.split())} words</p>
                            <p><strong>Reddit Research:</strong> {reddit_status_display} • <strong>Trust Level:</strong> {trust_level.replace('_', ' ').title()}</p>
                            <pre>{complete_content}</pre>
                        </div>
                    </div>

                    <div style="text-align: center; margin-top: 40px;">
                        <a href="/" class="back-btn" style="font-size: 18px; padding: 15px 30px;">🚀 Create Another Trust-Optimized Strategy</a>
                    </div>
                </div>
                
                <div class="zee-footer">
                    <h3>⚡ Built by Zeeshan Bashir</h3>
                    <p><strong>Zee SEO Tool:</strong> Advanced Trust Score optimization with Reddit research.</p>
                    <p><strong>Status:</strong> ✅ Deployed on Railway • Reddit: {reddit_status_display} • Trust Score: ✅ Active</p>
                    <p><strong>Features:</strong> Trust Score Assessment • Reddit Research • AI Integration • Performance Analytics</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        error_html = f"""
        <html>
        <head>
            <title>Zee SEO Tool - Error</title>
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .error-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    max-width: 600px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }}
                .logo {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #8B5CF6;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="logo">⚡ ZEE SEO TOOL</div>
                <h1>❌ Processing Error</h1>
                <p><strong>Error during content generation:</strong> {str(e)}</p>
                <a href="/" style="display: inline-block; margin-top: 20px; padding: 12px 25px; background: linear-gradient(135deg, #8B5CF6, #A855F7); color: white; text-decoration: none; border-radius: 25px;">← Try Again with Zee SEO Tool</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint with system status"""
    return {
        "status": "healthy",
        "version": "2.0 Original Design Restored",
        "features": {
            "ai_api": "✅" if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-anthropic-api-key-here" else "❌",
            "reddit_api": "✅" if reddit_researcher.reddit else "⚠️ Simulation Mode",
            "trust_score": "✅ Active",
            "ai_dialogue": "✅ Active",
            "original_design": "✅ Restored"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Zee SEO Tool v2.0 (Original Design Restored)...")
    print("=" * 60)
    print("🔧 System Status:")
    print(f"  📊 Trust Score Assessment: ✅ Active")
    print(f"  🎨 Original Design: ✅ Restored")
    print(f"  💬 AI Dialogue Window: ✅ Active")
    print(f"  🤖 AI API: {'✅ Connected' if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'your-anthropic-api-key-here' else '❌ Missing'}")
    print(f"  📚 PRAW Library: {'✅ Available' if PRAW_AVAILABLE else '⚠️ Missing (gracefully handled)'}")
    print(f"  📱 Reddit API: {'✅ Connected' if reddit_researcher.reddit else '⚠️ Simulation Mode'}")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
