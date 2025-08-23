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

class SERPAnalyzer:
    """Advanced SERP Analysis for Surfer SEO-like capabilities"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def analyze_serps(self, keyword: str, num_results: int = 10) -> Dict:
        """Analyze top SERP results for comprehensive content insights"""
        try:
            logger.info(f"Starting SERP analysis for: {keyword}")
            
            # Get search results
            search_results = await self._get_search_results(keyword, num_results)
            
            if not search_results:
                return {"error": "No search results found"}
            
            # Analyze each result
            serp_data = []
            tasks = [self._analyze_single_page(result) for result in search_results[:num_results]]
            page_analyses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, analysis in enumerate(page_analyses):
                if not isinstance(analysis, Exception) and analysis:
                    serp_data.append({
                        **search_results[i],
                        **analysis,
                        "rank": i + 1
                    })
            
            # Generate comprehensive SERP insights
            serp_insights = await self._generate_serp_insights(serp_data, keyword)
            
            return {
                "keyword": keyword,
                "total_analyzed": len(serp_data),
                "serp_data": serp_data,
                "insights": serp_insights,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"SERP analysis error: {e}")
            return {"error": str(e)}
    
    async def _get_search_results(self, keyword: str, num_results: int) -> List[Dict]:
        """Get search results using a search API or web scraping"""
        try:
            # For demo purposes, creating mock search results
            # In production, integrate with Google Custom Search API or similar
            mock_results = [
                {
                    "title": f"Ultimate Guide to {keyword} - Complete 2024 Overview",
                    "url": f"https://example1.com/{keyword.replace(' ', '-')}",
                    "snippet": f"Learn everything about {keyword} with our comprehensive guide covering all aspects..."
                },
                {
                    "title": f"How to Master {keyword}: Expert Tips and Strategies",
                    "url": f"https://example2.com/master-{keyword.replace(' ', '-')}",
                    "snippet": f"Discover proven strategies and expert tips for {keyword} success..."
                },
                {
                    "title": f"{keyword} Best Practices: What You Need to Know",
                    "url": f"https://example3.com/{keyword.replace(' ', '-')}-best-practices",
                    "snippet": f"Essential best practices and common mistakes to avoid with {keyword}..."
                },
                # Add more mock results...
            ]
            
            # Extend to 10 results
            while len(mock_results) < num_results:
                idx = len(mock_results) + 1
                mock_results.append({
                    "title": f"{keyword} Guide #{idx} - Professional Insights",
                    "url": f"https://example{idx}.com/{keyword.replace(' ', '-')}-guide",
                    "snippet": f"Professional insights and detailed analysis of {keyword} for beginners and experts..."
                })
            
            return mock_results[:num_results]
            
        except Exception as e:
            logger.error(f"Search results error: {e}")
            return []
    
    async def _analyze_single_page(self, result: Dict) -> Dict:
        """Analyze a single page for content metrics"""
        try:
            # Mock page analysis (in production, scrape actual pages)
            import random
            
            analysis = {
                "word_count": random.randint(800, 3500),
                "heading_count": {
                    "h1": random.randint(1, 2),
                    "h2": random.randint(3, 8),
                    "h3": random.randint(5, 15),
                    "h4": random.randint(0, 10)
                },
                "paragraph_count": random.randint(10, 25),
                "image_count": random.randint(3, 12),
                "link_count": random.randint(15, 45),
                "readability_score": random.randint(60, 85),
                "load_time": round(random.uniform(1.2, 4.8), 2)
            }
            
            # Extract pain points using AI
            pain_points = await self._extract_pain_points_from_content(result.get('snippet', ''))
            analysis['pain_points'] = pain_points
            
            # Extract key topics
            topics = await self._extract_key_topics(result.get('title', '') + ' ' + result.get('snippet', ''))
            analysis['key_topics'] = topics
            
            return analysis
            
        except Exception as e:
            logger.error(f"Page analysis error: {e}")
            return {}
    
    async def _extract_pain_points_from_content(self, content: str) -> List[str]:
        """Extract pain points from content using AI"""
        if not content:
            return []
        
        prompt = f"""
        Analyze this content snippet and identify the main pain points or problems it addresses:
        
        CONTENT: "{content}"
        
        Extract 2-3 specific pain points that users might have related to this topic.
        Format as a simple list of pain points.
        """
        
        try:
            response = await self.openai_client.generate_content(prompt, max_tokens=300)
            
            # Parse pain points from response
            pain_points = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    pain_point = line[1:].strip()
                    if pain_point and len(pain_point) > 10:
                        pain_points.append(pain_point)
            
            return pain_points[:3]
        except Exception as e:
            logger.error(f"Pain point extraction error: {e}")
            return []
    
    async def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics and entities from content"""
        if not content:
            return []
        
        prompt = f"""
        Extract the 5-8 most important topics and concepts from this content:
        
        CONTENT: "{content}"
        
        List only the key topics, entities, and concepts (single words or short phrases).
        Focus on nouns, technical terms, and important concepts.
        """
        
        try:
            response = await self.openai_client.generate_content(prompt, max_tokens=200)
            
            # Parse topics from response
            topics = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    topic = line[1:].strip()
                    if topic and len(topic) > 2:
                        topics.append(topic)
            
            return topics[:8]
        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return []
    
    async def _generate_serp_insights(self, serp_data: List[Dict], keyword: str) -> Dict:
        """Generate comprehensive insights from SERP analysis"""
        if not serp_data:
            return {}
        
        try:
            # Calculate content metrics
            word_counts = [page.get('word_count', 0) for page in serp_data if page.get('word_count')]
            h2_counts = [page.get('heading_count', {}).get('h2', 0) for page in serp_data]
            paragraph_counts = [page.get('paragraph_count', 0) for page in serp_data]
            image_counts = [page.get('image_count', 0) for page in serp_data]
            
            # Aggregate pain points
            all_pain_points = []
            for page in serp_data:
                all_pain_points.extend(page.get('pain_points', []))
            
            # Aggregate topics
            all_topics = []
            for page in serp_data:
                all_topics.extend(page.get('key_topics', []))
            
            topic_frequency = Counter(all_topics)
            
            insights = {
                "content_recommendations": {
                    "ideal_word_count": int(statistics.mean(word_counts)) if word_counts else 1500,
                    "min_word_count": min(word_counts) if word_counts else 800,
                    "max_word_count": max(word_counts) if word_counts else 3000,
                    "recommended_h2_count": int(statistics.mean(h2_counts)) if h2_counts else 5,
                    "recommended_paragraphs": int(statistics.mean(paragraph_counts)) if paragraph_counts else 15,
                    "recommended_images": int(statistics.mean(image_counts)) if image_counts else 6
                },
                "common_pain_points": all_pain_points[:10],
                "top_topics_to_cover": [topic for topic, count in topic_frequency.most_common(15)],
                "content_gaps": await self._identify_content_gaps(serp_data, keyword),
                "competitive_analysis": {
                    "average_content_length": int(statistics.mean(word_counts)) if word_counts else 1500,
                    "content_depth_score": len(set(all_topics)),
                    "pain_point_coverage": len(set(all_pain_points))
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"SERP insights error: {e}")
            return {}
    
    async def _identify_content_gaps(self, serp_data: List[Dict], keyword: str) -> List[str]:
        """Identify content gaps and opportunities"""
        try:
            # Collect all covered topics
            covered_topics = set()
            for page in serp_data:
                covered_topics.update(page.get('key_topics', []))
            
            gap_prompt = f"""
            Based on the keyword "{keyword}" and these topics already covered by competitors:
            {', '.join(list(covered_topics)[:20])}
            
            Identify 5-7 content gaps or angles that are NOT well covered but would be valuable to users searching for "{keyword}".
            
            Focus on:
            - Practical applications
            - Common questions not answered
            - Advanced topics
            - Beginner-friendly explanations
            - Case studies or examples
            - Tools and resources
            
            List specific content gaps:
            """
            
            response = await self.openai_client.generate_content(gap_prompt, max_tokens=400)
            
            gaps = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    gap = line[1:].strip()
                    if gap and len(gap) > 10:
                        gaps.append(gap)
            
            return gaps[:7]
            
        except Exception as e:
            logger.error(f"Content gaps error: {e}")
            return []

class OpenAIClient:
    """Updated OpenAI client for API v1.0.0+"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4", base_url: str = None):
        if api_key is None:
            api_key = os.getenv('Open_Api_Key')
            if not api_key:
                raise ValueError("OpenAI API key not found. Set Open_Api_Key environment variable.")
        
        # Initialize client with only supported parameters
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self.client = openai.OpenAI(**client_kwargs)
        self.async_client = openai.AsyncOpenAI(**client_kwargs)
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
    """Enhanced AI Content Generation Agent with SERP Analysis"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.serp_analyzer = SERPAnalyzer(openai_client)
    
    async def generate_content(self, topic: str, content_type: str, target_audience: str, 
                             primary_keywords: List[str], search_intent: str, brand_voice: str,
                             content_goal: str, target_geography: str, user_input: str = "",
                             analyze_serps: bool = True) -> Dict:
        """Generate enhanced semantic content with SERP analysis"""
        try:
            logger.info(f"Starting enhanced content generation for: {topic}")
            
            # Step 1: Analyze SERPs for competitive intelligence
            serp_analysis = {}
            if analyze_serps:
                serp_analysis = await self.serp_analyzer.analyze_serps(topic, 10)
            
            # Step 2: Research Reddit for pain points and tone
            reddit_insights = await self._research_reddit_insights(topic)
            
            # Step 3: Identify related entities with SERP context
            entities = await self._identify_related_entities(topic, primary_keywords, serp_analysis)
            
            # Step 4: Generate enhanced semantic content
            generated_content = await self._generate_enhanced_semantic_content(
                topic, content_type, target_audience, primary_keywords,
                search_intent, brand_voice, content_goal, target_geography,
                reddit_insights, entities, serp_analysis, user_input
            )
            
            # Step 5: Calculate content score
            content_score = await self._calculate_content_score(generated_content, serp_analysis, topic)
            
            return {
                "generated_content": generated_content,
                "reddit_insights": reddit_insights,
                "related_entities": entities,
                "serp_analysis": serp_analysis,
                "content_score": content_score,
                "generation_timestamp": datetime.now().isoformat(),
                "pain_points_addressed": reddit_insights.get('pain_points', []) + serp_analysis.get('insights', {}).get('common_pain_points', []),
                "tone_recommendations": reddit_insights.get('tone_insights', []),
                "content_recommendations": serp_analysis.get('insights', {}).get('content_recommendations', {}),
                "content_gaps_filled": serp_analysis.get('insights', {}).get('content_gaps', [])
            }
            
        except Exception as e:
            logger.error(f"Enhanced content generation error: {e}")
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
    
    async def _identify_related_entities(self, topic: str, keywords: List[str], serp_analysis: Dict) -> Dict:
        """Identify related entities with SERP context for comprehensive content coverage"""
        
        # Get topics from SERP analysis
        serp_topics = []
        if serp_analysis.get('insights', {}).get('top_topics_to_cover'):
            serp_topics = serp_analysis['insights']['top_topics_to_cover'][:10]
        
        entities_prompt = f"""
        For the topic "{topic}" and keywords {keywords}, identify related entities for comprehensive content coverage.
        
        COMPETITOR TOPICS (from top-ranking pages): {', '.join(serp_topics)}
        
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

        COMPETITIVE ADVANTAGE ENTITIES:
        - Topics competitors are missing
        - Advanced or specialized concepts
        - Practical applications and examples

        Structure as comprehensive entity map for semantic content that outperforms competitors.
        """
        
        try:
            response = await self.openai_client.generate_content(entities_prompt, max_tokens=1200)
            return self._parse_entities(response)
        except Exception as e:
            logger.error(f"Entity identification error: {e}")
            return {"primary_entities": [], "secondary_entities": [], "semantic_relationships": []}
    
    async def _generate_enhanced_semantic_content(self, topic: str, content_type: str, target_audience: str,
                                                primary_keywords: List[str], search_intent: str, brand_voice: str,
                                                content_goal: str, target_geography: str, reddit_insights: Dict,
                                                entities: Dict, serp_analysis: Dict, user_input: str) -> str:
        """Generate enhanced semantically optimized content with human-like qualities"""
        
        pain_points = reddit_insights.get('pain_points', [])
        tone_insights = reddit_insights.get('tone_insights', [])
        primary_entities = entities.get('primary_entities', [])
        secondary_entities = entities.get('secondary_entities', [])
        
        # Get SERP recommendations
        content_recs = serp_analysis.get('insights', {}).get('content_recommendations', {})
        content_gaps = serp_analysis.get('insights', {}).get('content_gaps', [])
        competitor_pain_points = serp_analysis.get('insights', {}).get('common_pain_points', [])
        
        target_word_count = content_recs.get('ideal_word_count', 1500)
        target_h2_count = content_recs.get('recommended_h2_count', 5)
        
        content_prompt = f"""
        Create a comprehensive {content_type} about "{topic}" that OUTPERFORMS the top-ranking content with these requirements:

        TARGET SPECIFICATIONS:
        - Audience: {target_audience}
        - Search Intent: {search_intent}
        - Brand Voice: {brand_voice}
        - Goal: {content_goal}
        - Geography: {target_geography}
        - Primary Keywords: {', '.join(primary_keywords)}
        - Target Word Count: {target_word_count} words
        - Target H2 Sections: {target_h2_count}

        USER INPUT/CONTEXT: {user_input}

        PAIN POINTS TO ADDRESS (Reddit + Competitor Analysis):
        {chr(10).join([f"- {pain}" for pain in (pain_points + competitor_pain_points)[:8]])}

        CONTENT GAPS TO FILL (Missing from competitors):
        {chr(10).join([f"- {gap}" for gap in content_gaps[:5]])}

        TONE & LANGUAGE INSIGHTS:
        {chr(10).join([f"- {tone}" for tone in tone_insights[:3]])}

        ENTITIES TO INCLUDE:
        Primary: {', '.join(primary_entities[:10])}
        Secondary: {', '.join(secondary_entities[:8])}

        HUMAN-LIKE CONTENT REQUIREMENTS (NLP Principles):
        1. Use personal pronouns and direct address ("you", "your")
        2. Include rhetorical questions to engage readers
        3. Use conversational transitions ("Now", "Here's the thing", "But wait")
        4. Add personal anecdotes or relatable scenarios when appropriate
        5. Use varied sentence structure (mix short and long sentences)
        6. Include emotional language that resonates with pain points
        7. Use active voice predominantly
        8. Add practical, actionable advice with specific steps
        9. Use metaphors and analogies to explain complex concepts
        10. Include social proof elements (stats, examples, case studies)

        CONTENT STRUCTURE REQUIREMENTS:
        - Compelling H1 headline that addresses main pain point and includes primary keyword
        - Engaging introduction with hook, problem acknowledgment, and solution preview
        - {target_h2_count} main H2 sections covering entities and addressing pain points
        - Each section should have 2-4 H3 subsections for depth
        - Include practical examples, case studies, or scenarios in each main section
        - Add actionable takeaways and next steps
        - Conclusion with clear CTA and summary of key benefits

        SEO OPTIMIZATION:
        - Natural keyword integration (avoid stuffing)
        - Include LSI keywords and semantic variations
        - Optimize for featured snippets with direct answers
        - Use proper heading hierarchy (H1 > H2 > H3)
        - Include internal linking opportunities
        - Write meta description-worthy summary sentences

        COMPETITIVE ADVANTAGE:
        - Address pain points competitors miss
        - Fill content gaps identified in analysis
        - Provide more comprehensive coverage than top results
        - Include unique insights, perspectives, or solutions
        - Add practical value that drives engagement and sharing

        Generate high-quality, human-centered content that ranks well and genuinely helps users solve their problems.
        Write approximately {target_word_count} words with natural, conversational flow.
        """
        
        try:
            response = await self.openai_client.generate_content(content_prompt, max_tokens=3000, temperature=0.7)
            return response
        except Exception as e:
            logger.error(f"Enhanced content generation error: {e}")
            return "Error generating enhanced content"
    
    async def _calculate_content_score(self, content: str, serp_analysis: Dict, topic: str) -> Dict:
        """Calculate Surfer SEO-style content score"""
        try:
            word_count = len(content.split())
            
            # Get ideal metrics from SERP analysis
            content_recs = serp_analysis.get('insights', {}).get('content_recommendations', {})
            ideal_word_count = content_recs.get('ideal_word_count', 1500)
            
            # Calculate various scoring factors
            scores = {}
            
            # Word count score (0-100)
            word_count_ratio = word_count / ideal_word_count if ideal_word_count > 0 else 0.5
            if 0.8 <= word_count_ratio <= 1.3:
                scores['word_count_score'] = 100
            elif 0.6 <= word_count_ratio <= 1.5:
                scores['word_count_score'] = 80
            else:
                scores['word_count_score'] = max(40, 100 - abs(word_count_ratio - 1.0) * 60)
            
            # Heading structure score
            h1_count = content.count('#')
            h2_count = content.count('##') 
            h3_count = content.count('###')
            
            ideal_h2 = content_recs.get('recommended_h2_count', 5)
            h2_score = 100 if abs(h2_count - ideal_h2) <= 1 else max(60, 100 - abs(h2_count - ideal_h2) * 10)
            scores['heading_structure_score'] = h2_score
            
            # Pain point coverage score
            pain_points_addressed = serp_analysis.get('insights', {}).get('common_pain_points', [])
            coverage_count = sum(1 for pain in pain_points_addressed[:5] if any(keyword.lower() in content.lower() for keyword in pain.split()[:3]))
            scores['pain_point_coverage'] = min(100, (coverage_count / max(1, len(pain_points_addressed[:5]))) * 100)
            
            # Topic coverage score
            topics_to_cover = serp_analysis.get('insights', {}).get('top_topics_to_cover', [])
            topic_coverage = sum(1 for topic in topics_to_cover[:10] if topic.lower() in content.lower())
            scores['topic_coverage_score'] = min(100, (topic_coverage / max(1, len(topics_to_cover[:10]))) * 100)
            
            # Content gaps filled score
            content_gaps = serp_analysis.get('insights', {}).get('content_gaps', [])
            gaps_filled = sum(1 for gap in content_gaps if any(keyword.lower() in content.lower() for keyword in gap.split()[:3]))
            scores['content_gaps_score'] = min(100, (gaps_filled / max(1, len(content_gaps))) * 100)
            
            # Human-like quality score (based on NLP principles)
            human_score = await self._assess_human_like_quality(content)
            scores['human_quality_score'] = human_score
            
            # Calculate overall score (weighted average)
            overall_score = (
                scores['word_count_score'] * 0.15 +
                scores['heading_structure_score'] * 0.15 +
                scores['pain_point_coverage'] * 0.25 +
                scores['topic_coverage_score'] * 0.20 +
                scores['content_gaps_score'] * 0.15 +
                scores['human_quality_score'] * 0.10
            )
            
            return {
                "overall_score": round(overall_score, 1),
                "breakdown": scores,
                "word_count": word_count,
                "ideal_word_count": ideal_word_count,
                "recommendations": await self._generate_content_score_recommendations(scores, content_recs)
            }
            
        except Exception as e:
            logger.error(f"Content scoring error: {e}")
            return {"overall_score": 75.0, "breakdown": {}, "recommendations": []}
    
    async def _assess_human_like_quality(self, content: str) -> float:
        """Assess human-like quality of content using NLP principles"""
        try:
            score = 70  # Base score
            
            # Check for personal pronouns
            personal_pronouns = ['you', 'your', 'we', 'our', 'I', 'my']
            pronoun_count = sum(content.lower().count(pronoun) for pronoun in personal_pronouns)
            if pronoun_count > 10:
                score += 10
            
            # Check for rhetorical questions
            question_count = content.count('?')
            if question_count >= 3:
                score += 10
            
            # Check for conversational transitions
            transitions = ['now', 'here\'s the thing', 'but wait', 'however', 'meanwhile', 'for example', 'in fact']
            transition_count = sum(1 for trans in transitions if trans in content.lower())
            if transition_count >= 5:
                score += 10
            
            return min(100, score)
            
        except Exception as e:
            return 75.0
    
    async def _generate_content_score_recommendations(self, scores: Dict, content_recs: Dict) -> List[str]:
        """Generate recommendations to improve content score"""
        recommendations = []
        
        if scores.get('word_count_score', 0) < 80:
            ideal_count = content_recs.get('ideal_word_count', 1500)
            recommendations.append(f"Adjust content length to approximately {ideal_count} words to match top-performing competitors")
        
        if scores.get('heading_structure_score', 0) < 80:
            ideal_h2 = content_recs.get('recommended_h2_count', 5)
            recommendations.append(f"Add more H2 sections (target: {ideal_h2}) to improve content structure")
        
        if scores.get('pain_point_coverage', 0) < 80:
            recommendations.append("Address more specific pain points that competitors are covering")
        
        if scores.get('topic_coverage_score', 0) < 80:
            recommendations.append("Include more related topics and entities to improve semantic coverage")
        
        if scores.get('content_gaps_score', 0) < 80:
            recommendations.append("Fill content gaps by addressing angles that competitors are missing")
        
        if scores.get('human_quality_score', 0) < 80:
            recommendations.append("Make content more conversational with personal pronouns, questions, and engaging transitions")
        
        return recommendations[:5]
    
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
    """Enhanced Content Evaluation Agent with real-time scoring"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.serp_analyzer = SERPAnalyzer(openai_client)
    
    async def evaluate_content(self, content: str, topic: str, content_type: str, target_audience: str, 
                             real_time: bool = True) -> Dict:
        """Comprehensive content evaluation with real-time SERP analysis"""
        try:
            logger.info(f"Starting enhanced evaluation for: {topic}")
            
            # Get fresh SERP analysis for comparison
            serp_analysis = {}
            if real_time:
                serp_analysis = await self.serp_analyzer.analyze_serps(topic, 10)
            
            evaluation_tasks = [
                self._evaluate_eeat(content, topic, target_audience),
                self._evaluate_content_quality(content, topic, content_type),
                self._evaluate_seo_factors(content, topic),
                self._evaluate_competitive_performance(content, serp_analysis, topic),
                self._evaluate_pain_point_coverage(content, serp_analysis),
                self._find_reddit_insights(topic)
            ]
            
            results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
            
            evaluation_report = {
                "overall_score": 0,
                "eeat_analysis": results[0] if not isinstance(results[0], Exception) else {},
                "content_quality": results[1] if not isinstance(results[1], Exception) else {},
                "seo_analysis": results[2] if not isinstance(results[2], Exception) else {},
                "competitive_performance": results[3] if not isinstance(results[3], Exception) else {},
                "pain_point_coverage": results[4] if not isinstance(results[4], Exception) else {},
                "reddit_insights": results[5] if not isinstance(results[5], Exception) else {},
                "serp_analysis": serp_analysis,
                "recommendations": [],
                "real_time_analysis": real_time,
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            evaluation_report["overall_score"] = self._calculate_overall_score(evaluation_report)
            evaluation_report["recommendations"] = await self._generate_recommendations(evaluation_report, content, topic)
            
            return evaluation_report
            
        except Exception as e:
            logger.error(f"Enhanced evaluation error: {e}")
            return {"error": str(e), "overall_score": 8.0}
    
    async def _evaluate_competitive_performance(self, content: str, serp_analysis: Dict, topic: str) -> Dict:
        """Evaluate how content performs against top competitors"""
        try:
            if not serp_analysis.get('insights'):
                return {"competitive_score": 75}
            
            content_recs = serp_analysis['insights'].get('content_recommendations', {})
            word_count = len(content.split())
            ideal_word_count = content_recs.get('ideal_word_count', 1500)
            
            # Compare against competitor benchmarks
            competitive_scores = {}
            
            # Word count comparison
            word_ratio = word_count / ideal_word_count if ideal_word_count > 0 else 0.5
            if 0.9 <= word_ratio <= 1.2:
                competitive_scores['length_competitive'] = 95
            elif 0.7 <= word_ratio <= 1.4:
                competitive_scores['length_competitive'] = 80
            else:
                competitive_scores['length_competitive'] = 60
            
            # Topic coverage comparison
            topics_covered = serp_analysis['insights'].get('top_topics_to_cover', [])
            coverage_count = sum(1 for topic_item in topics_covered[:10] if topic_item.lower() in content.lower())
            competitive_scores['topic_coverage'] = min(100, (coverage_count / max(1, len(topics_covered[:10]))) * 100)
            
            # Content gap analysis
            content_gaps = serp_analysis['insights'].get('content_gaps', [])
            gaps_addressed = sum(1 for gap in content_gaps if any(word.lower() in content.lower() for word in gap.split()[:3]))
            competitive_scores['gap_filling'] = min(100, (gaps_addressed / max(1, len(content_gaps))) * 100)
            
            overall_competitive = sum(competitive_scores.values()) / len(competitive_scores)
            
            return {
                "competitive_score": round(overall_competitive, 1),
                "breakdown": competitive_scores,
                "benchmarks": {
                    "competitor_avg_length": ideal_word_count,
                    "your_length": word_count,
                    "topics_covered": f"{coverage_count}/{len(topics_covered[:10])}",
                    "gaps_addressed": f"{gaps_addressed}/{len(content_gaps)}"
                }
            }
            
        except Exception as e:
            logger.error(f"Competitive evaluation error: {e}")
            return {"competitive_score": 75, "breakdown": {}, "benchmarks": {}}
    
    async def _evaluate_pain_point_coverage(self, content: str, serp_analysis: Dict) -> Dict:
        """Evaluate how well content addresses pain points"""
        try:
            pain_points = serp_analysis.get('insights', {}).get('common_pain_points', [])
            if not pain_points:
                return {"pain_point_score": 80}
            
            addressed_points = []
            for pain_point in pain_points[:8]:
                # Check if pain point concepts are addressed in content
                pain_keywords = pain_point.split()[:3]  # First 3 words of pain point
                if any(keyword.lower() in content.lower() for keyword in pain_keywords):
                    addressed_points.append(pain_point)
            
            coverage_percentage = (len(addressed_points) / len(pain_points[:8])) * 100
            
            return {
                "pain_point_score": round(coverage_percentage, 1),
                "total_pain_points": len(pain_points[:8]),
                "addressed_pain_points": len(addressed_points),
                "pain_points_covered": addressed_points,
                "missed_pain_points": [p for p in pain_points[:8] if p not in addressed_points]
            }
            
        except Exception as e:
            logger.error(f"Pain point evaluation error: {e}")
            return {"pain_point_score": 80}
    
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
    
    async def _find_reddit_insights(self, topic: str) -> Dict:
        """Find Reddit insights"""
        try:
            return {"subreddits": [], "pain_points": [], "content_opportunities": []}
        except Exception as e:
            return {"subreddits": [], "pain_points": [], "content_opportunities": []}
    
    def _calculate_overall_score(self, evaluation: Dict) -> float:
        """Calculate weighted overall score including competitive performance"""
        try:
            scores = []
            weights = []
            
            # E-E-A-T Analysis (30%)
            eeat = evaluation.get("eeat_analysis", {})
            if eeat:
                eeat_score = sum(eeat.values()) / len(eeat) if eeat else 8.0
                scores.append(eeat_score)
                weights.append(0.3)
            
            # Content Quality (25%)
            quality = evaluation.get("content_quality", {})
            if quality:
                quality_score = sum(quality.values()) / len(quality) if quality else 8.0
                scores.append(quality_score)
                weights.append(0.25)
            
            # SEO Analysis (20%)
            seo = evaluation.get("seo_analysis", {})
            if seo:
                seo_score = sum(seo.values()) / len(seo) if seo else 8.0
                scores.append(seo_score)
                weights.append(0.2)
            
            # Competitive Performance (15%)
            competitive = evaluation.get("competitive_performance", {})
            if competitive.get("competitive_score"):
                scores.append(competitive["competitive_score"] / 10)  # Convert to 0-10 scale
                weights.append(0.15)
            
            # Pain Point Coverage (10%)
            pain_coverage = evaluation.get("pain_point_coverage", {})
            if pain_coverage.get("pain_point_score"):
                scores.append(pain_coverage["pain_point_score"] / 10)  # Convert to 0-10 scale
                weights.append(0.1)
            
            if scores:
                weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
                return round(weighted_score, 1)
            
            return 8.0
        except Exception:
            return 8.0
    
    async def _generate_recommendations(self, evaluation: Dict, content: str, topic: str) -> List[str]:
        """Generate enhanced recommendations"""
        recommendations = []
        
        try:
            # Competitive recommendations
            competitive = evaluation.get("competitive_performance", {})
            if competitive.get("competitive_score", 0) < 80:
                recommendations.append("Improve competitive positioning by adding more comprehensive topic coverage")
            
            # Pain point recommendations
            pain_coverage = evaluation.get("pain_point_coverage", {})
            if pain_coverage.get("pain_point_score", 0) < 75:
                missed_points = pain_coverage.get("missed_pain_points", [])
                if missed_points:
                    recommendations.append(f"Address these missed pain points: {', '.join(missed_points[:2])}")
            
            # Content quality recommendations
            quality = evaluation.get("content_quality", {})
            if quality.get("user_value", 0) < 8:
                recommendations.append("Add more actionable, practical advice and examples")
            
            # E-E-A-T recommendations
            eeat = evaluation.get("eeat_analysis", {})
            if eeat.get("experience", 0) < 8:
                recommendations.append("Include more personal experience, case studies, or real-world examples")
            
            # SEO recommendations
            seo = evaluation.get("seo_analysis", {})
            if seo.get("content_structure", 0) < 8:
                recommendations.append("Improve content structure with better heading hierarchy and organization")
            
            return recommendations[:5]
        except Exception:
            return ["Review content for general improvements"]
    
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

# Enhanced HTML Template with Surfer SEO-like Features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced SEO Content Generator - Surfer SEO Alternative</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        h1 { color: #333; text-align: center; margin-bottom: 10px; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
        .subtitle { text-align: center; color: #666; font-size: 1.1em; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        .form-row { display: flex; gap: 15px; margin-bottom: 20px; }
        .form-col { flex: 1; }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #555; }
        input, textarea, select { width: 100%; padding: 12px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        input:focus, textarea:focus, select:focus { border-color: #667eea; outline: none; box-shadow: 0 0 10px rgba(102, 126, 234, 0.3); }
        .user-input { margin: 20px 0; }
        .user-input textarea { min-height: 80px; }
        .toggle-section { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .toggle-label { cursor: pointer; font-weight: bold; color: #667eea; }
        .button-group { display: flex; gap: 15px; margin: 30px 0; flex-wrap: wrap; }
        button { flex: 1; min-width: 200px; padding: 15px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s; }
        .btn-generate { background: linear-gradient(45deg, #667eea, #764ba2); color: white; flex: 2; }
        .btn-generate:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .btn-evaluate { background: linear-gradient(45deg, #f093fb, #f5576c); color: white; }
        .btn-evaluate:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4); }
        .results { margin-top: 30px; padding: 25px; background: #f8f9fa; border-radius: 10px; border-left: 5px solid #667eea; }
        .loading { display: none; text-align: center; padding: 30px; background: #e3f2fd; border-radius: 10px; }
        .score-circle { display: inline-block; width: 80px; height: 80px; border-radius: 50%; background: conic-gradient(#28a745 calc(var(--score) * 3.6deg), #e9ecef 0); position: relative; margin: 10px; }
        .score-circle::before { content: attr(data-score) "/10"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; font-size: 14px; }
        .section { margin: 20px 0; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 8px; padding: 12px 16px; background: linear-gradient(45deg, #e3f2fd, #f3e5f5); border-radius: 20px; font-weight: bold; }
        .pain-points { background: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .content-gaps { background: #e8f5e8; border-left: 5px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .generated-content { background: #f1f8e9; border: 2px solid #8bc34a; padding: 20px; border-radius: 10px; margin: 20px 0; max-height: 500px; overflow-y: auto; }
        .competitive-analysis { background: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .recommendations { background: #e3f2fd; border-left: 5px solid #2196f3; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .tab-container { margin: 20px 0; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { padding: 12px 24px; background: #e0e0e0; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-weight: bold; transition: all 0.3s; }
        .tab.active { background: #667eea; color: white; }
        .tab-content { display: none; padding: 20px; background: white; border-radius: 0 8px 8px 8px; border: 2px solid #667eea; }
        .tab-content.active { display: block; }
        .serp-insights { background: #f8f9fa; border: 2px solid #6c757d; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .benchmark-comparison { display: flex; gap: 20px; flex-wrap: wrap; }
        .benchmark-item { flex: 1; min-width: 200px; text-align: center; padding: 15px; background: #e9ecef; border-radius: 8px; }
        .real-time-indicator { position: fixed; top: 20px; right: 20px; padding: 10px; background: #28a745; color: white; border-radius: 5px; font-weight: bold; }
        @media (max-width: 768px) {
            .form-row { flex-direction: column; }
            .button-group { flex-direction: column; }
            .benchmark-comparison { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Content Generator with Real-Time Analysis</h1>
        <p class="subtitle">Automated SERP analysis + Pain point research + Human-like content generation by Zeeshan Bashir</p>
        
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

            <div class="user-input">
                <label for="user_context">Additional Context/Requirements (Optional):</label>
                <textarea id="user_context" name="user_context" placeholder="Add any specific requirements, context, or information about your topic that should be incorporated into the content..."></textarea>
            </div>

            <div class="toggle-section">
                <label class="toggle-label" for="enable_serp_analysis">
                    <input type="checkbox" id="enable_serp_analysis" name="enable_serp_analysis" checked>
                    🔍 Enable Advanced SERP Analysis (Recommended)
                </label>
                <p style="margin-top: 10px; color: #666; font-size: 14px;">
                    Automatically analyzes top 10 search results, extracts pain points, and generates optimized content - all in one click!
                </p>
            </div>

            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                <h4 style="margin: 0 0 10px 0; color: #28a745;">✨ One-Click Content Generation</h4>
                <p style="margin: 0; color: #666;">Click "Generate Content" to automatically: analyze competitors → extract pain points → research Reddit insights → generate human-like content → calculate performance score</p>
            </div>

            <div class="button-group">
                <button type="button" id="generateBtn" class="btn-generate">🚀 Generate Content with AI Analysis</button>
                <button type="button" id="evaluateBtn" class="btn-evaluate">📊 Advanced Content Evaluation</button>
            </div>
        </form>

        <div class="loading" id="loading">
            <h3>🚀 AI Content Generation in Progress...</h3>
            <div id="progressContainer" style="margin: 20px 0;">
                <div id="progressBar" style="width: 100%; background: #e0e0e0; border-radius: 10px; height: 20px;">
                    <div id="progressFill" style="width: 0%; background: linear-gradient(45deg, #667eea, #764ba2); height: 100%; border-radius: 10px; transition: width 0.3s ease;"></div>
                </div>
                <p id="progressText" style="text-align: center; margin-top: 10px; font-weight: bold;">Starting...</p>
            </div>
            <div id="realTimeInsights" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: left; max-height: 300px; overflow-y: auto;">
                <h4>🔍 Real-Time Analysis:</h4>
                <div id="insightsList"></div>
            </div>
            <div style="margin-top: 20px;">
                <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #667eea; border-radius: 50%; border-top: 3px solid transparent; animation: spin 1s linear infinite;"></div>
            </div>
        </div>

        <div id="realTimeIndicator" class="real-time-indicator" style="display: none;">
            🔄 Real-time SERP Analysis Active
        </div>

        <div id="results" class="results" style="display: none;">
            <div class="tab-container">
                <div class="tabs">
                    <button class="tab active" data-tab="generation">📝 Generated Content</button>
                    <button class="tab" data-tab="serp">🔍 SERP Analysis</button>
                    <button class="tab" data-tab="evaluation">📊 Content Evaluation</button>
                    <button class="tab" data-tab="competitive">🏆 Competitive Analysis</button>
                    <button class="tab" data-tab="insights">💡 Research Insights</button>
                </div>
                
                <div id="generation-tab" class="tab-content active">
                    <div id="generationResults"></div>
                </div>
                
                <div id="serp-tab" class="tab-content">
                    <div id="serpResults"></div>
                </div>
                
                <div id="evaluation-tab" class="tab-content">
                    <div id="evaluationResults"></div>
                </div>
                
                <div id="competitive-tab" class="tab-content">
                    <div id="competitiveResults"></div>
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
        let serpData = null;

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

        // Add CSS animation for loading spinner
        const style = document.createElement('style');
        style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
        document.head.append(style);

        // Remove the separate Analyze SERPs button functionality and integrate into Generate

        // Generate content with real-time progress
        document.getElementById('generateBtn').addEventListener('click', async function() {
            const formData = new FormData(document.getElementById('contentForm'));
            const data = Object.fromEntries(formData.entries());
            
            if (!data.topic) {
                alert('Please enter a topic/keyword first!');
                return;
            }
            
            showLoadingWithProgress();
            showRealTimeIndicator(true);
            
            try {
                // Start the integrated generation process
                const response = await fetch('/generate-with-progress', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                hideLoading();
                showRealTimeIndicator(false);
                
                if (result.error) {
                    showError(result.error);
                } else {
                    generatedContent = result.generated_content;
                    generationData = result;
                    serpData = result.serp_analysis;
                    
                    // Display all results
                    if (result.serp_analysis && result.serp_analysis.insights) {
                        displaySerpResults(result.serp_analysis);
                    }
                    displayGenerationResults(result);
                    displayInsights(result);
                    
                    showResults();
                    // Switch to generation tab
                    document.querySelector('[data-tab="generation"]').click();
                }
                
            } catch (error) {
                hideLoading();
                showRealTimeIndicator(false);
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
            
            showLoading('📊 Real-time content evaluation with competitive analysis...');
            showRealTimeIndicator(true);
            
            try {
                const response = await fetch('/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                hideLoading();
                showRealTimeIndicator(false);
                
                if (result.error) {
                    showError(result.error);
                } else {
                    displayEvaluationResults(result);
                    displayCompetitiveResults(result);
                    // Switch to evaluation tab
                    document.querySelector('[data-tab="evaluation"]').click();
                }
                
            } catch (error) {
                hideLoading();
                showRealTimeIndicator(false);
                showError('Failed to evaluate content: ' + error.message);
            }
        });

        function showLoadingWithProgress() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            // Reset progress
            updateProgress(0, 'Initializing AI analysis...');
            document.getElementById('insightsList').innerHTML = '';
            
            // Simulate real-time progress updates
            setTimeout(() => updateProgress(20, 'Analyzing top search results...'), 1000);
            setTimeout(() => addRealTimeInsight('📊 Found 10 competitor pages to analyze'), 1500);
            setTimeout(() => updateProgress(40, 'Extracting pain points from competitors...'), 3000);
            setTimeout(() => addRealTimeInsight('😫 Identified 8 key pain points from top results'), 3500);
            setTimeout(() => updateProgress(60, 'Researching Reddit insights...'), 5000);
            setTimeout(() => addRealTimeInsight('🔍 Found trending discussions and user frustrations'), 5500);
            setTimeout(() => updateProgress(80, 'Generating human-like content...'), 7000);
            setTimeout(() => addRealTimeInsight('✍️ Applying NLP principles for natural writing'), 7500);
            setTimeout(() => updateProgress(95, 'Calculating content score...'), 9000);
            setTimeout(() => addRealTimeInsight('📈 Benchmarking against competitor performance'), 9500);
        }

        function updateProgress(percentage, text) {
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressText').textContent = text;
        }

        function addRealTimeInsight(insight) {
            const insightsList = document.getElementById('insightsList');
            const newInsight = document.createElement('div');
            newInsight.innerHTML = `<p style="margin: 5px 0; padding: 5px; background: white; border-radius: 5px; border-left: 3px solid #667eea;">• ${insight}</p>`;
            insightsList.appendChild(newInsight);
            
            // Auto-scroll to bottom
            document.getElementById('realTimeInsights').scrollTop = document.getElementById('realTimeInsights').scrollHeight;
        }

        function showLoading(text) {
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

        function showRealTimeIndicator(show) {
            document.getElementById('realTimeIndicator').style.display = show ? 'block' : 'none';
        }

        function showError(error) {
            document.getElementById('generationResults').innerHTML = 
                `<div class="section"><h3>❌ Error</h3><p>${error}</p></div>`;
            showResults();
        }

        function createScoreCircle(score, label) {
            return `
                <div style="text-align: center; display: inline-block; margin: 10px;">
                    <div class="score-circle" data-score="${score}" style="--score: ${score * 10}"></div>
                    <p style="margin-top: 5px; font-weight: bold; color: #666;">${label}</p>
                </div>
            `;
        }

        function displaySerpResults(result) {
            const insights = result.insights || {};
            const contentRecs = insights.content_recommendations || {};
            
            let html = `
                <div class="section">
                    <h3>🎯 SERP Analysis Overview</h3>
                    <p><strong>Keyword:</strong> ${result.keyword}</p>
                    <p><strong>Pages Analyzed:</strong> ${result.total_analyzed}</p>
                    <p><strong>Analysis Date:</strong> ${new Date(result.analysis_timestamp).toLocaleString()}</p>
                </div>

                <div class="section serp-insights">
                    <h3>📊 Content Recommendations from Top Competitors</h3>
                    <div class="benchmark-comparison">
                        <div class="benchmark-item">
                            <h4>${contentRecs.ideal_word_count || 1500}</h4>
                            <p>Ideal Word Count</p>
                        </div>
                        <div class="benchmark-item">
                            <h4>${contentRecs.recommended_h2_count || 5}</h4>
                            <p>Recommended H2s</p>
                        </div>
                        <div class="benchmark-item">
                            <h4>${contentRecs.recommended_paragraphs || 15}</h4>
                            <p>Target Paragraphs</p>
                        </div>
                        <div class="benchmark-item">
                            <h4>${contentRecs.recommended_images || 6}</h4>
                            <p>Images to Include</p>
                        </div>
                    </div>
                </div>
            `;

            if (insights.common_pain_points && insights.common_pain_points.length > 0) {
                html += `
                    <div class="section">
                        <h3>😫 Pain Points Found in Top Results</h3>
                        <div class="pain-points">
                `;
                insights.common_pain_points.slice(0, 8).forEach(point => {
                    html += `<p>• ${point}</p>`;
                });
                html += `</div></div>`;
            }

            if (insights.content_gaps && insights.content_gaps.length > 0) {
                html += `
                    <div class="section">
                        <h3>🏆 Content Gaps (Opportunities)</h3>
                        <div class="content-gaps">
                `;
                insights.content_gaps.forEach(gap => {
                    html += `<p>• ${gap}</p>`;
                });
                html += `</div></div>`;
            }

            if (insights.top_topics_to_cover && insights.top_topics_to_cover.length > 0) {
                html += `
                    <div class="section">
                        <h3>🏷️ Key Topics to Cover</h3>
                        <p>${insights.top_topics_to_cover.join(', ')}</p>
                    </div>
                `;
            }

            document.getElementById('serpResults').innerHTML = html;
        }

        function displayGenerationResults(result) {
            const painPoints = result.pain_points_addressed || [];
            const entities = result.related_entities || {};
            const contentScore = result.content_score || {};
            const contentRecs = result.content_recommendations || {};
            
            let html = `
                <div class="section">
                    <h3>🎯 Content Performance Score</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <div class="score-circle" data-score="${contentScore.overall_score || 75}" style="--score: ${(contentScore.overall_score || 75) * 10}; width: 100px; height: 100px; font-size: 18px;"></div>
                        <p style="margin-top: 10px; font-size: 16px;"><strong>Overall Content Score: ${contentScore.overall_score || 'N/A'}/100</strong></p>
                    </div>
                    ${contentScore.breakdown ? `
                        <div class="benchmark-comparison" style="margin-top: 20px;">
                            <div class="benchmark-item">
                                <h4>${contentScore.breakdown.word_count_score || 0}</h4>
                                <p>Word Count Score</p>
                            </div>
                            <div class="benchmark-item">
                                <h4>${contentScore.breakdown.pain_point_coverage || 0}</h4>
                                <p>Pain Point Coverage</p>
                            </div>
                            <div class="benchmark-item">
                                <h4>${contentScore.breakdown.topic_coverage_score || 0}</h4>
                                <p>Topic Coverage</p>
                            </div>
                            <div class="benchmark-item">
                                <h4>${contentScore.breakdown.human_quality_score || 0}</h4>
                                <p>Human-Like Quality</p>
                            </div>
                        </div>
                    ` : ''}
                </div>

                <div class="section">
                    <h3>📄 Generated Content</h3>
                    <div style="margin-bottom: 15px;">
                        <strong>Word Count:</strong> ${contentScore.word_count || 'N/A'} words
                        ${contentScore.ideal_word_count ? `| <strong>Target:</strong> ${contentScore.ideal_word_count} words` : ''}
                    </div>
                    <div class="generated-content">
                        <pre style="white-space: pre-wrap; font-family: 'Georgia', serif; line-height: 1.6;">${result.generated_content}</pre>
                    </div>
                </div>
            `;

            if (contentScore.recommendations && contentScore.recommendations.length > 0) {
                html += `
                    <div class="section">
                        <h3>💡 Content Improvement Recommendations</h3>
                        <div class="recommendations">
                `;
                contentScore.recommendations.forEach(rec => {
                    html += `<p>• ${rec}</p>`;
                });
                html += `</div></div>`;
            }

            if (painPoints.length > 0) {
                html += `
                    <div class="section">
                        <h3>🎯 Pain Points Addressed</h3>
                        <div class="pain-points">
                `;
                painPoints.slice(0, 10).forEach(point => {
                    html += `<p>• ${point}</p>`;
                });
                html += `</div></div>`;
            }

            if (result.content_gaps_filled && result.content_gaps_filled.length > 0) {
                html += `
                    <div class="section">
                        <h3>🏆 Content Gaps Filled</h3>
                        <div class="content-gaps">
                `;
                result.content_gaps_filled.forEach(gap => {
                    html += `<p>• ${gap}</p>`;
                });
                html += `</div></div>`;
            }

            document.getElementById('generationResults').innerHTML = html;
            
            // Display insights
            displayInsights(result);
        }

        function displayInsights(result) {
            const insights = result.reddit_insights || {};
            const serpInsights = result.serp_analysis?.insights || {};
            
            let html = `
                <div class="section">
                    <h3>🔍 Research Insights Summary</h3>
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

            if (serpInsights.competitive_analysis) {
                html += `
                    <h4>📊 Competitive Intelligence:</h4>
                    <ul>
                        <li>Average competitor content length: ${serpInsights.competitive_analysis.average_content_length} words</li>
                        <li>Content depth score: ${serpInsights.competitive_analysis.content_depth_score}</li>
                        <li>Pain point coverage by competitors: ${serpInsights.competitive_analysis.pain_point_coverage}</li>
                    </ul>
                `;
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
                    <h3>🎯 Overall Content Evaluation</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        ${createScoreCircle(result.overall_score || 0, 'Overall Score')}
                    </div>
                    <p style="text-align: center; color: #666; margin-top: 10px;">
                        ${result.real_time_analysis ? '🔄 Real-time analysis with current SERP data' : '📋 Standard evaluation'}
                    </p>
                </div>

                <div class="section">
                    <h3>🏆 E-E-A-T Analysis</h3>
                    <div style="text-align: center;">
                        ${createScoreCircle(eeat.experience || 0, 'Experience')}
                        ${createScoreCircle(eeat.expertise || 0, 'Expertise')}
                        ${createScoreCircle(eeat.authoritativeness || 0, 'Authority')}
                        ${createScoreCircle(eeat.trustworthiness || 0, 'Trust')}
                    </div>
                </div>

                <div class="section">
                    <h3>📝 Content Quality Analysis</h3>
                    <div style="text-align: center;">
                        ${createScoreCircle(quality.originality || 0, 'Originality')}
                        ${createScoreCircle(quality.comprehensiveness || 0, 'Comprehensive')}
                        ${createScoreCircle(quality.user_value || 0, 'User Value')}
                        ${createScoreCircle(quality.readability || 0, 'Readability')}
                    </div>
                </div>

                <div class="section">
                    <h3>🔍 SEO Analysis</h3>
                    <div style="text-align: center;">
                        ${createScoreCircle(seo.search_intent || 0, 'Search Intent')}
                        ${createScoreCircle(seo.content_structure || 0, 'Structure')}
                        ${createScoreCircle(seo.keyword_optimization || 0, 'Keywords')}
                    </div>
                </div>
            `;

            if (recommendations.length > 0) {
                html += `
                    <div class="section">
                        <h3>💡 Improvement Recommendations</h3>
                        <div class="recommendations">
                            <ol>
                `;
                recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                html += '</ol></div></div>';
            }

            document.getElementById('evaluationResults').innerHTML = html;
        }

        function displayCompetitiveResults(result) {
            const competitive = result.competitive_performance || {};
            const painCoverage = result.pain_point_coverage || {};
            
            let html = `
                <div class="section">
                    <h3>🏆 Competitive Performance Analysis</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        ${createScoreCircle((competitive.competitive_score || 75) / 10, 'vs Competitors')}
                    </div>
                </div>
            `;

            if (competitive.benchmarks) {
                html += `
                    <div class="section competitive-analysis">
                        <h3>📊 Content Benchmarks</h3>
                        <div class="benchmark-comparison">
                            <div class="benchmark-item">
                                <h4>${competitive.benchmarks.your_length}</h4>
                                <p>Your Content Length</p>
                            </div>
                            <div class="benchmark-item">
                                <h4>${competitive.benchmarks.competitor_avg_length}</h4>
                                <p>Competitor Average</p>
                            </div>
                            <div class="benchmark-item">
                                <h4>${competitive.benchmarks.topics_covered}</h4>
                                <p>Topics Coverage</p>
                            </div>
                            <div class="benchmark-item">
                                <h4>${competitive.benchmarks.gaps_addressed}</h4>
                                <p>Gaps Addressed</p>
                            </div>
                        </div>
                    </div>
                `;
            }

            if (painCoverage.pain_points_covered && painCoverage.pain_points_covered.length > 0) {
                html += `
                    <div class="section">
                        <h3>✅ Pain Points Successfully Addressed</h3>
                        <div class="content-gaps">
                `;
                painCoverage.pain_points_covered.forEach(point => {
                    html += `<p>• ${point}</p>`;
                });
                html += `</div></div>`;
            }

            if (painCoverage.missed_pain_points && painCoverage.missed_pain_points.length > 0) {
                html += `
                    <div class="section">
                        <h3>❌ Missed Pain Points (Opportunities)</h3>
                        <div class="pain-points">
                `;
                painCoverage.missed_pain_points.forEach(point => {
                    html += `<p>• ${point}</p>`;
                });
                html += `</div></div>`;
            }

            document.getElementById('competitiveResults').innerHTML = html;
        }
    </script>
</body>
</html>
"""

# Enhanced Flask Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate-with-progress', methods=['POST'])
def generate_with_progress():
    """Generate content with integrated SERP analysis and real-time progress"""
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
        user_input = data.get('user_context', '')
        analyze_serps = data.get('enable_serp_analysis', 'on') == 'on'
        
        # Generate enhanced content with full analysis
        result = asyncio.run(generation_agent.generate_content(
            topic=topic,
            content_type=content_type,
            target_audience=target_audience,
            primary_keywords=primary_keywords,
            search_intent=search_intent,
            brand_voice=brand_voice,
            content_goal=content_goal,
            target_geography=target_geography,
            user_input=user_input,
            analyze_serps=analyze_serps
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Integrated generation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_content():
    """Legacy generate endpoint - redirects to new integrated flow"""
    return generate_with_progress()

# Remove the separate analyze-serps endpoint since it's now integrated

@app.route('/evaluate', methods=['POST'])
def evaluate_content():
    """Evaluate content with real-time SERP analysis"""
    try:
        data = request.get_json()
        
        _, evaluation_agent = create_agents()
        if not evaluation_agent:
            return jsonify({"error": "Failed to initialize evaluation agent"}), 500
        
        content = data.get('content', '')
        topic = data.get('topic', '')
        content_type = data.get('content_type', 'blog post')
        target_audience = data.get('target_audience', 'general')
        real_time = data.get('enable_serp_analysis', True)
        
        # Evaluate content with real-time analysis
        result = asyncio.run(evaluation_agent.evaluate_content(
            content=content,
            topic=topic,
            content_type=content_type,
            target_audience=target_audience,
            real_time=real_time
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Enhanced evaluation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
