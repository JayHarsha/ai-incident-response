# Incident INC-2024-0510 — Order Service Downstream Payment Failure

**Date:** 2024-05-10
**Service:** order-service
**Severity:** HIGH
**Duration:** 45 minutes
**Status:** RESOLVED

## Summary
Order placement failed for all customers. Root cause was payment-service being unreachable due to a bad deployment that misconfigured the service port.

## Error Observed
```
I/O error on POST request for "http://payment-service:8081/api/payments": Connection refused
feign.RetryableException: Connection refused executing POST http://payment-service:8081/api/payments
```

## Root Cause
A deployment of payment-service accidentally changed the container port from 8080 to 8081 without updating the Kubernetes Service selector. Order-service's Feign client was configured to call port 8080, causing connection refused errors.

## Timeline
- 11:00 — payment-service v2.3.1 deployed
- 11:05 — Order placement alerts fired
- 11:15 — Engineer identified port mismatch via kubectl describe
- 11:30 — Rollback to v2.3.0 initiated
- 11:45 — Service restored

## Resolution Steps
1. Rolled back payment-service to v2.3.0
2. Fixed port configuration in Helm chart for v2.3.2
3. Added pre-deployment smoke test that validates all service dependencies respond on expected ports
4. Implemented circuit breaker (Resilience4j) on payment-service calls from order-service

## Prevention
- Deployment smoke tests now mandatory for all services
- Resilience4j circuit breaker protects order-service from payment-service failures
- Kubernetes readiness probes updated to validate correct port
