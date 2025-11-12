"""
Kernel Studio - LLM Module
Handles OpenAI GPT-4 chat completions
"""

import os
from openai import OpenAI
from typing import List, Dict, Optional


class LLM:
    """LLM interface using OpenAI."""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize LLM.
        
        Args:
            model: Model name (gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.)
            api_key: OpenAI API key (defaults to env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            print("[LLM] ⚠️ No OPENAI_API_KEY found")
        
        self.client = OpenAI(api_key=self.api_key)
        print(f"[LLM] Initialized with model: {model}")
    
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_p: float = 1.0
    ) -> str:
        """
        Generate a response.
        
        Args:
            system_prompt: System prompt defining persona/behavior
            user_message: User's message
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum response length
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[LLM] ❌ Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_context(
        self,
        system_prompt: str,
        context: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate with injected context.
        
        Args:
            system_prompt: System prompt
            context: Retrieved context to inject
            user_message: User's message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated response
        """
        # Augment system prompt with context
        augmented_system = f"{system_prompt}\n\n### Context:\n{context}"
        
        return self.generate(
            augmented_system,
            user_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def generate_with_conversation(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate with full conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[LLM] ❌ Error: {e}")
            return f"Error: {str(e)}"
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def stream_generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Stream generation token by token.
        
        Args:
            system_prompt: System prompt
            user_message: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Yields:
            Tokens as they're generated
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"[LLM] ❌ Streaming error: {e}")
            yield f"Error: {str(e)}"


# Global instance
_llm_instance = None


def get_llm(model: str = "gpt-4") -> LLM:
    """Get or create global LLM instance."""
    global _llm_instance
    
    if _llm_instance is None or _llm_instance.model != model:
        _llm_instance = LLM(model=model)
    
    return _llm_instance
