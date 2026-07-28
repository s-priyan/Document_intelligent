# Chat With Your Docs — Backend

FastAPI backend for the document-intelligence RAG application. This slice covers
document ingestion (FR-1 upload, FR-2 validation, FR-3 Docling parsing) plus the
knowledge-index management the later chat flow builds on.

## Stack

- FastAPI + Pydantic v2
- Docling (document parsing)
- LangChain (recursive chunking) + Chroma (vector store)
- HuggingFace embeddings — `BAAI/bge-small-en-v1.5`
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
cd backend
uv sync            # creates .venv and installs dependencies
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

Interactive API docs: http://localhost:8000/docs

## Storage layout

Each knowledge index owns a flat folder under `storage/`:

```
storage/{index_id}/
    meta.json      # index metadata (id, name, created_at)
    raw/           # original uploaded files
    parsed/        # Docling-extracted markdown
    chroma/        # persisted Chroma vector store (embeddings + metadata)
```

## Ingestion pipeline

A bulk upload runs each file through: validate (FR-2) → store raw (FR-1) →
Docling parse to markdown (FR-3) → recursive chunking (FR-4) → embed with
`BAAI/bge-small-en-v1.5` and index into the per-index Chroma store (FR-5). Each
chunk carries `{index_id, source, chunk_index, start_index}` metadata for
citations. The first upload lazily loads the embedding model (a one-off delay).

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/api/health` | Service health (FR-21) |
| POST | `/api/knowledge-indexes` | Create a named knowledge index |
| GET  | `/api/knowledge-indexes` | List indexes (select one to chat) |
| GET  | `/api/knowledge-indexes/{index_id}` | Get one index |
| POST | `/api/knowledge-indexes/{index_id}/documents` | Bulk upload → validate → parse (FR-1/2/3) |

### Bulk upload example

```bash
curl -X POST http://localhost:8000/api/knowledge-indexes/my-docs/documents \
  -F "files=@report.pdf" \
  -F "files=@notes.txt"
```

## Tests

```bash
uv run pytest
```
