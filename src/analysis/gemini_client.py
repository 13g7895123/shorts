"""Gemini AI API client for video analysis."""

import time
import json
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..utils.config import config
from ..utils.logger import get_analysis_logger
from ..utils.exceptions import GeminiAPIError, RateLimitError

logger = get_analysis_logger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini AI API."""
    
    def __init__(self):
        """Initialize Gemini API client."""
        api_key = config.gemini_api_key
        if not api_key:
            raise GeminiAPIError("GEMINI_API_KEY not found in environment variables")
        
        try:
            genai.configure(api_key=api_key)
            
            # Load configuration
            gemini_config = config.load_yaml("gemini")
            self.model_name = gemini_config.get('api', {}).get('model', 'gemini-2.0-flash-exp')
            self.api_params = gemini_config.get('api', {}).get('parameters', {})
            self.retry_config = gemini_config.get('api', {}).get('retry', {})
            self.prompts = gemini_config.get('prompts', {})
            
            # Initialize model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    'temperature': self.api_params.get('temperature', 0.7),
                    'top_p': self.api_params.get('top_p', 0.95),
                    'top_k': self.api_params.get('top_k', 40),
                    'max_output_tokens': self.api_params.get('max_output_tokens', 8192),
                }
            )
            
            logger.info(f"Gemini client initialized with model: {self.model_name}")
        
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise GeminiAPIError(f"Failed to initialize Gemini API: {e}")
    
    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            GeminiAPIError: If all retries fail
        """
        max_attempts = self.retry_config.get('max_attempts', 3)
        backoff_base = self.retry_config.get('backoff_base', 2)
        timeout = self.retry_config.get('timeout', 60)
        
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if rate limited
                if 'quota' in error_msg or 'rate limit' in error_msg:
                    if attempt < max_attempts - 1:
                        wait_time = backoff_base ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_attempts}")
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError("Gemini API rate limit exceeded")
                
                # Check if retriable error
                if attempt < max_attempts - 1 and ('timeout' in error_msg or 'server' in error_msg):
                    wait_time = backoff_base ** attempt
                    logger.warning(f"Retriable error, waiting {wait_time}s before retry {attempt + 1}/{max_attempts}")
                    time.sleep(wait_time)
                    continue
                
                # Non-retriable error
                logger.error(f"Gemini API error: {e}")
                raise GeminiAPIError(f"Gemini API request failed: {e}")
        
        raise GeminiAPIError("Max retry attempts exceeded")
    
    def generate_text(self, prompt: str) -> str:
        """Generate text response from Gemini.
        
        Args:
            prompt: Text prompt
            
        Returns:
            Generated text response
            
        Raises:
            GeminiAPIError: If generation fails
        """
        logger.info(f"Generating text (prompt length: {len(prompt)} chars)")
        
        def _generate():
            response = self.model.generate_content(prompt)
            return response.text
        
        result = self._retry_with_backoff(_generate)
        logger.info(f"Generated text (response length: {len(result)} chars)")
        return result
    
    def generate_json(self, prompt: str) -> Dict:
        """Generate JSON response from Gemini.
        
        Args:
            prompt: Text prompt (should instruct to return JSON)
            
        Returns:
            Parsed JSON response as dictionary
            
        Raises:
            GeminiAPIError: If generation or JSON parsing fails
        """
        logger.info("Generating JSON response")
        
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON, no other text."
        
        text_response = self.generate_text(json_prompt)
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            cleaned = text_response.strip()
            if cleaned.startswith('```'):
                # Extract content between ```json and ```
                lines = cleaned.split('\n')
                json_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                
                cleaned = '\n'.join(json_lines)
            
            result = json.loads(cleaned)
            logger.info("Successfully parsed JSON response")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {text_response[:500]}...")
            raise GeminiAPIError(f"Failed to parse JSON response: {e}")
    
    def analyze_with_template(self, template_name: str, **variables) -> str:
        """Generate text using a prompt template.
        
        Args:
            template_name: Name of prompt template from config
            **variables: Variables to interpolate into template
            
        Returns:
            Generated text response
            
        Raises:
            GeminiAPIError: If template not found or generation fails
        """
        template = self.prompts.get(template_name)
        if not template:
            raise GeminiAPIError(f"Prompt template not found: {template_name}")
        
        # Interpolate variables
        try:
            prompt = template.format(**variables)
        except KeyError as e:
            raise GeminiAPIError(f"Missing variable for template: {e}")
        
        return self.generate_text(prompt)
    
    def analyze_json_with_template(self, template_name: str, **variables) -> Dict:
        """Generate JSON using a prompt template.
        
        Args:
            template_name: Name of prompt template from config
            **variables: Variables to interpolate into template
            
        Returns:
            Parsed JSON response as dictionary
            
        Raises:
            GeminiAPIError: If template not found or generation fails
        """
        template = self.prompts.get(template_name)
        if not template:
            raise GeminiAPIError(f"Prompt template not found: {template_name}")
        
        # Interpolate variables
        try:
            prompt = template.format(**variables)
        except KeyError as e:
            raise GeminiAPIError(f"Missing variable for template: {e}")
        
        return self.generate_json(prompt)
    
    def analyze_video_url(self, video_url: str, prompt: str) -> str:
        """Analyze a video URL with a custom prompt.
        
        Note: This requires Gemini models with multimodal support.
        Currently, this is a placeholder that analyzes video metadata.
        
        Args:
            video_url: YouTube video URL
            prompt: Analysis prompt
            
        Returns:
            Analysis result
        """
        # Note: Full video analysis requires uploading video to Gemini
        # For now, we'll provide a text-based analysis approach
        logger.warning("Direct video URL analysis not yet implemented")
        logger.info(f"Analyzing video metadata for: {video_url}")
        
        enhanced_prompt = f"""
Analyze this YouTube video: {video_url}

{prompt}

Please provide a detailed analysis based on the video URL and typical content patterns.
"""
        
        return self.generate_text(enhanced_prompt)
