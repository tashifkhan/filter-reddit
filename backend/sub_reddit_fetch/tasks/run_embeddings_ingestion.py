import logging
from typing import Any, Dict
from backend.celery import app
from common.clients.gemini_client import GeminiClient
from common.clients.opensearch_client import OpenSearchClient
from django.conf import settings

logger = logging.getLogger(__name__)


@app.task
def ingest_embeddings(sub_reddit_data: Dict[str, Any]):
    """Celery task that create and ingest embeddings to opensearch.

    Args:
        sub_reddit_data: Data of the subreddit to create embeddings and ingest to opensearch

    """

    logger.info("[Task] Starting embeddings ingestion")

    gemini_client = GeminiClient()
    opensearch_client = OpenSearchClient(index=settings.REDDIT_DATA_OPENSEARCH_INDEX)
    try:
        combined_text = sub_reddit_data.get("title", "") + " " + sub_reddit_data.get("selftext", "")
        embeddings = gemini_client.create_embeddings(combined_text)
        doc = {
            "post_embeddings": embeddings,
            "post_text": sub_reddit_data.get("selftext", ""),
            "title": sub_reddit_data.get("title", ""),
            "author": sub_reddit_data.get("author", ""),
            "score": sub_reddit_data.get("score", 0),
            "upvote_ratio": sub_reddit_data.get("upvote_ratio", 0),
            "url": sub_reddit_data.get("url", ""),
            "subreddit": sub_reddit_data.get("subreddit", ""),
        }
        opensearch_client.index_doc(doc)
        logger.info(f"Ingested embeddings")
        
    except Exception as exc:
        logger.exception("[Task] Embeddings ingestion failed: %s", exc)
        raise 
