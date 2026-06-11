from __future__ import annotations

from app.models import ProjectCreate, ScreenCreate


def sample_project() -> ProjectCreate:
    return ProjectCreate(
        project_name="Graduation Stage Mapping Demo",
        client_name="THE VISION",
        frame_rate=25,
        output_width=3840,
        output_height=1080,
        playback_software="Resolume Arena",
        codec_requirement="DXV3",
        onsite_notes="Confirm processor routing, output port order, and backup playback machine onsite.",
    )


def sample_screens() -> list[ScreenCreate]:
    return [
        ScreenCreate(
            screen_name="Main LED",
            surface_type="rectangle",
            x=0,
            y=0,
            width=1920,
            height=1080,
            polygon_points=[],
            safe_area_ratio=0.9,
            notes="Primary canvas for hero visuals.",
        ),
        ScreenCreate(
            screen_name="Right Diamond",
            surface_type="polygon",
            x=2280,
            y=140,
            width=640,
            height=640,
            polygon_points=[[2600, 140], [2920, 460], [2600, 780], [2280, 460]],
            safe_area_ratio=0.85,
            notes="Irregular scenic LED. Keep text inside safe area.",
        ),
        ScreenCreate(
            screen_name="Lyric Strip",
            surface_type="rectangle",
            x=3040,
            y=820,
            width=800,
            height=180,
            polygon_points=[],
            safe_area_ratio=0.92,
            notes="Low strip for lyrics and show information.",
        ),
    ]
