import logging
from django.core.management.base import BaseCommand
from sub_reddit_fetch.services.embeddings_kafka_consumer import EmbeddingsKafkaConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the Kafka consumer for processing post data and ingest embeddings to opensearch'

    def handle(self, *args, **options):
        logger.info("Starting Post Data Kafka Consumer...")
        self.stdout.write(self.style.SUCCESS("Starting Post Data Kafka Consumer..."))
        
        try:
            consumer = EmbeddingsKafkaConsumer()
            consumer.consume()
        except KeyboardInterrupt:
            logger.info("Post Data Kafka Consumer stopped by user")
            self.stdout.write(self.style.WARNING("Post Data Kafka Consumer stopped by user"))
        except Exception as e:
            logger.error(f"Error in Post Data Kafka Consumer: {e}")
            self.stdout.write(self.style.ERROR(f"Error in Post Data Kafka Consumer: {e}")) 
