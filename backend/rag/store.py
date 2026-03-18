from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models import Collection
from sentence_transformers import SentenceTransformer


class RAGStore:
    """
    ChromaDB + sentence-transformers 기반 RAG 스토어 스켈레톤.
    """

    def __init__(self, persist_dir: str, embedding_model: str) -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client: ClientAPI = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection: Collection = self.client.get_or_create_collection("ai_mafia_knowledge")
        self.embedder = SentenceTransformer(embedding_model)

    def add_documents(self, texts: Iterable[str], metadatas: Iterable[dict] | None = None) -> None:
        ids = [f"doc_{i}" for i, _ in enumerate(texts)]
        embeddings: List[list[float]] = self.embedder.encode(list(texts), convert_to_numpy=False)  # type: ignore[assignment]
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=list(metadatas) if metadatas is not None else None,
        )

    def similarity_search(self, query: str, k: int = 3) -> List[dict]:
        query_embedding: List[float] = self.embedder.encode([query], convert_to_numpy=False)[0]  # type: ignore[index]
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["metadatas", "distances"],
        )
        docs: List[dict] = []
        for meta, dist in zip(result.get("metadatas", [[]])[0], result.get("distances", [[]])[0]):
            docs.append({"metadata": meta, "score": float(dist)})
        return docs
