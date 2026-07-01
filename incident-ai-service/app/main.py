"""FastAPI entry point for the Incident AI Service."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_INPUT_TOPIC = os.getenv("KAFKA_INPUT_TOPIC", "incident-created")
KAFKA_OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC", "incident-analyzed")
KAFKA_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "incident-ai-group")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
JAVA_SERVICE_URL = os.getenv("JAVA_SERVICE_URL", "http://localhost:8080")
KB_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")

# ─── WebSocket progress state ─────────────────────────────────────────────────
# Keyed by incidentId.
# _progress_history  — stores all node events so a late-connecting client gets replayed history
# _progress_queues   — live asyncio.Queue per connected WebSocket client

_event_loop: asyncio.AbstractEventLoop | None = None
_progress_history: dict[str, list[dict]] = {}
_progress_queues: dict[str, asyncio.Queue] = {}


def _emit_progress(incident_id: str, node_name: str) -> None:
    """Called from the agent's background thread after each LangGraph node completes."""
    event = {"node": node_name, "incidentId": incident_id}

    # Store in history so late-connecting clients get full replay
    _progress_history.setdefault(incident_id, []).append(event)

    # Push to the live queue if a WebSocket client is connected
    queue = _progress_queues.get(incident_id)
    if queue and _event_loop:
        _event_loop.call_soon_threadsafe(queue.put_nowait, event)


# ─── Lifespan ────────────────────────────────────────────────────────────────

_consumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer, _event_loop
    _event_loop = asyncio.get_running_loop()

    from app.rag.document_loader import DocumentLoader
    from app.rag.qdrant_client import QdrantService
    from app.producer.kafka_producer import IncidentKafkaProducer
    from app.mcp.client import McpClient
    from app.agent.incident_agent import IncidentAgent
    from app.consumer.kafka_consumer import IncidentKafkaConsumer

    logger.info("Syncing knowledge base with Qdrant…")
    qdrant = QdrantService(host=QDRANT_HOST, port=QDRANT_PORT)
    docs = DocumentLoader(KB_PATH).load_all_documents()
    qdrant.sync_documents(docs)

    mcp_client = McpClient(java_service_url=JAVA_SERVICE_URL)
    logger.info("MCP client configured → %s/mcp", JAVA_SERVICE_URL)

    producer = IncidentKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP, topic=KAFKA_OUTPUT_TOPIC)
    agent = IncidentAgent(qdrant=qdrant, producer=producer, ollama_url=OLLAMA_URL, mcp_client=mcp_client)
    agent.on_progress = _emit_progress  # wire the callback

    _consumer = IncidentKafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        topic=KAFKA_INPUT_TOPIC,
        group_id=KAFKA_GROUP,
        agent=agent,
    )
    _consumer.start()
    logger.info("✅ Incident AI Service ready — consuming from '%s'", KAFKA_INPUT_TOPIC)

    yield

    if _consumer:
        _consumer.stop()
    producer.close()
    logger.info("Incident AI Service shut down")


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="Incident AI Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "incident-ai-service"}


@app.get("/api/status")
def status():
    return {
        "status": "running",
        "kafka_input": KAFKA_INPUT_TOPIC,
        "kafka_output": KAFKA_OUTPUT_TOPIC,
        "qdrant": f"{QDRANT_HOST}:{QDRANT_PORT}",
        "ollama": OLLAMA_URL,
    }


@app.post("/api/reindex")
def reindex():
    """Force sync all knowledge base files into Qdrant (re-embeds changed files only)."""
    from app.rag.document_loader import DocumentLoader
    from app.rag.qdrant_client import QdrantService
    qdrant = QdrantService(host=QDRANT_HOST, port=QDRANT_PORT)
    docs = DocumentLoader(KB_PATH).load_all_documents()
    qdrant.sync_documents(docs)
    return {"status": "synced", "documents_checked": len(docs)}


@app.websocket("/ws/incidents/{incident_id}")
async def incident_progress_ws(websocket: WebSocket, incident_id: str):
    """
    Frontend connects here while an incident is ANALYZING.
    Receives one JSON message per LangGraph node as it completes.
    Late-connecting clients receive full history replay first.
    """
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    _progress_queues[incident_id] = queue

    try:
        # Replay any nodes that already completed before client connected
        for past_event in _progress_history.get(incident_id, []):
            await websocket.send_json(past_event)

        # Then stream live events until client disconnects or 5-minute timeout
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=300)
            await websocket.send_json(event)

    except (asyncio.TimeoutError, WebSocketDisconnect):
        pass
    finally:
        _progress_queues.pop(incident_id, None)
        _progress_history.pop(incident_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
