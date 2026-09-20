"""Tests for the question-answering endpoints, JSON and streaming (FR-8 to FR-12).

A scripted :class:`~tests.conftest.FakeQaGraph` stands in for the LangGraph
pipeline so the retrieval and LLM backends are never touched.
"""

import json

from app.core.exceptions import QueryError

STREAM_URL = "/api/knowledge-indexes/docs/query/stream"
QUERY_URL = "/api/knowledge-indexes/docs/query"


def parse_sse(body: str) -> list[tuple[str, dict]]:
    """Parse an SSE response body into ``(event name, payload)`` pairs."""
    events = []
    for frame in body.replace("\r\n", "\n").strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in frame.splitlines() if ": " in line)
        if "data" in fields:
            events.append((fields.get("event", "message"), json.loads(fields["data"])))
    return events


def create_index(client) -> None:
    """Create the index the query tests run against."""
    client.post("/api/knowledge-indexes", json={"name": "Docs"})


def test_query_returns_answer_with_citations(client, qa_graph) -> None:
    create_index(client)

    response = client.post(QUERY_URL, json={"question": "hi?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Hello world"
    assert body["citations"][0]["source"] == "a.txt"
    assert body["session_id"]


def test_query_stream_emits_session_citations_deltas_then_done(client) -> None:
    create_index(client)

    response = client.post(STREAM_URL, json={"question": "hi?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_sse(response.text)
    assert [name for name, _ in events] == [
        "session",
        "citations",
        "delta",
        "delta",
        "done",
    ]

    payloads = dict(events[:2])
    assert payloads["session"]["session_id"]
    assert payloads["citations"]["citations"][0]["source"] == "a.txt"

    deltas = "".join(payload["text"] for name, payload in events if name == "delta")
    assert deltas == events[-1][1]["answer"] == "Hello world"


def test_query_stream_reuses_the_supplied_session_id(client, qa_graph) -> None:
    create_index(client)

    response = client.post(STREAM_URL, json={"question": "hi?", "session_id": "thread-1"})

    events = dict(parse_sse(response.text))
    assert events["session"]["session_id"] == "thread-1"
    # The session id doubles as the LangGraph thread id for multi-turn context.
    assert qa_graph.calls == [("docs", "hi?", "thread-1")]


def test_query_stream_on_missing_index_fails_before_streaming(client) -> None:
    response = client.post(
        "/api/knowledge-indexes/absent/query/stream", json={"question": "hi?"}
    )

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


def test_query_stream_reports_mid_stream_failure_as_an_error_event(client, qa_graph) -> None:
    create_index(client)
    qa_graph.failure = QueryError("backend exploded")

    response = client.post(STREAM_URL, json={"question": "hi?"})

    assert response.status_code == 200
    events = parse_sse(response.text)
    assert [name for name, _ in events] == ["session", "citations", "error"]
    assert events[-1][1]["detail"] == "backend exploded"


def test_query_rejects_an_empty_question(client) -> None:
    create_index(client)

    assert client.post(QUERY_URL, json={"question": ""}).status_code == 422
    assert client.post(STREAM_URL, json={"question": ""}).status_code == 422
