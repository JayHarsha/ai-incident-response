# incident-service — Java REST Backend

Spring Boot 4.1 service. Owns the incident lifecycle: REST API, Postgres persistence, and bidirectional Kafka integration with the AI layer.

---

## Responsibilities

- REST API consumed by the React dashboard
- Persists incidents to PostgreSQL
- Publishes incident JSON to Kafka `incident-created` on creation
- Consumes AI results from Kafka `incident-analyzed`, writes them back to Postgres

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/incidents` | Create incident (triggers Kafka publish) |
| `GET` | `/api/v1/incidents` | List all (newest first) |
| `GET` | `/api/v1/incidents/{id}` | Get by ID |
| `PUT` | `/api/v1/incidents/{id}/status` | Update status |
| `GET` | `/api/v1/incidents/service/{name}` | Filter by service |

### Create — example request

```json
POST /api/v1/incidents
{
  "serviceName": "payment-service",
  "errorMessage": "HikariCP connection pool exhausted after 30s",
  "severity": "CRITICAL",
  "environment": "PROD"
}
```

---

## Kafka Topics

| Direction | Topic | Details |
|---|---|---|
| Producer | `incident-created` | Full incident JSON, key = `incidentId`, `acks=all` |
| Consumer | `incident-analyzed` | AI result — updates root cause, steps, confidence, status → `ANALYZED` |

---

## Incident Status Flow

```
OPEN → ANALYZING (Python MCP) → ANALYZED (Kafka consumer) → RESOLVED (user)
```

---

## Tech Stack

| | |
|---|---|
| Runtime | Java 21 |
| Framework | Spring Boot 4.1 |
| Persistence | Spring Data JPA + Hibernate + PostgreSQL 17 |
| Pool | HikariCP (fixed 10-connection pool) |
| Messaging | Spring Kafka (producer + consumer) |
| Boilerplate | Lombok |

---

## Local Development

**Prerequisites:** Java 21, Maven 3.9+ (or use `mvnw` wrapper), Docker running

```bash
# Step 1 — start infrastructure (from repo root)
docker compose up kafka postgres -d

# Step 2 — run the service
cd incident-service
./mvnw spring-boot:run        # Mac/Linux
mvnw.cmd spring-boot:run      # Windows
```

Starts on **http://localhost:8080**

---

## Configuration

### Default credentials

| Setting | Value |
|---|---|
| DB URL | `localhost:5432/incident_db` (local) |
| DB username | `postgres` |
| DB password | `@Qwerty7` |
| Kafka | `localhost:9092` |

> Note: Docker Compose maps Postgres to host port **5433** to avoid conflict with local Postgres installations. The Java service inside Docker still connects via the internal `5432`.

### Changing the DB password

Update in **two places**:

```properties
# incident-service/src/main/resources/application.properties (local dev)
spring.datasource.password=your-new-password
```

```yaml
# docker-compose.yml (Docker)
POSTGRES_PASSWORD: your-new-password          # under postgres service
SPRING_DATASOURCE_PASSWORD: your-new-password # under incident-service
```

### Key properties

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/incident_db
spring.kafka.bootstrap-servers=localhost:9092
spring.jpa.hibernate.ddl-auto=update   # auto-creates tables
```

In Docker, `docker-compose.yml` env vars override these automatically:
- `SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/incident_db`
- `SPRING_KAFKA_BOOTSTRAP_SERVERS=kafka:29092`
