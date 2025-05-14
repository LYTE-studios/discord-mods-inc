from typing import Dict
import openai
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings
from .personality_types import PersonalityType

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_response(
        self,
        message: str,
        chat_type: str
    ) -> str:
        """Synchronous method to generate a response"""
        try:
            # Get personality type
            personality_type = PersonalityType.CTO if chat_type == 'cto' else PersonalityType.DEVELOPER
            
            # Create system message based on role
            system_message = (
                "You are an AI Chief Technical Officer with extensive experience in technical leadership and software architecture. "
                "Your responses should reflect your role as a CTO, focusing on technical strategy, architecture decisions, and best practices. "
                "Be direct, professional, and provide guidance from a leadership perspective."
                if chat_type == 'cto' else
                "You are an AI Developer with deep technical expertise. "
                "Your responses should reflect your role as a developer, focusing on implementation details, coding practices, and technical solutions. "
                "Be direct, technical, and provide specific coding and implementation guidance."
            )
            
            # Create messages array
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ]
            
            try:
                # Get response from OpenAI
                logger.info(f"Sending request to OpenAI for {chat_type} chat")
                response = openai.ChatCompletion.create(
                    model="gpt-4",  # Explicitly set model
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,  # Increased max tokens
                    n=1,
                    presence_penalty=0.6,
                    frequency_penalty=0.0,
                )
                
                ai_message = response.choices[0].message.content
                logger.info("Successfully received response from OpenAI")
                return ai_message

            except openai.error.AuthenticationError as e:
                logger.error(f"OpenAI Authentication Error: {str(e)}")
                return "Authentication error with AI service. Please check API key configuration."
                
            except openai.error.APIError as e:
                logger.error(f"OpenAI API Error: {str(e)}")
                return "AI service is temporarily unavailable. Please try again later."
                
            except Exception as e:
                logger.error(f"Error in OpenAI request: {str(e)}")
                return "I apologize, but I'm having trouble processing your request right now."

        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return "An unexpected error occurred. Please try again."

# Global instance
conversation_manager = ConversationManager()