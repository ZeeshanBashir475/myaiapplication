import json
import re
from typing import Dict, List, Any, Optional
from collections import Counter
from src.utils.llm_client import LLMClient

class AdvancedTopicResearchAgent:
    def __init__(self):
        self.llm = LLMClient()
        
        # SEO-focused research framework
        self.research_framework = {
            'keyword_research': {
                'primary_keywords': 'high_volume_high_relevance',
                'long_tail_keywords': 'specific_user_intent',
                'semantic_keywords': 'topic_cluster_support',
                'competitor_keywords': 'gap_identification',
                'trending_keywords': 'emerging_opportunities'
            },
            'content_strategy': {
                'pillar_content': 'comprehensive_topic_coverage',
                'cluster_content': 'supporting_subtopics',
                'commercial_content': 'product_service_focus',
                'informational_content': 'educational_value',
                'comparison_content': 'decision_support'
            },
            'competitive_analysis': {
                'content_gaps': 'underserved_topics',
                'quality_opportunities': 'improvement_potential',
                'authority_building': 'backlink_opportunities',
                'featured_snippets': 'serp_features_targeting'
            }
        }
        
        # Modern SEO principles
        self.seo_principles = {
            'search_intent_optimization': {
                'informational': ['how_to', 'what_is', 'guide', 'tutorial'],
                'commercial': ['best', 'top', 'review', 'comparison'],
                'transactional': ['buy', 'price', 'discount', 'deal'],
                'navigational': ['brand_name', 'login', 'contact']
            },
            'content_depth_requirements': {
                'pillar_pages': 3000,
                'cluster_pages': 1500,
                'commercial_pages': 2000,
                'informational_pages': 1000
            },
            'eeat_optimization': {
                'experience': 'first_hand_insights',
                'expertise': 'subject_matter_authority',
                'authoritativeness': 'industry_recognition',
                'trustworthiness': 'credible_sources'
            }
        }
    
    def research_topic_comprehensive(self, topic: str, industry: str, target_audience: str,
                                   business_goals: List[str], competitor_domains: List[str] = None,
                                   current_content_urls: List[str] = None) -> Dict[str, Any]:
        """
        Comprehensive topic research for SEO content strategy
        """
        
        print(f"🔬 Starting comprehensive topic research for: {topic}")
        print(f"📊 Industry: {industry}, Audience: {target_audience}")
        
        # 1. Strategic keyword research
        print("🔍 Conducting strategic keyword research...")
        keyword_research = self._conduct_strategic_keyword_research(topic, industry, target_audience)
        
        # 2. Search intent analysis
        print("🎯 Analyzing search intent patterns...")
        intent_analysis = self._analyze_search_intent_patterns(topic, keyword_research)
        
        # 3. Content gap identification
        print("📈 Identifying content gaps and opportunities...")
        content_gaps = self._identify_content_gaps(topic, industry, competitor_domains)
        
        # 4. Competitive landscape analysis
        print("🏆 Analyzing competitive landscape...")
        competitive_analysis = self._analyze_competitive_landscape(topic, industry, competitor_domains)
        
        # 5. Topic authority assessment
        print("⚡ Assessing topic authority requirements...")
        authority_requirements = self._assess_topic_authority_requirements(topic, industry)
        
        # 6. Content cluster strategy
        print("🗂️ Developing content cluster strategy...")
        cluster_strategy = self._develop_content_cluster_strategy(keyword_research, intent_analysis)
        
        # 7. SEO opportunity scoring
        print("🎯 Scoring SEO opportunities...")
        opportunity_scoring = self._score_seo_opportunities(
            keyword_research, content_gaps, competitive_analysis, business_goals
        )
        
        # 8. Implementation roadmap
        print("🗺️ Creating implementation roadmap...")
        implementation_roadmap = self._create_implementation_roadmap(
            opportunity_scoring, cluster_strategy, authority_requirements
        )
        
        return {
            'topic_research_summary': {
                'topic': topic,
                'industry': industry,
                'research_depth': 'comprehensive',
                'total_opportunities': len(opportunity_scoring.get('opportunities', [])),
                'recommended_strategy': self._determine_recommended_strategy(opportunity_scoring)
            },
            'keyword_research': keyword_research,
            'search_intent_analysis': intent_analysis,
            'content_gaps': content_gaps,
            'competitive_analysis': competitive_analysis,
            'authority_requirements': authority_requirements,
            'cluster_strategy': cluster_strategy,
            'opportunity_scoring': opportunity_scoring,
            'implementation_roadmap': implementation_roadmap,
            'success_metrics': self._define_success_metrics(topic, business_goals),
            'content_calendar_suggestions': self._generate_content_calendar(cluster_strategy, implementation_roadmap)
        }
    
    def _conduct_strategic_keyword_research(self, topic: str, industry: str, target_audience: str) -> Dict[str, Any]:
        """Conduct comprehensive keyword research for SEO strategy"""
        
        # Generate seed keywords
        seed_keywords = self._generate_seed_keywords(topic, industry)
        
        # Expand keyword universe
        expanded_keywords = self._expand_keyword_universe(seed_keywords, topic)
        
        # Analyze keyword difficulty and opportunity
        keyword_analysis = self._analyze_keyword_opportunities(expanded_keywords, target_audience)
        
        # Group keywords by intent and topic clusters
        keyword_clusters = self._cluster_keywords_by_intent(expanded_keywords)
        
        # Identify long-tail opportunities
        long_tail_opportunities = self._identify_long_tail_opportunities(expanded_keywords, topic)
        
        return {
            'seed_keywords': seed_keywords,
            'expanded_keywords': expanded_keywords[:100],  # Top 100 keywords
            'keyword_analysis': keyword_analysis,
            'keyword_clusters': keyword_clusters,
            'long_tail_opportunities': long_tail_opportunities,
            'priority_keywords': self._prioritize_keywords(keyword_analysis, keyword_clusters),
            'seasonal_trends': self._analyze_seasonal_trends(seed_keywords),
            'emerging_keywords': self._identify_emerging_keywords(topic, industry)
        }
    
    def _generate_seed_keywords(self, topic: str, industry: str) -> List[str]:
        """Generate initial seed keywords"""
        
        # Core topic variations
        seed_keywords = [
            topic,
            f"{topic} guide",
            f"{topic} tips",
            f"best {topic}",
            f"how to {topic}",
            f"{topic} strategy",
            f"{topic} solution",
            f"{topic} tool",
            f"{topic} service",
            f"{topic} software"
        ]
        
        # Industry-specific variations
        if industry:
            industry_keywords = [
                f"{topic} for {industry}",
                f"{industry} {topic}",
                f"{topic} {industry} solution",
                f"{industry} {topic} strategy"
            ]
            seed_keywords.extend(industry_keywords)
        
        # Question-based keywords
        question_keywords = [
            f"what is {topic}",
            f"why {topic}",
            f"when to use {topic}",
            f"where to find {topic}",
            f"which {topic} is best"
        ]
        seed_keywords.extend(question_keywords)
        
        return seed_keywords
    
    def _expand_keyword_universe(self, seed_keywords: List[str], topic: str) -> List[Dict[str, Any]]:
        """Expand keyword universe using AI analysis"""
        
        prompt = f"""
        Expand the keyword universe for "{topic}" based on these seed keywords: {seed_keywords[:10]}
        
        Generate a comprehensive list of related keywords that cover:
        1. Direct variations and synonyms
        2. Problem-focused keywords (pain points)
        3. Solution-focused keywords (benefits)
        4. Comparison keywords (vs, alternative, best)
        5. Technical keywords (advanced users)
        6. Beginner keywords (getting started)
        7. Commercial keywords (buy, price, cost)
        8. Informational keywords (learn, understand)
        
        Return as JSON array with this structure:
        [
            {{
                "keyword": "keyword phrase",
                "search_intent": "informational|commercial|transactional|navigational",
                "difficulty_estimate": "low|medium|high",
                "relevance_score": 8.5,
                "keyword_type": "primary|long_tail|semantic|commercial",
                "user_stage": "awareness|consideration|decision"
            }}
        ]
        
        Focus on keywords that real users would search for. Include specific, actionable keywords.
        """
        
        response = self.llm.generate_structured(prompt)
        
        try:
            expanded_keywords = json.loads(response)
            return expanded_keywords
        except json.JSONDecodeError:
            return self._generate_fallback_keywords(seed_keywords, topic)
    
    def _analyze_search_intent_patterns(self, topic: str, keyword_research: Dict) -> Dict[str, Any]:
        """Analyze search intent patterns for strategic content planning"""
        
        keywords = keyword_research.get('expanded_keywords', [])
        
        # Group by search intent
        intent_groups = {
            'informational': [],
            'commercial': [],
            'transactional': [],
            'navigational': []
        }
        
        for keyword in keywords:
            intent = keyword.get('search_intent', 'informational')
            intent_groups[intent].append(keyword)
        
        # Analyze intent distribution
        total_keywords = len(keywords)
        intent_distribution = {
            intent: round(len(kw_list) / total_keywords * 100, 1)
            for intent, kw_list in intent_groups.items()
        }
        
        # Identify intent-based content opportunities
        content_opportunities = self._map_intent_to_content_opportunities(intent_groups)
        
        # Analyze user journey mapping
        user_journey = self._map_keywords_to_user_journey(keywords)
        
        return {
            'intent_distribution': intent_distribution,
            'intent_groups': intent_groups,
            'content_opportunities': content_opportunities,
            'user_journey_mapping': user_journey,
            'recommended_content_mix': self._recommend_content_mix(intent_distribution),
            'priority_intents': self._prioritize_search_intents(intent_distribution, intent_groups)
        }
    
    def _identify_content_gaps(self, topic: str, industry: str, competitor_domains: List[str]) -> Dict[str, Any]:
        """Identify content gaps and opportunities in the market"""
        
        # Analyze what's missing in the current content landscape
        gap_analysis = self._analyze_content_landscape_gaps(topic, industry)
        
        # Identify underserved search queries
        underserved_queries = self._identify_underserved_queries(topic, industry)
        
        # Find format gaps (video, infographic, tools, etc.)
        format_gaps = self._identify_format_gaps(topic)
        
        # Analyze competitor content gaps
        competitor_gaps = self._analyze_competitor_content_gaps(topic, competitor_domains)
        
        # Identify emerging topic gaps
        emerging_gaps = self._identify_emerging_topic_gaps(topic, industry)
        
        return {
            'landscape_gaps': gap_analysis,
            'underserved_queries': underserved_queries,
            'format_opportunities': format_gaps,
            'competitor_gaps': competitor_gaps,
            'emerging_opportunities': emerging_gaps,
            'high_priority_gaps': self._prioritize_content_gaps(gap_analysis, underserved_queries),
            'quick_win_opportunities': self._identify_quick_win_gaps(gap_analysis),
            'long_term_opportunities': self._identify_long_term_gaps(emerging_gaps)
        }
    
    def _analyze_competitive_landscape(self, topic: str, industry: str, 
                                     competitor_domains: List[str]) -> Dict[str, Any]:
        """Analyze competitive landscape for strategic positioning"""
        
        # Content quality analysis
        quality_analysis = self._analyze_competitor_content_quality(topic, competitor_domains)
        
        # Authority assessment
        authority_analysis = self._assess_competitor_authority(competitor_domains)
        
        # Content strategy analysis
        strategy_analysis = self._analyze_competitor_content_strategies(topic, competitor_domains)
        
        # Opportunity identification
        competitive_opportunities = self._identify_competitive_opportunities(
            quality_analysis, authority_analysis, strategy_analysis
        )
        
        # Positioning recommendations
        positioning = self._recommend_competitive_positioning(competitive_opportunities, topic)
        
        return {
            'market_leaders': self._identify_market_leaders(authority_analysis),
            'content_quality_benchmark': quality_analysis,
            'authority_landscape': authority_analysis,
            'strategy_patterns': strategy_analysis,
            'competitive_opportunities': competitive_opportunities,
            'positioning_strategy': positioning,
            'differentiation_opportunities': self._identify_differentiation_opportunities(competitive_opportunities),
            'barrier_assessment': self._assess_competitive_barriers(authority_analysis)
        }
    
    def _assess_topic_authority_requirements(self, topic: str, industry: str) -> Dict[str, Any]:
        """Assess requirements for building topic authority"""
        
        # Determine authority threshold needed
        authority_threshold = self._determine_authority_threshold(topic, industry)
        
        # Identify required credentials and expertise
        credential_requirements = self._identify_credential_requirements(topic, industry)
        
        # Assess content depth requirements
        content_depth_requirements = self._assess_content_depth_requirements(topic)
        
        # Identify trust signals needed
        trust_signals = self._identify_required_trust_signals(topic, industry)
        
        # Create authority building roadmap
        authority_roadmap = self._create_authority_building_roadmap(
            authority_threshold, credential_requirements, trust_signals
        )
        
        return {
            'authority_threshold': authority_threshold,
            'credential_requirements': credential_requirements,
            'content_depth_requirements': content_depth_requirements,
            'trust_signals_needed': trust_signals,
            'authority_building_roadmap': authority_roadmap,
            'time_to_authority': self._estimate_time_to_authority(authority_threshold),
            'investment_required': self._estimate_authority_investment(authority_roadmap),
            'risk_assessment': self._assess_authority_building_risks(topic, industry)
        }
    
    def _develop_content_cluster_strategy(self, keyword_research: Dict, intent_analysis: Dict) -> Dict[str, Any]:
        """Develop comprehensive content cluster strategy"""
        
        # Identify pillar content opportunities
        pillar_opportunities = self._identify_pillar_content_opportunities(keyword_research, intent_analysis)
        
        # Create cluster mapping
        cluster_mapping = self._create_cluster_mapping(pillar_opportunities, keyword_research)
        
        # Plan internal linking strategy
        linking_strategy = self._plan_internal_linking_strategy(cluster_mapping)
        
        # Prioritize cluster development
        cluster_priorities = self._prioritize_cluster_development(cluster_mapping, intent_analysis)
        
        return {
            'pillar_content_opportunities': pillar_opportunities,
            'content_clusters': cluster_mapping,
            'internal_linking_strategy': linking_strategy,
            'development_priorities': cluster_priorities,
            'cluster_performance_prediction': self._predict_cluster_performance(cluster_mapping),
            'maintenance_strategy': self._plan_cluster_maintenance(cluster_mapping)
        }
    
    def _score_seo_opportunities(self, keyword_research: Dict, content_gaps: Dict, 
                               competitive_analysis: Dict, business_goals: List[str]) -> Dict[str, Any]:
        """Score and prioritize SEO opportunities"""
        
        opportunities = []
        
        # Score keyword opportunities
        keyword_opportunities = self._score_keyword_opportunities(
            keyword_research['priority_keywords'], competitive_analysis
        )
        opportunities.extend(keyword_opportunities)
        
        # Score content gap opportunities
        gap_opportunities = self._score_content_gap_opportunities(
            content_gaps['high_priority_gaps'], business_goals
        )
        opportunities.extend(gap_opportunities)
        
        # Score competitive opportunities
        competitive_opportunities = self._score_competitive_opportunities(
            competitive_analysis['competitive_opportunities']
        )
        opportunities.extend(competitive_opportunities)
        
        # Prioritize all opportunities
        prioritized_opportunities = sorted(opportunities, key=lambda x: x['score'], reverse=True)
        
        return {
            'opportunities': prioritized_opportunities,
            'top_10_opportunities': prioritized_opportunities[:10],
            'quick_wins': [o for o in prioritized_opportunities if o.get('difficulty') == 'low'][:5],
            'high_impact_opportunities': [o for o in prioritized_opportunities if o.get('impact') == 'high'][:5],
            'opportunity_distribution': self._analyze_opportunity_distribution(prioritized_opportunities),
            'resource_allocation_guide': self._create_resource_allocation_guide(prioritized_opportunities)
        }
    
    def _create_implementation_roadmap(self, opportunity_scoring: Dict, cluster_strategy: Dict,
                                     authority_requirements: Dict) -> Dict[str, Any]:
        """Create detailed implementation roadmap"""
        
        # Phase 1: Foundation (0-3 months)
        phase_1 = {
            'timeline': '0-3 months',
            'focus': 'Foundation & Quick Wins',
            'activities': self._plan_phase_1_activities(opportunity_scoring, cluster_strategy),
            'deliverables': self._define_phase_1_deliverables(opportunity_scoring),
            'success_metrics': ['Baseline content published', 'Initial keyword tracking', 'Author authority established']
        }
        
        # Phase 2: Growth (3-6 months)
        phase_2 = {
            'timeline': '3-6 months', 
            'focus': 'Content Cluster Development',
            'activities': self._plan_phase_2_activities(cluster_strategy, authority_requirements),
            'deliverables': self._define_phase_2_deliverables(cluster_strategy),
            'success_metrics': ['Cluster content published', 'Internal linking established', 'Rankings improvement']
        }
        
        # Phase 3: Authority (6-12 months)
        phase_3 = {
            'timeline': '6-12 months',
            'focus': 'Authority & Market Leadership',
            'activities': self._plan_phase_3_activities(authority_requirements, opportunity_scoring),
            'deliverables': self._define_phase_3_deliverables(authority_requirements),
            'success_metrics': ['Industry recognition', 'Backlink growth', 'Thought leadership']
        }
        
        return {
            'implementation_phases': {
                'phase_1': phase_1,
                'phase_2': phase_2,
                'phase_3': phase_3
            },
            'critical_success_factors': [
                'Consistent content quality',
                'Strategic keyword targeting',
                'Authority signal building',
                'User experience optimization'
            ],
            'resource_requirements': {
                'content_creation': '60% of resources',
                'technical_seo': '20% of resources',
                'promotion_outreach': '20% of resources'
            },
            'risk_mitigation': self._identify_implementation_risks(opportunity_scoring, authority_requirements),
            'milestone_tracking': self._define_milestone_tracking(phase_1, phase_2, phase_3)
        }
    
    # Helper methods for comprehensive analysis
    def _determine_recommended_strategy(self, opportunity_scoring: Dict) -> str:
        """Determine recommended overall strategy"""
        
        opportunities = opportunity_scoring.get('opportunities', [])
        quick_wins = opportunity_scoring.get('quick_wins', [])
        
        if len(quick_wins) >= 5:
            return 'quick_wins_first'
        elif len([o for o in opportunities if o.get('impact') == 'high']) >= 3:
            return 'high_impact_focus'
        else:
            return 'balanced_approach'
    
    def _generate_fallback_keywords(self, seed_keywords: List[str], topic: str) -> List[Dict[str, Any]]:
        """Generate fallback keyword data if AI analysis fails"""
        
        fallback_keywords = []
        
        for seed in seed_keywords[:20]:
            fallback_keywords.append({
                'keyword': seed,
                'search_intent': 'informational',
                'difficulty_estimate': 'medium',
                'relevance_score': 7.0,
                'keyword_type': 'primary',
                'user_stage': 'awareness'
            })
        
        return fallback_keywords
    
    def _map_intent_to_content_opportunities(self, intent_groups: Dict) -> Dict[str, List[str]]:
        """Map search intents to content opportunities"""
        
        return {
            'informational': [
                'Comprehensive guides and tutorials',
                'Educational blog posts',
                'FAQ content',
                'Explainer videos'
            ],
            'commercial': [
                'Comparison articles',
                'Review roundups',
                'Best-of lists',
                'Product comparisons'
            ],
            'transactional': [
                'Product pages',
                'Pricing information',
                'Service descriptions',
                'Conversion-focused landing pages'
            ],
            'navigational': [
                'Brand-specific content',
                'Company information',
                'Contact and location pages',
                'About pages'
            ]
        }
    
    def _define_success_metrics(self, topic: str, business_goals: List[str]) -> Dict[str, List[str]]:
        """Define success metrics for the research implementation"""
        
        return {
            'seo_metrics': [
                'Organic traffic growth',
                'Keyword rankings improvement',
                'Featured snippet captures',
                'Page one rankings count'
            ],
            'content_metrics': [
                'Content engagement rates',
                'Time on page',
                'Pages per session',
                'Return visitor rate'
            ],
            'business_metrics': [
                'Lead generation increase',
                'Conversion rate improvement',
                'Brand awareness growth',
                'Authority score increase'
            ],
            'competitive_metrics': [
                'Share of voice increase',
                'Competitive keyword wins',
                'Backlink growth rate',
                'Industry mention frequency'
            ]
        }
    
    def _generate_content_calendar(self, cluster_strategy: Dict, roadmap: Dict) -> Dict[str, Any]:
        """Generate content calendar suggestions"""
        
        # Extract pillar and cluster content from strategy
        pillar_content = cluster_strategy.get('pillar_content_opportunities', [])
        clusters = cluster_strategy.get('content_clusters', {})
        
        calendar_suggestions = {
            'month_1': {
                'focus': 'Foundation Content',
                'content_pieces': self._select_foundation_content(pillar_content),
                'priority_level': 'high'
            },
            'month_2': {
                'focus': 'Cluster Development',
                'content_pieces': self._select_cluster_content(clusters, 1),
                'priority_level': 'high'
            },
            'month_3': {
                'focus': 'Content Expansion',
                'content_pieces': self._select_cluster_content(clusters, 2),
                'priority_level': 'medium'
            }
        }
        
        return {
            'quarterly_calendar': calendar_suggestions,
            'content_themes': self._identify_content_themes(cluster_strategy),
            'seasonal_considerations': self._add_seasonal_considerations(cluster_strategy),
            'content_types_mix': self._recommend_content_types_mix(cluster_strategy)
        }
    
    # Placeholder methods for complex analysis (simplified for brevity)
    def _analyze_content_landscape_gaps(self, topic: str, industry: str) -> List[str]:
        """Analyze gaps in current content landscape"""
        return [
            f"Lack of comprehensive {topic} guides",
            f"Limited practical examples in {industry}",
            f"Insufficient beginner-level content",
            f"Missing advanced strategy content"
        ]
    
    def _identify_underserved_queries(self, topic: str, industry: str) -> List[str]:
        """Identify underserved search queries"""
        return [
            f"How to implement {topic} in {industry}",
            f"Common {topic} mistakes to avoid",
            f"{topic} ROI calculation methods",
            f"Free {topic} tools and resources"
        ]
    
    def _plan_phase_1_activities(self, opportunity_scoring: Dict, cluster_strategy: Dict) -> List[str]:
        """Plan Phase 1 implementation activities"""
        return [
            "Create foundational pillar content",
            "Optimize existing content for target keywords",
            "Establish author authority and credentials",
            "Set up analytics and tracking"
        ]
    
    def _select_foundation_content(self, pillar_content: List) -> List[str]:
        """Select foundation content for first month"""
        return [
            "Primary pillar page",
            "Essential how-to guide",
            "Topic overview article",
            "Beginner's guide"
        ]
