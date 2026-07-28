"""LangGraph RAG pipeline: retrieve context then generate a grounded answer.

The graph (``retrieve -> generate``) is compiled once with an in-memory
checkpointer, so conversation history is retained per ``thread_id`` and reused
as context for follow-up questions (FR-9, FR-10, FR-12). Only the human
question and the assistant answer are persisted per turn; the retrieved context
is injected fresh into a system message each turn and is not stored in history.
"""

import logging
from typing import Annotated, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.rag.citations import CitationBuilder
from app.rag.vector_store import VectorStoreService
from app.schemas.query import Citation

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
            {"messages": [HumanMessage(content=question)], "index_id": index_id},
            config={"configurable": {"thread_id": thread_id}},
        )
        answer = result["messages"][-1].content
        return answer, result.get("citations", [])

    def _build(self):
        """Assemble and compile the graph with an in-memory checkpointer."""
        builder = StateGraph(ChatState)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("generate", self._generate)
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
        model = getattr(self._chat_model, "model_name", "unknown")
        logger.info(
            "Generating answer | model=%s context_chunks=%d history_msgs=%d",
            model,
            len(state["context"]),
            len(state["messages"]),
        )
        system = SystemMessage(content=_SYSTEM_PROMPT.format(context=self._format_context(state)))
        response = self._chat_model.invoke([system, *state["messages"]])
        logger.info("Answer generated | chars=%d", len(response.content))
        return {"messages": [response]}

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
