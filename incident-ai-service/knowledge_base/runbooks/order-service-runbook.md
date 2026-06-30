# Runbook: order-service

## Overview
Order service orchestrates the full order placement flow. Depends on auth-service, payment-service, and inventory-service. SLA: 15-minute response.

## Common Incidents & Remediation

### 1. Downstream payment-service Unreachable
**Symptoms:** `Connection refused` or `Upstream connect error` calling payment-service
**Steps:**
1. Verify payment-service health: `curl http://payment-service:8080/actuator/health`
2. Check circuit breaker state: `GET /actuator/circuitbreakers`
3. If CB is OPEN, orders will fail fast — investigate payment-service directly
4. Check Kubernetes service DNS: `nslookup payment-service`
5. Verify service port is correct: `kubectl describe service payment-service`
6. If recent deployment, rollback: `kubectl rollout undo deployment/order-service`

### 2. Database Deadlock on orders Table
**Symptoms:** `CannotAcquireLockException` or `deadlock detected`
**Steps:**
1. Identify blocking queries: `SELECT pid, query FROM pg_stat_activity WHERE wait_event_type = 'Lock'`
2. Terminate stale long-running transactions if safe
3. Check if batch reconciliation jobs are running — suspend if so
4. Review lock acquisition order in recent code changes
5. Add `SELECT FOR UPDATE SKIP LOCKED` to competing queries

### 3. Inventory-service Timeout
**Symptoms:** `Read timeout` calling inventory-service during stock check
**Steps:**
1. Check inventory-service health and response times
2. Increase circuit breaker timeout threshold temporarily
3. Enable fallback: return "pending" status rather than rejecting orders

## Escalation
- On-call: orders-oncall@company.com
- If payment-service is root cause: escalate to payments-oncall

## Health Endpoints
- `/actuator/health`
- `/actuator/circuitbreakers`
- `/actuator/metrics/order.placement.rate`
