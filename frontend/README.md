# Chat With Your Docs — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS frontend for the "Chat With Your Docs"
RAG application. It covers the chat experience (FR-14 → FR-18) plus the document
management flow needed to build a knowledge index.

## Flow

1. **Document Manager** (`/`) — name a knowledge index, stage documents (drag & drop
   or browse), remove staged files client-side, then **Create Knowledge Index**. This
   creates the index and uploads the files (stored raw, parsed with Docling, chunked
   and embedded into Chroma) in one action, showing a per-file ingestion summary.
2. **Chat** (`/chat/[indexId]`) — reached via **Talk with document**. A `session_id`
   is issued by the backend on the first question and reused as the LangGraph
   `thread_id` for all follow-ups. Answers show expandable source citations. **New
   chat** clears the session.

## Tech stack

- Next.js 15 (App Router), React 19, TypeScript
- Tailwind CSS 3 with a Claude-inspired theme (warm cream canvas, terracotta accent)

## Getting started

```bash
npm install
cp .env.example .env.local   # adjust NEXT_PUBLIC_API_BASE_URL if needed
npm run dev
```

The app runs on http://localhost:3000 (the backend allows CORS from this origin).

### Environment

| Variable                   | Default                       | Description                          |
| -------------------------- | ----------------------------- | ------------------------------------ |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api`   | Backend base URL, including `/api`.  |

## Project structure

```
frontend/
├── app/                     # Next.js routes
│   ├── page.tsx             # Document Manager (screen 1)
│   └── chat/[indexId]/      # Chat (screen 2)
├── components/
│   ├── documents/           # upload, staging, create-index flow
│   ├── chat/                # chat panel, thread, bubbles, input, citations
│   └── ui/                  # shared icons
└── lib/                     # API client, types, hooks, validation
```

## Scope notes

- **No streaming (FR-16):** answers render on full response, per current scope.
- **No database:** session state is held client-side; the backend keeps history in
  memory per `thread_id`.
- **Remove documents** is client-side staging only (no backend delete).
- **Citations (FR-17):** the API returns citation *locations* (source/section/index);
  the raw snippet text is not exposed by the backend, so the expanded panel shows
  that location metadata.
```
