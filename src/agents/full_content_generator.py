import json
from src.utils.llm_client import LLMClient

class FullContentGenerator:
    def __init__(self):
        self.llm = LLMClient()
        self.content_templates = {
            "blog_post": self.generate_blog_post,
            "landing_page": self.generate_landing_page,
            "product_page": self.generate_product_page,
            "guide": self.generate_guide,
            "comparison": self.generate_comparison,
            "listicle": self.generate_listicle
        }
    
    def generate_complete_content(self, topic, content_type, reddit_insights, 
                                journey_data, business_context, human_inputs, eeat_assessment=None):
        """Generate complete content using Figment Agency's hybrid approach"""
        
        if content_type in self.content_templates:
            return self.content_templates[content_type](
                topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment
            )
        else:
            return self.generate_generic_content(
                topic, content_type, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment
            )
    
    def generate_blog_post(self, topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate complete blog post using Figment's human-AI hybrid methodology"""
        
        prompt = f"""
        Create a high-performance blog post using Figment Agency's methodology.
        Their research shows human-enhanced content gets 5.44x more traffic than AI-only content.
        
        RESEARCH FOUNDATION:
        Topic: {topic}
        Reddit Customer Voice: {json.dumps(reddit_insights, indent=2)}
        Customer Journey: {json.dumps(journey_data, indent=2)}
        Business Context: {json.dumps(business_context, indent=2)}
        Human Expertise: {json.dumps(human_inputs, indent=2)}
        E-E-A-T Assessment: {json.dumps(eeat_assessment, indent=2) if eeat_assessment else 'Not assessed'}
        
        FIGMENT'S HIGH-PERFORMANCE CONTENT PRINCIPLES:
        
        1. AUTHENTICITY (Critical for Performance):
           - Use real human experiences from business context
           - Include specific examples from human inputs
           - Avoid generic AI phrasing like "In today's fast-paced world"
           - Use customer's actual language from Reddit research
        
        2. EMOTIONAL INTELLIGENCE:
           - Match tone to customer emotional state from journey analysis
           - Show empathy for customer pain points
           - Use reassuring language for anxious customers
           - Inject personality that reflects business brand voice
        
        3. EXPERIENCE-DRIVEN CONTENT (E-E-A-T):
           - Lead with first-hand experience from human inputs
           - Include real case studies and examples
           - Reference actual customer conversations
           - Demonstrate lived understanding of the topic
        
        Create a comprehensive blog post (1,500-2,500 words) that:
        1. Uses compelling headline addressing customer pain points
        2. Opens with authentic customer language from Reddit
        3. Incorporates business expertise and human insights
        4. Addresses the customer journey stage appropriately
        5. Includes actionable advice and real examples
        6. Ends with clear call-to-action aligned with business goals
        
        Target Audience: {business_context.get('target_audience', 'general audience')}
        Brand Voice: {business_context.get('brand_voice', 'professional yet approachable')}
        Business Goal: {business_context.get('content_goal', 'education and trust building')}
        
        Create the complete blog post now, ensuring it demonstrates why human-enhanced content 
        outperforms AI-only content by incorporating real experience, emotion, and expertise.
        """
        
        return self.llm.generate(prompt, max_tokens=3000)
    
    def generate_landing_page(self, topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate conversion-focused landing page"""
        
        prompt = f"""
        Create a high-converting landing page for: {topic}
        
        Research Data:
        - Reddit Insights: {json.dumps(reddit_insights, indent=2)}
        - Customer Journey: {json.dumps(journey_data, indent=2)}
        - Business Context: {json.dumps(business_context, indent=2)}
        - Human Inputs: {json.dumps(human_inputs, indent=2)}
        
        Create a landing page with these sections:
        
        1. HEADLINE: Powerful, benefit-focused headline addressing main pain point
        2. SUBHEADLINE: Supporting text that clarifies the offer
        3. HERO SECTION: Value proposition using customer language
        4. PROBLEM SECTION: Agitate pain points from Reddit research
        5. SOLUTION SECTION: Present your solution with unique differentiators
        6. BENEFITS SECTION: Key benefits that matter to your audience
        7. SOCIAL PROOF: Trust signals and credibility elements
        8. CTA SECTION: Clear call-to-action aligned with business goals
        9. FAQ SECTION: Address common objections from customer research
        
        Target Action: {business_context.get('target_action', 'conversion')}
        Audience: {business_context.get('target_audience')}
        
        Provide complete landing page copy, optimized for conversions.
        """
        
        return self.llm.generate(prompt, max_tokens=2500)
    
    def generate_product_page(self, topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate detailed product page"""
        
        prompt = f"""
        Create compelling product page content for: {topic}
        
        Research Insights:
        - Customer Pain Points: {reddit_insights.get('customer_voice', {}).get('pain_points', [])}
        - Customer Language: {reddit_insights.get('customer_voice', {}).get('common_language', [])}
        - Business Strengths: {business_context.get('key_strengths', 'Not provided')}
        - Target Audience: {business_context.get('target_audience', 'General')}
        
        Create a product page with:
        
        1. PRODUCT TITLE: SEO-optimized, benefit-focused title
        2. PRODUCT DESCRIPTION: Compelling overview addressing main benefits
        3. KEY FEATURES: Bullet points highlighting important features
        4. BENEFITS SECTION: How features translate to customer value
        5. SPECIFICATIONS: Technical details (placeholder for human input)
        6. USE CASES: Specific scenarios where product excels
        7. COMPARISON: How it differs from alternatives
        8. TESTIMONIALS: Placeholder for customer reviews
        9. FAQ: Common questions from Reddit research
        10. PURCHASE CTA: Clear buying instruction
        
        Write for {business_context.get('business_type', 'B2C')} audience.
        """
        
        return self.llm.generate(prompt, max_tokens=2000)
    
    def generate_guide(self, topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate comprehensive guide"""
        
        prompt = f"""
        Create a comprehensive, actionable guide for: {topic}
        
        Based on Research:
        - Customer Questions: {reddit_insights.get('customer_voice', {}).get('frequent_questions', [])}
        - Pain Points: {reddit_insights.get('customer_voice', {}).get('pain_points', [])}
        - Business Expertise: {business_context.get('unique_value_prop', 'Industry knowledge')}
        
        Structure the guide as:
        
        1. INTRODUCTION
           - Why this guide matters
           - What readers will achieve
           - Brief overview of process
        
        2. GETTING STARTED
           - Prerequisites
           - What you'll need
           - Initial setup
        
        3. STEP-BY-STEP PROCESS
           - Clear, numbered steps
           - Actionable instructions
           - Common pitfalls to avoid
           - Pro tips from business expertise
        
        4. TROUBLESHOOTING
           - Common issues (from Reddit research)
           - Solutions and workarounds
        
        5. ADVANCED TIPS
           - Next-level strategies
           - Business-specific insights
        
        6. CONCLUSION
           - Key takeaways
           - Next steps
           - How to get help
        
        Audience Level: {journey_data.get('primary_stage', 'beginner')}
        """
        
        return self.llm.generate(prompt, max_tokens=2500)
    
    def generate_comparison(self, topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate comparison content"""
        
        prompt = f"""
        Create a detailed comparison for: {topic}
        
        Customer Research:
        - What customers compare: {reddit_insights.get('customer_voice', {}).get('frequent_questions', [])}
        - Decision factors: {journey_data.get('key_pain_points', [])}
        - Business positioning: {business_context.get('competitive_advantages', [])}
        
        Create comparison with:
        
        1. INTRODUCTION
           - What we're comparing and why
           - Who this comparison helps
        
        2. COMPARISON CRITERIA
           - Key factors that matter to customers
           - How we'll evaluate each option
        
        3. DETAILED COMPARISON
           - Side-by-side analysis
           - Pros and cons for each
           - Use cases for different scenarios
        
        4. WINNER BY CATEGORY
           - Best for budget
           - Best for features
           - Best for specific use cases
        
        5. FINAL RECOMMENDATION
           - Overall winner and why
           - Alternative recommendations
           - How to decide what's right for you
        
        Business Angle: {business_context.get('content_angle', 'neutral expert advice')}
        """
        
        return self.llm.generate(prompt, max_tokens=2000)
    
    def generate_listicle(self, topic, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate listicle content"""
        
        prompt = f"""
        Create an engaging listicle for: {topic}
        
        Based on:
        - Customer interests from Reddit: {reddit_insights.get('customer_voice', {}).get('common_language', [])}
        - Business expertise: {business_context.get('key_strengths', [])}
        
        Create a list-style article with:
        1. Compelling numbered headline
        2. Brief introduction explaining the value
        3. 5-10 main points, each with:
           - Clear subheading
           - Detailed explanation
           - Real examples where possible
           - Actionable takeaways
        4. Summary conclusion
        5. Call-to-action
        
        Make it scannable, engaging, and packed with value.
        """
        
        return self.llm.generate(prompt, max_tokens=2000)
    
    def generate_generic_content(self, topic, content_type, reddit_insights, journey_data, business_context, human_inputs, eeat_assessment):
        """Generate content for any content type"""
        
        prompt = f"""
        Create high-quality {content_type} content for: {topic}
        
        Use this research to inform the content:
        - Customer insights: {json.dumps(reddit_insights, indent=2)}
        - Customer journey: {json.dumps(journey_data, indent=2)}
        - Business context: {json.dumps(business_context, indent=2)}
        - Human inputs: {json.dumps(human_inputs, indent=2)}
        
        Create {content_type} that:
        1. Addresses customer pain points from Reddit research
        2. Uses authentic customer language
        3. Incorporates business positioning and strengths
        4. Matches the customer journey stage
        5. Includes compelling call-to-action
        6. Optimized for the target audience
        
        Make it comprehensive, actionable, and valuable for the intended audience.
        """
        
        return self.llm.generate(prompt, max_tokens=2000)