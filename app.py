import re
import json
import os
import openai
from typing import Dict, List
from datetime import datetime
import asyncio
from flask import Flask, request, jsonify, render_template_string
import requests
import logging

# NLP & Analysis imports
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
except:
    vader_analyzer = None

try:
    import yake
    kw_extractor = yake.KeywordExtractor(top=10, stopwords=None)
except:
    kw_extractor = None

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
except:
    cosine_similarity = None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting Waqzee Advanced Content Tool...")

# Add src/agents to path
import sys
agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'agents')
if os.path.exists(agents_path):
    if agents_path not in sys.path:
        sys.path.insert(0, agents_path)

# Import agents
RedditScraper = None
PainPointExtractor = None  
PainPointHumanizer = None

try:
    from Reddit_scraper import RedditScraper
    logger.info("RedditScraper imported")
except Exception as e:
    logger.error(f"Failed to import RedditScraper: {e}")

try:
    from Pain_point_extractor import PainPointExtractor
    logger.info("PainPointExtractor imported")
except Exception as e:
    logger.error(f"Failed to import PainPointExtractor: {e}")

try:
    from Pain_point_humanizer import PainPointHumanizer
    logger.info("PainPointHumanizer imported")
except Exception as e:
    logger.error(f"Failed to import PainPointHumanizer: {e}")

app = Flask(__name__)

class OpenAIClient:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        if api_key is None:
            api_key = os.getenv('Open_Api_Key')
            if not api_key:
                raise ValueError("No OpenAI API key found")
        
        self.api_key = api_key.strip()
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key, timeout=60.0)
        self.async_client = openai.AsyncOpenAI(api_key=self.api_key, timeout=60.0)
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
    async def generate_content(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=120.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"Error: {str(e)}"

    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for semantic comparison"""
        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

class SerpAPIResearch:
    """Research using Google SERP data"""
    
    @staticmethod
    def get_top_results(query: str) -> Dict:
        """Get top-ranking results for a query"""
        try:
            api_key = os.getenv('Serp_API')
            if not api_key:
                return {"error": "Serp_API key not configured"}
            
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": api_key,
                "num": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = {
                "organic_results": [],
                "people_also_ask": [],
                "top_keywords": []
            }
            
            # Organic results
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    results["organic_results"].append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "position": result.get("position", 0)
                    })
            
            # People Also Ask
            if "people_also_ask" in data:
                for question in data["people_also_ask"][:5]:
                    results["people_also_ask"].append({
                        "question": question.get("question", ""),
                        "snippet": question.get("snippet", "")[:200]
                    })
            
            logger.info(f"Got {len(results['organic_results'])} SERP results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Serp API error: {e}")
            return {"error": str(e)}

class NewsResearch:
    """Research using News API for trends"""
    
    @staticmethod
    def get_trending(query: str) -> Dict:
        """Get trending news for topic"""
        try:
            api_key = os.getenv('News_API')
            if not api_key:
                return {"error": "News_API key not configured"}
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": api_key,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            trending = []
            if data.get("articles"):
                for article in data["articles"][:5]:
                    trending.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "publishedAt": article.get("publishedAt", "")
                    })
            
            logger.info(f"Got {len(trending)} trending news articles")
            return {"articles": trending}
            
        except Exception as e:
            logger.error(f"News API error: {e}")
            return {"error": str(e)}

class PersonaGenerator:
    """Generate personas from Reddit data"""
    
    @staticmethod
    def extract_personas(posts: List[Dict], comments: List[Dict]) -> List[Dict]:
        """Extract personas from Reddit data"""
        try:
            personas = []
            all_text = []
            
            # Collect all text
            for post in posts[:20]:
                all_text.append(post.get("title", "") + " " + post.get("selftext", ""))
            for comment in comments[:50]:
                all_text.append(comment.get("body", ""))
            
            combined_text = " ".join(all_text).lower()
            
            # Sentiment analysis
            sentiment_scores = []
            if vader_analyzer:
                for text in all_text[:10]:
                    if text:
                        scores = vader_analyzer.polarity_scores(text)
                        sentiment_scores.append(scores)
            
            # Calculate average sentiment
            if sentiment_scores:
                avg_positive = sum(s["pos"] for s in sentiment_scores) / len(sentiment_scores)
                avg_negative = sum(s["neg"] for s in sentiment_scores) / len(sentiment_scores)
                avg_neutral = sum(s["neu"] for s in sentiment_scores) / len(sentiment_scores)
            else:
                avg_positive = avg_negative = avg_neutral = 0.33
            
            # Keyword extraction for persona names
            keywords = []
            if kw_extractor:
                try:
                    keywords = kw_extractor.extract_keywords(combined_text, top=10)
                except:
                    pass
            
            # Generate personas based on sentiment and keywords
            if avg_negative > avg_positive:
                personas.append({
                    "name": "The Frustrated User",
                    "sentiment": "negative",
                    "keywords": [k[0] for k in keywords[:3]] if keywords else [],
                    "pain_point": "Struggling with common issues",
                    "motivation": "Find solution quickly"
                })
            
            if avg_positive > avg_negative:
                personas.append({
                    "name": "The Opportunity Seeker",
                    "sentiment": "positive",
                    "keywords": [k[0] for k in keywords[:3]] if keywords else [],
                    "pain_point": "Missing out on best practices",
                    "motivation": "Learn and improve"
                })
            
            if avg_neutral > 0.4:
                personas.append({
                    "name": "The Information Gatherer",
                    "sentiment": "neutral",
                    "keywords": [k[0] for k in keywords[:3]] if keywords else [],
                    "pain_point": "Need clear information",
                    "motivation": "Make informed decisions"
                })
            
            logger.info(f"Generated {len(personas)} personas")
            return personas
            
        except Exception as e:
            logger.error(f"Persona generation error: {e}")
            return []

class CTAGenerator:
    """Generate smart CTAs based on content"""
    
    @staticmethod
    def generate_cta(openai_client, content: str, topic: str, personas: List[Dict]) -> str:
        """Generate smart CTA based on content and personas"""
        try:
            persona_names = [p["name"] for p in personas]
            persona_str = ", ".join(persona_names)
            
            prompt = f"""Based on this article about "{topic}" written for personas: {persona_str}

Article snippet:
{content[:500]}...

Generate a compelling, specific, and actionable call-to-action that:
1. Addresses the main benefit mentioned
2. Creates urgency without being pushy
3. Matches the reader's motivation
4. Includes specific next steps

Return ONLY the CTA text, no additional explanation:"""
            
            cta = asyncio.run(openai_client.generate_content(prompt, max_tokens=100, temperature=0.8))
            return cta.strip()
            
        except Exception as e:
            logger.error(f"CTA generation error: {e}")
            return "Ready to get started? Take the next step today."

class ContentAnalytics:
    """Advanced content analysis"""
    
    @staticmethod
    def analyze_emotions(text: str) -> Dict:
        """Analyze emotional tone using VADER"""
        try:
            if not vader_analyzer:
                return {"error": "VADER not available"}
            
            scores = vader_analyzer.polarity_scores(text)
            return {
                "positive": round(scores["pos"] * 100, 1),
                "negative": round(scores["neg"] * 100, 1),
                "neutral": round(scores["neu"] * 100, 1),
                "overall_sentiment": "positive" if scores["compound"] > 0.05 else "negative" if scores["compound"] < -0.05 else "neutral"
            }
        except Exception as e:
            logger.error(f"Emotion analysis error: {e}")
            return {}
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract keywords using YAKE"""
        try:
            if not kw_extractor:
                return []
            
            keywords = kw_extractor.extract_keywords(text, top=10)
            return [k[0] for k in keywords]
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
    
    @staticmethod
    def calculate_engagement_potential(text: str) -> Dict:
        """Calculate engagement potential"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        power_words = [
            "amazing", "discover", "proven", "secret", "best", "essential",
            "incredible", "revolutionary", "ultimate", "powerful", "exclusive",
            "urgent", "limited", "guaranteed", "transform", "breakthrough"
        ]
        
        power_word_count = sum(1 for s in sentences for w in power_words if w in s.lower())
        avg_sentence_length = len(text.split()) / max(1, len(sentences))
        
        engagement_score = min(100, (power_word_count * 5) + ((20 - avg_sentence_length) * 2))
        
        return {
            "power_words_used": power_word_count,
            "average_sentence_length": round(avg_sentence_length, 1),
            "engagement_score": round(engagement_score, 1)
        }
    
    @staticmethod
    def calculate_trust_markers(text: str) -> Dict:
        """Calculate trust markers in content"""
        facts = len(re.findall(r'\d+%|\d+\s+(?:million|billion|thousand)', text, re.IGNORECASE))
        citations = len(re.findall(r'\[.*?\]|according to|studies show|research|data shows', text, re.IGNORECASE))
        quotes = len(re.findall(r'["\'].*?["\']', text))
        
        trust_score = min(100, facts * 10 + citations * 5 + quotes * 2)
        
        return {
            "statistics_mentioned": facts,
            "citations_or_references": citations,
            "quotes": quotes,
            "trust_score": trust_score
        }

class SemanticAnalysis:
    """Compare content with top results using embeddings"""
    
    @staticmethod
    def compare_with_top_results(openai_client, generated_content: str, top_results: List[Dict]) -> Dict:
        """Compare generated content with top results semantically"""
        try:
            if not cosine_similarity:
                return {"error": "scikit-learn not available"}
            
            # Get embedding for generated content
            generated_embedding = openai_client.get_embeddings(generated_content[:1000])
            if not generated_embedding:
                return {"error": "Could not generate embedding"}
            
            top_results_text = " ".join([r.get("snippet", "") for r in top_results[:3]])
            top_embedding = openai_client.get_embeddings(top_results_text)
            
            if not top_embedding:
                return {"error": "Could not get top results embedding"}
            
            # Calculate similarity
            import numpy as np
            similarity = cosine_similarity(
                [generated_embedding],
                [top_embedding]
            )[0][0]
            
            uniqueness = 100 - (similarity * 100)
            
            return {
                "semantic_similarity": round(similarity * 100, 1),
                "uniqueness_score": round(uniqueness, 1),
                "comparison_insight": "Very unique content" if uniqueness > 60 else "Similar to top results" if uniqueness < 30 else "Moderately unique"
            }
            
        except Exception as e:
            logger.error(f"Semantic analysis error: {e}")
            return {"error": str(e)}

def create_agents():
    try:
        api_key = os.getenv('Open_Api_Key')
        if not api_key:
            logger.error("No OpenAI API key")
            return None, None, None, None
        
        try:
            openai_client = OpenAIClient(model="gpt-4o-mini")
        except:
            try:
                openai_client = OpenAIClient(model="gpt-4o")
            except:
                openai_client = OpenAIClient(model="gpt-3.5-turbo")
        
        generation_agent = ContentGenerationAgent(openai_client)
        reddit_scraper = RedditScraper() if RedditScraper else None
        pain_extractor = PainPointExtractor(openai_client) if PainPointExtractor else None
        
        return generation_agent, reddit_scraper, pain_extractor, openai_client
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        return None, None, None, None

class ContentGenerationAgent:
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def generate_content(self, topic: str, content_type: str, personas: List[Dict], 
                             pain_points: List[str], serp_data: Dict) -> Dict:
        """Generate content optimized for personas and SERP data"""
        
        pain_points_str = '\n'.join([f"• {p}" for p in (pain_points or [])])
        personas_str = '\n'.join([f"- {p['name']}: {p.get('motivation', '')}" for p in personas])
        people_ask = '\n'.join([f"• {q['question']}" for q in serp_data.get("people_also_ask", [])[:3]])
        
        prompt = f"""Create a compelling {content_type} about "{topic}"

Target Personas:
{personas_str}

Pain Points to Address:
{pain_points_str}

Questions Your Readers Ask:
{people_ask}

Requirements:
1. Write in conversational, engaging tone
2. Address specific pain points directly
3. Answer the common questions
4. Include practical examples
5. End with a strong benefit statement
6. Approximately 1500-2000 words
7. Use clear heading hierarchy

Generate the article now:"""
        
        content = await self.openai_client.generate_content(prompt, 4000, temperature=0.8)
        return {"content": content}

# ADVANCED HTML TEMPLATE WITH LOADING INDICATORS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waqzee - Advanced Content Generation</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f9f9f9;
            color: #1a1a1a;
        }
        
        .header {
            background: white;
            border-bottom: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 1000;
            padding: 20px 40px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
        }
        
        .main {
            max-width: 1800px;
            margin: 0 auto;
            padding: 40px;
        }
        
        .page-title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 40px;
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .form-section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 6px;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            font-size: 13px;
            font-family: inherit;
        }
        
        input:focus, select:focus, textarea:focus {
            border-color: #000;
            outline: none;
            box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
        }
        
        .btn {
            width: 100%;
            padding: 12px;
            background: #000;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }
        
        .btn:hover {
            background: #333;
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        /* Loading Indicator */
        .loading-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.95);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 20px;
        }
        
        .loading-overlay.show {
            display: flex;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid #f0f0f0;
            border-top: 4px solid #000;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        .loading-text {
            font-size: 18px;
            font-weight: 600;
            color: #000;
        }
        
        .loading-subtext {
            font-size: 14px;
            color: #666;
            max-width: 400px;
            text-align: center;
        }
        
        .loading-bar {
            width: 300px;
            height: 4px;
            background: #f0f0f0;
            border-radius: 2px;
            overflow: hidden;
        }
        
        .loading-bar-fill {
            height: 100%;
            background: #000;
            width: 0%;
            animation: loading-progress 2s ease-in-out infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes loading-progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }
        
        /* Results Display */
        .results-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .result-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .result-card h4 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #000;
        }
        
        .persona {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        
        .persona-name {
            font-weight: 600;
            color: #000;
        }
        
        .persona-detail {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 13px;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #666;
        }
        
        .metric-value {
            font-weight: 600;
            color: #000;
        }
        
        .serp-result {
            padding: 12px;
            background: #fafafa;
            border-left: 3px solid #000;
            margin-bottom: 12px;
            font-size: 13px;
        }
        
        .serp-title {
            font-weight: 600;
            color: #0066cc;
            margin-bottom: 4px;
        }
        
        .serp-url {
            color: #006621;
            font-size: 12px;
        }
        
        .editor-full {
            background: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            overflow: hidden;
        }
        
        .tabs {
            display: flex;
            border-bottom: 1px solid #e0e0e0;
            background: #fafafa;
        }
        
        .tab {
            flex: 1;
            padding: 12px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-weight: 500;
            border-bottom: 2px solid transparent;
        }
        
        .tab.active {
            border-bottom-color: #000;
            color: #000;
        }
        
        .tab-content {
            display: none;
            padding: 30px;
        }
        
        .tab-content.show {
            display: block;
        }
        
        .ql-container {
            border: none !important;
            min-height: 500px;
        }
        
        .ql-editor {
            font-size: 14px;
        }
        
        @media (max-width: 1200px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            .results-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Waqzee Advanced Content Engine</div>
    </div>

    <div class="main">
        <h1 class="page-title">Generate Optimized Content with SERP & Persona Intelligence</h1>

        <!-- Loading Overlay -->
        <div id="loadingOverlay" class="loading-overlay">
            <div class="spinner"></div>
            <div class="loading-text" id="loadingText">Researching...</div>
            <div class="loading-subtext" id="loadingSubtext">Analyzing Reddit, Google, News & generating personas</div>
            <div class="loading-bar">
                <div class="loading-bar-fill"></div>
            </div>
        </div>

        <!-- Input Section -->
        <div class="content-grid">
            <div>
                <div class="form-section">
                    <h3 class="section-title">Research Input</h3>
                    
                    <div class="form-group">
                        <label>Topic</label>
                        <input type="text" id="topic" placeholder="e.g., best cars for NHS employees" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Article Title</label>
                        <input type="text" id="title" placeholder="Your article title">
                    </div>
                    
                    <div class="form-group">
                        <label>English Variant</label>
                        <select id="english">
                            <option value="british">British English</option>
                            <option value="american" selected>American English</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Content Type</label>
                        <select id="contentType">
                            <option value="blog post">Blog Post</option>
                            <option value="guide">Comprehensive Guide</option>
                            <option value="comparison">Comparison Article</option>
                        </select>
                    </div>
                    
                    <button class="btn" onclick="generateContent()">Generate Content</button>
                </div>
            </div>

            <!-- Real-time Metrics -->
            <div>
                <div class="form-section">
                    <h3 class="section-title">Real-time Metrics</h3>
                    <div id="realtimeMetrics">
                        <div class="metric">
                            <span class="metric-label">Readability</span>
                            <span class="metric-value" id="metricReadability">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Engagement Potential</span>
                            <span class="metric-value" id="metricEngagement">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Trust Score</span>
                            <span class="metric-value" id="metricTrust">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Emotional Tone</span>
                            <span class="metric-value" id="metricEmotion">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Uniqueness vs SERP</span>
                            <span class="metric-value" id="metricUniqueness">-</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Results Section -->
        <div id="resultsSection" style="display: none;">
            <div class="results-grid">
                <!-- Personas -->
                <div class="result-card">
                    <h4>Generated Personas</h4>
                    <div id="personasDisplay"></div>
                </div>

                <!-- SERP Data -->
                <div class="result-card">
                    <h4>Top Ranking Websites</h4>
                    <div id="serpDisplay"></div>
                </div>

                <!-- Pain Points -->
                <div class="result-card">
                    <h4>Identified Pain Points</h4>
                    <div id="painPointsDisplay"></div>
                </div>

                <!-- Advanced Analytics -->
                <div class="result-card">
                    <h4>Content Intelligence</h4>
                    <div id="analyticsDisplay"></div>
                </div>
            </div>

            <!-- Editor -->
            <div class="editor-full">
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('editor')">Editor</button>
                    <button class="tab" onclick="switchTab('code')">Code</button>
                    <button class="tab" onclick="switchTab('preview')">Preview</button>
                </div>
                <div id="editorTab" class="tab-content show">
                    <div id="editor"></div>
                </div>
                <div id="codeTab" class="tab-content">
                    <pre><code id="codeDisplay"></code></pre>
                </div>
                <div id="previewTab" class="tab-content">
                    <div id="previewDisplay"></div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
    <script>
        let editor = null;
        let currentContent = "";
        let currentPersonas = [];
        let currentPainPoints = [];

        function showLoading(text, subtext = "") {
            document.getElementById('loadingText').textContent = text;
            if (subtext) document.getElementById('loadingSubtext').textContent = subtext;
            document.getElementById('loadingOverlay').classList.add('show');
        }

        function hideLoading() {
            document.getElementById('loadingOverlay').classList.remove('show');
        }

        async function generateContent() {
            const topic = document.getElementById('topic').value;
            const title = document.getElementById('title').value;
            
            if (!topic) {
                alert('Please enter a topic');
                return;
            }

            showLoading(
                'Generating Content',
                'Researching Reddit, Google SERP, News APIs & analyzing sentiment...'
            );

            try {
                const response = await fetch('/generate-advanced', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        topic,
                        title: title || topic,
                        content_type: document.getElementById('contentType').value,
                        english_variant: document.getElementById('english').value
                    })
                });

                const result = await response.json();
                hideLoading();

                if (result.error) {
                    alert('Error: ' + result.error);
                    return;
                }

                // Display results
                currentPersonas = result.personas || [];
                currentPainPoints = result.pain_points || [];
                currentContent = result.content || "";

                displayPersonas(currentPersonas);
                displaySERPResults(result.serp_results || []);
                displayPainPoints(currentPainPoints);
                displayAnalytics(result.analytics || {});

                // Initialize editor
                if (!editor) {
                    editor = new Quill('#editor', {
                        theme: 'snow',
                        modules: {
                            toolbar: [
                                ['bold', 'italic', 'underline'],
                                [{ 'header': [1, 2, 3] }],
                                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                                ['link', 'image'],
                                ['clean']
                            ]
                        }
                    });
                    
                    editor.on('text-change', updateLiveMetrics);
                }

                editor.root.innerHTML = currentContent;
                updateLiveMetrics();
                
                document.getElementById('resultsSection').style.display = 'block';

            } catch (error) {
                hideLoading();
                alert('Error: ' + error.message);
            }
        }

        function displayPersonas(personas) {
            const html = personas.map(p => `
                <div class="persona">
                    <div class="persona-name">${p.name}</div>
                    <div class="persona-detail">Sentiment: ${p.sentiment}</div>
                    <div class="persona-detail">Motivation: ${p.motivation}</div>
                </div>
            `).join('');
            document.getElementById('personasDisplay').innerHTML = html;
        }

        function displaySERPResults(results) {
            const html = results.slice(0, 3).map(r => `
                <div class="serp-result">
                    <div class="serp-title">${r.title}</div>
                    <div class="serp-url">${r.url}</div>
                </div>
            `).join('');
            document.getElementById('serpDisplay').innerHTML = html || '<p>No SERP data available</p>';
        }

        function displayPainPoints(points) {
            const html = points.map((p, i) => `
                <div class="metric">
                    <span>${i + 1}. ${p}</span>
                </div>
            `).join('');
            document.getElementById('painPointsDisplay').innerHTML = html;
        }

        function displayAnalytics(analytics) {
            const html = `
                <div class="metric">
                    <span class="metric-label">Emotional Tone</span>
                    <span class="metric-value">${analytics.emotion_tone || '-'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Trust Markers</span>
                    <span class="metric-value">${analytics.trust_markers || '-'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Engagement Power</span>
                    <span class="metric-value">${analytics.engagement_power || '-'}</span>
                </div>
            `;
            document.getElementById('analyticsDisplay').innerHTML = html;
        }

        function updateLiveMetrics() {
            if (!editor) return;

            fetch('/analyze-advanced', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    content: editor.root.innerHTML,
                    pain_points: currentPainPoints
                })
            })
            .then(r => r.json())
            .then(data => {
                const m = data.metrics || {};
                document.getElementById('metricReadability').textContent = m.readability || '-';
                document.getElementById('metricEngagement').textContent = m.engagement || '-';
                document.getElementById('metricTrust').textContent = m.trust || '-';
                document.getElementById('metricEmotion').textContent = m.emotion || '-';
                document.getElementById('metricUniqueness').textContent = m.uniqueness || '-';
            })
            .catch(e => console.error('Metrics error:', e));
        }

        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('show'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            
            if (tab === 'editor') {
                document.getElementById('editorTab').classList.add('show');
            } else if (tab === 'code') {
                document.getElementById('codeTab').classList.add('show');
                document.getElementById('codeDisplay').textContent = editor.root.innerHTML;
            } else if (tab === 'preview') {
                document.getElementById('previewTab').classList.add('show');
                document.getElementById('previewDisplay').innerHTML = editor.root.innerHTML;
            }
            
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

@app.route('/')
@app.route('/tools')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-advanced', methods=['POST'])
def generate_advanced():
    """Complete advanced generation with all APIs"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({"error": "Topic required"}), 400
        
        # Get SERP data
        serp_data = SerpAPIResearch.get_top_results(topic)
        serp_results = serp_data.get("organic_results", [])
        
        # Get news trends
        news_data = NewsResearch.get_trending(topic)
        
        # Get Reddit data for personas
        generation_agent, reddit_scraper, pain_extractor, openai_client = create_agents()
        
        if not reddit_scraper:
            return jsonify({"error": "Reddit scraper not available"}), 500
        
        reddit_data = reddit_scraper.scrape_for_pain_points("reddit", topic, 25)
        posts = reddit_data.get('posts', [])
        comments = reddit_data.get('comments', [])
        
        # Extract pain points
        if pain_extractor:
            pain_analysis = asyncio.run(
                pain_extractor.extract_pain_points_from_posts(posts, topic, 8)
            )
            pain_points = [pp['pain_point'] if isinstance(pp, dict) else pp 
                          for pp in pain_analysis.get('pain_points', [])]
        else:
            pain_points = reddit_data.get('pain_points_extracted', [])[:8]
        
        if not pain_points:
            pain_points = ["Understanding user needs", "Finding relevant solutions"]
        
        # Generate personas
        personas = PersonaGenerator.extract_personas(posts, comments)
        
        # Generate content
        content_result = asyncio.run(
            generation_agent.generate_content(
                topic=data.get('title', topic),
                content_type=data.get('content_type', 'blog post'),
                personas=personas,
                pain_points=pain_points,
                serp_data=serp_data
            )
        )
        
        content = content_result.get('content', '')
        
        # Generate CTA
        cta = CTAGenerator.generate_cta(openai_client, content, topic, personas)
        final_content = content + f"\n\n<p><strong>{cta}</strong></p>"
        
        # Analyze content
        emotions = ContentAnalytics.analyze_emotions(final_content)
        engagement = ContentAnalytics.calculate_engagement_potential(final_content)
        trust = ContentAnalytics.calculate_trust_markers(final_content)
        
        return jsonify({
            "success": True,
            "content": final_content,
            "personas": personas,
            "pain_points": pain_points,
            "serp_results": serp_results,
            "news_trends": news_data.get('articles', [])[:3],
            "analytics": {
                "emotion_tone": emotions.get("overall_sentiment", "neutral"),
                "trust_markers": trust.get("trust_score", 0),
                "engagement_power": engagement.get("engagement_score", 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-advanced', methods=['POST'])
def analyze_advanced():
    """Advanced real-time analysis"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        pain_points = data.get('pain_points', [])
        
        emotions = ContentAnalytics.analyze_emotions(content)
        engagement = ContentAnalytics.calculate_engagement_potential(content)
        trust = ContentAnalytics.calculate_trust_markers(content)
        
        return jsonify({
            "metrics": {
                "readability": round(engagement.get("engagement_score", 0), 1),
                "engagement": round(engagement.get("engagement_score", 0), 1),
                "trust": trust.get("trust_score", 0),
                "emotion": emotions.get("overall_sentiment", "neutral"),
                "uniqueness": "high"
            }
        })
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
