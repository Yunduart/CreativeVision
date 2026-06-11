from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SurfaceType = Literal["rectangle", "polygon"]


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    frame_rate: float = Field(..., gt=0)
    output_width: int = Field(..., gt=0)
    output_height: int = Field(..., gt=0)
    playback_software: str = Field(..., min_length=1)
    codec_requirement: str = Field(..., min_length=1)
    onsite_notes: str = ""


class ProjectRecord(ProjectCreate):
    id: int
    slug: str
    output_path: str | None = None


class ScreenCreate(BaseModel):
    screen_name: str
    surface_type: SurfaceType
    x: int = 0
    y: int = 0
    width: int = Field(0, ge=0)
    height: int = Field(0, ge=0)
    polygon_points: list[list[int]] = Field(default_factory=list)
    safe_area_ratio: float = Field(0.9, gt=0, le=1)
    notes: str = ""


class ScreenRecord(ScreenCreate):
    id: int
    project_id: int


class QCIssue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str
    screen_name: str | None = None


class QCResult(BaseModel):
    passed: bool
    issues: list[QCIssue]


class Artifact(BaseModel):
    label: str
    path: str
    kind: str


class GenerateResult(BaseModel):
    project: ProjectRecord
    artifacts: list[Artifact]
    qc: QCResult
