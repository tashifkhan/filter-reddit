import logging

from backend.celery import app
from sub_reddit_fetch.services.sub_reddit_data_extractor import SubRedditDataExtractor
from common.clients.kafka_producer import KafkaProducer
from django.conf import settings

logger = logging.getLogger(__name__)


@app.task
def fetch_sub_reddit_data(sub_reddit_name: str,duration: int) -> dict:
    """Celery task that fetches data from a subreddit.

    Args:
        sub_reddit_name: Name of the subreddit to fetch data from
        duration: Duration of the data to fetch in minutes

    Returns:
        Dict containing processing results
    """

    logger.info("[Task] Starting subreddit data extraction for sub_reddit_name: %s", sub_reddit_name)

    extractor = SubRedditDataExtractor()
    kafka_producer = KafkaProducer()
    try:
        sub_reddit_data = extractor.fetch_sub_reddit_data(sub_reddit_name,duration)
        logger.info("[Task] Completed subreddit data extraction for sub_reddit_name: %s", sub_reddit_name)

        for data in sub_reddit_data:
            kafka_producer.produce_message(
                topic=settings.EMBEDDINGS_TOPIC,
                message=data
            )
        logger.info(f"Sent sub_reddit_name to SubReddit Data Extraction for {sub_reddit_name}")
        
    except Exception as exc:
        logger.exception("[Task] Subreddit data extraction failed for sub_reddit_name %s: %s", sub_reddit_name, exc)
        raise 
