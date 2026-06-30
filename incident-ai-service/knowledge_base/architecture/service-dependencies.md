# Service Dependencies Architecture

## Service Graph

### Payment Service

- **Dependencies**: Database, Payment Gateway API
- **Dependents**: Order Service, Billing Service
- **Critical**: YES

### Auth Service

- **Dependencies**: LDAP, OAuth Provider, Database
- **Dependents**: All Services (frontend gateway dependency)
- **Critical**: YES

### Order Service

- **Dependencies**: Auth Service, Payment Service, Inventory Service, Database
- **Dependents**: Shipping Service, Analytics Service
- **Critical**: YES

### Inventory Service

- **Dependencies**: Database, Cache
- **Dependents**: Order Service, Admin Portal
- **Critical**: YES

### Notification Service

- **Dependencies**: Message Queue, Email Provider, SMS Provider
- **Dependents**: Order Service, Payment Service, Auth Service
- **Critical**: NO

## Inter-Service Communication

- API calls use REST with 30s timeout
- Async events via Kafka message bus
- Database queries use connection pooling

## Failure Modes

- Auth Service Down: All services affected (block at gateway)
- Payment Service Down: Order placement fails
- Database Down: All dependent services fail
