"""
SEO Engine - Real-Time Metrics and Recommendations
Like SurferSEO but integrated with NLP and competitor data
"""

import re
import logging
from typing import Dict, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class SEOEngine:
    """Real-time SEO analysis engine"""
    
    def __init__(self, nlp_agent=None):
        """
        Initialize SEO Engine
        
        Args:
            nlp_agent: Optional NLPAgent instance for entity analysis
        """
        self.nlp_agent = nlp_agent
        logger.info("✅ SEO Engine initialized")
    
    def get_word_count(self, text: str) -> int:
        """Get word count from text"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return len(clean_text.split())
    
    def get_keyword_density(self, text: str, keyword: str) -> Dict:
        """
        Calculate keyword density
        
        Returns:
            Dict with density percentage, count, and status
        """
        # Clean text
        clean_text = re.sub(r'<[^>]+>', ' ', text).lower()
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        keyword_lower = keyword.lower()
        word_count = len(clean_text.split())
        
        # Count exact keyword
        keyword_count = clean_text.count(keyword_lower)
        
        # Count variations (words from keyword)
        keyword_words = set(keyword_lower.split())
        variation_count = sum(1 for word in clean_text.split() if word in keyword_words)
        
        if word_count == 0:
            return {
                'density': 0.0,
                'keyword_count': 0,
                'variation_count': 0,
                'word_count': 0,
                'status': 'no_content',
                'optimal': False
            }
        
        density = (keyword_count / word_count) * 100
        
        # Optimal range: 1-2%
        status = 'optimal' if 1.0 <= density <= 2.0 else 'low' if density < 1.0 else 'high'
        
        return {
            'density': round(density, 2),
            'keyword_count': keyword_count,
            'variation_count': variation_count,
            'word_count': word_count,
            'status': status,
            'optimal': status == 'optimal',
            'target_range': '1-2%'
        }
    
    def get_entities(self, text: str) -> List[Dict]:
        """
        Extract entities using NLP agent
        
        Returns:
            List of entities with name, type, and salience
        """
        if not self.nlp_agent or not self.nlp_agent.available:
            logger.warning("NLP agent not available for entity extraction")
            return []
        
        try:
            # Clean HTML
            clean_text = re.sub(r'<[^>]+>', ' ', text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            entities = self.nlp_agent.extract_entities(clean_text)
            return entities[:20]  # Top 20 entities
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return []
    
    def missing_entities(
        self,
        text: str,
        competitor_entities: List[Dict]
    ) -> Dict:
        """
        Find entities missing from content
        
        Args:
            text: Article text
            competitor_entities: List of competitor entities
            
        Returns:
            Dict with missing entities and coverage score
        """
        if not competitor_entities:
            return {
                'missing': [],
                'coverage': 100.0,
                'covered_count': 0,
                'total_required': 0,
                'status': 'no_baseline'
            }
        
        # Get article entities
        article_entities = self.get_entities(text)
        
        # Convert to sets for comparison
        article_names = set([e['name'].lower() for e in article_entities])
        competitor_names = set([e['name'].lower() for e in competitor_entities])
        
        # Find missing
        missing_names = competitor_names - article_names
        covered_names = competitor_names & article_names
        
        # Get details for missing entities
        missing_entities = []
        for entity in competitor_entities:
            if entity['name'].lower() in missing_names:
                missing_entities.append({
                    'name': entity['name'],
                    'type': entity.get('type', 'UNKNOWN'),
                    'salience': entity.get('salience', 0.0)
                })
        
        # Sort by salience (importance)
        missing_entities.sort(key=lambda x: x.get('salience', 0), reverse=True)
        
        # Calculate coverage
        coverage = (len(covered_names) / len(competitor_names) * 100) if competitor_names else 100.0
        
        # Status
        if coverage >= 90:
            status = 'excellent'
        elif coverage >= 80:
            status = 'good'
        elif coverage >= 70:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'missing': missing_entities[:15],  # Top 15 missing
            'coverage': round(coverage, 2),
            'covered_count': len(covered_names),
            'total_required': len(competitor_names),
            'status': status,
            'grade': self._get_grade(coverage)
        }
    
    def _get_grade(self, coverage: float) -> str:
        """Convert coverage to letter grade"""
        if coverage >= 90:
            return 'A+'
        elif coverage >= 85:
            return 'A'
        elif coverage >= 80:
            return 'B+'
        elif coverage >= 75:
            return 'B'
        elif coverage >= 70:
            return 'C'
        else:
            return 'D'
    
    def readability(self, text: str) -> Dict:
        """
        Calculate readability metrics
        
        Returns:
            Dict with Flesch Reading Ease and grade level
        """
        # Clean text
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            return {
                'score': 0,
                'grade_level': 'N/A',
                'status': 'no_content'
            }
        
        # Count sentences
        sentences = len(re.findall(r'[.!?]+', clean_text))
        if sentences == 0:
            sentences = 1
        
        # Count words
        words = len(clean_text.split())
        if words == 0:
            return {
                'score': 0,
                'grade_level': 'N/A',
                'status': 'no_content'
            }
        
        # Count syllables (rough approximation)
        syllables = sum([self._count_syllables(word) for word in clean_text.split()])
        
        # Flesch Reading Ease
        # Score = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        try:
            score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
            score = max(0, min(100, score))  # Clamp between 0-100
            
            # Determine grade level
            if score >= 90:
                grade = '5th grade (Very Easy)'
                status = 'excellent'
            elif score >= 80:
                grade = '6th grade (Easy)'
                status = 'good'
            elif score >= 70:
                grade = '7th-8th grade (Fairly Easy)'
                status = 'good'
            elif score >= 60:
                grade = '8th-9th grade (Standard)'
                status = 'acceptable'
            elif score >= 50:
                grade = '10th-12th grade (Fairly Difficult)'
                status = 'difficult'
            else:
                grade = 'College+ (Difficult)'
                status = 'very_difficult'
            
            return {
                'score': round(score, 1),
                'grade_level': grade,
                'status': status,
                'avg_words_per_sentence': round(words / sentences, 1),
                'avg_syllables_per_word': round(syllables / words, 2)
            }
            
        except ZeroDivisionError:
            return {
                'score': 0,
                'grade_level': 'N/A',
                'status': 'error'
            }
    
    def _count_syllables(self, word: str) -> int:
        """Rough syllable count"""
        word = word.lower()
        syllables = 0
        vowels = 'aeiouy'
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllables += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            syllables -= 1
        
        # Ensure at least 1 syllable
        if syllables == 0:
            syllables = 1
        
        return syllables
    
    def check_headings(self, text: str) -> Dict:
        """Analyze heading structure"""
        h1_count = len(re.findall(r'<h1[^>]*>.*?</h1>', text, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>.*?</h2>', text, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>.*?</h3>', text, re.IGNORECASE))
        
        # Extract H2 headings
        h2_headings = re.findall(r'<h2[^>]*>(.*?)</h2>', text, re.IGNORECASE)
        
        status = 'good' if h1_count == 1 and h2_count >= 4 else 'needs_improvement'
        
        return {
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'h2_headings': h2_headings,
            'status': status,
            'has_proper_structure': h1_count == 1 and h2_count >= 4
        }
    
    def seo_score(
        self,
        text: str,
        keyword: str,
        competitor_entities: Optional[List[Dict]] = None,
        target_word_count: int = 2000
    ) -> Dict:
        """
        Calculate comprehensive SEO score (0-100)
        
        Factors:
        - Word count (20 points)
        - Keyword density (20 points)
        - Heading structure (15 points)
        - Entity coverage (25 points)
        - Readability (20 points)
        """
        score = 0
        breakdown = {}
        
        # 1. Word Count (20 points)
        word_count = self.get_word_count(text)
        if word_count >= target_word_count:
            wc_score = 20
        elif word_count >= target_word_count * 0.8:
            wc_score = 15
        elif word_count >= target_word_count * 0.6:
            wc_score = 10
        else:
            wc_score = 5
        
        score += wc_score
        breakdown['word_count'] = {
            'score': wc_score,
            'max': 20,
            'current': word_count,
            'target': target_word_count
        }
        
        # 2. Keyword Density (20 points)
        kw_data = self.get_keyword_density(text, keyword)
        if kw_data['status'] == 'optimal':
            kw_score = 20
        elif kw_data['status'] == 'low':
            kw_score = 10
        else:
            kw_score = 12
        
        score += kw_score
        breakdown['keyword_density'] = {
            'score': kw_score,
            'max': 20,
            'density': kw_data['density'],
            'status': kw_data['status']
        }
        
        # 3. Heading Structure (15 points)
        headings = self.check_headings(text)
        if headings['has_proper_structure']:
            h_score = 15
        elif headings['h2_count'] >= 2:
            h_score = 10
        else:
            h_score = 5
        
        score += h_score
        breakdown['headings'] = {
            'score': h_score,
            'max': 15,
            'h2_count': headings['h2_count'],
            'status': headings['status']
        }
        
        # 4. Entity Coverage (25 points)
        if competitor_entities and self.nlp_agent:
            entity_data = self.missing_entities(text, competitor_entities)
            coverage = entity_data['coverage']
            
            if coverage >= 90:
                e_score = 25
            elif coverage >= 80:
                e_score = 20
            elif coverage >= 70:
                e_score = 15
            elif coverage >= 60:
                e_score = 10
            else:
                e_score = 5
            
            score += e_score
            breakdown['entity_coverage'] = {
                'score': e_score,
                'max': 25,
                'coverage': coverage,
                'grade': entity_data['grade']
            }
        else:
            # No entity data - give partial credit
            score += 15
            breakdown['entity_coverage'] = {
                'score': 15,
                'max': 25,
                'status': 'no_baseline'
            }
        
        # 5. Readability (20 points)
        read_data = self.readability(text)
        if read_data['status'] in ['excellent', 'good']:
            r_score = 20
        elif read_data['status'] == 'acceptable':
            r_score = 15
        else:
            r_score = 10
        
        score += r_score
        breakdown['readability'] = {
            'score': r_score,
            'max': 20,
            'flesch_score': read_data.get('score', 0),
            'status': read_data['status']
        }
        
        return {
            'total_score': score,
            'max_score': 100,
            'percentage': round(score, 1),
            'grade': self._score_to_grade(score),
            'breakdown': breakdown
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 65:
            return 'C'
        else:
            return 'D'
    
    def recommendations(
        self,
        text: str,
        keyword: str,
        competitor_entities: Optional[List[Dict]] = None,
        reddit_pain_points: Optional[List] = None,
        competitor_headings: Optional[List[str]] = None,
        target_word_count: int = 2000
    ) -> List[Dict]:
        """
        Generate actionable SEO recommendations
        
        Returns:
            List of recommendations with priority and specific actions
        """
        recs = []
        
        # Get metrics
        word_count = self.get_word_count(text)
        kw_data = self.get_keyword_density(text, keyword)
        headings = self.check_headings(text)
        
        # Word count recommendations
        if word_count < target_word_count:
            shortage = target_word_count - word_count
            recs.append({
                'category': 'Content Length',
                'priority': 'high',
                'impact': 5,
                'tip': f"Add {shortage} more words to reach {target_word_count} target",
                'current': word_count,
                'target': target_word_count,
                'action': 'Expand existing sections with more examples and details'
            })
        
        # Keyword density recommendations
        if kw_data['status'] == 'low':
            target_count = int((word_count * 0.015) - kw_data['keyword_count'])
            recs.append({
                'category': 'Keyword Optimization',
                'priority': 'high',
                'impact': 5,
                'tip': f"Use '{keyword}' {target_count} more times (current: {kw_data['keyword_count']})",
                'current': kw_data['density'],
                'target': '1-2%',
                'action': f"Naturally incorporate '{keyword}' in headings and topic sentences"
            })
        elif kw_data['status'] == 'high':
            recs.append({
                'category': 'Keyword Optimization',
                'priority': 'medium',
                'impact': 3,
                'tip': f"Keyword density is high ({kw_data['density']}%) - use more variations",
                'current': kw_data['density'],
                'target': '1-2%',
                'action': 'Replace some exact matches with synonyms and related terms'
            })
        
        # Heading recommendations
        if headings['h2_count'] < 4:
            recs.append({
                'category': 'Structure',
                'priority': 'high',
                'impact': 4,
                'tip': f"Add {4 - headings['h2_count']} more H2 headings for better structure",
                'current': headings['h2_count'],
                'target': '4-8',
                'action': 'Break long sections into focused subsections with clear H2 headings'
            })
        
        # Entity recommendations
        if competitor_entities and self.nlp_agent:
            entity_data = self.missing_entities(text, competitor_entities)
            if entity_data['coverage'] < 80:
                top_missing = [e['name'] for e in entity_data['missing'][:3]]
                recs.append({
                    'category': 'Entity Coverage',
                    'priority': 'high',
                    'impact': 5,
                    'tip': f"Coverage is {entity_data['coverage']:.0f}% - add missing entities",
                    'current': f"{entity_data['coverage']:.0f}%",
                    'target': '90%+',
                    'action': f"Mention these key entities: {', '.join(top_missing)}",
                    'missing_entities': entity_data['missing'][:5]
                })
        
        # Reddit pain point recommendations
        if reddit_pain_points:
            # Check if pain points are addressed (simple keyword matching)
            pain_text = ' '.join([str(p.get('pain', p) if isinstance(p, dict) else p).lower() for p in reddit_pain_points[:5]])
            text_lower = text.lower()
            
            unaddressed = []
            for p in reddit_pain_points[:5]:
                pain = str(p.get('pain', p) if isinstance(p, dict) else p)
                keywords_in_pain = [w for w in pain.lower().split() if len(w) > 4][:3]
                
                if not any(kw in text_lower for kw in keywords_in_pain):
                    unaddressed.append(pain[:60])
            
            if unaddressed:
                recs.append({
                    'category': 'User Intent',
                    'priority': 'high',
                    'impact': 4,
                    'tip': f"Address {len(unaddressed)} pain points from Reddit",
                    'action': 'Add sections addressing real user questions and concerns',
                    'unaddressed_pain_points': unaddressed[:3]
                })
        
        # Readability recommendations
        read_data = self.readability(text)
        if read_data['status'] in ['difficult', 'very_difficult']:
            recs.append({
                'category': 'Readability',
                'priority': 'medium',
                'impact': 3,
                'tip': f"Text is {read_data['status']} - simplify language",
                'current': read_data.get('grade_level', 'N/A'),
                'target': '7th-9th grade',
                'action': 'Use shorter sentences and simpler words'
            })
        
        # Sort by priority and impact
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recs.sort(key=lambda x: (priority_order.get(x['priority'], 2), -x['impact']))
        
        return recs[:10]  # Top 10 recommendations


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = SEOEngine()
    
    test_html = """
    <h1>Car Insurance Guide</h1>
    <h2>What is Car Insurance?</h2>
    <p>Car insurance is a contract between you and an insurance company. You pay premiums and the insurer covers your financial losses from accidents.</p>
    <h2>Types of Coverage</h2>
    <p>There are several types of car insurance coverage available in the UK, including comprehensive, third party, and third party fire and theft.</p>
    """
    
    print("Testing SEO Engine...")
    print("\nWord Count:", engine.get_word_count(test_html))
    print("\nKeyword Density:", engine.get_keyword_density(test_html, "car insurance"))
    print("\nReadability:", engine.readability(test_html))
    print("\nHeadings:", engine.check_headings(test_html))
    print("\nSEO Score:", engine.seo_score(test_html, "car insurance", target_word_count=100))
    print("\n✅ SEO Engine working")
