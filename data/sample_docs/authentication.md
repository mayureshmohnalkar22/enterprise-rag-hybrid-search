# Authentication and Authorization

## Token issuance
Clients authenticate with a username and password over TLS. On successful login, the service issues a signed access token valid for fifteen minutes and a refresh token valid for seven days. Access tokens carry a subject identifier, audience, expiry timestamp and role claims.

## Token renewal
The client exchanges a valid refresh token at POST /v1/auth/refresh for a new access token. Refresh token rotation invalidates the previous refresh token after each successful use. Reusing a revoked refresh token triggers a security alert and revokes the entire token family.

## Permission checks
Every protected route verifies the token signature, audience, expiration, and role-based permissions. A user role can view their own data. An admin role can manage accounts. Missing permissions return HTTP 403, while missing or invalid tokens return HTTP 401.

## Session termination
POST /v1/auth/logout revokes the current refresh token. Access tokens expire naturally after fifteen minutes. Password changes invalidate all existing refresh token families.

## OAuth integrations
Third-party integrations use the authorization code flow with PKCE. Redirect URIs must be registered in advance. State values prevent cross-site request forgery and PKCE mitigates intercepted authorization codes.
