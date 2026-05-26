"""Schemas for face analysis endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FacePosition(BaseModel):
    """Bounding box for a detected face (image pixel coordinates)."""

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=1)
    h: int = Field(ge=1)


class FaceAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: FacePosition
    confidence: float | None = Field(default=None, description="Detector score, 0..1")
    age: int | None = None
    gender: str | None = None
    dominant_race: str | None = None
    dominant_emotion: str | None = None
    emotion: dict[str, float] | None = None
    race: dict[str, float] | None = None


class AnalyzeResponse(BaseModel):
    status: str = Field(default="success")
    faces_detected: int = Field(ge=0)
    faces: list[FaceAnalysis]
    output_file: str | None = None
