from pathlib import Path

from app.generators import generate_project_package
from app.models import ProjectCreate, ScreenCreate
from app.qc import run_qc


def sample_project() -> ProjectCreate:
    return ProjectCreate(
        project_name="Demo Stage",
        client_name="THE VISION",
        frame_rate=25,
        output_width=1920,
        output_height=1080,
        playback_software="Resolume Arena",
        codec_requirement="DXV3",
        onsite_notes="Check processor output before doors.",
    )


def sample_screens() -> list[ScreenCreate]:
    return [
        ScreenCreate(
            screen_name="Main LED",
            surface_type="rectangle",
            x=0,
            y=0,
            width=960,
            height=540,
            polygon_points=[],
            safe_area_ratio=0.9,
            notes="Primary content.",
        ),
        ScreenCreate(
            screen_name="Diamond",
            surface_type="polygon",
            x=1100,
            y=120,
            width=500,
            height=500,
            polygon_points=[[1350, 120], [1600, 370], [1350, 620], [1100, 370]],
            safe_area_ratio=0.85,
            notes="Irregular scenic LED.",
        ),
    ]


def test_qc_reports_even_bounds_overlap_and_missing_fields():
    project = sample_project()
    screens = [
        ScreenCreate(
            screen_name="Main",
            surface_type="rectangle",
            x=0,
            y=0,
            width=961,
            height=540,
            polygon_points=[],
            safe_area_ratio=0.9,
            notes="",
        ),
        ScreenCreate(
            screen_name="",
            surface_type="rectangle",
            x=900,
            y=0,
            width=300,
            height=1200,
            polygon_points=[],
            safe_area_ratio=0.9,
            notes="Missing name and out of canvas.",
        ),
    ]

    result = run_qc(project, screens)

    codes = {issue.code for issue in result.issues}
    assert "ODD_DIMENSION" in codes
    assert "OUT_OF_CANVAS" in codes
    assert "OVERLAP" in codes
    assert "MISSING_FIELD" in codes
    assert result.passed is False


def test_generate_project_package_creates_required_artifacts(tmp_path: Path):
    artifacts = generate_project_package(
        project=sample_project(),
        screens=sample_screens(),
        output_root=tmp_path,
    )

    expected_dirs = [
        "00_Input",
        "01_Analysis",
        "02_ScreenSpec",
        "03_PixelMap",
        "04_AE",
        "05_C4D",
        "06_Export",
        "07_Onsite",
        "08_Archive",
    ]
    for dirname in expected_dirs:
        assert (tmp_path / "Demo_Stage" / dirname).is_dir()

    expected_files = {
        "01_Analysis/qc_report.md",
        "02_ScreenSpec/screen_spec.md",
        "03_PixelMap/project_pixelmap_full.png",
        "03_PixelMap/project_pixelmap_numbered.png",
        "03_PixelMap/project_pixelmap_safearea.png",
        "03_PixelMap/project_pixelmap_mask.svg",
        "03_PixelMap/project_mapping.json",
        "04_AE/create_project.jsx",
        "05_C4D/create_stage_scene.py",
        "07_Onsite/delivery_spec.md",
    }
    artifact_paths = {Path(item.path).as_posix() for item in artifacts}
    for expected in expected_files:
        assert any(path.endswith(expected) for path in artifact_paths)
        assert (tmp_path / "Demo_Stage" / expected).is_file()

    screen_spec = (tmp_path / "Demo_Stage" / "02_ScreenSpec" / "screen_spec.md").read_text(encoding="utf-8")
    assert "Main LED" in screen_spec
    assert "Diamond" in screen_spec
    assert "1920 x 1080" in screen_spec

    qc_report = (tmp_path / "Demo_Stage" / "01_Analysis" / "qc_report.md").read_text(encoding="utf-8")
    assert "QC Report" in qc_report
    assert "Passed" in qc_report
