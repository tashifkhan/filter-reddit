import json
import logging
from abc import ABC, abstractmethod
from confluent_kafka import Consumer, KafkaError
from django.conf import settings

logger = logging.getLogger(__name__)

class AbstractConfluentKafkaConsumer(ABC):
    def __init__(self, topic, group_id='my-group', auto_offset_reset='earliest'):
        self.topic = topic
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        # Initialize the Kafka consumer with manual offset commits.
        self.consumer = Consumer({
            'bootstrap.servers': self.bootstrap_servers,
            'auto.offset.reset': auto_offset_reset,
            'group.id': group_id,
            'enable.auto.commit': False
        })
        try:
            self.consumer.subscribe([self.topic])
        except Exception as e:
            logger.error(f"Error subscribing to topic {self.topic}: {e}")
            raise e

    def consume_messages(self):
        """Continuously poll and process messages from Kafka."""
        try:
            while True:
                msg = self.consumer.poll(1.0)  # Poll with a timeout of 1 second.
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                    else:
                        logger.error(f"Error: {msg.error()}")
                    continue

                try:
                    # Decode the message value (assuming UTF-8) and parse as JSON.
                    message_value = msg.value()
                    if isinstance(message_value, bytes):
                        message_value = message_value.decode('utf-8')
                    logger.info(f"Processing message at offset {msg.offset()}: {message_value}")
                    content = json.loads(message_value)
                    self._process_message(content)

                    self.consumer.commit(msg)
                    logger.info(f"Committed offset {msg.offset()} for partition {msg.partition()}.")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON for message at offset {msg.offset()}: {e}")
                except Exception as e:
                    logger.error(f"Error processing message at offset {msg.offset()}: {e}")
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.consumer.close()

    @abstractmethod
    def _process_message(self, content):
        """Implement this method in subclasses to define custom processing of messages."""
        pass
