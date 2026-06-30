# Incident Report: Database Deadlock — inventory-service

**Date:** 2026-05-14  
**Severity:** HIGH  
**Duration:** 47 minutes  
**Service:** inventory-service  
**Environment:** PRODUCTION

## Summary
A database deadlock cascade caused 23% of order placements to fail during peak traffic.
The root cause was concurrent stock reservation transactions acquiring row locks in inconsistent order.

## Error Message
```
Database deadlock detected on orders table
SQLSTATE[40P01]: Deadlock found when trying to get lock; try restarting transaction
Lock wait timeout exceeded; try restarting transaction
```

## Timeline
- **14:32** — First deadlock alerts fire. Error rate climbs to 8%.
- **14:35** — On-call engineer paged. PostgreSQL shows 14 waiting lock sessions.
- **14:41** — Identified two concurrent flows acquiring locks on `inventory` and `reservations` tables in opposite order.
- **14:48** — Killed 14 blocking DB sessions manually. Error rate drops to 2%.
- **14:55** — Code fix deployed: standardised lock acquisition order (inventory row first, reservation row second).
- **15:19** — Error rate back to baseline 0.02%. Incident closed.

## Root Cause
Two concurrent code paths acquired row-level locks in opposite order:
- Flow A: `LOCK inventory row → LOCK reservation row`
- Flow B: `LOCK reservation row → LOCK inventory row`

When both ran simultaneously, each held the first lock and waited for the second — classic deadlock.

## Impact
- 23% of order placement requests failed with 500 error
- Approximately 1,847 orders lost (recovered via retry queue)
- No data corruption — all transactions rolled back cleanly

## Resolution
1. Identified conflicting lock order using `pg_locks` and `pg_stat_activity`
2. Killed blocking sessions using `pg_terminate_backend(pid)`
3. Standardised lock order: always acquire `inventory` lock before `reservation` lock
4. Added retry logic with exponential backoff for SQLSTATE 40P01
5. Added `SELECT FOR UPDATE SKIP LOCKED` where exclusive access is not required

## Prevention
- Added PostgreSQL deadlock detection alert at threshold > 3/minute
- Added integration test that simulates concurrent reservation to catch lock order issues
- Added `lock_timeout = 3s` at session level to prevent indefinite waits
- Added DB connection pool metrics to Grafana dashboard
