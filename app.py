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
        # Get API key from Railway environment variable if not provided
        if api_key is None:
            api_key = os.getenv('Open_Api_Key')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set Open_Api_Key environment variable.")
        
        # Initialize the new OpenAI client
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
    
    def generate_content_sync(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Synchronous version using the new OpenAI API format"""
        try:
            response = self.client.chat.completions.create(
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

class ContentEvaluationAgent:
    """GPT-4 Enhanced Content Evaluation Agent"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def evaluate_content(self, content: str, topic: str, content_type: str, target_audience: str) -> Dict:
        """Comprehensive content evaluation using GPT-4"""
        try:
            logger.info(f"Starting GPT-4 evaluation for: {topic}")
            
            # Parallel evaluation tasks
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
            
            # Calculate overall score
            evaluation_report["overall_score"] = self._calculate_overall_score(evaluation_report)
            
            # Generate recommendations
            evaluation_report["recommendations"] = await self._generate_recommendations(evaluation_report, content, topic)
            
            logger.info(f"GPT-4 evaluation completed. Score: {evaluation_report['overall_score']}")
            return evaluation_report
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {"error": str(e), "overall_score": 8.0}
    
    async def _evaluate_eeat(self, content: str, topic: str, target_audience: str) -> Dict:
        """Evaluate E-E-A-T factors using GPT-4"""
        
        eeat_prompt = f"""
        Using GPT-4's advanced reasoning, evaluate this content for Google's E-E-A-T factors:

        CONTENT: {content[:2000]}...
        TOPIC: {topic}
        AUDIENCE: {target_audience}

        Rate each factor (1-10) with reasoning:

        EXPERIENCE (First-hand knowledge demonstrated):
        - Personal anecdotes or case studies present?
        - Practical examples from real usage?
        - Behind-the-scenes insights shown?

        EXPERTISE (Deep knowledge demonstrated):
        - Technical accuracy and depth?
        - Industry-specific knowledge?
        - Advanced concepts explained clearly?

        AUTHORITATIVENESS (Authority established):
        - Author credentials mentioned or implied?
        - Quality sources referenced?
        - Industry recognition shown?

        TRUSTWORTHINESS (Trust signals present):
        - Transparent sourcing?
        - Balanced perspective?
        - Honest communication?

        Provide scores (1-10) for each factor.
        """
        
        try:
            response = await self.openai_client.generate_content(eeat_prompt, max_tokens=800)
            return self._parse_eeat_response(response)
        except Exception as e:
            logger.error(f"E-E-A-T evaluation error: {e}")
            return {"experience": 8, "expertise": 8, "authoritativeness": 8, "trustworthiness": 8}
    
    async def _evaluate_content_quality(self, content: str, topic: str, content_type: str) -> Dict:
        """Evaluate content quality using GPT-4"""
        
        quality_prompt = f"""
        Using GPT-4 reasoning, evaluate this {content_type} about "{topic}" for quality:

        CONTENT: {content[:2000]}...

        Rate each factor (1-10):

        ORIGINALITY:
        - Unique insights or perspective?
        - Novel angle on the topic?
        - Avoids generic information?

        COMPREHENSIVENESS:
        - Complete topic coverage?
        - Multiple angles addressed?
        - Actionable information provided?

        USER VALUE:
        - Solves real problems?
        - Provides actionable advice?
        - Clear takeaways present?

        READABILITY:
        - Clear structure with headings?
        - Appropriate language level?
        - Logical flow and transitions?

        Provide scores (1-10) for each factor.
        """
        
        try:
            response = await self.openai_client.generate_content(quality_prompt, max_tokens=800)
            return self._parse_quality_response(response)
        except Exception as e:
            logger.error(f"Quality evaluation error: {e}")
            return {"originality": 8, "comprehensiveness": 8, "user_value": 8, "readability": 8}
    
    async def _evaluate_seo_factors(self, content: str, topic: str) -> Dict:
        """Evaluate SEO factors using GPT-4"""
        
        seo_prompt = f"""
        Use GPT-4 to analyze this content for SEO quality:

        TOPIC: {topic}
        CONTENT: {content[:2000]}...

        Rate these SEO factors (1-10):

        SEARCH INTENT ALIGNMENT:
        - Matches what users search for?
        - Answers user questions?
        - Covers related topics?

        CONTENT STRUCTURE:
        - Proper heading hierarchy?
        - Scannable format?
        - Logical organization?

        KEYWORD OPTIMIZATION:
        - Natural keyword usage?
        - Semantic relevance?
        - Long-tail coverage?

        Provide scores (1-10) for each factor.
        """
        
        try:
            response = await self.openai_client.generate_content(seo_prompt, max_tokens=600)
            return self._parse_seo_response(response)
        except Exception as e:
            logger.error(f"SEO evaluation error: {e}")
            return {"search_intent": 8, "content_structure": 8, "keyword_optimization": 8}
    
    async def _analyze_entities_and_clusters(self, content: str, topic: str) -> Dict:
        """Analyze entities and content clusters using GPT-4"""
        
        entity_prompt = f"""
        Use GPT-4 to analyze entities and content opportunities:

        TOPIC: {topic}
        CONTENT: {content[:2000]}...

        Identify:

        PRIMARY ENTITIES:
        - Main concepts, people, products mentioned
        - Key terms and important concepts
        - Technologies or methodologies discussed

        RELATED ENTITIES:
        - Connected concepts for separate content
        - Subtopics deserving dedicated pieces
        - Supporting concepts that enhance understanding

        CONTENT CLUSTERS:
        - What pillar topics could this support?
        - What cluster topics are missing?
        - How does this connect to other content?

        CLUSTER OPPORTUNITIES:
        - Specific content pieces to create
        - Content calendar suggestions
        - Linking strategy between pieces

        Provide structured analysis.
        """
        
        try:
            response = await self.openai_client.generate_content(entity_prompt, max_tokens=1000)
            return self._parse_entity_response(response)
        except Exception as e:
            logger.error(f"Entity analysis error: {e}")
            return {"primary_entities": [], "related_entities": [], "cluster_opportunities": []}
    
    async def _find_reddit_insights(self, topic: str) -> Dict:
        """Use GPT-4 to identify Reddit communities and pain points"""
        
        reddit_prompt = f"""
        Use GPT-4's knowledge to identify Reddit insights for "{topic}":

        RELEVANT SUBREDDITS:
        - Which subreddits discuss "{topic}" most actively?
        - What communities have quality discussions?
        - Any specialized communities relevant?

        COMMON PAIN POINTS:
        - What problems do people discuss about "{topic}"?
        - What challenges are frequently mentioned?
        - What solutions are people seeking?

        CONTENT OPPORTUNITIES:
        - What angles are underserved?
        - What problems need better content?
        - What questions come up repeatedly?

        DISCUSSION THEMES:
        - Common debate topics
        - Frequent challenges mentioned
        - Popular success stories

        Provide actionable insights.
        """
        
        try:
            response = await self.openai_client.generate_content(reddit_prompt, max_tokens=800)
            return self._parse_reddit_response(response)
        except Exception as e:
            logger.error(f"Reddit insights error: {e}")
            return {"subreddits": [], "pain_points": [], "content_opportunities": []}
    
    def _calculate_overall_score(self, evaluation: Dict) -> float:
        """Calculate weighted overall score"""
        try:
            scores = []
            weights = []
            
            # E-E-A-T scores (40% weight)
            eeat = evaluation.get("eeat_analysis", {})
            if eeat:
                eeat_score = (
                    eeat.get("experience", 8) * 0.25 +
                    eeat.get("expertise", 8) * 0.25 +
                    eeat.get("authoritativeness", 8) * 0.25 +
                    eeat.get("trustworthiness", 8) * 0.25
                )
                scores.append(eeat_score)
                weights.append(0.4)
            
            # Content quality (35% weight)
            quality = evaluation.get("content_quality", {})
            if quality:
                quality_score = (
                    quality.get("originality", 8) * 0.25 +
                    quality.get("comprehensiveness", 8) * 0.25 +
                    quality.get("user_value", 8) * 0.25 +
                    quality.get("readability", 8) * 0.25
                )
                scores.append(quality_score)
                weights.append(0.35)
            
            # SEO factors (25% weight)
            seo = evaluation.get("seo_analysis", {})
            if seo:
                seo_score = (
                    seo.get("search_intent", 8) * 0.4 +
                    seo.get("content_structure", 8) * 0.3 +
                    seo.get("keyword_optimization", 8) * 0.3
                )
                scores.append(seo_score)
                weights.append(0.25)
            
            if not scores:
                return 8.0
            
            # Calculate weighted average
            total_weight = sum(weights)
            if total_weight > 0:
                weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
                return round(weighted_score, 1)
            
            return 8.0
            
        except Exception as e:
            logger.error(f"Score calculation error: {e}")
            return 8.0
    
    async def _generate_recommendations(self, evaluation: Dict, content: str, topic: str) -> List[str]:
        """Generate recommendations using GPT-4"""
        
        recommendations_prompt = f"""
        Use GPT-4 to generate specific recommendations for this content:

        TOPIC: {topic}
        OVERALL SCORE: {evaluation.get('overall_score', 8)}

        EVALUATION RESULTS:
        - E-E-A-T: {evaluation.get('eeat_analysis', {})}
        - Quality: {evaluation.get('content_quality', {})}
        - SEO: {evaluation.get('seo_analysis', {})}

        Generate 8-10 specific, actionable recommendations to improve this content:

        Focus on:
        - Lowest-scoring areas first
        - Highest-impact improvements
        - Practical implementation
        - Both content and technical aspects

        Provide specific recommendations.
        """
        
        try:
            response = await self.openai_client.generate_content(recommendations_prompt, max_tokens=600)
            return self._parse_recommendations(response)
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            return ["Add more examples and case studies", "Improve heading structure", "Include more actionable advice"]
    
    def _parse_eeat_response(self, response: str) -> Dict:
        """Parse E-E-A-T scores from response"""
        try:
            scores = {}
            factors = ["experience", "expertise", "authoritativeness", "trustworthiness"]
            
            for factor in factors:
                patterns = [
                    rf"{factor}.*?(\d+(?:\.\d+)?)",
                    rf"{factor}.*?score.*?(\d+(?:\.\d+)?)",
                ]
                
                score_found = False
                for pattern in patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        score = float(match.group(1))
                        scores[factor] = max(1.0, min(10.0, score))
                        score_found = True
                        break
                
                if not score_found:
                    scores[factor] = 8.0
            
            return scores
        except Exception as e:
            logger.error(f"E-E-A-T parsing error: {e}")
            return {"experience": 8, "expertise": 8, "authoritativeness": 8, "trustworthiness": 8}
    
    def _parse_quality_response(self, response: str) -> Dict:
        """Parse quality scores from response"""
        try:
            scores = {}
            factors = ["originality", "comprehensiveness", "user_value", "readability"]
            
            for factor in factors:
                patterns = [
                    rf"{factor}.*?(\d+(?:\.\d+)?)",
                    rf"{factor}.*?score.*?(\d+(?:\.\d+)?)",
                ]
                
                score_found = False
                for pattern in patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        score = float(match.group(1))
                        scores[factor] = max(1.0, min(10.0, score))
                        score_found = True
                        break
                
                if not score_found:
                    scores[factor] = 8.0
            
            return scores
        except Exception as e:
            logger.error(f"Quality parsing error: {e}")
            return {"originality": 8, "comprehensiveness": 8, "user_value": 8, "readability": 8}
    
    def _parse_seo_response(self, response: str) -> Dict:
        """Parse SEO scores from response"""
        try:
            scores = {}
            factors = ["search_intent", "content_structure", "keyword_optimization"]
            
            for factor in factors:
                factor_clean = factor.replace('_', '[ _-]')
                patterns = [
                    rf"{factor_clean}.*?(\d+(?:\.\d+)?)",
                    rf"{factor_clean}.*?score.*?(\d+(?:\.\d+)?)",
                ]
                
                score_found = False
                for pattern in patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        score = float(match.group(1))
                        scores[factor] = max(1.0, min(10.0, score))
                        score_found = True
                        break
                
                if not score_found:
                    scores[factor] = 8.0
            
            return scores
        except Exception as e:
            logger.error(f"SEO parsing error: {e}")
            return {"search_intent": 8, "content_structure": 8, "keyword_optimization": 8}
    
    def _parse_entity_response(self, response: str) -> Dict:
        """Parse entity analysis from response"""
        try:
            return {
                "primary_entities": self._extract_list_from_response(response, "primary entities"),
                "related_entities": self._extract_list_from_response(response, "related entities"),
                "cluster_opportunities": self._extract_list_from_response(response, "cluster opportunities"),
                "content_calendar": self._extract_list_from_response(response, "content calendar")
            }
        except Exception as e:
            logger.error(f"Entity parsing error: {e}")
            return {"primary_entities": [], "related_entities": [], "cluster_opportunities": []}
    
    def _parse_reddit_response(self, response: str) -> Dict:
        """Parse Reddit insights from response"""
        try:
            return {
                "subreddits": self._extract_list_from_response(response, "subreddits"),
                "pain_points": self._extract_list_from_response(response, "pain points"),
                "content_opportunities": self._extract_list_from_response(response, "content opportunities"),
                "discussion_themes": self._extract_list_from_response(response, "discussion themes")
            }
        except Exception as e:
            logger.error(f"Reddit parsing error: {e}")
            return {"subreddits": [], "pain_points": [], "content_opportunities": []}
    
    def _parse_recommendations(self, response: str) -> List[str]:
        """Parse recommendations from response"""
        try:
            recommendations = []
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    recommendations.append(line)
                elif line.startswith(('-', '•', '*')):
                    recommendations.append(line[1:].strip())
                elif len(line) > 20 and any(word in line.lower() for word in ['add', 'include', 'improve', 'enhance', 'optimize']):
                    recommendations.append(line)
            
            cleaned_recommendations = []
            for rec in recommendations[:10]:
                if len(rec) > 10:
                    cleaned_recommendations.append(rec)
            
            return cleaned_recommendations if cleaned_recommendations else [
                "Add more specific examples and case studies",
                "Improve heading structure and readability", 
                "Include more actionable advice for readers"
            ]
        except Exception as e:
            logger.error(f"Recommendations parsing error: {e}")
            return ["Review content for improvement opportunities"]
    
    def _extract_list_from_response(self, response: str, section_name: str) -> List[str]:
        """Extract lists from response based on section name"""
        try:
            items = []
            lines = response.split('\n')
            in_section = False
            
            for line in lines:
                line = line.strip()
                if section_name.lower() in line.lower():
                    in_section = True
                    continue
                
                if in_section:
                    if line.startswith(('-', '•', '*')):
                        item = line[1:].strip()
                        if item:
                            items.append(item)
                    elif re.match(r'^\d+\.', line):
                        item = line.split('.', 1)[1].strip()
                        if item:
                            items.append(item)
                    elif line and line[0].isupper() and len(line) > 5:
                        if ':' in line and len(items) > 0:
                            break
                        items.append(line)
            
            return items[:15]  # Limit to 15 items
        except Exception as e:
            logger.error(f"List extraction error: {e}")
            return []

class KnowledgeGraphAgent:
    """Google Knowledge Graph integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://kgsearch.googleapis.com/v1/entities:search"
    
    async def get_entity_connections(self, entities: List[str]) -> Dict:
        """Get entity connections from Google Knowledge Graph"""
        if not self.api_key:
            return {
                "entity_connections": [],
                "related_topics": [],
                "error": "No Google Knowledge Graph API key provided"
            }
        
        try:
            all_entities = []
            for entity in entities[:3]:  # Limit to avoid rate limiting
                response = await self._search_entity(entity)
                if response.get('entities'):
                    all_entities.extend(response['entities'])
            
            return {
                "entity_connections": all_entities,
                "related_topics": self._extract_related_topics(all_entities)
            }
        except Exception as e:
            logger.error(f"Knowledge Graph error: {e}")
            return {"entity_connections": [], "error": str(e)}
    
    async def _search_entity(self, query: str) -> Dict:
        """Search for entity in Knowledge Graph"""
        if not self.api_key:
            return {"entities": []}
        
        try:
            params = {
                'query': query,
                'key': self.api_key,
                'limit': 3,
                'indent': True
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            entities = []
            
            for item in data.get('itemListElement', []):
                entity = item.get('result', {})
                entities.append({
                    'name': entity.get('name', ''),
                    'description': entity.get('description', ''),
                    'types': entity.get('@type', []),
                    'score': item.get('resultScore', 0)
                })
            
            return {"entities": entities}
        except Exception as e:
            logger.error(f"Entity search error: {e}")
            return {"entities": []}
    
    def _extract_related_topics(self, entities: List[Dict]) -> List[str]:
        """Extract related topics from entity data"""
        topics = set()
        for entity in entities:
            description = entity.get('description', '')
            if description:
                words = description.split()
                for word in words:
                    if len(word) > 4 and word.isalpha():
                        topics.add(word.title())
        
        return list(topics)[:15]

def create_evaluation_agent():
    """Create and return a ContentEvaluationAgent instance"""
    try:
        # Create OpenAI client - automatically uses Open_Api_Key from Railway
        openai_client = OpenAIClient(model="gpt-4")  # or "gpt-3.5-turbo" for lower cost
        
        # Create evaluation agent
        evaluation_agent = ContentEvaluationAgent(openai_client)
        
        return evaluation_agent
    except Exception as e:
        logger.error(f"Failed to create evaluation agent: {e}")
        return None

# HTML Template with Enhanced SEO Input Fields
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Content Evaluation Tool</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        .form-row { display: flex; gap: 15px; margin-bottom: 20px; }
        .form-col { flex: 1; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        textarea { height: 120px; resize: vertical; }
        #content { height: 200px; }
        button { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
        button:hover { background: #005a87; }
        .results { margin-top: 30px; padding: 20px; background: #f9f9f9; border-radius: 5px; }
        .score { font-size: 24px; font-weight: bold; color: #007cba; }
        .section { margin: 20px 0; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #007cba; }
        .loading { display: none; text-align: center; padding: 20px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #e7f3ff; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Advanced SEO Content Evaluation Tool</h1>
        
        <form id="evaluationForm">
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
                    <label for="secondary_keywords">Secondary Keywords (comma separated):</label>
                    <input type="text" id="secondary_keywords" name="secondary_keywords" placeholder="e.g., machine learning, digital health, patient care">
                </div>
            </div>

            <div class="form-row">
                <div class="form-col">
                    <label for="competitor_urls">Competitor URLs (one per line):</label>
                    <textarea id="competitor_urls" name="competitor_urls" placeholder="https://competitor1.com/article
https://competitor2.com/page"></textarea>
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
                    <label for="content_length">Target Content Length:</label>
                    <select id="content_length" name="content_length">
                        <option value="">Select Length</option>
                        <option value="short">Short (300-800 words)</option>
                        <option value="medium">Medium (800-1500 words)</option>
                        <option value="long">Long (1500-3000 words)</option>
                        <option value="comprehensive">Comprehensive (3000+ words)</option>
                    </select>
                </div>
            </div>

            <div class="form-group">
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

            <div class="form-group">
                <label for="content">Content to Evaluate:</label>
                <textarea id="content" name="content" required placeholder="Paste your content here for evaluation..."></textarea>
            </div>

            <button type="submit">🔍 Analyze Content</button>
        </form>

        <div class="loading" id="loading">
            <h3>⚡ Analyzing your content with AI...</h3>
            <p>This may take 30-60 seconds for comprehensive analysis.</p>
        </div>

        <div id="results" class="results" style="display: none;">
            <h2>📊 Evaluation Results</h2>
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
        document.getElementById('evaluationForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            try {
                const response = await fetch('/evaluate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                // Hide loading
                document.getElementById('loading').style.display = 'none';
                
                if (result.error) {
                    document.getElementById('resultsContent').innerHTML = `<div class="section"><h3>❌ Error</h3><p>${result.error}</p></div>`;
                } else {
                    displayResults(result);
                }
                
                document.getElementById('results').style.display = 'block';
                document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('resultsContent').innerHTML = `<div class="section"><h3>❌ Error</h3><p>Failed to analyze content: ${error.message}</p></div>`;
                document.getElementById('results').style.display = 'block';
            }
        });

        function displayResults(result) {
            const eeat = result.eeat_analysis || {};
            const quality = result.content_quality || {};
            const seo = result.seo_analysis || {};
            const recommendations = result.recommendations || [];
            const reddit = result.reddit_insights || {};

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

            if (reddit.subreddits && reddit.subreddits.length > 0) {
                html += `
                    <div class="section">
                        <h3>🌐 Reddit Insights</h3>
                        <p><strong>Relevant Subreddits:</strong> ${reddit.subreddits.join(', ')}</p>
                `;
                if (reddit.pain_points && reddit.pain_points.length > 0) {
                    html += `<p><strong>Pain Points:</strong> ${reddit.pain_points.join(', ')}</p>`;
                }
                html += '</div>';
            }

            document.getElementById('resultsContent').innerHTML = html;
        }
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    """Serve the main page with enhanced SEO input fields"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/evaluate', methods=['POST'])
async def evaluate_content():
    """Evaluate content with enhanced SEO parameters"""
    try:
        data = request.get_json()
        
        # Create agent
        evaluation_agent = create_evaluation_agent()
        if not evaluation_agent:
            return jsonify({"error": "Failed to initialize evaluation agent"}), 500
        
        # Extract all the enhanced SEO parameters
        content = data.get('content', '')
        topic = data.get('topic', '')
        content_type = data.get('content_type', 'blog post')
        target_audience = data.get('target_audience', 'general')
        search_intent = data.get('search_intent', '')
        primary_keywords = data.get('primary_keywords', '')
        secondary_keywords = data.get('secondary_keywords', '')
        competitor_urls = data.get('competitor_urls', '')
        target_geography = data.get('target_geography', 'global')
        content_goal = data.get('content_goal', '')
        content_length = data.get('content_length', '')
        brand_voice = data.get('brand_voice', '')
        
        # Enhanced evaluation with additional context
        enhanced_topic = f"{topic} (Intent: {search_intent}, Geography: {target_geography}, Goal: {content_goal})"
        enhanced_audience = f"{target_audience} seeking {search_intent} content with {brand_voice} tone"
        
        # Run evaluation
        result = await evaluation_agent.evaluate_content(
            content=content,
            topic=enhanced_topic,
            content_type=content_type,
            target_audience=enhanced_audience
        )
        
        # Add the additional context to the result
        result['seo_context'] = {
            'primary_keywords': primary_keywords.split(',') if primary_keywords else [],
            'secondary_keywords': secondary_keywords.split(',') if secondary_keywords else [],
            'search_intent': search_intent,
            'target_geography': target_geography,
            'content_goal': content_goal,
            'content_length': content_length,
            'brand_voice': brand_voice,
            'competitor_urls': competitor_urls.split('\n') if competitor_urls else []
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Main function for testing
async def main():
    """Test the evaluation agent"""
    evaluation_agent = create_evaluation_agent()
    if evaluation_agent:
        result = await evaluation_agent.evaluate_content(
            content="Artificial Intelligence is revolutionizing healthcare by enabling more accurate diagnoses, personalized treatment plans, and improved patient outcomes. Medical professionals are leveraging AI-powered tools to analyze medical images, predict disease progression, and optimize treatment protocols.",
            topic="AI in Healthcare 2024",
            content_type="blog post",
            target_audience="healthcare professionals"
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    # For Railway deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
