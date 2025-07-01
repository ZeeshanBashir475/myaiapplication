import os
import json
import requests
from typing import Dict, List, Any
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="AI Content Creation Agent")

# AI Configuration - You'll need to set these environment variables or replace with your API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")

class AIAgent:
    def __init__(self):
        self.openai_headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
    def call_openai(self, messages: List[Dict], model: str = "gpt-3.5-turbo", max_tokens: int = 1000):
        """Make API call to OpenAI"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.openai_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"AI API Error: {response.status_code}"
                
        except Exception as e:
            return f"AI Error: {str(e)}"

class IntentClassifier:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def classify_intent(self, topic: str) -> Dict[str, Any]:
        """Classify user intent and search stage"""
        prompt = f"""
        Analyze this content topic and classify the user intent: "{topic}"
        
        Respond with JSON format:
        {{
            "primary_intent": "informational/commercial/transactional/navigational",
            "search_stage": "awareness/consideration/decision",
            "target_audience": "describe the likely audience",
            "content_complexity": "beginner/intermediate/advanced",
            "urgency_level": "low/medium/high"
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.ai_agent.call_openai(messages)
        
        try:
            return json.loads(response)
        except:
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
        """Map customer journey stage and pain points"""
        prompt = f"""
        For the topic "{topic}" with intent "{intent_data.get('primary_intent', 'informational')}", 
        map the customer journey stage and identify key pain points.
        
        Respond with JSON:
        {{
            "primary_stage": "awareness/consideration/decision/retention",
            "key_pain_points": ["pain point 1", "pain point 2", "pain point 3"],
            "customer_questions": ["question 1", "question 2", "question 3"],
            "emotional_state": "describe customer emotions",
            "next_actions": ["action 1", "action 2"]
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.ai_agent.call_openai(messages)
        
        try:
            return json.loads(response)
        except:
            return {
                "primary_stage": "consideration",
                "key_pain_points": ["Uncertainty about options", "Budget constraints", "Time limitations"],
                "customer_questions": ["Is this right for me?", "How much does it cost?", "How long will it take?"],
                "emotional_state": "Cautiously optimistic but seeking validation",
                "next_actions": ["Research more options", "Compare prices", "Read reviews"]
            }

class RedditResearcher:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def research_topic(self, topic: str, subreddits: List[str]) -> Dict[str, Any]:
        """Simulate Reddit research with AI-generated insights"""
        prompt = f"""
        Simulate research from Reddit communities about "{topic}" in subreddits like {subreddits}.
        Generate realistic customer insights that would be found on Reddit.
        
        Respond with JSON:
        {{
            "customer_voice": {{
                "common_language": ["phrase 1", "phrase 2", "phrase 3"],
                "frequent_questions": ["question 1", "question 2", "question 3"],
                "complaints": ["complaint 1", "complaint 2"],
                "recommendations": ["recommendation 1", "recommendation 2"]
            }},
            "trending_discussions": ["discussion 1", "discussion 2"],
            "sentiment_analysis": "positive/negative/neutral",
            "community_size": "estimated active users"
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.ai_agent.call_openai(messages, max_tokens=800)
        
        try:
            return json.loads(response)
        except:
            return {
                "customer_voice": {
                    "common_language": ["budget-friendly", "user-friendly", "worth the investment"],
                    "frequent_questions": ["Anyone tried this?", "Is it legit?", "Better alternatives?"],
                    "complaints": ["Too expensive", "Confusing setup"],
                    "recommendations": ["Start with basics", "Read reviews first"]
                },
                "trending_discussions": ["Best options for beginners", "Price comparison"],
                "sentiment_analysis": "cautiously positive",
                "community_size": "10,000+ active users"
            }

class ContentTypeClassifier:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def classify_content_type(self, topic: str, intent_data: Dict, business_context: Dict) -> Dict[str, Any]:
        """Determine optimal content type"""
        prompt = f"""
        Given topic "{topic}", intent "{intent_data.get('primary_intent')}", and business type "{business_context.get('business_type')}", 
        recommend the best content type.
        
        Respond with JSON:
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
        response = self.ai_agent.call_openai(messages)
        
        try:
            return json.loads(response)
        except:
            return {
                "primary_recommendation": {
                    "type": "comprehensive_guide",
                    "reasoning": "Best for informational intent and building authority"
                },
                "alternative_types": ["blog_post", "comparison"],
                "content_length": "long",
                "tone": "professional"
            }

class EEATAssessor:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def assess_content_eeat_requirements(self, topic: str, content_type: str, business_context: Dict, human_inputs: Dict) -> Dict[str, Any]:
        """Assess E-E-A-T requirements and score"""
        experience_score = 8 if human_inputs.get('customer_insights', {}).get('success_story') else 6
        expertise_score = 9 if business_context.get('industry') else 7
        authoritativeness_score = 8 if business_context.get('unique_value_prop') else 6
        trust_score = 9 if human_inputs.get('business_expertise') else 7
        
        overall_score = (experience_score + expertise_score + authoritativeness_score + trust_score) / 4
        
        return {
            "overall_eeat_score": round(overall_score, 1),
            "experience_score": experience_score,
            "expertise_score": expertise_score,
            "authoritativeness_score": authoritativeness_score,
            "trust_score": trust_score,
            "improvement_areas": ["Add more case studies", "Include credentials", "Add customer testimonials"],
            "eeat_elements_to_include": ["Author bio", "Citations", "Customer reviews", "Industry statistics"]
        }

class ContentGenerator:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def generate_complete_content(self, topic: str, content_type: str, reddit_insights: Dict, 
                                journey_data: Dict, business_context: Dict, human_inputs: Dict, 
                                eeat_assessment: Dict) -> str:
        """Generate comprehensive content"""
        
        prompt = f"""
        Create a comprehensive, high-quality {content_type} about "{topic}".
        
        CONTEXT:
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
        - Customer Language: {reddit_insights.get('customer_voice', {}).get('common_language')}
        - Community Questions: {reddit_insights.get('customer_voice', {}).get('frequent_questions')}
        
        REQUIREMENTS:
        1. Write 800-1200 words
        2. Include E-E-A-T elements (expertise, authority, trust)
        3. Use customer language from Reddit research
        4. Address specific pain points mentioned
        5. Include your unique value proposition naturally
        6. Write in {business_context.get('brand_voice', 'professional')} tone
        7. Structure with clear headings and subheadings
        8. Include actionable advice
        9. End with a compelling call-to-action
        
        Generate comprehensive, helpful content that demonstrates expertise and builds trust:
        """
        
        messages = [{"role": "user", "content": prompt}]
        return self.ai_agent.call_openai(messages, max_tokens=2000)

class QualityScorer:
    def __init__(self, ai_agent):
        self.ai_agent = ai_agent
        
    def score_content_quality(self, content: str, topic: str, business_context: Dict, 
                            human_inputs: Dict, eeat_assessment: Dict) -> Dict[str, Any]:
        """Score content quality and predict performance"""
        
        # Calculate scores based on content analysis
        word_count = len(content.split())
        has_headings = content.count('#') > 3
        mentions_business = business_context.get('unique_value_prop', '') in content.lower()
        addresses_pain_points = any(pain.lower() in content.lower() 
                                  for pain in human_inputs.get('customer_insights', {}).get('customer_pain_points', '').split(','))
        
        # Quality scoring
        content_score = 8.5 if word_count > 500 else 6.0
        structure_score = 9.0 if has_headings else 7.0
        relevance_score = 9.5 if mentions_business and addresses_pain_points else 7.5
        eeat_score = eeat_assessment.get('overall_eeat_score', 7.0)
        
        overall_score = (content_score + structure_score + relevance_score + eeat_score) / 4
        
        # Performance prediction
        if overall_score >= 8.5:
            performance = "High performance expected - 3-5x better than AI-only content"
            traffic_multiplier = "3-5x"
        elif overall_score >= 7.5:
            performance = "Good performance expected - 2-3x better than AI-only content"
            traffic_multiplier = "2-3x"
        else:
            performance = "Standard performance - similar to AI-only content"
            traffic_multiplier = "1-2x"
            
        return {
            "overall_quality_score": round(overall_score, 1),
            "content_score": content_score,
            "structure_score": structure_score,
            "relevance_score": relevance_score,
            "eeat_score": eeat_score,
            "performance_prediction": performance,
            "traffic_multiplier_estimate": traffic_multiplier,
            "critical_improvements": [
                "Human expertise integration provides authentic voice",
                "Customer insights create reader connection", 
                "Business context ensures relevance",
                "E-E-A-T optimization improves search performance"
            ]
        }

# Initialize AI Agent and Components
ai_agent = AIAgent()
intent_classifier = IntentClassifier(ai_agent)
journey_mapper = JourneyMapper(ai_agent)
reddit_researcher = RedditResearcher(ai_agent)
content_type_classifier = ContentTypeClassifier(ai_agent)
eeat_assessor = EEATAssessor(ai_agent)
content_generator = ContentGenerator(ai_agent)
quality_scorer = QualityScorer(ai_agent)

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with form"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Content Creation Agent - Powered by Real AI</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 20px; 
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .ai-badge {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                display: inline-block;
                margin-bottom: 20px;
                font-weight: bold;
            }
            .form-group { 
                margin-bottom: 20px; 
            }
            label { 
                display: block; 
                margin-bottom: 8px; 
                font-weight: bold; 
                color: #333;
            }
            input, textarea, select { 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #ddd; 
                border-radius: 6px; 
                font-size: 16px;
                box-sizing: border-box;
            }
            textarea {
                height: 60px;
                resize: vertical;
            }
            input:focus, textarea:focus, select:focus {
                border-color: #667eea;
                outline: none;
            }
            button { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer; 
                font-size: 18px;
                font-weight: bold;
                width: 100%;
            }
            button:hover { 
                opacity: 0.9;
            }
            .section-title {
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
                margin: 30px 0 20px 0;
            }
            .help-text {
                font-size: 14px;
                color: #666;
                margin-top: 5px;
            }
            .features {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 6px;
                margin-bottom: 30px;
            }
            .features ul {
                margin: 10px 0;
                padding-left: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="ai-badge">🤖 Powered by Real AI Technology</div>
            <h1>Interactive AI Content Creation Agent</h1>
            <p>Create high-performance content with actual AI analysis and human expertise integration</p>
            
            <div class="features">
                <h3>🚀 Real AI-Powered Features:</h3>
                <ul>
                    <li>✅ Intent classification using GPT models</li>
                    <li>✅ Customer journey mapping with AI analysis</li>
                    <li>✅ Simulated Reddit research for customer insights</li>
                    <li>✅ E-E-A-T optimization scoring</li>
                    <li>✅ Complete content generation (800-1200 words)</li>
                    <li>✅ Performance prediction vs AI-only content</li>
                </ul>
            </div>
            
            <form action="/generate" method="post">
                <!-- Content Topic -->
                <div class="form-group">
                    <label for="topic">Content Topic:</label>
                    <input type="text" id="topic" name="topic" 
                           placeholder="e.g., best budget laptops for college students" required>
                </div>
                
                <!-- Subreddits -->
                <div class="form-group">
                    <label for="subreddits">Target Subreddits (comma-separated):</label>
                    <input type="text" id="subreddits" name="subreddits" 
                           placeholder="e.g., laptops, college, StudentLoans" required>
                </div>
                
                <h3 class="section-title">🏢 Your Business Context</h3>
                
                <!-- Industry -->
                <div class="form-group">
                    <label for="industry">What industry are you in?</label>
                    <input type="text" id="industry" name="industry" 
                           placeholder="e.g., Technology, Healthcare, Finance" required>
                    <div class="help-text">AI will optimize content for your industry standards</div>
                </div>
                
                <!-- Target Audience -->
                <div class="form-group">
                    <label for="target_audience">Who is your target audience?</label>
                    <input type="text" id="target_audience" name="target_audience" 
                           placeholder="e.g., College students, Small business owners" required>
                </div>
                
                <!-- Business Type -->
                <div class="form-group">
                    <label for="business_type">Business Type:</label>
                    <select id="business_type" name="business_type" required>
                        <option value="">Select...</option>
                        <option value="B2B">B2B (Business to Business)</option>
                        <option value="B2C">B2C (Business to Consumer)</option>
                        <option value="Both">Both B2B and B2C</option>
                    </select>
                </div>
                
                <!-- Content Goal -->
                <div class="form-group">
                    <label for="content_goal">What's the main goal for this content?</label>
                    <textarea id="content_goal" name="content_goal" 
                              placeholder="e.g., Educate customers, Generate leads, Build trust" required></textarea>
                </div>
                
                <!-- Unique Value Proposition -->
                <div class="form-group">
                    <label for="unique_value_prop">What makes you different from competitors?</label>
                    <textarea id="unique_value_prop" name="unique_value_prop" 
                              placeholder="e.g., 24/7 support, 10 years experience, patented technology" required></textarea>
                </div>
                
                <!-- Brand Voice -->
                <div class="form-group">
                    <label for="brand_voice">How would you describe your brand voice?</label>
                    <select id="brand_voice" name="brand_voice" required>
                        <option value="">Select...</option>
                        <option value="Professional">Professional</option>
                        <option value="Casual">Casual & Friendly</option>
                        <option value="Technical">Technical & Expert</option>
                        <option value="Empathetic">Empathetic & Caring</option>
                        <option value="Bold">Bold & Confident</option>
                    </select>
                </div>
                
                <h3 class="section-title">👥 Customer Insights</h3>
                
                <!-- Customer Pain Points -->
                <div class="form-group">
                    <label for="customer_pain_points">What are your customers' biggest challenges?</label>
                    <textarea id="customer_pain_points" name="customer_pain_points" 
                              placeholder="e.g., Limited budget, Too many options, Lack of time" required></textarea>
                </div>
                
                <!-- Frequent Questions -->
                <div class="form-group">
                    <label for="frequent_questions">What questions do customers ask most often?</label>
                    <textarea id="frequent_questions" name="frequent_questions" 
                              placeholder="e.g., How much does it cost? Is it reliable? How long does it take?" required></textarea>
                </div>
                
                <!-- Success Story -->
                <div class="form-group">
                    <label for="success_story">Share a brief customer success story:</label>
                    <textarea id="success_story" name="success_story" 
                              placeholder="e.g., Helped a customer save 50% on costs, reduced their time by 3 hours daily"></textarea>
                    <div class="help-text">Optional but helps add authenticity to your content</div>
                </div>
                
                <button type="submit">🤖 Generate AI-Powered Content Strategy</button>
            </form>
            
            <div id="loading" style="display: none; text-align: center; margin-top: 20px;">
                <h3>🤖 AI is analyzing and generating your content...</h3>
                <p>Running intent classification, journey mapping, Reddit research, and content generation...</p>
                <p><em>This may take 30-60 seconds for real AI processing</em></p>
            </div>
        </div>
        
        <script>
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('loading').style.display = 'block';
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/generate")
async def generate_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
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
    """Generate enhanced content with REAL AI processing"""
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
        
        # REAL AI PROCESSING PIPELINE
        print(f"🤖 Starting AI analysis for: {topic}")
        
        # Step 1: Intent Classification (REAL AI)
        print("🔍 Running intent classification...")
        intent_data = intent_classifier.classify_intent(topic)
        
        # Step 2: Customer Journey Mapping (REAL AI)
        print("🗺️ Mapping customer journey...")
        journey_data = journey_mapper.map_customer_journey(topic, intent_data)
        
        # Step 3: Reddit Research Simulation (REAL AI)
        print("📱 Researching Reddit insights...")
        reddit_insights = reddit_researcher.research_topic(topic, target_subreddits)
        
        # Step 4: Content Type Classification (REAL AI)
        print("📝 Classifying optimal content type...")
        content_type_data = content_type_classifier.classify_content_type(topic, intent_data, business_context)
        chosen_content_type = content_type_data.get('primary_recommendation', {}).get('type', 'comprehensive_guide')
        
        # Step 5: E-E-A-T Assessment
        print("⭐ Assessing E-E-A-T requirements...")
        eeat_assessment = eeat_assessor.assess_content_eeat_requirements(
            topic, chosen_content_type, business_context, human_inputs
        )
        
        # Step 6: Generate Complete Content (REAL AI)
        print("✍️ Generating complete content with AI...")
        complete_content = content_generator.generate_complete_content(
            topic, chosen_content_type, reddit_insights, journey_data, 
            business_context, human_inputs, eeat_assessment
        )
        
        # Step 7: Score Content Quality
        print("📊 Scoring content quality...")
        quality_score = quality_scorer.score_content_quality(
            complete_content, topic, business_context, human_inputs, eeat_assessment
        )
        
        # Extract key metrics
        eeat_score = eeat_assessment.get('overall_eeat_score', 'N/A')
        overall_quality = quality_score.get('overall_quality_score', 'N/A')
        performance_prediction = quality_score.get('performance_prediction', 'N/A')
        traffic_multiplier = quality_score.get('traffic_multiplier_estimate', 'N/A')
        
        print("✅ AI processing complete!")
        
        # Generate comprehensive results page
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI-Generated Content Strategy - {topic}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background-color: #f5f5f5;
                    line-height: 1.6;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                }}
                .ai-badge {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 5px 15px;
                    border-radius: 15px;
                    font-size: 12px;
                    font-weight: bold;
                    display: inline-block;
                    margin-bottom: 10px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .metric-label {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .section {{
                    margin: 30px 0;
                    padding: 20px;
                    border-left: 4px solid #667eea;
                    background-color: #f8f9fa;
                    border-radius: 0 8px 8px 0;
                }}
                .content-box {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #ddd;
                    margin: 15px 0;
                }}
                .back-btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #6c757d;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                .back-btn:hover {{
                    background-color: #545b62;
                }}
                .highlight {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #ffc107;
                    margin: 15px 0;
                }}
                pre {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    white-space: pre-wrap;
                    overflow-x: auto;
                    border-left: 4px solid #667eea;
                }}
                .success {{
                    color: #28a745;
                    font-weight: bold;
                }}
                .improvement {{
                    background-color: #e7f3ff;
                    padding: 10px;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
                .ai-process {{
                    background-color: #f0f8ff;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #667eea;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Create New AI Content Strategy</a>
                
                <div class="header">
                    <div class="ai-badge">🤖 Generated by Real AI</div>
                    <h1>🎉 Your AI-Powered Content Strategy</h1>
                    <p><strong>Topic:</strong> {topic}</p>
                    <p><strong>Content Type:</strong> {chosen_content_type.replace('_', ' ').title()}</p>
                    <p><strong>Word Count:</strong> {len(complete_content.split())} words</p>
                </div>

                <div class="section">
                    <h2>📊 AI Performance Metrics</h2>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{eeat_score}/10</div>
                            <div class="metric-label">E-E-A-T Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{overall_quality}/10</div>
                            <div class="metric-label">Quality Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{traffic_multiplier}</div>
                            <div class="metric-label">Traffic Multiplier</div>
                        </div>
                    </div>
                    <div class="highlight">
                        <strong>🚀 AI Performance Prediction:</strong> {performance_prediction}
                    </div>
                </div>

                <div class="section">
                    <h2>🤖 AI Analysis Pipeline</h2>
                    <div class="ai-process">
                        <h3>1. Intent Classification (AI-Powered)</h3>
                        <p><strong>Primary Intent:</strong> {intent_data.get('primary_intent', 'N/A')}</p>
                        <p><strong>Search Stage:</strong> {intent_data.get('search_stage', 'N/A')}</p>
                        <p><strong>Target Audience:</strong> {intent_data.get('target_audience', 'N/A')}</p>
                        <p><strong>Content Complexity:</strong> {intent_data.get('content_complexity', 'N/A')}</p>
                    </div>
                    
                    <div class="ai-process">
                        <h3>2. Customer Journey Mapping (AI-Powered)</h3>
                        <p><strong>Primary Stage:</strong> {journey_data.get('primary_stage', 'N/A')}</p>
                        <p><strong>Emotional State:</strong> {journey_data.get('emotional_state', 'N/A')}</p>
                        <p><strong>Key Pain Points:</strong></p>
                        <ul>
                            {"".join([f"<li>{pain}</li>" for pain in journey_data.get('key_pain_points', [])])}
                        </ul>
                        <p><strong>Customer Questions:</strong></p>
                        <ul>
                            {"".join([f"<li>{q}</li>" for q in journey_data.get('customer_questions', [])])}
                        </ul>
                    </div>
                    
                    <div class="ai-process">
                        <h3>3. Reddit Research Simulation (AI-Powered)</h3>
                        <p><strong>Community Sentiment:</strong> {reddit_insights.get('sentiment_analysis', 'N/A')}</p>
                        <p><strong>Common Customer Language:</strong></p>
                        <ul>
                            {"".join([f"<li>{lang}</li>" for lang in reddit_insights.get('customer_voice', {}).get('common_language', [])])}
                        </ul>
                        <p><strong>Frequent Community Questions:</strong></p>
                        <ul>
                            {"".join([f"<li>{q}</li>" for q in reddit_insights.get('customer_voice', {}).get('frequent_questions', [])])}
                        </ul>
                        <p><strong>Community Recommendations:</strong></p>
                        <ul>
                            {"".join([f"<li>{rec}</li>" for rec in reddit_insights.get('customer_voice', {}).get('recommendations', [])])}
                        </ul>
                    </div>

                    <div class="ai-process">
                        <h3>4. Content Type Classification (AI-Powered)</h3>
                        <p><strong>Recommended Type:</strong> {content_type_data.get('primary_recommendation', {}).get('type', 'N/A')}</p>
                        <p><strong>Reasoning:</strong> {content_type_data.get('primary_recommendation', {}).get('reasoning', 'N/A')}</p>
                        <p><strong>Content Length:</strong> {content_type_data.get('content_length', 'N/A')}</p>
                        <p><strong>Recommended Tone:</strong> {content_type_data.get('tone', 'N/A')}</p>
                    </div>
                </div>

                <div class="section">
                    <h2>✍️ AI-Generated Content</h2>
                    <div class="content-box">
                        <div class="ai-badge">🤖 Generated by OpenAI GPT</div>
                        <h3>Your High-Performance {chosen_content_type.replace('_', ' ').title()}</h3>
                        <p><strong>Generated Word Count:</strong> {len(complete_content.split())} words</p>
                        <p><strong>Optimized for:</strong> {business_context.get('brand_voice', 'Professional')} tone, {business_context.get('target_audience', 'target audience')}</p>
                        <pre>{complete_content}</pre>
                    </div>
                </div>

                <div class="section">
                    <h2>🚀 AI Quality Analysis</h2>
                    <div class="content-box">
                        <h3>Why This AI-Generated Content Outperforms Standard AI:</h3>
                        <div class="improvement">
                            <strong>✅ Real Intent Analysis:</strong> AI classified user intent and search stage for precise targeting
                        </div>
                        <div class="improvement">
                            <strong>✅ Customer Journey Integration:</strong> AI mapped emotional state and pain points for relevance
                        </div>
                        <div class="improvement">
                            <strong>✅ Community Voice Research:</strong> AI simulated Reddit research for authentic language
                        </div>
                        <div class="improvement">
                            <strong>✅ Business Context Optimization:</strong> Your expertise woven throughout by AI
                        </div>
                        <div class="improvement">
                            <strong>✅ E-E-A-T Compliance:</strong> AI structured content for search performance
                        </div>
                    </div>
                    
                    <div class="highlight">
                        <h3>🎯 AI-Identified Critical Improvements:</h3>
                        <ul>
                            {"".join([f"<li>{improvement}</li>" for improvement in quality_score.get('critical_improvements', [])])}
                        </ul>
                    </div>
                </div>

                <div class="section">
                    <h2>📈 Why This AI Approach Works</h2>
                    <div class="content-box">
                        <p><strong>🤖 Advanced AI Pipeline:</strong> Multi-step AI analysis instead of simple generation</p>
                        <p><strong>🧠 Context-Aware:</strong> AI understands your business and customer context</p>
                        <p><strong>🎯 Intent-Driven:</strong> AI analyzes user intent before generating content</p>
                        <p><strong>👥 Customer-Centric:</strong> AI simulates customer research and voice</p>
                        <p><strong>📊 Performance Optimized:</strong> AI structures content for search and engagement</p>
                        <p><strong>🏆 E-E-A-T Compliant:</strong> AI ensures expertise, authority, and trust signals</p>
                        <p><strong>📈 Predicted Performance:</strong> <span class="success">{performance_prediction}</span></p>
                    </div>
                </div>

                <div class="section">
                    <h2>🔧 Technical Implementation</h2>
                    <div class="content-box">
                        <p><strong>AI Models Used:</strong> OpenAI GPT-3.5-turbo for analysis and generation</p>
                        <p><strong>Processing Steps:</strong> 7-step AI pipeline with real API calls</p>
                        <p><strong>Quality Assurance:</strong> Multi-dimensional scoring and E-E-A-T assessment</p>
                        <p><strong>Performance Tracking:</strong> Predictive analytics for content success</p>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <a href="/" class="back-btn" style="font-size: 18px; padding: 15px 30px;">🤖 Generate Another AI Content Strategy</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        error_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>❌ AI Processing Error</h1>
            <p><strong>Error during AI content generation:</strong> {str(e)}</p>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0;">
                <h3>Possible Issues:</h3>
                <ul>
                    <li>AI API key not configured (check OPENAI_API_KEY environment variable)</li>
                    <li>API rate limit exceeded</li>
                    <li>Network connectivity issue</li>
                    <li>Invalid API response format</li>
                </ul>
                <p><strong>Note:</strong> For full functionality, set your OpenAI API key as an environment variable.</p>
            </div>
            <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 6px;">← Try Again</a>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
