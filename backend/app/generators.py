from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import svgwrite
from PIL import Image, ImageDraw, ImageFont
from shapely.affinity import scale

from app.models import Artifact, ProjectCreate, ScreenCreate
from app.qc import run_qc, screen_geometry


PROJECT_DIRS = [
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


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    return slug or "Untitled_Project"


def screen_points(screen: ScreenCreate) -> list[tuple[int, int]]:
    if screen.surface_type == "polygon":
        return [(int(point[0]), int(point[1])) for point in screen.polygon_points]
    return [
        (screen.x, screen.y),
        (screen.x + screen.width, screen.y),
        (screen.x + screen.width, screen.y + screen.height),
        (screen.x, screen.y + screen.height),
    ]


def safe_area_points(screen: ScreenCreate) -> list[tuple[int, int]]:
    geometry = screen_geometry(screen)
    if geometry is None or geometry.is_empty:
        return screen_points(screen)
    safe_geometry = scale(
        geometry,
        xfact=screen.safe_area_ratio,
        yfact=screen.safe_area_ratio,
        origin="centroid",
    )
    return [(int(x), int(y)) for x, y in list(safe_geometry.exterior.coords)[:-1]]


def draw_pixel_map(
    project: ProjectCreate,
    screens: list[ScreenCreate],
    path: Path,
    numbered: bool = False,
    safe_area: bool = False,
) -> None:
    image = Image.new("RGB", (project.output_width, project.output_height), "#08090b")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    grid_color = "#1d2630"
    grid_step = max(120, min(project.output_width, project.output_height) // 12)
    for x in range(0, project.output_width, grid_step):
        draw.line([(x, 0), (x, project.output_height)], fill=grid_color, width=1)
    for y in range(0, project.output_height, grid_step):
        draw.line([(0, y), (project.output_width, y)], fill=grid_color, width=1)

    palette = ["#22d3ee", "#f472b6", "#a3e635", "#facc15", "#c084fc", "#fb7185"]
    for index, screen in enumerate(screens, start=1):
        points = safe_area_points(screen) if safe_area else screen_points(screen)
        color = palette[(index - 1) % len(palette)]
        draw.polygon(points, outline=color, fill=None)
        draw.line(points + [points[0]], fill=color, width=4)

        if numbered:
            geometry = screen_geometry(screen)
            if geometry is not None and not geometry.is_empty:
                center = geometry.centroid
                label = f"{index} {screen.screen_name}"
                draw.rectangle(
                    [(int(center.x) - 8, int(center.y) - 12), (int(center.x) + 170, int(center.y) + 10)],
                    fill="#050507",
                    outline=color,
                )
                draw.text((int(center.x), int(center.y) - 8), label, fill="#ffffff", font=font)

    image.save(path)


def write_svg_mask(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    drawing = svgwrite.Drawing(
        filename=str(path),
        size=(project.output_width, project.output_height),
        viewBox=f"0 0 {project.output_width} {project.output_height}",
    )
    drawing.add(drawing.rect(insert=(0, 0), size=("100%", "100%"), fill="black"))
    for screen in screens:
        points = screen_points(screen)
        drawing.add(drawing.polygon(points=points, fill="white", stroke="#00ffff", stroke_width=2))
    drawing.save()


def write_mapping_json(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    payload = {
        "project_name": project.project_name,
        "client_name": project.client_name,
        "frame_rate": project.frame_rate,
        "output_resolution": {
            "width": project.output_width,
            "height": project.output_height,
        },
        "playback_software": project.playback_software,
        "codec_requirement": project.codec_requirement,
        "screens": [
            {
                "id": slugify(screen.screen_name).upper(),
                "name": screen.screen_name,
                "type": screen.surface_type,
                "x": screen.x,
                "y": screen.y,
                "width": screen.width,
                "height": screen.height,
                "polygon_points": screen.polygon_points,
                "safe_area_ratio": screen.safe_area_ratio,
                "notes": screen.notes,
            }
            for screen in screens
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_screen_spec(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    lines = [
        f"# Screen Spec - {project.project_name}",
        "",
        f"- Client: {project.client_name}",
        f"- Output canvas: {project.output_width} x {project.output_height}",
        f"- Frame rate: {project.frame_rate}",
        f"- Playback software: {project.playback_software}",
        f"- Codec requirement: {project.codec_requirement}",
        "",
        "| Screen | Type | Origin | Size | Safe Area | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for screen in screens:
        if screen.surface_type == "polygon":
            point_text = " ".join(f"({x},{y})" for x, y in screen_points(screen))
            size_text = f"polygon bounds {screen.width} x {screen.height}"
            origin_text = point_text
        else:
            size_text = f"{screen.width} x {screen.height}"
            origin_text = f"{screen.x}, {screen.y}"
        notes = screen.notes.replace("|", "/")
        lines.append(
            f"| {screen.screen_name} | {screen.surface_type} | {origin_text} | {size_text} | {screen.safe_area_ratio} | {notes} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_qc_report(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    result = run_qc(project, screens)
    lines = [
        f"# QC Report - {project.project_name}",
        "",
        f"Status: {'Passed' if result.passed else 'Failed'}",
        "",
        "## Checks",
        "- Even output and rectangle screen dimensions",
        "- Screen coordinates inside output canvas",
        "- Screen overlap detection",
        "- Required project and screen fields",
        "",
        "## Issues",
    ]
    if result.issues:
        for issue in result.issues:
            screen_name = f" [{issue.screen_name}]" if issue.screen_name else ""
            lines.append(f"- {issue.severity.upper()} {issue.code}{screen_name}: {issue.message}")
    else:
        lines.append("- No issues found.")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ae_jsx(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    screen_lines = []
    for screen in screens:
        comp_name = f"SCREEN_{slugify(screen.screen_name).upper()}_PRECOMP"
        width = screen.width or max(1, int(screen_geometry(screen).bounds[2] - screen_geometry(screen).bounds[0]))
        height = screen.height or max(1, int(screen_geometry(screen).bounds[3] - screen_geometry(screen).bounds[1]))
        screen_lines.append(
            f'var {comp_name} = app.project.items.addComp("{comp_name}", {width}, {height}, 1, 30, {project.frame_rate});'
        )

    content = f"""// Generated by VJ Stage Visual Production OS
app.beginUndoGroup("Create VJ Project OS Comp");
var project = app.project || app.newProject();
var mainComp = app.project.items.addComp(
  "MAIN_COMP_{project.output_width}x{project.output_height}",
  {project.output_width},
  {project.output_height},
  1,
  30,
  {project.frame_rate}
);
var pixelMapFile = new File("../03_PixelMap/project_pixelmap_numbered.png");
if (pixelMapFile.exists) {{
  var importOptions = new ImportOptions(pixelMapFile);
  var pixelMap = app.project.importFile(importOptions);
  var pixelLayer = mainComp.layers.add(pixelMap);
  pixelLayer.guideLayer = true;
  pixelLayer.name = "PIXEL_MAP_GUIDE";
}}
var safeAreaFile = new File("../03_PixelMap/project_pixelmap_safearea.png");
if (safeAreaFile.exists) {{
  var safeImportOptions = new ImportOptions(safeAreaFile);
  var safeMap = app.project.importFile(safeImportOptions);
  var safeLayer = mainComp.layers.add(safeMap);
  safeLayer.guideLayer = true;
  safeLayer.name = "SAFE_AREA_GUIDE";
}}
{chr(10).join(screen_lines)}
app.endUndoGroup();
"""
    path.write_text(content, encoding="utf-8")


def write_c4d_script(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    screen_defs = []
    for screen in screens:
        geometry = screen_geometry(screen)
        bounds = geometry.bounds if geometry is not None else (screen.x, screen.y, screen.x + screen.width, screen.y + screen.height)
        width = int(bounds[2] - bounds[0])
        height = int(bounds[3] - bounds[1])
        center_x = int(bounds[0] + width / 2)
        center_y = int(bounds[1] + height / 2)
        screen_defs.append(
            f'    create_screen_plane(doc, "{screen.screen_name}", {width}, {height}, {center_x}, {center_y})'
        )

    content = f'''# Generated by VJ Stage Visual Production OS
import c4d


def create_screen_plane(doc, name, width, height, x, y):
    plane = c4d.BaseObject(c4d.Oplane)
    plane.SetName(name)
    plane[c4d.PRIM_PLANE_WIDTH] = width
    plane[c4d.PRIM_PLANE_HEIGHT] = height
    plane.SetAbsPos(c4d.Vector(x - {project.output_width / 2}, {project.output_height / 2} - y, 0))
    doc.InsertObject(plane)
    return plane


def main():
    doc = c4d.documents.GetActiveDocument()
    material = c4d.BaseMaterial(c4d.Mmaterial)
    material.SetName("Material_PixelMap_Texture")
    doc.InsertMaterial(material)
{chr(10).join(screen_defs)}

    camera = c4d.BaseObject(c4d.Ocamera)
    camera.SetName("Camera_Front")
    camera.SetAbsPos(c4d.Vector(0, 0, -3000))
    doc.InsertObject(camera)
    doc.SetActiveObject(camera)

    render_data = doc.GetActiveRenderData()
    render_data[c4d.RDATA_XRES] = {project.output_width}
    render_data[c4d.RDATA_YRES] = {project.output_height}
    c4d.EventAdd()


if __name__ == "__main__":
    main()
'''
    path.write_text(content, encoding="utf-8")


def write_delivery_spec(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    lines = [
        f"# Delivery Spec - {project.project_name}",
        "",
        f"- Client: {project.client_name}",
        f"- Output resolution: {project.output_width} x {project.output_height}",
        f"- Frame rate: {project.frame_rate}",
        f"- Codec: {project.codec_requirement}",
        f"- Playback software: {project.playback_software}",
        "",
        "## Screen List",
    ]
    for screen in screens:
        lines.append(
            f"- {screen.screen_name}: {screen.surface_type}, {screen.x},{screen.y}, {screen.width}x{screen.height}, safe area {screen.safe_area_ratio}"
        )
    lines.extend(
        [
            "",
            "## File Naming Rule",
            "`PROJECT_SCREEN_VERSION_CODEC_RESOLUTION.ext`",
            "",
            "## Onsite Notes",
            project.onsite_notes or "Confirm processor routing, playback frame rate, and backup outputs onsite.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_ffmpeg_probe(ffmpeg_path: str = "ffmpeg") -> bool:
    try:
        subprocess.run([ffmpeg_path, "-version"], check=False, capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
    return True


def generate_project_package(
    project: ProjectCreate,
    screens: list[ScreenCreate],
    output_root: Path,
) -> list[Artifact]:
    project_root = output_root / slugify(project.project_name)
    for dirname in PROJECT_DIRS:
        (project_root / dirname).mkdir(parents=True, exist_ok=True)

    def artifact(label: str, path: Path, kind: str) -> Artifact:
        return Artifact(label=label, path=path.as_posix(), kind=kind)

    artifacts = [
        artifact("QC report", project_root / "01_Analysis" / "qc_report.md", "markdown"),
        artifact("Screen spec", project_root / "02_ScreenSpec" / "screen_spec.md", "markdown"),
        artifact("Full pixel map", project_root / "03_PixelMap" / "project_pixelmap_full.png", "png"),
        artifact("Numbered pixel map", project_root / "03_PixelMap" / "project_pixelmap_numbered.png", "png"),
        artifact("Safe area pixel map", project_root / "03_PixelMap" / "project_pixelmap_safearea.png", "png"),
        artifact("SVG mask", project_root / "03_PixelMap" / "project_pixelmap_mask.svg", "svg"),
        artifact("Mapping JSON", project_root / "03_PixelMap" / "project_mapping.json", "json"),
        artifact("AE JSX script", project_root / "04_AE" / "create_project.jsx", "jsx"),
        artifact("C4D Python script", project_root / "05_C4D" / "create_stage_scene.py", "python"),
        artifact("Delivery spec", project_root / "07_Onsite" / "delivery_spec.md", "markdown"),
    ]

    write_qc_report(project, screens, Path(artifacts[0].path))
    write_screen_spec(project, screens, Path(artifacts[1].path))
    draw_pixel_map(project, screens, Path(artifacts[2].path))
    draw_pixel_map(project, screens, Path(artifacts[3].path), numbered=True)
    draw_pixel_map(project, screens, Path(artifacts[4].path), safe_area=True)
    write_svg_mask(project, screens, Path(artifacts[5].path))
    write_mapping_json(project, screens, Path(artifacts[6].path))
    write_ae_jsx(project, screens, Path(artifacts[7].path))
    write_c4d_script(project, screens, Path(artifacts[8].path))
    write_delivery_spec(project, screens, Path(artifacts[9].path))

    return artifacts
