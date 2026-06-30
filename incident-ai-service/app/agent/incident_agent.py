"""LangGraph agent — the main AI brain of the incident platform."""

import logging
import re
from typing import Any, Callable, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from app.agent.prompts import ANALYSIS_PROMPT, CLASSIFICATION_PROMPT, SYSTEM_PROMPT
from app.mcp.tools import (
    get_recent_logs,
    get_service_dependencies,
    update_incident_status,
)
from app.models.incident import AnalysisResult, IncidentEvent
from app.producer.kafka_producer import IncidentKafkaProducer
from app.rag.qdrant_client import QdrantService

logger = logging.getLogger(__name__)


# ─── Agent state ────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    incident: IncidentEvent
    incident_type: str
    rag_results: list[str]  # filled by rag_search (parallel branch 1)
    logs: str               # filled by gather_context (parallel branch 2)
    dependencies: str       # filled by gather_context (parallel branch 2)
    analysis_text: str
    result: Any             # AnalysisResult | None


# ─── Agent ──────────────────────────────────────────────────────────────────

class IncidentAgent:

    def __init__(self, qdrant: QdrantService, producer: IncidentKafkaProducer, ollama_url: str):
        self.qdrant = qdrant
        self.producer = producer
        self.llm = ChatOllama(base_url=ollama_url, model="llama3.2", temperature=0.1, num_predict=1024)
        self.on_progress: Callable[[str, str], None] | None = None  # set from main.py
        self.graph = self._build_graph()

    # ── Graph wiring ─────────────────────────────────────────────────────────

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("classify", self._classify)
        g.add_node("rag_search", self._rag_search)
        g.add_node("gather_context", self._gather_context)
        g.add_node("generate_analysis", self._generate_analysis)
        g.add_node("publish", self._publish)

        g.set_entry_point("classify")

        # After classify, fan OUT to two nodes that run in PARALLEL
        g.add_edge("classify", "rag_search")
        g.add_edge("classify", "gather_context")

        # generate_analysis fans IN — waits for BOTH parallel nodes to finish
        g.add_edge("rag_search", "generate_analysis")
        g.add_edge("gather_context", "generate_analysis")

        g.add_edge("generate_analysis", "publish")
        g.add_edge("publish", END)
        return g.compile()

    # ── Public entry point ───────────────────────────────────────────────────

    def process_incident(self, incident: IncidentEvent) -> None:
        logger.info("Agent starting analysis for %s", incident.incidentId)
        update_incident_status(incident.incidentId, "ANALYZING")

        state: AgentState = {
            "incident": incident,
            "incident_type": "",
            "rag_results": [],
            "logs": "",
            "dependencies": "",
            "analysis_text": "",
            "result": None,
        }

        # stream() fires after every node — invoke() fires only at the end
        for event in self.graph.stream(state):
            node_name = list(event.keys())[0]
            if node_name == "__end__":
                continue
            logger.info("Node completed: [%s] for incident %s", node_name, incident.incidentId)
            if self.on_progress:
                self.on_progress(incident.incidentId, node_name)

    # ── Node implementations ─────────────────────────────────────────────────

    def _classify(self, state: AgentState) -> dict:
        inc = state["incident"]
        prompt = CLASSIFICATION_PROMPT.format(
            service=inc.serviceName, error=inc.errorMessage, severity=inc.severity
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        incident_type = response.content.strip().upper()
        logger.info("Classified %s as %s", inc.incidentId, incident_type)
        return {"incident_type": incident_type}

    # ── Parallel branch 1 ────────────────────────────────────────────────────

    def _rag_search(self, state: AgentState) -> dict:
        inc = state["incident"]
        query = f"{inc.serviceName} {inc.errorMessage} {state['incident_type']}"
        past = self.qdrant.search(query, limit=3, doc_type="past_incident")
        runbooks = self.qdrant.search(query, limit=2, doc_type="runbook")
        rag_results = [r["content"][:600] for r in past + runbooks]
        logger.info("RAG returned %d results for %s", len(rag_results), inc.incidentId)
        return {"rag_results": rag_results}

    # ── Parallel branch 2 ────────────────────────────────────────────────────

    def _gather_context(self, state: AgentState) -> dict:
        inc = state["incident"]
        return {
            "logs": get_recent_logs(inc.serviceName, 40),
            "dependencies": get_service_dependencies(inc.serviceName),
        }

    # ── Fan-in — runs only after BOTH parallel branches complete ─────────────

    def _generate_analysis(self, state: AgentState) -> dict:
        inc = state["incident"]
        rag_text = "\n---\n".join(state["rag_results"]) if state["rag_results"] else "None found"

        stack_section = f"Stack Trace:\n{inc.stackTrace[:500]}\n\n" if inc.stackTrace else ""
        context = (
            f"Incident ID: {inc.incidentId}\n"
            f"Service: {inc.serviceName}\n"
            f"Error: {inc.errorMessage}\n"
            f"Severity: {inc.severity}\n"
            f"Environment: {inc.environment}\n"
            f"Incident Type: {state['incident_type']}\n\n"
            + stack_section
            + f"Recent Logs:\n{state['logs'][:600]}\n\n"
            f"Service Dependencies:\n{state['dependencies'][:400]}\n\n"
            f"RAG — Similar Past Incidents & Runbooks:\n{rag_text[:1200]}"
        )
        prompt = ANALYSIS_PROMPT.format(context=context)
        response = self.llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        return {"analysis_text": response.content}

    def _publish(self, state: AgentState) -> dict:
        inc = state["incident"]
        result = self._parse_analysis(inc.incidentId, state["analysis_text"], state)
        self.producer.publish_analysis_result(result)
        logger.info("Published analysis for %s (confidence %.2f)", inc.incidentId, result.confidenceScore)
        return {"result": result}

    # ── Parser ───────────────────────────────────────────────────────────────

    def _parse_analysis(self, incident_id: str, text: str, state: AgentState) -> AnalysisResult:
        # Strip markdown formatting the LLM adds despite being told not to
        clean = re.sub(r"\*+", "", text)
        clean = re.sub(r"`+", "", clean)
        clean = re.sub(r"^#+\s*", "", clean, flags=re.MULTILINE)

        root_cause = ""
        impacted: list[str] = []
        steps: list[str] = []
        similar: list[str] = []
        confidence = 0.5
        current_section = ""

        for line in clean.splitlines():
            stripped = line.strip()
            lower = stripped.lower()
            if not stripped:
                continue

            # Use re.search so headers are found anywhere on the line,
            # not just at the start — handles LLM preamble like "Incident Report Root Cause:"
            if re.search(r"root\s*cause\s*:", lower):
                m = re.search(r"root\s*cause\s*:\s*(.+)", stripped, re.IGNORECASE)
                if m:
                    root_cause = m.group(1).strip()
                current_section = "root_cause"  # capture next line if inline text missing
            elif current_section == "root_cause" and not root_cause and not re.search(r"impacted|remediation|similar|confidence", lower):
                root_cause = stripped
                current_section = ""
            elif re.search(r"impacted\s*services", lower):
                current_section = "impacted"
            elif re.search(r"remediation\s*steps|recommended\s*steps", lower):
                current_section = "steps"
            elif re.search(r"similar\s*past\s*incidents", lower):
                current_section = "similar"
            elif re.search(r"confidence\s*:", lower):
                m = re.search(r"confidence\s*:\s*([\d.]+)", stripped, re.IGNORECASE)
                if m:
                    try:
                        val = float(m.group(1))
                        confidence = val / 100 if val > 1 else val
                    except ValueError:
                        pass
            elif re.match(r"^[-•*]\s+\S", stripped) or re.match(r"^\d+[.)]\s+\S", stripped):
                item = re.sub(r"^[-•*\d][.)]\s*", "", stripped).strip()
                item = re.sub(r"^-\s*", "", item).strip()
                if item:
                    if current_section == "impacted":
                        impacted.append(item)
                    elif current_section == "steps":
                        steps.append(item)
                    elif current_section == "similar":
                        similar.append(item)

        if not root_cause:
            # Last resort: grab the first non-empty sentence from the response
            sentences = [s.strip() for s in re.split(r"[.\n]", clean) if len(s.strip()) > 20]
            root_cause = sentences[0] if sentences else clean[:200].replace("\n", " ")

        # Match a runbook from RAG results — extract just the title, not raw content
        matched_runbook = None
        for r in state.get("rag_results", []):
            if "runbook" in r.lower():
                lines = [l.strip() for l in r.splitlines() if l.strip()]
                title = re.sub(r'^#+\s*', '', lines[0]) if lines else r[:80]
                matched_runbook = title
                break

        # Override LLM-reported confidence with evidence-based scoring.
        # The LLM consistently over-reports confidence, so we compute it
        # deterministically from what evidence was actually available.
        inc = state["incident"]
        has_logs = bool(state.get("logs", "").strip()) and "not found" not in state.get("logs", "").lower()
        has_stack_trace = bool(inc.stackTrace) if hasattr(inc, "stackTrace") else False
        has_rag = len(state.get("rag_results", [])) > 0

        if has_logs or has_stack_trace:
            evidence_confidence = 0.6
            if has_rag:
                evidence_confidence += 0.2   # logs + past match = up to 0.8
        elif has_rag:
            evidence_confidence = 0.5        # runbook/past match only = 0.5
        else:
            evidence_confidence = 0.3        # error message only = 0.3

        return AnalysisResult(
            incidentId=incident_id,
            rootCause=root_cause,
            impactedServices=impacted[:5],
            recommendedSteps=steps[:5],
            similarPastIncidents=similar[:3],
            confidenceScore=round(min(evidence_confidence, 1.0), 2),
            matchedRunbook=matched_runbook,
            rawAnalysis=text,
        )
