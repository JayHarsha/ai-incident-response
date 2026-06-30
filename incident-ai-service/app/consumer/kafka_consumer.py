"""Kafka consumer — listens on incident-created and drives the AI agent."""

import json
import logging
import threading

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from app.models.incident import IncidentEvent

logger = logging.getLogger(__name__)


class IncidentKafkaConsumer:

    def __init__(self, bootstrap_servers: str, topic: str, group_id: str, agent):
        self._agent = agent
        self._running = False
        self._thread: threading.Thread | None = None

        self._consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            consumer_timeout_ms=1000,  # lets the loop check _running every second
        )
        logger.info("Kafka consumer initialised ← topic: %s  group: %s", topic, group_id)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True, name="kafka-consumer")
        self._thread.start()
        logger.info("Kafka consumer thread started")

    def stop(self) -> None:
        self._running = False
        self._consumer.close()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Kafka consumer stopped")

    def _consume_loop(self) -> None:
        while self._running:
            try:
                for message in self._consumer:
                    if not self._running:
                        break
                    try:
                        incident = IncidentEvent(**message.value)
                        logger.info(
                            "Received incident %s from %s (severity: %s)",
                            incident.incidentId,
                            incident.serviceName,
                            incident.severity,
                        )
                        # Run agent in its own thread — consumer keeps polling
                        threading.Thread(
                            target=self._agent.process_incident,
                            args=(incident,),
                            daemon=True,
                            name=f"agent-{incident.incidentId}",
                        ).start()
                    except Exception as e:
                        logger.error("Error processing message: %s", e, exc_info=True)
            except KafkaError as e:
                if self._running:
                    logger.error("Kafka consumer error: %s", e)
