# Runbook: payment-service

## Overview
Payment service handles all monetary transactions. SLA: 15-minute response. Any CRITICAL or HIGH incident requires immediate on-call page.

## Common Incidents & Remediation

### 1. HikariCP Connection Pool Exhausted
**Symptoms:** `Connection is not available, request timed out after 30000ms`
**Steps:**
1. Check pool metrics: `GET /actuator/metrics/hikaricp.connections.active`
2. Identify long-running queries: `SELECT pid, query, duration FROM pg_stat_activity WHERE state = 'active'`
3. Kill blocking queries if safe: `SELECT pg_terminate_backend(pid)`
4. Increase pool size temporarily: update `maximum-pool-size` in config and rolling-restart
5. Check for batch jobs holding connections — suspend if running
6. Long-term: move analytics queries to read replica

### 2. Payment Gateway Timeout
**Symptoms:** `Read timeout executing POST https://gateway.payments.io/charge`
**Steps:**
1. Check gateway status page
2. Verify outbound network connectivity from pod: `curl -v https://gateway.payments.io/health`
3. Check circuit breaker state via `/actuator/circuitbreakers`
4. If CB is OPEN, payments will auto-recover once gateway is back
5. If prolonged (>30 min), escalate to payment provider support

### 3. High Error Rate (5xx)
**Steps:**
1. Check error logs: `kubectl logs -l app=payment-service --tail=200`
2. Review recent deployments: any changes in last 2 hours?
3. Rollback if deployment is suspected cause: `kubectl rollout undo deployment/payment-service`

## Escalation
- On-call: payments-oncall@company.com
- SEV1 (>5% transactions failing): page immediately
- SEV2 (degraded performance): notify within 15 minutes

## Health Endpoints
- `/actuator/health` — overall health
- `/actuator/metrics/hikaricp.connections.active` — pool usage
- `/actuator/circuitbreakers` — circuit breaker states
