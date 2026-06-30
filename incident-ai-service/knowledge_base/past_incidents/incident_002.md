# Incident INC-2024-0203 — Auth Service OutOfMemoryError

**Date:** 2024-02-03
**Service:** auth-service
**Severity:** CRITICAL
**Duration:** 1 hour 45 minutes
**Status:** RESOLVED

## Summary
Authentication service crashed with OutOfMemoryError causing all services to reject login requests. The root cause was a JWT token cache growing unboundedly due to a missing eviction policy.

## Error Observed
```
java.lang.OutOfMemoryError: Java heap space
Exception in thread "pool-3-thread-1" java.lang.OutOfMemoryError: GC overhead limit exceeded
Heap usage: 98% — GC is spending >98% of time reclaiming <2% memory
```

## Root Cause
JWT token validation cache (ConcurrentHashMap) had no eviction policy and no TTL. Each unique token was cached indefinitely. After a high-traffic promotional event, the cache accumulated 2.3 million entries and exhausted the 2GB JVM heap.

## Timeline
- 14:00 — Promotional email campaign sent to 500k users
- 14:15 — Login traffic spiked 8x normal
- 14:45 — GC overhead alerts fired
- 15:00 — Service OOM crashed, restarted by Kubernetes
- 15:20 — Cache eviction patch deployed
- 15:45 — Service stable, monitoring confirmed

## Resolution Steps
1. Replaced ConcurrentHashMap cache with Caffeine cache (max 10k entries, TTL 15 min)
2. Increased JVM heap from 2GB to 4GB as temporary buffer
3. Added heap usage alert at 70% to give earlier warning
4. Deployed fix as a rolling update with zero downtime

## Prevention
- All in-memory caches must use Caffeine with explicit size bounds and TTL
- JVM heap dashboards added to all services
- Load testing to include promotional traffic scenarios
