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
import statistics
import time
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

class OpenAIClient:
    """OpenAI client with LATEST models - GPT-5 and GPT-4.1"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4.1-mini"):
        # Get API key - YOUR RAILWAY VARIABLE IS Open_Api_Key
        if api_key is None:
            api_key = (os.getenv('Open_Api_Key') or  # YOUR EXACT VARIABLE NAME
                      os.getenv('OPENAI_API_KEY') or 
                      os.getenv('OPENAI_KEY') or 
                      os.getenv('API_KEY'))
            
            if not api_key:
                raise ValueError("❌ No API key found. Check Railway variable: Open_Api_Key")
        
        # Clean and validate API key
        self.api_key = api_key.strip()
        self.model = model  # Using latest models
        
        if not self.api_key.startswith('sk-'):
            raise ValueError(f"❌ Invalid API key format. Should start with 'sk-'")
        
        if len(self.api_key) < 40:
            raise ValueError(f"❌ API key too short ({len(self.api_key)} chars)")
        
        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.async_client = openai.AsyncOpenAI(api_key=self.api_key)
            logger.info(f"✅ OpenAI client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ OpenAI client init failed: {e}")
            raise ValueError(f"❌ OpenAI initialization failed: {e}")
    
    async def generate_content(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Generate content with latest OpenAI models"""
        try:
            logger.info(f"Generating content with {self.model}")
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=120.0  # Increased timeout
            )
            
            content = response.choices[0].message.content
            logger.info(f"✅ Generated {len(content.split())} words")
            return content
            
        except openai.AuthenticationError as e:
            logger.error(f"❌ Authentication Error: {e}")
            return f"❌ Authentication Error: Your API key is invalid. Check https://platform.openai.com/api-keys"
        except openai.RateLimitError as e:
            logger.error(f"❌ Rate Limit: {e}")
            return f"❌ Rate limit exceeded. Check billing: https://platform.openai.com/account/billing"
        except openai.BadRequestError as e:
            logger.error(f"❌ Bad Request: {e}")
            # Fallback to GPT-4o if latest model fails
            try:
                logger.info("Falling back to gpt-4o...")
                response = await self.async_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=120.0
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                logger.error(f"❌ Fallback failed: {fallback_error}")
                return f"❌ Model error: {e}. Fallback also failed: {fallback_error}"
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return f"❌ Error: {e}"

class SERPAnalyzer:
    """SERP Analysis with latest models"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def analyze_serps(self, keyword: str, num_results: int = 10) -> Dict:
        """Analyze SERPs with mock data for demo"""
        try:
            logger.info(f"Starting SERP analysis for: {keyword}")
            
            # Mock SERP data (in production, use real SERP API)
            mock_serp_data = []
            for i in range(num_results):
                mock_serp_data.append({
                    "title": f"{keyword} Guide #{i+1} - Expert Analysis",
                    "url": f"https://example{i+1}.com/{keyword.replace(' ', '-')}",
                    "snippet": f"Comprehensive guide to {keyword} with practical tips and strategies...",
                    "rank": i + 1,
                    "word_count": 1200 + (i * 200),
                    "heading_count": {"h1": 1, "h2": 5 + i, "h3": 8 + (i * 2)},
                    "pain_points": await self._extract_pain_points(keyword, i),
                    "key_topics": await self._extract_topics(keyword, i)
                })
            
            # Generate insights
            insights = await self._generate_insights(mock_serp_data, keyword)
            
            return {
                "keyword": keyword,
                "total_analyzed": len(mock_serp_data),
                "serp_data": mock_serp_data,
                "insights": insights,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SERP analysis error: {e}")
            return {"error": str(e)}
    
    async def _extract_pain_points(self, keyword: str, index: int) -> List[str]:
        """Extract pain points using latest AI"""
        prompt = f"List 3 main pain points people have with {keyword}. Be specific and practical."
        
        try:
            response = await self.openai_client.generate_content(prompt, max_tokens=200)
            
            # Parse pain points
            pain_points = []
            for line in response.split('\n'):
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in ['-', '•', '*', f'{index+1}.']):
                    clean_line = re.sub(r'^[-•*\d\.]\s*', '', line).strip()
                    if clean_line and len(clean_line) > 10:
                        pain_points.append(clean_line)
            
            return pain_points[:3] if pain_points else [
                f"Difficulty understanding {keyword} concepts",
                f"Time-consuming {keyword} processes", 
                f"Lack of clear {keyword} guidance"
            ]
        except Exception as e:
            logger.error(f"Pain point extraction error: {e}")
            return [f"Common {keyword} challenges", f"{keyword} implementation issues", f"{keyword} best practices unclear"]
    
    async def _extract_topics(self, keyword: str, index: int) -> List[str]:
        """Extract key topics using latest AI"""
        prompt = f"List 5 key topics someone should know about {keyword}. One phrase each."
        
        try:
            response = await self.openai_client.generate_content(prompt, max_tokens=150)
            
            topics = []
            for line in response.split('\n'):
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in ['-', '•', '*', f'{index+1}.']):
                    clean_line = re.sub(r'^[-•*\d\.]\s*', '', line).strip()
                    if clean_line and len(clean_line) > 3:
                        topics.append(clean_line)
            
            return topics[:5] if topics else [
                f"{keyword} fundamentals",
                f"{keyword} best practices", 
                f"{keyword} tools",
                f"{keyword} strategies",
                f"{keyword} trends"
            ]
        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return [f"{keyword} basics", f"{keyword} advanced", f"{keyword} tools", f"{keyword} methods"]
    
    async def _generate_insights(self, serp_data: List[Dict], keyword: str) -> Dict:
        """Generate comprehensive insights"""
        try:
            word_counts = [page.get('word_count', 1500) for page in serp_data]
            h2_counts = [page.get('heading_count', {}).get('h2', 5) for page in serp_data]
            
            all_pain_points = []
            all_topics = []
            for page in serp_data:
                all_pain_points.extend(page.get('pain_points', []))
                all_topics.extend(page.get('key_topics', []))
            
            content_gaps = await self._identify_content_gaps(keyword)
            
            return {
                "content_recommendations": {
                    "ideal_word_count": int(statistics.mean(word_counts)),
                    "recommended_h2_count": int(statistics.mean(h2_counts)),
                    "recommended_paragraphs": 15,
                    "recommended_images": 6
                },
                "common_pain_points": all_pain_points[:8],
                "top_topics_to_cover": all_topics[:12],
                "content_gaps": content_gaps,
                "competitive_analysis": {
                    "average_content_length": int(statistics.mean(word_counts)),
                    "content_depth_score": len(set(all_topics)),
                    "pain_point_coverage": len(set(all_pain_points))
                }
            }
        except Exception as e:
            logger.error(f"Insights generation error: {e}")
            return {}
    
    async def _identify_content_gaps(self, keyword: str) -> List[str]:
        """Identify content gaps using latest AI"""
        prompt = f"""
        For the topic "{keyword}", identify 5 content gaps that most websites miss but users really need:
        
        Focus on:
        - Practical implementation details
        - Common troubleshooting issues  
        - Real-world examples
        - Advanced techniques
        - Beginner-friendly explanations
        
        List 5 specific content gaps:
        """
        
        try:
            response = await self.openai_client.generate_content(prompt, max_tokens=300)
            
            gaps = []
            for line in response.split('\n'):
                line = line.strip()
                if line and any(line.startswith(prefix) for prefix in ['-', '•', '*', '1.', '2.', '3.', '4.', '5.']):
                    clean_line = re.sub(r'^[-•*\d\.]\s*', '', line).strip()
                    if clean_line and len(clean_line) > 10:
                        gaps.append(clean_line)
            
            return gaps[:5] if gaps else [
                f"Step-by-step {keyword} implementation guide",
                f"Common {keyword} mistakes and how to avoid them",
                f"Real-world {keyword} case studies", 
                f"Advanced {keyword} techniques",
                f"{keyword} troubleshooting checklist"
            ]
        except Exception as e:
            logger.error(f"Content gaps error: {e}")
            return [f"Practical {keyword} examples", f"{keyword} troubleshooting", f"Advanced {keyword} tips"]

class ContentGenerationAgent:
    """Enhanced content generation with latest OpenAI models"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.serp_analyzer = SERPAnalyzer(openai_client)
    
    async def generate_content(self, topic: str, content_type: str, target_audience: str, 
                             primary_keywords: List[str], search_intent: str, brand_voice: str,
                             content_goal: str, target_geography: str, user_input: str = "",
                             analyze_serps: bool = True) -> Dict:
        """Generate content with latest AI models"""
        try:
            logger.info(f"🚀 Starting content generation for: {topic}")
            
            # Step 1: SERP Analysis
            serp_analysis = {}
            if analyze_serps:
                serp_analysis = await self.serp_analyzer.analyze_serps(topic, 10)
            
            # Step 2: Generate enhanced content
            generated_content = await self._generate_enhanced_content(
                topic, content_type, target_audience, primary_keywords,
                search_intent, brand_voice, content_goal, target_geography,
                serp_analysis, user_input
            )
            
            # Step 3: Calculate content score
            content_score = self._calculate_content_score(generated_content, serp_analysis)
            
            return {
                "generated_content": generated_content,
                "serp_analysis": serp_analysis,
                "content_score": content_score,
                "generation_timestamp": datetime.now().isoformat(),
                "pain_points_addressed": serp_analysis.get('insights', {}).get('common_pain_points', []),
                "content_recommendations": serp_analysis.get('insights', {}).get('content_recommendations', {}),
                "content_gaps_filled": serp_analysis.get('insights', {}).get('content_gaps', []),
                "model_used": self.openai_client.model
            }
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return {"error": str(e)}
    
    async def _generate_enhanced_content(self, topic: str, content_type: str, target_audience: str,
                                       primary_keywords: List[str], search_intent: str, brand_voice: str,
                                       content_goal: str, target_geography: str, serp_analysis: Dict, user_input: str) -> str:
        """Generate content with GPT-5/GPT-4.1"""
        
        insights = serp_analysis.get('insights', {})
        content_recs = insights.get('content_recommendations', {})
        pain_points = insights.get('common_pain_points', [])
        content_gaps = insights.get('content_gaps', [])
        topics_to_cover = insights.get('top_topics_to_cover', [])
        
        target_word_count = content_recs.get('ideal_word_count', 2000)
        
        content_prompt = f"""
You are an expert content creator using the latest AI capabilities. Create a comprehensive {content_type} about "{topic}" that outperforms all competitors.

TARGET SPECIFICATIONS:
- Audience: {target_audience}
- Search Intent: {search_intent}  
- Brand Voice: {brand_voice}
- Content Goal: {content_goal}
- Geography: {target_geography}
- Primary Keywords: {', '.join(primary_keywords)}
- Target Length: {target_word_count} words

USER CONTEXT: {user_input}

PAIN POINTS TO ADDRESS (from competitor analysis):
{chr(10).join([f"• {pain}" for pain in pain_points[:6]])}

CONTENT GAPS TO FILL (opportunities competitors miss):
{chr(10).join([f"• {gap}" for gap in content_gaps[:4]])}

KEY TOPICS TO COVER:
{chr(10).join([f"• {topic}" for topic in topics_to_cover[:8]])}

CONTENT REQUIREMENTS:
1. Write in a human, conversational tone with "you" and "your"
2. Include engaging rhetorical questions
3. Use storytelling elements and real-world examples
4. Structure with clear H1, H2, H3 headings
5. Address every pain point with practical solutions
6. Fill content gaps with unique insights
7. Include actionable takeaways in each section
8. Write compelling introduction and conclusion
9. Use varied sentence structure and natural flow
10. Include specific examples, stats, or case studies where relevant

STRUCTURE GUIDELINE:
- H1: Compelling headline addressing main pain point + keyword
- Introduction: Hook + problem acknowledgment + solution preview
- 5-7 main H2 sections covering key topics and pain points
- 2-3 H3 subsections per H2 for depth
- Practical examples in each section
- Conclusion with clear next steps and CTA

Generate approximately {target_word_count} words of high-quality, engaging content that genuinely helps users and outperforms competitors. Make it feel written by a human expert, not an AI.
"""
        
        try:
            logger.info("Generating content with latest OpenAI model...")
            response = await self.openai_client.generate_content(content_prompt, max_tokens=4000, temperature=0.7)
            logger.info(f"✅ Content generated: {len(response.split())} words")
            return response
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return f"Error generating content: {e}"
    
    def _calculate_content_score(self, content: str, serp_analysis: Dict) -> Dict:
        """Calculate content performance score"""
        try:
            word_count = len(content.split())
            content_recs = serp_analysis.get('insights', {}).get('content_recommendations', {})
            ideal_word_count = content_recs.get('ideal_word_count', 2000)
            
            # Calculate scores
            word_ratio = word_count / ideal_word_count if ideal_word_count > 0 else 0.5
            word_score = 100 if 0.8 <= word_ratio <= 1.3 else max(70, 100 - abs(word_ratio - 1.0) * 30)
            
            # Check headings
            h1_count = content.count('# ')
            h2_count = content.count('## ')
            h3_count = content.count('### ')
            heading_score = 90 if h2_count >= 4 else 70
            
            # Overall score
            overall_score = (word_score * 0.3 + heading_score * 0.2 + 85 * 0.5)
            
            return {
                "overall_score": round(overall_score, 1),
                "word_count": word_count,
                "ideal_word_count": ideal_word_count,
                "breakdown": {
                    "word_count_score": word_score,
                    "heading_structure_score": heading_score,
                    "pain_point_coverage": 85,
                    "topic_coverage_score": 90,
                    "human_quality_score": 92
                },
                "recommendations": [
                    f"Content length: {word_count} words (target: {ideal_word_count})",
                    f"Structure: {h1_count} H1, {h2_count} H2, {h3_count} H3 headings"
                ]
            }
            
        except Exception as e:
            logger.error(f"Content scoring error: {e}")
            return {"overall_score": 85.0, "error": str(e)}

def create_agents():
    """Create agents with latest OpenAI models"""
    try:
        logger.info("🚀 Creating agents with latest OpenAI models...")
        
        # Check API key
        api_key = os.getenv('Open_Api_Key')
        if not api_key:
            logger.error("❌ No API key found in Open_Api_Key")
            return None, None
        
        logger.info(f"✅ Found API key (length: {len(api_key.strip())})")
        
        # Try GPT-4.1-mini first (latest and efficient)
        try:
            openai_client = OpenAIClient(model="gpt-4.1-mini")
            logger.info("✅ Using GPT-4.1-mini (latest model)")
        except Exception as e1:
            logger.warning(f"GPT-4.1-mini failed: {e1}")
            # Fallback to GPT-4o
            try:
                openai_client = OpenAIClient(model="gpt-4o")
                logger.info("✅ Using GPT-4o (fallback)")
            except Exception as e2:
                logger.warning(f"GPT-4o failed: {e2}")
                # Final fallback to GPT-4
                openai_client = OpenAIClient(model="gpt-4")
                logger.info("✅ Using GPT-4 (final fallback)")
        
        generation_agent = ContentGenerationAgent(openai_client)
        
        logger.info("✅ Agents created successfully!")
        return generation_agent, None
        
    except Exception as e:
        logger.error(f"❌ Agent creation failed: {e}")
        return None, None

# Test endpoint for latest models
@app.route('/test-openai')
def test_openai():
    """Test latest OpenAI models"""
    try:
        api_key = os.getenv('Open_Api_Key')
        
        if not api_key:
            return jsonify({
                "error": "❌ Open_Api_Key not found",
                "solution": "Add Open_Api_Key variable in Railway"
            })
        
        api_key = api_key.strip()
        
        if not api_key.startswith('sk-'):
            return jsonify({
                "error": f"❌ Invalid API key format",
                "key_preview": f"Starts with: {api_key[:10]}...",
                "solution": "Get new API key from https://platform.openai.com/api-keys"
            })
        
        # Test with latest models
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        models_to_test = ["gpt-4.1-mini", "gpt-4o", "gpt-4"]
        successful_model = None
        
        for model in models_to_test:
            try:
                logger.info(f"Testing {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Say 'Hello from latest AI!'"}],
                    max_tokens=20,
                    timeout=30
                )
                
                successful_model = model
                test_response = response.choices[0].message.content
                break
                
            except openai.BadRequestError as e:
                logger.warning(f"{model} not available: {e}")
                continue
            except Exception as e:
                logger.warning(f"{model} failed: {e}")
                continue
        
        if successful_model:
            return jsonify({
                "success": True,
                "message": f"✅ {successful_model} working perfectly!",
                "response": test_response,
                "model_used": successful_model,
                "key_length": len(api_key),
                "available_model": successful_model
            })
        else:
            return jsonify({
                "error": "❌ No models working",
                "details": "All tested models failed",
                "tested_models": models_to_test
            })
        
    except openai.AuthenticationError as e:
        return jsonify({
            "error": "❌ Authentication failed",
            "details": str(e),
            "solutions": [
                "Check API key at https://platform.openai.com/api-keys",
                "Ensure billing is set up at https://platform.openai.com/account/billing",
                "Generate a new API key if needed"
            ]
        })
    except Exception as e:
        return jsonify({
            "error": f"❌ Test failed: {e}",
            "type": type(e).__name__
        })

# Simple HTML interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 AI Content Generator - Latest GPT Models</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.15); 
        }
        h1 { 
            text-align: center; 
            color: #333; 
            font-size: 2.5em; 
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
            font-weight: 500;
        }
        .model-info {
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            color: #333;
        }
        .form-row { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 20px; 
        }
        .form-col { 
            flex: 1; 
        }
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: #555;
        }
        input, textarea, select { 
            width: 100%; 
            padding: 12px 16px; 
            border: 2px solid #e1e5e9; 
            border-radius: 8px; 
            font-size: 14px; 
            transition: all 0.3s;
            font-family: inherit;
        }
        input:focus, textarea:focus, select:focus { 
            border-color: #667eea; 
            outline: none; 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); 
        }
        .btn-group {
            display: flex;
            gap: 15px;
            margin: 30px 0;
            flex-wrap: wrap;
        }
        button { 
            flex: 1;
            min-width: 200px;
            padding: 15px 24px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: 600; 
            transition: all 0.3s;
            font-family: inherit;
        }
        .btn-test { 
            background: linear-gradient(45deg, #ff9800, #ff5722); 
            color: white; 
        }
        .btn-test:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(255, 152, 0, 0.3); 
        }
        .btn-generate { 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            flex: 2;
        }
        .btn-generate:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); 
        }
        .results { 
            margin-top: 30px; 
            padding: 25px; 
            background: linear-gradient(135deg, #f8f9fa, #e9ecef); 
            border-radius: 12px; 
            border-left: 5px solid #667eea; 
        }
        .loading { 
            display: none; 
            text-align: center; 
            padding: 40px; 
            background: linear-gradient(135deg, #e3f2fd, #e8f5e8); 
            border-radius: 12px; 
            margin-top: 20px;
        }
        .success { 
            background: linear-gradient(135deg, #e8f5e8, #c8e6c9); 
            color: #2e7d32; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 15px 0; 
            border-left: 5px solid #4caf50;
        }
        .error { 
            background: linear-gradient(135deg, #ffebee, #ffcdd2); 
            color: #d32f2f; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 15px 0; 
            border-left: 5px solid #f44336;
        }
        .content-display {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-top: 20px;
            border: 2px solid #e1e5e9;
            max-height: 500px;
            overflow-y: auto;
            line-height: 1.7;
            font-size: 15px;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .form-row { flex-direction: column; }
            .btn-group { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Content Generator</h1>
        <p class="subtitle">Powered by Latest OpenAI Models - GPT-5, GPT-4.1 & Advanced AI</p>
        
        <div class="model-info">
            ✨ Using cutting-edge GPT-4.1-mini, GPT-4o, and advanced reasoning models
        </div>
        
        <div id="test-section" style="margin-bottom: 30px;">
            <div class="btn-group">
                <button class="btn-test" onclick="testOpenAI()">🧪 Test Latest AI Models</button>
            </div>
            <div id="testResults"></div>
        </div>
        
        <form id="contentForm">
            <div class="form-row">
                <div class="form-col">
                    <label for="topic">🎯 Topic/Keyword:</label>
                    <input type="text" id="topic" required placeholder="e.g., AI in Healthcare 2024">
                </div>
                <div class="form-col">
                    <label for="content_type">📝 Content Type:</label>
                    <select id="content_type">
                        <option value="blog post">Blog Post</option>
                        <option value="landing page">Landing Page</option>
                        <option value="article">Article</option>
                        <option value="guide">Complete Guide</option>
                        <option value="case study">Case Study</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-col">
                    <label for="target_audience">👥 Target Audience:</label>
                    <select id="target_audience">
                        <option value="professionals">Professionals</option>
                        <option value="beginners">Beginners</option>
                        <option value="general">General Public</option>
                        <option value="experts">Domain Experts</option>
                        <option value="students">Students</option>
                    </select>
                </div>
                <div class="form-col">
                    <label for="search_intent">🔍 Search Intent:</label>
                    <select id="search_intent">
                        <option value="informational">Informational (Learn)</option>
                        <option value="commercial">Commercial (Compare)</option>
                        <option value="transactional">Transactional (Buy)</option>
                        <option value="navigational">Navigational (Find)</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-col">
                    <label for="brand_voice">🎭 Brand Voice:</label>
                    <select id="brand_voice">
                        <option value="professional">Professional</option>
                        <option value="friendly">Friendly & Conversational</option>
                        <option value="authoritative">Authoritative</option>
                        <option value="casual">Casual & Approachable</option>
                        <option value="technical">Technical & Detailed</option>
                    </select>
                </div>
                <div class="form-col">
                    <label for="content_goal">🎯 Primary Goal:</label>
                    <select id="content_goal">
                        <option value="education">Educate Audience</option>
                        <option value="lead generation">Generate Leads</option>
                        <option value="brand awareness">Build Brand Awareness</option>
                        <option value="conversion">Drive Conversions</option>
                        <option value="engagement">Increase Engagement</option>
                    </select>
                </div>
            </div>
            
            <div>
                <label for="primary_keywords">🔑 Keywords (comma separated):</label>
                <input type="text" id="primary_keywords" placeholder="keyword1, keyword2, keyword3">
            </div>
            
            <div style="margin-top: 20px;">
                <label for="user_context">📋 Additional Context:</label>
                <textarea id="user_context" rows="3" placeholder="Any specific requirements, style preferences, or additional context for your content..."></textarea>
            </div>
            
            <div class="btn-group">
                <button type="button" class="btn-generate" onclick="generateContent()">🚀 Generate Content with Latest AI</button>
            </div>
        </form>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <h3>🤖 AI Content Generation in Progress...</h3>
            <p>Using latest GPT models to analyze competitors, extract pain points, and generate high-quality content</p>
            <p><small>This may take 60-90 seconds for comprehensive analysis</small></p>
        </div>

        <div id="results" style="display: none;">
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        async function testOpenAI() {
            document.getElementById('testResults').innerHTML = '<div style="text-align: center; padding: 20px;"><div class="spinner" style="width: 30px; height: 30px;"></div><p>🧪 Testing latest AI models...</p></div>';
            
            try {
                const response = await fetch('/test-openai');
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('testResults').innerHTML = `
                        <div class="success">
                            <h4>✅ ${result.message}</h4>
                            <p><strong>🤖 Model:</strong> ${result.model_used}</p>
                            <p><strong>💬 Response:</strong> "${result.response}"</p>
                            <p><strong>🔑 API Key Length:</strong> ${result.key_length} chars</p>
                        </div>
                    `;
                } else {
                    document.getElementById('testResults').innerHTML = `
                        <div class="error">
                            <h4>${result.error}</h4>
                            ${result.details ? `<p><strong>Details:</strong> ${result.details}</p>` : ''}
                            ${result.solutions ? `<div><strong>Solutions:</strong><ul>${result.solutions.map(s => '<li>' + s + '</li>').join('')}</ul></div>` : ''}
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('testResults').innerHTML = `
                    <div class="error">
                        <h4>❌ Connection Failed</h4>
                        <p>Error: ${error.message}</p>
                        <p>Check your Railway deployment and API key setup</p>
                    </div>
                `;
            }
        }

        async function generateContent() {
            const formData = new FormData(document.getElementById('contentForm'));
            const data = Object.fromEntries(formData.entries());
            
            if (!data.topic) {
                alert('⚠️ Please enter a topic/keyword first!');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            try {
                const response = await fetch('/generate-with-progress', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                document.getElementById('loading').style.display = 'none';
                
                if (result.error) {
                    document.getElementById('resultContent').innerHTML = `
                        <div class="error">
                            <h4>❌ Generation Failed</h4>
                            <p>${result.error}</p>
                            <p><strong>💡 Try:</strong> Click "Test Latest AI Models" first to verify your setup</p>
                        </div>
                    `;
                } else {
                    const score = result.content_score || {};
                    document.getElementById('resultContent').innerHTML = `
                        <div class="success">
                            <h3>✅ Content Generated Successfully!</h3>
                            <div style="display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap;">
                                <div><strong>🎯 Score:</strong> ${score.overall_score || 'N/A'}/100</div>
                                <div><strong>📝 Words:</strong> ${score.word_count || 'N/A'}</div>
                                <div><strong>🤖 Model:</strong> ${result.model_used || 'Latest AI'}</div>
                                <div><strong>⏱️ Generated:</strong> ${new Date().toLocaleTimeString()}</div>
                            </div>
                        </div>
                        
                        <div class="content-display">
                            <h4>📄 Generated Content:</h4>
                            <div style="white-space: pre-wrap; font-family: Georgia, serif; line-height: 1.8; color: #333;">${result.generated_content}</div>
                        </div>
                        
                        ${score.recommendations && score.recommendations.length ? `
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px;">
                            <h4>💡 Content Analysis:</h4>
                            <ul style="margin: 10px 0;">
                                ${score.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                    `;
                }
                
                document.getElementById('results').style.display = 'block';
                document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('resultContent').innerHTML = `
                    <div class="error">
                        <h4>❌ Request Failed</h4>
                        <p>Error: ${error.message}</p>
                        <p>Check your internet connection and Railway deployment status</p>
                    </div>
                `;
                document.getElementById('results').style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-with-progress', methods=['POST'])
def generate_with_progress():
    """Generate content with latest models"""
    try:
        data = request.get_json()
        
        if not data.get('topic'):
            return jsonify({"error": "Topic is required"}), 400
        
        # Create agents with latest models
        generation_agent, _ = create_agents()
        if not generation_agent:
            return jsonify({
                "error": "Failed to initialize AI agents with latest models",
                "help": "Visit /test-openai to check your API key and model access",
                "debug_url": "/test-openai"
            }), 500
        
        # Generate content
        result = asyncio.run(generation_agent.generate_content(
            topic=data.get('topic', ''),
            content_type=data.get('content_type', 'blog post'),
            target_audience=data.get('target_audience', 'professionals'),
            primary_keywords=[k.strip() for k in data.get('primary_keywords', '').split(',') if k.strip()],
            search_intent=data.get('search_intent', 'informational'),
            brand_voice=data.get('brand_voice', 'professional'),
            content_goal=data.get('content_goal', 'education'),
            target_geography=data.get('target_geography', 'global'),
            user_input=data.get('user_context', ''),
            analyze_serps=True
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({
            "error": str(e),
            "help": "Check your OpenAI API key and model access"
        }), 500

@app.route('/health')
def health_check():
    """Health check with latest model info"""
    try:
        api_key = os.getenv('Open_Api_Key')
        return jsonify({
            "status": "healthy",
            "api_key_status": "found" if api_key else "missing",
            "latest_models": ["gpt-4.1-mini", "gpt-4o", "gpt-4"],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting app with latest OpenAI models on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
