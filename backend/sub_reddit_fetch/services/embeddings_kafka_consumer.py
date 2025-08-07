import logging
from typing import Dict, Any
from common.clients.abstract_kafka_consumer import AbstractConfluentKafkaConsumer
from django.conf import settings

from sub_reddit_fetch.tasks.run_embeddings_ingestion import ingest_embeddings

logger = logging.getLogger(__name__)


class EmbeddingsKafkaConsumer(AbstractConfluentKafkaConsumer):
    """Kafka consumer that receives messages and triggers
    the asynchronous embeddings ingestion task."""

    def __init__(self):
        super().__init__(
            topic=settings.EMBEDDINGS_TOPIC,
            group_id=settings.EMBEDDINGS_KAFKA_CONSUMER_GROUP_ID,
        )

    def _process_message(self, content: Dict[str,Any]) -> None:
        try:
            if not content:
                logger.warning("Received empty message – skipping")
                return

            async_res = ingest_embeddings.delay(content)
            logger.info("Scheduled ingest_embeddings task %s for sub_reddit_name: %s", 
                       async_res.id, async_res.subreddit)

        except Exception as exc:
            logger.error("Error processing message: %s", exc) 
