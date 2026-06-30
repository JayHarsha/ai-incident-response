# Inventory Service Runbook

## Service Overview
The inventory-service manages stock levels, reservations, and availability across all warehouses.
It is a critical dependency for order-service (checks stock before accepting orders) and notification-service (low-stock alerts).

## Common Incidents

### Database Deadlock on Orders/Inventory Tables
**Symptoms:** `Database deadlock detected`, `Lock wait timeout exceeded`, high DB CPU, order failures
**Root Cause:** Concurrent transactions updating the same inventory rows in inconsistent lock order
**Resolution:**
1. Check active DB locks: `SELECT * FROM pg_locks WHERE granted = false;`
2. Identify blocking query: `SELECT pid, query, wait_event FROM pg_stat_activity WHERE wait_event_type = 'Lock';`
3. Kill blocking session if safe: `SELECT pg_terminate_backend(<pid>);`
4. Review application code — ensure consistent lock ordering (always lock lower ID first)
5. Add `NOWAIT` or `SKIP LOCKED` to SELECT FOR UPDATE queries where appropriate
6. Add retry logic with exponential backoff for deadlock errors (SQLSTATE 40P01)

### Stock Count Drift
**Symptoms:** Negative stock values, overselling, `InventoryValidationException`
**Root Cause:** Race condition in reservation flow — read-modify-write without atomic update
**Resolution:**
1. Switch stock decrement to single atomic SQL: `UPDATE inventory SET stock = stock - ? WHERE id = ? AND stock >= ?`
2. Check rows affected — if 0, stock was insufficient (optimistic locking)
3. Reconcile stock counts against order history for affected SKUs
4. Re-run scheduled stock reconciliation job

### Connection Pool Exhaustion
**Symptoms:** `HikariCP connection pool exhausted`, `Connection is not available, request timed out`
**Root Cause:** Slow queries holding connections; deadlocks causing long transactions
**Resolution:**
1. Check pool stats: search logs for `HikariPool` metrics
2. Identify long-running transactions in PostgreSQL
3. Kill stuck connections
4. Temporarily increase pool size (max 20) as emergency measure
5. Root fix: add query timeouts (`spring.datasource.hikari.connection-timeout=5000`)

## Dependencies
- **Upstream (calls):** PostgreSQL, Redis (cache), order-service
- **Downstream (called by):** order-service, notification-service, API gateway
- **On-Call:** inventory-team@company.com | PagerDuty: inventory-oncall
- **SLA:** P1 response < 5 minutes

## Monitoring
- Dashboard: grafana/inventory-service
- Key metrics: `inventory_reservation_errors_total`, `db_connection_pool_active`, `stock_update_latency_p99`
- Alert threshold: error rate > 1% for 2 minutes → PagerDuty
