# Data Governance and Retention

## Classification
Information is classified as public, internal, confidential or restricted. Restricted data includes government identifiers and payment credentials. Confidential data includes customer contact information and internal financial forecasts.

## Access controls
All confidential and restricted datasets require role-based access controls and audit logging. Access requests need manager approval and expire after ninety days unless renewed. Quarterly reviews remove unused entitlements.

## Retention
Application logs are retained for thirty days. Security audit logs are retained for one year. Customer account data is deleted within thirty days after an approved deletion request, except where a statutory retention obligation applies.

## Encryption
Data in transit must use TLS 1.2 or newer. Confidential and restricted data at rest uses AES-256 encryption. Encryption keys are managed centrally and rotated annually.

## Incident reporting
Employees report suspected data leaks to the security team within one hour. The security team triages incidents by severity and coordinates containment, investigation, remediation and customer notification when applicable.
