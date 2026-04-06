from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from backend.rag.store import RAGStore

logger = logging.getLogger("mafia.backend.rag.retriever")


@dataclass
class SituationDescription:
    text: str


class StrategyRetriever:
    """
    게임 상황 설명을 받아, 관련 전략 지식을 Top-K로 반환하는 RAG 래퍼.
    """

    def __init__(self, store: RAGStore) -> None:
        self.store = store

    def retrieve_strategies(self, situation: SituationDescription, k: int = 3) -> List[dict]:
        results = self.store.similarity_search(situation.text, k=k)
        logger.debug("rag retrieved k=%d", len(results))
        return results
