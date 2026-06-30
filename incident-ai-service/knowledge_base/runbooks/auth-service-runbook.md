# Runbook: auth-service

## Overview
Auth service is the gateway dependency for ALL other services. Any auth outage causes a full platform outage. SLA: 5-minute response. AUTO-PAGE on any CRITICAL alert.

## Common Incidents & Remediation

### 1. OutOfMemoryError / Heap Exhaustion
**Symptoms:** `java.lang.OutOfMemoryError: Java heap space` or GC overhead >90%
**Steps:**
1. Check heap usage: `GET /actuator/metrics/jvm.memory.used`
2. Trigger heap dump if stable: `jmap -dump:format=b,file=heap.hprof <pid>`
3. Immediate: rolling restart — `kubectl rollout restart deployment/auth-service`
4. Check for unbounded caches: JWT token cache, session cache
5. Apply emergency patch: set `caffeine.cache.maximum-size=10000`
6. Long-term: profile with JProfiler to identify memory leak source

### 2. High Latency on Token Validation
**Symptoms:** P99 auth latency >500ms, downstream services timing out
**Steps:**
1. Check Redis cache hit rate: `redis-cli info stats | grep hit_rate`
2. If cache miss rate is high: flush and rebuild cache
3. Check LDAP/OAuth provider response times
4. If LDAP is slow: check LDAP connection pool and AD health

### 3. JWT Signing Key Rotation Issues
**Symptoms:** `Invalid signature` errors after key rotation
**Steps:**
1. Verify new signing key propagated to all instances
2. Ensure old key is kept as verification key for 15 minutes during rotation
3. Monitor `auth.token.validation.errors` metric during rotation window

## Escalation
- On-call: platform-oncall@company.com
- ANY auth outage → immediate all-hands page
- Downstream impact: ALL services will reject requests

## Health Endpoints
- `/actuator/health` — overall health
- `/actuator/metrics/jvm.memory.used` — heap usage
- `/actuator/metrics/jvm.gc.pause` — GC pressure
