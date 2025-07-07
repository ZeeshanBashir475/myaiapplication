import json
import logging
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StreamingChatAgent:
    """Enhanced Claude-style streaming chat agent with real-time metrics updates"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.improvement_patterns = self._load_improvement_patterns()
        logger.info("✅ Enhanced Streaming Chat Agent initialized")
    
    def _load_improvement_patterns(self) -> Dict[str, Dict]:
        """Load patterns for different types of improvements"""
        return {
            'trust_improvement': {
                'keywords': ['trust', 'credibility', 'authority', 'expertise', 'eeat', 'professional'],
                'actions': [
                    'Add author credentials and certifications',
                    'Include professional experience details',
                    'Add customer testimonials and case studies',
                    'Reference authoritative industry sources',
                    'Include contact information and business location',
                    'Add professional headshot and bio'
                ],
                'score_impact': {'trust_score': 0.3, 'overall_score': 0.15}
            },
            'quality_improvement': {
                'keywords': ['quality', 'better', 'improve', 'enhance', 'optimize'],
                'actions': [
                    'Add more specific examples and case studies',
                    'Include step-by-step actionable guidance',
                    'Improve content structure with clear headings',
                    'Add visual elements and formatting',
                    'Include more detailed explanations',
                    'Add relevant statistics and data'
                ],
                'score_impact': {'quality_score': 0.25, 'overall_score': 0.12}
            },
            'pain_point_focus': {
                'keywords': ['pain point', 'problem', 'issue', 'challenge', 'difficulty', 'customer'],
                'actions': [
                    'Address specific customer pain points directly',
                    'Add solutions for common problems',
                    'Include customer success stories',
                    'Provide troubleshooting guides',
                    'Add FAQ section for common issues',
                    'Include prevention strategies'
                ],
                'score_impact': {'quality_score': 0.2, 'pain_points_addressed': 2}
            },
            'beginner_friendly': {
                'keywords': ['beginner', 'simple', 'easy', 'basic', 'start', 'newbie'],
                'actions': [
                    'Simplify technical language and jargon',
                    'Add definitions for complex terms',
                    'Include step-by-step beginner guides',
                    'Add "What you need to know" sections',
                    'Include basic vs advanced options',
                    'Add prerequisite information'
                ],
                'score_impact': {'quality_score': 0.2, 'accessibility_score': 0.3}
            },
            'seo_optimization': {
                'keywords': ['seo', 'search', 'ranking', 'keywords', 'optimize'],
                'actions': [
                    'Optimize title and meta descriptions',
                    'Add relevant internal and external links',
                    'Improve keyword integration naturally',
                    'Add structured data markup suggestions',
                    'Optimize heading hierarchy (H1, H2, H3)',
                    'Include related keyword variations'
                ],
                'score_impact': {'seo_score': 0.4, 'overall_score': 0.1}
            },
            'content_expansion': {
                'keywords': ['expand', 'more', 'detailed', 'comprehensive', 'thorough'],
                'actions': [
                    'Add more comprehensive coverage of subtopics',
                    'Include additional examples and use cases',
                    'Add related topics and cross-references',
                    'Include industry insights and trends',
                    'Add comparison tables and charts',
                    'Include expert quotes and opinions'
                ],
                'score_impact': {'content_depth': 0.3, 'word_count': 500}
            }
        }
    
    async def process_message(self, message: str, session: Dict, connection_manager) -> None:
        """Process chat message with intelligent streaming and real-time updates"""
        
        session_id = session['session_id']
        
        # Add user message to conversation history
        session['conversation_history'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze message intent and improvement type
        improvement_type = self._analyze_improvement_intent(message)
        content_modification_requested = self._is_content_modification_request(message)
        
        # Send typing indicator
        await connection_manager.send_message(session_id, {
            'type': 'assistant_start'
        })
        
        # Generate contextual response
        if content_modification_requested:
            await self._handle_content_modification(message, session, connection_manager, improvement_type)
        elif improvement_type:
            await self._handle_improvement_suggestion(message, session, connection_manager, improvement_type)
        elif self._is_analysis_question(message):
            await self._handle_analysis_question(message, session, connection_manager)
        else:
            await self._handle_general_conversation(message, session, connection_manager)
        
        # Send completion signal
        await connection_manager.send_message(session_id, {
            'type': 'assistant_complete'
        })
    
    def _analyze_improvement_intent(self, message: str) -> Optional[str]:
        """Analyze what type of improvement the user is requesting"""
        message_lower = message.lower()
        
        for improvement_type, pattern in self.improvement_patterns.items():
            if any(keyword in message_lower for keyword in pattern['keywords']):
                return improvement_type
        
        return None
    
    def _is_content_modification_request(self, message: str) -> bool:
        """Check if user is requesting actual content changes"""
        modification_keywords = [
            'change', 'modify', 'update', 'rewrite', 'edit', 'alter', 'replace',
            'make it', 'turn this into', 'convert to', 'apply', 'implement'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in modification_keywords)
    
    def _is_analysis_question(self, message: str) -> bool:
        """Check if user is asking about the analysis data"""
        analysis_keywords = [
            'reddit', 'pain points', 'analysis', 'research', 'data', 'scores',
            'why', 'how', 'what', 'explain', 'show me', 'tell me about'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in analysis_keywords)
    
    async def _handle_content_modification(self, message: str, session: Dict, connection_manager, improvement_type: str):
        """Handle requests to actually modify the content"""
        
        session_id = session['session_id']
        current_content = session['current_content']
        analysis_results = session['analysis_results']
        
        # Build comprehensive context
        context = self._build_comprehensive_context(session, improvement_type)
        
        # Create modification prompt
        prompt = f"""You are an expert content editor helping to modify content based on the user's request.

USER REQUEST: {message}

IMPROVEMENT TYPE DETECTED: {improvement_type or 'general'}

CURRENT CONTENT (first 2000 chars):
{current_content[:2000]}...

CONTEXT & ANALYSIS DATA:
{context}

The user wants to modify the content. Please:

1. First, briefly explain what specific changes you'll make and why
2. Then provide the COMPLETE updated content that incorporates their request
3. Make the improvements substantial and meaningful
4. Ensure the content addresses the Reddit pain points identified
5. Maintain the professional tone and expertise level

Start with: "I'll make the following improvements:" then explain briefly, then provide the full updated content.

Be conversational and helpful like Claude, but focus on delivering real value."""

        # Stream the response
        response_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=4000):
            response_chunks.append(chunk)
            await connection_manager.send_message(session_id, {
                'type': 'assistant_stream',
                'chunk': chunk
            })
        
        response = ''.join(response_chunks)
        
        # Add response to conversation history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat(),
            'intent': 'content_modification',
            'improvement_type': improvement_type
        })
        
        # Extract and update content if provided
        updated_content = self._extract_updated_content(response)
        if updated_content and len(updated_content) > 500:
            session['current_content'] = updated_content
            
            # Apply metrics improvements
            await self._apply_improvement_metrics(session, improvement_type, connection_manager)
            
            # Notify about content update
            await connection_manager.send_message(session_id, {
                'type': 'content_updated',
                'content': updated_content,
                'improvement_applied': True
            })
    
    async def _handle_improvement_suggestion(self, message: str, session: Dict, connection_manager, improvement_type: str):
        """Handle requests for improvement suggestions without immediate application"""
        
        session_id = session['session_id']
        analysis_results = session['analysis_results']
        
        # Get specific improvement actions for this type
        pattern = self.improvement_patterns.get(improvement_type, {})
        suggested_actions = pattern.get('actions', [])
        
        # Build context for suggestions
        context = self._build_improvement_context(session, improvement_type)
        
        prompt = f"""You are an expert content strategist providing specific improvement recommendations.

USER REQUEST: {message}

IMPROVEMENT TYPE: {improvement_type}

ANALYSIS CONTEXT:
{context}

SUGGESTED ACTIONS FOR {improvement_type.upper()}:
{chr(10).join(['• ' + action for action in suggested_actions])}

Provide specific, actionable recommendations based on the analysis data. Include:

1. Why these improvements will help (reference the Reddit pain points)
2. Specific implementation steps
3. Expected impact on metrics
4. Ask if they want you to apply these improvements to the content

Be encouraging and specific. Reference the actual data from the analysis."""

        # Stream the response
        response_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=2500):
            response_chunks.append(chunk)
            await connection_manager.send_message(session_id, {
                'type': 'assistant_stream',
                'chunk': chunk
            })
        
        response = ''.join(response_chunks)
        
        # Add to conversation history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat(),
            'intent': 'improvement_suggestion',
            'improvement_type': improvement_type
        })
    
    async def _handle_analysis_question(self, message: str, session: Dict, connection_manager):
        """Handle questions about the analysis data with rich context"""
        
        session_id = session['session_id']
        analysis_results = session['analysis_results']
        
        # Extract relevant analysis data
        reddit_insights = analysis_results.get('analysis_stages', {}).get('reddit_insights', {})
        eeat_assessment = analysis_results.get('analysis_stages', {}).get('eeat_assessment', {})
        quality_assessment = analysis_results.get('analysis_stages', {}).get('quality_assessment', {})
        
        # Build comprehensive analysis summary
        analysis_summary = self._build_analysis_summary(analysis_results)
        
        prompt = f"""You are explaining the analysis results to the user in a helpful, conversational way.

USER QUESTION: {message}

COMPREHENSIVE ANALYSIS SUMMARY:
{analysis_summary}

Answer their question about the analysis in a helpful way. Use specific data points and explain what they mean for content strategy. Be encouraging and actionable.

If they're asking about pain points, reference the actual Reddit data.
If they're asking about scores, explain what impacts them and how to improve.
If they're asking about the research process, explain what was analyzed and why it's valuable."""

        # Stream the response
        response_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=2000):
            response_chunks.append(chunk)
            await connection_manager.send_message(session_id, {
                'type': 'assistant_stream',
                'chunk': chunk
            })
        
        response = ''.join(response_chunks)
        
        # Add to conversation history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat(),
            'intent': 'analysis_question'
        })
    
    async def _handle_general_conversation(self, message: str, session: Dict, connection_manager):
        """Handle general conversation with contextual awareness"""
        
        session_id = session['session_id']
        topic = session['form_data'].get('topic', 'your topic')
        
        # Build conversation context
        recent_context = self._get_recent_conversation_context(session)
        capabilities_context = self._build_capabilities_context(session)
        
        prompt = f"""You are a helpful AI content assistant having a conversation about content for "{topic}".

USER MESSAGE: {message}

RECENT CONVERSATION CONTEXT:
{recent_context}

YOUR CAPABILITIES:
{capabilities_context}

Respond in a helpful, conversational way like Claude. Be encouraging and offer specific ways you can help with their content. Reference the analysis data when relevant."""

        # Stream the response
        response_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=1500):
            response_chunks.append(chunk)
            await connection_manager.send_message(session_id, {
                'type': 'assistant_stream',
                'chunk': chunk
            })
        
        response = ''.join(response_chunks)
        
        # Add to conversation history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat(),
            'intent': 'general_conversation'
        })
    
    async def _apply_improvement_metrics(self, session: Dict, improvement_type: str, connection_manager):
        """Apply realistic improvement metrics based on the improvement type"""
        
        session_id = session['session_id']
        pattern = self.improvement_patterns.get(improvement_type, {})
        score_impact = pattern.get('score_impact', {})
        
        # Update live metrics
        live_metrics = session['live_metrics']
        live_metrics['improvements_applied'] += 1
        
        # Apply specific score improvements
        for metric, improvement in score_impact.items():
            if metric in live_metrics:
                live_metrics[metric] = min(10.0, live_metrics[metric] + improvement)
        
        # Recalculate overall score
        if 'trust_score' in live_metrics and 'quality_score' in live_metrics:
            live_metrics['overall_score'] = (live_metrics['trust_score'] + live_metrics['quality_score']) / 2
        
        # Update word count if content was expanded
        if 'word_count' in score_impact:
            live_metrics['content_word_count'] = live_metrics.get('content_word_count', 0) + score_impact['word_count']
        
        # Send metrics update
        await connection_manager.send_message(session_id, {
            'type': 'metrics_update',
            'metrics': live_metrics,
            'improvement_applied': {
                'type': improvement_type,
                'impact': score_impact
            }
        })
        
        logger.info(f"Applied {improvement_type} improvements to session {session_id}")
    
    def _build_comprehensive_context(self, session: Dict, improvement_type: str) -> str:
        """Build comprehensive context for content modification"""
        form_data = session['form_data']
        analysis_results = session['analysis_results']
        
        context_parts = [
            f"Topic: {form_data.get('topic', 'Unknown')}",
            f"Target Audience: {form_data.get('target_audience', 'General')}",
            f"Industry: {form_data.get('industry', 'General')}",
            f"Current Content Length: {len(session['current_content'])} characters"
        ]
        
        # Add Reddit insights
        reddit_insights = analysis_results.get('analysis_stages', {}).get('reddit_insights', {})
        if reddit_insights:
            pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
            if pain_points:
                top_pains = list(pain_points.keys())[:3]
                context_parts.append(f"Top Customer Pain Points: {', '.join(top_pains)}")
            
            quotes = reddit_insights.get('customer_voice', {}).get('authentic_quotes', [])
            if quotes:
                context_parts.append(f"Sample Customer Quote: \"{quotes[0][:100]}...\"")
        
        # Add current scores
        live_metrics = session.get('live_metrics', {})
        context_parts.append(f"Current Trust Score: {live_metrics.get('trust_score', 'N/A')}")
        context_parts.append(f"Current Quality Score: {live_metrics.get('quality_score', 'N/A')}")
        
        return '\n'.join(context_parts)
    
    def _build_improvement_context(self, session: Dict, improvement_type: str) -> str:
        """Build context for improvement suggestions"""
        analysis_results = session['analysis_results']
        
        context_parts = []
        
        # Add specific context based on improvement type
        if improvement_type == 'trust_improvement':
            eeat = analysis_results.get('analysis_stages', {}).get('eeat_assessment', {})
            context_parts.append(f"Current Trust Score: {eeat.get('overall_trust_score', 'N/A')}")
            recommendations = eeat.get('improvement_recommendations', [])
            if recommendations:
                context_parts.append(f"E-E-A-T Recommendations: {', '.join(recommendations[:3])}")
        
        elif improvement_type == 'pain_point_focus':
            reddit_insights = analysis_results.get('analysis_stages', {}).get('reddit_insights', {})
            pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
            if pain_points:
                context_parts.append(f"Top Pain Points: {', '.join(list(pain_points.keys())[:5])}")
        
        return '\n'.join(context_parts) if context_parts else "General improvement context"
    
    def _build_analysis_summary(self, analysis_results: Dict) -> str:
        """Build comprehensive analysis summary"""
        summary_parts = []
        
        # Reddit analysis summary
        reddit_insights = analysis_results.get('analysis_stages', {}).get('reddit_insights', {})
        if reddit_insights:
            metadata = reddit_insights.get('research_metadata', {})
            summary_parts.append(f"Reddit Analysis: {metadata.get('total_posts_analyzed', 0)} posts analyzed")
            
            pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
            if pain_points:
                top_pain = max(pain_points.items(), key=lambda x: x[1])[0]
                summary_parts.append(f"Top Pain Point: {top_pain} ({pain_points[top_pain]} mentions)")
        
        # E-E-A-T summary
        eeat = analysis_results.get('analysis_stages', {}).get('eeat_assessment', {})
        if eeat:
            summary_parts.append(f"Trust Score: {eeat.get('overall_trust_score', 'N/A')}/10")
            components = eeat.get('component_scores', {})
            if components:
                lowest_component = min(components.items(), key=lambda x: x[1])
                summary_parts.append(f"Lowest E-E-A-T Component: {lowest_component[0]} ({lowest_component[1]})")
        
        # Quality summary
        quality = analysis_results.get('analysis_stages', {}).get('quality_assessment', {})
        if quality:
            summary_parts.append(f"Quality Score: {quality.get('overall_score', 'N/A')}/10")
        
        return '\n'.join(summary_parts) if summary_parts else "Analysis summary not available"
    
    def _build_capabilities_context(self, session: Dict) -> str:
        """Build context about what the assistant can do"""
        capabilities = [
            "• Modify and improve your content in real-time",
            "• Explain analysis results and Reddit research findings",
            "• Provide specific improvement recommendations",
            "• Update trust scores, quality scores, and other metrics",
            "• Address customer pain points identified in Reddit research",
            "• Optimize content for SEO and user experience",
            "• Make content more beginner-friendly or technical as needed"
        ]
        
        return '\n'.join(capabilities)
    
    def _get_recent_conversation_context(self, session: Dict) -> str:
        """Get recent conversation context for continuity"""
        history = session.get('conversation_history', [])[-4:]  # Last 4 messages
        
        context_parts = []
        for msg in history:
            role = msg['role'].upper()
            content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
            context_parts.append(f"{role}: {content}")
        
        return '\n'.join(context_parts) if context_parts else "No recent conversation"
    
    def _extract_updated_content(self, response: str) -> Optional[str]:
        """Extract updated content from assistant response"""
        # Look for content markers
        content_markers = [
            'updated content:',
            'revised content:',
            'new content:',
            'modified content:',
            'complete content:',
            'here\'s the improved content:',
            'here\'s the updated version:'
        ]
        
        response_lower = response.lower()
        start_pos = -1
        
        for marker in content_markers:
            pos = response_lower.find(marker)
            if pos != -1:
                start_pos = pos + len(marker)
                break
        
        if start_pos == -1:
            return None
        
        # Extract content from start position to end
        content_part = response[start_pos:].strip()
        
        # Remove any trailing conversation text
        end_markers = [
            'what do you think',
            'does this work',
            'how does this look',
            'let me know',
            'would you like',
            'any other changes'
        ]
        
        for end_marker in end_markers:
            pos = content_part.lower().find(end_marker)
            if pos != -1:
                content_part = content_part[:pos].strip()
                break
        
        return content_part if len(content_part) > 100 else None
