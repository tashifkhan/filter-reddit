import logging
import json
import threading
from typing import Dict, Any
from django.conf import settings
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

class KafkaProducer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the Kafka producer with configuration from Django settings."""
        # Ensure that initialization happens only once
        if hasattr(self, 'producer'):
            return

        # Get configuration from Django settings
        self.bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', None)
        if not self.bootstrap_servers:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS not configured in Django settings")

        # Configure producer
        conf = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': getattr(settings, 'KAFKA_CLIENT_ID', 'reddit-filter')
        }

        # Create producer instance
        try:
            self.producer = Producer(conf)
        except Exception as e:
            logger.error(f"Error creating Kafka producer: {e}")
            raise e

    def delivery_report(self, err, msg):
        """Callback for message delivery reports."""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    def produce_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """
        Produce a message to Kafka topic.
        
        Args:
            topic: Kafka topic to produce to
            message: Dictionary containing the message to send
            
        Returns:
            bool: True if message was successfully queued, False otherwise
        """
        try:
            # Convert message to JSON string
            message_str = json.dumps(message)

            # Produce message
            self.producer.produce(
                topic=topic,
                value=message_str.encode('utf-8'),
                callback=self.delivery_report
            )

            # Trigger delivery report callbacks
            self.producer.poll(0)
            
            # Flush to ensure message is delivered
            self.producer.flush()
            
            return True

        except Exception as e:
            logger.error(f"Error producing message to Kafka: {str(e)}")
            return False
    