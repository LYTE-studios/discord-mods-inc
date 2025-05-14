from typing import List, Dict, Optional, Tuple
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
from datetime import datetime, timezone
from config import settings
from utils.logger import logger
from database.supabase_client import db
from .personality_types import (
    PersonalityType, get_personality_config,
    get_system_prompt, get_task_prompt,
    get_review_prompt, get_collaboration_prompt
)

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.tokens = self._count_tokens(content)
        self.timestamp = datetime.now(timezone.utc)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
            return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}")
            return len(text) // 4  # Rough estimation

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

class ConversationContext:
    def __init__(self):
        self.current_task: Optional[str] = None
        self.related_tickets: List[str] = []
        self.github_context: Dict = {}
        self.collaboration_history: List[Dict] = []
        self.last_code_review: Optional[Dict] = None

class Conversation:
    def __init__(self, personality_type: PersonalityType):
        self.personality_type = personality_type
        self.messages: List[Message] = []
        self.total_tokens = 0
        self.max_tokens = 4000  # Conservative limit for context window
        self.context = ConversationContext()
        
        # Initialize with system message
        system_prompt = get_system_prompt(personality_type)
        self.add_message("system", system_prompt)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation"""
        message = Message(role, content)
        
        # Check if adding this message would exceed token limit
        while self.total_tokens + message.tokens > self.max_tokens:
            # Remove oldest non-system message
            for i, msg in enumerate(self.messages):
                if msg.role != "system":
                    self.total_tokens -= msg.tokens
                    self.messages.pop(i)
                    break
        
        self.messages.append(message)
        self.total_tokens += message.tokens

    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages in format required by OpenAI API"""
        return [msg.to_dict() for msg in self.messages]

    def update_context(self, **kwargs) -> None:
        """Update conversation context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        openai.api_key = settings.OPENAI_API_KEY

    def get_or_create_conversation(
        self, conversation_id: str, personality_type: PersonalityType
    ) -> Conversation:
        """Get existing conversation or create new one"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(personality_type)
        return self.conversations[conversation_id]

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
            personality_type = PersonalityType.CTO if chat_type == 'cto' else PersonalityType.DEVELOPER
            conversation = Conversation(personality_type)
            conversation.add_message("user", message)
            
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=conversation.get_messages(),
                temperature=0.7,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                n=1,
                presence_penalty=0.6,
                frequency_penalty=0.0,
            )
            
            ai_message = response.choices[0].message.content
            return ai_message

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now."

# Global instance
conversation_manager = ConversationManager()