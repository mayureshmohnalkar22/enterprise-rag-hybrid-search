# Deployment and Operations

## Environments
The service runs in development, staging and production environments. Development uses local SQLite storage; staging and production use managed PostgreSQL. All environments have separate secrets and isolated databases.

## Deployments
A new release enters staging first. Automated integration tests and a smoke test must pass before production promotion. Production uses rolling deployments with readiness probes. Failed readiness probes prevent traffic from reaching a new instance.

## Rollbacks
If the HTTP error rate exceeds five percent for ten minutes after rollout, the deployment controller restores the last stable image. A rollback must not reverse database migrations that have already committed. Backward-compatible schema migrations are mandatory.

## Observability
The service exports request latency, error rate, throughput and dependency health metrics. Logs use structured JSON and correlation IDs. Distributed tracing propagates a trace identifier between gateway, API and database.

## Secrets
Production credentials are stored in a secret manager and never committed to Git. The deployment process injects secrets at runtime. Credentials rotate every ninety days, with immediate rotation after any suspected disclosure.
