# Incident INC-2024-0808 — Inventory Service Database Deadlock

**Date:** 2024-08-08
**Service:** inventory-service
**Severity:** HIGH
**Duration:** 1 hour 20 minutes
**Status:** RESOLVED

## Summary
Inventory service experienced recurring database deadlocks during a flash sale event, causing order placement to fail intermittently. 15% of checkout attempts returned 500 errors.

## Error Observed
```
ERROR: could not serialize access due to concurrent update
org.springframework.dao.CannotAcquireLockException: could not execute statement; SQL [n/a];
nested exception is org.hibernate.exception.LockAcquisitionException: could not execute statement
Deadlock detected on table 'inventory' between transactions 7823 and 7829
```

## Root Cause
Two concurrent operations were acquiring row-level locks in opposite order:
1. `order-service` → locked `inventory` row, then tried to lock `reservations` row
2. `inventory-service` batch reconciliation → locked `reservations` row, then tried to lock `inventory` row

This classic lock-ordering deadlock caused PostgreSQL to abort one transaction repeatedly.

## Timeline
- 18:00 — Flash sale started, order traffic spiked 5x
- 18:05 — First deadlock errors appeared
- 18:15 — Error rate reached 15%
- 18:30 — Batch reconciliation job suspended
- 18:40 — Deadlocks stopped
- 19:20 — Lock ordering fix deployed, reconciliation re-enabled

## Resolution Steps
1. Standardised lock acquisition order: always lock `inventory` before `reservations`
2. Added explicit `SELECT FOR UPDATE SKIP LOCKED` to batch reconciliation queries
3. Moved batch reconciliation to off-peak window (03:00–05:00)
4. Added retry logic (3 retries with exponential backoff) for deadlock errors

## Prevention
- All DB transactions involving multiple tables reviewed for consistent lock ordering
- Deadlock rate monitoring alert added (threshold: >5 per minute)
- Load testing now includes concurrent write scenarios
