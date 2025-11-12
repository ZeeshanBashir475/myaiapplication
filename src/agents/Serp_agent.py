"""
SERP Agent - Google Search Results & Competitor Analysis
Analyzes search results, PAA questions, and competitor content
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


class SerpAgent:
    """
    Comprehensive SERP analysis agent for SEO optimization
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize SERP Agent with API credentials
        
        Args:
            api_key: SerpAPI key (or gets from environment)
        """
        self.api_key = api_key or os.getenv('Serp_API')
        self.base_url = "https://serpapi.com/search"
        logger.info("✅ SerpAgent initialized")
    
    def analyze_keyword(self, keyword: str, location: str = "United Kingdom", 
                       language: str = "en", num_results: int = 10) -> Dict:
        """
        Complete SERP analysis for a keyword
        
        Args:
            keyword: Target keyword to analyze
            location: Geographic location for search
            language: Language code
            num_results: Number of results to analyze
        
        Returns:
            Dictionary with comprehensive SERP data
        """
        try:
            logger.info(f"🔍 Analyzing SERP for: '{keyword}'")
            
            if not self.api_key:
                logger.warning("No SERP API key - using fallback data")
                return self._get_fallback_data(keyword)
            
            # Build request parameters
            params = {
                "q": keyword,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google",
                "location": location,
                "gl": "uk" if location == "United Kingdom" else "us",
                "hl": language
            }
            
            # Make API request
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Parse and structure the data
            analysis = {
                'keyword': keyword,
                'search_metadata': data.get('search_metadata', {}),
                'organic_results': self._parse_organic_results(data.get('organic_results', [])),
                'people_also_ask': self._parse_paa(data.get('related_questions', [])),
                'related_searches': self._parse_related_searches(data.get('related_searches', [])),
                'featured_snippet': self._parse_featured_snippet(data),
                'knowledge_graph': data.get('knowledge_graph'),
                'competitor_analysis': self._analyze_competitors(data.get('organic_results', [])),
                'content_opportunities': [],
                'serp_features': self._identify_serp_features(data),
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Generate content opportunities
            analysis['content_opportunities'] = self._generate_opportunities(analysis)
            
            logger.info(f"✅ SERP analysis complete: {len(analysis['organic_results'])} results analyzed")
            return analysis
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ SERP API request failed: {e}")
            return self._get_fallback_data(keyword)
        except Exception as e:
            logger.error(f"❌ SERP analysis error: {e}")
            return self._get_fallback_data(keyword)
    
    def get_competitor_content_gaps(self, keyword: str, top_n: int = 5) -> Dict:
        """
        Identify content gaps in top-ranking competitors
        
        Args:
            keyword: Target keyword
            top_n: Number of top results to analyze
        
        Returns:
            Dictionary with content gap analysis
        """
        try:
            analysis = self.analyze_keyword(keyword, num_results=top_n)
            competitors = analysis['organic_results'][:top_n]
            
            gaps = {
                'missing_topics': [],
                'weak_coverage': [],
                'format_opportunities': [],
                'update_opportunities': []
            }
            
            # Analyze content types
            has_video = any('video' in c.get('title', '').lower() for c in competitors)
            has_list = any(re.search(r'\d+\s+(ways|tips|best)', c.get('title', '').lower()) for c in competitors)
            has_guide = any('guide' in c.get('title', '').lower() for c in competitors)
            has_comparison = any(any(word in c.get('title', '').lower() for word in ['vs', 'versus', 'comparison']) for c in competitors)
            
            if not has_video:
                gaps['format_opportunities'].append("Create video content - no video results in top 5")
            if not has_list:
                gaps['format_opportunities'].append("Create listicle format - underrepresented in SERP")
            if not has_guide:
                gaps['format_opportunities'].append("Create comprehensive guide - gap in SERP")
            if not has_comparison:
                gaps['format_opportunities'].append("Create comparison/alternative content")
            
            return gaps
            
        except Exception as e:
            logger.error(f"❌ Gap analysis error: {e}")
            return {'missing_topics': [], 'weak_coverage': [], 'format_opportunities': [], 'update_opportunities': []}
    
    def get_paa_questions(self, keyword: str, max_questions: int = 10) -> List[Dict]:
        """
        Extract People Also Ask questions
        
        Args:
            keyword: Search keyword
            max_questions: Maximum questions to return
        
        Returns:
            List of PAA questions with snippets
        """
        try:
            analysis = self.analyze_keyword(keyword)
            paa = analysis.get('people_also_ask', [])
            return paa[:max_questions]
        except Exception as e:
            logger.error(f"❌ PAA extraction error: {e}")
            return []
    
    def get_related_keywords(self, keyword: str, max_keywords: int = 10) -> List[str]:
        """
        Get related search keywords
        
        Args:
            keyword: Base keyword
            max_keywords: Maximum related keywords
        
        Returns:
            List of related keywords
        """
        try:
            analysis = self.analyze_keyword(keyword)
            related = analysis.get('related_searches', [])
            return related[:max_keywords]
        except Exception as e:
            logger.error(f"❌ Related keywords error: {e}")
            return []
    
    def compare_with_competitors(self, keyword: str, your_url: str = None) -> Dict:
        """
        Compare your content with top competitors
        
        Args:
            keyword: Target keyword
            your_url: Your website URL (optional)
        
        Returns:
            Comparison report
        """
        try:
            analysis = self.analyze_keyword(keyword)
            competitors = analysis['organic_results'][:5]
            
            comparison = {
                'keyword': keyword,
                'your_position': None,
                'top_competitors': competitors,
                'avg_title_length': sum(len(c.get('title', '')) for c in competitors) / len(competitors) if competitors else 0,
                'avg_description_length': sum(len(c.get('snippet', '')) for c in competitors) / len(competitors) if competitors else 0,
                'common_themes': self._extract_common_themes(competitors),
                'serp_features_present': analysis['serp_features'],
                'recommendations': []
            }
            
            # Check if your URL is ranking
            if your_url:
                for idx, result in enumerate(analysis['organic_results'], 1):
                    if your_url in result.get('link', ''):
                        comparison['your_position'] = idx
                        break
            
            # Generate recommendations
            comparison['recommendations'] = self._generate_comparison_recommendations(comparison)
            
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Competitor comparison error: {e}")
            return {}
    
    # Helper methods
    
    def _parse_organic_results(self, results: List[Dict]) -> List[Dict]:
        """Parse and clean organic search results"""
        parsed = []
        for idx, result in enumerate(results, 1):
            parsed.append({
                'position': idx,
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'displayed_link': result.get('displayed_link', ''),
                'snippet': result.get('snippet', ''),
                'date': result.get('date'),
                'rich_snippet': result.get('rich_snippet'),
                'sitelinks': result.get('sitelinks')
            })
        return parsed
    
    def _parse_paa(self, questions: List[Dict]) -> List[Dict]:
        """Parse People Also Ask questions"""
        parsed = []
        for q in questions:
            parsed.append({
                'question': q.get('question', ''),
                'snippet': q.get('snippet', '')[:300],  # Limit snippet length
                'title': q.get('title', ''),
                'link': q.get('link', '')
            })
        return parsed
    
    def _parse_related_searches(self, searches: List[Dict]) -> List[str]:
        """Parse related searches"""
        return [s.get('query', '') for s in searches if s.get('query')]
    
    def _parse_featured_snippet(self, data: Dict) -> Optional[Dict]:
        """Extract featured snippet if present"""
        snippet = data.get('answer_box') or data.get('featured_snippet')
        if snippet:
            return {
                'type': snippet.get('type'),
                'title': snippet.get('title'),
                'snippet': snippet.get('snippet') or snippet.get('answer'),
                'link': snippet.get('link')
            }
        return None
    
    def _identify_serp_features(self, data: Dict) -> List[str]:
        """Identify SERP features present"""
        features = []
        
        if data.get('answer_box') or data.get('featured_snippet'):
            features.append('Featured Snippet')
        if data.get('knowledge_graph'):
            features.append('Knowledge Graph')
        if data.get('related_questions'):
            features.append('People Also Ask')
        if data.get('video_results'):
            features.append('Video Results')
        if data.get('image_results'):
            features.append('Image Pack')
        if data.get('local_results'):
            features.append('Local Pack')
        if data.get('shopping_results'):
            features.append('Shopping Results')
        if data.get('top_stories'):
            features.append('Top Stories')
        
        return features
    
    def _analyze_competitors(self, results: List[Dict]) -> Dict:
        """Analyze competitor content patterns"""
        if not results:
            return {}
        
        titles = [r.get('title', '') for r in results[:10]]
        snippets = [r.get('snippet', '') for r in results[:10]]
        
        analysis = {
            'total_analyzed': len(results),
            'avg_title_length': sum(len(t) for t in titles) / len(titles) if titles else 0,
            'avg_snippet_length': sum(len(s) for s in snippets) / len(snippets) if snippets else 0,
            'title_patterns': self._extract_title_patterns(titles),
            'common_words': self._extract_common_words(titles + snippets),
            'content_types': self._identify_content_types(titles)
        }
        
        return analysis
    
    def _extract_title_patterns(self, titles: List[str]) -> Dict:
        """Extract common patterns in titles"""
        patterns = {
            'has_numbers': sum(1 for t in titles if re.search(r'\d+', t)),
            'has_year': sum(1 for t in titles if re.search(r'202\d', t)),
            'has_how_to': sum(1 for t in titles if 'how to' in t.lower()),
            'has_best': sum(1 for t in titles if 'best' in t.lower()),
            'has_guide': sum(1 for t in titles if 'guide' in t.lower()),
            'has_vs': sum(1 for t in titles if any(word in t.lower() for word in ['vs', 'versus']))
        }
        return patterns
    
    def _extract_common_words(self, texts: List[str], top_n: int = 10) -> List[str]:
        """Extract most common meaningful words"""
        from collections import Counter
        
        # Combine and clean text
        all_text = ' '.join(texts).lower()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'this', 'that'}
        
        words = re.findall(r'\b[a-z]{4,}\b', all_text)
        words = [w for w in words if w not in stop_words]
        
        return [word for word, count in Counter(words).most_common(top_n)]
    
    def _identify_content_types(self, titles: List[str]) -> Dict:
        """Identify types of content in SERP"""
        types = {
            'lists': sum(1 for t in titles if re.search(r'\d+\s+(ways|tips|best|top)', t.lower())),
            'guides': sum(1 for t in titles if 'guide' in t.lower()),
            'how_to': sum(1 for t in titles if 'how to' in t.lower()),
            'comparisons': sum(1 for t in titles if any(word in t.lower() for word in ['vs', 'versus', 'comparison', 'alternative'])),
            'reviews': sum(1 for t in titles if 'review' in t.lower()),
            'definitions': sum(1 for t in titles if any(word in t.lower() for word in ['what is', 'definition', 'meaning']))
        }
        return types
    
    def _generate_opportunities(self, analysis: Dict) -> List[str]:
        """Generate content opportunities based on SERP analysis"""
        opportunities = []
        
        # Check for missing content types
        content_types = analysis['competitor_analysis'].get('content_types', {})
        
        if content_types.get('lists', 0) < 3:
            opportunities.append("Create a numbered list article (e.g., '10 Best...' or '7 Ways to...')")
        
        if content_types.get('guides', 0) < 2:
            opportunities.append("Write a comprehensive guide with step-by-step instructions")
        
        if content_types.get('comparisons', 0) < 2:
            opportunities.append("Create comparison tables or 'vs' content")
        
        if not analysis.get('featured_snippet'):
            opportunities.append("Optimize for featured snippet with concise answer format")
        
        # PAA opportunities
        if len(analysis.get('people_also_ask', [])) > 0:
            opportunities.append(f"Include FAQ section answering {len(analysis['people_also_ask'])} PAA questions")
        
        # SERP features
        serp_features = analysis.get('serp_features', [])
        if 'Video Results' in serp_features:
            opportunities.append("Consider creating video content to compete in video results")
        
        if 'Image Pack' in serp_features:
            opportunities.append("Include high-quality, optimized images with descriptive alt text")
        
        # Related searches
        if len(analysis.get('related_searches', [])) > 5:
            opportunities.append("Incorporate related search terms for broader keyword coverage")
        
        return opportunities[:8]  # Limit to top 8 opportunities
    
    def _extract_common_themes(self, competitors: List[Dict]) -> List[str]:
        """Extract common themes from competitor content"""
        all_text = ' '.join([c.get('title', '') + ' ' + c.get('snippet', '') for c in competitors])
        common_words = self._extract_common_words([all_text], top_n=8)
        return common_words
    
    def _generate_comparison_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations based on comparison"""
        recommendations = []
        
        avg_title_len = comparison.get('avg_title_length', 0)
        if avg_title_len > 0:
            recommendations.append(f"Optimize title length to ~{int(avg_title_len)} characters (competitor average)")
        
        avg_desc_len = comparison.get('avg_description_length', 0)
        if avg_desc_len > 0:
            recommendations.append(f"Write meta description ~{int(avg_desc_len)} characters")
        
        if not comparison.get('your_position'):
            recommendations.append("Focus on improving on-page SEO to enter top 10 results")
        elif comparison.get('your_position', 0) > 3:
            recommendations.append(f"Improve content depth and relevance to move from position {comparison['your_position']} to top 3")
        
        common_themes = comparison.get('common_themes', [])
        if common_themes:
            recommendations.append(f"Include these key terms: {', '.join(common_themes[:5])}")
        
        serp_features = comparison.get('serp_features_present', [])
        if 'Featured Snippet' in serp_features:
            recommendations.append("Structure content to target the featured snippet position")
        if 'People Also Ask' in serp_features:
            recommendations.append("Add FAQ schema markup for PAA visibility")
        
        return recommendations
    
    def _get_fallback_data(self, keyword: str) -> Dict:
        """Generate fallback data when API is unavailable"""
        logger.info("Using fallback SERP data")
        
        return {
            'keyword': keyword,
            'search_metadata': {},
            'organic_results': [
                {
                    'position': 1,
                    'title': f"The Ultimate Guide to {keyword}",
                    'link': f"https://example.com/{keyword.replace(' ', '-')}",
                    'snippet': f"Comprehensive guide covering everything about {keyword}. Learn best practices, tips, and expert advice."
                },
                {
                    'position': 2,
                    'title': f"Best {keyword} in 2024: Top Recommendations",
                    'link': f"https://example2.com/best-{keyword.replace(' ', '-')}",
                    'snippet': f"Discover the best {keyword} options available. Expert reviews and comparisons."
                },
                {
                    'position': 3,
                    'title': f"How to Choose {keyword}: Complete Guide",
                    'link': f"https://example3.com/choosing-{keyword.replace(' ', '-')}",
                    'snippet': f"Step-by-step guide to selecting the right {keyword} for your needs."
                }
            ],
            'people_also_ask': [
                {'question': f"What is {keyword}?", 'snippet': f"Basic definition and overview of {keyword}."},
                {'question': f"How does {keyword} work?", 'snippet': f"Explanation of how {keyword} functions."},
                {'question': f"Is {keyword} worth it?", 'snippet': f"Analysis of the value of {keyword}."}
            ],
            'related_searches': [
                f"{keyword} guide",
                f"best {keyword}",
                f"{keyword} tips",
                f"how to use {keyword}",
                f"{keyword} alternatives"
            ],
            'featured_snippet': None,
            'knowledge_graph': None,
            'competitor_analysis': {
                'total_analyzed': 3,
                'avg_title_length': 50,
                'avg_snippet_length': 120,
                'title_patterns': {'has_numbers': 1, 'has_year': 1, 'has_how_to': 1, 'has_best': 1, 'has_guide': 2, 'has_vs': 0},
                'common_words': [keyword.split()[0] if ' ' in keyword else keyword, 'guide', 'best', 'how', 'tips'],
                'content_types': {'lists': 1, 'guides': 2, 'how_to': 1, 'comparisons': 0, 'reviews': 1, 'definitions': 0}
            },
            'content_opportunities': [
                "Create detailed comparison tables",
                "Include real user testimonials from Reddit",
                "Add visual elements and infographics",
                "Write FAQ section for common questions",
                "Include 2024 updates and latest trends"
            ],
            'serp_features': ['People Also Ask'],
            'analyzed_at': datetime.now().isoformat()
        }
    
    def save_analysis(self, analysis: Dict, filename: str):
        """Save SERP analysis to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved SERP analysis to {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving analysis: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize SERP agent
    agent = SerpAgent()
    
    # Test analysis
    print("\n" + "="*80)
    print("SERP AGENT - Test Mode")
    print("="*80)
    
    keyword = "eco-friendly detergent"
    
    # Run analysis
    analysis = agent.analyze_keyword(keyword)
    
    print(f"\n✅ Analyzed: {keyword}")
    print(f"Top {len(analysis['organic_results'])} results:")
    for result in analysis['organic_results'][:3]:
        print(f"\n{result['position']}. {result['title']}")
        print(f"   {result['link']}")
    
    print(f"\n✅ People Also Ask ({len(analysis['people_also_ask'])} questions):")
    for q in analysis['people_also_ask'][:3]:
        print(f"   • {q['question']}")
    
    print(f"\n✅ Content Opportunities:")
    for opp in analysis['content_opportunities']:
        print(f"   • {opp}")
    
    # Save analysis
    agent.save_analysis(analysis, 'serp_analysis.json')
    
    print("\n" + "="*80)
    print("✅ SERP Agent test complete!")
    print("="*80)
