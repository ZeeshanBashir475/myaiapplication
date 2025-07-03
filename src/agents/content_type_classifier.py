import json
import re
from typing import Dict, List, Any, Tuple
from collections import Counter
from src.utils.llm_client import LLMClient

class ContentTypeClassifier:
    def __init__(self):
        self.llm = LLMClient()
        
        # SEO-first content classification with modern copywriting principles
        self.seo_content_types = {
            'pillar_content': {
                'description': 'Comprehensive, authoritative content that establishes topical authority',
                'seo_priority': 'high',
                'length_range': (2000, 5000),
                'keyword_strategy': 'primary_topic_cluster',
                'eeat_requirements': ['expertise', 'authoritativeness', 'trustworthiness'],
                'conversion_intent': 'awareness_to_consideration'
            },
            'cluster_content': {
                'description': 'Supporting content that links to pillar pages and targets long-tail keywords',
                'seo_priority': 'medium-high',
                'length_range': (800, 2000),
                'keyword_strategy': 'long_tail_support',
                'eeat_requirements': ['experience', 'expertise'],
                'conversion_intent': 'consideration_to_decision'
            },
            'commercial_content': {
                'description': 'Product/service-focused content optimized for commercial keywords',
                'seo_priority': 'high',
                'length_range': (1000, 3000),
                'keyword_strategy': 'commercial_intent',
                'eeat_requirements': ['experience', 'trustworthiness'],
                'conversion_intent': 'decision_to_action'
            },
            'informational_content': {
                'description': 'Educational content targeting informational search queries',
                'seo_priority': 'medium',
                'length_range': (600, 1500),
                'keyword_strategy': 'informational_intent',
                'eeat_requirements': ['expertise', 'authoritativeness'],
                'conversion_intent': 'awareness'
            },
            'comparison_content': {
                'description': 'Comparative content for users evaluating options',
                'seo_priority': 'high',
                'length_range': (1200, 2500),
                'keyword_strategy': 'comparison_keywords',
                'eeat_requirements': ['experience', 'expertise', 'trustworthiness'],
                'conversion_intent': 'consideration_to_decision'
            }
        }
        
        # Modern copywriting frameworks
        self.copywriting_frameworks = {
            'aida': ['attention', 'interest', 'desire', 'action'],
            'pas': ['problem', 'agitation', 'solution'],
            'before_after_bridge': ['before_state', 'after_state', 'bridge_solution'],
            'problem_solution_benefit': ['problem_identification', 'solution_presentation', 'benefit_emphasis'],
            'features_advantages_benefits': ['features', 'advantages', 'benefits'],
            'storytelling_arc': ['setup', 'confrontation', 'resolution']
        }
        
        # SEO optimization rules
        self.seo_optimization_rules = {
            'facebook': {
                'optimal_length': {'title': (40, 80), 'content': (100, 500)},
                'content_types': ['story', 'community', 'discussion', 'personal', 'family'],
                'engagement_factors': ['emotional', 'relatable', 'shareable', 'community-driven'],
                'format_preferences': ['long-form', 'storytelling', 'visual-text-combo'],
                'audience_behavior': ['comments', 'shares', 'reactions', 'discussions'],
                'best_for': ['personal stories', 'community building', 'detailed explanations', 'life updates'],
                'content_multipliers': {'story': 1.5, 'emotional': 1.3, 'community': 1.4, 'discussion': 1.2}
            },
        # SEO optimization rules
        self.seo_optimization_rules = {
            'title_optimization': {
                'primary_keyword_placement': 'beginning_preferred',
                'length_range': (50, 60),
                'modifiers': ['current_year', 'guide', 'best', 'complete', 'ultimate'],
                'power_words': ['proven', 'essential', 'secret', 'advanced', 'expert'],
                'emotional_triggers': ['avoid', 'mistakes', 'boost', 'increase', 'transform']
            },
            'meta_description': {
                'length_range': (150, 160),
                'include_cta': True,
                'benefit_focused': True,
                'keyword_inclusion': 'natural'
            },
            'header_structure': {
                'h1_count': 1,
                'h2_distribution': 'logical_sections',
                'keyword_variation': 'semantic_keywords',
                'user_intent_alignment': True
            },
            'content_structure': {
                'introduction_hook': 'bucket_brigade',
                'paragraph_length': 'scannable',
                'bullet_points': 'actionable',
                'conclusion_cta': 'specific_next_step'
            },
            'internal_linking': {
                'pillar_to_cluster': 'strategic',
                'cluster_to_pillar': 'contextual',
                'cross_linking': 'topic_relevance'
            }
        }
        
        # E-E-A-T optimization framework
        self.eeat_framework = {
            'experience': {
                'first_hand_evidence': ['personal_anecdotes', 'case_studies', 'original_research'],
                'proof_points': ['screenshots', 'data', 'results'],
                'authenticity_markers': ['real_examples', 'specific_details', 'honest_limitations']
            },
            'expertise': {
                'depth_indicators': ['comprehensive_coverage', 'technical_accuracy', 'industry_insights'],
                'credential_display': ['author_bio', 'qualifications', 'certifications'],
                'knowledge_demonstration': ['advanced_concepts', 'nuanced_understanding', 'original_insights']
            },
            'authoritativeness': {
                'reputation_signals': ['backlinks', 'citations', 'media_mentions'],
                'industry_recognition': ['awards', 'speaking', 'publications'],
                'thought_leadership': ['original_frameworks', 'industry_predictions', 'innovative_approaches']
            },
            'trustworthiness': {
                'transparency': ['sources_cited', 'update_dates', 'author_disclosure'],
                'accuracy': ['fact_checking', 'current_information', 'balanced_perspective'],
                'user_safety': ['secure_site', 'privacy_policy', 'contact_information']
            }
        }
        
        # Content performance indicators
        self.performance_indicators = {
            'seo_signals': ['organic_traffic', 'keyword_rankings', 'featured_snippets', 'backlinks'],
            'user_engagement': ['time_on_page', 'bounce_rate', 'scroll_depth', 'return_visits'],
            'conversion_metrics': ['lead_generation', 'email_signups', 'product_inquiries', 'sales']
        }
        
        # Social media as secondary consideration
        self.social_amplification = {
            'shareability_factors': ['emotional_resonance', 'practical_value', 'surprising_insights'],
            'platform_optimization': {
                'linkedin': 'professional_insights',
                'twitter': 'key_takeaways',
                'facebook': 'community_discussion'
            }
        }
        
        # Content type patterns
        self.content_patterns = {
            'how-to': {
                'indicators': ['how to', 'step by step', 'tutorial', 'guide', 'instructions'],
                'platforms': {'youtube': 9, 'tiktok': 8, 'instagram': 7, 'facebook': 6, 'linkedin': 5, 'twitter': 4}
            },
            'story': {
                'indicators': ['story', 'experience', 'happened', 'journey', 'personal'],
                'platforms': {'facebook': 9, 'instagram': 8, 'linkedin': 7, 'twitter': 6, 'tiktok': 5}
            },
            'tips': {
                'indicators': ['tips', 'advice', 'hacks', 'tricks', 'secrets'],
                'platforms': {'instagram': 8, 'twitter': 8, 'tiktok': 9, 'facebook': 7, 'linkedin': 6}
            },
            'opinion': {
                'indicators': ['opinion', 'think', 'believe', 'perspective', 'hot take'],
                'platforms': {'twitter': 9, 'linkedin': 8, 'facebook': 7, 'instagram': 5, 'tiktok': 6}
            },
            'news': {
                'indicators': ['news', 'update', 'breaking', 'announcement', 'latest'],
                'platforms': {'twitter': 10, 'linkedin': 8, 'facebook': 7, 'instagram': 5, 'tiktok': 4}
            },
            'educational': {
                'indicators': ['learn', 'education', 'explain', 'understand', 'knowledge'],
                'platforms': {'linkedin': 9, 'youtube': 8, 'facebook': 7, 'instagram': 6, 'tiktok': 8, 'twitter': 5}
            },
            'entertainment': {
                'indicators': ['funny', 'hilarious', 'entertaining', 'fun', 'amusing'],
                'platforms': {'tiktok': 10, 'instagram': 8, 'facebook': 7, 'twitter': 6, 'linkedin': 3}
            },
            'inspirational': {
                'indicators': ['inspire', 'motivate', 'motivation', 'success', 'achievement'],
                'platforms': {'instagram': 9, 'linkedin': 8, 'facebook': 7, 'twitter': 6, 'tiktok': 7}
            },
            'question': {
                'indicators': ['?', 'question', 'ask', 'wondering', 'curious'],
                'platforms': {'facebook': 8, 'twitter': 8, 'instagram': 7, 'linkedin': 6, 'tiktok': 5}
            },
            'review': {
                'indicators': ['review', 'rating', 'opinion', 'pros and cons', 'evaluation'],
                'platforms': {'youtube': 9, 'instagram': 7, 'facebook': 7, 'twitter': 6, 'linkedin': 5, 'tiktok': 6}
            }
        }
        
        # Industry-specific platform preferences
        self.industry_preferences = {
            'technology': {'linkedin': 1.3, 'twitter': 1.2, 'facebook': 1.0, 'instagram': 0.9, 'tiktok': 0.8},
            'fashion': {'instagram': 1.5, 'tiktok': 1.4, 'facebook': 1.1, 'twitter': 0.9, 'linkedin': 0.7},
            'food': {'instagram': 1.4, 'tiktok': 1.3, 'facebook': 1.2, 'twitter': 1.0, 'linkedin': 0.8},
            'business': {'linkedin': 1.5, 'twitter': 1.2, 'facebook': 1.1, 'instagram': 0.9, 'tiktok': 0.7},
            'health': {'instagram': 1.3, 'facebook': 1.2, 'tiktok': 1.1, 'twitter': 1.0, 'linkedin': 0.9},
            'education': {'linkedin': 1.3, 'facebook': 1.2, 'instagram': 1.1, 'tiktok': 1.2, 'twitter': 1.0},
            'entertainment': {'tiktok': 1.6, 'instagram': 1.4, 'facebook': 1.2, 'twitter': 1.1, 'linkedin': 0.6},
            'finance': {'linkedin': 1.4, 'twitter': 1.3, 'facebook': 1.1, 'instagram': 0.9, 'tiktok': 0.8},
            'lifestyle': {'instagram': 1.5, 'facebook': 1.3, 'tiktok': 1.2, 'twitter': 1.0, 'linkedin': 0.8},
            'news': {'twitter': 1.5, 'facebook': 1.3, 'linkedin': 1.2, 'instagram': 1.0, 'tiktok': 0.9}
        }
    
    def classify_and_optimize_content(self, title: str, content: str, topic: str, 
                                    target_keywords: List[str], industry: str = None, 
                                    target_audience: str = None, business_goals: List[str] = None,
                                    reddit_insights: Dict = None) -> Dict[str, Any]:
        """
        Classify content type and provide SEO optimization recommendations with modern copywriting principles
        """
        
        print(f"🔍 Analyzing content for SEO optimization: {title[:50]}...")
        
        # Core content analysis
        content_analysis = self._analyze_content_for_seo(title, content, topic, target_keywords)
        
        # Determine optimal content type for SEO
        content_type = self._classify_seo_content_type(content_analysis, business_goals)
        
        # E-E-A-T assessment
        eeat_analysis = self._assess_eeat_potential(content_analysis, industry, content_type)
        
        # SEO optimization recommendations
        seo_optimization = self._generate_seo_optimization_plan(
            title, content, content_analysis, content_type, target_keywords
        )
        
        # Modern copywriting enhancement
        copywriting_optimization = self._apply_copywriting_frameworks(
            content_analysis, content_type, target_audience, reddit_insights
        )
        
        # Performance prediction
        performance_prediction = self._predict_seo_performance(
            content_analysis, content_type, eeat_analysis, seo_optimization
        )
        
        # Content enhancement strategy
        enhancement_strategy = self._create_enhancement_strategy(
            content_type, seo_optimization, copywriting_optimization, eeat_analysis
        )
        
        # Social media as secondary consideration
        social_potential = self._assess_social_amplification_potential(content_analysis, content_type)
        
        return {
            'content_classification': {
                'primary_type': content_type['primary'],
                'seo_priority': content_type['seo_priority'],
                'content_purpose': content_type['purpose'],
                'target_funnel_stage': content_type['funnel_stage']
            },
            'seo_optimization': {
                'title_optimization': seo_optimization['title'],
                'meta_description': seo_optimization['meta_description'],
                'header_structure': seo_optimization['headers'],
                'content_structure': seo_optimization['structure'],
                'keyword_optimization': seo_optimization['keywords'],
                'internal_linking': seo_optimization['internal_links']
            },
            'copywriting_enhancement': {
                'recommended_framework': copywriting_optimization['framework'],
                'hook_optimization': copywriting_optimization['hooks'],
                'storytelling_elements': copywriting_optimization['storytelling'],
                'conversion_optimization': copywriting_optimization['conversion'],
                'emotional_triggers': copywriting_optimization['emotional_triggers']
            },
            'eeat_optimization': {
                'current_assessment': eeat_analysis['current_score'],
                'improvement_areas': eeat_analysis['gaps'],
                'enhancement_strategies': eeat_analysis['strategies'],
                'credibility_signals': eeat_analysis['credibility_signals']
            },
            'performance_prediction': {
                'seo_potential': performance_prediction['seo_score'],
                'conversion_potential': performance_prediction['conversion_score'],
                'engagement_prediction': performance_prediction['engagement_score'],
                'competitive_advantage': performance_prediction['competitive_edge']
            },
            'enhancement_strategy': enhancement_strategy,
            'social_amplification': social_potential  # Secondary consideration
        }
    
    def _analyze_content_for_seo(self, title: str, content: str, topic: str, 
                               target_keywords: List[str]) -> Dict[str, Any]:
        """Analyze content characteristics for SEO optimization"""
        
        combined_text = f"{title} {content}".lower()
        
        analysis = {
            'content_metrics': {
                'word_count': len(content.split()),
                'reading_time': len(content.split()) / 200,  # Average reading speed
                'readability_score': self._calculate_readability_score(content),
                'content_depth': self._assess_content_depth(content),
                'uniqueness_score': self._assess_content_uniqueness(content, topic)
            },
            'keyword_analysis': {
                'primary_keyword_density': self._calculate_keyword_density(combined_text, target_keywords[0] if target_keywords else topic),
                'keyword_distribution': self._analyze_keyword_distribution(combined_text, target_keywords),
                'semantic_keyword_coverage': self._assess_semantic_coverage(combined_text, topic),
                'keyword_stuffing_risk': self._assess_keyword_stuffing_risk(combined_text, target_keywords)
            },
            'content_structure': {
                'has_clear_introduction': self._has_clear_intro(content),
                'logical_flow': self._assess_logical_flow(content),
                'scannable_format': self._assess_scannability(content),
                'conclusion_strength': self._assess_conclusion_strength(content),
                'call_to_action_presence': self._has_effective_cta(content)
            },
            'search_intent_alignment': {
                'informational_signals': self._count_informational_signals(combined_text),
                'commercial_signals': self._count_commercial_signals(combined_text),
                'navigational_signals': self._count_navigational_signals(combined_text),
                'transactional_signals': self._count_transactional_signals(combined_text),
                'primary_intent': self._determine_primary_search_intent(combined_text)
            },
            'content_quality_indicators': {
                'original_insights': self._count_original_insights(content),
                'actionable_advice': self._count_actionable_elements(content),
                'expert_signals': self._count_expert_signals(content),
                'evidence_based': self._count_evidence_citations(content),
                'comprehensive_coverage': self._assess_topic_comprehensiveness(content, topic)
            },
            'user_experience_factors': {
                'engagement_hooks': self._count_engagement_hooks(content),
                'bucket_brigades': self._count_bucket_brigades(content),
                'storytelling_elements': self._count_storytelling_elements(content),
                'emotional_resonance': self._assess_emotional_resonance(content),
                'practical_value': self._assess_practical_value(content)
            }
        }
        
        return analysis
    
    def _classify_seo_content_type(self, content_analysis: Dict, business_goals: List[str]) -> Dict[str, Any]:
        """Classify content type based on SEO and business objectives"""
        
        # Score each content type based on analysis
        type_scores = {}
        
        for content_type, characteristics in self.seo_content_types.items():
            score = 0
            
            # Word count alignment
            word_count = content_analysis['content_metrics']['word_count']
            min_words, max_words = characteristics['length_range']
            
            if min_words <= word_count <= max_words:
                score += 3
            elif word_count >= min_words * 0.8:  # Close to range
                score += 2
            elif word_count >= max_words * 1.2:  # Longer than expected
                score += 1
            
            # Search intent alignment
            primary_intent = content_analysis['search_intent_alignment']['primary_intent']
            
            if content_type == 'commercial_content' and primary_intent in ['commercial', 'transactional']:
                score += 4
            elif content_type == 'informational_content' and primary_intent == 'informational':
                score += 4
            elif content_type == 'comparison_content' and 'comparison' in primary_intent:
                score += 4
            elif content_type == 'pillar_content' and content_analysis['content_quality_indicators']['comprehensive_coverage'] > 0.7:
                score += 4
            elif content_type == 'cluster_content' and content_analysis['content_quality_indicators']['comprehensive_coverage'] < 0.7:
                score += 3
            
            # Content depth and quality
            content_depth = content_analysis['content_metrics']['content_depth']
            if content_type in ['pillar_content', 'commercial_content'] and content_depth > 0.7:
                score += 2
            elif content_type in ['cluster_content', 'informational_content'] and content_depth > 0.5:
                score += 2
            
            # Business goal alignment
            if business_goals:
                if 'lead_generation' in business_goals and content_type == 'commercial_content':
                    score += 2
                elif 'brand_awareness' in business_goals and content_type == 'pillar_content':
                    score += 2
                elif 'seo_traffic' in business_goals and content_type in ['cluster_content', 'informational_content']:
                    score += 2
            
            # Actionability and practical value
            actionable_score = content_analysis['content_quality_indicators']['actionable_advice']
            if actionable_score > 0.6:
                score += 1
            
            type_scores[content_type] = score
        
        # Determine primary content type
        primary_type = max(type_scores, key=type_scores.get)
        confidence = type_scores[primary_type] / sum(type_scores.values()) if sum(type_scores.values()) > 0 else 0.5
        
        # Determine SEO priority and funnel stage
        seo_priority = self.seo_content_types[primary_type]['seo_priority']
        funnel_stage = self.seo_content_types[primary_type]['conversion_intent']
        
        return {
            'primary': primary_type,
            'confidence': round(confidence, 2),
            'seo_priority': seo_priority,
            'purpose': self.seo_content_types[primary_type]['description'],
            'funnel_stage': funnel_stage,
            'type_scores': type_scores,
            'recommended_length': self.seo_content_types[primary_type]['length_range'],
            'keyword_strategy': self.seo_content_types[primary_type]['keyword_strategy'],
            'eeat_focus': self.seo_content_types[primary_type]['eeat_requirements']
        }
    
    def _assess_eeat_potential(self, content_analysis: Dict, industry: str, content_type: Dict) -> Dict[str, Any]:
        """Assess E-E-A-T potential and provide improvement recommendations"""
        
        eeat_scores = {
            'experience': 0,
            'expertise': 0, 
            'authoritativeness': 0,
            'trustworthiness': 0
        }
        
        # Experience assessment
        experience_indicators = [
            content_analysis['content_quality_indicators']['original_insights'],
            content_analysis['user_experience_factors']['storytelling_elements'],
            content_analysis['content_quality_indicators']['evidence_based']
        ]
        eeat_scores['experience'] = min(10, sum(experience_indicators) * 2)
        
        # Expertise assessment  
        expertise_indicators = [
            content_analysis['content_metrics']['content_depth'],
            content_analysis['content_quality_indicators']['expert_signals'],
            content_analysis['content_quality_indicators']['comprehensive_coverage']
        ]
        eeat_scores['expertise'] = min(10, sum(indicator * 3.33 for indicator in expertise_indicators))
        
        # Authoritativeness assessment
        authority_indicators = [
            content_analysis['content_quality_indicators']['original_insights'],
            content_analysis['content_metrics']['uniqueness_score'],
            content_analysis['content_quality_indicators']['comprehensive_coverage']
        ]
        eeat_scores['authoritativeness'] = min(10, sum(indicator * 3.33 for indicator in authority_indicators))
        
        # Trustworthiness assessment (most important)
        trust_indicators = [
            content_analysis['content_quality_indicators']['evidence_based'],
            content_analysis['content_structure']['logical_flow'],
            content_analysis['content_metrics']['readability_score']
        ]
        eeat_scores['trustworthiness'] = min(10, sum(indicator * 3.33 for indicator in trust_indicators))
        
        # Overall E-E-A-T score (Trust weighted higher)
        overall_score = (
            eeat_scores['experience'] * 0.2 +
            eeat_scores['expertise'] * 0.25 +  
            eeat_scores['authoritativeness'] * 0.25 +
            eeat_scores['trustworthiness'] * 0.3
        )
        
        # YMYL topics need higher standards
        is_ymyl = self._is_ymyl_topic(industry)
        if is_ymyl:
            overall_score *= 0.8  # Higher standards for YMYL
        
        # Identify improvement areas
        improvement_areas = []
        for component, score in eeat_scores.items():
            if score < 7:
                improvement_areas.append(component)
        
        # Generate specific strategies
        strategies = self._generate_eeat_strategies(eeat_scores, content_type, is_ymyl)
        
        return {
            'current_score': round(overall_score, 1),
            'component_scores': {k: round(v, 1) for k, v in eeat_scores.items()},
            'gaps': improvement_areas,
            'strategies': strategies,
            'is_ymyl': is_ymyl,
            'credibility_signals': self._identify_credibility_signals(content_analysis),
            'improvement_potential': round(10 - overall_score, 1)
        }
    
    def _generate_seo_optimization_plan(self, title: str, content: str, analysis: Dict, 
                                      content_type: Dict, target_keywords: List[str]) -> Dict[str, Any]:
        """Generate comprehensive SEO optimization recommendations"""
        
        primary_keyword = target_keywords[0] if target_keywords else content_type['primary']
        
        optimization_plan = {
            'title': self._optimize_title_for_seo(title, primary_keyword, content_type),
            'meta_description': self._generate_meta_description(title, content, primary_keyword),
            'headers': self._optimize_header_structure(content, target_keywords),
            'structure': self._optimize_content_structure(content, analysis, content_type),
            'keywords': self._optimize_keyword_usage(content, target_keywords, analysis),
            'internal_links': self._suggest_internal_linking_strategy(content_type, target_keywords)
        }
        
        return optimization_plan
    
    def _optimize_title_for_seo(self, title: str, primary_keyword: str, content_type: Dict) -> Dict[str, Any]:
        """Optimize title for SEO performance"""
        
        current_length = len(title)
        optimal_range = self.seo_optimization_rules['title_optimization']['length_range']
        
        recommendations = []
        optimized_variants = []
        
        # Length optimization
        if current_length < optimal_range[0]:
            recommendations.append(f"Expand title (current: {current_length}, optimal: {optimal_range[0]}-{optimal_range[1]})")
        elif current_length > optimal_range[1]:
            recommendations.append(f"Shorten title (current: {current_length}, optimal: {optimal_range[0]}-{optimal_range[1]})")
        
        # Keyword placement
        if not title.lower().startswith(primary_keyword.lower()[:10]):
            recommendations.append("Move primary keyword closer to the beginning")
        
        # Power words and modifiers
        power_words = self.seo_optimization_rules['title_optimization']['power_words']
        modifiers = self.seo_optimization_rules['title_optimization']['modifiers']
        
        # Generate optimized variants
        if content_type['primary'] == 'pillar_content':
            optimized_variants = [
                f"The Complete {primary_keyword} Guide for 2025",
                f"Ultimate {primary_keyword} Strategy: Expert Guide",
                f"{primary_keyword}: The Definitive Guide"
            ]
        elif content_type['primary'] == 'commercial_content':
            optimized_variants = [
                f"Best {primary_keyword} Solutions in 2025",
                f"{primary_keyword} Reviews: Top Picks & Comparisons",
                f"How to Choose the Right {primary_keyword}"
            ]
        elif content_type['primary'] == 'informational_content':
            optimized_variants = [
                f"What is {primary_keyword}? Complete Explanation",
                f"{primary_keyword} Explained: Essential Guide",
                f"Understanding {primary_keyword}: Key Facts"
            ]
        
        return {
            'current_analysis': {
                'length': current_length,
                'keyword_placement': 'beginning' if title.lower().startswith(primary_keyword.lower()[:10]) else 'middle/end',
                'power_words_used': [word for word in power_words if word in title.lower()]
            },
            'recommendations': recommendations,
            'optimized_variants': optimized_variants,
            'seo_score': self._calculate_title_seo_score(title, primary_keyword)
        }
    
    # Core analysis helper methods
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score using simplified Flesch formula"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return 0.5
        
        avg_sentence_length = words / sentences
        
        # Simplified readability score (0-1, higher is better)
        if avg_sentence_length <= 15:
            return 0.9  # Very readable
        elif avg_sentence_length <= 20:
            return 0.7  # Good readability
        elif avg_sentence_length <= 25:
            return 0.5  # Average readability
        else:
            return 0.3  # Poor readability
    
    def _assess_content_depth(self, content: str) -> float:
        """Assess the depth and comprehensiveness of content"""
        depth_indicators = [
            'because', 'therefore', 'however', 'furthermore', 'moreover',
            'specifically', 'for example', 'such as', 'in other words',
            'research shows', 'studies indicate', 'according to'
        ]
        
        depth_score = sum(1 for indicator in depth_indicators if indicator in content.lower())
        word_count = len(content.split())
        
        # Normalize based on content length
        normalized_score = min(1.0, (depth_score / max(word_count / 100, 1)))
        
        return normalized_score
    
    def _assess_content_uniqueness(self, content: str, topic: str) -> float:
        """Assess content uniqueness and originality"""
        uniqueness_indicators = [
            'in my experience', 'i found', 'our research', 'case study',
            'exclusive', 'original', 'unique', 'never before',
            'first time', 'breakthrough', 'innovative'
        ]
        
        uniqueness_count = sum(1 for indicator in uniqueness_indicators if indicator in content.lower())
        
        # Check for specific examples and data
        has_specific_data = bool(re.search(r'\d+%', content))
        has_examples = 'for example' in content.lower() or 'such as' in content.lower()
        
        base_score = min(1.0, uniqueness_count * 0.1)
        
        if has_specific_data:
            base_score += 0.2
        if has_examples:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _calculate_keyword_density(self, text: str, keyword: str) -> float:
        """Calculate keyword density"""
        words = text.split()
        keyword_count = text.lower().count(keyword.lower())
        
        if len(words) == 0:
            return 0
        
        density = (keyword_count / len(words)) * 100
        return round(density, 2)
    
    def _analyze_keyword_distribution(self, text: str, keywords: List[str]) -> Dict[str, float]:
        """Analyze distribution of target keywords"""
        distribution = {}
        
        for keyword in keywords:
            density = self._calculate_keyword_density(text, keyword)
            distribution[keyword] = density
        
        return distribution
    
    def _assess_semantic_coverage(self, text: str, topic: str) -> float:
        """Assess semantic keyword coverage"""
        semantic_indicators = [
            'what is', 'how to', 'why', 'when', 'where',
            'benefits', 'advantages', 'disadvantages', 'pros', 'cons',
            'types', 'kinds', 'examples', 'tips', 'strategies'
        ]
        
        coverage_count = sum(1 for indicator in semantic_indicators if indicator in text.lower())
        
        # Normalize to 0-1 scale
        return min(1.0, coverage_count / len(semantic_indicators))
    
    def _determine_primary_search_intent(self, text: str) -> str:
        """Determine primary search intent from content"""
        
        intent_scores = {
            'informational': 0,
            'commercial': 0,
            'transactional': 0,
            'navigational': 0
        }
        
        # Informational signals
        info_signals = ['what is', 'how to', 'guide', 'tutorial', 'learn', 'understand', 'explain']
        intent_scores['informational'] = sum(1 for signal in info_signals if signal in text)
        
        # Commercial signals  
        commercial_signals = ['best', 'top', 'review', 'comparison', 'vs', 'versus', 'alternative']
        intent_scores['commercial'] = sum(1 for signal in commercial_signals if signal in text)
        
        # Transactional signals
        transactional_signals = ['buy', 'purchase', 'price', 'cost', 'discount', 'deal', 'order']
        intent_scores['transactional'] = sum(1 for signal in transactional_signals if signal in text)
        
        # Navigational signals
        nav_signals = ['login', 'sign up', 'contact', 'about', 'homepage']
        intent_scores['navigational'] = sum(1 for signal in nav_signals if signal in text)
        
        return max(intent_scores, key=intent_scores.get) if any(intent_scores.values()) else 'informational'
    
    def _count_engagement_hooks(self, content: str) -> float:
        """Count engagement hooks in content"""
        hooks = [
            "here's the deal:", "here's what happened:", "but here's the thing:",
            "want to know the secret?", "here's the truth:", "the bottom line:",
            "here's why:", "the result?", "what happened next?"
        ]
        
        hook_count = sum(1 for hook in hooks if hook in content.lower())
        
        # Normalize based on content length
        words = len(content.split())
        normalized_score = min(1.0, hook_count / max(words / 200, 1))
        
        return normalized_score
    
    def _count_bucket_brigades(self, content: str) -> float:
        """Count bucket brigades (engagement elements)"""
        bucket_brigades = [
            "here's the deal:", "here's what:", "but here's the kicker:",
            "want to know the best part?", "it gets better:", "here's why:",
            "the truth is:", "here's the thing:", "but wait, there's more:"
        ]
        
        count = sum(1 for brigade in bucket_brigades if brigade in content.lower())
        
        # Normalize score
        return min(1.0, count * 0.2)
    
    def _is_ymyl_topic(self, industry: str) -> bool:
        """Determine if topic/industry is YMYL (Your Money or Your Life)"""
        ymyl_industries = [
            'finance', 'health', 'medical', 'legal', 'investment', 'insurance',
            'banking', 'cryptocurrency', 'tax', 'retirement', 'healthcare',
            'pharmaceutical', 'nutrition', 'diet', 'safety', 'government'
        ]
        
        if not industry:
            return False
            
        return any(ymyl in industry.lower() for ymyl in ymyl_industries)
    
    def _generate_eeat_strategies(self, scores: Dict[str, float], content_type: Dict, is_ymyl: bool) -> List[str]:
        """Generate specific E-E-A-T improvement strategies"""
        strategies = []
        
        # Experience strategies
        if scores['experience'] < 7:
            strategies.extend([
                "Add personal anecdotes and first-hand experiences",
                "Include specific examples from real situations",
                "Share case studies or real-world applications",
                "Add behind-the-scenes insights"
            ])
        
        # Expertise strategies  
        if scores['expertise'] < 7:
            strategies.extend([
                "Cite authoritative sources and research",
                "Include technical details and advanced concepts",
                "Add expert quotes and industry insights",
                "Demonstrate deep knowledge of the topic"
            ])
        
        # Authoritativeness strategies
        if scores['authoritativeness'] < 7:
            strategies.extend([
                "Build topical authority with comprehensive coverage",
                "Create original frameworks and methodologies",
                "Establish thought leadership in the industry",
                "Earn backlinks from authoritative sources"
            ])
        
        # Trustworthiness strategies (most important)
        if scores['trustworthiness'] < 7:
            strategies.extend([
                "Add clear author bio and credentials",
                "Include publication and update dates",
                "Cite reputable sources with links",
                "Provide balanced perspectives on controversial topics"
            ])
        
        # YMYL-specific strategies
        if is_ymyl:
            strategies.extend([
                "Add appropriate disclaimers for YMYL content",
                "Ensure all medical/financial claims are backed by evidence",
                "Include expert review or fact-checking",
                "Provide clear contact information and credentials"
            ])
        
        return strategies
    
    def _calculate_title_seo_score(self, title: str, primary_keyword: str) -> float:
        """Calculate SEO score for title"""
        score = 0
        
        # Keyword placement (higher score for beginning)
        if title.lower().startswith(primary_keyword.lower()):
            score += 3
        elif primary_keyword.lower() in title.lower()[:len(title)//2]:
            score += 2
        elif primary_keyword.lower() in title.lower():
            score += 1
        
        # Length optimization
        title_length = len(title)
        if 50 <= title_length <= 60:
            score += 2
        elif 40 <= title_length <= 70:
            score += 1
        
        # Power words presence
        power_words = ['guide', 'complete', 'ultimate', 'best', 'top', 'proven', 'secret']
        power_word_count = sum(1 for word in power_words if word in title.lower())
        score += min(2, power_word_count)
        
        # Emotional triggers
        emotional_words = ['boost', 'increase', 'improve', 'transform', 'master', 'avoid']
        emotional_count = sum(1 for word in emotional_words if word in title.lower())
        score += min(1, emotional_count)
        
        return min(10, score)
    
    def _apply_copywriting_frameworks(self, content_analysis: Dict, content_type: Dict, 
                                    target_audience: str, reddit_insights: Dict) -> Dict[str, Any]:
        """Apply modern copywriting frameworks for optimization"""
        
        # Determine best framework based on content type and analysis
        recommended_framework = self._select_optimal_framework(content_type, content_analysis)
        
        # Generate hooks based on framework
        hooks = self._generate_framework_hooks(recommended_framework, content_analysis, reddit_insights)
        
        # Storytelling elements
        storytelling = self._enhance_storytelling_elements(content_analysis, reddit_insights)
        
        # Conversion optimization
        conversion = self._optimize_for_conversion(content_type, content_analysis)
        
        # Emotional triggers
        emotional_triggers = self._identify_emotional_triggers(content_analysis, reddit_insights)
        
        return {
            'framework': recommended_framework,
            'hooks': hooks,
            'storytelling': storytelling,
            'conversion': conversion,
            'emotional_triggers': emotional_triggers,
            'implementation_guide': self._create_framework_implementation_guide(recommended_framework)
        }
    
    def _select_optimal_framework(self, content_type: Dict, analysis: Dict) -> str:
        """Select the best copywriting framework for the content"""
        
        primary_intent = analysis['search_intent_alignment']['primary_intent']
        content_purpose = content_type['primary']
        
        # Framework selection logic
        if content_purpose == 'commercial_content' and primary_intent in ['commercial', 'transactional']:
            return 'problem_solution_benefit'
        elif content_purpose == 'pillar_content':
            return 'before_after_bridge'
        elif primary_intent == 'informational':
            return 'features_advantages_benefits'
        elif analysis['user_experience_factors']['storytelling_elements'] > 0.5:
            return 'storytelling_arc'
        elif analysis['content_quality_indicators']['actionable_advice'] > 0.6:
            return 'pas'  # Problem-Agitation-Solution
        else:
            return 'aida'  # Attention-Interest-Desire-Action
    
    def _predict_seo_performance(self, content_analysis: Dict, content_type: Dict, 
                               eeat_analysis: Dict, seo_optimization: Dict) -> Dict[str, Any]:
        """Predict SEO performance based on analysis"""
        
        # Calculate component scores
        content_quality_score = self._calculate_content_quality_score(content_analysis)
        technical_seo_score = self._calculate_technical_seo_score(seo_optimization)
        eeat_score = eeat_analysis['current_score']
        
        # Weighted overall SEO score
        seo_score = (
            content_quality_score * 0.4 +
            technical_seo_score * 0.3 +
            eeat_score * 0.3
        )
        
        # Conversion potential based on content type and call-to-actions
        conversion_score = self._calculate_conversion_potential(content_type, content_analysis)
        
        # Engagement prediction based on user experience factors
        engagement_score = self._calculate_engagement_potential(content_analysis)
        
        # Competitive advantage assessment
        competitive_edge = self._assess_competitive_advantage(content_analysis, eeat_analysis)
        
        return {
            'seo_score': round(seo_score, 1),
            'conversion_score': round(conversion_score, 1),
            'engagement_score': round(engagement_score, 1),
            'competitive_edge': competitive_edge,
            'performance_tier': self._determine_performance_tier(seo_score),
            'expected_outcomes': self._generate_performance_expectations(seo_score, conversion_score),
            'timeline_to_results': self._estimate_results_timeline(seo_score, content_type)
        }
    
    def _create_enhancement_strategy(self, content_type: Dict, seo_optimization: Dict, 
                                   copywriting_optimization: Dict, eeat_analysis: Dict) -> Dict[str, Any]:
        """Create comprehensive content enhancement strategy"""
        
        strategy = {
            'immediate_actions': [],
            'short_term_improvements': [],
            'long_term_strategy': [],
            'priority_level': 'medium'
        }
        
        # Immediate SEO fixes
        if seo_optimization['title']['seo_score'] < 7:
            strategy['immediate_actions'].append("Optimize title for primary keyword and length")
        
        if any(score < 2 for score in seo_optimization['keywords']['distribution'].values()):
            strategy['immediate_actions'].append("Improve keyword distribution throughout content")
        
        # E-E-A-T improvements
        if eeat_analysis['current_score'] < 7:
            strategy['short_term_improvements'].extend([
                "Add author bio and credentials",
                "Include authoritative sources and citations",
                "Add publication date and update schedule"
            ])
        
        # Content quality enhancements
        content_depth = eeat_analysis['component_scores']['expertise']
        if content_depth < 7:
            strategy['short_term_improvements'].append("Increase content depth and comprehensiveness")
        
        # Long-term authority building
        if content_type['seo_priority'] == 'high':
            strategy['long_term_strategy'].extend([
                "Build topical authority through content clusters",
                "Establish thought leadership in the industry",
                "Create linkable assets and original research"
            ])
        
        # Determine priority
        if eeat_analysis['current_score'] < 5 or seo_optimization['title']['seo_score'] < 5:
            strategy['priority_level'] = 'critical'
        elif eeat_analysis['current_score'] < 7:
            strategy['priority_level'] = 'high'
        
        strategy['success_metrics'] = self._define_enhancement_success_metrics(content_type)
        strategy['implementation_timeline'] = self._create_implementation_timeline(strategy)
        
        return strategy
    
    def _assess_social_amplification_potential(self, content_analysis: Dict, content_type: Dict) -> Dict[str, Any]:
        """Assess potential for social media amplification (secondary consideration)"""
        
        shareability = content_analysis['user_experience_factors']['practical_value']
        emotional_appeal = content_analysis['user_experience_factors']['emotional_resonance']
        
        social_score = (shareability + emotional_appeal) / 2
        
        # Platform-specific recommendations (simplified for SEO focus)
        platform_fit = {
            'linkedin': 'high' if content_type['primary'] in ['pillar_content', 'commercial_content'] else 'medium',
            'twitter': 'high' if content_analysis['content_metrics']['word_count'] < 1000 else 'medium',
            'facebook': 'medium'  # General sharing potential
        }
        
        return {
            'overall_potential': 'high' if social_score > 0.7 else 'medium' if social_score > 0.4 else 'low',
            'platform_recommendations': platform_fit,
            'shareability_factors': self._identify_shareability_factors(content_analysis),
            'optimization_tips': [
                "Create quotable snippets for social sharing",
                "Design visual assets to accompany content",
                "Add social sharing buttons and CTAs"
            ]
        }
    
    # Additional helper methods
    def _calculate_content_quality_score(self, analysis: Dict) -> float:
        """Calculate overall content quality score"""
        
        factors = [
            analysis['content_metrics']['content_depth'],
            analysis['content_metrics']['uniqueness_score'],
            analysis['content_quality_indicators']['actionable_advice'],
            analysis['content_quality_indicators']['comprehensive_coverage'],
            analysis['content_structure']['logical_flow']
        ]
        
        return sum(factors) / len(factors) * 10
    
    def _calculate_technical_seo_score(self, seo_optimization: Dict) -> float:
        """Calculate technical SEO score"""
        
        title_score = seo_optimization['title']['seo_score']
        
        # Simplified scoring for other factors
        keyword_score = 7  # Would be calculated from keyword optimization
        structure_score = 8  # Would be calculated from content structure
        
        return (title_score + keyword_score + structure_score) / 3
    
    def _determine_performance_tier(self, seo_score: float) -> str:
        """Determine performance tier based on SEO score"""
        
        if seo_score >= 8.5:
            return 'excellent'
        elif seo_score >= 7.0:
            return 'good'
        elif seo_score >= 5.5:
            return 'average'
        else:
            return 'needs_improvement'
    
    def _generate_performance_expectations(self, seo_score: float, conversion_score: float) -> List[str]:
        """Generate expected performance outcomes"""
        
        expectations = []
        
        if seo_score >= 8:
            expectations.append("High potential for first page rankings")
            expectations.append("Strong organic traffic growth expected")
        elif seo_score >= 6:
            expectations.append("Good ranking potential with optimization")
            expectations.append("Steady organic traffic increase")
        else:
            expectations.append("Requires significant optimization for ranking success")
        
        if conversion_score >= 7:
            expectations.append("High conversion potential")
        elif conversion_score >= 5:
            expectations.append("Moderate conversion potential")
        
        return expectations
    
    def _estimate_results_timeline(self, seo_score: float, content_type: Dict) -> str:
        """Estimate timeline for SEO results"""
        
        if seo_score >= 8:
            return "2-4 weeks for initial results, 2-3 months for full impact"
        elif seo_score >= 6:
            return "4-8 weeks for initial results, 3-6 months for full impact"
        else:
            return "8-12 weeks for initial results after optimization, 6+ months for significant impact"
    
    # Simplified placeholder methods for methods referenced but not fully implemented
    def _has_clear_intro(self, content: str) -> float:
        """Check if content has clear introduction"""
        intro_words = content[:200].lower()
        intro_indicators = ['in this', 'this article', 'this guide', 'you will learn', 'we will cover']
        return 0.8 if any(indicator in intro_words for indicator in intro_indicators) else 0.3
    
    def _assess_logical_flow(self, content: str) -> float:
        """Assess logical flow of content"""
        transition_words = ['however', 'therefore', 'furthermore', 'in addition', 'next', 'finally']
        transition_count = sum(1 for word in transition_words if word in content.lower())
        return min(1.0, transition_count / 5)
    
    def _assess_scannability(self, content: str) -> float:
        """Assess how scannable the content is"""
        bullet_points = content.count('•') + content.count('-')
        numbered_lists = len(re.findall(r'\d+\.', content))
        headers = content.count('#')
        
        scannability_score = (bullet_points + numbered_lists + headers) / max(len(content.split()) / 100, 1)
        return min(1.0, scannability_score)
    
    def _assess_conclusion_strength(self, content: str) -> float:
        """Assess strength of conclusion"""
        conclusion_words = content[-200:].lower()
        conclusion_indicators = ['in conclusion', 'to summarize', 'final thoughts', 'takeaway', 'next steps']
        return 0.8 if any(indicator in conclusion_words for indicator in conclusion_indicators) else 0.4
    
    def _has_effective_cta(self, content: str) -> float:
        """Check for effective call-to-action"""
        cta_words = ['contact', 'get started', 'learn more', 'download', 'subscribe', 'try', 'sign up']
        return 0.8 if any(word in content.lower() for word in cta_words) else 0.2
    
    def _create_content_variants(self, title: str, content: str, 
                               content_type: Dict, platform_scores: Dict) -> Dict[str, Dict]:
        """Create optimized content variants for different platforms"""
        
        variants = {}
        top_platforms = sorted(platform_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for platform, score in top_platforms:
            if score >= 6.0:
                platform_rules = self.platform_rules.get(platform, {})
                
                # Optimize title for platform
                optimized_title = self._optimize_title_for_platform(title, platform, platform_rules)
                
                # Optimize content for platform
                optimized_content = self._optimize_content_for_platform(content, platform, platform_rules)
                
                # Add platform-specific elements
                platform_elements = self._add_platform_elements(platform, content_type)
                
                variants[platform] = {
                    'title': optimized_title,
                    'content': optimized_content,
                    'platform_elements': platform_elements,
                    'hashtags': self._generate_hashtags_for_platform(title + ' ' + content, platform),
                    'call_to_action': self._generate_cta_for_platform(platform, content_type['primary']),
                    'posting_tips': self._generate_posting_tips(platform, content_type['primary'])
                }
        
        return variants
    
    def _optimize_title_for_platform(self, title: str, platform: str, rules: Dict) -> str:
        """Optimize title for specific platform"""
        
        optimal_length = rules.get('optimal_length', {}).get('title', (50, 100))
        current_length = len(title)
        
        if platform == 'twitter' and current_length > 280:
            # Shorten for Twitter
            return title[:277] + '...'
        elif platform == 'instagram' and current_length > 150:
            # Shorten for Instagram
            return title[:147] + '...'
        elif platform == 'linkedin' and current_length < 50:
            # Expand for LinkedIn
            return f"{title} - Key Insights and Strategies"
        elif platform == 'tiktok' and current_length > 100:
            # Shorten for TikTok
            return title[:97] + '...'
        elif platform == 'facebook' and current_length < 40:
            # Expand for Facebook
            return f"{title} - What You Need to Know"
        
        return title
    
    def _optimize_content_for_platform(self, content: str, platform: str, rules: Dict) -> str:
        """Optimize content for specific platform"""
        
        optimal_length = rules.get('optimal_length', {}).get('content', (100, 500))
        current_length = len(content)
        
        if platform == 'twitter' and current_length > 280:
            # Create thread-style content
            return content[:250] + '... (Thread 1/N)'
        elif platform == 'instagram' and current_length > 300:
            # Focus on visual description
            return content[:280] + '... ✨'
        elif platform == 'linkedin' and current_length < 300:
            # Add professional context
            return f"{content}\n\nWhat are your thoughts on this? Share your experience in the comments."
        elif platform == 'tiktok' and current_length > 200:
            # Make it snappy
            return content[:180] + '... 🎯'
        elif platform == 'facebook' and current_length < 100:
            # Add community engagement
            return f"{content}\n\nWhat's your experience with this? I'd love to hear your thoughts!"
        
        return content
    
    def _add_platform_elements(self, platform: str, content_type: Dict) -> List[str]:
        """Add platform-specific elements"""
        
        elements = []
        
        if platform == 'instagram':
            elements.extend(['Add relevant emojis', 'Include story highlights', 'Use carousel if multiple points'])
        elif platform == 'twitter':
            elements.extend(['Create thread for long content', 'Use trending hashtags', 'Add poll if applicable'])
        elif platform == 'linkedin':
            elements.extend(['Add professional insights', 'Tag relevant connections', 'Use professional headshot'])
        elif platform == 'tiktok':
            elements.extend(['Create hook in first 3 seconds', 'Use trending sounds', 'Add captions for accessibility'])
        elif platform == 'facebook':
            elements.extend(['Encourage comments', 'Ask questions', 'Share to relevant groups'])
        
        return elements
    
    def _generate_hashtags_for_platform(self, text: str, platform: str) -> List[str]:
        """Generate relevant hashtags for each platform"""
        
        # Extract keywords from text
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)
        
        # Get top keywords
        top_keywords = [word for word, count in word_freq.most_common(10) if len(word) > 3]
        
        # Platform-specific hashtag strategies
        if platform == 'instagram':
            # Instagram allows up to 30 hashtags
            hashtags = [f"#{keyword}" for keyword in top_keywords[:15]]
            hashtags.extend(['#instagood', '#follow', '#like4like'])
        elif platform == 'twitter':
            # Twitter works better with 1-3 hashtags
            hashtags = [f"#{keyword}" for keyword in top_keywords[:3]]
        elif platform == 'linkedin':
            # LinkedIn hashtags should be professional
            hashtags = [f"#{keyword}" for keyword in top_keywords[:5]]
            hashtags.extend(['#professional', '#business', '#career'])
        elif platform == 'tiktok':
            # TikTok hashtags should include trending ones
            hashtags = [f"#{keyword}" for keyword in top_keywords[:8]]
            hashtags.extend(['#fyp', '#viral', '#trending'])
        else:
            hashtags = [f"#{keyword}" for keyword in top_keywords[:5]]
        
        return hashtags[:20]  # Limit to 20 hashtags max
    
    def _generate_cta_for_platform(self, platform: str, content_type: str) -> str:
        """Generate call-to-action for each platform"""
        
        cta_templates = {
            'facebook': {
                'story': "Share your story in the comments below! 👇",
                'tips': "Try these tips and let me know how they work for you!",
                'question': "What's your take on this? I'd love to hear your thoughts!",
                'default': "What do you think? Share your thoughts in the comments!"
            },
            'instagram': {
                'story': "Double tap if you relate! 💖 Share your story in the comments",
                'tips': "Save this post for later! 📌 Which tip will you try first?",
                'question': "Vote in my story poll! 📊 What's your opinion?",
                'default': "Like and save for later! ✨ What's your favorite part?"
            },
            'twitter': {
                'story': "RT if you've been there! What's your story? 🧵",
                'tips': "Which tip resonates with you? Reply and let me know! 💭",
                'question': "What's your take? Jump into the conversation below 👇",
                'default': "Thoughts? Reply and let's discuss! 💬"
            },
            'linkedin': {
                'story': "Share your professional experience in the comments. How did you handle this?",
                'tips': "Which strategy have you found most effective? Share your insights below.",
                'question': "What's your professional opinion on this? I'd value your perspective.",
                'default': "I'd love to hear your thoughts and experiences. Please share in the comments."
            },
            'tiktok': {
                'story': "Comment if this happened to you! 😱 Follow for more stories",
                'tips': "Try this and let me know if it works! 🔥 Follow for more tips",
                'question': "What do you think? Drop your answer in the comments! 💭",
                'default': "Comment your thoughts! 👇 Follow for more content like this"
            }
        }
        
        platform_ctas = cta_templates.get(platform, cta_templates['facebook'])
        return platform_ctas.get(content_type, platform_ctas['default'])
    
    def _generate_posting_tips(self, platform: str, content_type: str) -> List[str]:
        """Generate posting tips for each platform"""
        
        tips = {
            'facebook': [
                "Post when your audience is most active (typically 1-4 PM)",
                "Use Facebook Insights to track performance",
                "Encourage comments to boost engagement",
                "Share to relevant Facebook groups"
            ],
            'instagram': [
                "Post during peak hours (11 AM - 1 PM, 7-9 PM)",
                "Use all 30 hashtags for maximum reach",
                "Create Instagram Stories to increase visibility",
                "Engage with comments within the first hour"
            ],
            'twitter': [
                "Tweet during business hours for professional content",
                "Use trending hashtags relevant to your topic",
                "Engage with replies quickly",
                "Consider creating a thread for longer content"
            ],
            'linkedin': [
                "Post on weekdays between 8-10 AM or 12-2 PM",
                "Write in first person for authenticity",
                "Ask questions to encourage professional discussion",
                "Share in relevant LinkedIn groups"
            ],
            'tiktok': [
                "Post between 6-10 AM or 7-9 PM",
                "Use trending sounds and effects",
                "Add captions for accessibility",
                "Engage with comments to boost algorithm performance"
            ]
        }
        
        return tips.get(platform, ["Post consistently", "Engage with your audience", "Use relevant hashtags"])
    
    def _predict_engagement(self, analysis: Dict, platform_scores: Dict, 
                          reddit_insights: Dict) -> Dict[str, Any]:
        """Predict engagement performance for each platform"""
        
        predictions = {}
        
        for platform, score in platform_scores.items():
            if score >= 6.0:
                # Base engagement prediction
                base_engagement = score * 10  # Convert to percentage
                
                # Adjust based on content characteristics
                shareability = analysis['engagement_factors']['shareability_score']
                discussion_potential = analysis['engagement_factors']['discussion_potential']
                
                # Platform-specific adjustments
                if platform == 'facebook':
                    predicted_engagement = base_engagement * (1 + discussion_potential * 0.3)
                elif platform == 'instagram':
                    predicted_engagement = base_engagement * (1 + shareability * 0.4)
                elif platform == 'twitter':
                    predicted_engagement = base_engagement * (1 + analysis['topic_analysis']['professional_tone'] * 0.2)
                elif platform == 'linkedin':
                    predicted_engagement = base_engagement * (1 + analysis['topic_analysis']['professional_tone'] * 0.5)
                elif platform == 'tiktok':
                    predicted_engagement = base_engagement * (1 + analysis['emotional_analysis']['emotional_intensity'] * 0.3)
                else:
                    predicted_engagement = base_engagement
                
                # Add Reddit insights boost
                if reddit_insights and 'social_media_insights' in reddit_insights:
                    platform_performance = reddit_insights['social_media_insights'].get('platform_performance', {})
                    if platform in platform_performance:
                        reddit_boost = platform_performance[platform] / 10
                        predicted_engagement *= (1 + reddit_boost * 0.1)
                
                predictions[platform] = {
                    'engagement_rate': round(min(100, predicted_engagement), 1),
                    'confidence_level': 'high' if score >= 8 else 'medium' if score >= 6.5 else 'low',
                    'key_success_factors': self._identify_success_factors(platform, analysis),
                    'potential_reach': self._estimate_reach(platform, predicted_engagement)
                }
        
        return predictions
    
    def _identify_success_factors(self, platform: str, analysis: Dict) -> List[str]:
        """Identify key success factors for each platform"""
        
        factors = []
        
        if platform == 'facebook':
            if analysis['engagement_factors']['discussion_potential'] > 0.6:
                factors.append('High discussion potential')
            if analysis['emotional_analysis']['emotional_intensity'] > 0.5:
                factors.append('Strong emotional appeal')
        elif platform == 'instagram':
            if analysis['engagement_factors']['visual_appeal_potential'] > 0.6:
                factors.append('High visual appeal')
            if analysis['engagement_factors']['shareability_score'] > 0.6:
                factors.append('High shareability')
        elif platform == 'twitter':
            if analysis['topic_analysis']['professional_tone'] > 0.5:
                factors.append('Professional relevance')
            if analysis['content_structure']['has_call_to_action']:
                factors.append('Clear call-to-action')
        elif platform == 'linkedin':
            if analysis['topic_analysis']['professional_tone'] > 0.6:
                factors.append('Professional value')
            if analysis['topic_analysis']['technical_complexity'] > 0.5:
                factors.append('Industry expertise')
        elif platform == 'tiktok':
            if analysis['emotional_analysis']['emotional_intensity'] > 0.6:
                factors.append('High emotional engagement')
            if analysis['engagement_factors']['actionability_score'] > 0.6:
                factors.append('Actionable content')
        
        return factors or ['Content quality', 'Audience relevance']
    
    def _estimate_reach(self, platform: str, engagement_rate: float) -> str:
        """Estimate potential reach based on engagement rate"""
        
        if engagement_rate >= 80:
            return 'very_high'
        elif engagement_rate >= 60:
            return 'high'
        elif engagement_rate >= 40:
            return 'medium'
        elif engagement_rate >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def _generate_strategic_recommendations(self, content_type: Dict, 
                                         platform_scores: Dict, 
                                         engagement_predictions: Dict) -> Dict[str, Any]:
        """Generate strategic recommendations for content distribution"""
        
        top_platforms = sorted(platform_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Distribution strategy
        if len([p for p, s in top_platforms if s >= 8]) >= 2:
            distribution_strategy = 'multi_platform_simultaneous'
        elif len([p for p, s in top_platforms if s >= 7]) >= 2:
            distribution_strategy = 'multi_platform_sequential'
        else:
            distribution_strategy = 'single_platform_focus'
        
        # Content adaptation needs
        adaptation_needs = []
        for platform, score in top_platforms:
            if score < 8:
                adaptation_needs.append(f"Optimize for {platform}")
        
        # Timing recommendations
        timing_recommendations = self._generate_timing_recommendations(top_platforms)
        
        # Success metrics
        success_metrics = self._define_success_metrics(top_platforms, engagement_predictions)
        
        return {
            'distribution_strategy': distribution_strategy,
            'priority_platforms': [p[0] for p in top_platforms],
            'adaptation_needs': adaptation_needs,
            'timing_recommendations': timing_recommendations,
            'success_metrics': success_metrics,
            'content_lifecycle': self._plan_content_lifecycle(top_platforms, content_type),
            'optimization_opportunities': self._identify_optimization_opportunities(platform_scores)
        }
    
    def _generate_timing_recommendations(self, top_platforms: List[Tuple[str, float]]) -> Dict[str, str]:
        """Generate timing recommendations for each platform"""
        
        timing = {}
        
        for platform, score in top_platforms:
            if platform == 'facebook':
                timing[platform] = "1-4 PM on weekdays, 12-1 PM on weekends"
            elif platform == 'instagram':
                timing[platform] = "11 AM-1 PM, 7-9 PM on weekdays"
            elif platform == 'twitter':
                timing[platform] = "8-10 AM, 12-2 PM on weekdays"
            elif platform == 'linkedin':
                timing[platform] = "8-10 AM, 12-2 PM on weekdays"
            elif platform == 'tiktok':
                timing[platform] = "6-10 AM, 7-9 PM daily"
        
        return timing
    
    def _define_success_metrics(self, top_platforms: List[Tuple[str, float]], 
                              engagement_predictions: Dict) -> Dict[str, List[str]]:
        """Define success metrics for each platform"""
        
        metrics = {}
        
        for platform, score in top_platforms:
            if platform == 'facebook':
                metrics[platform] = ['Comments', 'Shares', 'Reactions', 'Reach']
            elif platform == 'instagram':
                metrics[platform] = ['Likes', 'Saves', 'Shares', 'Story views']
            elif platform == 'twitter':
                metrics[platform] = ['Retweets', 'Likes', 'Replies', 'Impressions']
            elif platform == 'linkedin':
                metrics[platform] = ['Engagement rate', 'Shares', 'Comments', 'Profile views']
            elif platform == 'tiktok':
                metrics[platform] = ['Views', 'Likes', 'Shares', 'Comments']
        
        return metrics
    
    def _plan_content_lifecycle(self, top_platforms: List[Tuple[str, float]], 
                              content_type: Dict) -> Dict[str, str]:
        """Plan content lifecycle across platforms"""
        
        lifecycle = {}
        
        # Primary platform (highest score)
        if top_platforms:
            primary_platform = top_platforms[0][0]
            lifecycle['primary_launch'] = f"Launch on {primary_platform} first"
            
            # Secondary platforms
            if len(top_platforms) > 1:
                secondary_platforms = [p[0] for p in top_platforms[1:]]
                lifecycle['secondary_distribution'] = f"Cross-post to {', '.join(secondary_platforms)} within 24 hours"
            
            # Content repurposing
            if content_type['primary'] in ['how-to', 'tips']:
                lifecycle['repurposing'] = "Create carousel posts for Instagram, thread for Twitter"
            elif content_type['primary'] == 'story':
                lifecycle['repurposing'] = "Create Instagram stories, LinkedIn narrative post"
        
        return lifecycle
    
    def _identify_optimization_opportunities(self, platform_scores: Dict[str, float]) -> List[str]:
        """Identify optimization opportunities"""
        
        opportunities = []
        
        for platform, score in platform_scores.items():
            if 6.0 <= score < 8.0:
                opportunities.append(f"Optimize for {platform} - score {score}/10")
        
        if not opportunities:
            opportunities.append("Content is well-optimized across all platforms")
        
        return opportunities
    
    # Helper methods for content analysis
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (simplified)"""
        
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0:
            return 0.5
        
        avg_sentence_length = words / sentences
        
        # Simple readability score (lower is better)
        if avg_sentence_length <= 15:
            return 0.8  # Easy to read
        elif avg_sentence_length <= 20:
            return 0.6  # Moderate
        else:
            return 0.4  # Difficult
    
    def _count_emotional_words(self, text: str) -> int:
        """Count emotional words in text"""
        
        emotional_words = ['amazing', 'awesome', 'incredible', 'fantastic', 'terrible', 'awful', 
                          'love', 'hate', 'excited', 'frustrated', 'happy', 'sad', 'angry', 
                          'surprised', 'disappointed', 'thrilled', 'worried', 'confident']
        
        return sum(1 for word in emotional_words if word in text.lower())
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score (0-1 scale)"""
        
        positive_words = ['good', 'great', 'amazing', 'awesome', 'love', 'excellent', 'perfect', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disappointing']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        total_sentiment = positive_count + negative_count
        
        if total_sentiment == 0:
            return 0.5  # Neutral
        
        return positive_count / total_sentiment
    
    def _calculate_emotional_intensity(self, text: str) -> float:
        """Calculate emotional intensity (0-1 scale)"""
        
        emotional_words = self._count_emotional_words(text)
        total_words = len(text.split())
        
        if total_words == 0:
            return 0
        
        return min(1.0, emotional_words / total_words * 10)
    
    def _has_call_to_action(self, text: str) -> bool:
        """Check if text has call-to-action"""
        
        cta_indicators = ['comment', 'share', 'like', 'follow', 'subscribe', 'click', 'visit', 
                         'check out', 'try', 'download', 'sign up', 'join', 'contact']
        
        return any(indicator in text.lower() for indicator in cta_indicators)
    
    def _calculate_topic_relevance(self, text: str, topic: str) -> float:
        """Calculate topic relevance score"""
        
        topic_words = topic.lower().split()
        text_words = text.lower().split()
        
        matches = sum(1 for word in topic_words if word in text_words)
        
        if not topic_words:
            return 0.5
        
        return matches / len(topic_words)
    
    def _assess_technical_complexity(self, text: str) -> float:
        """Assess technical complexity of text"""
        
        technical_indicators = ['API', 'algorithm', 'implementation', 'configuration', 'optimization',
                               'architecture', 'framework', 'methodology', 'analysis', 'strategy']
        
        technical_count = sum(1 for indicator in technical_indicators if indicator.lower() in text.lower())
        words = len(text.split())
        
        if words == 0:
            return 0
        
        return min(1.0, technical_count / words * 20)
    
    def _assess_professional_tone(self, text: str) -> float:
        """Assess professional tone of text"""
        
        professional_indicators = ['professional', 'business', 'strategy', 'analysis', 'industry',
                                  'market', 'research', 'development', 'management', 'leadership']
        
        professional_count = sum(1 for indicator in professional_indicators if indicator in text.lower())
        words = len(text.split())
        
        if words == 0:
            return 0
        
        return min(1.0, professional_count / words * 15)
    
    def _assess_casual_tone(self, text: str) -> float:
        """Assess casual tone of text"""
        
        casual_indicators = ['cool', 'awesome', 'fun', 'easy', 'simple', 'quick', 'hey', 'wow',
                            'just', 'really', 'super', 'totally', 'basically', 'actually']
        
        casual_count = sum(1 for indicator in casual_indicators if indicator in text.lower())
        words = len(text.split())
        
        if words == 0:
            return 0
        
        return min(1.0, casual_count / words * 10)
    
    def _calculate_shareability_score(self, text: str) -> float:
        """Calculate shareability score"""
        
        shareability_factors = ['tip', 'secret', 'hack', 'amazing', 'incredible', 'shocking',
                               'surprising', 'must-know', 'life-changing', 'game-changer']
        
        shareability_count = sum(1 for factor in shareability_factors if factor in text.lower())
        
        # Normalize to 0-1 scale
        return min(1.0, shareability_count / 3)
    
    def _calculate_discussion_potential(self, text: str) -> float:
        """Calculate discussion potential score"""
        
        discussion_indicators = ['?', 'what do you think', 'opinion', 'thoughts', 'experience',
                                'agree', 'disagree', 'debate', 'controversial', 'perspective']
        
        discussion_count = sum(1 for indicator in discussion_indicators if indicator in text.lower())
        
        # Normalize to 0-1 scale
        return min(1.0, discussion_count / 2)
    
    def _assess_visual_appeal_potential(self, text: str) -> float:
        """Assess visual appeal potential"""
        
        visual_indicators = ['image', 'photo', 'video', 'visual', 'infographic', 'chart',
                            'diagram', 'screenshot', 'before', 'after', 'step-by-step']
        
        visual_count = sum(1 for indicator in visual_indicators if indicator in text.lower())
        
        # Normalize to 0-1 scale
        return min(1.0, visual_count / 2)
    
    def _calculate_actionability_score(self, text: str) -> float:
        """Calculate actionability score"""
        
        actionable_indicators = ['how to', 'step', 'guide', 'tutorial', 'method', 'way',
                                'process', 'technique', 'strategy', 'approach', 'instructions']
        
        actionable_count = sum(1 for indicator in actionable_indicators if indicator in text.lower())
        
        # Normalize to 0-1 scale
        return min(1.0, actionable_count / 3)
