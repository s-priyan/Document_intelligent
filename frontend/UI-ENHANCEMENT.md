# UI enhancement checklist

- [x] Searchable library cards with index names, document counts, and creation dates.
- [x] Accessible new-index dialog with name, drag/drop upload, validation, and file removal.
- [x] Create-and-chat navigation with in-memory upload progress and per-file failures.
- [x] Index detail route with available metadata and generic starter questions.
- [x] Streaming chat with clickable citations and a responsive source excerpt panel.
- [x] Previous/next source navigation, close control, Escape dismissal, and focus return.
- [x] Dark navy theme, blue actions, keyboard focus styles, reduced-motion support.
- [x] Production compilation and TypeScript validation.
- [x] Live browser checks for library search, modal, index detail, and starter handoff.
- [x] Live streamed answer, source excerpt selection, next navigation, and Escape/focus return.

## Backend boundaries

The API supplies creation time, not last-used or updated time. Search covers index names only.
There is no document-list endpoint. Document filenames, sizes, and chunk counts are shown
only when available from uploads during the current page session; existing indexes show
their document count. Starter questions are generic, not generated from documents.

Citations contain a source, optional section, character offset, and a shortened snippet.
They are deduplicated by source/section, so the UI calls them source excerpts rather than
claiming a complete retrieved-chunk count. Match scores, chunk IDs, full chunk text,
neighboring text, page counts, and Open in document are omitted.

Uploads continue across client-side navigation in the same tab. They are not durable
background jobs; keep the tab open during indexing. Chat is disabled while indexing.
Failed files can be selected again on the chat screen. No backend changes are required.
