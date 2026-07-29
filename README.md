# Chat With Your Docs

A full-stack Retrieval-Augmented Generation (RAG) application: upload a collection of
documents, build a per-collection knowledge index, and ask grounded, citation-backed
questions in a conversational UI.

- **Backend:** FastAPI · Python · LangGraph · OpenAI · Docling · Chroma
- **Frontend:** Next.js · React · TypeScript · Tailwind CSS
- **Repo layout:** two top-level folders — `[backend/](./backend)` and `[frontend/](./frontend)`

---

## a. Quick setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package/env manager), Python 3.11+, Node.js 18+
- An OpenAI API key

### Backend

Dependencies are managed with **uv** (`pyproject.toml` + `uv.lock`).

```bash
cd backend
uv sync                         # creates .venv and installs pinned dependencies

# Configure secrets/settings (do NOT commit real keys)
cp .env.example .env            # then set APP_OPENAI_API_KEY=sk-...

uv run uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local      # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
npm run dev
```

App: `http://localhost:3000`. The backend allows CORS from `:3000` (and `:3001`).

### Usage

1. Name an index → upload documents → **Create Knowledge Index** (validates, stores,
  parses, chunks, embeds).
2. Or pick an existing index from the dropdown.
3. **Talk with document** → chat with grounded answers and expandable citations.

---

## b. Architecture overview

![system overview](https://github.com/s-priyan/Document_intelligent/blob/main/system-overview.png)

---

## c. Productionizing on AWS (scalability & deployment)

The current build favours a simple, self-contained local footprint (filesystem storage,
in-memory sessions, synchronous ingestion). To productionize:


| Concern                | Now (dev)                           | Production target on AWS                                                                                                                       |
| ---------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Compute / API**      | Uvicorn dev server                  | FastAPI on Lambda (or API behind API Gateway); auto-scaling                                                                                    |
| **File storage**       | Local `storage/`                    | **S3** for raw + parsed artifacts (`s3://.../{index_id}/...`)                                                                                  |
| **Ingestion**          | Synchronous in the request          | **Event-driven**: upload → S3 event → **SQS** queue → **Lambda** does parse→chunk→embed; API returns immediately with a job id                 |
| **Vector store**       | On-disk Chroma per index            | Managed vector DB (pgvector on RDS, OpenSearch, or Pinecone) for concurrency & scale                                                           |
| **Sessions / history** | LangGraph `MemorySaver` (in-memory) | **PostgreSQL checkpointer** (LangGraph `PostgresSaver`) + a conversations/messages schema for **multi-session** history (ChatGPT/Claude style) |
| **Config / secrets**   | `.env` files                        | AWS Secrets Manager / SSM Parameter Store; no secrets in the repo                                                                              |
| **Streaming**          | Full-response JSON                  | SSE/WebSocket token streaming from the LLM                                                                                                     |
| **Observability**      | Standard logging                    | CloudWatch logs/metrics, LLM tracing (LangSmith)                                                                                               |
| **Access control**     | None (v1)                           | Cognito auth + RBAC; per-user/tenant index isolation                                                                                           |
| **Delivery**           | `next dev`                          | Frontend on Vercel or S3+CloudFront; CI/CD via GitHub Actions                                                          |


Target flow (event-driven ingestion):

```
Client → API (presigned PUT) → S3 ──(ObjectCreated)──► SQS ──► Lambda/Worker
      → parse (Docling) → chunk → embed → upsert to vector DB → update job status (DDB/RDS)
```

This decouples slow ingestion from request latency, absorbs bursts, and scales
each stage independently.

---

## d. RAG / LLM approach & decisions

**Pipeline.** Ingestion: *validate → Docling parse to markdown → recursive chunking →
embed → persist to Chroma*. Query (LangGraph `retrieve → generate`): embed the question,
similarity-search top-`k` chunks, inject them into a grounded system prompt, generate,
and build citations.


| Component         | Options considered                                  | Final choice                                  | Why                                                                                  |
| ----------------- | --------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------ |
| **LLM**           | OpenAI GPT, Anthropic Claude        | **OpenAI GPT** (`openai_model`, configurable) | Strong grounded-QA quality, simple API, easy to swap via config                      |
| **Embeddings**    | OpenAI `text-embedding-3`, `BAAI/bge-small-en-v1.5` | `bge-small-en-v1.5` (HuggingFace open source) | Strong quality-for-size, runs locally, no per-embedding API cost/keys                |
| **Vector DB**     | FAISS, Chroma, pgvector                             | **Chroma** (on-disk, per-index collection)    | Zero-infra persistence, simple isolation per index; clean upgrade path to pgvector   |
| **Orchestration** | Raw calls, LangChain chains, **LangGraph**          | **LangGraph**                                 | Explicit stateful graph + checkpointer gives clean multi-turn memory per `thread_id` |
| **Parser**        | PyPDF/textract, **Docling**                         | **Docling**                                   | Preserves structure (headings/tables) as markdown → better chunks & citations        |


- **Chunking:** `RecursiveCharacterTextSplitter`, size **5000** / overlap **150**, with
`add_start_index` so each chunk keeps its character offset (used for citations).
- **Context management:** retrieved chunks are injected fresh into a *system* message each
turn; only human/assistant turns are persisted in history (retrieved context is not),
keeping the window lean and avoiding stale-context drift.
- **Prompt & guardrails:** the system prompt instructs the model to answer **only** from
the provided context and to **explicitly decline** when context is insufficient
(FR-12 no-hallucination). Grounding is enforced via the prompt rather than sampling
tweaks, so newer models that reject non-default `temperature` still work.
- **Citations (quality/trust):** one citation per distinct source+section, where section
is the nearest markdown heading at/above the chunk offset — derived at query time from
the parsed markdown, so no ingestion changes are needed.
- **Observability:** structured logging across ingestion and query stages (chunk counts,
retrieval `k`, citation counts, answer size). LangSmith tracing is a natural next step.

---

## e. Key technical decisions

- **Two-folder layout** (`backend`/`frontend`) with strong internal module boundaries and
dependency injection (`api/deps.py`) for testability and clear separation of concerns.
- **Index-scoped isolation:** each knowledge index is a self-contained folder
(`raw/`, `parsed/`, `chroma/`, `meta.json`) — simple, debuggable, and portable.
- **Typed contracts end to end:** Pydantic schemas on the backend mirrored by TypeScript
types on the frontend; the API client normalizes errors into a single `ApiError`.
- **Session id = LangGraph thread id:** the backend issues a `session_id` on the first
turn; the frontend reuses it so multi-turn context "just works" without a DB (v1).
- **Lazy, cached heavy resources** (embeddings, LLM client, Docling converter) via
`lru_cache` to keep startup fast and avoid reloading weights.
- **Per-file resilience:** bulk upload reports success/failure per document without
aborting the batch.

---

## f. Engineering standards

**Followed**

- Clean architecture, SOLID, single-responsibility modules; DI over globals.
- Explicit type annotations (Python) and strict TypeScript; PEP 8 / typed models.
- Descriptive docblocks (incl. `:raises`), early-return style, minimal duplication.
- Meaningful HTTP status codes and centralized error mapping (`AppError`).
- Secrets via environment/`.env` (kept out of source); CORS locked to known origins.
- Frontend accessibility basics (labels, roles, keyboard handling) and clear UX states.

**Skipped / deferred (scope)**

- Automated test suite (unit/integration) — a `tests/` folder is scaffolded but coverage
is minimal for the exercise.
- Auth/RBAC, rate limiting, and multi-tenant isolation.
- Streaming responses and persistent multi-session history.
- CI/CD, containerization, and IaC.

---

## g. How AI tools were used

- Used an AI coding assistant to scaffold the Next.js frontend, generate the typed API client, hooks, and themed components, and to align frontend contracts with backend Pydantic schemas.
- All AI output was reviewed, adjusted for the project's standards, and **verified by
building/running** (production build + dev boot) before acceptance — AI accelerated
boilerplate and iteration, not correctness decisions.
- System overview digram genaration 

---

## h. What I'd do with more time

- **Decouple ingestion** into an event-driven job queue (S3 → SQS → worker) with a job
status API and progress UI, instead of synchronous upload.
- **Streaming responses** (SSE/WebSocket) for token-by-token answers.
- **Multiple persistent sessions** (Postgres-backed) with a conversation sidebar
(ChatGPT/Claude style), including rename/delete and cross-restart resume.
- **Logging/observability**: structured JSON logs, request tracing, and LLM tracing
(LangSmith), plus evaluation harness for retrieval/answer quality.
- **RBAC & auth**: user accounts, per-user index ownership, and tenant isolation.
- **Retrieval upgrades**: hybrid search (BM25 + vectors), reranking, and scoped querying
across selected documents.
- **Test coverage**: unit tests for pipeline stages and API contract/integration tests.

