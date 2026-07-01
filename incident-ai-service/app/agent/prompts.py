"""Prompt templates for the LangGraph incident analysis agent."""

SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) AI assistant.
You analyse production incidents, identify root causes, and provide precise, actionable remediation steps.
Be concise, structured, and specific. Do not guess — reason from the evidence provided."""

CLASSIFICATION_PROMPT = """Classify this production incident into exactly ONE of these categories:
DATABASE | MEMORY | NETWORK | KAFKA | APPLICATION | INFRASTRUCTURE

Service: {service}
Error: {error}
Severity: {severity}

Reply with ONLY the category name, nothing else."""

ANALYSIS_PROMPT = """Analyse this production incident using the context below.

=== INCIDENT CONTEXT ===
{context}

=== OUTPUT FORMAT ===
Output ONLY valid JSON — no markdown, no code fences, no extra text before or after.
Use exactly these keys:

{{
  "rootCause": "<one-sentence hypothesis — use 'likely' or 'possibly' when uncertain>",
  "impactedServices": ["<service-name>"],
  "remediationSteps": [
    "<Step 1: inspect logs/metrics WITHOUT restarting the service — include the exact command or log pattern>",
    "<Step 2: narrow down — name the specific metric, config value, or query to check>",
    "<Step 3: targeted fix — specific command, config change, or code path>",
    "<Step 4: verification — exactly how to confirm the fix worked>",
    "<Step 5: Long-term prevention — a follow-up task, NOT an immediate action>"
  ],
  "similarPastIncidents": ["<incident title from the RAG context>"],
  "confidence": 0.8
}}

Rules:
- remediationSteps MUST have exactly 5 items
- similarPastIncidents: use titles/descriptions from RAG context; empty array [] if none found
- confidence: 0.3 if error message only; 0.5-0.7 if runbook or past incident match; 0.8 only if logs + past incident matches
- Step 1 must NEVER tell the developer to restart or stop the service"""
