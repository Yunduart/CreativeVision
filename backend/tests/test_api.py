from pathlib import Path
import zipfile

from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(
        database_path=tmp_path / "test.db",
        output_root=tmp_path / "exports",
        seed=False,
    )
    return TestClient(app)


def project_payload() -> dict:
    return {
        "project_name": "API Demo",
        "client_name": "THE VISION",
        "frame_rate": 25,
        "output_width": 1920,
        "output_height": 1080,
        "playback_software": "Resolume Arena",
        "codec_requirement": "DXV3",
        "onsite_notes": "Confirm scaler routing onsite.",
    }


def screen_payload() -> dict:
    return {
        "screen_name": "Main LED",
        "surface_type": "rectangle",
        "x": 0,
        "y": 0,
        "width": 960,
        "height": 540,
        "polygon_points": [],
        "safe_area_ratio": 0.9,
        "notes": "Primary screen.",
    }


def test_health_endpoint(tmp_path: Path):
    client = make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_project_and_screen_crud(tmp_path: Path):
    client = make_client(tmp_path)

    project_response = client.post("/projects", json=project_payload())
    assert project_response.status_code == 201
    project = project_response.json()
    assert project["id"] == 1
    assert project["slug"] == "API_Demo"

    screen_response = client.post(f"/projects/{project['id']}/screens", json=screen_payload())
    assert screen_response.status_code == 201
    screen = screen_response.json()
    assert screen["project_id"] == project["id"]
    assert screen["screen_name"] == "Main LED"

    projects = client.get("/projects").json()
    assert len(projects) == 1
    assert projects[0]["project_name"] == "API Demo"

    screens = client.get(f"/projects/{project['id']}/screens").json()
    assert len(screens) == 1
    assert screens[0]["screen_name"] == "Main LED"


def test_qc_and_generation_routes(tmp_path: Path):
    client = make_client(tmp_path)
    project = client.post("/projects", json=project_payload()).json()
    client.post(f"/projects/{project['id']}/screens", json=screen_payload())

    missing_zip_response = client.get(f"/projects/{project['id']}/package.zip")
    assert missing_zip_response.status_code == 409

    qc_response = client.get(f"/projects/{project['id']}/qc")
    assert qc_response.status_code == 200
    qc_payload = qc_response.json()
    assert qc_payload["passed"] is True
    assert {check["code"] for check in qc_payload["checks"]} >= {
        "CANVAS_DIMENSIONS_VALID",
        "CANVAS_DIMENSIONS_EVEN",
        "FRAME_RATE_VALID",
    }

    generate_response = client.post(f"/projects/{project['id']}/generate")
    assert generate_response.status_code == 200
    payload = generate_response.json()
    artifact_paths = [artifact["path"] for artifact in payload["artifacts"]]
    artifact_relative_paths = [artifact["relative_path"] for artifact in payload["artifacts"]]

    assert payload["qc"]["passed"] is True
    assert any(path.endswith("03_PixelMap/project_pixelmap_full.png") for path in artifact_paths)
    assert any(path.endswith("04_AE/create_project.jsx") for path in artifact_paths)
    assert any(path.endswith("05_C4D/create_stage_scene.py") for path in artifact_paths)
    assert "02_ScreenSpec/screen_spec.json" in artifact_relative_paths
    assert "04_AE/README_AE.md" in artifact_relative_paths
    assert "05_C4D/README_C4D.md" in artifact_relative_paths
    assert "06_Export/export_presets.json" in artifact_relative_paths
    assert "06_Export/ffmpeg_proxy_commands.txt" in artifact_relative_paths
    assert "07_Onsite/onsite_runbook.md" in artifact_relative_paths
    assert "07_Onsite/playback_spec.md" in artifact_relative_paths
    assert all(artifact["created_at"] for artifact in payload["artifacts"])
    assert all(artifact["size_bytes"] > 0 for artifact in payload["artifacts"])
    assert (tmp_path / "exports" / "API_Demo" / "07_Onsite" / "delivery_spec.md").is_file()

    artifacts_response = client.get(f"/projects/{project['id']}/artifacts")
    assert artifacts_response.status_code == 200
    assert {artifact["relative_path"] for artifact in artifacts_response.json()} == set(artifact_relative_paths)

    zip_response = client.get(f"/projects/{project['id']}/package.zip")
    assert zip_response.status_code == 200
    zip_path = tmp_path / "package.zip"
    zip_path.write_bytes(zip_response.content)
    with zipfile.ZipFile(zip_path) as package_zip:
        names = set(package_zip.namelist())
    assert "API_Demo/00_Input/" in names
    assert "API_Demo/02_ScreenSpec/screen_spec.json" in names
    assert "API_Demo/06_Export/export_presets.json" in names
    assert "API_Demo/07_Onsite/playback_spec.md" in names


def test_artifact_downloads_do_not_use_stale_same_slug_directory_before_generation(tmp_path: Path):
    client = make_client(tmp_path)
    project = client.post("/projects", json=project_payload()).json()
    client.post(f"/projects/{project['id']}/screens", json=screen_payload())

    stale_root = tmp_path / "exports" / "API_Demo"
    stale_artifact = stale_root / "01_Analysis" / "qc_report.md"
    stale_artifact.parent.mkdir(parents=True)
    stale_artifact.write_text("stale package", encoding="utf-8")

    artifacts_response = client.get(f"/projects/{project['id']}/artifacts")
    zip_response = client.get(f"/projects/{project['id']}/package.zip")
    artifact_response = client.get(f"/projects/{project['id']}/artifacts/01_Analysis/qc_report.md")

    assert artifacts_response.status_code == 200
    assert artifacts_response.json() == []
    assert zip_response.status_code == 409
    assert artifact_response.status_code == 409


def test_patch_screen_updates_rectangle_and_rejects_out_of_canvas(tmp_path: Path):
    client = make_client(tmp_path)
    project = client.post("/projects", json=project_payload()).json()
    screen = client.post(f"/projects/{project['id']}/screens", json=screen_payload()).json()

    update_payload = {
        **screen_payload(),
        "x": 120,
        "y": 140,
        "width": 800,
        "height": 480,
        "notes": "Moved during calibration.",
    }
    update_response = client.patch(
        f"/projects/{project['id']}/screens/{screen['id']}",
        json=update_payload,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["x"] == 120
    assert updated["y"] == 140
    assert updated["width"] == 800
    assert updated["height"] == 480
    assert updated["notes"] == "Moved during calibration."
    assert client.get(f"/projects/{project['id']}/qc").json()["passed"] is True

    invalid_response = client.patch(
        f"/projects/{project['id']}/screens/{screen['id']}",
        json={**update_payload, "x": 1800, "width": 300},
    )

    assert invalid_response.status_code == 400
    persisted = client.get(f"/projects/{project['id']}/screens").json()[0]
    assert persisted["x"] == 120
    assert persisted["width"] == 800


def test_patch_polygon_screen_without_dimensions_uses_points_for_qc(tmp_path: Path):
    client = make_client(tmp_path)
    project = client.post("/projects", json=project_payload()).json()
    polygon_payload = {
        "screen_name": "Diamond Header",
        "surface_type": "polygon",
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0,
        "polygon_points": [[1200, 100], [1500, 300], [1200, 500], [900, 300]],
        "safe_area_ratio": 0.86,
        "notes": "Irregular trim.",
    }
    screen = client.post(f"/projects/{project['id']}/screens", json=polygon_payload).json()

    updated_points = [[1220, 120], [1520, 320], [1220, 520], [920, 320]]
    update_response = client.patch(
        f"/projects/{project['id']}/screens/{screen['id']}",
        json={**polygon_payload, "polygon_points": updated_points},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["width"] == 0
    assert updated["height"] == 0
    assert updated["polygon_points"] == updated_points
    assert client.get(f"/projects/{project['id']}/qc").json()["passed"] is True
