# Ghostrace 👻

> High-performance, zero-touch LLM agent observability and tracing framework.

Ghostrace is a complete agent monitoring solution that captures prompts, tokens, costs, tool calls, loop patterns, and errors automatically with zero configuration. It consists of a high-speed asynchronous python SDK, a FastAPI backend using SQLAlchemy/sqlite, and a premium React/Vite web dashboard with HSL dark mode styling.

---

## Key Features

- **Zero-touch Auto-Instrumentation:** Wrap your OpenAI or Anthropic SDK instances in one line of code to capture all LLM calls.
- **Asynchronous Telemetry Ingestion:** Multi-threaded in-memory batching queue that flushes traces in the background without affecting agent latency.
- **Agent Loop Detector:** Detect repetitive patterns, cyclic reasoning loops, and endless recursion in your agents before they consume your budget.
- **Interactive UI Dashboard:** Fully responsive glassmorphism dark-mode interface built with Vanilla CSS variables and lucide icons.
- **Model Usage & Costs:** Real-time tracking of token counts, latency percentiles (p50/p95/p99), and model calls sorted by cost or call volume.

---

## Project Structure

```text
├── backend/             # FastAPI backend with DB models, schemas, and CRUD
├── frontend/            # React + Vite dashboard with SVG trend charts and UI components
├── sdk/                 # Python SDK with decorator tracing and auto-instrumentation
├── API.md               # API documentation for all endpoints
├── CONTRIBUTING.md      # Setup guide and development workflow
├── Makefile             # Convenient dev, test, and lint commands
└── pytest.ini           # Unified testing configuration
```

---

## Quickstart

### 1. Run the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Run the Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to view the dashboard.

### 3. Instrument your Agent SDK

```python
from ghostrace import trace, session

@trace()
async def my_agent_step(question: str):
    # Traces and metrics are captured automatically here
    return "Response"

with session(name="my-agent-run") as s:
    s.tag("environment", "production")
    my_agent_step("What is the speed of gravity?")
```

---

## Architecture Diagram

```mermaid
graph TD
    subgraph SDK [Python Agent App]
        AgentCode[Agent Code] -->|Decorators / Auto-instrument| SDK_Core[Ghostrace SDK]
        SDK_Core -->|Buffer batches| Queue[In-memory Queue]
        Queue -->|Async Worker| Sender[Sender Thread]
    end

    subgraph Backend [FastAPI Server]
        Sender -->|REST JSON Payloads| IngestRouter[/v1/ingest]
        IngestRouter -->|Validate & Rate Limit| DB[(SQLite Database)]
        DashboardRouter[/api/*] -->|Query telemetry| DB
    end

    subgraph UI [React Dashboard]
        DashboardRouter -->|Fetch metrics| WebApp[Vite Dashboard UI]
        WebApp -->|Interactive Charts| User([Developer / Operator])
    end
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
