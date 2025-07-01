import anthropic
import os
from dotenv import load_dotenv

# Load environment variables directly
load_dotenv()

class LLMClient:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate(self, prompt, model="claude-3-5-sonnet-20241022", max_tokens=1500):
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0.7,
                system="You are an expert content strategist and customer research analyst.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_structured(self, prompt, model="claude-3-5-sonnet-20241022"):
        """Generate structured response with JSON format"""
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.5,
                system="You are an expert content strategist. Always respond in valid JSON format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"