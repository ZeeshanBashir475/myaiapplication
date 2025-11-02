"""
AI-Powered Pain Point Extractor
Uses OpenAI to intelligently extract and categorize pain points from Reddit content
"""

import logging
from typing import List, Dict
import json
import re

logger = logging.getLogger(__name__)


class PainPointExtractor:
    """
    Extracts and analyzes pain points from Reddit data using AI
    """
    
    def __init__(self, openai_client=None):
        """
        Initialize with OpenAI client
        
        Args:
            openai_client: OpenAIClient instance from your app.py
        """
        self.openai_client = openai_client
    
    async def extract_pain_points_from_posts(self, posts: List[Dict], 
                                            topic: str = None,
                                            max_pain_points: int = 10) -> Dict:
        """
        Extract pain points from Reddit posts using AI
        
        Args:
            posts: List of Reddit post dictionaries
            topic: Optional topic context
            max_pain_points: Maximum pain points to extract
        
        Returns:
            Dictionary with categorized pain points
        """
        if not self.openai_client:
            logger.warning("No OpenAI client - using basic extraction")
            return self._basic_extraction(posts, max_pain_points)
        
        try:
            # Prepare content for AI analysis
            content = self._prepare_content_for_analysis(posts)
            
            prompt = f"""
Analyze these Reddit posts{f' about {topic}' if topic else ''} and extract the main pain points, problems, and challenges people are facing.

REDDIT CONTENT:
{content}

Extract the top {max_pain_points} most common and significant pain points. For each pain point:
1. State the pain point clearly and specifically
2. Estimate how many people mentioned this (frequency)
3. Assess severity (High/Medium/Low)
4. Provide a brief example quote

Format as JSON:
{{
  "pain_points": [
    {{
      "pain_point": "Clear statement of the problem",
      "frequency": "Common/Occasional/Rare",
      "severity": "High/Medium/Low",
      "example": "Brief quote showing this pain point",
      "category": "Category like Financial, Time Management, Knowledge Gap, etc."
    }}
  ],
  "summary": "Overall summary of main themes"
}}

Focus on:
- Specific, actionable problems (not vague complaints)
- Things people struggle with or can't figure out
- Barriers preventing them from achieving goals
- Frustrations and obstacles
- Questions they're asking repeatedly
"""
            
            logger.info("🤖 Analyzing Reddit content with AI...")
            response = await self.openai_client.generate_content(prompt, max_tokens=2000, temperature=0.3)
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    pain_data = json.loads(json_match.group())
                else:
                    # If no JSON, parse manually
                    pain_data = self._parse_text_response(response, max_pain_points)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON, using text parsing")
                pain_data = self._parse_text_response(response, max_pain_points)
            
            logger.info(f"✅ Extracted {len(pain_data.get('pain_points', []))} pain points")
            return pain_data
            
        except Exception as e:
            logger.error(f"❌ AI extraction failed: {e}")
            return self._basic_extraction(posts, max_pain_points)
    
    async def extract_pain_points_from_comments(self, comments: List[Dict],
                                               max_pain_points: int = 10) -> Dict:
        """
        Extract pain points from Reddit comments using AI
        
        Args:
            comments: List of comment dictionaries
            max_pain_points: Maximum pain points to extract
        
        Returns:
            Dictionary with pain points
        """
        if not self.openai_client:
            return self._basic_extraction_comments(comments, max_pain_points)
        
        try:
            # Get top comments by score
            sorted_comments = sorted(comments, key=lambda x: x.get('score', 0), reverse=True)
            top_comments = sorted_comments[:50]  # Analyze top 50 comments
            
            content = "\n\n---\n\n".join([
                f"Comment (score: {c['score']}): {c['body'][:500]}"
                for c in top_comments
                if len(c.get('body', '')) > 20
            ])
            
            prompt = f"""
Analyze these Reddit comments and extract the main pain points and problems people are discussing.

COMMENTS:
{content}

Extract {max_pain_points} key pain points mentioned in these comments.

For each pain point, provide:
1. Clear statement of the problem
2. How commonly it's mentioned
3. Severity level
4. Example quote

Format as a list of pain points with details.
"""
            
            logger.info("🤖 Analyzing comments with AI...")
            response = await self.openai_client.generate_content(prompt, max_tokens=1500, temperature=0.3)
            
            pain_data = self._parse_text_response(response, max_pain_points)
            
            logger.info(f"✅ Extracted {len(pain_data.get('pain_points', []))} pain points from comments")
            return pain_data
            
        except Exception as e:
            logger.error(f"❌ Comment extraction failed: {e}")
            return self._basic_extraction_comments(comments, max_pain_points)
    
    async def categorize_pain_points(self, pain_points: List[str]) -> Dict:
        """
        Categorize pain points into themes
        
        Args:
            pain_points: List of pain point strings
        
        Returns:
            Dictionary with categorized pain points
        """
        if not self.openai_client:
            return {'categories': {'Uncategorized': pain_points}}
        
        try:
            pain_list = "\n".join([f"{i+1}. {pp}" for i, pp in enumerate(pain_points)])
            
            prompt = f"""
Categorize these pain points into logical themes/categories:

{pain_list}

Create 3-5 categories and group the pain points accordingly.
Common categories might include:
- Financial/Money concerns
- Time management
- Knowledge gaps
- Technical difficulties
- Personal obstacles
- Resource limitations
- Process inefficiencies

Provide the categorization in a clear format.
"""
            
            response = await self.openai_client.generate_content(prompt, max_tokens=800)
            
            # Parse categories (basic parsing)
            categories = self._parse_categories(response, pain_points)
            
            return {'categories': categories, 'raw_response': response}
            
        except Exception as e:
            logger.error(f"❌ Categorization failed: {e}")
            return {'categories': {'Uncategorized': pain_points}}
    
    async def prioritize_pain_points(self, pain_points: List[Dict], 
                                    business_context: str = None) -> List[Dict]:
        """
        Prioritize pain points by severity, frequency, and addressability
        
        Args:
            pain_points: List of pain point dictionaries
            business_context: Optional business context for prioritization
        
        Returns:
            Sorted list of pain points with priority scores
        """
        if not self.openai_client:
            return sorted(pain_points, key=lambda x: x.get('frequency', 0), reverse=True)
        
        try:
            pain_list = "\n".join([
                f"{i+1}. {pp.get('pain_point', pp)}"
                for i, pp in enumerate(pain_points)
            ])
            
            context_str = f"\n\nBusiness Context: {business_context}" if business_context else ""
            
            prompt = f"""
Prioritize these pain points based on:
1. How severe/impactful the problem is
2. How frequently it occurs
3. How addressable it is with content/solutions
4. Business opportunity (if there's a clear way to help){context_str}

PAIN POINTS:
{pain_list}

Rank them from highest to lowest priority and explain why.
Provide a priority score (1-10) for each.
"""
            
            response = await self.openai_client.generate_content(prompt, max_tokens=1000)
            
            # Parse priorities
            prioritized = self._parse_priorities(response, pain_points)
            
            return prioritized
            
        except Exception as e:
            logger.error(f"❌ Prioritization failed: {e}")
            return pain_points
    
    async def generate_content_angles(self, pain_points: List[str], 
                                     topic: str) -> List[Dict]:
        """
        Generate content angle ideas based on pain points
        
        Args:
            pain_points: List of pain points
            topic: Main topic
        
        Returns:
            List of content angle ideas
        """
        if not self.openai_client:
            return []
        
        try:
            pain_list = "\n".join([f"• {pp}" for pp in pain_points[:8]])
            
            prompt = f"""
Based on these pain points about {topic}, suggest 5-7 compelling content angles that would resonate with this audience:

PAIN POINTS:
{pain_list}

For each content angle, provide:
1. Headline/Title
2. Brief description
3. Which pain points it addresses
4. Unique angle/hook

Make them specific, actionable, and emotionally compelling.
"""
            
            response = await self.openai_client.generate_content(prompt, max_tokens=1500)
            
            angles = self._parse_content_angles(response)
            
            return angles
            
        except Exception as e:
            logger.error(f"❌ Angle generation failed: {e}")
            return []
    
    # Helper methods
    
    def _prepare_content_for_analysis(self, posts: List[Dict], max_chars: int = 8000) -> str:
        """Prepare post content for AI analysis"""
        content_parts = []
        char_count = 0
        
        for post in posts:
            post_text = f"Title: {post.get('title', '')}\n"
            if post.get('selftext'):
                post_text += f"Content: {post['selftext'][:500]}...\n"
            post_text += f"(Score: {post.get('score', 0)}, Comments: {post.get('num_comments', 0)})\n"
            
            if char_count + len(post_text) > max_chars:
                break
            
            content_parts.append(post_text)
            char_count += len(post_text)
        
        return "\n---\n".join(content_parts)
    
    def _parse_text_response(self, response: str, max_points: int) -> Dict:
        """Parse text response into structured pain points"""
        lines = response.split('\n')
        pain_points = []
        
        current_pain = {}
        for line in lines:
            line = line.strip()
            
            # Look for pain point statements
            if re.match(r'^\d+\.|\*|-|•', line):
                if current_pain and 'pain_point' in current_pain:
                    pain_points.append(current_pain)
                
                pain_text = re.sub(r'^[\d\.\*\-•\s]+', '', line)
                current_pain = {
                    'pain_point': pain_text,
                    'frequency': 'Unknown',
                    'severity': 'Medium',
                    'category': 'General'
                }
            
            # Look for frequency/severity indicators
            if any(word in line.lower() for word in ['common', 'frequent', 'often']):
                if current_pain:
                    current_pain['frequency'] = 'Common'
            
            if any(word in line.lower() for word in ['critical', 'major', 'severe', 'high']):
                if current_pain:
                    current_pain['severity'] = 'High'
        
        # Add last pain point
        if current_pain and 'pain_point' in current_pain:
            pain_points.append(current_pain)
        
        return {
            'pain_points': pain_points[:max_points],
            'summary': 'AI-extracted pain points from Reddit content'
        }
    
    def _basic_extraction(self, posts: List[Dict], max_points: int) -> Dict:
        """Basic pain point extraction without AI"""
        pain_indicators = [
            r"(?:struggling|problem|issue|challenge|difficult|hard)\s+(?:with|to)\s+([^.!?]+)",
            r"(?:how do i|how can i|how to)\s+([^?]+)\?",
            r"(?:can't|cannot|unable)\s+(?:to\s+)?([^.!?]+)",
            r"(?:frustrated|hate|dislike)\s+(?:with|about|that)\s+([^.!?]+)",
            r"(?:need|want|looking for)\s+([^.!?]+)"
        ]
        
        pain_points = []
        
        for post in posts:
            text = post.get('full_text', '') or f"{post.get('title', '')} {post.get('selftext', '')}"
            text_lower = text.lower()
            
            for pattern in pain_indicators:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    if 10 < len(match) < 150:
                        pain_points.append({
                            'pain_point': match.strip(),
                            'frequency': 'Unknown',
                            'severity': 'Medium',
                            'source': 'basic_extraction'
                        })
        
        # Deduplicate
        unique_pains = list({pp['pain_point']: pp for pp in pain_points}.values())
        
        return {
            'pain_points': unique_pains[:max_points],
            'summary': f'Extracted {len(unique_pains)} pain points using pattern matching'
        }
    
    def _basic_extraction_comments(self, comments: List[Dict], max_points: int) -> Dict:
        """Basic extraction from comments"""
        # Convert comments to post-like format
        pseudo_posts = [
            {'full_text': c.get('body', '')}
            for c in comments
            if len(c.get('body', '')) > 20
        ]
        return self._basic_extraction(pseudo_posts, max_points)
    
    def _parse_categories(self, response: str, pain_points: List[str]) -> Dict:
        """Parse category response"""
        # Simple parsing - you can enhance this
        categories = {}
        current_category = "General"
        
        for line in response.split('\n'):
            line = line.strip()
            
            # Check if it's a category header
            if line and line[0].isupper() and ':' in line:
                current_category = line.split(':')[0].strip()
                categories[current_category] = []
            
            # Check if it's a pain point
            elif any(pp in line for pp in pain_points):
                if current_category not in categories:
                    categories[current_category] = []
                categories[current_category].append(line)
        
        # If no categories found, put all in General
        if not categories:
            categories['General'] = pain_points
        
        return categories
    
    def _parse_priorities(self, response: str, pain_points: List[Dict]) -> List[Dict]:
        """Parse priority response"""
        # Look for priority scores in response
        for pp in pain_points:
            pp['priority_score'] = 5  # Default
        
        # Try to extract scores from response
        score_pattern = r'(\d+)[/.]?\s*(?:out of)?\s*10|priority[:\s]+(\d+)'
        scores = re.findall(score_pattern, response, re.IGNORECASE)
        
        if scores:
            for i, pp in enumerate(pain_points[:len(scores)]):
                score = int(scores[i][0] or scores[i][1] or 5)
                pp['priority_score'] = score
        
        # Sort by priority score
        return sorted(pain_points, key=lambda x: x.get('priority_score', 0), reverse=True)
    
    def _parse_content_angles(self, response: str) -> List[Dict]:
        """Parse content angle suggestions"""
        angles = []
        
        lines = response.split('\n')
        current_angle = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for numbered items or titles
            if re.match(r'^\d+\.|\*\*', line):
                if current_angle:
                    angles.append(current_angle)
                
                title = re.sub(r'^[\d\.\*\s]+', '', line).strip('*')
                current_angle = {'title': title, 'description': ''}
            
            elif current_angle and line and not line.startswith('#'):
                current_angle['description'] += ' ' + line
        
        if current_angle:
            angles.append(current_angle)
        
        return angles


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Mock data for testing
    sample_posts = [
        {
            'title': "Struggling to validate business idea without spending money",
            'selftext': "I have a business idea but I'm afraid to invest money before knowing if people want it. How do I validate cheaply?",
            'score': 234,
            'num_comments': 45
        },
        {
            'title': "Overwhelmed by legal requirements for LLC",
            'selftext': "Starting my first business and the legal stuff is confusing. Do I need an LLC right away? What about taxes?",
            'score': 189,
            'num_comments': 67
        }
    ]
    
    print("Pain Point Extractor - Test Mode")
    print("="*80)
    print("\nNote: This would normally use OpenAI for better extraction.")
    print("Running basic extraction for demonstration...")
    
    extractor = PainPointExtractor()
    result = extractor._basic_extraction(sample_posts, 10)
    
    print(f"\n✅ Extracted {len(result['pain_points'])} pain points:")
    for i, pp in enumerate(result['pain_points'], 1):
        print(f"\n{i}. {pp['pain_point']}")
        print(f"   Severity: {pp['severity']}")
