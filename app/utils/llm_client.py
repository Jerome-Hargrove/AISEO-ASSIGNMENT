"""LLM client wrapper for OpenAI GPT-4."""
import json
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Async OpenAI client wrapper for content generation."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate a completion using the LLM.
        
        Args:
            system_prompt: System instruction for the model
            user_prompt: User message/prompt
            temperature: Creativity parameter (0-2)
            max_tokens: Maximum response tokens
            response_format: Optional format specification (e.g., {"type": "json_object"})
        
        Returns:
            Generated text response
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise
    
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Generate a JSON response from the LLM.
        
        Args:
            system_prompt: System instruction (should request JSON output)
            user_prompt: User message/prompt
            temperature: Creativity parameter
            max_tokens: Maximum response tokens
        
        Returns:
            Parsed JSON as dictionary
        """
        # Enhance system prompt to request JSON
        json_system_prompt = system_prompt + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no explanation, just the JSON object."
        
        response = await self.generate_completion(
            system_prompt=json_system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens
            # Don't use response_format for broader model compatibility
        )
        
        try:
            # Try to parse the response directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"Failed to parse JSON response: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM")
    
    async def analyze_text(
        self,
        text: str,
        analysis_prompt: str,
        output_schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze text and return structured output.
        
        Args:
            text: Text to analyze
            analysis_prompt: What to analyze/extract
            output_schema: Optional JSON schema description
        
        Returns:
            Analysis results as dictionary
        """
        system_prompt = """You are an expert content analyst. Analyze the provided text and return structured JSON output.
Always respond with valid JSON only, no additional text."""
        
        if output_schema:
            system_prompt += f"\n\nExpected output format:\n{output_schema}"
        
        user_prompt = f"{analysis_prompt}\n\nText to analyze:\n{text}"
        
        return await self.generate_json(system_prompt, user_prompt)


# Singleton instance
llm_client = LLMClient()
