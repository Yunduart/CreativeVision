from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.generators import slugify
from app.models import ProjectCreate, ProjectRecord, ScreenCreate, ScreenRecord


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    frame_rate REAL NOT NULL,
                    output_width INTEGER NOT NULL,
                    output_height INTEGER NOT NULL,
                    playback_software TEXT NOT NULL,
                    codec_requirement TEXT NOT NULL,
                    onsite_notes TEXT NOT NULL DEFAULT '',
                    slug TEXT NOT NULL,
                    output_path TEXT
                );

                CREATE TABLE IF NOT EXISTS screens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    screen_name TEXT NOT NULL,
                    surface_type TEXT NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    polygon_points TEXT NOT NULL,
                    safe_area_ratio REAL NOT NULL,
                    notes TEXT NOT NULL DEFAULT ''
                );
                """
            )

    def create_project(self, payload: ProjectCreate) -> ProjectRecord:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO projects (
                    project_name, client_name, frame_rate, output_width, output_height,
                    playback_software, codec_requirement, onsite_notes, slug
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.project_name,
                    payload.client_name,
                    payload.frame_rate,
                    payload.output_width,
                    payload.output_height,
                    payload.playback_software,
                    payload.codec_requirement,
                    payload.onsite_notes,
                    slugify(payload.project_name),
                ),
            )
            connection.commit()
            return self.get_project(cursor.lastrowid)

    def get_project(self, project_id: int) -> ProjectRecord:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            raise KeyError(f"Project {project_id} not found")
        return self._project_from_row(row)

    def list_projects(self) -> list[ProjectRecord]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        return [self._project_from_row(row) for row in rows]

    def update_project_output_path(self, project_id: int, output_path: str) -> ProjectRecord:
        with self.connect() as connection:
            connection.execute(
                "UPDATE projects SET output_path = ? WHERE id = ?",
                (output_path, project_id),
            )
            connection.commit()
        return self.get_project(project_id)

    def create_screen(self, project_id: int, payload: ScreenCreate) -> ScreenRecord:
        self.get_project(project_id)
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO screens (
                    project_id, screen_name, surface_type, x, y, width, height,
                    polygon_points, safe_area_ratio, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    payload.screen_name,
                    payload.surface_type,
                    payload.x,
                    payload.y,
                    payload.width,
                    payload.height,
                    json.dumps(payload.polygon_points),
                    payload.safe_area_ratio,
                    payload.notes,
                ),
            )
            connection.commit()
            return self.get_screen(cursor.lastrowid)

    def update_screen(self, project_id: int, screen_id: int, payload: ScreenCreate) -> ScreenRecord:
        self.get_project(project_id)
        current = self.get_screen(screen_id)
        if current.project_id != project_id:
            raise KeyError(f"Screen {screen_id} not found")

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE screens
                SET screen_name = ?,
                    surface_type = ?,
                    x = ?,
                    y = ?,
                    width = ?,
                    height = ?,
                    polygon_points = ?,
                    safe_area_ratio = ?,
                    notes = ?
                WHERE id = ? AND project_id = ?
                """,
                (
                    payload.screen_name,
                    payload.surface_type,
                    payload.x,
                    payload.y,
                    payload.width,
                    payload.height,
                    json.dumps(payload.polygon_points),
                    payload.safe_area_ratio,
                    payload.notes,
                    screen_id,
                    project_id,
                ),
            )
            connection.commit()
        return self.get_screen(screen_id)

    def get_screen(self, screen_id: int) -> ScreenRecord:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM screens WHERE id = ?", (screen_id,)).fetchone()
        if row is None:
            raise KeyError(f"Screen {screen_id} not found")
        return self._screen_from_row(row)

    def list_screens(self, project_id: int) -> list[ScreenRecord]:
        self.get_project(project_id)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM screens WHERE project_id = ? ORDER BY id",
                (project_id,),
            ).fetchall()
        return [self._screen_from_row(row) for row in rows]

    @staticmethod
    def _project_from_row(row: sqlite3.Row) -> ProjectRecord:
        return ProjectRecord(**dict(row))

    @staticmethod
    def _screen_from_row(row: sqlite3.Row) -> ScreenRecord:
        data = dict(row)
        data["polygon_points"] = json.loads(data["polygon_points"])
        return ScreenRecord(**data)
