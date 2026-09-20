"""Verifies the real LangGraph wiring streams tokens and keeps history.

Uses a fake chat model so the graph, its checkpointer and the ``messages``
stream mode are exercised for real without calling OpenAI.
"""

import asyncio

from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.rag.qa_graph import QaGraph
from app.schemas.query import Citation


class StubVectorStore:
    """Return one fixed chunk for any search."""

    def search(self, index_id: str, question: str, k: int) -> list[Document]:
        return [Document(page_content="the sky is blue", metadata={"source": "a.txt"})]


class StubCitationBuilder:
    """Map any documents to a single citation."""

    def build(self, documents: list[Document]) -> list[Citation]:
        return [Citation(source="a.txt")]


def build_graph(*answers: str) -> QaGraph:
    """Build a graph whose model replies with ``answers`` in order."""
    model = GenericFakeChatModel(messages=iter([AIMessage(content=a) for a in answers]))
    return QaGraph(StubVectorStore(), StubCitationBuilder(), model, retrieval_k=2)


async def collect(graph: QaGraph, question: str, thread_id: str) -> list:
    """Drain the streaming turn into a list of events."""
    return [event async for event in graph.astream_answer("docs", question, thread_id)]


def test_astream_answer_streams_tokens_and_retains_history() -> None:
    graph = build_graph("the sky is blue", "still blue")

    events = asyncio.run(collect(graph, "colour?", "t1"))

    names = [type(event).__name__ for event in events]
    assert names[0] == "CitationsEvent"
    assert names[-1] == "DoneEvent"
    assert names.count("DeltaEvent") > 1
    # More than one delta proves tokens are surfaced as produced, not in one lump.

    deltas = "".join(event.text for event in events if type(event).__name__ == "DeltaEvent")
    assert deltas == events[-1].answer == "the sky is blue"

    # The streamed answer is persisted, so the follow-up turn sees the history.
    follow_up = asyncio.run(collect(graph, "still?", "t1"))
    assert follow_up[-1].answer == "still blue"

    state = graph._graph.get_state({"configurable": {"thread_id": "t1"}})
    contents = [message.content for message in state.values["messages"]]
    assert contents == ["colour?", "the sky is blue", "still?", "still blue"]


def test_answer_still_runs_the_blocking_path() -> None:
    answer, citations = build_graph("the sky is blue").answer("docs", "colour?", "t2")

    assert answer == "the sky is blue"
    assert citations == [Citation(source="a.txt")]
