from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
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

ARTIFACT_DEFINITIONS = [
    ("QC report", "01_Analysis/qc_report.md", "markdown"),
    ("Screen spec", "02_ScreenSpec/screen_spec.md", "markdown"),
    ("Screen spec JSON", "02_ScreenSpec/screen_spec.json", "json"),
    ("Full pixel map", "03_PixelMap/project_pixelmap_full.png", "png"),
    ("Numbered pixel map", "03_PixelMap/project_pixelmap_numbered.png", "png"),
    ("Safe area pixel map", "03_PixelMap/project_pixelmap_safearea.png", "png"),
    ("SVG mask", "03_PixelMap/project_pixelmap_mask.svg", "svg"),
    ("Mapping JSON", "03_PixelMap/project_mapping.json", "json"),
    ("AE README", "04_AE/README_AE.md", "markdown"),
    ("AE JSX script", "04_AE/create_project.jsx", "jsx"),
    ("C4D README", "05_C4D/README_C4D.md", "markdown"),
    ("C4D Python script", "05_C4D/create_stage_scene.py", "python"),
    ("Export presets", "06_Export/export_presets.json", "json"),
    ("FFmpeg proxy commands", "06_Export/ffmpeg_proxy_commands.txt", "text"),
    ("Delivery spec", "07_Onsite/delivery_spec.md", "markdown"),
    ("Onsite runbook", "07_Onsite/onsite_runbook.md", "markdown"),
    ("Playback spec", "07_Onsite/playback_spec.md", "markdown"),
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    return slug or "Untitled_Project"


def project_package_root(project: ProjectCreate, output_root: Path) -> Path:
    return output_root / slugify(project.project_name)


def artifact_from_file(label: str, path: Path, kind: str, package_root: Path) -> Artifact:
    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    relative_path = path.relative_to(package_root).as_posix()
    return Artifact(
        label=label,
        path=path.as_posix(),
        kind=kind,
        relative_path=relative_path,
        created_at=created_at,
        size_bytes=stat.st_size,
    )


def expected_artifact_paths(package_root: Path) -> list[tuple[str, Path, str]]:
    return [(label, package_root / relative_path, kind) for label, relative_path, kind in ARTIFACT_DEFINITIONS]


def list_project_artifacts(package_root: Path) -> list[Artifact]:
    if not package_root.exists():
        return []
    artifacts: list[Artifact] = []
    for label, path, kind in expected_artifact_paths(package_root):
        if path.is_file():
            artifacts.append(artifact_from_file(label, path, kind, package_root))
    return artifacts


def screen_points(screen: ScreenCreate) -> list[tuple[int, int]]:
    if screen.surface_type == "polygon":
        return [(int(point[0]), int(point[1])) for point in screen.polygon_points]
    return [
        (screen.x, screen.y),
        (screen.x + screen.width, screen.y),
        (screen.x + screen.width, screen.y + screen.height),
        (screen.x, screen.y + screen.height),
    ]


def screen_bounds(screen: ScreenCreate) -> tuple[float, float, float, float]:
    geometry = screen_geometry(screen)
    if geometry is not None and not geometry.is_empty:
        return geometry.bounds
    return (screen.x, screen.y, screen.x + screen.width, screen.y + screen.height)


def screen_display_dimensions(screen: ScreenCreate) -> tuple[int, int]:
    min_x, min_y, max_x, max_y = screen_bounds(screen)
    return max(0, int(round(max_x - min_x))), max(0, int(round(max_y - min_y)))


def screen_size_text(screen: ScreenCreate) -> str:
    width, height = screen_display_dimensions(screen)
    return f"{width} x {height}"


def screen_origin_text(screen: ScreenCreate) -> str:
    min_x, min_y, _, _ = screen_bounds(screen)
    return f"{int(round(min_x))}, {int(round(min_y))}"


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
            size_text = f"polygon bounds {screen_size_text(screen)}"
            origin_text = point_text
        else:
            size_text = screen_size_text(screen)
            origin_text = f"{screen.x}, {screen.y}"
        notes = screen.notes.replace("|", "/")
        lines.append(
            f"| {screen.screen_name} | {screen.surface_type} | {origin_text} | {size_text} | {screen.safe_area_ratio} | {notes} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_screen_spec_json(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    payload = {
        "project_name": project.project_name,
        "client_name": project.client_name,
        "output_width": project.output_width,
        "output_height": project.output_height,
        "frame_rate": project.frame_rate,
        "playback_software": project.playback_software,
        "codec_requirement": project.codec_requirement,
        "screens": [
            {
                "screen_name": screen.screen_name,
                "surface_type": screen.surface_type,
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
        width, height = screen_display_dimensions(screen)
        width = max(1, width)
        height = max(1, height)
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
        bounds = screen_bounds(screen)
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
        size_text = screen_size_text(screen)
        origin_text = screen_origin_text(screen)
        lines.append(
            f"- {screen.screen_name}: {screen.surface_type}, {origin_text}, {size_text}, safe area {screen.safe_area_ratio}"
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


def write_ae_readme(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    lines = [
        f"# After Effects Setup - {project.project_name}",
        "",
        "1. Open After Effects and run `create_project.jsx` from this folder.",
        "2. Confirm the generated main comp matches the delivery resolution.",
        "3. Use the imported pixel map and safe-area guide as guide layers only.",
        "4. Render each screen precomp according to the delivery spec.",
        "",
        "## Screen Precomps",
    ]
    lines.extend(f"- {screen.screen_name}: {screen_size_text(screen)}" for screen in screens)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_c4d_readme(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    lines = [
        f"# Cinema 4D Setup - {project.project_name}",
        "",
        "1. Open Cinema 4D and run `create_stage_scene.py` from the Script Manager.",
        "2. Verify screen plane scale and camera framing against the pixel map.",
        "3. Assign the numbered pixel map texture before camera or render adjustments.",
        "",
        "## Screen Planes",
    ]
    lines.extend(f"- {screen.screen_name}: {screen.surface_type}, {screen_size_text(screen)}" for screen in screens)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_export_presets(project: ProjectCreate, path: Path) -> None:
    payload = {
        "project_name": project.project_name,
        "resolution": {"width": project.output_width, "height": project.output_height},
        "frame_rate": project.frame_rate,
        "codec_requirement": project.codec_requirement,
        "playback_software": project.playback_software,
        "presets": [
            {
                "name": "Master delivery",
                "container": "mov",
                "codec": project.codec_requirement,
                "pixel_format": "source",
                "audio": "none unless specified",
            },
            {
                "name": "H264 proxy",
                "container": "mp4",
                "codec": "h264",
                "pixel_format": "yuv420p",
                "audio": "aac",
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_ffmpeg_proxy_commands(project: ProjectCreate, path: Path) -> None:
    command = (
        "ffmpeg -i 06_Export/master.mov "
        f"-r {project.frame_rate} -s {project.output_width}x{project.output_height} "
        "-c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium "
        "06_Export/proxy_h264.mp4"
    )
    path.write_text(command + "\n", encoding="utf-8")


def write_onsite_runbook(project: ProjectCreate, screens: list[ScreenCreate], path: Path) -> None:
    lines = [
        f"# Onsite Runbook - {project.project_name}",
        "",
        "## Preflight",
        "- Confirm output resolution and processor routing.",
        "- Load the numbered pixel map and verify every physical surface.",
        "- Confirm backup playback machine uses the same frame rate and codec.",
        "",
        "## Screen Checklist",
    ]
    lines.extend(f"- {screen.screen_name}: verify origin {screen.x},{screen.y} and safe area {screen.safe_area_ratio}" for screen in screens)
    lines.extend(["", "## Notes", project.onsite_notes or "No onsite notes supplied."])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_playback_spec(project: ProjectCreate, path: Path) -> None:
    lines = [
        f"# Playback Spec - {project.project_name}",
        "",
        f"- Playback software: {project.playback_software}",
        f"- Codec: {project.codec_requirement}",
        f"- Resolution: {project.output_width} x {project.output_height}",
        f"- Frame rate: {project.frame_rate}fps",
        "- Audio: confirm per show file",
        "- File naming: PROJECT_SCREEN_VERSION_CODEC_RESOLUTION.ext",
    ]
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
    project_root = project_package_root(project, output_root)
    for dirname in PROJECT_DIRS:
        (project_root / dirname).mkdir(parents=True, exist_ok=True)

    write_qc_report(project, screens, project_root / "01_Analysis" / "qc_report.md")
    write_screen_spec(project, screens, project_root / "02_ScreenSpec" / "screen_spec.md")
    write_screen_spec_json(project, screens, project_root / "02_ScreenSpec" / "screen_spec.json")
    draw_pixel_map(project, screens, project_root / "03_PixelMap" / "project_pixelmap_full.png")
    draw_pixel_map(project, screens, project_root / "03_PixelMap" / "project_pixelmap_numbered.png", numbered=True)
    draw_pixel_map(project, screens, project_root / "03_PixelMap" / "project_pixelmap_safearea.png", safe_area=True)
    write_svg_mask(project, screens, project_root / "03_PixelMap" / "project_pixelmap_mask.svg")
    write_mapping_json(project, screens, project_root / "03_PixelMap" / "project_mapping.json")
    write_ae_readme(project, screens, project_root / "04_AE" / "README_AE.md")
    write_ae_jsx(project, screens, project_root / "04_AE" / "create_project.jsx")
    write_c4d_readme(project, screens, project_root / "05_C4D" / "README_C4D.md")
    write_c4d_script(project, screens, project_root / "05_C4D" / "create_stage_scene.py")
    write_export_presets(project, project_root / "06_Export" / "export_presets.json")
    write_ffmpeg_proxy_commands(project, project_root / "06_Export" / "ffmpeg_proxy_commands.txt")
    write_delivery_spec(project, screens, project_root / "07_Onsite" / "delivery_spec.md")
    write_onsite_runbook(project, screens, project_root / "07_Onsite" / "onsite_runbook.md")
    write_playback_spec(project, project_root / "07_Onsite" / "playback_spec.md")

    return list_project_artifacts(project_root)
