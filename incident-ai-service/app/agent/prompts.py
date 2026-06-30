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

=== STRICT OUTPUT RULES ===
- Output ONLY the structure below. Nothing before it, nothing after it.
- No markdown. No asterisks. No bold. No backticks. No headers with #.
- Start your response with the literal text "Root Cause:" on the first line.
- The root cause is a HYPOTHESIS. If evidence is limited, qualify it with "likely" or "possibly".
- Step 1 must NEVER tell the developer to stop or restart the service — diagnose while it runs.
- Include specific commands, metric names, or log patterns wherever possible.
- Confidence scoring rules (be conservative):
    * 0.1–0.4 if you only have the error message with no logs or stack trace
    * 0.5–0.7 if you have matching past incidents or relevant runbook context
    * 0.8–0.9 only if you have actual logs, stack traces, AND past incident matches
- Step 5 is a long-term prevention measure — label it clearly, it is NOT an immediate action.

Root Cause: <one-sentence hypothesis — qualify with "likely" or "possibly" when uncertain>

Impacted Services:
- <service name>

Remediation Steps:
1. <inspect logs/metrics WITHOUT stopping the service — include the specific command or log pattern to search for>
2. <narrow down the root cause — name the specific metric, config value, or query to check>
3. <targeted fix — include the specific command, config change, or code path to address>
4. <verification — describe exactly how to confirm the fix worked>
5. Long-term: <prevention measure — this is a follow-up task, not an immediate action>

Similar Past Incidents:
- <title or brief description from the RAG context, or "None found">

Confidence: <decimal 0.0 to 1.0 — follow the scoring rules above>"""
