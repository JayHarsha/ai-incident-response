# incident-dashboard — React Frontend

Real-time incident management UI. Live AI analysis progress via WebSocket, auto-refresh, create/resolve incidents.

---

## Pages

### Dashboard `/`
- Summary cards: OPEN / ANALYZING / ANALYZED / RESOLVED counts
- Click a card to filter the list
- **Create Incident** modal with quick-fill sample services
- Auto-refreshes every 10 seconds

### Incident Detail `/incidents/:id`
- **LangGraph Progress Tracker** — live node chips (Classify → Search ∥ Gather → Analyse → Publish), each turns green on completion via WebSocket
- **AI Analysis Report** — root cause hypothesis, remediation steps, confidence score, matched runbook
- **Mark Resolved** button
- Auto-refreshes every 10 seconds while OPEN or ANALYZING

---

## Tech Stack

| | |
|---|---|
| Framework | React 19 |
| Build | Vite 8 |
| Styling | TailwindCSS v4 |
| Routing | React Router v7 |
| HTTP | Axios |
| Real-time | Native WebSocket API |

---

## Proxy Setup

In **dev** (`vite.config.js`):
- `/api/*` → `http://localhost:8080` (Java)
- `/ws/*` → `ws://localhost:8000` (Python)

In **production** (`nginx.conf` inside Docker):
- Same routing handled by nginx inside the container

No CORS config needed in either environment.

---

## Component Structure

```
src/
├── pages/
│   ├── Dashboard.jsx        cards, list, create modal
│   └── IncidentPage.jsx     detail view + WebSocket progress tracker
├── components/
│   ├── IncidentDetail.jsx   AI report display
│   ├── IncidentList.jsx     filtered card list
│   ├── IncidentCard.jsx     compact clickable card
│   ├── CreateIncidentForm.jsx  modal with sample quick-fills
│   ├── StatusBadge.jsx      colour-coded status pill
│   └── SeverityBadge.jsx   colour-coded severity pill
└── services/
    └── api.js               axios wrapper for Java REST API
```

---

## Local Development

**Prerequisites:** Node.js 18+, Java service on :8080, Python AI service on :8000

```bash
cd incident-dashboard
npm install
npm run dev    # opens at http://localhost:3000
```

---

## Docker / Production Build

Built automatically by `docker compose up --build`.

To build manually:
```bash
docker build -t incident-dashboard .
```

Multi-stage: Node 20 Alpine builds `dist/` → nginx Alpine serves it on port 80 (mapped to host :3000).
