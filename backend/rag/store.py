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
        self._indexed = False
        self._knowledge_root: Path | None = None

    def add_documents(self, texts: Iterable[str], metadatas: Iterable[dict] | None = None) -> None:
        ids = [f"doc_{i}" for i, _ in enumerate(texts)]
        embeddings: List[list[float]] = self.embedder.encode(list(texts), convert_to_numpy=False)  # type: ignore[assignment]
        docs_texts = list(texts)
        self.collection.upsert(
            ids=ids,
            documents=docs_texts,
            embeddings=embeddings,
            metadatas=list(metadatas) if metadatas is not None else None,
        )

    def similarity_search(self, query: str, k: int = 3) -> List[dict]:
        try:
            if self.collection.count() == 0:
                return []
        except Exception:
            # count()가 막히면 질의를 시도
            pass

        query_embedding: List[float] = self.embedder.encode([query], convert_to_numpy=False)[0]  # type: ignore[index]
        try:
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        docs: List[dict] = []
        metadatas = result.get("metadatas", [[]])[0] or []
        distances = result.get("distances", [[]])[0] or []
        documents = result.get("documents", [[]])[0] or []
        for meta, dist, text in zip(metadatas, distances, documents):
            docs.append({"metadata": meta, "score": float(dist), "text": text})
        return docs

    def index_from_disk(self, knowledge_root: str | Path) -> None:
        """
        backend/rag/knowledge/ 아래의 문서(.md)들을 찾아 Chroma에 적재.
        문서가 없으면 아무 것도 하지 않고 넘어갑니다.
        """
        root = Path(knowledge_root)
        self._knowledge_root = root

        if self._indexed:
            return

        try:
            if self.collection.count() > 0:
                self._indexed = True
                return
        except Exception:
            # count가 막혀있거나 버전 이슈가 있으면 계속 진행
            pass

        md_files = list(root.rglob("*.md"))
        if not md_files:
            self._indexed = True
            return

        texts: list[str] = []
        metadatas: list[dict] = []
        folder_to_category = {
            "strategies": "strategy",
            "speech_patterns": "speech",
            "situations": "situation",
            "rules": "rule",
        }
        for fp in md_files:
            try:
                text = fp.read_text(encoding="utf-8")
            except Exception:
                continue

            if not text.strip():
                continue

            rel = fp.relative_to(root)
            parts = rel.parts
            category = parts[0] if len(parts) >= 1 else "unknown"
            category = folder_to_category.get(category, category)
            metadatas.append(
                {
                    "category": category,
                    "source": "disk",
                    "file": fp.name,
                }
            )
            texts.append(text)

        if texts:
            self.add_documents(texts=texts, metadatas=metadatas)
        self._indexed = True
