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

    try:
        extractor.fetch_sub_reddit_data(sub_reddit_name,duration)
        logger.info("[Task] Completed subreddit data extraction for sub_reddit_name: %s", sub_reddit_name)

        # Publish message for control matrix extraction
        kafka_producer = KafkaProducer()
        kafka_producer.produce_message(
            topic=settings.SUB_REDDIT_DATA_TOPIC,
            message={
                "sub_reddit_name": sub_reddit_name,
                "duration": duration
            }
        )
        logger.info(f"Sent sub_reddit_name to SubReddit Data Extraction for {sub_reddit_name}")
        
        return {"sub_reddit_name": sub_reddit_name, "duration": duration, "status": "completed"}
    except Exception as exc:
        logger.exception("[Task] Subreddit data extraction failed for sub_reddit_name %s: %s", sub_reddit_name, exc)
        raise 