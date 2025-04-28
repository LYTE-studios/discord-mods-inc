"""
AI service module for handling AI-related functionality
"""
from typing import Optional, Dict
import openai
from django.conf import settings

class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        openai.api_key = self.api_key

    async def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Generate AI response using OpenAI API
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            # Log error and return fallback response
            print(f"Error generating AI response: {e}")
            return "I apologize, but I'm unable to process your request at the moment."

ai_service = AIService()