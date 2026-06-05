# Ghostrace API Reference

Base URL: `http://localhost:8000`

All authenticated endpoints require a **Bearer token** in the `Authorization` header.

---

## Authentication — `/api/auth`

### `POST /api/auth/signup`
Register a new user. Creates a default project and API key.

**Body:**
```json
{ "email": "user@example.com", "password": "SecurePass1!" }
```
**Response:** `201 Created` → `UserResponse`

---

### `POST /api/auth/token`
Login and receive a JWT access token.

**Body (form-data):** `username`, `password`

**Response:**
```json
{ "access_token": "...", "token_type": "bearer", "expires_in": 86400 }
```
**Rate limiting:** Returns `429` after 10 failed attempts from the same IP.

---

### `POST /api/auth/refresh`
Exchange a refresh token for a new access token.

**Body:** `{ "refresh_token": "..." }`

---

### `GET /api/auth/me`
Get current authenticated user profile. **Requires auth.**

**Response:** `UserResponse`

---

## Projects — `/api/projects`

### `GET /api/projects/`
List all projects for the current user.

### `POST /api/projects/`
Create a new project.
**Body:** `{ "name": "my-project" }`

### `DELETE /api/projects/{project_id}`
Delete a project and all its sessions.

### `GET /api/projects/{project_id}/keys`
List API keys for a project.

### `POST /api/projects/{project_id}/keys`
Create a new API key.
**Body:** `{ "name": "Production Key" }`

### `DELETE /api/projects/{project_id}/keys/{key_id}`
Delete an API key.

---

## Sessions — `/api/sessions`

### `GET /api/sessions/`
List sessions for a project.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `project_id` | string | required | Project ID |
| `skip` | int | 0 | Pagination offset |
| `limit` | int | 50 | Max results (1–200) |
| `search` | string | — | Filter by session name |
| `tag_key` | string | — | Filter by tag key |
| `tag_value` | string | — | Filter by tag value |

### `GET /api/sessions/{session_id}`
Get a single session with events and loop detection.

### `DELETE /api/sessions/{session_id}`
Delete a session permanently.

### `GET /api/sessions/{session_id}/export`
Download session as a JSON file.

---

## Trace Events — `/api/sessions/{session_id}/events`

### `GET /api/sessions/{session_id}/events/count`
Total event count (optional `event_type` filter).

### `GET /api/sessions/{session_id}/events/tokens`
Aggregated token usage and cost.

### `GET /api/sessions/{session_id}/events/errors`
All error events in the session.

### `GET /api/sessions/{session_id}/events/latency`
Latency percentiles: p50, p95, p99.

### `GET /api/sessions/{session_id}/events/models`
Per-model call count, tokens, and cost breakdown.

---

## Analytics — `/api/projects/{project_id}/analytics`

### `GET /api/projects/{project_id}/analytics`

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `period_days` | int | 30 | Look-back window (7–365) |

**Response includes:** daily metrics, weekly trends, top models by cost, error rate over time, average session duration.

---

## Health — `/health`

### `GET /health/live`
Liveness probe — always returns `200` if process is running.

### `GET /health/ready`
Readiness probe — checks database connectivity.

---

## SDK Ingestion — `/v1`

### `POST /v1/ingest`
Ingest a session payload from the Ghostrace SDK.

**Header:** `Authorization: Bearer <api_key>`
