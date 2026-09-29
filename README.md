# Procurement Analytics & AI Assistant

A full-stack procurement analytics application built on the **California public procurement dataset**. The project combines a React analytics dashboard, a FastAPI analytics API, and an independent FastAPI AI service that translates natural-language procurement questions into validated MongoDB aggregation pipelines.

The main goal of the project is to demonstrate how traditional procurement analytics and an agentic AI workflow can work together over the same source data.

---

## Highlights

- Interactive analytics for **orders, suppliers, and departments**
- MongoDB Atlas as the analytical data store
- FastAPI backend with reusable aggregation endpoints
- React + TypeScript + Tailwind CSS frontend
- Natural-language → MongoDB query generation
- Intent routing for greetings, project help, out-of-scope requests, and analytics
- LangGraph workflow with validation and automatic query correction
- Grounded answers generated from real MongoDB results
- Persistent conversation history backed by MongoDB
- Independent chats with a conversation sidebar and follow-up context
- Server-Sent Events (SSE) for live workflow progress and streamed answers
- Request ID correlation across the browser, AI API, stored turns, and LangSmith
- Generated MongoDB pipeline available in the UI for transparency

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Tailwind CSS |
| Analytics API | FastAPI, Python |
| AI service | FastAPI, LangChain, LangGraph |
| Database | MongoDB Atlas |
| AI orchestration | LangChain, LangGraph |
| LLM provider | OpenRouter |
| Model | `xiaomi/mimo-v2.5` |
| Streaming | Server-Sent Events (SSE) |
| Data processing | Pandas |

---

## Project Architecture

```mermaid
flowchart LR
    U[React UI] --> API[Analytics API]
    U --> AI[AI Service]
    API --> M[(MongoDB Atlas)]
    AI --> H[(Conversations and messages)]
    H --> G
    AI --> G[LangGraph Agent]
    G --> R{Route request}
    R -->|Greeting / help / out of scope| D[Direct response]
    R -->|Analytical| Q[Generate MongoDB Pipeline]
    Q --> V[Validate Pipeline]
    V -->|Invalid| C[Correct Query]
    C --> V
    V -->|Valid| M
    M --> A[Generate Grounded Answer]
    A --> S[SSE / Chat Response]
    S --> U
```

The analytics pages and the AI assistant use the same `procurement_records` collection, so both traditional dashboards and conversational answers are grounded in the same dataset.

### Important data semantics

- One MongoDB document represents a **procurement line record**
- A reconstructed unique purchase order is identified by `order_key`
- Procurement value is calculated from `total_price`
- Order counts use distinct `order_key` values
- `creation_date` is the primary time field used for analysis
- Helper fields such as `year`, `month`, and `quarter` support efficient time-based queries

---

## Application Pages

### Overview

The Overview page provides a high-level snapshot of procurement activity. It combines key procurement metrics and summary visualizations to help users quickly understand overall purchasing activity.

![Overview page](screenshots/overview.png)

### Orders

The Orders page focuses on **what is being purchased**. It includes order-level KPIs, spending trends, acquisition-type analysis, order-value distribution, filtering, pagination, and detailed order exploration.

![Orders page](screenshots/orders.png)

### Suppliers

The Suppliers page focuses on **who the organization is buying from**. It includes supplier activity, top suppliers by procurement value, average supplier spend, supplier rankings, and spend by procurement category.

![Suppliers page](screenshots/suppliers.png)

### Departments

The Departments page focuses on **which departments are spending the money**. It includes department rankings, procurement value, spending trends, top suppliers, category analysis, and acquisition-type breakdowns.

![Departments page](screenshots/departments.png)

### AI Assistant

The AI Assistant allows users to ask procurement questions conversationally instead of manually selecting filters or building reports.

Examples:

- `How many orders were placed in Q2 2014?`
- `Which quarter had the highest procurement spending?`
- `Who were the top 5 suppliers by procurement value in 2014?`
- `Which department spent the most on IT Goods in Q3 2013?`
- Follow-up: `What about IT Services?`

The assistant dynamically generates a MongoDB aggregation pipeline, validates it before execution, queries MongoDB Atlas, and then produces a concise answer grounded in the returned data.

The workflow also supports automatic query correction when validation fails, conversation context for follow-up questions, and SSE streaming so the frontend can display progress and answer text as the workflow runs. Private reasoning and internal graph state are not streamed to the client.

![AI Assistant page](screenshots/ai-assistant.png)

---

## AI Assistant Workflow

At a high level, each user message follows this process:

1. A router classifies the message as a greeting, project-help request, out-of-scope request, or analytical procurement question.
2. Direct-response categories receive an immediate scoped reply and stop without generating or executing a database query.
3. For analytical questions, the LLM receives the procurement schema, business rules, and current conversation context and generates a structured MongoDB aggregation pipeline.
4. A deterministic Python validator checks the pipeline before any database execution.
5. Invalid pipelines are sent through a correction/retry path.
6. Valid pipelines execute against MongoDB Atlas with result and execution safeguards.
7. The returned data is passed to the answer-generation step and streamed back to the frontend.
8. Completed turns are stored in the `conversations` and `messages` MongoDB collections. Reopening a conversation loads its recent context for routing and query generation, including after an API restart.

The validator is intentionally separate from the LLM. It restricts unsupported or unsafe MongoDB behavior and prevents generated queries from being executed blindly.

---

## Selected API Endpoints

The analytics API runs on port `8000`, while the independent AI service runs on
port `8001`.

| Service | Method | Endpoint | Purpose |
| --- | --- | --- | --- |
| Analytics | `GET` | `/api/orders/summary` | Order KPIs and procurement summary |
| Analytics | `GET` | `/api/orders` | Paginated and filterable order explorer |
| Analytics | `GET` | `/api/suppliers/ranking` | Top suppliers by procurement value |
| Analytics | `GET` | `/api/departments/summary` | Department-level procurement KPIs |
| AI | `POST` | `/api/chat` | Standard AI assistant request |
| AI | `POST` | `/api/chat/stream` | Streaming AI workflow using SSE |
| AI | `GET` | `/api/chat/conversations` | Conversation history for the sidebar |
| AI | `GET` | `/api/chat/conversations/{id}` | A conversation and all of its messages |

FastAPI also exposes interactive API documentation at:

```text
Analytics API: http://127.0.0.1:8000/docs
AI service:    http://127.0.0.1:8001/docs
```

---

## Repository Structure

```text
.
├── backend/
│   └── app/
│       ├── database/
│       ├── queries/
│       ├── routers/
│       └── services/
├── ai-service/
│   └── app/
│       ├── ai/
│       │   ├── agent/
│       │   ├── nodes/
│       │   ├── prompts/
│       │   ├── schema/
│       │   └── validators/
│       ├── database/
│       ├── models/
│       ├── routers/
│       └── services/
├── frontend/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── scripts/
└── 
    └── screenshots/
```

---

## Local Setup

### Run with Docker Compose

Docker Compose starts the React frontend, analytics API, and AI service together,
with source mounts and automatic reload enabled for all three services.

First, create the local environment file and fill in your MongoDB and OpenRouter
credentials:

```bash
cp .env.example .env
```

Then build and start the application from the repository root:

```bash
docker compose up --build
```

Open the frontend at `http://localhost:5173`, analytics documentation at
`http://localhost:8000/docs`, and AI service documentation at
`http://localhost:8001/docs`. Stop the services with `Ctrl+C`, or run
`docker compose down` if they were started in detached mode.

In Docker, analytics requests use `VITE_API_URL` (port `8000`) and chat requests
use `VITE_AI_API_URL` (port `8001`). Both values can be overridden in `.env`.

The remaining steps describe the non-Docker local setup.

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd procurement-ai-assistant
```

### 2. Create the Conda environment

```bash
conda create -n procurement-ai-assistant python=3.11
conda activate procurement-ai-assistant
```

### 3. Install service dependencies

From the backend directory:

```bash
cd backend
pip install -r requirements.txt

cd ../ai-service
pip install -r requirements.txt
```

The analytics backend has only API and MongoDB dependencies. LangChain,
LangGraph, and the OpenRouter client are isolated in the AI service.

### 4. Configure environment variables

Create a root `.env` file shared by the Compose services.

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/
MONGODB_DB=procurement_ai_assistant

OPENROUTER_API_KEY=<your-openrouter-api-key>
OPENROUTER_MODEL=xiaomi/mimo-v2.5
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=procurement-ai-assistant
APP_ENV=development

VITE_API_URL=http://localhost:8000
VITE_AI_API_URL=http://localhost:8001
```

Never commit `.env` to source control.

When LangSmith tracing is enabled, every AI prompt creates one LangGraph trace
containing the agent nodes and nested model calls. The browser-generated UUID is
sent as `X-Request-ID`, returned in the response and chat events, stored with the
conversation turn, and attached to the trace as `metadata.request_id`. Use that
field to find the full agent cycle in LangSmith or correlate it with other
observability tools. Invalid or missing incoming request IDs are replaced with a
server-generated UUID.

Each completed agent trace also records `route_category`, `outcome`,
`retry_count`, `has_visualization`, and `environment` metadata. Use these fields
to build LangSmith charts for route volume, failures, retries, latency, and cost.
For route distribution, chart only root traces named
`procurement-agent-request` and group them by `metadata.route_category`.

### 5. Prepare MongoDB Atlas

1. Create a MongoDB Atlas cluster.
2. Create a database user.
3. Allow your development IP address under Network Access.
4. Add the Atlas connection string to `MONGODB_URI`.
5. Ensure the application uses the `procurement_records` collection.

After configuring MongoDB, run `python scripts/create_indexes.py` once. Alongside
the analytics indexes, it creates the conversation/message indexes used by chat
history.

### 6. Prepare and load the procurement data

Place the source CSV in the project's raw data directory:
- and here is the link of the data : 
- https://www.kaggle.com/datasets/sohier/large-purchases-by-the-state-of-ca
- put the downloaded data into data/raw directory 


Run the repository's cleaning/preprocessing script to create the processed dataset, then import it into MongoDB Atlas using the ingestion script.

Typical workflow:

```bash
python scripts/clean_data.py
python scripts/import_to_mongodb.py
```

The preprocessing stage normalizes column names, converts dates and numeric values, creates `order_key`, and derives helper time fields such as `year`, `month`, and `quarter`.

If your Atlas collection has already been populated, this step can be skipped.

### 7. Run the backend

From `backend/`:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### 8. Run the AI service

From `ai-service/`, in a second terminal:

```bash
uvicorn app.main:app --reload --port 8001
```

AI service documentation:

```text
http://127.0.0.1:8001/docs
```

### 9. Run the frontend

In a third terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server normally runs at:

```text
http://localhost:5173
```

The frontend consumes the analytics and AI APIs, renders dashboard views,
manages the conversation ID, and displays streamed AI responses and generated
MongoDB pipelines.

---

## AI Verification

The AI workflow was tested incrementally before frontend integration, including:

- structured MongoDB query generation
- procurement-specific query semantics
- safety validation
- invalid-query correction and retry
- execution against the real Atlas collection
- grounded answer generation
- follow-up conversation understanding
- thread isolation and memory
- FastAPI chat requests
- SSE streaming, keep-alives, error handling, and client disconnect cleanup

The generated queries can also be compared against the manually implemented analytics endpoints to verify that both approaches return consistent procurement results.

---

## Dataset

This project uses the **Large Purchases by the State of California** public procurement dataset. The source contains purchase-order and line-level procurement information including departments, suppliers, acquisition types, items, prices, quantities, and UNSPSC classification data.

---

## Notes

- The application uses USD because the source data represents California public procurement.
- Conversation memory currently depends on the configured LangGraph checkpointer. If an in-memory checkpointer is used, conversations are reset when the AI service restarts.
- AI-generated answers should remain grounded in database results. The generated MongoDB pipeline is exposed in the UI to make the analytical process easier to inspect.

---
