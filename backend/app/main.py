from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.database import Database
from app.generators import generate_project_package, slugify
from app.models import GenerateResult, ProjectCreate, ProjectRecord, QCResult, ScreenCreate, ScreenRecord
from app.qc import run_qc
from app.sample_data import sample_project, sample_screens


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "vj_os.sqlite3"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "exports"


def create_app(
    database_path: Path | None = None,
    output_root: Path | None = None,
    seed: bool = True,
) -> FastAPI:
    database = Database(database_path or DEFAULT_DATABASE)
    export_root = output_root or DEFAULT_OUTPUT_ROOT
    database.init()

    if seed and not database.list_projects():
        project = database.create_project(sample_project())
        for screen in sample_screens():
            database.create_screen(project.id, screen)

    app = FastAPI(title="VJ Stage Visual Production OS", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_project_or_404(project_id: int) -> ProjectRecord:
        try:
            return database.get_project(project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def get_screens_or_404(project_id: int) -> list[ScreenRecord]:
        try:
            return database.list_screens(project_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/projects", response_model=list[ProjectRecord])
    def list_projects() -> list[ProjectRecord]:
        return database.list_projects()

    @app.post("/projects", response_model=ProjectRecord, status_code=status.HTTP_201_CREATED)
    def create_project(payload: ProjectCreate) -> ProjectRecord:
        return database.create_project(payload)

    @app.get("/projects/{project_id}", response_model=ProjectRecord)
    def get_project(project_id: int) -> ProjectRecord:
        return get_project_or_404(project_id)

    @app.get("/projects/{project_id}/screens", response_model=list[ScreenRecord])
    def list_project_screens(project_id: int) -> list[ScreenRecord]:
        return get_screens_or_404(project_id)

    @app.post(
        "/projects/{project_id}/screens",
        response_model=ScreenRecord,
        status_code=status.HTTP_201_CREATED,
    )
    def create_screen(project_id: int, payload: ScreenCreate) -> ScreenRecord:
        try:
            return database.create_screen(project_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/projects/{project_id}/qc", response_model=QCResult)
    def project_qc(project_id: int) -> QCResult:
        project = get_project_or_404(project_id)
        screens = get_screens_or_404(project_id)
        return run_qc(project, screens)

    @app.post("/projects/{project_id}/generate", response_model=GenerateResult)
    def generate_project(project_id: int) -> GenerateResult:
        project = get_project_or_404(project_id)
        screens = get_screens_or_404(project_id)
        qc = run_qc(project, screens)
        artifacts = generate_project_package(project, screens, export_root)
        project_root = export_root / slugify(project.project_name)
        updated_project = database.update_project_output_path(project.id, str(project_root))
        return GenerateResult(project=updated_project, artifacts=artifacts, qc=qc)

    return app


app = create_app()
