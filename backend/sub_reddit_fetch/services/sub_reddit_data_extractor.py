import logging
import time
from typing import Dict, Any, List

import requests

logger = logging.getLogger(__name__)

class SubRedditDataExtractor:
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
    
    def fetch_sub_reddit_data(self, sub_reddit_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches subreddit posts from the Reddit Data Filter API.
        """
        url = f"{self.api_base_url}/subreddit/{sub_reddit_name}/posts"
        params = {"subreddit_name": sub_reddit_name, "limit": limit}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch subreddit data for '{sub_reddit_name}': {e}")
            return []

        