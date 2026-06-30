"""Pydantic models matching the Java IncidentEntity and Kafka payloads."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class IncidentEvent(BaseModel):
    """Payload consumed from the incident-created Kafka topic (mirrors Java IncidentEntity)."""

    incidentId: str
    traceId: Optional[str] = None
    serviceName: str
    environment: Optional[str] = "PROD"
    severity: str
    status: str
    errorMessage: str
    stackTrace: Optional[str] = None
    endpointOrOperation: Optional[str] = None
    createdAt: Any = None


class AnalysisResult(BaseModel):
    """Payload published to the incident-analyzed Kafka topic."""

    incidentId: str
    rootCause: str
    impactedServices: list[str] = Field(default_factory=list)
    recommendedSteps: list[str] = Field(default_factory=list)
    similarPastIncidents: list[str] = Field(default_factory=list)
    confidenceScore: float = Field(default=0.5, ge=0.0, le=1.0)
    matchedRunbook: Optional[str] = None
    rawAnalysis: Optional[str] = None
