import os
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"

        # Cache for boy prompts
        self.boy_prompts: Dict[int, str] = {}

        # Cache for conversation history
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def _get_conversation_key(self, user_id: int, boy_id: int, game_id: int) -> str:
        """Generate a unique key for a conversation."""
        return f"{user_id}_{boy_id}_{game_id}"

    def _get_or_create_conversation(self, user_id: int, boy_id: int, game_id: int) -> List[Dict[str, str]]:
        """Get or create a conversation history."""
        key = self._get_conversation_key(user_id, boy_id, game_id)
        if key not in self.conversations:
            self.conversations[key] = []
        return self.conversations[key]

    def set_boy_prompt(self, boy_id: int, prompt: str):
        """Set the prompt for a boy."""
        self.boy_prompts[boy_id] = prompt
        logger.info(f"Set prompt for boy {boy_id}")

    def get_boy_prompt(self, boy_id: int) -> Optional[str]:
        """Get the prompt for a boy."""
        return self.boy_prompts.get(boy_id)

    async def generate_response(self, user_id: int, boy_id: int, game_id: int, message: str, 
                               secret_admirer_id: Optional[int] = None) -> str:
        """Generate a response from a boy to a user message."""
        # Log the incoming message
        logger.info(f"Generating response for user {user_id}, boy {boy_id}, game {game_id}")
        logger.info(f"User message: '{message}'")

        # Get the boy's prompt
        boy_prompt = self.get_boy_prompt(boy_id)
        if not boy_prompt:
            logger.error(f"No prompt found for boy {boy_id}")
            return "Sorry, I'm having trouble understanding you right now."

        # Get the conversation history
        conversation = self._get_or_create_conversation(user_id, boy_id, game_id)

        # Prepare the messages for the API
        messages = [
            {"role": "system", "content": boy_prompt}
        ]

        # Add information about the secret admirer if provided
        if secret_admirer_id is not None:
            is_secret_admirer = boy_id == secret_admirer_id
            secret_info = f"You {'are' if is_secret_admirer else 'are not'} the secret admirer in this game. "
            if not is_secret_admirer:
                secret_info += f"Boy #{secret_admirer_id} is the secret admirer. "
            secret_info += "Give subtle hints about who the secret admirer is or isn't without directly revealing it."
            messages.append({"role": "system", "content": secret_info})

        # Add conversation history
        for msg in conversation:
            messages.append(msg)

        # Add the user's message
        messages.append({"role": "user", "content": message})

        try:
            # Log the messages being sent to OpenAI
            logger.info(f"Sending request to OpenAI with {len(messages)} messages")
            for i, msg in enumerate(messages):
                logger.info(f"Message {i+1}: role={msg['role']}, content={msg['content'][:50]}...")

            # Call the OpenAI API
            logger.info(f"Calling OpenAI API with model {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )

            # Extract the response text
            response_text = response.choices[0].message.content
            logger.info(f"Received response from OpenAI: '{response_text[:100]}...'")
            logger.info(f"Response usage: {response.usage.total_tokens} tokens")

            # Update the conversation history
            conversation.append({"role": "user", "content": message})
            conversation.append({"role": "assistant", "content": response_text})

            # Limit conversation history to last 20 messages to avoid token limits
            if len(conversation) > 20:
                conversation = conversation[-20:]

            # Save the conversation back to the dictionary
            conversation_key = self._get_conversation_key(user_id, boy_id, game_id)
            self.conversations[conversation_key] = conversation
            logger.info(f"Updated conversation history for key {conversation_key}, now has {len(conversation)} messages")

            logger.info(f"Generated response for boy {boy_id} to user {user_id}")
            logger.info(f"Returning response: '{response_text}'")
            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Sorry, I'm having trouble responding right now."

# Create a singleton instance
gpt_service = GPTService()
