from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List

from backend.rag.store import RAGStore

logger = logging.getLogger("mafia.backend.rag.retriever")


@dataclass
class SituationDescription:
    text: str
    player_role: str | None = None
    player_team: str | None = None


def _rag_where_for_player(role: str, team: str) -> dict:
    """역할·팀 일치 또는 공용 카테고리(situation/rule/speech) 문서만 검색."""
    return {
        "$or": [
            {"role": role},
            {"team": team},
            {"category": "situation"},
            {"category": "rule"},
            {"category": "speech"},
        ]
    }


class StrategyRetriever:
    """
    게임 상황 설명을 받아, 관련 전략 지식을 Top-K로 반환하는 RAG 래퍼.
    """

    def __init__(self, store: RAGStore) -> None:
        self.store = store

    def retrieve_strategies(self, situation: SituationDescription, k: int = 3) -> List[dict]:
        use_filter = os.getenv("MAFIA_RAG_METADATA_FILTER", "1").strip().lower() in {"1", "true", "yes"}
        use_mmr = os.getenv("MAFIA_RAG_USE_MMR", "0").strip().lower() in {"1", "true", "yes"}
        mmr_lambda = float(os.getenv("MAFIA_RAG_MMR_LAMBDA", "0.5"))

        where = None
        if (
            use_filter
            and situation.player_role is not None
            and situation.player_team is not None
        ):
            where = _rag_where_for_player(situation.player_role, situation.player_team)

        results = self.store.similarity_search(
            situation.text,
            k=k,
            where=where,
            use_mmr=use_mmr,
            mmr_lambda=mmr_lambda,
        )
        hits = len(results)
        if os.getenv("MAFIA_RAG_LOG_HITS", "1").strip().lower() in {"1", "true", "yes"}:
            logger.info("rag retrieve hits=%d k_requested=%d", hits, k)
        else:
            logger.debug("rag retrieve hits=%d", hits)
        return results
