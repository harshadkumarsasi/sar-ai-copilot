"""
RAG pipeline (disabled for free local mode).

This version removes OpenAI embeddings and vector storage
so the app can run fully offline with Ollama.
"""

from typing import List, Dict, Any


class SARRAGPipeline:
    def __init__(self, persist_dir: str = ".chroma"):
        # RAG disabled in free mode
        self.persist_dir = persist_dir

    def ingest_documents(self, raw_docs: List[str], metadata: Dict[str, Any]):
        # No-op in free mode
        pass

    def retrieve_context(self, query: str, k: int = 4) -> str:
        # Return empty context since embeddings are disabled
        return ""