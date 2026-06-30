# Incident INC-2024-0315 — Payment Service DB Connection Pool Exhaustion

**Date:** 2024-03-15
**Service:** payment-service
**Severity:** CRITICAL
**Duration:** 2.5 hours
**Status:** RESOLVED

## Summary
Payment service became unresponsive during month-end batch processing. HikariCP connection pool was exhausted causing all new payment requests to fail with timeout errors.

## Error Observed
```
HikariPool-1 - Connection is not available, request timed out after 30000ms
CRITICAL: Connection pool exhausted - rejecting new connections
```

## Root Cause
Month-end billing triggered a 3x traffic spike. The HikariCP pool was configured with `maximum-pool-size=10` which was insufficient. Long-running analytical queries from the billing batch job held connections open for 45+ seconds, blocking the pool entirely.

## Timeline
- 09:00 — Month-end billing batch job started
- 09:12 — First timeout alerts fired
- 09:15 — Pool utilisation hit 100% (10/10)
- 09:30 — On-call engineer paged
- 10:30 — Pool size increased to 25, service recovered
- 11:30 — Analytical queries moved to read replica

## Resolution Steps
1. Increased `spring.datasource.hikari.maximum-pool-size` from 10 to 25
2. Reduced `spring.datasource.hikari.connection-timeout` to 5000ms for faster fail-fast
3. Moved batch analytics queries to dedicated read-replica database
4. Added HikariCP metrics to Grafana dashboard

## Prevention
- Pool size now auto-tuned based on load testing results
- Batch jobs restricted to off-peak hours (02:00–06:00)
- Connection pool monitoring alert at 80% utilisation
