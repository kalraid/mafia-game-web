from __future__ import annotations

import logging
import math
import re
import uuid
from pathlib import Path
from typing import Iterable, List, Tuple

import chromadb

logger = logging.getLogger("mafia.backend.rag.store")
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

    def add_documents(
        self,
        texts: Iterable[str],
        metadatas: Iterable[dict] | None = None,
        ids: Iterable[str] | None = None,
    ) -> None:
        docs_texts = list(texts)
        if ids is None:
            # runtime 문서가 누적될 수 있도록 id를 유니크하게 생성한다.
            ids = [f"doc_{uuid.uuid4().hex}_{i}" for i in range(len(docs_texts))]
        else:
            ids = list(ids)

        embeddings: List[list[float]] = self.embedder.encode(docs_texts, convert_to_numpy=False)  # type: ignore[assignment]
        self.collection.upsert(
            ids=ids,
            documents=docs_texts,
            embeddings=embeddings,
            metadatas=list(metadatas) if metadatas is not None else None,
        )

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) + 1e-12
        nb = math.sqrt(sum(x * x for x in b)) + 1e-12
        return float(dot / (na * nb))

    @staticmethod
    def _mmr_pick(
        query_emb: List[float],
        candidates: List[dict],
        k: int,
        lambda_mult: float,
    ) -> List[dict]:
        """Maximal Marginal Relevance: 관련성과 후보 간 중복을 함께 고려해 k건 선택."""
        if k <= 0 or not candidates:
            return []
        emb_key = "_emb"
        rel = []
        for c in candidates:
            e = c.get(emb_key)
            if not e:
                rel.append(0.0)
            else:
                rel.append(RAGStore._cosine_sim(query_emb, e))
        selected: List[int] = []
        remaining = set(range(len(candidates)))
        while len(selected) < min(k, len(candidates)) and remaining:
            best_i = None
            best_score = -1e9
            for i in remaining:
                div = 0.0
                if selected:
                    ei = candidates[i].get(emb_key) or []
                    div = max(
                        RAGStore._cosine_sim(ei, candidates[j].get(emb_key) or [])
                        for j in selected
                    )
                mmr = lambda_mult * rel[i] - (1.0 - lambda_mult) * div
                if mmr > best_score:
                    best_score = mmr
                    best_i = i
            if best_i is None:
                break
            selected.append(best_i)
            remaining.discard(best_i)
        return [candidates[i] for i in selected]

    def similarity_search(
        self,
        query: str,
        k: int = 3,
        *,
        where: dict | None = None,
        fetch_k: int | None = None,
        use_mmr: bool = False,
        mmr_lambda: float = 0.5,
    ) -> List[dict]:
        try:
            if self.collection.count() == 0:
                return []
        except Exception as e:
            logger.warning("RAG count() 실패 (query=%r): %s", query, e)

        query_embedding: List[float] = self.embedder.encode([query], convert_to_numpy=False)[0]  # type: ignore[index]
        n_target = max(1, k)
        n_fetch = fetch_k if fetch_k is not None else n_target
        if use_mmr:
            n_fetch = max(n_fetch, n_target * 4, n_target + 4)

        include = ["documents", "metadatas", "distances"]
        if use_mmr:
            include.append("embeddings")

        def _run_query(w: dict | None, n: int) -> List[dict]:
            try:
                kwargs = dict(
                    query_embeddings=[query_embedding],
                    n_results=min(n, max(1, self.collection.count())),
                    include=include,
                )
                if w is not None:
                    kwargs["where"] = w
                result = self.collection.query(**kwargs)
            except Exception as e:
                logger.warning("RAG 검색 실패 (where=%s query=%r): %s", w is not None, query, e)
                return []

            metadatas = result.get("metadatas", [[]])[0] or []
            distances = result.get("distances", [[]])[0] or []
            documents = result.get("documents", [[]])[0] or []
            embeddings = result.get("embeddings", [[]])[0] or []
            docs: List[dict] = []
            for idx, (meta, dist, text) in enumerate(zip(metadatas, distances, documents)):
                row: dict = {"metadata": meta, "score": float(dist), "text": text}
                if use_mmr and idx < len(embeddings) and embeddings[idx] is not None:
                    row["_emb"] = list(embeddings[idx])
                docs.append(row)
            return docs

        docs = _run_query(where, n_fetch)
        if not docs and where is not None:
            docs = _run_query(None, n_fetch)

        if use_mmr and len(docs) > n_target:
            with_emb = [d for d in docs if d.get("_emb")]
            if len(with_emb) >= n_target:
                picked = self._mmr_pick(query_embedding, with_emb, n_target, mmr_lambda)
            else:
                picked = docs[:n_target]
            for p in picked:
                p.pop("_emb", None)
            docs = picked
        else:
            for d in docs:
                d.pop("_emb", None)
            docs = docs[:n_target]

        return docs

    @staticmethod
    def _extract_frontmatter(text: str) -> Tuple[dict, str]:
        """
        md 파일에서 첫 번째 `---` 줄을 기준으로 frontmatter/body를 분리한다.
        frontmatter는 `key: value` 형태의 라인만 metadata로 채택한다.

        frontmatter가 없거나 충분한 key:value가 없으면 ({} , 원문) 반환.
        """
        if not text or not text.strip():
            return {}, text

        lines = text.splitlines()
        delim_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "---":
                delim_idx = i
                break

        if delim_idx is None:
            return {}, text

        front_lines = lines[:delim_idx]
        body_lines = lines[delim_idx + 1 :]

        meta: dict[str, str] = {}
        for line in front_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in stripped:
                continue
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key:
                meta[key] = val

        if not meta:
            return {}, text

        expected_keys = {"category", "role", "team", "difficulty", "speech_style"}
        if not (expected_keys & set(meta.keys())):
            return {}, text

        body = "\n".join(body_lines).lstrip("\n")
        return meta, body

    def index_from_disk(self, knowledge_root: str | Path) -> None:
        """
        knowledge_root 아래의 문서(.md)들을 찾아 Chroma에 적재.
        문서가 없으면 아무 것도 하지 않고 넘어갑니다.
        """
        root = Path(knowledge_root)
        self._knowledge_root = root

        sentinel_path = self.persist_dir / ".rag_index_root.txt"
        previous_root = None
        if sentinel_path.exists():
            try:
                previous_root = sentinel_path.read_text(encoding="utf-8").strip()
            except Exception:
                previous_root = None

        # root이 바뀌었으면 기존 컬렉션을 비운다.
        if previous_root and previous_root != str(root):
            try:
                self.collection.delete(where={})
            except Exception:
                pass
            self._indexed = False

        # 같은 root로 이미 인덱싱되어 있고 컬렉션에 문서가 있으면 skip
        if previous_root == str(root) and not self._indexed:
            try:
                if self.collection.count() > 0:
                    self._indexed = True
                    return
            except Exception:
                pass

        if self._indexed and previous_root == str(root):
            return

        md_files = list(root.rglob("*.md"))
        if not md_files:
            self._indexed = True
            try:
                sentinel_path.write_text(str(root), encoding="utf-8")
            except Exception:
                pass
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

            parsed_meta, body = self._extract_frontmatter(text)

            rel = fp.relative_to(root)
            parts = rel.parts
            folder_category = parts[0] if len(parts) >= 1 else "unknown"
            folder_category = folder_to_category.get(folder_category, folder_category)

            category = parsed_meta.get("category") or folder_category
            meta = {
                "category": category,
                # WORK_ORDER / RAG 설계: 정적 지식은 static, 런타임 인사이트는 runtime
                "source": "static",
                "file": fp.name,
                "knowledge_root": str(root),
            }
            meta.update(parsed_meta)
            metadatas.append(meta)
            texts.append(body)

        if texts:
            self.add_documents(texts=texts, metadatas=metadatas)

        self._indexed = True
        try:
            sentinel_path.write_text(str(root), encoding="utf-8")
        except Exception:
            pass
