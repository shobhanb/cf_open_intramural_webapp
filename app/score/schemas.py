from __future__ import annotations

from app.schemas import CustomBaseModel


class ScoreBaseModel(CustomBaseModel):
    ordinal: int
    event_name: str
    score: int
    valid: int
    score_display: str
    reps: int | None
    time_ms: str | None
    tiebreak_ms: str | None


class ScoreExtendedModel(ScoreBaseModel):
    participation_score: int
    top3_score: int
    judge_score: int
    attendance_score: int


class ScoreEvents(CustomBaseModel):
    event_name: str
