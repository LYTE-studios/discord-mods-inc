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
                "You are an AI Chief Technical Officer, focused on technical leadership and strategic decisions. "
                "Provide guidance with a focus on architecture, best practices, and technical direction."
                if chat_type == 'cto' else
                "You are an AI Developer, focused on implementation details and coding practices. "
                "Provide specific technical advice and coding guidance."
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
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
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