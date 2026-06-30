"""Kafka producer — publishes AnalysisResult to incident-analyzed topic."""

import json
import logging

from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.models.incident import AnalysisResult

logger = logging.getLogger(__name__)


class IncidentKafkaProducer:

    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
        )
        logger.info("Kafka producer initialised → topic: %s", topic)

    def publish_analysis_result(self, result: AnalysisResult) -> None:
        try:
            future = self.producer.send(
                self.topic,
                key=result.incidentId,
                value=result.model_dump(),
            )
            self.producer.flush()
            record_metadata = future.get(timeout=10)
            logger.info(
                "Published analysis for %s → partition %s offset %s",
                result.incidentId,
                record_metadata.partition,
                record_metadata.offset,
            )
        except KafkaError as e:
            logger.error("Failed to publish analysis result for %s: %s", result.incidentId, e)

    def close(self) -> None:
        self.producer.close()
        logger.info("Kafka producer closed")
