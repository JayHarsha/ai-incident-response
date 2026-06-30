# Notification Service Runbook

## Service Overview
The notification-service sends emails, SMS, and push notifications triggered by events from order-service and inventory-service via Kafka.
It is stateless — no database. All state is in Kafka consumer offsets and the external provider APIs (SendGrid, Twilio).

## Common Incidents

### Kafka Consumer Lag — Notifications Delayed
**Symptoms:** Consumer lag growing in `notification-events` topic, users not receiving emails
**Root Cause:** Notification-service processing too slowly, or external provider rate-limiting
**Resolution:**
1. Check consumer lag: Kafka-UI → Topics → notification-events → Consumer Groups
2. If lag > 10k messages, scale horizontally (add consumer instances)
3. Check SendGrid/Twilio API response times in logs
4. If external provider is throttling: implement exponential backoff, not retry-immediately
5. Mark non-critical notifications (marketing) as lower priority — skip or batch them
6. Dead-letter queue: failed notifications after 3 retries go to `notification-dlq` topic for manual review

### SendGrid 429 Rate Limit
**Symptoms:** `HTTP 429 Too Many Requests` in logs, email notifications failing
**Root Cause:** Burst of order events exceeding SendGrid plan limit
**Resolution:**
1. Immediately: switch to queued mode — buffer notifications and send at rate limit pace
2. Check SendGrid dashboard for current quota usage
3. Enable SendGrid IP warmup if this is a new IP
4. Long-term: implement token bucket rate limiter in notification-service
5. Upgrade SendGrid plan if burst is expected regularly

### Duplicate Notifications
**Symptoms:** Users receive same email/SMS 2-3 times
**Root Cause:** Kafka consumer rebalance causing message reprocessing without idempotency check
**Resolution:**
1. Add idempotency key to each notification: `hash(eventId + recipientId + templateId)`
2. Store sent notification IDs in Redis with 24h TTL before sending
3. Check before send: if key exists in Redis, skip
4. Ensure Kafka consumer commits offsets AFTER successful send, not before

### OOM / Memory Leak
**Symptoms:** `OutOfMemoryError`, pod restarts, heap > 90%
**Root Cause:** JWT token cache unbounded growth (if using auth), or large email template rendering
**Resolution:**
1. Check heap: look for `GC overhead limit exceeded` or `Java heap space` in logs
2. Set explicit heap: `-Xmx512m` for this service (it should be small)
3. Add cache eviction: Caffeine cache with max size 10k and 1h TTL
4. Profile with async-profiler if leak persists

## Dependencies
- **Upstream (consumes from):** Kafka topics: order-events, inventory-alerts
- **External APIs:** SendGrid (email), Twilio (SMS), Firebase (push)
- **On-Call:** platform-team@company.com | PagerDuty: notifications-oncall
- **SLA:** Notifications delivered within 60 seconds of event. P1 response < 15 min.

## Monitoring
- Dashboard: grafana/notification-service
- Key metrics: `notifications_sent_total`, `kafka_consumer_lag`, `provider_api_latency_p95`
- Alert threshold: consumer lag > 5000 for 5 minutes → PagerDuty
