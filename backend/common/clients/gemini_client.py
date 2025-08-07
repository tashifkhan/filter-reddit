import logging
import os
import re
import json
import time
import threading
from google import genai
from google.genai import types
from django.conf import settings

# Setup logging
logger = logging.getLogger(__name__)

class GeminiClient:
    _thread_local = threading.local()

    def _get_client(self):
        """
        Get or create a client for the current thread.
        """
        if not hasattr(self._thread_local, "client"):
            self._thread_local.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            logger.info("GeminiClient initialized for thread %s", threading.get_ident())
        return self._thread_local.client

    def execute_prompt(self, prompt, model='gemini-2.5-flash', temperature=0, max_tokens=int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", 65000)), response_type='text', thinking_budget=None):
        if response_type == 'json':
            response_format = "application/json"
        elif response_type == 'text':
            response_format = "text/plain"
        try:
            # Create generation config as a dictionary
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "response_mime_type": response_format,
            }

            # Add thinking_config if thinking_budget is provided
            if thinking_budget is not None:
                generation_config["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
            
            response = self._get_client().models.generate_content(
                        model=model,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            **generation_config
                        ),
                    )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error occurred while gemini api call: {e}")
            raise
    
    def create_embeddings(self, text, model="gemini-embedding-001", task_type=None):
        retry_waits = [10, 60, 100]
        for attempt in range(3):
            try:
                config=types.EmbedContentConfig(task_type=task_type)
                response = self._get_client().models.embed_content(model=model, contents=[text], config=config)
                return response.embeddings[0].values
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "RATE_LIMIT_EXCEEDED" in error_str:
                    if attempt < 2:  # Only retry if we have attempts left
                        wait_time = retry_waits[attempt]
                        logger.warning(f"Rate limit hit (attempt {attempt + 1}/3). Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limit hit after 3 attempts. Giving up on this requirement.")
                        return []
                else:
                    # Other error - don't retry
                    logger.error(f"Error generating embeddings for requirement: {e}")
                    return []
