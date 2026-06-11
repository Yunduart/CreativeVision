from __future__ import annotations

from shapely.geometry import Polygon, box

from app.models import ProjectCreate, QCIssue, QCResult, ScreenCreate


def screen_geometry(screen: ScreenCreate):
    if screen.surface_type == "polygon":
        if len(screen.polygon_points) < 3:
            return None
        return Polygon([(point[0], point[1]) for point in screen.polygon_points])

    if screen.width <= 0 or screen.height <= 0:
        return None
    return box(screen.x, screen.y, screen.x + screen.width, screen.y + screen.height)


def run_qc(project: ProjectCreate, screens: list[ScreenCreate]) -> QCResult:
    issues: list[QCIssue] = []

    project_fields = {
        "project name": project.project_name,
        "client name": project.client_name,
        "playback software": project.playback_software,
        "codec requirement": project.codec_requirement,
    }
    for label, value in project_fields.items():
        if not str(value).strip():
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message=f"Missing project {label}.",
                )
            )

    if project.output_width % 2 or project.output_height % 2:
        issues.append(
            QCIssue(
                code="ODD_DIMENSION",
                severity="error",
                message="Project output width and height must be even.",
            )
        )

    canvas = box(0, 0, project.output_width, project.output_height)
    geometries: list[tuple[ScreenCreate, object]] = []

    for screen in screens:
        if not screen.screen_name.strip():
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Screen name is required.",
                    screen_name=screen.screen_name or None,
                )
            )

        if screen.surface_type == "rectangle" and (screen.width % 2 or screen.height % 2):
            issues.append(
                QCIssue(
                    code="ODD_DIMENSION",
                    severity="error",
                    message="Screen width and height must be even.",
                    screen_name=screen.screen_name or None,
                )
            )

        if screen.surface_type == "polygon" and len(screen.polygon_points) < 3:
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Polygon screens require at least three points.",
                    screen_name=screen.screen_name or None,
                )
            )

        geometry = screen_geometry(screen)
        if geometry is None or geometry.is_empty:
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Screen geometry is incomplete.",
                    screen_name=screen.screen_name or None,
                )
            )
            continue

        if not canvas.covers(geometry):
            issues.append(
                QCIssue(
                    code="OUT_OF_CANVAS",
                    severity="error",
                    message="Screen coordinates must stay inside the output canvas.",
                    screen_name=screen.screen_name or None,
                )
            )

        geometries.append((screen, geometry))

    for index, (left_screen, left_geometry) in enumerate(geometries):
        for right_screen, right_geometry in geometries[index + 1 :]:
            if left_geometry.intersects(right_geometry) and left_geometry.intersection(right_geometry).area > 0:
                issues.append(
                    QCIssue(
                        code="OVERLAP",
                        severity="warning",
                        message=f"{left_screen.screen_name or 'Unnamed screen'} overlaps {right_screen.screen_name or 'unnamed screen'}.",
                        screen_name=left_screen.screen_name or None,
                    )
                )

    return QCResult(
        passed=not any(issue.severity == "error" for issue in issues),
        issues=issues,
    )
