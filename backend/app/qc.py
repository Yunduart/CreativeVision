from __future__ import annotations

from shapely.geometry import Polygon, box

from app.models import ProjectCreate, QCCheck, QCIssue, QCResult, ScreenCreate


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
    checks: list[QCCheck] = []

    def add_check(code: str, label: str, passed: bool, severity: str, message: str) -> None:
        checks.append(
            QCCheck(
                code=code,
                label=label,
                passed=passed,
                severity=severity,
                message=message,
            )
        )

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

    canvas_dimensions_valid = project.output_width > 0 and project.output_height > 0
    add_check(
        "CANVAS_DIMENSIONS_VALID",
        "Canvas dimensions valid",
        canvas_dimensions_valid,
        "error",
        "Output canvas width and height must be positive.",
    )

    canvas_dimensions_even = project.output_width % 2 == 0 and project.output_height % 2 == 0
    add_check(
        "CANVAS_DIMENSIONS_EVEN",
        "Canvas dimensions even",
        canvas_dimensions_even,
        "error",
        "Output canvas width and height must be even.",
    )
    if not canvas_dimensions_even:
        issues.append(
            QCIssue(
                code="ODD_DIMENSION",
                severity="error",
                message="Project output width and height must be even.",
            )
        )

    frame_rate_valid = project.frame_rate > 0
    add_check(
        "FRAME_RATE_VALID",
        "Frame rate valid",
        frame_rate_valid,
        "error",
        "Frame rate must be greater than zero.",
    )

    canvas = box(0, 0, project.output_width, project.output_height)
    geometries: list[tuple[ScreenCreate, object]] = []
    screen_names_present = True
    screen_dimensions_valid = True
    screens_inside_canvas = True
    polygon_point_count_valid = True
    polygon_geometry_valid = True
    safe_area_ratio_valid = True
    overlap_free = True

    for screen in screens:
        if not screen.screen_name.strip():
            screen_names_present = False
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Screen name is required.",
                    screen_name=screen.screen_name or None,
                )
            )

        dimensions_valid = screen.width > 0 and screen.height > 0
        if not dimensions_valid:
            screen_dimensions_valid = False
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Screen dimensions must be positive.",
                    screen_name=screen.screen_name or None,
                )
            )

        if screen.surface_type == "rectangle" and (screen.width % 2 or screen.height % 2):
            screen_dimensions_valid = False
            issues.append(
                QCIssue(
                    code="ODD_DIMENSION",
                    severity="error",
                    message="Screen width and height must be even.",
                    screen_name=screen.screen_name or None,
                )
            )

        if screen.surface_type == "polygon" and len(screen.polygon_points) < 3:
            polygon_point_count_valid = False
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Polygon screens require at least three points.",
                    screen_name=screen.screen_name or None,
                )
            )

        if screen.safe_area_ratio <= 0 or screen.safe_area_ratio > 1:
            safe_area_ratio_valid = False
            issues.append(
                QCIssue(
                    code="SAFE_AREA_RATIO",
                    severity="error",
                    message="Safe area ratio must be greater than 0 and no more than 1.",
                    screen_name=screen.screen_name or None,
                )
            )

        geometry = screen_geometry(screen)
        if geometry is None or geometry.is_empty:
            polygon_geometry_valid = False
            issues.append(
                QCIssue(
                    code="MISSING_FIELD",
                    severity="error",
                    message="Screen geometry is incomplete.",
                    screen_name=screen.screen_name or None,
                )
            )
            continue

        if screen.surface_type == "polygon" and (not geometry.is_valid or geometry.area <= 0):
            polygon_geometry_valid = False
            issues.append(
                QCIssue(
                    code="INVALID_POLYGON",
                    severity="error",
                    message="Polygon geometry must be valid and non-self-intersecting.",
                    screen_name=screen.screen_name or None,
                )
            )

        if not canvas.covers(geometry):
            screens_inside_canvas = False
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
                overlap_free = False
                issues.append(
                    QCIssue(
                        code="OVERLAP",
                        severity="warning",
                        message=f"{left_screen.screen_name or 'Unnamed screen'} overlaps {right_screen.screen_name or 'unnamed screen'}.",
                        screen_name=left_screen.screen_name or None,
                    )
                )

    add_check(
        "SCREEN_NAMES_PRESENT",
        "Screen names present",
        screen_names_present,
        "error",
        "Every screen must have a name.",
    )
    add_check(
        "SCREEN_DIMENSIONS_VALID",
        "Screen dimensions valid",
        screen_dimensions_valid,
        "error",
        "Screen dimensions must be positive and rectangle dimensions must be even.",
    )
    add_check(
        "SCREENS_INSIDE_CANVAS",
        "Screens inside canvas",
        screens_inside_canvas,
        "error",
        "Every screen must stay inside the output canvas.",
    )
    add_check(
        "POLYGON_POINT_COUNT",
        "Polygon screens have at least 3 points",
        polygon_point_count_valid,
        "error",
        "Polygon screens require at least three points.",
    )
    add_check(
        "POLYGON_GEOMETRY_VALID",
        "Polygon geometry valid",
        polygon_geometry_valid,
        "error",
        "Polygon geometry must be valid and non-self-intersecting.",
    )
    add_check(
        "SAFE_AREA_RATIO_VALID",
        "Safe area ratio valid",
        safe_area_ratio_valid,
        "error",
        "Safe area ratio must be greater than 0 and no more than 1.",
    )
    add_check(
        "OVERLAP_WARNINGS",
        "Overlap warnings",
        overlap_free,
        "warning",
        "Screens should not overlap unless the overlap is intentional.",
    )

    return QCResult(
        passed=not any(issue.severity == "error" for issue in issues),
        checks=checks,
        issues=issues,
    )
