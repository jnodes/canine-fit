"""
Native OpenAI integration for Canine.Fit.
Replaces emergentintegrations.llm.chat
"""

from openai import AsyncOpenAI
from typing import Optional, List
import logging
import json

logger = logging.getLogger(__name__)


class UserMessage:
    """A user message for the LLM."""
    
    def __init__(self, text: str):
        self.text = text


class LlmResponse:
    """Response from the LLM."""
    
    def __init__(self, text: str):
        self.text = text


class LlmChat:
    """
    Native OpenAI chat integration.
    
    Provides a simple interface for LLM interactions,
    compatible with the emergentintegrations interface.
    """
    
    def __init__(
        self,
        api_key: str,
        session_id: str = "",
        system_message: str = "",
        model: str = "gpt-4o"
    ):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)
        self.messages: List[dict] = []
        
        # Add system message if provided
        if system_message:
            self.messages.append({
                "role": "system",
                "content": system_message
            })
    
    def with_model(self, provider: str, model: str) -> "LlmChat":
        """
        Set the model to use.
        
        Args:
            provider: The provider name (e.g., "openai")
            model: The model name (e.g., "gpt-4o")
            
        Returns:
            self for chaining
        """
        # Normalize model name
        if model.startswith("gpt-"):
            self.model = model
        else:
            self.model = f"gpt-4o"  # Default to GPT-4o
        return self
    
    async def send_message(self, message: UserMessage) -> LlmResponse:
        """
        Send a message to the LLM and get a response.
        
        Args:
            message: The UserMessage to send
            
        Returns:
            LlmResponse with the LLM's reply
        """
        try:
            # Add user message
            self.messages.append({
                "role": "user",
                "content": message.text
            })
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract response
            reply = response.choices[0].message.content
            
            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": reply
            })
            
            return LlmResponse(text=reply)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def send_json_message(
        self,
        message: UserMessage,
        json_schema: Optional[dict] = None
    ) -> dict:
        """
        Send a message and parse the response as JSON.
        
        Args:
            message: The UserMessage to send
            json_schema: Optional JSON schema for structured output
            
        Returns:
            Parsed JSON response
        """
        try:
            response = await self.send_message(message)
            
            # Try to parse as JSON
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"LLM response was not valid JSON: {response.text}")
