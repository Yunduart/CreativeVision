from pathlib import Path

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

    qc_response = client.get(f"/projects/{project['id']}/qc")
    assert qc_response.status_code == 200
    assert qc_response.json()["passed"] is True

    generate_response = client.post(f"/projects/{project['id']}/generate")
    assert generate_response.status_code == 200
    payload = generate_response.json()
    artifact_paths = [artifact["path"] for artifact in payload["artifacts"]]

    assert payload["qc"]["passed"] is True
    assert any(path.endswith("03_PixelMap/project_pixelmap_full.png") for path in artifact_paths)
    assert any(path.endswith("04_AE/create_project.jsx") for path in artifact_paths)
    assert any(path.endswith("05_C4D/create_stage_scene.py") for path in artifact_paths)
    assert (tmp_path / "exports" / "API_Demo" / "07_Onsite" / "delivery_spec.md").is_file()
