"""
StreamingChatAgent - Real Claude-style streaming chat for content improvement

This file replaces the old ContinuousImprovementChat system.
Put this file at: src/agents/streaming_chat.py
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StreamingChatAgent:
    """Claude-style streaming chat agent for real-time content improvement"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        logger.info("✅ Streaming Chat Agent initialized")
    
    async def process_message(self, message: str, session: Dict, connection_manager) -> None:
        """Process chat message and stream response like Claude"""
        
        session_id = session['session_id']
        
        # Add user message to conversation history
        session['conversation_history'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Determine intent and generate appropriate response
        intent = self._analyze_message_intent(message)
        
        # Send typing indicator
        await connection_manager.send_message(session_id, {
            'type': 'assistant_start'
        })
        
        # Generate context-aware response based on intent
        if intent == 'content_modification':
            await self._handle_content_modification(message, session, connection_manager)
        elif intent == 'content_improvement':
            await self._handle_content_improvement(message, session, connection_manager)
        elif intent == 'question_about_analysis':
            await self._handle_analysis_question(message, session, connection_manager)
        elif intent == 'request_examples':
            await self._handle_example_request(message, session, connection_manager)
        else:
            await self._handle_general_conversation(message, session, connection_manager)
        
        # Send completion signal
        await connection_manager.send_message(session_id, {
            'type': 'assistant_complete'
        })
    
    def _analyze_message_intent(self, message: str) -> str:
        """Analyze user message to determine intent"""
        message_lower = message.lower()
        
        # Content modification requests
        if any(word in message_lower for word in [
            'change', 'modify', 'update', 'rewrite', 'edit', 'alter', 'replace'
        ]):
            return 'content_modification'
        
        # Content improvement requests
        if any(word in message_lower for word in [
            'improve', 'better', 'enhance', 'optimize', 'strengthen', 'boost'
        ]):
            return 'content_improvement'
        
        # Questions about analysis
        if any(word in message_lower for word in [
            'why', 'how', 'what', 'explain', 'tell me about', 'show me'
        ]) and any(word in message_lower for word in [
            'reddit', 'analysis', 'pain points', 'research', 'data'
        ]):
            return 'question_about_analysis'
        
        # Example requests
        if any(word in message_lower for word in [
            'example', 'show me', 'demonstrate', 'sample'
        ]):
            return 'request_examples'
        
        return 'general_conversation'
    
    async def _handle_content_modification(self, message: str, session: Dict, connection_manager):
        """Handle requests to modify the content"""
        
        session_id = session['session_id']
        current_content = session['current_content']
        form_data = session['form_data']
        analysis_results = session['analysis_results']
        
        # Build context for content modification
        context = self._build_content_context(session)
        
        prompt = f"""You are helping to modify content based on the user's request.

USER REQUEST: {message}

CURRENT CONTENT (first 1500 chars):
{current_content[:1500]}...

CONTEXT:
{context}

The user wants to modify the content. Please:
1. Explain what changes you'll make
2. Then provide the COMPLETE updated content incorporating their request

Be conversational and helpful like Claude. Start by acknowledging their request, then explain your approach."""

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
            'intent': 'content_modification'
        })
        
        # Check if response contains updated content
        if self._response_contains_updated_content(response):
            await self._extract_and_update_content(response, session, connection_manager)
    
    async def _handle_content_improvement(self, message: str, session: Dict, connection_manager):
        """Handle requests to improve the content"""
        
        session_id = session['session_id']
        current_content = session['current_content']
        reddit_insights = session['analysis_results'].get('reddit_insights', {})
        
        # Extract specific improvement areas
        improvement_focus = self._identify_improvement_focus(message)
        
        # Build improvement suggestions based on Reddit research
        pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
        customer_quotes = reddit_insights.get('customer_voice', {}).get('authentic_quotes', [])
        
        prompt = f"""You are an expert content advisor helping improve content based on REAL Reddit research.

USER REQUEST: {message}

IMPROVEMENT FOCUS: {improvement_focus}

REAL PAIN POINTS FROM REDDIT:
{json.dumps(pain_points, indent=2)}

CUSTOMER QUOTES:
{chr(10).join(['- "' + quote + '"' for quote in customer_quotes[:5]])}

CURRENT CONTENT QUALITY:
- Length: {len(current_content)} characters
- Topic: {session['form_data'].get('topic', 'Unknown')}

Provide specific, actionable improvement suggestions based on the real Reddit data. Be conversational and explain:
1. What specific improvements you recommend
2. Why these improvements will help (based on the Reddit pain points)
3. How to implement them

If they ask you to apply the improvements, generate the updated content."""

        # Stream the response
        response_chunks = []
        async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=3000):
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
            'intent': 'content_improvement'
        })
    
    async def _handle_analysis_question(self, message: str, session: Dict, connection_manager):
        """Handle questions about the Reddit analysis"""
        
        session_id = session['session_id']
        reddit_insights = session['analysis_results'].get('reddit_insights', {})
        
        # Extract relevant analysis data
        pain_points = reddit_insights.get('critical_pain_points', {})
        customer_voice = reddit_insights.get('customer_voice', {})
        insights = reddit_insights.get('insights', {})
        metadata = reddit_insights.get('research_metadata', {})
        
        prompt = f"""You are explaining Reddit research results to the user in a conversational way.

USER QUESTION: {message}

REDDIT ANALYSIS DATA:
- Posts Analyzed: {metadata.get('total_posts_analyzed', 0)}
- Subreddits Researched: {metadata.get('subreddits_researched', 0)}
- Data Source: {metadata.get('data_source', 'Unknown')}

PAIN POINTS FOUND:
{json.dumps(pain_points.get('top_pain_points', {}), indent=2)}

CUSTOMER QUOTES:
{chr(10).join(['- "' + quote + '"' for quote in customer_voice.get('authentic_quotes', [])[:5]])}

INSIGHTS:
- Most Common Pain: {insights.get('most_common_pain', 'Unknown')}
- Emotional Intensity: {insights.get('emotional_intensity', 0):.1f}
- Problem Severity: {pain_points.get('problem_severity', 'Unknown')}

Answer their question about the Reddit research in a helpful, conversational way. Explain what the data means and why it's useful for content creation."""

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
    
    async def _handle_example_request(self, message: str, session: Dict, connection_manager):
        """Handle requests for examples"""
        
        session_id = session['session_id']
        topic = session['form_data'].get('topic', 'the topic')
        reddit_insights = session['analysis_results'].get('reddit_insights', {})
        
        prompt = f"""The user is asking for examples related to {topic}.

USER REQUEST: {message}

REDDIT INSIGHTS AVAILABLE:
- Pain Points: {list(reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {}).keys())[:5]}
- Customer Quotes: {reddit_insights.get('customer_voice', {}).get('authentic_quotes', [])[:3]}

Provide helpful, specific examples based on their request. Be conversational and practical. 

If they're asking for examples of:
- Content improvements: Show specific before/after examples
- Pain point solutions: Give concrete examples of how to address the Reddit pain points
- Customer language: Use the actual Reddit quotes as examples
- Writing techniques: Show specific examples related to their topic

Make your examples actionable and relevant to their content about {topic}."""

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
            'intent': 'example_request'
        })
    
    async def _handle_general_conversation(self, message: str, session: Dict, connection_manager):
        """Handle general conversation about the content and analysis"""
        
        session_id = session['session_id']
        topic = session['form_data'].get('topic', 'your topic')
        
        # Build conversation context
        recent_context = self._get_recent_conversation_context(session)
        
        prompt = f"""You are a helpful AI content assistant having a conversation about content for "{topic}".

USER MESSAGE: {message}

RECENT CONVERSATION CONTEXT:
{recent_context}

AVAILABLE CAPABILITIES:
- Modify or rewrite the content
- Improve content quality based on Reddit research
- Explain the Reddit analysis findings
- Provide examples and suggestions
- Answer questions about content strategy

Respond in a helpful, conversational way like Claude. Be encouraging and offer specific ways you can help with their content."""

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
    
    def _build_content_context(self, session: Dict) -> str:
        """Build context about the content and analysis"""
        form_data = session['form_data']
        reddit_insights = session['analysis_results'].get('reddit_insights', {})
        
        context_parts = [
            f"Topic: {form_data.get('topic', 'Unknown')}",
            f"Target Audience: {form_data.get('target_audience', 'Unknown')}",
            f"Content Length: {len(session['current_content'])} characters"
        ]
        
        # Add Reddit insights context
        pain_points = reddit_insights.get('critical_pain_points', {}).get('top_pain_points', {})
        if pain_points:
            top_pain = max(pain_points.items(), key=lambda x: x[1])[0]
            context_parts.append(f"Main Customer Pain Point: {top_pain}")
        
        return '\n'.join(context_parts)
    
    def _identify_improvement_focus(self, message: str) -> str:
        """Identify what aspect of content to improve"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['beginner', 'simple', 'easy', 'basic']):
            return 'beginner_friendliness'
        elif any(word in message_lower for word in ['example', 'case study', 'specific']):
            return 'examples_and_specificity'
        elif any(word in message_lower for word in ['trust', 'credibility', 'authority']):
            return 'trust_and_authority'
        elif any(word in message_lower for word in ['pain', 'problem', 'customer']):
            return 'pain_point_addressing'
        elif any(word in message_lower for word in ['seo', 'search', 'ranking']):
            return 'seo_optimization'
        elif any(word in message_lower for word in ['structure', 'format', 'organization']):
            return 'content_structure'
        else:
            return 'general_quality'
    
    def _get_recent_conversation_context(self, session: Dict) -> str:
        """Get recent conversation context for continuity"""
        history = session['conversation_history'][-4:]  # Last 4 messages
        
        context_parts = []
        for msg in history:
            role = msg['role'].upper()
            content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
            context_parts.append(f"{role}: {content}")
        
        return '\n'.join(context_parts) if context_parts else "No recent conversation"
    
    def _response_contains_updated_content(self, response: str) -> bool:
        """Check if response contains updated content that should replace current content"""
        indicators = [
            'here\'s the updated content',
            'updated version:',
            'revised content:',
            'new content:',
            'modified content:',
            'complete updated content'
        ]
        
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in indicators)
    
    async def _extract_and_update_content(self, response: str, session: Dict, connection_manager):
        """Extract updated content from response and update the session"""
        
        session_id = session['session_id']
        
        # Use a more sophisticated extraction method
        lines = response.split('\n')
        content_started = False
        updated_content_lines = []
        
        for line in lines:
            line_lower = line.lower()
            
            # Look for content start indicators
            if any(indicator in line_lower for indicator in [
                'updated content:', 'revised content:', 'new content:', 'modified content:'
            ]):
                content_started = True
                continue
            
            # Stop at conversation indicators
            if content_started and any(phrase in line_lower for phrase in [
                'what do you think', 'does this work', 'how does this look', 'let me know'
            ]):
                break
            
            if content_started and line.strip():
                updated_content_lines.append(line)
        
        if updated_content_lines:
            updated_content = '\n'.join(updated_content_lines).strip()
            
            # Only update if we have substantial content
            if len(updated_content) > 500:
                session['current_content'] = updated_content
                
                # Notify about content update
                await connection_manager.send_message(session_id, {
                    'type': 'content_updated',
                    'content': updated_content
                })
                
                logger.info(f"Content updated for session {session_id}: {len(updated_content)} characters")

# Backward compatibility class name (in case other files import the old name)
class ContinuousImprovementChat(StreamingChatAgent):
    """Backward compatibility wrapper for old import statements"""
    
    def __init__(self, llm_client=None):
        super().__init__(llm_client)
        logger.warning("Using ContinuousImprovementChat compatibility mode. Update imports to use StreamingChatAgent.")
    
    def initialize_session(self, analysis_results):
        """Compatibility method for old initialization"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {'session_id': session_id}
    
    async def process_message(self, message: str, session_id: str = None):
        """Compatibility method - redirects to new streaming system"""
        logger.warning("Old process_message called. This should be handled by the new streaming system.")
        return {"message": "Please use the new streaming chat interface."}
    
    def get_session_metrics(self, session_id: str = None):
        """Compatibility method"""
        return {
            "improvements_applied": 0,
            "total_quality_increase": 0.0,
            "total_trust_increase": 0.0
        }
