from typing import Dict, List, Optional, Tuple
from venv import logger
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings
from web.chat.models import Conversation
from .personality_types import PersonalityType, get_collaboration_prompt, get_review_prompt, get_task_prompt

class ConversationManager:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_ai_response(
        self,
        conversation_id: str,
        user_message: str,
        personality_type: PersonalityType,
        context: Optional[Dict] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Get AI response for user message"""
        try:
            # Get or create conversation
            conversation = self.get_or_create_conversation(conversation_id, personality_type)
            
            # Update context if provided
            if context:
                conversation.update_context(**context)
            
            # Add user message to conversation
            conversation.add_message("user", user_message)
            
            # Get AI response
            response = await openai.ChatCompletion.acreate(
                model=settings.OPENAI_MODEL,
                messages=conversation.get_messages(),
                temperature=temperature,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                n=1,
                presence_penalty=0.6,
                frequency_penalty=0.0,
            )
            
            # Extract and store response
            ai_message = response.choices[0].message.content
            conversation.add_message("assistant", ai_message)
            
            # Log token usage
            logger.info(
                f"Token usage - Prompt: {response.usage.prompt_tokens}, "
                f"Completion: {response.usage.completion_tokens}, "
                f"Total: {response.usage.total_tokens}"
            )
            
            return ai_message

        except openai.error.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            return "I'm currently experiencing high demand. Please try again in a moment."
            
        except openai.error.InvalidRequestError as e:
            logger.error(f"Invalid request to OpenAI API: {str(e)}")
            return "I encountered an error processing your request. Please try a shorter message."
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now."

    async def get_task_response(
        self,
        conversation_id: str,
        personality_type: PersonalityType,
        task_description: str,
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """Get AI response for a specific task"""
        prompt = get_task_prompt(personality_type, task_description)
        return await self.get_ai_response(
            conversation_id=conversation_id,
            user_message=prompt,
            personality_type=personality_type,
            context=context
        )

    async def get_review_response(
        self,
        conversation_id: str,
        personality_type: PersonalityType,
        content: str,
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """Get AI response for a review task"""
        prompt = get_review_prompt(personality_type, content)
        return await self.get_ai_response(
            conversation_id=conversation_id,
            user_message=prompt,
            personality_type=personality_type,
            context=context
        )

    async def get_collaboration_response(
        self,
        conversation_id: str,
        personality_type: PersonalityType,
        collaborator_role: str,
        topic: str,
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """Get AI response for collaboration"""
        prompt = get_collaboration_prompt(personality_type, collaborator_role, topic)
        return await self.get_ai_response(
            conversation_id=conversation_id,
            user_message=prompt,
            personality_type=personality_type,
            context=context
        )

    async def facilitate_team_discussion(
        self,
        topic: str,
        participants: List[Tuple[str, PersonalityType]],
        context: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """Facilitate a discussion between multiple AI team members"""
        try:
            responses = []
            
            for conv_id, personality_type in participants:
                response = await self.get_ai_response(
                    conversation_id=conv_id,
                    user_message=f"Please provide your perspective on: {topic}",
                    personality_type=personality_type,
                    context=context
                )
                
                if response:
                    responses.append({
                        "role": personality_type.value,
                        "response": response
                    })
            
            return responses

        except Exception as e:
            logger.error(f"Error facilitating team discussion: {str(e)}")
            return []

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation's history"""
        if conversation_id in self.conversations:
            personality_type = self.conversations[conversation_id].personality_type
            self.conversations[conversation_id] = Conversation(personality_type)

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
            
            # Get response from OpenAI
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                n=1,
                presence_penalty=0.6,
                frequency_penalty=0.0,
            )
            
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now."

# Global instance
conversation_manager = ConversationManager()