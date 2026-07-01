# incident-ai-service — Python AI Agent

FastAPI service hosting the LangGraph AI agent. Consumes incidents from Kafka, analyses them using RAG + Ollama, streams progress via WebSocket, publishes results back to Kafka.

---

## Pipeline

```
classify
   │
   ├──── rag_search    (parallel)  → searches Qdrant for past incidents + runbooks
   └──── gather_context (parallel) → reads service logs + dependency map
              │
         generate_analysis  → LLM synthesises root cause + remediation steps
              │
           publish  → writes result to Kafka incident-analyzed
```

Parallel branches cut wall-clock time roughly in half vs sequential execution.

---

## Confidence Scoring

Score is computed from actual evidence — not from the LLM's self-report:

| Evidence available | Score |
|---|---|
| Error message only | 30% |
| RAG match (runbook / past incident) | 50% |
| Logs or stack trace | 60% |
| Logs + RAG match | 80% |

---

## RAG Knowledge Base

```
knowledge_base/
├── past_incidents/    incident_001.md … incident_006.md
├── runbooks/          payment, auth, order, inventory, notification
└── architecture/      service-dependencies.md, service-map.json
```

- Embedded into Qdrant on startup using `all-MiniLM-L6-v2` (384 dims)
- SHA-256 hash deduplication — only changed files are re-embedded on restart
- First index: ~30s. Subsequent starts: instant

---

## WebSocket — Live Progress

`WS /ws/incidents/{incident_id}`

Emits after each node completes:
```json
{ "node": "classify",          "incidentId": "INC-78128" }
{ "node": "rag_search",        "incidentId": "INC-78128" }
{ "node": "gather_context",    "incidentId": "INC-78128" }
{ "node": "generate_analysis", "incidentId": "INC-78128" }
{ "node": "publish",           "incidentId": "INC-78128" }
```

Late-connecting clients receive full history replay on connect.

---

## HTTP Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /api/status` | Config dump |
| `POST /api/reindex` | Force re-sync knowledge base to Qdrant |
| `WS /ws/incidents/{id}` | Real-time node progress |

---

## MCP Client

The agent uses a lightweight **MCP client** (`app/mcp/client.py`) to call tools on the Java MCP server via JSON-RPC 2.0 (Streamable HTTP transport).

```
Agent calls:  mcp.call_tool("update_incident_status", {...})
  → POST /mcp  {"jsonrpc":"2.0","method":"tools/call","params":{...}}
  ← {"result": {"content": [{"type":"text","text":"Status updated to ANALYZING"}]}}
```

Protocol flow per incident:
1. `initialize` — handshake with Java MCP server
2. `tools/call: update_incident_status` — set status → ANALYZING before pipeline starts

The MCP server on the Java side also exposes `get_incident` for ad-hoc tool discovery.

---

## Tech Stack

| | |
|---|---|
| Runtime | Python 3.11 |
| API | FastAPI 0.138 + uvicorn |
| AI | LangGraph 0.2 + LangChain 0.3 |
| LLM | Ollama — llama3.2, temperature=0.1, num_predict=2048 (JSON mode for analysis) |
| Embeddings | Sentence Transformers — all-MiniLM-L6-v2 |
| Vector DB | Qdrant — cosine similarity |
| Messaging | kafka-python 2.0 |
| MCP client | mcp 1.28.1 — ClientSession + streamablehttp_client |
| HTTP client | httpx |

---

## Local Development

**Prerequisites:** Python 3.11, Docker running (Kafka + Qdrant), Ollama running

```bash
# Step 1 — start infrastructure (from repo root)
docker compose up kafka qdrant -d

# Step 2 — pull the model (one-time)
ollama pull llama3.2
ollama serve

# Step 3 — activate venv
.\venv\Scripts\Activate.ps1     # Windows
source venv/bin/activate         # Mac/Linux

# Step 4 — run
python -m uvicorn app.main:app --port 8000 --reload
```

---

## Environment Variables

Loaded from `.env` (local dev) or `docker-compose.yml` (Docker).

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `KAFKA_INPUT_TOPIC` | `incident-created` | Topic to consume |
| `KAFKA_OUTPUT_TOPIC` | `incident-analyzed` | Topic to publish |
| `KAFKA_CONSUMER_GROUP` | `incident-ai-group` | Consumer group |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `JAVA_SERVICE_URL` | `http://localhost:8080` | Java backend (MCP status updates) |
| `KNOWLEDGE_BASE_PATH` | `./knowledge_base` | Markdown knowledge base path |

> `.env` is gitignored. All defaults point to localhost for local dev. Docker Compose overrides them automatically with container hostnames.
