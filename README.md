# InciSight — AI Incident Intelligence Platform

> Auto-classify, analyse, and remediate production incidents using LangGraph agents, RAG, and real-time streaming.

---

## What It Does

1. Engineer submits an incident (service name + error + severity)
2. Java service saves it to Postgres and publishes to Kafka
3. Python AI agent runs a 5-step pipeline:
   - **Classify** → identifies incident type (DATABASE / KAFKA / NETWORK / etc.)
   - **RAG Search** + **Gather Context** → runs in parallel; searches past incidents & runbooks in Qdrant, fetches live logs
   - **Generate Analysis** → LLM produces root cause hypothesis + actionable remediation steps
   - **Publish** → result sent back via Kafka, Postgres updated
4. Dashboard shows live node progress via WebSocket, then displays the full AI report

---

## Architecture

```
React Dashboard (3000)
      │  REST + WebSocket
      ▼
incident-service  ──Kafka: incident-created──▶  incident-ai-service
Java / Spring Boot (8080)                        Python / FastAPI (8000)
      │  ◀──── MCP (JSON-RPC 2.0) ─────────────────────┤
      │                                          ┌──────┴──────┐
      ▼                                       Qdrant        Ollama
  PostgreSQL (5433)                          vectors       local LLM
      ▲                                        └──────┬──────┘
      └──────Kafka: incident-analyzed──────────────────┘
```

**Three communication protocols in use:**
- **REST** — React dashboard ↔ Java (synchronous CRUD)
- **Kafka** — Java ↔ Python AI agent (async event streaming)
- **MCP** — Python AI agent → Java (tool calls via JSON-RPC 2.0 protocol)

---

## Services & Ports

| Service | Port | Role |
|---|---|---|
| `incident-dashboard` | 3000 | React UI |
| `incident-service` | 8080 | Java REST API + Kafka producer/consumer |
| `incident-ai-service` | 8000 | Python AI agent + WebSocket |
| Kafka | 9092 | Event bus |
| Kafka UI | 8081 | Browse topics & messages |
| **PostgreSQL** | **5433** | Incident storage (Docker mapped to 5433 to avoid conflict with local Postgres on 5432) |
| Qdrant | 6333 | Vector DB for RAG |

> **Why 5433?** Docker Postgres is mapped to `5433` so it coexists with any local Postgres installation on the default `5432`. All inter-service communication inside Docker still uses `5432` — only the host-facing port changes.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | 24+ | Must be running |
| Ollama | 0.3+ | Must run on host machine |
| Git | any | |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/JayHarsha/ai-incident-response.git
cd ai-incident-response

# 2. Pull the LLM (one-time, ~2 GB)
ollama pull llama3.2

# 3. Make sure Ollama is running
ollama serve

# 4. Start everything
docker compose up --build
```

First build: **5–10 min**. Subsequent starts: fast (cached layers).

### URLs after startup

| URL | What |
|---|---|
| http://localhost:3000 | Dashboard |
| http://localhost:8080/api/v1/incidents | Java REST API |
| http://localhost:8000/health | AI service health |
| http://localhost:8081 | Kafka UI |
| http://localhost:6333/dashboard | Qdrant |

---

## Configuration

### Credentials (defaults — work out of the box)

| Setting | Value |
|---|---|
| DB host (from host machine) | `localhost:5433` |
| DB name | `incident_db` |
| DB username | `postgres` |
| DB password | `@Qwerty7` |

### Changing the DB password

Update it in **both** files:

```yaml
# docker-compose.yml — under postgres service
POSTGRES_PASSWORD: your-new-password

# docker-compose.yml — under incident-service
SPRING_DATASOURCE_PASSWORD: your-new-password
```

```properties
# incident-service/src/main/resources/application.properties (local dev only)
spring.datasource.password=your-new-password
```

> After changing password on an existing volume: `docker compose down -v` then `docker compose up --build`

### Changing the Ollama model

1. `ollama pull <model-name>`
2. Update `model=` in `incident-ai-service/app/agent/incident_agent.py`

---

## Local Development (without Docker)

Run infrastructure in Docker, services natively for faster iteration.

```bash
# Start only infrastructure
docker compose up kafka postgres qdrant -d
```

Then in separate terminals:

```bash
# Java service
cd incident-service
./mvnw spring-boot:run          # Mac/Linux
mvnw.cmd spring-boot:run        # Windows
```

```bash
# Python AI service
cd incident-ai-service
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate       # Mac/Linux
python -m uvicorn app.main:app --port 8000 --reload
```

```bash
# React dashboard
cd incident-dashboard
npm install && npm run dev      # opens at localhost:3000
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| AI service can't reach Ollama | Run `ollama serve` on host. On Linux add `--add-host=host.docker.internal:host-gateway` |
| `incident-service` Kafka errors on startup | Normal — Kafka healthcheck retries 15×. Wait 30s or check `docker compose logs kafka` |
| Qdrant slow on first start | Expected — embedding 12 knowledge base files takes ~30s. Fast on restart |
| Port already in use | Stop local services on 8080 / 8000 / 3000 / 9092 / 6333 / 8081 |
| Local Postgres conflict on 5432 | Docker Postgres uses 5433 — no conflict. If issues: `docker compose down -v && docker compose up --build` |
| DB auth failure after password change | `docker compose down -v` wipes the old volume, then re-up |

---

## Tech Stack

```
Java 21 · Spring Boot 4.1 · Spring Kafka · Spring Data JPA · PostgreSQL 17 · HikariCP · MCP Server
Python 3.11 · FastAPI · LangGraph 0.2 · LangChain · ChatOllama (llama3.2) · MCP Client
Sentence Transformers (all-MiniLM-L6-v2) · Qdrant · kafka-python · Pydantic v2 · httpx
React 19 · Vite 8 · TailwindCSS v4 · React Router v7 · Axios · Native WebSocket
Apache Kafka (KRaft) · Model Context Protocol (MCP) · Docker · nginx
```
