"""
Pain Point Humanization Analyzer
Evaluates AI-generated content and suggests human improvements
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class PainPointHumanizer:
    """
    Analyzes content to identify:
    1. Which pain points are addressed
    2. How well they're addressed
    3. What human elements are missing
    4. Specific suggestions to make it more compelling
    """
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        
        # Human elements AI typically misses
        self.human_indicators = {
            'personal_stories': {
                'keywords': ['I remember', 'when I', 'my experience', 'I struggled', 'I learned', 'story', 'happened to me'],
                'weight': 10
            },
            'specific_examples': {
                'keywords': ['for example', 'specifically', 'case in point', 'real-world', 'actual', 'like when'],
                'weight': 8
            },
            'emotional_language': {
                'keywords': ['frustrated', 'excited', 'overwhelmed', 'relieved', 'anxious', 'confident', 'worried', 'hopeful'],
                'weight': 9
            },
            'conversational_tone': {
                'keywords': ['you know', 'right?', 'honestly', 'let\'s be real', 'here\'s the thing', 'trust me', 'look'],
                'weight': 7
            },
            'questions_to_reader': {
                'pattern': r'\?',
                'weight': 6
            },
            'contractions': {
                'keywords': ['don\'t', 'can\'t', 'won\'t', 'it\'s', 'you\'re', 'we\'re', 'they\'re', 'shouldn\'t'],
                'weight': 5
            },
            'specific_numbers': {
                'pattern': r'\b\d+\b',
                'weight': 6
            },
            'temporal_references': {
                'keywords': ['last week', 'yesterday', 'recently', 'a few months ago', 'back in', 'these days'],
                'weight': 8
            },
            'mistakes_admission': {
                'keywords': ['mistake', 'wrong', 'failed', 'learned the hard way', 'wish I knew', 'if I could go back'],
                'weight': 10
            },
            'reader_empathy': {
                'keywords': ['you\'re probably', 'if you\'re like me', 'I know how you feel', 'you might be wondering', 'sound familiar?'],
                'weight': 9
            }
        }
        
        # AI writing tells
        self.ai_tells = {
            'generic_phrases': [
                'it\'s important to note',
                'it\'s worth mentioning',
                'in today\'s digital age',
                'in conclusion',
                'to sum up',
                'first and foremost',
                'at the end of the day',
                'leverage',
                'utilize',
                'implement',
                'facilitate',
                'optimize',
                'comprehensive',
                'robust',
                'seamless',
                'cutting-edge',
                'state-of-the-art',
                'game-changer',
                'delve into',
                'dive deep',
                'in this article, we will',
                'stay tuned'
            ],
            'overly_formal': [
                'furthermore',
                'moreover',
                'subsequently',
                'therefore',
                'consequently',
                'nevertheless',
                'nonetheless',
                'henceforth'
            ],
            'list_overuse': r'^\s*[-•*\d\.]\s',  # Lines starting with bullets/numbers
            'perfect_grammar': True  # No sentence fragments, all perfect
        }
    
    def analyze_content(self, content: str, pain_points: List[str]) -> Dict:
        """
        Complete analysis of content against pain points with humanization suggestions
        """
        try:
            # Core analyses
            pain_point_coverage = self._analyze_pain_point_coverage(content, pain_points)
            human_score = self._calculate_human_score(content)
            ai_tells_found = self._detect_ai_tells(content)
            missing_elements = self._identify_missing_human_elements(content)
            specific_suggestions = self._generate_specific_suggestions(
                content, pain_points, pain_point_coverage, missing_elements
            )
            
            # Overall assessment
            overall_score = self._calculate_overall_score(pain_point_coverage, human_score)
            
            return {
                'overall_assessment': {
                    'score': overall_score,
                    'human_score': human_score,
                    'pain_coverage_score': pain_point_coverage['overall_coverage_percentage'],
                    'verdict': self._get_verdict(overall_score)
                },
                'pain_point_analysis': pain_point_coverage,
                'human_elements': {
                    'present': human_score['elements_present'],
                    'missing': missing_elements,
                    'ai_tells_detected': ai_tells_found
                },
                'specific_improvements': specific_suggestions,
                'before_after_examples': self._create_before_after_examples(content, ai_tells_found)
            }
            
        except Exception as e:
            logger.error(f"Content analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_pain_point_coverage(self, content: str, pain_points: List[str]) -> Dict:
        """Analyze how well each pain point is addressed"""
        coverage = []
        content_lower = content.lower()
        
        for pain_point in pain_points:
            # Extract key terms from pain point
            keywords = self._extract_keywords_from_pain_point(pain_point)
            
            # Check if pain point is mentioned
            mentioned = any(keyword in content_lower for keyword in keywords)
            
            # Check if solution is provided
            has_solution = self._check_for_solution(content, pain_point, keywords)
            
            # Check depth of coverage
            depth_score = self._assess_depth(content, keywords)
            
            coverage.append({
                'pain_point': pain_point,
                'is_mentioned': mentioned,
                'has_solution': has_solution,
                'depth_score': depth_score,
                'coverage_percentage': self._calculate_coverage_percentage(mentioned, has_solution, depth_score),
                'missing_human_touches': self._suggest_human_touches_for_pain_point(pain_point, content)
            })
        
        total_coverage = sum(p['coverage_percentage'] for p in coverage) / len(coverage) if coverage else 0
        
        return {
            'pain_points_analyzed': len(pain_points),
            'pain_points_mentioned': sum(1 for p in coverage if p['is_mentioned']),
            'pain_points_with_solutions': sum(1 for p in coverage if p['has_solution']),
            'overall_coverage_percentage': round(total_coverage, 1),
            'detailed_coverage': coverage
        }
    
    def _calculate_human_score(self, content: str) -> Dict:
        """Calculate how human the content sounds"""
        content_lower = content.lower()
        elements_present = {}
        total_score = 0
        max_score = 0
        
        for element, config in self.human_indicators.items():
            max_score += config['weight']
            
            if 'keywords' in config:
                count = sum(1 for keyword in config['keywords'] if keyword in content_lower)
                elements_present[element] = {
                    'found': count > 0,
                    'count': count,
                    'weight': config['weight']
                }
                if count > 0:
                    # Score based on presence, not overwhelming count
                    total_score += min(config['weight'], config['weight'] * (count / 3))
            
            elif 'pattern' in config:
                matches = len(re.findall(config['pattern'], content_lower))
                elements_present[element] = {
                    'found': matches > 0,
                    'count': matches,
                    'weight': config['weight']
                }
                if matches > 0:
                    total_score += min(config['weight'], config['weight'] * (matches / 5))
        
        human_percentage = (total_score / max_score) * 100
        
        return {
            'human_percentage': round(human_percentage, 1),
            'elements_present': elements_present,
            'interpretation': self._interpret_human_score(human_percentage)
        }
    
    def _detect_ai_tells(self, content: str) -> Dict:
        """Detect telltale signs of AI writing"""
        content_lower = content.lower()
        detected = {
            'generic_phrases': [],
            'overly_formal': [],
            'excessive_lists': 0,
            'total_ai_tells': 0
        }
        
        # Check generic phrases
        for phrase in self.ai_tells['generic_phrases']:
            if phrase in content_lower:
                detected['generic_phrases'].append(phrase)
        
        # Check overly formal words
        for word in self.ai_tells['overly_formal']:
            if word in content_lower:
                detected['overly_formal'].append(word)
        
        # Check list overuse
        lines = content.split('\n')
        list_lines = sum(1 for line in lines if re.match(self.ai_tells['list_overuse'], line))
        detected['excessive_lists'] = list_lines
        
        detected['total_ai_tells'] = (
            len(detected['generic_phrases']) + 
            len(detected['overly_formal']) + 
            (detected['excessive_lists'] // 5)
        )
        
        return detected
    
    def _identify_missing_human_elements(self, content: str) -> List[Dict]:
        """Identify what human elements are missing"""
        missing = []
        content_lower = content.lower()
        
        checks = [
            {
                'element': 'Personal Story or Anecdote',
                'present': any(keyword in content_lower for keyword in ['I remember', 'when I', 'my experience', 'I struggled']),
                'importance': 'HIGH',
                'why_it_matters': 'Personal stories create emotional connection and make advice more credible',
                'how_to_add': 'Share a brief 2-3 sentence story about when you faced this problem'
            },
            {
                'element': 'Specific Real-World Example',
                'present': any(keyword in content_lower for keyword in ['for example', 'specifically', 'like when', 'such as']),
                'importance': 'HIGH',
                'why_it_matters': 'Concrete examples make abstract concepts tangible and memorable',
                'how_to_add': 'Replace generic advice with "For example, when Sarah tried this, she..." type specifics'
            },
            {
                'element': 'Emotional Language',
                'present': any(keyword in content_lower for keyword in ['frustrated', 'excited', 'overwhelmed', 'relieved', 'anxious']),
                'importance': 'HIGH',
                'why_it_matters': 'Emotions make content relatable and show you understand reader\'s feelings',
                'how_to_add': 'Acknowledge the emotion: "I know how frustrating it is when..."'
            },
            {
                'element': 'Conversational Questions',
                'present': '?' in content and any(phrase in content_lower for phrase in ['you know', 'right?', 'sound familiar?']),
                'importance': 'MEDIUM',
                'why_it_matters': 'Questions engage readers and make content feel like a conversation',
                'how_to_add': 'Add rhetorical questions: "Ever felt like you\'re spinning your wheels?"'
            },
            {
                'element': 'Admission of Mistakes',
                'present': any(keyword in content_lower for keyword in ['mistake', 'wrong', 'failed', 'learned the hard way']),
                'importance': 'HIGH',
                'why_it_matters': 'Vulnerability builds trust and makes you relatable',
                'how_to_add': 'Share what didn\'t work: "I wasted 3 months trying X before realizing..."'
            },
            {
                'element': 'Casual Contractions',
                'present': any(keyword in content for keyword in ['don\'t', 'can\'t', 'won\'t', 'it\'s', 'you\'re']),
                'importance': 'MEDIUM',
                'why_it_matters': 'Contractions make writing sound natural, not stiff',
                'how_to_add': 'Change "do not" to "don\'t", "it is" to "it\'s", etc.'
            },
            {
                'element': 'Time-Specific References',
                'present': any(keyword in content_lower for keyword in ['last week', 'yesterday', 'recently', 'a few months ago']),
                'importance': 'MEDIUM',
                'why_it_matters': 'Temporal references make content feel current and authentic',
                'how_to_add': 'Add context: "Just last week, I saw..." or "This happened to a client recently"'
            },
            {
                'element': 'Reader Empathy Statements',
                'present': any(keyword in content_lower for keyword in ['you\'re probably', 'if you\'re like me', 'I know how you feel']),
                'importance': 'HIGH',
                'why_it_matters': 'Shows you understand reader\'s situation and challenges',
                'how_to_add': 'Add empathy: "If you\'re like most people, you\'re probably..."'
            },
            {
                'element': 'Sentence Variety (Fragments)',
                'present': self._has_sentence_fragments(content),
                'importance': 'LOW',
                'why_it_matters': 'Perfect grammar can sound robotic; occasional fragments add personality',
                'how_to_add': 'Use short fragments for emphasis: "Here\'s the thing. Nobody tells you this."'
            },
            {
                'element': 'Colloquial Language',
                'present': any(phrase in content_lower for phrase in ['let\'s be real', 'here\'s the deal', 'honestly', 'look']),
                'importance': 'MEDIUM',
                'why_it_matters': 'Informal language makes content approachable and friendly',
                'how_to_add': 'Start paragraphs with: "Here\'s the thing..." or "Let\'s be honest..."'
            }
        ]
        
        for check in checks:
            if not check['present']:
                missing.append({
                    'element': check['element'],
                    'importance': check['importance'],
                    'why_it_matters': check['why_it_matters'],
                    'how_to_add': check['how_to_add']
                })
        
        # Sort by importance
        importance_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        missing.sort(key=lambda x: importance_order[x['importance']])
        
        return missing
    
    def _generate_specific_suggestions(self, content: str, pain_points: List[str], 
                                      pain_coverage: Dict, missing_elements: List[Dict]) -> List[Dict]:
        """Generate actionable, specific suggestions for improvement"""
        suggestions = []
        
        # Suggestion 1: Address uncovered pain points
        uncovered = [p for p in pain_coverage['detailed_coverage'] if p['coverage_percentage'] < 50]
        if uncovered:
            suggestions.append({
                'category': 'Pain Point Coverage',
                'priority': 'CRITICAL',
                'issue': f'{len(uncovered)} pain points are barely addressed',
                'suggestion': 'Add dedicated sections for these pain points',
                'specific_action': self._create_pain_point_sections(uncovered),
                'example': self._example_pain_point_section(uncovered[0] if uncovered else None)
            })
        
        # Suggestion 2: Add human elements
        high_priority_missing = [e for e in missing_elements if e['importance'] == 'HIGH']
        if high_priority_missing:
            suggestions.append({
                'category': 'Human Elements',
                'priority': 'HIGH',
                'issue': f'Missing {len(high_priority_missing)} critical human touches',
                'suggestion': 'Add personal stories, emotions, and real examples',
                'specific_action': [e['how_to_add'] for e in high_priority_missing],
                'example': self._example_humanization()
            })
        
        # Suggestion 3: Remove AI tells
        ai_tells = self._detect_ai_tells(content)
        if ai_tells['total_ai_tells'] > 5:
            suggestions.append({
                'category': 'AI Detection Risk',
                'priority': 'HIGH',
                'issue': f'Found {ai_tells["total_ai_tells"]} AI writing tells',
                'suggestion': 'Replace generic phrases with specific, conversational language',
                'specific_action': self._create_replacement_suggestions(ai_tells),
                'example': self._example_ai_tell_fixes()
            })
        
        # Suggestion 4: Improve weak pain point coverage
        weak_coverage = [p for p in pain_coverage['detailed_coverage'] 
                        if p['is_mentioned'] but not p['has_solution']]
        if weak_coverage:
            suggestions.append({
                'category': 'Solution Depth',
                'priority': 'MEDIUM',
                'issue': f'{len(weak_coverage)} pain points mentioned but not solved',
                'suggestion': 'Add practical, step-by-step solutions',
                'specific_action': self._create_solution_frameworks(weak_coverage),
                'example': self._example_solution_section()
            })
        
        # Suggestion 5: Add credibility markers
        if not self._has_credibility_markers(content):
            suggestions.append({
                'category': 'Credibility',
                'priority': 'MEDIUM',
                'issue': 'No personal experience or credentials mentioned',
                'suggestion': 'Add brief credibility statements',
                'specific_action': [
                    'Share years of experience: "After 5 years of..."',
                    'Mention specific results: "I\'ve helped 50+ clients..."',
                    'Reference mistakes: "I made every mistake in the book..."'
                ],
                'example': '"After struggling with this myself for 2 years, I finally figured out..."'
            })
        
        return suggestions
    
    def _create_before_after_examples(self, content: str, ai_tells: Dict) -> List[Dict]:
        """Create before/after examples showing how to humanize"""
        examples = []
        
        # Example 1: Generic phrase replacement
        if ai_tells['generic_phrases']:
            examples.append({
                'issue': 'Generic AI Phrase',
                'before': f'"{ai_tells["generic_phrases"][0]}"',
                'after': self._humanize_generic_phrase(ai_tells['generic_phrases'][0]),
                'why_better': 'More specific and conversational'
            })
        
        # Example 2: Add personal touch
        examples.append({
            'issue': 'Missing Personal Connection',
            'before': '"This strategy can help improve your results."',
            'after': '"I tried this strategy last month and my conversion rate jumped 40%. Here\'s exactly what I did..."',
            'why_better': 'Specific numbers, personal experience, and promises details'
        })
        
        # Example 3: Add emotion
        examples.append({
            'issue': 'Lacks Emotional Resonance',
            'before': '"Managing multiple tasks can be difficult."',
            'after': '"Ever feel like you\'re drowning in tasks? I used to wake up anxious every day..."',
            'why_better': 'Uses relatable question and emotional language'
        })
        
        # Example 4: Make specific
        examples.append({
            'issue': 'Too Vague',
            'before': '"Use the right tools to optimize your workflow."',
            'after': '"I use Notion for task management and it saved me 10 hours per week. Here\'s my exact setup..."',
            'why_better': 'Names specific tool and quantifies benefit'
        })
        
        return examples
    
    # Helper methods
    
    def _extract_keywords_from_pain_point(self, pain_point: str) -> List[str]:
        """Extract key terms from a pain point"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        words = pain_point.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords
    
    def _check_for_solution(self, content: str, pain_point: str, keywords: List[str]) -> bool:
        """Check if content provides solution to pain point"""
        solution_indicators = ['how to', 'solution', 'fix', 'solve', 'here\'s what', 'try this', 'instead', 'better way']
        content_lower = content.lower()
        
        # Check if pain point keywords are near solution indicators
        for keyword in keywords:
            for indicator in solution_indicators:
                if keyword in content_lower and indicator in content_lower:
                    return True
        return False
    
    def _assess_depth(self, content: str, keywords: List[str]) -> int:
        """Assess depth of coverage (0-100)"""
        content_lower = content.lower()
        
        # Count occurrences of keywords
        total_mentions = sum(content_lower.count(keyword) for keyword in keywords)
        
        # Check for depth indicators
        depth_indicators = ['example', 'specifically', 'step', 'how', 'why', 'because', 'result']
        depth_signals = sum(1 for indicator in depth_indicators if indicator in content_lower)
        
        # Calculate score
        depth_score = min(100, (total_mentions * 15) + (depth_signals * 10))
        return depth_score
    
    def _calculate_coverage_percentage(self, mentioned: bool, has_solution: bool, depth_score: int) -> float:
        """Calculate overall coverage percentage"""
        if not mentioned:
            return 0
        
        base_score = 30  # Just mentioned
        if has_solution:
            base_score = 60  # Has solution
        
        # Add depth bonus
        depth_bonus = (depth_score / 100) * 40
        
        return min(100, base_score + depth_bonus)
    
    def _suggest_human_touches_for_pain_point(self, pain_point: str, content: str) -> List[str]:
        """Suggest human touches for specific pain point"""
        suggestions = []
        
        suggestions.append(f"Share a personal story about when you faced: '{pain_point}'")
        suggestions.append(f"Give specific example with numbers: 'When I dealt with {pain_point}, I...'")
        suggestions.append(f"Add emotional acknowledgment: 'I know how frustrating {pain_point} can be...'")
        suggestions.append(f"Include mistake admission: 'I made this worse by... Here's what actually works...'")
        
        return suggestions
    
    def _interpret_human_score(self, score: float) -> str:
        """Interpret the human score"""
        if score >= 70:
            return "Content sounds fairly human with good personal touches"
        elif score >= 40:
            return "Some human elements present, but needs more personality"
        else:
            return "Content sounds very AI-generated - needs significant humanization"
    
    def _calculate_overall_score(self, pain_coverage: Dict, human_score: Dict) -> float:
        """Calculate overall content quality score"""
        pain_score = pain_coverage['overall_coverage_percentage']
        human_pct = human_score['human_percentage']
        
        # Weighted average: 60% pain coverage, 40% human touch
        overall = (pain_score * 0.6) + (human_pct * 0.4)
        return round(overall, 1)
    
    def _get_verdict(self, score: float) -> str:
        """Get overall verdict"""
        if score >= 80:
            return "Excellent - compelling content that addresses pain points with human touch"
        elif score >= 60:
            return "Good - addresses pain points but needs more human elements"
        elif score >= 40:
            return "Needs work - weak pain point coverage and lacks human touch"
        else:
            return "Poor - generic content that doesn't address user needs"
    
    def _has_sentence_fragments(self, content: str) -> bool:
        """Check for intentional sentence fragments"""
        # Simple check: sentences without verbs or very short sentences
        sentences = re.split(r'[.!?]', content)
        fragments = [s for s in sentences if len(s.strip().split()) < 4 and len(s.strip()) > 0]
        return len(fragments) > 2
    
    def _has_credibility_markers(self, content: str) -> bool:
        """Check if content has credibility markers"""
        credibility_phrases = [
            'years of', 'experience', 'helped', 'clients', 'tested', 
            'tried', 'learned', 'discovered', 'found that'
        ]
        content_lower = content.lower()
        return sum(1 for phrase in credibility_phrases if phrase in content_lower) >= 2
    
    def _create_pain_point_sections(self, uncovered: List[Dict]) -> List[str]:
        """Create actionable section suggestions for uncovered pain points"""
        return [
            f"Add H2 section: 'How to Handle {p['pain_point']}' with 3-4 practical steps"
            for p in uncovered[:3]
        ]
    
    def _example_pain_point_section(self, pain_point: Dict) -> str:
        """Generate example section for a pain point"""
        if not pain_point:
            return "N/A"
        
        return f'''
## How to Handle {pain_point['pain_point']}

I struggled with this for months. Here's what finally worked:

**1. [Specific Action]** - When I tried this, I saw results in just 3 days...

**2. [Another Action]** - This was the game-changer. Here's exactly how...

**3. [Final Action]** - Don't skip this. I learned the hard way...
'''
    
    def _example_humanization(self) -> str:
        """Example of humanized content"""
        return '''
BEFORE: "It is important to understand that time management can be challenging."

AFTER: "Let's be real - I used to waste 3 hours every day just trying to figure out what to work on. Sound familiar? Here's what finally clicked for me..."
'''
    
    def _create_replacement_suggestions(self, ai_tells: Dict) -> List[str]:
        """Create specific replacement suggestions"""
        suggestions = []
        
        if ai_tells['generic_phrases']:
            for phrase in ai_tells['generic_phrases'][:3]:
                suggestions.append(f"Replace '{phrase}' with specific example or personal insight")
        
        if ai_tells['overly_formal']:
            suggestions.append("Use contractions and casual language instead of formal words")
        
        if ai_tells['excessive_lists'] > 10:
            suggestions.append("Convert some lists into conversational paragraphs with stories")
        
        return suggestions
    
    def _example_ai_tell_fixes(self) -> str:
        """Examples of fixing AI tells"""
        return '''
❌ "It's important to note that time management is crucial."
✅ "Here's what nobody tells you: time management isn't about doing more - it's about doing less of the wrong things."

❌ "In order to optimize your workflow, you should utilize..."
✅ "Want to save 10 hours per week? I use these 3 tools..."

❌ "Furthermore, it is essential to implement..."
✅ "And here's the kicker - this one change cut my workload in half..."
'''
    
    def _create_solution_frameworks(self, weak_coverage: List[Dict]) -> List[str]:
        """Create solution frameworks"""
        return [
            "Use this structure: 'The Problem → My Mistake → What Actually Works → Specific Steps'",
            "Include specific numbers: 'This took me 2 hours instead of 8'",
            "Add a mini case study: 'When [Name] tried this, here's what happened...'"
        ]
    
    def _example_solution_section(self) -> str:
        """Example solution section"""
        return '''
## Here's What Actually Works

I wasted 2 months trying every productivity app. Here's what I learned:

**The Problem:** Too many tools creates more chaos

**My Mistake:** I thought more features = better results (wrong!)

**What Works:** I now use just 3 tools:
- Notion for everything (yes, everything)
- Pomodoro timer (changed my life)
- Friday review ritual (15 mins weekly)

**Results:** I went from 60hr weeks to 40hrs with BETTER output.

Try just Notion first. Here's my exact setup... [continue with specifics]
'''
    
    def _humanize_generic_phrase(self, phrase: str) -> str:
        """Suggest humanized version of generic phrase"""
        replacements = {
            "it's important to note": "Here's what matters:",
            "it's worth mentioning": "Oh, and here's something most people miss:",
            "in today's digital age": "Right now,",
            "in conclusion": "Bottom line:",
            "to sum up": "Here's what it all means:",
            "leverage": "use",
            "utilize": "use",
            "implement": "start using",
            "facilitate": "make easier",
            "optimize": "improve"
        }
        return replacements.get(phrase, f"Replace with something more specific and personal")
    
    async def generate_enhanced_version(self, content: str, analysis: Dict) -> str:
        """Generate an enhanced version with humanization applied"""
        if not self.openai_client:
            return "OpenAI client not available for content generation"
        
        suggestions = analysis.get('specific_improvements', [])
        missing_elements = analysis.get('human_elements', {}).get('missing', [])
        
        prompt = f"""
You are a content humanization expert. Take this AI-generated content and make it MUCH more human and compelling.

ORIGINAL CONTENT:
{content}

MISSING HUMAN ELEMENTS:
{chr(10).join([f"- {e['element']}: {e['how_to_add']}" for e in missing_elements[:5]])}

SPECIFIC IMPROVEMENTS NEEDED:
{chr(10).join([f"- {s['issue']}: {s['suggestion']}" for s in suggestions[:3]])}

REQUIREMENTS:
1. Keep all the information but make it sound like a real person wrote it
2. Add personal stories or examples (make them realistic)
3. Use emotional language and empathy
4. Add conversational elements (questions, casual phrases)
5. Include specific numbers and examples
6. Admit mistakes or challenges
7. Use contractions and varied sentence length
8. Remove AI-sounding phrases
9. Make it engaging and relatable
10. Keep the same overall structure but improve readability

Generate the enhanced, humanized version:
"""
        
        try:
            enhanced = await self.openai_client.generate_content(prompt, max_tokens=4000, temperature=0.8)
            return enhanced
        except Exception as e:
            logger.error(f"Enhancement generation error: {e}")
            return f"Error generating enhanced version: {e}"


def format_analysis_for_display(analysis: Dict) -> str:
    """Format analysis results for readable display"""
    output = []
    
    # Overall Assessment
    output.append("=" * 80)
    output.append("📊 CONTENT ANALYSIS REPORT")
    output.append("=" * 80)
    output.append("")
    
    overall = analysis.get('overall_assessment', {})
    output.append(f"🎯 OVERALL SCORE: {overall.get('score', 0)}/100")
    output.append(f"   Pain Point Coverage: {overall.get('pain_coverage_score', 0)}/100")
    output.append(f"   Human Touch Score: {overall.get('human_score', 0)}/100")
    output.append(f"   Verdict: {overall.get('verdict', 'N/A')}")
    output.append("")
    
    # Pain Point Analysis
    output.append("-" * 80)
    output.append("💔 PAIN POINT COVERAGE")
    output.append("-" * 80)
    
    pain_analysis = analysis.get('pain_point_analysis', {})
    detailed = pain_analysis.get('detailed_coverage', [])
    
    for i, pain in enumerate(detailed, 1):
        output.append(f"\n{i}. {pain['pain_point']}")
        output.append(f"   ✓ Mentioned: {'Yes' if pain['is_mentioned'] else 'No'}")
        output.append(f"   ✓ Solution Provided: {'Yes' if pain['has_solution'] else 'No'}")
        output.append(f"   ✓ Coverage: {pain['coverage_percentage']}%")
        
        if pain.get('missing_human_touches'):
            output.append(f"   💡 Human Touches to Add:")
            for touch in pain['missing_human_touches'][:2]:
                output.append(f"      • {touch}")
    
    # Missing Human Elements
    output.append("\n" + "-" * 80)
    output.append("🚫 MISSING HUMAN ELEMENTS")
    output.append("-" * 80)
    
    missing = analysis.get('human_elements', {}).get('missing', [])
    for element in missing[:5]:
        output.append(f"\n❌ {element['element']} [{element['importance']} PRIORITY]")
        output.append(f"   Why: {element['why_it_matters']}")
        output.append(f"   How: {element['how_to_add']}")
    
    # Specific Improvements
    output.append("\n" + "-" * 80)
    output.append("✨ SPECIFIC IMPROVEMENTS")
    output.append("-" * 80)
    
    improvements = analysis.get('specific_improvements', [])
    for i, imp in enumerate(improvements, 1):
        output.append(f"\n{i}. {imp['category']} [{imp['priority']} PRIORITY]")
        output.append(f"   Issue: {imp['issue']}")
        output.append(f"   Fix: {imp['suggestion']}")
        if imp.get('example'):
            output.append(f"   Example: {imp['example'][:150]}...")
    
    # Before/After Examples
    output.append("\n" + "-" * 80)
    output.append("📝 BEFORE/AFTER EXAMPLES")
    output.append("-" * 80)
    
    examples = analysis.get('before_after_examples', [])
    for example in examples[:4]:
        output.append(f"\n{example['issue']}:")
        output.append(f"   BEFORE: {example['before']}")
        output.append(f"   AFTER: {example['after']}")
        output.append(f"   Why Better: {example['why_better']}")
    
    output.append("\n" + "=" * 80)
    
    return "\n".join(output)


# Example usage
if __name__ == "__main__":
    # Example content to analyze
    sample_content = """
# Guide to Time Management

Time management is important in today's fast-paced world. It helps you accomplish more tasks efficiently.

## Benefits of Good Time Management

Good time management provides numerous benefits:
- Increased productivity
- Better work-life balance  
- Reduced stress
- Improved decision making

## Strategies for Better Time Management

There are several strategies you can implement:

1. Prioritize tasks effectively
2. Use time-blocking techniques
3. Eliminate distractions
4. Set clear goals

It is important to note that consistency is key. Therefore, you should practice these techniques regularly.

## Conclusion

In conclusion, time management is essential for success. By implementing these strategies, you can optimize your workflow and achieve better results.
"""
    
    sample_pain_points = [
        "Difficulty prioritizing tasks when everything seems urgent",
        "Getting distracted by notifications and interruptions",
        "Feeling overwhelmed by too many commitments",
        "Not knowing how to estimate time for tasks",
        "Struggling to maintain work-life balance"
    ]
    
    # Create analyzer
    humanizer = PainPointHumanizer()
    
    # Analyze
    analysis = humanizer.analyze_content(sample_content, sample_pain_points)
    
    # Display results
    print(format_analysis_for_display(analysis))
