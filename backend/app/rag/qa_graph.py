"""LangGraph RAG pipeline: retrieve context then generate a grounded answer.

The graph (``retrieve -> generate``) is compiled once with an in-memory
checkpointer, so conversation history is retained per ``thread_id`` and reused
as context for follow-up questions (FR-9, FR-10, FR-12). Only the human
question and the assistant answer are persisted per turn; the retrieved context
is injected fresh into a system message each turn and is not stored in history.

A turn can be run to completion (``answer``) or consumed incrementally as
citations and answer tokens (``astream_answer``).
"""

import logging
from collections.abc import AsyncIterator
from typing import Annotated, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import (
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    message_chunk_to_message,
)
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.rag.citations import CitationBuilder
from app.rag.vector_store import VectorStoreService
from app.schemas.query import Citation, CitationsEvent, DeltaEvent, DoneEvent

_SYSTEM_PROMPT = """You answer questions strictly using the context extracted from the user's \
documents, shown below.

Rules:
- Use ONLY the information in the context. Do not rely on prior or outside knowledge.
- If the context does not contain enough information to answer, reply that you cannot answer \
the question based on the available documents.
- Be concise and factual.

Context:
{context}"""

_NO_CONTEXT = "(no relevant context was found)"

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """State threaded through the RAG graph for a single conversation turn."""

    messages: Annotated[list[BaseMessage], add_messages]
    index_id: str
    context: list[Document]
    citations: list[Citation]


class QaGraph:
    """Compile and run the retrieve-then-generate RAG pipeline (FR-9/FR-10/FR-12)."""

    def __init__(
        self,
        vector_store: VectorStoreService,
        citation_builder: CitationBuilder,
        chat_model: ChatOpenAI,
        retrieval_k: int,
    ) -> None:
        self._vector_store = vector_store
        self._citation_builder = citation_builder
        self._chat_model = chat_model
        self._retrieval_k = retrieval_k
        self._graph = self._build()

    def answer(
        self, index_id: str, question: str, thread_id: str
    ) -> tuple[str, list[Citation]]:
        """Run one turn of the pipeline and return the answer text and citations."""
        result = self._graph.invoke(
            self._turn_input(index_id, question),
            config={"configurable": {"thread_id": thread_id}},
        )
        answer = result["messages"][-1].content
        return answer, result.get("citations", [])

    async def astream_answer(
        self, index_id: str, question: str, thread_id: str
    ) -> AsyncIterator[CitationsEvent | DeltaEvent | DoneEvent]:
        """Run one turn, emitting citations first and then the answer token by token.

        The ``updates`` stream mode carries the citations produced by the
        retrieve node, while ``messages`` carries the model's token chunks.
        """
        deltas: list[str] = []
        stream = self._graph.astream(
            self._turn_input(index_id, question),
            config={"configurable": {"thread_id": thread_id}},
            stream_mode=["updates", "messages"],
        )
        async for mode, payload in stream:
            if mode == "updates":
                citations = payload.get("retrieve", {}).get("citations")
                if citations is not None:
                    yield CitationsEvent(citations=citations)
            else:
                chunk, _metadata = payload
                text = chunk.content if isinstance(chunk.content, str) else ""
                if text:
                    deltas.append(text)
                    yield DeltaEvent(text=text)

        yield DoneEvent(answer="".join(deltas))

    @staticmethod
    def _turn_input(index_id: str, question: str) -> dict:
        """Build the graph input for a single conversation turn."""
        return {"messages": [HumanMessage(content=question)], "index_id": index_id}

    def _build(self):
        """Assemble and compile the graph with an in-memory checkpointer.

        The generate node exposes both a blocking and a streaming
        implementation, so the same compiled graph (and therefore the same
        conversation history) serves ``answer`` and ``astream_answer``.
        """
        builder = StateGraph(ChatState)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("generate", RunnableLambda(self._generate, afunc=self._agenerate))
        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "generate")
        builder.add_edge("generate", END)
        return builder.compile(checkpointer=MemorySaver())

    def _retrieve(self, state: ChatState) -> dict:
        """Fetch the most relevant chunks for the latest question (FR-9/FR-11)."""
        index_id = state["index_id"]
        question = state["messages"][-1].content
        logger.info("Retrieving context | index=%s k=%d", index_id, self._retrieval_k)
        documents = self._vector_store.search(index_id, question, self._retrieval_k)
        citations = self._citation_builder.build(documents)
        logger.info(
            "Retrieved %d chunk(s), %d citation(s) | index=%s",
            len(documents),
            len(citations),
            index_id,
        )
        return {"context": documents, "citations": citations}

    def _generate(self, state: ChatState) -> dict:
        """Generate an answer grounded in the retrieved context (FR-10/FR-12)."""
        self._log_generation(state)
        response = self._chat_model.invoke(self._prompt(state))
        logger.info("Answer generated | chars=%d", len(response.content))
        return {"messages": [response]}

    async def _agenerate(self, state: ChatState) -> dict:
        """Stream the grounded answer, persisting the accumulated message.

        Streaming here is what lets LangGraph's ``messages`` mode surface token
        chunks to the caller; only the assembled message enters history.
        """
        self._log_generation(state)
        accumulated: AIMessageChunk | None = None
        async for chunk in self._chat_model.astream(self._prompt(state)):
            accumulated = chunk if accumulated is None else accumulated + chunk

        if accumulated is None:
            logger.warning("Answer stream produced no chunks")
            return {"messages": []}

        logger.info("Answer streamed | chars=%d", len(accumulated.content))
        return {"messages": [message_chunk_to_message(accumulated)]}

    def _log_generation(self, state: ChatState) -> None:
        """Log the model and the amount of context about to be sent to it."""
        logger.info(
            "Generating answer | model=%s context_chunks=%d history_msgs=%d",
            getattr(self._chat_model, "model_name", "unknown"),
            len(state["context"]),
            len(state["messages"]),
        )

    def _prompt(self, state: ChatState) -> list[BaseMessage]:
        """Build the grounding system message followed by the conversation history."""
        system = SystemMessage(content=_SYSTEM_PROMPT.format(context=self._format_context(state)))
        return [system, *state["messages"]]

    @staticmethod
    def _format_context(state: ChatState) -> str:
        """Render retrieved chunks into a numbered, source-labelled context block."""
        documents = state["context"]
        if not documents:
            return _NO_CONTEXT

        blocks = [
            f"[{position}] Source: {document.metadata.get('source', 'unknown')}\n"
            f"{document.page_content}"
            for position, document in enumerate(documents, start=1)
        ]
        return "\n\n".join(blocks)
