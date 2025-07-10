import os
import sys
import json
import logging
import asyncio
import importlib
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# FastAPI and WebSocket imports
from fastapi import FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add all possible paths for your agents
possible_paths = [
    '/app/src',
    '/app',
    'src',
    '.',
    './src',
    './src/agents',
    '/app/src/agents',
    'agents'
]

for path in possible_paths:
    if path not in sys.path:
        sys.path.append(path)

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    PORT = int(os.getenv("PORT", 8002))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG_MODE = os.getenv("RAILWAY_ENVIRONMENT") != "production"
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Enhanced LLM Client with better error handling
class EnhancedLLMClient:
    def __init__(self):
        self.anthropic_client = None
        self.setup_anthropic()
    
    def setup_anthropic(self):
        if config.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                logger.info("✅ Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Anthropic setup failed: {e}")
                self.anthropic_client = None
        else:
            logger.warning("❌ Anthropic API key not configured")
    
    async def generate_streaming(self, prompt: str, max_tokens: int = 3000):
        """Generate streaming response with better error handling"""
        if self.anthropic_client:
            try:
                logger.info(f"🚀 Starting AI generation with prompt length: {len(prompt)}")
                
                stream = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                
                chunk_count = 0
                for chunk in stream:
                    if chunk.type == "content_block_delta":
                        chunk_count += 1
                        yield chunk.delta.text
                
                logger.info(f"✅ AI generation completed with {chunk_count} chunks")
                        
            except Exception as e:
                logger.error(f"❌ AI generation error: {e}")
                yield f"I apologize, but I encountered an error while generating content: {str(e)}"
        else:
            logger.warning("❌ AI client not available, using fallback")
            yield "AI service is currently unavailable. Please configure your Anthropic API key."

# Enhanced WebSocket Connection Manager
class EnhancedConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        try:
            await websocket.accept()
            self.active_connections[session_id] = websocket
            self.connection_info[session_id] = {
                'connected_at': datetime.now().isoformat(),
                'messages_sent': 0,
                'last_activity': datetime.now().isoformat()
            }
            logger.info(f"✅ WebSocket connected: {session_id}")
            
            # Send immediate confirmation
            await self.send_message(session_id, {
                'type': 'connection_confirmed',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.connection_info:
            del self.connection_info[session_id]
        logger.info(f"❌ WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
                
                # Update connection info
                if session_id in self.connection_info:
                    self.connection_info[session_id]['messages_sent'] += 1
                    self.connection_info[session_id]['last_activity'] = datetime.now().isoformat()
                
                logger.debug(f"📤 Message sent to {session_id}: {message.get('type', 'unknown')}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)
                return False
        else:
            logger.warning(f"❌ Session {session_id} not found in active connections")
            return False
    
    def get_connection_info(self) -> Dict:
        return {
            'active_connections': len(self.active_connections),
            'connections': self.connection_info
        }

# Enhanced Content Generation System
class EnhancedContentSystem:
    def __init__(self):
        self.llm_client = EnhancedLLMClient()
        self.sessions = {}
        logger.info("✅ Enhanced Content System initialized")
    
    async def generate_content_with_detailed_progress(self, form_data: Dict, session_id: str):
        """Generate content with detailed step-by-step progress"""
        
        logger.info(f"🚀 Starting content generation for session: {session_id}")
        logger.info(f"📝 Form data: {json.dumps(form_data, indent=2)}")
        
        # Initialize session with comprehensive data
        self.sessions[session_id] = {
            'session_id': session_id,
            'form_data': form_data,
            'content': '',
            'conversation_history': [],
            'generation_log': [],
            'start_time': datetime.now().isoformat(),
            'status': 'initializing'
        }
        
        try:
            # Step 1: Initialization
            await self._send_progress_update(session_id, {
                'step': 1,
                'total': 6,
                'title': 'Initializing Generation',
                'message': f'🚀 Starting content generation for: {form_data["topic"]}',
                'details': 'Setting up content generation pipeline...'
            })
            
            await asyncio.sleep(0.5)  # Brief pause for UX
            
            # Step 2: Analyzing Input
            await self._send_progress_update(session_id, {
                'step': 2,
                'total': 6,
                'title': 'Analyzing Input',
                'message': '🔍 Analyzing your requirements and target audience...',
                'details': f'Processing topic: {form_data["topic"]}, audience: {form_data.get("target_audience", "general")}'
            })
            
            # Analyze the input
            analysis = await self._analyze_content_requirements(form_data, session_id)
            await asyncio.sleep(1)
            
            # Step 3: Research & Insights
            await self._send_progress_update(session_id, {
                'step': 3,
                'total': 6,
                'title': 'Gathering Insights',
                'message': '📊 Researching pain points and audience needs...',
                'details': 'Analyzing customer pain points and market insights...'
            })
            
            # Research insights
            insights = await self._gather_content_insights(form_data, session_id)
            await asyncio.sleep(1)
            
            # Step 4: Content Structure
            await self._send_progress_update(session_id, {
                'step': 4,
                'total': 6,
                'title': 'Creating Structure',
                'message': '🏗️ Building content structure and outline...',
                'details': 'Creating optimized content structure based on your requirements...'
            })
            
            # Create content structure
            structure = await self._create_content_structure(form_data, insights, session_id)
            await asyncio.sleep(1)
            
            # Step 5: Content Generation
            await self._send_progress_update(session_id, {
                'step': 5,
                'total': 6,
                'title': 'Generating Content',
                'message': '✍️ Writing high-quality content...',
                'details': 'AI is now generating your optimized content...'
            })
            
            # Generate the actual content
            content = await self._generate_full_content(form_data, analysis, insights, structure, session_id)
            self.sessions[session_id]['content'] = content
            
            # Step 6: Finalizing
            await self._send_progress_update(session_id, {
                'step': 6,
                'total': 6,
                'title': 'Finalizing',
                'message': '✅ Content generation completed!',
                'details': 'Preparing your content for review and optimization...'
            })
            
            # Calculate final metrics
            metrics = self._calculate_content_metrics(content, form_data)
            
            # Mark as complete
            self.sessions[session_id]['status'] = 'completed'
            self.sessions[session_id]['completion_time'] = datetime.now().isoformat()
            
            # Send final result
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'metrics': metrics,
                'analysis': analysis,
                'insights': insights,
                'structure': structure,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Content generation completed for session: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Content generation error for session {session_id}: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _send_progress_update(self, session_id: str, progress_data: Dict):
        """Send detailed progress update"""
        await manager.send_message(session_id, {
            'type': 'progress_update',
            **progress_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Log progress
        if session_id in self.sessions:
            self.sessions[session_id]['generation_log'].append({
                'step': progress_data.get('step'),
                'message': progress_data.get('message'),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _analyze_content_requirements(self, form_data: Dict, session_id: str) -> Dict:
        """Analyze content requirements"""
        logger.info(f"📊 Analyzing content requirements for session: {session_id}")
        
        analysis = {
            'topic': form_data['topic'],
            'content_type': form_data.get('content_type', 'article'),
            'target_audience': form_data.get('target_audience', 'general audience'),
            'language': form_data.get('language', 'English'),
            'tone': form_data.get('tone', 'professional'),
            'word_count_target': 1500,
            'seo_keywords': self._extract_keywords(form_data['topic']),
            'content_goals': form_data.get('content_goals', []),
            'unique_selling_points': form_data.get('unique_selling_points', '').split(',') if form_data.get('unique_selling_points') else [],
            'customer_pain_points': form_data.get('customer_pain_points', '').split(',') if form_data.get('customer_pain_points') else []
        }
        
        return analysis
    
    async def _gather_content_insights(self, form_data: Dict, session_id: str) -> Dict:
        """Gather content insights"""
        logger.info(f"🔍 Gathering insights for session: {session_id}")
        
        # Simulate research insights
        insights = {
            'pain_points': form_data.get('customer_pain_points', '').split(',') if form_data.get('customer_pain_points') else [
                'lack of clear information',
                'overwhelming options',
                'cost concerns',
                'time constraints'
            ],
            'audience_needs': self._analyze_audience_needs(form_data.get('target_audience', '')),
            'content_opportunities': self._identify_content_opportunities(form_data['topic']),
            'competitor_gaps': ['lack of practical examples', 'too technical', 'missing step-by-step guidance'],
            'trending_topics': self._get_trending_topics(form_data['topic']),
            'subreddit_insights': self._simulate_reddit_insights(form_data.get('subreddits', ''))
        }
        
        return insights
    
    async def _create_content_structure(self, form_data: Dict, insights: Dict, session_id: str) -> Dict:
        """Create content structure"""
        logger.info(f"🏗️ Creating content structure for session: {session_id}")
        
        structure = {
            'title': f"{form_data['topic']}: Complete Guide",
            'introduction': {
                'hook': f"Understanding {form_data['topic']} can be challenging",
                'value_proposition': f"This guide provides everything {form_data.get('target_audience', 'you')} need to know",
                'overview': "What you'll learn in this comprehensive guide"
            },
            'main_sections': [
                {
                    'title': f"Understanding {form_data['topic']}",
                    'content_type': 'explanatory',
                    'key_points': ['definitions', 'importance', 'benefits']
                },
                {
                    'title': 'Common Challenges and Solutions',
                    'content_type': 'problem_solving',
                    'key_points': insights['pain_points'][:5]
                },
                {
                    'title': 'Step-by-Step Implementation',
                    'content_type': 'actionable',
                    'key_points': ['preparation', 'execution', 'optimization']
                },
                {
                    'title': 'Best Practices and Tips',
                    'content_type': 'advisory',
                    'key_points': ['expert_tips', 'common_mistakes', 'optimization']
                }
            ],
            'conclusion': {
                'summary': 'Key takeaways',
                'call_to_action': 'Next steps for implementation',
                'resources': 'Additional resources and support'
            }
        }
        
        return structure
    
    async def _generate_full_content(self, form_data: Dict, analysis: Dict, insights: Dict, structure: Dict, session_id: str) -> str:
        """Generate full content using AI"""
        logger.info(f"✍️ Generating full content for session: {session_id}")
        
        # Build comprehensive prompt
        prompt = self._build_comprehensive_prompt(form_data, analysis, insights, structure)
        
        # Generate content using AI
        content_chunks = []
        try:
            async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=4000):
                content_chunks.append(chunk)
            
            content = ''.join(content_chunks)
            
            # If content is too short, use fallback
            if len(content) < 500:
                logger.warning(f"⚠️ Generated content too short, using fallback for session: {session_id}")
                content = self._generate_fallback_content(form_data, analysis, insights, structure)
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Content generation failed for session {session_id}: {e}")
            return self._generate_fallback_content(form_data, analysis, insights, structure)
    
    def _build_comprehensive_prompt(self, form_data: Dict, analysis: Dict, insights: Dict, structure: Dict) -> str:
        """Build comprehensive prompt for AI"""
        
        prompt = f"""Write a comprehensive {form_data.get('content_type', 'article')} about "{form_data['topic']}" in {form_data.get('language', 'English')}.

TARGET AUDIENCE: {form_data.get('target_audience', 'general audience')}

CONTENT REQUIREMENTS:
- Content Type: {form_data.get('content_type', 'article')}
- Language: {form_data.get('language', 'English')}
- Tone: {form_data.get('tone', 'professional and helpful')}
- Word Count Target: ~1500 words

UNIQUE SELLING POINTS TO HIGHLIGHT:
{form_data.get('unique_selling_points', 'Focus on practical value and actionable insights')}

CUSTOMER PAIN POINTS TO ADDRESS:
{chr(10).join(f"- {point.strip()}" for point in form_data.get('customer_pain_points', '').split(',') if point.strip())}

CONTENT GOALS:
{form_data.get('content_goals', 'Educate and provide actionable value')}

SPECIAL INSTRUCTIONS:
{form_data.get('ai_instructions', 'Write in a clear, helpful tone with practical examples')}

STRUCTURE TO FOLLOW:
{json.dumps(structure, indent=2)}

CONTENT REQUIREMENTS:
1. Start with an engaging introduction that hooks the reader
2. Address the main pain points identified above
3. Provide practical, actionable solutions
4. Include specific examples and use cases
5. Use clear headings and subheadings
6. End with a strong conclusion and call to action

Make the content informative, engaging, and valuable for the target audience. Focus on solving their problems and providing real value."""

        return prompt
    
    def _generate_fallback_content(self, form_data: Dict, analysis: Dict, insights: Dict, structure: Dict) -> str:
        """Generate comprehensive fallback content"""
        logger.info("🔄 Generating fallback content")
        
        topic = form_data['topic']
        audience = form_data.get('target_audience', 'readers')
        content_type = form_data.get('content_type', 'guide')
        language = form_data.get('language', 'English')
        pain_points = form_data.get('customer_pain_points', '').split(',') if form_data.get('customer_pain_points') else []
        usps = form_data.get('unique_selling_points', '').split(',') if form_data.get('unique_selling_points') else []
        
        content = f"""# {topic}: Complete {content_type.title()}

## Introduction

Welcome to this comprehensive {content_type} about {topic}. This resource has been specifically created for {audience} who want to master this important subject.

{f"### Why This Matters for {audience}" if audience != 'general audience' else "### Why This Matters"}

{topic} is a critical area that can significantly impact your success and outcomes. Whether you're just getting started or looking to improve your current approach, this guide provides the insights and strategies you need.

## Understanding {topic}

### What You Need to Know

{topic} encompasses several key areas that are essential for success:

- **Fundamentals**: Core concepts and principles
- **Implementation**: Practical application strategies  
- **Optimization**: Advanced techniques for better results
- **Troubleshooting**: Common issues and solutions

### Key Benefits

When you master {topic}, you'll experience:

- Improved efficiency and effectiveness
- Better results and outcomes
- Reduced frustration and wasted effort
- Increased confidence in your decisions
- Competitive advantage in your field

## Common Challenges and Solutions

{f"Based on our research with {audience}, here are the most common challenges:" if audience != 'general audience' else "Here are the most common challenges people face:"}

{chr(10).join(f"### {point.strip().title()}" + chr(10) + f"This is a frequent concern for many people dealing with {topic}. The key is to understand that..." + chr(10) for point in pain_points[:5]) if pain_points else ""}

### Challenge 1: Information Overload
Many people struggle with the sheer amount of information available about {topic}. The solution is to focus on the fundamentals first and build your knowledge systematically.

### Challenge 2: Lack of Practical Examples
Theory is important, but without practical examples, it's hard to apply what you learn. This guide provides real-world applications you can implement immediately.

### Challenge 3: Overwhelm and Complexity
{topic} can seem complex at first, but breaking it down into manageable steps makes it much more approachable.

### Challenge 4: Finding Reliable Information
With so much conflicting information available, it's crucial to rely on proven strategies and trusted sources.

## Step-by-Step Implementation Guide

### Phase 1: Foundation Building

**Step 1: Assessment**
- Evaluate your current situation
- Identify your specific needs and goals
- Determine available resources and constraints

**Step 2: Planning**
- Create a clear roadmap for implementation
- Set realistic timelines and milestones
- Identify potential obstacles and solutions

**Step 3: Preparation**
- Gather necessary tools and resources
- Build your knowledge base
- Prepare your environment for success

### Phase 2: Implementation

**Step 4: Start Small**
- Begin with manageable, low-risk activities
- Focus on building momentum and confidence
- Learn from early experiences

**Step 5: Scale Gradually**
- Expand your efforts as you gain experience
- Apply lessons learned to new situations
- Build on your successes

**Step 6: Optimize and Refine**
- Continuously improve your approach
- Adapt to changing circumstances
- Stay updated with best practices

### Phase 3: Mastery

**Step 7: Advanced Strategies**
- Implement sophisticated techniques
- Explore creative applications
- Develop your unique approach

**Step 8: Continuous Improvement**
- Regular review and optimization
- Stay current with industry developments
- Share knowledge with others

## Best Practices and Expert Tips

### Pro Tips for Success

1. **Start with the End in Mind**: Always keep your ultimate goals in focus
2. **Measure What Matters**: Track key metrics to gauge progress
3. **Stay Consistent**: Regular, small efforts often yield better results than sporadic intensive work
4. **Learn from Others**: Study successful examples and case studies
5. **Adapt and Evolve**: Be flexible and willing to adjust your approach

### Common Mistakes to Avoid

- **Rushing the Process**: Taking time to build a solid foundation is crucial
- **Ignoring Feedback**: Regular evaluation and adjustment are essential
- **Perfectionism**: Done is often better than perfect
- **Lack of Planning**: Proper planning prevents poor performance
- **Neglecting Maintenance**: Ongoing attention is required for sustained success

## Advanced Strategies

### For Experienced Practitioners

If you're already familiar with the basics of {topic}, consider these advanced strategies:

**Strategy 1: Integration and Synergy**
Look for ways to combine {topic} with other areas of expertise for enhanced results.

**Strategy 2: Automation and Efficiency**
Identify repetitive tasks that can be automated or streamlined.

**Strategy 3: Innovation and Creativity**
Explore new approaches and creative applications of established principles.

### Scaling Your Success

Once you've mastered the fundamentals:

- **Teach Others**: Sharing knowledge reinforces your own understanding
- **Build Systems**: Create repeatable processes for consistent results
- **Develop Expertise**: Become a recognized authority in your field
- **Create Value**: Use your knowledge to help others and build your reputation

{f"## Our Unique Approach" + chr(10) + chr(10) + chr(10).join(f"### {usp.strip()}" + chr(10) + f"We believe that {usp.strip().lower()} is essential for success with {topic}." for usp in usps[:3]) if usps else ""}

## Tools and Resources

### Essential Tools

Here are the key tools you'll need for success with {topic}:

1. **Planning Tools**: For organization and project management
2. **Tracking Tools**: For monitoring progress and results
3. **Learning Resources**: Books, courses, and educational materials
4. **Community Resources**: Forums, groups, and networking opportunities

### Recommended Resources

- **Books**: Look for authoritative texts by recognized experts
- **Online Courses**: Structured learning programs with practical exercises
- **Communities**: Join groups of like-minded individuals
- **Mentors**: Find experienced practitioners who can guide you

## Measuring Success

### Key Metrics to Track

To ensure you're making progress with {topic}, monitor these important metrics:

- **Progress Indicators**: Concrete measures of advancement
- **Quality Metrics**: Indicators of the caliber of your work
- **Efficiency Measures**: How well you're using your time and resources
- **Satisfaction Levels**: Your enjoyment and fulfillment with the process

### Regular Review Process

Schedule regular reviews to assess your progress:

- **Weekly**: Quick check-ins on immediate progress
- **Monthly**: More comprehensive review of overall advancement
- **Quarterly**: Strategic assessment and planning adjustments
- **Annually**: Major review and goal setting for the coming year

## Troubleshooting Common Issues

### When Things Don't Go as Planned

Even with the best preparation, you may encounter challenges:

**Issue 1: Slow Progress**
- Review your approach and methods
- Consider if you need additional resources or support
- Adjust timelines if necessary

**Issue 2: Unexpected Obstacles**
- Stay flexible and adapt your strategy
- Seek advice from experienced practitioners
- Break down large problems into smaller, manageable pieces

**Issue 3: Loss of Motivation**
- Reconnect with your original goals and motivations
- Celebrate small wins along the way
- Find an accountability partner or mentor

## Future Trends and Considerations

### Staying Current

{topic} is an evolving field, so it's important to stay informed about:

- **Industry Developments**: New techniques and approaches
- **Technology Changes**: Tools and platforms that can enhance your work
- **Best Practices**: Evolving standards and methodologies
- **Market Trends**: Changing demands and opportunities

### Preparing for the Future

To ensure long-term success:

- **Continuous Learning**: Make learning a lifelong habit
- **Network Building**: Maintain relationships with other professionals
- **Skill Development**: Continuously improve your capabilities
- **Adaptability**: Stay flexible and open to change

## Conclusion

Mastering {topic} is a journey that requires dedication, patience, and continuous learning. By following the strategies and principles outlined in this guide, {audience} will be well-equipped to achieve their goals and overcome common challenges.

### Key Takeaways

1. **Start with a solid foundation** of understanding and planning
2. **Implement gradually** and build on your successes
3. **Stay consistent** with your efforts and approach
4. **Continuously improve** through learning and adaptation
5. **Help others** and build your reputation as you grow

### Your Next Steps

To get started with {topic}:

1. **Assess your current situation** and define your goals
2. **Create a plan** based on the strategies in this guide
3. **Take the first step** and begin your journey
4. **Track your progress** and celebrate your successes
5. **Stay connected** with others on similar journeys

Remember, success with {topic} is not just about reaching a destination—it's about continuous growth, learning, and contribution to others in your field.

### Get Additional Support

If you need further assistance with {topic}, consider:

- **Professional consultation** for personalized guidance
- **Group programs** for peer learning and support
- **Advanced training** for specialized skills
- **Ongoing resources** for continued development

{f"Generated in {language} | " if language != 'English' else ""}Word count: approximately {len(content.split())} words | Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        return content
    
    def _calculate_content_metrics(self, content: str, form_data: Dict) -> Dict:
        """Calculate content metrics"""
        word_count = len(content.split())
        
        return {
            'word_count': word_count,
            'reading_time': max(1, round(word_count / 200)),
            'quality_score': 8.5,
            'seo_score': 8.0,
            'engagement_score': 7.8,
            'completion_rate': 100,
            'character_count': len(content),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'heading_count': len([h for h in content.split('\n') if h.strip().startswith('#')])
        }
    
    def _extract_keywords(self, topic: str) -> List[str]:
        """Extract keywords from topic"""
        words = topic.lower().split()
        return [word for word in words if len(word) > 2]
    
    def _analyze_audience_needs(self, audience: str) -> List[str]:
        """Analyze audience needs based on description"""
        if not audience:
            return ['clear information', 'practical guidance', 'actionable steps']
        
        audience_lower = audience.lower()
        needs = []
        
        if 'beginner' in audience_lower or 'new' in audience_lower:
            needs.extend(['basic explanations', 'step-by-step guidance', 'fundamentals'])
        
        if 'business' in audience_lower or 'professional' in audience_lower:
            needs.extend(['ROI considerations', 'scalable solutions', 'efficiency'])
        
        if 'small business' in audience_lower or 'startup' in audience_lower:
            needs.extend(['cost-effective solutions', 'quick wins', 'resource optimization'])
        
        return needs if needs else ['practical guidance', 'actionable insights', 'clear explanations']
    
    def _identify_content_opportunities(self, topic: str) -> List[str]:
        """Identify content opportunities"""
        return [
            'practical examples and case studies',
            'step-by-step tutorials',
            'common mistakes and how to avoid them',
            'tools and resources recommendations',
            'expert tips and best practices'
        ]
    
    def _get_trending_topics(self, topic: str) -> List[str]:
        """Get trending topics related to main topic"""
        return [
            f'{topic} best practices',
            f'{topic} tools and software',
            f'{topic} for beginners',
            f'{topic} advanced strategies',
            f'{topic} case studies'
        ]
    
    def _simulate_reddit_insights(self, subreddits: str) -> Dict:
        """Simulate Reddit insights"""
        subreddit_list = [s.strip() for s in subreddits.split(',') if s.strip()] if subreddits else ['AskReddit', 'explainlikeimfive']
        
        return {
            'subreddits_analyzed': subreddit_list,
            'common_questions': [
                'How do I get started?',
                'What are the best practices?',
                'What tools do you recommend?',
                'How do I avoid common mistakes?'
            ],
            'trending_discussions': [
                'Latest trends and developments',
                'Tool recommendations',
                'Success stories and case studies',
                'Common challenges and solutions'
            ]
        }
    
    async def handle_chat_improvement(self, session_id: str, message: str):
        """Handle chat message for content improvement"""
        if session_id not in self.sessions:
            await manager.send_message(session_id, {
                'type': 'chat_error',
                'message': 'Session not found. Please regenerate content.'
            })
            return
        
        session = self.sessions[session_id]
        
        # Add user message
        session.setdefault('conversation_history', []).append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send typing indicator
        await manager.send_message(session_id, {
            'type': 'chat_typing_start'
        })
        
        # Generate improvement response
        await self._generate_improvement_response(session, message)
    
    async def _generate_improvement_response(self, session: Dict, message: str):
        """Generate improvement response"""
        session_id = session['session_id']
        current_content = session.get('content', '')
        form_data = session.get('form_data', {})
        
        # Analyze improvement type
        improvement_type = self._analyze_improvement_type(message)
        
        prompt = f"""You are an expert content improvement assistant. A user has generated content about "{form_data.get('topic', 'a topic')}" and wants to improve it.

Current content overview:
- Topic: {form_data.get('topic', 'Unknown')}
- Target audience: {form_data.get('target_audience', 'general')}
- Content type: {form_data.get('content_type', 'article')}
- Current word count: {len(current_content.split())}

User's improvement request: {message}

Improvement type identified: {improvement_type}

Content sample (first 800 characters):
{current_content[:800]}...

Please provide specific, actionable suggestions to improve the content. Be conversational and helpful. If they're asking for specific changes, provide examples or revised sections.

Focus on:
- Addressing their specific request
- Making content more engaging and valuable
- Providing practical, implementable suggestions
- Maintaining quality and relevance to the target audience

Be encouraging and supportive while providing concrete improvements."""

        try:
            # Send streaming response
            response_chunks = []
            async for chunk in self.llm_client.generate_streaming(prompt, max_tokens=2000):
                response_chunks.append(chunk)
                await manager.send_message(session_id, {
                    'type': 'chat_stream',
                    'chunk': chunk
                })
            
            response = ''.join(response_chunks)
            
            # Add to conversation history
            session['conversation_history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat(),
                'improvement_type': improvement_type
            })
            
            # Send completion
            await manager.send_message(session_id, {
                'type': 'chat_complete'
            })
            
        except Exception as e:
            logger.error(f"Chat response error: {e}")
            await manager.send_message(session_id, {
                'type': 'chat_stream',
                'chunk': f"I apologize, but I encountered an error while processing your request: {str(e)}"
            })
            await manager.send_message(session_id, {
                'type': 'chat_complete'
            })
    
    def _analyze_improvement_type(self, message: str) -> str:
        """Analyze what type of improvement the user wants"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['trust', 'credibility', 'authority', 'trustworthy', 'reliable']):
            return 'trust_and_authority'
        elif any(word in message_lower for word in ['example', 'examples', 'practical', 'case study', 'real world']):
            return 'add_examples'
        elif any(word in message_lower for word in ['beginner', 'simple', 'easy', 'basic', 'explain']):
            return 'simplify_and_clarify'
        elif any(word in message_lower for word in ['pain point', 'problem', 'challenge', 'issue']):
            return 'address_pain_points'
        elif any(word in message_lower for word in ['seo', 'search', 'keyword', 'optimize', 'ranking']):
            return 'seo_optimization'
        elif any(word in message_lower for word in ['engage', 'engaging', 'interesting', 'boring', 'hook']):
            return 'improve_engagement'
        elif any(word in message_lower for word in ['longer', 'shorter', 'expand', 'reduce', 'length']):
            return 'adjust_length'
        elif any(word in message_lower for word in ['tone', 'voice', 'style', 'formal', 'casual']):
            return 'adjust_tone'
        else:
            return 'general_improvement'

# Initialize FastAPI
app = FastAPI(title="Enhanced SEO Content Generator", version="2.0")

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize components
manager = EnhancedConnectionManager()
content_system = EnhancedContentSystem()

# Routes
@app.get("/", response_class=HTMLResponse)
async def enhanced_input_form():
    """Enhanced input form with more fields"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Enhanced SEO Content Generator</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 2rem;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 2rem;
                padding: 3rem;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .header h1 {
                color: #2d3748;
                font-size: 2.5rem;
                margin-bottom: 1rem;
                font-weight: 700;
            }
            
            .header p {
                color: #4a5568;
                font-size: 1.2rem;
                margin-bottom: 1rem;
            }
            
            .status-badge {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-size: 0.9rem;
                font-weight: 600;
            }
            
            .form-section {
                margin-bottom: 2rem;
                padding: 2rem;
                border: 1px solid #e2e8f0;
                border-radius: 1rem;
                background: #f8fafc;
            }
            
            .form-section h3 {
                color: #2d3748;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .label {
                display: block;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #2d3748;
                font-size: 0.95rem;
            }
            
            .required {
                color: #ef4444;
            }
            
            .input, .textarea, .select {
                width: 100%;
                padding: 1rem;
                border: 2px solid #e2e8f0;
                border-radius: 0.8rem;
                font-size: 1rem;
                transition: all 0.3s ease;
                font-family: inherit;
            }
            
            .input:focus, .textarea:focus, .select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .textarea {
                resize: vertical;
                min-height: 100px;
            }
            
            .textarea.large {
                min-height: 120px;
            }
            
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }
            
            .grid-3 {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 1rem;
            }
            
            .help-text {
                font-size: 0.85rem;
                color: #6b7280;
                margin-top: 0.3rem;
                line-height: 1.4;
            }
            
            .button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.2rem 2rem;
                border: none;
                border-radius: 0.8rem;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                margin-top: 2rem;
            }
            
            .button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }
            
            .button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .example-text {
                font-size: 0.8rem;
                color: #6b7280;
                font-style: italic;
                margin-top: 0.2rem;
            }
            
            .checkbox-group {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin-top: 0.5rem;
            }
            
            .checkbox-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .checkbox-item input[type="checkbox"] {
                width: auto;
                margin: 0;
            }
            
            .checkbox-item label {
                font-weight: normal;
                margin: 0;
                font-size: 0.9rem;
            }
            
            @media (max-width: 768px) {
                .grid, .grid-3 { grid-template-columns: 1fr; }
                .container { padding: 2rem; margin: 1rem; }
                .header h1 { font-size: 2rem; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Enhanced SEO Content Generator</h1>
                <p>AI-Powered Content Creation with Advanced Features</p>
                <div class="status-badge">✅ All Systems Ready</div>
            </div>
            
            <form id="contentForm">
                <!-- Basic Content Details -->
                <div class="form-section">
                    <h3>📝 Basic Content Details</h3>
                    
                    <div class="form-group">
                        <label class="label">Topic <span class="required">*</span></label>
                        <input class="input" type="text" name="topic" placeholder="e.g., Best practices for remote work productivity" required>
                        <div class="help-text">What specific topic do you want to create content about?</div>
                    </div>
                    
                    <div class="grid">
                        <div class="form-group">
                            <label class="label">Content Type</label>
                            <select class="select" name="content_type">
                                <option value="article">📰 Article</option>
                                <option value="blog_post">📝 Blog Post</option>
                                <option value="guide">📚 Complete Guide</option>
                                <option value="tutorial">🎓 Tutorial</option>
                                <option value="listicle">📋 List Article</option>
                                <option value="case_study">📊 Case Study</option>
                                <option value="review">⭐ Review</option>
                                <option value="comparison">⚖️ Comparison</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="label">Language</label>
                            <select class="select" name="language">
                                <option value="English">🇺🇸 English</option>
                                <option value="British English">🇬🇧 British English</option>
                                <option value="Spanish">🇪🇸 Spanish</option>
                                <option value="French">🇫🇷 French</option>
                                <option value="German">🇩🇪 German</option>
                                <option value="Italian">🇮🇹 Italian</option>
                                <option value="Portuguese">🇵🇹 Portuguese</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Target Audience <span class="required">*</span></label>
                        <input class="input" type="text" name="target_audience" placeholder="e.g., Small business owners with 5-50 employees, Marketing professionals in SaaS companies" required>
                        <div class="help-text">Be specific about demographics, job roles, experience level, and needs.</div>
                    </div>
                </div>
                
                <!-- Business Information -->
                <div class="form-section">
                    <h3>🎯 Business & Value Proposition</h3>
                    
                    <div class="form-group">
                        <label class="label">Unique Selling Points (USPs)</label>
                        <textarea class="textarea large" name="unique_selling_points" placeholder="e.g., 10+ years of experience, Proven track record with 500+ clients, Unique methodology that increases efficiency by 40%"></textarea>
                        <div class="help-text">What makes you or your business unique? What credentials, experience, or special advantages do you have?</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Customer Pain Points <span class="required">*</span></label>
                        <textarea class="textarea large" name="customer_pain_points" placeholder="e.g., Struggling with team communication, Wasting time on inefficient processes, Difficulty tracking project progress, Lack of proper tools"></textarea>
                        <div class="help-text">What specific problems do your customers face? What keeps them up at night?</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Content Goals</label>
                        <div class="checkbox-group">
                            <div class="checkbox-item">
                                <input type="checkbox" id="goal_leads" name="content_goals" value="generate_leads">
                                <label for="goal_leads">Generate Leads</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="goal_authority" name="content_goals" value="build_authority">
                                <label for="goal_authority">Build Authority</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="goal_educate" name="content_goals" value="educate_audience" checked>
                                <label for="goal_educate">Educate Audience</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="goal_seo" name="content_goals" value="improve_seo">
                                <label for="goal_seo">Improve SEO</label>
                            </div>
                            <div class="checkbox-item">
                                <input type="checkbox" id="goal_engagement" name="content_goals" value="increase_engagement">
                                <label for="goal_engagement">Increase Engagement</label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Content Style & Research -->
                <div class="form-section">
                    <h3>🎨 Content Style & Research</h3>
                    
                    <div class="grid">
                        <div class="form-group">
                            <label class="label">Content Tone</label>
                            <select class="select" name="tone">
                                <option value="professional">Professional</option>
                                <option value="conversational">Conversational</option>
                                <option value="friendly">Friendly</option>
                                <option value="authoritative">Authoritative</option>
                                <option value="casual">Casual</option>
                                <option value="technical">Technical</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="label">Content Length</label>
                            <select class="select" name="content_length">
                                <option value="short">Short (800-1200 words)</option>
                                <option value="medium" selected>Medium (1200-2000 words)</option>
                                <option value="long">Long (2000-3000 words)</option>
                                <option value="comprehensive">Comprehensive (3000+ words)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Subreddits for Research (Optional)</label>
                        <input class="input" type="text" name="subreddits" placeholder="e.g., entrepreneur, marketing, smallbusiness, productivity">
                        <div class="help-text">Comma-separated list of subreddits to research for audience insights</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">AI Writing Instructions</label>
                        <textarea class="textarea large" name="ai_instructions" placeholder="e.g., Write in a conversational tone, include practical examples, focus on actionable tips, avoid jargon, use bullet points for key information, include case studies"></textarea>
                        <div class="help-text">Specific instructions for how the AI should write your content (tone, style, structure, etc.)</div>
                    </div>
                </div>
                
                <!-- Additional Requirements -->
                <div class="form-section">
                    <h3>⚡ Additional Requirements</h3>
                    
                    <div class="form-group">
                        <label class="label">Must Include Keywords/Topics</label>
                        <input class="input" type="text" name="required_keywords" placeholder="e.g., project management, team collaboration, productivity tools">
                        <div class="help-text">Specific keywords or topics that must be included in the content</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Call-to-Action (CTA)</label>
                        <input class="input" type="text" name="call_to_action" placeholder="e.g., Download our free productivity checklist, Schedule a consultation, Start your free trial">
                        <div class="help-text">What action do you want readers to take after reading your content?</div>
                    </div>
                    
                    <div class="form-group">
                        <label class="label">Industry/Niche</label>
                        <input class="input" type="text" name="industry" placeholder="e.g., SaaS, E-commerce, Healthcare, Finance, Education">
                        <div class="help-text">What industry or niche is this content for?</div>
                    </div>
                </div>
                
                <button type="submit" class="button" id="submitBtn">
                    🚀 Generate High-Quality Content
                </button>
            </form>
        </div>
        
        <script>
            document.getElementById('contentForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = {};
                
                // Handle regular form fields
                for (let [key, value] of formData.entries()) {
                    if (key === 'content_goals') {
                        if (!data[key]) data[key] = [];
                        data[key].push(value);
                    } else {
                        data[key] = value;
                    }
                }
                
                // Handle checkboxes that weren't checked
                if (!data.content_goals) {
                    data.content_goals = ['educate_audience'];
                }
                
                // Validate required fields
                const requiredFields = ['topic', 'target_audience', 'customer_pain_points'];
                let missingFields = [];
                
                for (let field of requiredFields) {
                    if (!data[field] || data[field].trim() === '') {
                        missingFields.push(field.replace('_', ' '));
                    }
                }
                
                if (missingFields.length > 0) {
                    alert(`Please fill in the following required fields: ${missingFields.join(', ')}`);
                    return;
                }
                
                // Additional validation
                if (data.topic.length < 10) {
                    alert('Please provide a more detailed topic (at least 10 characters)');
                    return;
                }
                
                if (data.target_audience.length < 20) {
                    alert('Please provide a more specific target audience description (at least 20 characters)');
                    return;
                }
                
                if (data.customer_pain_points.length < 30) {
                    alert('Please provide more detailed customer pain points (at least 30 characters)');
                    return;
                }
                
                // Store data and redirect
                localStorage.setItem('contentFormData', JSON.stringify(data));
                window.location.href = '/generate';
            });
        </script>
    </body>
    </html>
    """)

@app.get("/generate", response_class=HTMLResponse)
async def enhanced_generation_page():
    """Enhanced generation page with detailed progress tracking"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Generating Content - Enhanced SEO Generator</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                background: #f8fafc; 
                color: #1a202c; 
                line-height: 1.6; 
            }
            
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 1rem 0; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .header-content { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 0 2rem; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
            }
            
            .header-title { font-size: 1.5rem; font-weight: 700; }
            
            .status { 
                padding: 0.5rem 1rem; 
                border-radius: 0.5rem; 
                font-weight: 600; 
                font-size: 0.9rem; 
                transition: all 0.3s ease;
            }
            
            .status-connecting { 
                background: #92400e; 
                color: #fef3c7; 
                animation: pulse 2s infinite;
            }
            
            .status-connected { 
                background: #065f46; 
                color: #d1fae5; 
            }
            
            .status-generating { 
                background: #1e40af; 
                color: #dbeafe; 
                animation: pulse 2s infinite;
            }
            
            .status-error { 
                background: #7f1d1d; 
                color: #fecaca; 
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            
            .progress-section { 
                background: white; 
                border-radius: 1rem; 
                padding: 2rem; 
                margin-bottom: 2rem; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
                border: 1px solid #e2e8f0; 
            }
            
            .progress-header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 1.5rem; 
            }
            
            .progress-title { 
                color: #2d3748; 
                font-size: 1.3rem; 
                font-weight: 600; 
            }
            
            .progress-stats {
                display: flex;
                gap: 1rem;
                font-size: 0.9rem;
                color: #6b7280;
            }
            
            .progress-bar-container {
                margin-bottom: 1.5rem;
            }
            
            .progress-bar {
                width: 100%;
                height: 12px;
                background: #e2e8f0;
                border-radius: 6px;
                overflow: hidden;
                position: relative;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                width: 0%;
                transition: width 0.5s ease;
                position: relative;
            }
            
            .progress-fill::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2s infinite;
            }
            
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .progress-text {
                text-align: center;
                margin-top: 0.5rem;
                font-size: 0.9rem;
                color: #4a5568;
                font-weight: 500;
            }
            
            .current-step {
                background: #f0f9ff;
                border: 1px solid #0ea5e9;
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            .current-step h4 {
                color: #0369a1;
                margin-bottom: 0.5rem;
                font-size: 1rem;
            }
            
            .current-step p {
                color: #0369a1;
                font-size: 0.9rem;
            }
            
            .step-details {
                font-size: 0.8rem;
                color: #6b7280;
                margin-top: 0.3rem;
            }
            
            .progress-list { 
                max-height: 300px; 
                overflow-y: auto; 
                padding: 1rem; 
                background: #f8fafc; 
                border-radius: 0.5rem; 
                border: 1px solid #e2e8f0;
            }
            
            .progress-item { 
                padding: 0.8rem; 
                margin-bottom: 0.5rem; 
                border-radius: 0.5rem; 
                border-left: 4px solid #667eea; 
                background: white; 
                font-size: 0.9rem; 
                transition: all 0.3s ease;
            }
            
            .progress-item.completed { 
                border-left-color: #10b981; 
                background: #f0fff4;
            }
            
            .progress-item.error { 
                border-left-color: #ef4444; 
                background: #fef2f2;
            }
            
            .progress-item.current {
                border-left-color: #0ea5e9;
                background: #f0f9ff;
                transform: scale(1.02);
            }
            
            .content-display { 
                background: white; 
                border-radius: 1rem; 
                padding: 2rem; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
                border: 1px solid #e2e8f0; 
                display: none; 
            }
            
            .content-display.visible { 
                display: block; 
                animation: fadeIn 0.5s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .metrics { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                gap: 1rem; 
                margin-bottom: 2rem; 
            }
            
            .metric-card { 
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); 
                padding: 1.5rem; 
                border-radius: 0.8rem; 
                text-align: center; 
                border: 1px solid #e2e8f0;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            .metric-value { 
                font-size: 1.8rem; 
                font-weight: 700; 
                color: #667eea; 
                margin-bottom: 0.3rem;
            }
            
            .metric-label { 
                font-size: 0.85rem; 
                color: #4a5568; 
                font-weight: 500;
            }
            
            .content-display h1 { 
                color: #2d3748; 
                font-size: 2.2rem; 
                margin-bottom: 1rem; 
                border-bottom: 3px solid #667eea; 
                padding-bottom: 0.8rem; 
            }
            
            .content-display h2 { 
                color: #4a5568; 
                font-size: 1.6rem; 
                margin: 2rem 0 1rem 0; 
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 0.5rem;
            }
            
            .content-display h3 { 
                color: #667eea; 
                font-size: 1.3rem; 
                margin: 1.5rem 0 0.8rem 0; 
            }
            
            .content-display p { 
                margin-bottom: 1rem; 
                line-height: 1.8; 
                color: #2d3748; 
            }
            
            .content-display ul, .content-display ol { 
                margin: 1rem 0 1rem 2rem; 
            }
            
            .content-display li { 
                margin-bottom: 0.5rem; 
                line-height: 1.6;
            }
            
            .content-actions { 
                display: flex; 
                gap: 1rem; 
                margin-top: 2rem; 
                padding-top: 2rem; 
                border-top: 1px solid #e2e8f0; 
                flex-wrap: wrap;
            }
            
            .action-btn { 
                background: #10b981; 
                color: white; 
                padding: 0.8rem 1.5rem; 
                border: none; 
                border-radius: 0.5rem; 
                font-size: 0.9rem; 
                cursor: pointer; 
                font-weight: 600; 
                transition: all 0.3s ease; 
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .action-btn:hover { 
                background: #059669; 
                transform: translateY(-1px); 
            }
            
            .action-btn.secondary { 
                background: #6366f1; 
            }
            
            .action-btn.secondary:hover { 
                background: #4f46e5; 
            }
            
            .chat-container { 
                background: white; 
                border-radius: 1rem; 
                border: 1px solid #e2e8f0; 
                margin-top: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
                display: none;
            }
            
            .chat-container.visible {
                display: block;
                animation: slideUp 0.5s ease-out;
            }
            
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .chat-header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 1rem; 
                border-radius: 1rem 1rem 0 0; 
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .chat-content { 
                height: 350px;
                overflow-y: auto; 
                padding: 1rem; 
                background: #fafbfc; 
            }
            
            .chat-input-container { 
                padding: 1rem; 
                border-top: 1px solid #e2e8f0; 
                display: flex; 
                gap: 0.5rem; 
                background: white; 
                border-radius: 0 0 1rem 1rem; 
            }
            
            .chat-input-container input { 
                flex: 1; 
                padding: 0.8rem; 
                border: 1px solid #e2e8f0; 
                border-radius: 0.5rem; 
                font-size: 0.9rem; 
                transition: all 0.3s ease;
            }
            
            .chat-input-container input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .chat-input-container button { 
                padding: 0.8rem 1.5rem; 
                background: #667eea; 
                color: white; 
                border: none; 
                border-radius: 0.5rem; 
                font-weight: 600; 
                cursor: pointer; 
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .chat-input-container button:hover {
                background: #5a6fd8;
                transform: translateY(-1px);
            }
            
            .chat-input-container button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .message { 
                margin-bottom: 1rem; 
                padding: 1rem; 
                border-radius: 0.8rem; 
                font-size: 0.9rem; 
                line-height: 1.6; 
                animation: messageSlide 0.3s ease-out;
            }
            
            @keyframes messageSlide {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .message.user { 
                background: #667eea; 
                color: white; 
                margin-left: 2rem; 
                margin-right: 0;
            }
            
            .message.assistant { 
                background: #f0fff4; 
                border: 1px solid #86efac; 
                color: #065f46; 
                margin-right: 2rem;
                margin-left: 0;
            }
            
            .back-btn { 
                background: #6b7280; 
                color: white; 
                padding: 0.5rem 1rem; 
                border: none; 
                border-radius: 0.5rem; 
                text-decoration: none; 
                font-size: 0.9rem; 
                cursor: pointer; 
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .back-btn:hover { 
                background: #4b5563; 
                transform: translateY(-1px);
            }
            
            .loading { 
                text-align: center; 
                padding: 3rem; 
                color: #6b7280; 
            }
            
            .spinner { 
                border: 4px solid #f3f4f6; 
                border-top: 4px solid #667eea; 
                border-radius: 50%; 
                width: 40px; 
                height: 40px; 
                animation: spin 1s linear infinite; 
                margin: 0 auto 1rem; 
            }
            
            @keyframes spin { 
                0% { transform: rotate(0deg); } 
                100% { transform: rotate(360deg); } 
            }
            
            .debug-panel {
                background: #1f2937;
                color: #f9fafb;
                padding: 1rem;
                border-radius: 0.5rem;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.8rem;
                margin-top: 1rem;
                max-height: 200px;
                overflow-y: auto;
                display: none;
            }
            
            .debug-panel.visible {
                display: block;
            }
            
            .debug-toggle {
                background: #374151;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 0.3rem;
                font-size: 0.8rem;
                cursor: pointer;
                margin-left: 1rem;
            }
            
            @media (max-width: 768px) { 
                .header-content { 
                    flex-direction: column; 
                    gap: 1rem; 
                    text-align: center;
                }
                
                .content-actions { 
                    flex-direction: column; 
                }
                
                .metrics { 
                    grid-template-columns: 1fr 1fr; 
                }
                
                .progress-header {
                    flex-direction: column;
                    gap: 1rem;
                    align-items: stretch;
                }
                
                .progress-stats {
                    justify-content: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="header-title">🚀 Enhanced SEO Content Generator</div>
                <div style="display: flex; align-items: center;">
                    <div class="status status-connecting" id="connectionStatus">Connecting...</div>
                    <button class="debug-toggle" onclick="toggleDebug()">Debug</button>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="progress-section">
                <div class="progress-header">
                    <div class="progress-title">📊 Content Generation Progress</div>
                    <div class="progress-stats">
                        <span>Session: <span id="sessionId">--</span></span>
                        <span>•</span>
                        <span>Started: <span id="startTime">--</span></span>
                    </div>
                    <a href="/" class="back-btn">← Back to Form</a>
                </div>
                
                <div class="progress-bar-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">Initializing...</div>
                </div>
                
                <div class="current-step" id="currentStep" style="display: none;">
                    <h4 id="currentStepTitle">Loading...</h4>
                    <p id="currentStepMessage">Please wait while we set up your content generation...</p>
                    <div class="step-details" id="currentStepDetails"></div>
                </div>
                
                <div class="progress-list" id="progressList">
                    <div class="loading" id="loadingIndicator">
                        <div class="spinner"></div>
                        <p>Initializing content generation system...</p>
                        <p style="font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem;">
                            Connecting to AI services and preparing your content...
                        </p>
                    </div>
                </div>
                
                <div class="debug-panel" id="debugPanel">
                    <div id="debugLog">Debug information will appear here...</div>
                </div>
            </div>
            
            <div class="content-display" id="contentDisplay">
                <div class="metrics" id="metricsDisplay">
                    <div class="metric-card">
                        <div class="metric-value" id="wordCount">--</div>
                        <div class="metric-label">Words</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="readingTime">--</div>
                        <div class="metric-label">Reading Time</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="qualityScore">--</div>
                        <div class="metric-label">Quality Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="seoScore">--</div>
                        <div class="metric-label">SEO Score</div>
                    </div>
                </div>
                
                <div id="generatedContent"></div>
                
                <div class="content-actions">
                    <button class="action-btn" onclick="copyContent()">📋 Copy Content</button>
                    <button class="action-btn secondary" onclick="downloadContent()">💾 Download</button>
                    <button class="action-btn secondary" onclick="regenerateContent()">🔄 Regenerate</button>
                </div>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="chat-header">
                    🤖 AI Content Assistant - Improve Your Content
                </div>
                <div class="chat-content" id="chatContent">
                    <div class="message assistant">
                        <strong>AI Assistant:</strong> Content generated successfully! I can help you improve it further. Try asking:
                        <br><br>
                        • "Make this more trustworthy and authoritative"<br>
                        • "Add more practical examples and case studies"<br>
                        • "Make this more beginner-friendly"<br>
                        • "Optimize for search engines"<br>
                        • "Address customer pain points better"<br>
                        • "Improve engagement and readability"<br>
                        • "Add more compelling call-to-actions"
                    </div>
                </div>
                <div class="chat-input-container">
                    <input type="text" id="chatInput" placeholder="How would you like to improve the content?" />
                    <button id="sendChatBtn" onclick="sendChatMessage()">Send</button>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            let generatedContent = '';
            let formData = null;
            let generationComplete = false;
            let currentAssistantMessage = null;
            let debugMode = false;
            let connectionAttempts = 0;
            let maxConnectionAttempts = 3;
            
            // Debug logging
            function debugLog(message) {
                const timestamp = new Date().toISOString();
                const logElement = document.getElementById('debugLog');
                logElement.innerHTML += `[${timestamp}] ${message}\n`;
                logElement.scrollTop = logElement.scrollHeight;
                console.log(`[DEBUG] ${message}`);
            }
            
            function toggleDebug() {
                debugMode = !debugMode;
                const debugPanel = document.getElementById('debugPanel');
                debugPanel.classList.toggle('visible', debugMode);
            }
            
            // Initialize on page load
            window.addEventListener('load', function() {
                debugLog('Page loaded, starting initialization');
                
                // Display session info
                document.getElementById('sessionId').textContent = sessionId.split('_')[1];
                document.getElementById('startTime').textContent = new Date().toLocaleTimeString();
                
                // Get form data from localStorage
                const storedData = localStorage.getItem('contentFormData');
                if (storedData) {
                    formData = JSON.parse(storedData);
                    debugLog(`Form data loaded: ${JSON.stringify(formData, null, 2)}`);
                    initWebSocket();
                } else {
                    debugLog('No form data found, redirecting to form');
                    alert('No form data found. Please fill out the form first.');
                    window.location.href = '/';
                }
            });
            
            function initWebSocket() {
                connectionAttempts++;
                debugLog(`WebSocket connection attempt ${connectionAttempts}`);
                
                try {
                    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsHost = window.location.host;
                    const wsUrl = `${wsProtocol}//${wsHost}/ws/${sessionId}`;
                    
                    debugLog(`Connecting to WebSocket: ${wsUrl}`);
                    
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function(event) {
                        debugLog('WebSocket connection opened successfully');
                        document.getElementById('connectionStatus').textContent = 'Connected';
                        document.getElementById('connectionStatus').className = 'status status-connected';
                        
                        // Start content generation after brief delay
                        setTimeout(() => {
                            startContentGeneration();
                        }, 1000);
                    };
                    
                    ws.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            debugLog(`Received message: ${data.type}`);
                            handleWebSocketMessage(data);
                        } catch (error) {
                            debugLog(`Error parsing WebSocket message: ${error.message}`);
                            console.error('Error parsing WebSocket message:', error);
                        }
                    };
                    
                    ws.onclose = function(event) {
                        debugLog(`WebSocket closed: ${event.code} - ${event.reason}`);
                        console.log('WebSocket closed:', event.code, event.reason);
                        document.getElementById('connectionStatus').textContent = 'Disconnected';
                        document.getElementById('connectionStatus').className = 'status status-error';
                        
                        // Retry connection if not completed and under max attempts
                        if (!generationComplete && connectionAttempts < maxConnectionAttempts) {
                            debugLog('Attempting to reconnect...');
                            setTimeout(() => {
                                initWebSocket();
                            }, 2000);
                        }
                    };
                    
                    ws.onerror = function(error) {
                        debugLog(`WebSocket error: ${error.message || 'Unknown error'}`);
                        console.error('WebSocket error:', error);
                        document.getElementById('connectionStatus').textContent = 'Connection Error';
                        document.getElementById('connectionStatus').className = 'status status-error';
                        
                        addProgressItem('❌ Connection error. Retrying...', 'error');
                    };
                    
                    // Connection timeout
                    setTimeout(() => {
                        if (ws.readyState === WebSocket.CONNECTING) {
                            debugLog('WebSocket connection timeout');
                            ws.close();
                            if (connectionAttempts < maxConnectionAttempts) {
                                initWebSocket();
                            } else {
                                addProgressItem('❌ Connection failed after multiple attempts. Please refresh the page.', 'error');
                            }
                        }
                    }, 10000); // 10 second timeout
                    
                } catch (error) {
                    debugLog(`Failed to initialize WebSocket: ${error.message}`);
                    console.error('Failed to initialize WebSocket:', error);
                    document.getElementById('connectionStatus').textContent = 'Setup Error';
                    document.getElementById('connectionStatus').className = 'status status-error';
                    
                    addProgressItem('❌ WebSocket setup failed. Please refresh the page.', 'error');
                }
            }
            
            function startContentGeneration() {
                if (ws && ws.readyState === WebSocket.OPEN && formData) {
                    debugLog('Starting content generation');
                    document.getElementById('connectionStatus').textContent = 'Generating';
                    document.getElementById('connectionStatus').className = 'status status-generating';
                    
                    ws.send(JSON.stringify({
                        type: 'start_generation',
                        data: formData
                    }));
                } else {
                    debugLog(`Cannot start generation - WebSocket state: ${ws ? ws.readyState : 'null'}, FormData: ${!!formData}`);
                    console.error('Cannot start content generation - WebSocket not ready or form data missing');
                    addProgressItem('❌ Cannot start generation. Please refresh the page.', 'error');
                }
            }
            
            function handleWebSocketMessage(data) {
                debugLog(`Handling message type: ${data.type}`);
                
                switch(data.type) {
                    case 'connection_confirmed':
                        debugLog('Connection confirmed by server');
                        break;
                        
                    case 'progress_update':
                        document.getElementById('loadingIndicator').style.display = 'none';
                        updateProgress(data);
                        addProgressItem(data.message, data.step === data.total ? 'completed' : 'current');
                        break;
                        
                    case 'generation_complete':
                        debugLog('Generation completed');
                        generationComplete = true;
                        updateProgress({step: 6, total: 6, title: 'Complete', message: '✅ Generation finished!'});
                        displayContent(data);
                        showChatInterface();
                        document.getElementById('connectionStatus').textContent = 'Complete';
                        document.getElementById('connectionStatus').className = 'status status-connected';
                        break;
                        
                    case 'chat_typing_start':
                        startAssistantMessage();
                        break;
                        
                    case 'chat_stream':
                        appendToChatStream(data.chunk);
                        break;
                        
                    case 'chat_complete':
                        completeAssistantMessage();
                        break;
                        
                    case 'generation_error':
                        debugLog(`Generation error: ${data.error}`);
                        addProgressItem(`❌ Error: ${data.error}`, 'error');
                        document.getElementById('connectionStatus').textContent = 'Error';
                        document.getElementById('connectionStatus').className = 'status status-error';
                        break;
                        
                    case 'chat_error':
                        debugLog(`Chat error: ${data.message}`);
                        addProgressItem(`❌ Chat Error: ${data.message}`, 'error');
                        break;
                        
                    default:
                        debugLog(`Unknown message type: ${data.type}`);
                        break;
                }
            }
            
            function updateProgress(data) {
                const percentage = (data.step / data.total) * 100;
                document.getElementById('progressFill').style.width = percentage + '%';
                document.getElementById('progressText').textContent = `Step ${data.step} of ${data.total}: ${data.title}`;
                
                // Update current step display
                const currentStep = document.getElementById('currentStep');
                currentStep.style.display = 'block';
                document.getElementById('currentStepTitle').textContent = data.title;
                document.getElementById('currentStepMessage').textContent = data.message;
                document.getElementById('currentStepDetails').textContent = data.details || '';
            }
            
            function addProgressItem(message, type = 'progress') {
                const progressList = document.getElementById('progressList');
                const item = document.createElement('div');
                item.className = `progress-item ${type}`;
                item.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong> ${message}`;
                progressList.appendChild(item);
                progressList.scrollTop = progressList.scrollHeight;
            }
            
            function displayContent(data) {
                generatedContent = data.content;
                
                // Update metrics
                const metrics = data.metrics || {};
                document.getElementById('wordCount').textContent = metrics.word_count?.toLocaleString() || '--';
                document.getElementById('readingTime').textContent = metrics.reading_time ? metrics.reading_time + ' min' : '--';
                document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '8.5';
                document.getElementById('seoScore').textContent = metrics.seo_score?.toFixed(1) || '8.0';
                
                // Format and display content
                const formattedContent = formatContent(data.content);
                document.getElementById('generatedContent').innerHTML = formattedContent;
                
                // Show content display
                document.getElementById('contentDisplay').classList.add('visible');
                document.getElementById('contentDisplay').scrollIntoView({ behavior: 'smooth' });
                
                debugLog(`Content displayed - ${metrics.word_count || 0} words`);
            }
            
            function showChatInterface() {
                document.getElementById('chatContainer').classList.add('visible');
                setTimeout(() => {
                    document.getElementById('chatContainer').scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                    });
                }, 500);
            }
            
            function formatContent(content) {
                return content
                    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                    .replace(/^- (.+)$/gm, '<li>$1</li>')
                    .replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>')
                    .replace(/((<li>.*?<\\/li>\\s*)+)/gs, '<ul>$1</ul>')
                    .replace(/\\n\\n/g, '</p><p>')
                    .replace(/^([^<].+)$/gm, '<p>$1</p>')
                    .replace(/<p><h/g, '<h')
                    .replace(/<\\/h([1-6])><\\/p>/g, '</h$1>')
                    .replace(/<p><ul>/g, '<ul>')
                    .replace(/<\\/ul><\\/p>/g, '</ul>');
            }
            
            function sendChatMessage() {
                const chatInput = document.getElementById('chatInput');
                const sendBtn = document.getElementById('sendChatBtn');
                const message = chatInput.value.trim();
                
                if (!message || !generationComplete || !ws || ws.readyState !== WebSocket.OPEN) {
                    return;
                }
                
                debugLog(`Sending chat message: ${message}`);
                
                chatInput.disabled = true;
                sendBtn.disabled = true;
                sendBtn.textContent = 'Sending...';
                
                const chatContent = document.getElementById('chatContent');
                const userMessage = document.createElement('div');
                userMessage.className = 'message user';
                userMessage.innerHTML = `<strong>You:</strong> ${message}`;
                chatContent.appendChild(userMessage);
                
                try {
                    ws.send(JSON.stringify({
                        type: 'chat_message',
                        message: message
                    }));
                } catch (error) {
                    debugLog(`Failed to send chat message: ${error.message}`);
                    console.error('Failed to send chat message:', error);
                }
                
                chatInput.value = '';
                chatContent.scrollTop = chatContent.scrollHeight;
                
                setTimeout(() => {
                    chatInput.disabled = false;
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    chatInput.focus();
                }, 1000);
            }
            
            function startAssistantMessage() {
                const chatContent = document.getElementById('chatContent');
                currentAssistantMessage = document.createElement('div');
                currentAssistantMessage.className = 'message assistant';
                currentAssistantMessage.innerHTML = '<strong>AI Assistant:</strong> <span class="streaming-text"></span>';
                chatContent.appendChild(currentAssistantMessage);
                chatContent.scrollTop = chatContent.scrollHeight;
            }
            
            function appendToChatStream(chunk) {
                if (currentAssistantMessage) {
                    const streamingText = currentAssistantMessage.querySelector('.streaming-text');
                    streamingText.textContent += chunk;
                    document.getElementById('chatContent').scrollTop = document.getElementById('chatContent').scrollHeight;
                }
            }
            
            function completeAssistantMessage() {
                currentAssistantMessage = null;
            }
            
            function copyContent() {
                const content = document.getElementById('generatedContent').innerText;
                navigator.clipboard.writeText(content).then(() => {
                    const btn = event.target;
                    const originalText = btn.textContent;
                    btn.textContent = '✅ Copied!';
                    setTimeout(() => {
                        btn.textContent = originalText;
                    }, 2000);
                    debugLog('Content copied to clipboard');
                }).catch(err => {
                    console.error('Failed to copy content:', err);
                    debugLog(`Failed to copy content: ${err.message}`);
                });
            }
            
            function downloadContent() {
                const content = document.getElementById('generatedContent').innerText;
                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `content_${new Date().toISOString().split('T')[0]}.txt`;
                a.click();
                URL.revokeObjectURL(url);
                debugLog('Content downloaded');
            }
            
            function regenerateContent() {
                debugLog('Regenerating content');
                window.location.reload();
            }
            
            // Chat input enter key support
            document.addEventListener('DOMContentLoaded', function() {
                const chatInput = document.getElementById('chatInput');
                if (chatInput) {
                    chatInput.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            sendChatMessage();
                        }
                    });
                }
            });
            
            // Handle page unload
            window.addEventListener('beforeunload', function() {
                if (ws) {
                    ws.close();
                }
            });
        </script>
    </body>
    </html>
