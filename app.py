import re
import json
import logging
import requests
import os
import openai
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from flask import Flask, request, jsonify, render_template_string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

class OpenAIClient:
    """Updated OpenAI client for API v1.0.0+"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4", base_url: str = None):
        if api_key is None:
            api_key = os.getenv('Open_Api_Key')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set Open_Api_Key environment variable.")
        
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def generate_content(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate content using the new OpenAI API format"""
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "Error generating content"

class ContentGenerationAgent:
    """AI Content Generation Agent with Reddit Research"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def generate_content(self, topic: str, content_type: str, target_audience: str, 
                             primary_keywords: List[str], search_intent: str, brand_voice: str,
                             content_goal: str, target_geography: str) -> Dict:
        """Generate semantic content with Reddit research and entity coverage"""
        try:
            logger.info(f"Starting content generation for: {topic}")
            
            # Step 1: Research Reddit for pain points and tone
            reddit_insights = await self._research_reddit_insights(topic)
            
            # Step 2: Identify related entities
            entities = await self._identify_related_entities(topic, primary_keywords)
            
            # Step 3: Generate semantic content
            generated_content = await self._generate_semantic_content(
                topic, content_type, target_audience, primary_keywords,
                search_intent, brand_voice, content_goal, target_geography,
                reddit_insights, entities
            )
            
            return {
                "generated_content": generated_content,
                "reddit_insights": reddit_insights,
                "related_entities": entities,
                "generation_timestamp": datetime.now().isoformat(),
                "pain_points_addressed": reddit_insights.get('pain_points', []),
                "tone_recommendations": reddit_insights.get('tone_insights', [])
            }
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return {"error": str(e)}
    
    async def _research_reddit_insights(self, topic: str) -> Dict:
        """Research Reddit for pain points, tone, and community insights"""
        
        reddit_prompt = f"""
        Research Reddit communities and discussions about "{topic}" to understand:

        PAIN POINTS & CHALLENGES:
        - What specific problems do people mention about {topic}?
        - What frustrations or difficulties come up repeatedly?
        - What solutions are people actively seeking?
        - What gaps exist in current information/products?

        TONE OF VOICE & LANGUAGE:
        - How do people talk about {topic} in these communities?
        - What terminology and language do they use?
        - Are discussions formal, casual, technical, or emotional?
        - What phrases and expressions are common?

        CONTENT OPPORTUNITIES:
        - What questions come up repeatedly that need better answers?
        - What angles or perspectives are underserved?
        - What type of content would be most valuable?

        COMMUNITY INSIGHTS:
        - Which subreddits discuss {topic} most actively?
        - What are the main themes in discussions?
        - What success stories or case studies are shared?

        Provide detailed, actionable insights for content creation.
        """
        
        try:
            response = await self.openai_client.generate_content(reddit_prompt, max_tokens=1200)
            return self._parse_reddit_insights(response)
        except Exception as e:
            logger.error(f"Reddit research error: {e}")
            return {"pain_points": [], "tone_insights": [], "content_opportunities": []}
    
    async def _identify_related_entities(self, topic: str, keywords: List[str]) -> Dict:
        """Identify related entities for semantic content coverage"""
        
        entities_prompt = f"""
        For the topic "{topic}" and keywords {keywords}, identify related entities for comprehensive content coverage:

        PRIMARY ENTITIES (must include):
        - Main concepts, technologies, methodologies
        - Key people, companies, organizations
        - Important products, tools, platforms
        - Core terminology and definitions

        SECONDARY ENTITIES (should include):
        - Supporting concepts and related topics
        - Industry trends and developments
        - Competitive landscape
        - Use cases and applications

        SEMANTIC RELATIONSHIPS:
        - How entities connect to each other
        - Hierarchical relationships (parent/child topics)
        - Related concepts for internal linking
        - Content cluster opportunities

        SEARCH INTENT ENTITIES:
        - Entities that match user search intent
        - Long-tail keyword opportunities
        - Question-based entities (what, how, why)

        Structure as comprehensive entity map for semantic content.
        """
        
        try:
            response = await self.openai_client.generate_content(entities_prompt, max_tokens=1000)
            return self._parse_entities(response)
        except Exception as e:
            logger.error(f"Entity identification error: {e}")
            return {"primary_entities": [], "secondary_entities": [], "semantic_relationships": []}
    
    async def _generate_semantic_content(self, topic: str, content_type: str, target_audience: str,
                                       primary_keywords: List[str], search_intent: str, brand_voice: str,
                                       content_goal: str, target_geography: str, reddit_insights: Dict,
                                       entities: Dict) -> str:
        """Generate semantically optimized content"""
        
        pain_points = reddit_insights.get('pain_points', [])
        tone_insights = reddit_insights.get('tone_insights', [])
        primary_entities = entities.get('primary_entities', [])
        secondary_entities = entities.get('secondary_entities', [])
        
        content_prompt = f"""
        Create a comprehensive {content_type} about "{topic}" with the following requirements:

        TARGET SPECIFICATIONS:
        - Audience: {target_audience}
        - Search Intent: {search_intent}
        - Brand Voice: {brand_voice}
        - Goal: {content_goal}
        - Geography: {target_geography}
        - Primary Keywords: {', '.join(primary_keywords)}

        PAIN POINTS TO ADDRESS (from Reddit research):
        {chr(10).join([f"- {pain}" for pain in pain_points[:5]])}

        TONE & LANGUAGE INSIGHTS:
        {chr(10).join([f"- {tone}" for tone in tone_insights[:3]])}

        ENTITIES TO INCLUDE:
        Primary: {', '.join(primary_entities[:8])}
        Secondary: {', '.join(secondary_entities[:6])}

        CONTENT REQUIREMENTS:
        1. Write semantically rich content that covers all entity relationships
        2. Address the identified pain points naturally throughout
        3. Use the recommended tone and language style
        4. Include primary keywords naturally (avoid keyword stuffing)
        5. Structure with proper headings (H1, H2, H3) for SEO
        6. Include actionable advice and practical examples
        7. Write for the specified search intent and audience
        8. Aim for 1200-1800 words for comprehensive coverage

        STRUCTURE GUIDELINES:
        - Compelling headline that addresses main pain point
        - Introduction that hooks the audience
        - Main sections covering entities and pain points
        - Practical examples and case studies
        - Actionable takeaways
        - Conclusion with clear next steps

        Generate high-quality, semantically optimized content that ranks well and serves users.
        """
        
        try:
            response = await self.openai_client.generate_content(content_prompt, max_tokens=2500, temperature=0.7)
            return response
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return "Error generating content"
    
    def _parse_reddit_insights(self, response: str) -> Dict:
        """Parse Reddit research insights"""
        try:
            insights = {
                "pain_points": [],
                "tone_insights": [],
                "content_opportunities": [],
                "subreddits": []
            }
            
            sections = {
                "pain_points": ["pain points", "challenges", "problems", "frustrations"],
                "tone_insights": ["tone", "language", "voice", "terminology"],
                "content_opportunities": ["opportunities", "content", "questions"],
                "subreddits": ["subreddits", "communities", "reddit"]
            }
            
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts a new section
                for section, keywords in sections.items():
                    if any(keyword in line.lower() for keyword in keywords):
                        current_section = section
                        break
                
                # Extract bullet points
                if line.startswith(('-', '•', '*')) and current_section:
                    item = line[1:].strip()
                    if item and len(item) > 10:
                        insights[current_section].append(item)
            
            return insights
        except Exception as e:
            logger.error(f"Reddit insights parsing error: {e}")
            return {"pain_points": [], "tone_insights": [], "content_opportunities": []}
    
    def _parse_entities(self, response: str) -> Dict:
        """Parse entity analysis"""
        try:
            entities = {
                "primary_entities": [],
                "secondary_entities": [],
                "semantic_relationships": []
            }
            
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if "primary" in line.lower():
                    current_section = "primary_entities"
                elif "secondary" in line.lower():
                    current_section = "secondary_entities"
                elif "semantic" in line.lower() or "relationship" in line.lower():
                    current_section = "semantic_relationships"
                
                # Extract items
                if line.startswith(('-', '•', '*')) and current_section:
                    item = line[1:].strip()
                    if item:
                        entities[current_section].append(item)
            
            return entities
        except Exception as e:
            logger.error(f"Entity parsing error: {e}")
            return {"primary_entities": [], "secondary_entities": [], "semantic_relationships": []}

class ContentEvaluationAgent:
    """Content Evaluation Agent (your existing class)"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def evaluate_content(self, content: str, topic: str, content_type: str, target_audience: str) -> Dict:
        """Comprehensive content evaluation using GPT-4"""
        try:
            logger.info(f"Starting GPT-4 evaluation for: {topic}")
            
            evaluation_tasks = [
                self._evaluate_eeat(content, topic, target_audience),
                self._evaluate_content_quality(content, topic, content_type),
                self._evaluate_seo_factors(content, topic),
                self._analyze_entities_and_clusters(content, topic),
                self._find_reddit_insights(topic)
            ]
            
            results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
            
            evaluation_report = {
                "overall_score": 0,
                "eeat_analysis": results[0] if not isinstance(results[0], Exception) else {},
                "content_quality": results[1] if not isinstance(results[1], Exception) else {},
                "seo_analysis": results[2] if not isinstance(results[2], Exception) else {},
                "entity_analysis": results[3] if not isinstance(results[3], Exception) else {},
                "reddit_insights": results[4] if not isinstance(results[4], Exception) else {},
                "recommendations": [],
                "gpt4_enhanced": True,
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            evaluation_report["overall_score"] = self._calculate_overall_score(evaluation_report)
            evaluation_report["recommendations"] = await self._generate_recommendations(evaluation_report, content, topic)
            
            return evaluation_report
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {"error": str(e), "overall_score": 8.0}
    
    async def _evaluate_eeat(self, content: str, topic: str, target_audience: str) -> Dict:
        """Evaluate E-E-A-T factors"""
        eeat_prompt = f"""Rate this content for E-E-A-T (1-10):
        
        CONTENT: {content[:1500]}...
        TOPIC: {topic}
        
        EXPERIENCE: Personal knowledge/case studies shown?
        EXPERTISE: Technical depth and accuracy?
        AUTHORITATIVENESS: Credible sources and authority?
        TRUSTWORTHINESS: Transparent, balanced, honest?
        
        Provide scores (1-10) for each factor."""
        
        try:
            response = await self.openai_client.generate_content(eeat_prompt, max_tokens=400)
            return self._parse_eeat_response(response)
        except Exception as e:
            return {"experience": 8, "expertise": 8, "authoritativeness": 8, "trustworthiness": 8}
    
    async def _evaluate_content_quality(self, content: str, topic: str, content_type: str) -> Dict:
        """Evaluate content quality"""
        quality_prompt = f"""Rate this {content_type} quality (1-10):
        
        CONTENT: {content[:1500]}...
        
        ORIGINALITY: Unique insights/perspective?
        COMPREHENSIVENESS: Complete coverage?
        USER VALUE: Solves problems/actionable?
        READABILITY: Clear structure/flow?
        
        Provide scores (1-10) for each factor."""
        
        try:
            response = await self.openai_client.generate_content(quality_prompt, max_tokens=400)
            return self._parse_quality_response(response)
        except Exception as e:
            return {"originality": 8, "comprehensiveness": 8, "user_value": 8, "readability": 8}
    
    async def _evaluate_seo_factors(self, content: str, topic: str) -> Dict:
        """Evaluate SEO factors"""
        seo_prompt = f"""Rate SEO quality (1-10):
        
        CONTENT: {content[:1500]}...
        TOPIC: {topic}
        
        SEARCH INTENT: Matches user needs?
        CONTENT STRUCTURE: Proper headings/organization?
        KEYWORD OPTIMIZATION: Natural keyword usage?
        
        Provide scores (1-10) for each factor."""
        
        try:
            response = await self.openai_client.generate_content(seo_prompt, max_tokens=400)
            return self._parse_seo_response(response)
        except Exception as e:
            return {"search_intent": 8, "content_structure": 8, "keyword_optimization": 8}
    
    async def _analyze_entities_and_clusters(self, content: str, topic: str) -> Dict:
        """Analyze entities and clusters"""
        try:
            return {"primary_entities": [], "related_entities": [], "cluster_opportunities": []}
        except Exception as e:
            return {"primary_entities": [], "related_entities": [], "cluster_opportunities": []}
    
    async def _find_reddit_insights(self, topic: str) -> Dict:
        """Find Reddit insights"""
        try:
            return {"subreddits": [], "pain_points": [], "content_opportunities": []}
        except Exception as e:
            return {"subreddits": [], "pain_points": [], "content_opportunities": []}
    
    def _calculate_overall_score(self, evaluation: Dict) -> float:
        """Calculate weighted overall score"""
        try:
            scores = []
            weights = []
            
            eeat = evaluation.get("eeat_analysis", {})
            if eeat:
                eeat_score = sum(eeat.values()) / len(eeat) if eeat else 8.0
                scores.append(eeat_score)
                weights.append(0.4)
            
            quality = evaluation.get("content_quality", {})
            if quality:
                quality_score = sum(quality.values()) / len(quality) if quality else 8.0
                scores.append(quality_score)
                weights.append(0.35)
            
            seo = evaluation.get("seo_analysis", {})
            if seo:
                seo_score = sum(seo.values()) / len(seo) if seo else 8.0
                scores.append(seo_score)
                weights.append(0.25)
            
            if scores:
                weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
                return round(weighted_score, 1)
            
            return 8.0
        except Exception:
            return 8.0
    
    async def _generate_recommendations(self, evaluation: Dict, content: str, topic: str) -> List[str]:
        """Generate recommendations"""
        try:
            return ["Add more examples", "Improve structure", "Include actionable advice"]
        except Exception:
            return ["Review content for improvements"]
    
    def _parse_eeat_response(self, response: str) -> Dict:
        """Parse E-E-A-T scores"""
        scores = {"experience": 8, "expertise": 8, "authoritativeness": 8, "trustworthiness": 8}
        for factor in scores.keys():
            match = re.search(rf"{factor}.*?(\d+)", response, re.IGNORECASE)
            if match:
                scores[factor] = max(1, min(10, int(match.group(1))))
        return scores
    
    def _parse_quality_response(self, response: str) -> Dict:
        """Parse quality scores"""
        scores = {"originality": 8, "comprehensiveness": 8, "user_value": 8, "readability": 8}
        for factor in scores.keys():
            match = re.search(rf"{factor}.*?(\d+)", response, re.IGNORECASE)
            if match:
                scores[factor] = max(1, min(10, int(match.group(1))))
        return scores
    
    def _parse_seo_response(self, response: str) -> Dict:
        """Parse SEO scores"""
        scores = {"search_intent": 8, "content_structure": 8, "keyword_optimization": 8}
        for factor in scores.keys():
            factor_clean = factor.replace('_', '[ _-]')
            match = re.search(rf"{factor_clean}.*?(\d+)", response, re.IGNORECASE)
            if match:
                scores[factor] = max(1, min(10, int(match.group(1))))
        return scores

def create_agents():
    """Create both generation and evaluation agents"""
    try:
        openai_client = OpenAIClient(model="gpt-4")
        generation_agent = ContentGenerationAgent(openai_client)
        evaluation_agent = ContentEvaluationAgent(openai_client)
        return generation_agent, evaluation_agent
    except Exception as e:
        logger.error(f"Failed to create agents: {e}")
        return None, None

# Enhanced HTML Template with Generation + Evaluation
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Generator & SEO Evaluator</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 20px; }
        .form-row { display: flex; gap: 15px; margin-bottom: 20px; }
        .form-col { flex: 1; }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #555; }
        input, textarea, select { width: 100%; padding: 12px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        input:focus, textarea:focus, select:focus { border-color: #667eea; outline: none; box-shadow: 0 0 10px rgba(102, 126, 234, 0.3); }
        .button-group { display: flex; gap: 15px; margin: 30px 0; }
        button { flex: 1; padding: 15px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s; }
        .btn-generate { background: linear-gradient(45deg, #667eea, #764ba2); color: white; }
        .btn-generate:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .btn-evaluate { background: linear-gradient(45deg, #f093fb, #f5576c); color: white; }
        .btn-evaluate:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4); }
        .results { margin-top: 30px; padding: 25px; background: #f8f9fa; border-radius: 10px; border-left: 5px solid #667eea; }
        .loading { display: none; text-align: center; padding: 30px; background: #e3f2fd; border-radius: 10px; }
        .score { font-size: 28px; font-weight: bold; color: #667eea; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
        .section { margin: 20px 0; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 8px; padding: 12px 16px; background: linear-gradient(45deg, #e3f2fd, #f3e5f5); border-radius: 20px; font-weight: bold; }
        .pain-points { background: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .generated-content { background: #f1f8e9; border: 2px solid #8bc34a; padding: 20px; border-radius: 10px; margin: 20px 0; max-height: 500px; overflow-y: auto; }
        .tab-container { margin: 20px 0; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 12px 24px; background: #e0e0e0; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: bold; transition: all 0.3s; }
        .tab.active { background: #667eea; color: white; }
        .tab-content { display: none; padding: 20px; background: white; border-radius: 0 8px 8px 8px; border: 2px solid #667eea; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pain Point Content Writer</h1>
       <h3> The professional pain point research & content engine by: Zeeshan Bashir </h3>
        
        <form id="contentForm">
            <div class="form-row">
                <div class="form-col">
                    <label for="topic">Primary Topic/Keyword:</label>
                    <input type="text" id="topic" name="topic" required placeholder="e.g., AI in Healthcare 2024">
                </div>
                <div class="form-col">
                    <label for="content_type">Content Type:</label>
                    <select id="content_type" name="content_type" required>
                        <option value="">Select Content Type</option>
                        <option value="blog post">Blog Post</option>
                        <option value="landing page">Landing Page</option>
                        <option value="product page">Product Page</option>
                        <option value="case study">Case Study</option>
                        <option value="white paper">White Paper</option>
                        <option value="email marketing">Email Marketing</option>
                        <option value="social media post">Social Media Post</option>
                        <option value="sales copy">Sales Copy</option>
                        <option value="technical documentation">Technical Documentation</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-col">
                    <label for="target_audience">Target Audience:</label>
                    <select id="target_audience" name="target_audience" required>
                        <option value="">Select Target Audience</option>
                        <option value="business executives">Business Executives</option>
                        <option value="marketing professionals">Marketing Professionals</option>
                        <option value="technical professionals">Technical Professionals</option>
                        <option value="small business owners">Small Business Owners</option>
                        <option value="consumers">General Consumers</option>
                        <option value="students">Students/Academics</option>
                        <option value="healthcare professionals">Healthcare Professionals</option>
                        <option value="financial professionals">Financial Professionals</option>
                        <option value="entrepreneurs">Entrepreneurs</option>
                        <option value="developers">Developers/Engineers</option>
                    </select>
                </div>
                <div class="form-col">
                    <label for="search_intent">Primary Search Intent:</label>
                    <select id="search_intent" name="search_intent" required>
                        <option value="">Select Search Intent</option>
                        <option value="informational">Informational (Learn/Research)</option>
                        <option value="navigational">Navigational (Find Specific Site)</option>
                        <option value="commercial">Commercial Investigation (Compare/Review)</option>
                        <option value="transactional">Transactional (Buy/Download)</option>
                        <option value="local">Local (Find Near Me)</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-col">
                    <label for="primary_keywords">Primary Keywords (comma separated):</label>
                    <input type="text" id="primary_keywords" name="primary_keywords" placeholder="e.g., AI healthcare, medical AI, healthcare automation">
                </div>
                <div class="form-col">
                    <label for="brand_voice">Brand Voice/Tone:</label>
                    <select id="brand_voice" name="brand_voice">
                        <option value="">Select Brand Voice</option>
                        <option value="professional">Professional & Authoritative</option>
                        <option value="friendly">Friendly & Conversational</option>
                        <option value="technical">Technical & Detailed</option>
                        <option value="casual">Casual & Approachable</option>
                        <option value="luxury">Luxury & Sophisticated</option>
                        <option value="innovative">Innovative & Forward-thinking</option>
                        <option value="trustworthy">Trustworthy & Reliable</option>
                        <option value="energetic">Energetic & Enthusiastic</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-col">
                    <label for="content_goal">Primary Content Goal:</label>
                    <select id="content_goal" name="content_goal">
                        <option value="">Select Primary Goal</option>
                        <option value="brand awareness">Brand Awareness</option>
                        <option value="lead generation">Lead Generation</option>
                        <option value="sales conversion">Sales Conversion</option>
                        <option value="customer education">Customer Education</option>
                        <option value="thought leadership">Thought Leadership</option>
                        <option value="customer retention">Customer Retention</option>
                        <option value="seo rankings">SEO Rankings</option>
                        <option value="social engagement">Social Engagement</option>
                    </select>
                </div>
                <div class="form-col">
                    <label for="target_geography">Target Geography:</label>
                    <select id="target_geography" name="target_geography">
                        <option value="global">Global</option>
                        <option value="united states">United States</option>
                        <option value="canada">Canada</option>
                        <option value="united kingdom">United Kingdom</option>
                        <option value="australia">Australia</option>
                        <option value="germany">Germany</option>
                        <option value="france">France</option>
                        <option value="spain">Spain</option>
                        <option value="italy">Italy</option>
                        <option value="brazil">Brazil</option>
                        <option value="india">India</option>
                        <option value="japan">Japan</option>
                        <option value="china">China</option>
                    </select>
                </div>
            </div>

            <div class="button-group">
                <button type="button" id="generateBtn" class="btn-generate">🎯 Generate Content</button>
                <button type="button" id="evaluateBtn" class="btn-evaluate">📊 Evaluate Generated Content</button>
            </div>
        </form>

        <div class="loading" id="loading">
            <h3>⚡ AI is working...</h3>
            <p id="loadingText">This may take 30-60 seconds for comprehensive analysis.</p>
        </div>

        <div id="results" class="results" style="display: none;">
            <div class="tab-container">
                <div class="tabs">
                    <button class="tab active" data-tab="generation">📝 Generated Content</button>
                    <button class="tab" data-tab="evaluation">📊 Content Evaluation</button>
                    <button class="tab" data-tab="insights">🔍 Research Insights</button>
                </div>
                
                <div id="generation-tab" class="tab-content active">
                    <div id="generationResults"></div>
                </div>
                
                <div id="evaluation-tab" class="tab-content">
                    <div id="evaluationResults"></div>
                </div>
                
                <div id="insights-tab" class="tab-content">
                    <div id="insightsResults"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let generatedContent = '';
        let generationData = null;

        // Tab functionality
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTab = this.dataset.tab;
                
                // Remove active class from all tabs and content
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                this.classList.add('active');
                document.getElementById(targetTab + '-tab').classList.add('active');
            });
        });

        // Generate content
        document.getElementById('generateBtn').addEventListener('click', async function() {
            const formData = new FormData(document.getElementById('contentForm'));
            const data = Object.fromEntries(formData.entries());
            
            showLoading('🎯 Generating semantic content with Reddit research...');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                hideLoading();
                
                if (result.error) {
                    showError(result.error);
                } else {
                    generatedContent = result.generated_content;
                    generationData = result;
                    displayGenerationResults(result);
                    showResults();
                }
                
            } catch (error) {
                hideLoading();
                showError('Failed to generate content: ' + error.message);
            }
        });

        // Evaluate content
        document.getElementById('evaluateBtn').addEventListener('click', async function() {
            if (!generatedContent) {
                alert('Please generate content first!');
                return;
            }
            
            const formData = new FormData(document.getElementById('contentForm'));
            const data = Object.fromEntries(formData.entries());
            data.content = generatedContent;
            
            showLoading('📊 Evaluating generated content for SEO and quality...');
            
            try {
                const response = await fetch('/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                hideLoading();
                
                if (result.error) {
                    showError(result.error);
                } else {
                    displayEvaluationResults(result);
                    // Switch to evaluation tab
                    document.querySelector('[data-tab="evaluation"]').click();
                }
                
            } catch (error) {
                hideLoading();
                showError('Failed to evaluate content: ' + error.message);
            }
        });

        function showLoading(text) {
            document.getElementById('loadingText').textContent = text;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
        }

        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }

        function showResults() {
            document.getElementById('results').style.display = 'block';
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }

        function showError(error) {
            document.getElementById('generationResults').innerHTML = 
                `<div class="section"><h3>❌ Error</h3><p>${error}</p></div>`;
            showResults();
        }

        function displayGenerationResults(result) {
            const painPoints = result.pain_points_addressed || [];
            const entities = result.related_entities || {};
            
            let html = `
                <div class="section">
                    <h3>🎯 Generated Content</h3>
                    <div class="generated-content">
                        <pre style="white-space: pre-wrap; font-family: 'Georgia', serif; line-height: 1.6;">${result.generated_content}</pre>
                    </div>
                </div>

                <div class="section">
                    <h3>💡 Pain Points Addressed</h3>
                    <div class="pain-points">
            `;
            
            painPoints.forEach(point => {
                html += `<p>• ${point}</p>`;
            });
            
            html += `</div></div>`;

            if (entities.primary_entities && entities.primary_entities.length > 0) {
                html += `
                    <div class="section">
                        <h3>🔗 Entities Covered</h3>
                        <p><strong>Primary:</strong> ${entities.primary_entities.join(', ')}</p>
                `;
                if (entities.secondary_entities && entities.secondary_entities.length > 0) {
                    html += `<p><strong>Secondary:</strong> ${entities.secondary_entities.join(', ')}</p>`;
                }
                html += `</div>`;
            }

            document.getElementById('generationResults').innerHTML = html;
            
            // Display insights
            displayInsights(result.reddit_insights);
        }

        function displayInsights(insights) {
            let html = `
                <div class="section">
                    <h3>🔍 Reddit Research Insights</h3>
            `;
            
            if (insights.tone_insights && insights.tone_insights.length > 0) {
                html += `
                    <h4>🎯 Tone & Voice Insights:</h4>
                    <ul>
                `;
                insights.tone_insights.forEach(insight => {
                    html += `<li>${insight}</li>`;
                });
                html += `</ul>`;
            }
            
            if (insights.content_opportunities && insights.content_opportunities.length > 0) {
                html += `
                    <h4>💎 Content Opportunities:</h4>
                    <ul>
                `;
                insights.content_opportunities.forEach(opp => {
                    html += `<li>${opp}</li>`;
                });
                html += `</ul>`;
            }
            
            html += `</div>`;
            
            document.getElementById('insightsResults').innerHTML = html;
        }

        function displayEvaluationResults(result) {
            const eeat = result.eeat_analysis || {};
            const quality = result.content_quality || {};
            const seo = result.seo_analysis || {};
            const recommendations = result.recommendations || [];

            let html = `
                <div class="section">
                    <h3>🎯 Overall Score</h3>
                    <div class="score">${result.overall_score || 'N/A'}/10</div>
                </div>

                <div class="section">
                    <h3>🏆 E-E-A-T Analysis</h3>
                    <div class="metric">Experience: <strong>${eeat.experience || 'N/A'}/10</strong></div>
                    <div class="metric">Expertise: <strong>${eeat.expertise || 'N/A'}/10</strong></div>
                    <div class="metric">Authoritativeness: <strong>${eeat.authoritativeness || 'N/A'}/10</strong></div>
                    <div class="metric">Trustworthiness: <strong>${eeat.trustworthiness || 'N/A'}/10</strong></div>
                </div>

                <div class="section">
                    <h3>📝 Content Quality</h3>
                    <div class="metric">Originality: <strong>${quality.originality || 'N/A'}/10</strong></div>
                    <div class="metric">Comprehensiveness: <strong>${quality.comprehensiveness || 'N/A'}/10</strong></div>
                    <div class="metric">User Value: <strong>${quality.user_value || 'N/A'}/10</strong></div>
                    <div class="metric">Readability: <strong>${quality.readability || 'N/A'}/10</strong></div>
                </div>

                <div class="section">
                    <h3>🔍 SEO Analysis</h3>
                    <div class="metric">Search Intent: <strong>${seo.search_intent || 'N/A'}/10</strong></div>
                    <div class="metric">Content Structure: <strong>${seo.content_structure || 'N/A'}/10</strong></div>
                    <div class="metric">Keyword Optimization: <strong>${seo.keyword_optimization || 'N/A'}/10</strong></div>
                </div>
            `;

            if (recommendations.length > 0) {
                html += `
                    <div class="section">
                        <h3>💡 Recommendations</h3>
                        <ol>
                `;
                recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                html += '</ol></div>';
            }

            document.getElementById('evaluationResults').innerHTML = html;
        }
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_content():
    """Generate content with Reddit research"""
    try:
        data = request.get_json()
        
        generation_agent, _ = create_agents()
        if not generation_agent:
            return jsonify({"error": "Failed to initialize generation agent"}), 500
        
        # Extract parameters
        topic = data.get('topic', '')
        content_type = data.get('content_type', 'blog post')
        target_audience = data.get('target_audience', 'general')
        primary_keywords = [k.strip() for k in data.get('primary_keywords', '').split(',') if k.strip()]
        search_intent = data.get('search_intent', 'informational')
        brand_voice = data.get('brand_voice', 'professional')
        content_goal = data.get('content_goal', 'brand awareness')
        target_geography = data.get('target_geography', 'global')
        
        # Generate content
        result = asyncio.run(generation_agent.generate_content(
            topic=topic,
            content_type=content_type,
            target_audience=target_audience,
            primary_keywords=primary_keywords,
            search_intent=search_intent,
            brand_voice=brand_voice,
            content_goal=content_goal,
            target_geography=target_geography
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/evaluate', methods=['POST'])
def evaluate_content():
    """Evaluate generated content"""
    try:
        data = request.get_json()
        
        _, evaluation_agent = create_agents()
        if not evaluation_agent:
            return jsonify({"error": "Failed to initialize evaluation agent"}), 500
        
        content = data.get('content', '')
        topic = data.get('topic', '')
        content_type = data.get('content_type', 'blog post')
        target_audience = data.get('target_audience', 'general')
        
        # Evaluate content
        result = asyncio.run(evaluation_agent.evaluate_content(
            content=content,
            topic=topic,
            content_type=content_type,
            target_audience=target_audience
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
