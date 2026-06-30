# Incident INC-2024-0620 — Notification Service Kafka Consumer Lag

**Date:** 2024-06-20
**Service:** notification-service
**Severity:** MEDIUM
**Duration:** 3 hours
**Status:** RESOLVED

## Summary
Notification service Kafka consumer fell 80,000 messages behind, causing delayed order confirmation emails and SMS alerts. Customers were not receiving notifications for up to 4 hours after placing orders.

## Error Observed
```
Consumer group lag for 'notification-service-group' on topic 'order-events': 80,412 messages
WARN: Consumer poll timeout exceeded — processing 450ms per message vs 50ms target
```

## Root Cause
A new email template feature introduced a synchronous HTTP call to an external template rendering service. This increased per-message processing time from 50ms to 450ms. With a single-partition consumer and 9x slower processing, lag accumulated rapidly.

## Timeline
- 10:00 — notification-service v1.8.0 deployed (new email templates)
- 10:30 — Consumer lag monitoring alert fired at 5,000 messages
- 12:00 — Lag reached 80,000 messages
- 13:00 — Root cause identified (synchronous template call)
- 13:15 — Template caching enabled, processing restored to 60ms/msg
- 14:00 — Lag cleared

## Resolution Steps
1. Added in-memory Caffeine cache for email templates (TTL 10 minutes)
2. Increased consumer partition count from 1 to 6 for parallelism
3. Made template rendering async using CompletableFuture
4. Added consumer lag alert threshold at 1,000 messages (was 5,000)

## Prevention
- All Kafka consumer implementations reviewed for synchronous external calls
- Performance benchmark required: must process <100ms per message in integration tests
- Consumer lag dashboards added to on-call runbook
