from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.narratives.aggregator import NarrativeCandidate


@dataclass(frozen=True)
class NarrativeScoreResult:
    score: float
    components: dict[str, float]


class NarrativeScorer:
    EVENT_COUNT_WEIGHT = 30.0
    CONFIDENCE_WEIGHT = 40.0
    RECENCY_WEIGHT = 20.0
    DIVERSITY_WEIGHT = 10.0
    EVENT_COUNT_CAP = 5
    EVENT_TYPE_DIVERSITY_CAP = 4

    def score(
        self,
        candidate: NarrativeCandidate,
        *,
        range_start: date,
        range_end: date,
    ) -> NarrativeScoreResult:
        event_count_score = (
            min(candidate.event_count, self.EVENT_COUNT_CAP)
            / self.EVENT_COUNT_CAP
            * self.EVENT_COUNT_WEIGHT
        )
        confidence_score = (
            (candidate.average_confidence + candidate.max_confidence)
            / 2
            * self.CONFIDENCE_WEIGHT
        )
        recency_score = self._recency_ratio(
            last_seen=candidate.last_seen,
            range_start=range_start,
            range_end=range_end,
        ) * self.RECENCY_WEIGHT
        event_type_diversity_score = (
            min(
                max(len(candidate.event_types) - 1, 0),
                self.EVENT_TYPE_DIVERSITY_CAP - 1,
            )
            / (self.EVENT_TYPE_DIVERSITY_CAP - 1)
            * self.DIVERSITY_WEIGHT
        )

        components = {
            "event_count_score": round(event_count_score, 4),
            "confidence_score": round(confidence_score, 4),
            "recency_score": round(recency_score, 4),
            "event_type_diversity_score": round(event_type_diversity_score, 4),
        }
        return NarrativeScoreResult(
            score=round(sum(components.values()), 4),
            components=components,
        )

    @staticmethod
    def _recency_ratio(*, last_seen: date, range_start: date, range_end: date) -> float:
        span_days = (range_end - range_start).days
        if span_days <= 0:
            return 1.0

        elapsed_days = (last_seen - range_start).days
        return max(0.0, min(1.0, elapsed_days / span_days))
