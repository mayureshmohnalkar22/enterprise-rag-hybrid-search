# API Reference

## Request conventions
The REST API uses JSON and HTTPS. Write requests should include a request idempotency key. Clients provide the X-Request-ID header to make support logs searchable. Pagination uses page_size and cursor query parameters.

## Rate limiting
Each API key is limited to 120 requests per minute. HTTP 429 indicates throttling. The Retry-After response header tells clients how long to wait. Clients should implement exponential backoff with jitter when retrying.

## GET /v1/items
GET /v1/items retrieves the caller's items. The default page size is twenty and the maximum page size is one hundred. Use the next_cursor field to retrieve additional pages.

## POST /v1/items
POST /v1/items creates an item. The request must provide a unique external_id and a nonempty name. A duplicate external_id returns HTTP 409. Validation failures return HTTP 422.

## Errors
HTTP 400 means malformed request syntax, HTTP 401 means unauthenticated, HTTP 403 means forbidden, HTTP 404 means missing resource, HTTP 409 means conflict, and HTTP 503 means temporarily unavailable.
