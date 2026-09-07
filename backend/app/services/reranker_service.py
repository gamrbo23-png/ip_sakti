"""
IP-SAKTI Sahayak — BGE Reranker Service
Uses BAAI/bge-reranker-v2-m3 to score and reorder candidate passages.
"""
from __future__ import annotations

import time
from typing import List, Optional, Tuple

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RerankerService:
    """
    Multilingual reranker using BAAI/bge-reranker-v2-m3.
    Takes a query and candidate passages, returns scored and sorted results.
    """

    def __init__(self) -> None:
        self._model = None
        self._model_name = settings.reranker_model_name
        self._device = settings.reranker_device
        self._ready = False

    def _load_model(self) -> None:
        if self._model is not None:
            return

        logger.info("Loading reranker model", model=self._model_name, device=self._device)
        start = time.monotonic()

        try:
            from FlagEmbedding import FlagReranker

            self._model = FlagReranker(
                self._model_name,
                use_fp16=(self._device == "cuda"),
                device=self._device,
            )
            self._ready = True
            elapsed = round(time.monotonic() - start, 2)
            logger.info("Reranker model loaded", elapsed_s=elapsed)
        except Exception as exc:
            logger.warning("FlagEmbedding reranker not available locally. Using fast keyword relevance fallback.", error=str(exc))
            self._model = "fallback"
            self._ready = True

    def is_ready(self) -> bool:
        return self._ready

    def rerank(
        self,
        query: str,
        passages: List[str],
        top_k: Optional[int] = None,
        normalize: bool = True,
    ) -> List[Tuple[int, float]]:
        """
        Score and sort passages by relevance to query.

        Args:
            query: The user's question.
            passages: List of candidate text passages.
            top_k: Return only the top-k results.
            normalize: Apply sigmoid normalization to scores.

        Returns:
            List of (original_index, score) sorted by score descending.
        """
        if not self._ready:
            self._load_model()

        if not passages:
            return []

        if self._model == "fallback":
            # Token overlap scoring
            q_tokens = set(query.lower().split())
            scores = []
            for p in passages:
                p_tokens = set(p.lower().split())
                overlap = len(q_tokens & p_tokens) / max(len(q_tokens), 1)
                scores.append(0.5 + 0.5 * min(overlap, 1.0))
            indexed = list(enumerate(scores))
            indexed.sort(key=lambda x: x[1], reverse=True)
            return indexed[:k]

        try:
            # Build (query, passage) pairs
            pairs = [[query, p] for p in passages]

            scores = self._model.compute_score(
                pairs,
                normalize=normalize,
                batch_size=min(16, len(pairs)),
            )

            if not isinstance(scores, list):
                scores = list(scores)

            # Sort by score descending
            indexed = list(enumerate(scores))
            indexed.sort(key=lambda x: x[1], reverse=True)

            return indexed[:k]

        except Exception as exc:
            logger.error("Reranking failed", error=str(exc))
            # Fallback: return original order with uniform scores
            return [(i, 0.5) for i in range(min(k, len(passages)))]


# ── Singleton ─────────────────────────────────────────────────────────────────
_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    """Return the global reranker service singleton."""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService()
    return _reranker_service
