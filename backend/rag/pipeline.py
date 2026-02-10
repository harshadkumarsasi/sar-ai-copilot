

"""
RAG (Retrieval-Augmented Generation) pipeline for SAR AI Copilot.

Responsibilities:
- Load and index regulatory / SAR reference documents
- Retrieve relevant context for a given SAR case
- Augment LLM input with grounded, auditable references

This pipeline is intentionally simple and hackathon-safe.
"""

from typing import List, Dict, Any
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document


class SARRAGPipeline:
    def __init__(self, persist_dir: str = ".chroma"):
        """
        Initialize the vector store and embedding model.
        """
        self.persist_dir = persist_dir

        self.embeddings = OpenAIEmbeddings()

        self.vectorstore = Chroma(
            collection_name="sar_knowledge_base",
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
        )

    def ingest_documents(self, raw_docs: List[str], metadata: Dict[str, Any]):
        """
        Ingest regulatory or SAR reference documents into the vector store.

        raw_docs: list of raw text documents
        metadata: metadata to attach to each chunk (e.g., source="FATF")
        """
        documents: List[Document] = []

        for text in raw_docs:
            chunks = self.text_splitter.split_text(text)
            for chunk in chunks:
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata=metadata,
                    )
                )

        self.vectorstore.add_documents(documents)
        self.vectorstore.persist()

    def retrieve_context(self, query: str, k: int = 4) -> str:
        """
        Retrieve top-k relevant chunks for a given query.
        """
        results = self.vectorstore.similarity_search(query, k=k)

        if not results:
            return ""

        context_blocks = []
        for doc in results:
            source = doc.metadata.get("source", "unknown")
            context_blocks.append(
                f"[SOURCE: {source}]\n{doc.page_content}"
            )

        return "\n\n".join(context_blocks)