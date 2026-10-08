# On-Call Incident Response

## Severity definitions
SEV1 incidents cause complete service outages or confirmed data exposure. SEV2 incidents cause major degradation affecting multiple customers. SEV3 incidents have limited customer impact with an available workaround.

## Paging
SEV1 incidents page the primary and secondary responders immediately. The primary acknowledges within five minutes. An unacknowledged page escalates to the engineering manager after ten minutes.

## Mitigation
The incident commander prioritizes restoring service before investigating root cause. Mitigation options include traffic shifting, feature flag rollback, scaling, and service restart. All actions are recorded in the incident timeline.

## Communications
For SEV1, update the public status page every thirty minutes. For SEV2, post an internal incident update every hour. Send an incident resolution announcement after recovery.

## Postmortems
SEV1 and SEV2 incidents require a blameless postmortem within five business days. The report includes timeline, customer impact, contributing causes, action items, owners and deadlines.
