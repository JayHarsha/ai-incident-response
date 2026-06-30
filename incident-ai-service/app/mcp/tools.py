"""MCP-style tool functions the LangGraph agent can call."""

import json
import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
_KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"
_JAVA_URL = os.getenv("JAVA_SERVICE_URL", "http://localhost:8080")


def get_recent_logs(service_name: str, lines: int = 50) -> str:
    """Return the last N lines from a service log file."""
    log_file = _LOGS_DIR / f"{service_name}.log"
    if not log_file.exists():
        return f"[No log file found for '{service_name}'. Available: {[f.stem for f in _LOGS_DIR.glob('*.log')]}]"
    all_lines = log_file.read_text(encoding="utf-8").splitlines()
    return "\n".join(all_lines[-lines:])


def get_service_dependencies(service_name: str) -> str:
    """Return upstream/downstream dependency info for a service."""
    map_file = _KB_DIR / "architecture" / "service-map.json"
    if not map_file.exists():
        return "[service-map.json not found]"
    service_map: dict = json.loads(map_file.read_text(encoding="utf-8"))
    data = service_map.get(service_name)
    if not data:
        # Fuzzy: try stripping '-service' suffix
        short = service_name.replace("-service", "")
        data = next((v for k, v in service_map.items() if short in k), None)
    if not data:
        return f"[Service '{service_name}' not found in service map]"
    return json.dumps(data, indent=2)


def update_incident_status(incident_id: str, status: str) -> str:
    """Call the Java backend to update incident status via REST."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.put(
                f"{_JAVA_URL}/api/v1/incidents/{incident_id}/status",
                json={"status": status},
            )
            return f"Status updated → {status} (HTTP {resp.status_code})"
    except Exception as e:
        logger.warning("Could not update incident status: %s", e)
        return f"[Status update failed: {e}]"
