import { PointerEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Check,
  Crosshair,
  Download,
  Maximize2,
  MonitorUp,
  RotateCcw,
  Save,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

import type { Project, QCResult, Screen } from "./api";
import {
  clampPolygonPoint,
  clampRectangleToCanvas,
  Point,
  pointsForScreen,
  resizeRectangleToCanvas,
  safeAreaPoints,
  screenBounds,
  toSvgPoints,
} from "./stageGeometry";

interface StagePreviewProps {
  project: Project | null;
  screens: Screen[];
  qc: QCResult | null;
  selectedScreenId: number | null;
  packageStale: boolean;
  saving: boolean;
  onSelectScreen: (screenId: number | null) => void;
  onSaveScreen: (screen: Screen) => Promise<void>;
  copy: {
    title: string;
    outputCanvas: string;
    noScreens: string;
    safeArea: string;
    qcIssue: string;
    screenSurfaceCount: (count: number) => string;
    zoomIn: string;
    zoomOut: string;
    resetView: string;
    fitCanvas: string;
    exportPreviewPng: string;
    showGrid: string;
    showSafeArea: string;
    showScreenNumbers: string;
    showCoordinates: string;
    showDimensions: string;
    showLabels: string;
    selectedScreen: string;
    noScreenSelected: string;
    origin: string;
    dimensions: string;
    polygonBounds: string;
    saveEdits: string;
    cancelEdits: string;
    packageStale: string;
  };
}

interface CanvasView {
  zoom: number;
  panX: number;
  panY: number;
}

interface CanvasToggles {
  grid: boolean;
  safeArea: boolean;
  numbers: boolean;
  coordinates: boolean;
  dimensions: boolean;
  labels: boolean;
}

type DragState =
  | { kind: "pan"; pointerId: number; startSvg: Point; baseView: CanvasView }
  | { kind: "move-rectangle"; pointerId: number; startCanvas: Point; original: Screen }
  | { kind: "resize-rectangle"; pointerId: number; original: Screen }
  | { kind: "polygon-vertex"; pointerId: number; index: number; original: Screen };

const palette = ["#22d3ee", "#f472b6", "#a3e635", "#facc15", "#c084fc", "#fb7185"];
const defaultView: CanvasView = { zoom: 1, panX: 0, panY: 0 };
const defaultToggles: CanvasToggles = {
  grid: true,
  safeArea: true,
  numbers: true,
  coordinates: true,
  dimensions: true,
  labels: true,
};

export function StagePreview({
  project,
  screens,
  qc,
  selectedScreenId,
  packageStale,
  saving,
  onSelectScreen,
  onSaveScreen,
  copy,
}: StagePreviewProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const shellRef = useRef<HTMLDivElement | null>(null);
  const [view, setView] = useState<CanvasView>(defaultView);
  const [toggles, setToggles] = useState<CanvasToggles>(defaultToggles);
  const [draftScreen, setDraftScreen] = useState<Screen | null>(null);
  const [drag, setDrag] = useState<DragState | null>(null);
  const [tooltip, setTooltip] = useState<{ screenId: number; x: number; y: number } | null>(null);

  const selectedScreen = useMemo(
    () => screens.find((screen) => screen.id === selectedScreenId) ?? null,
    [screens, selectedScreenId],
  );

  useEffect(() => {
    setDraftScreen(selectedScreen ? cloneScreen(selectedScreen) : null);
  }, [selectedScreen]);

  if (!project) return null;

  const issueScreens = new Set(qc?.issues.map((issue) => issue.screen_name).filter(Boolean) ?? []);
  const displayScreens = screens.map((screen) => (draftScreen?.id === screen.id ? draftScreen : screen));
  const tooltipScreen = tooltip ? displayScreens.find((screen) => screen.id === tooltip.screenId) ?? null : null;
  const editorScreen = draftScreen ?? selectedScreen;
  const editorBounds = editorScreen ? screenBounds(editorScreen) : null;
  const draftDirty =
    Boolean(selectedScreen && draftScreen) &&
    JSON.stringify(screenToInput(selectedScreen as Screen)) !== JSON.stringify(screenToInput(draftScreen as Screen));

  function transformMatrix() {
    return `matrix(${view.zoom} 0 0 ${view.zoom} ${view.panX} ${view.panY})`;
  }

  function setToggle(key: keyof CanvasToggles) {
    setToggles((current) => ({ ...current, [key]: !current[key] }));
  }

  function zoomBy(multiplier: number) {
    setView((current) => ({ ...current, zoom: Math.min(6, Math.max(0.25, current.zoom * multiplier)) }));
  }

  function fitCanvas() {
    setView(defaultView);
  }

  function svgPoint(event: PointerEvent<SVGSVGElement | SVGElement>): Point {
    const svg = svgRef.current;
    if (!svg) return [0, 0];
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const matrix = svg.getScreenCTM()?.inverse();
    const next = matrix ? point.matrixTransform(matrix) : point;
    return [next.x, next.y];
  }

  function canvasPoint(event: PointerEvent<SVGSVGElement | SVGElement>): Point {
    const [x, y] = svgPoint(event);
    return [(x - view.panX) / view.zoom, (y - view.panY) / view.zoom];
  }

  function updateTooltip(event: PointerEvent<SVGElement>, screenId: number) {
    const shell = shellRef.current;
    if (!shell) return;
    const rect = shell.getBoundingClientRect();
    setTooltip({ screenId, x: event.clientX - rect.left + 12, y: event.clientY - rect.top + 12 });
  }

  function beginPan(event: PointerEvent<SVGSVGElement>) {
    const target = event.target as Element;
    if (target.getAttribute("data-pan-target") !== "true") return;
    event.currentTarget.setPointerCapture(event.pointerId);
    setDrag({ kind: "pan", pointerId: event.pointerId, startSvg: svgPoint(event), baseView: view });
  }

  function beginScreenPointer(event: PointerEvent<SVGElement>, screen: Screen) {
    event.stopPropagation();
    onSelectScreen(screen.id);
    setTooltip(null);

    if (screen.surface_type !== "rectangle") return;
    const working = draftScreen?.id === screen.id ? draftScreen : cloneScreen(screen);
    setDraftScreen(working);
    event.currentTarget.setPointerCapture(event.pointerId);
    setDrag({
      kind: "move-rectangle",
      pointerId: event.pointerId,
      startCanvas: canvasPoint(event),
      original: working,
    });
  }

  function beginResize(event: PointerEvent<SVGCircleElement>, screen: Screen) {
    event.stopPropagation();
    const working = draftScreen?.id === screen.id ? draftScreen : cloneScreen(screen);
    setDraftScreen(working);
    event.currentTarget.setPointerCapture(event.pointerId);
    setDrag({ kind: "resize-rectangle", pointerId: event.pointerId, original: working });
  }

  function beginVertexDrag(event: PointerEvent<SVGCircleElement>, screen: Screen, index: number) {
    event.stopPropagation();
    const working = draftScreen?.id === screen.id ? draftScreen : cloneScreen(screen);
    setDraftScreen(working);
    event.currentTarget.setPointerCapture(event.pointerId);
    setDrag({ kind: "polygon-vertex", pointerId: event.pointerId, index, original: working });
  }

  function handlePointerMove(event: PointerEvent<SVGSVGElement>) {
    if (!drag) return;

    if (drag.kind === "pan") {
      const [x, y] = svgPoint(event);
      setView({
        ...drag.baseView,
        panX: drag.baseView.panX + x - drag.startSvg[0],
        panY: drag.baseView.panY + y - drag.startSvg[1],
      });
      return;
    }

    const [x, y] = canvasPoint(event);
    if (drag.kind === "move-rectangle") {
      const dx = x - drag.startCanvas[0];
      const dy = y - drag.startCanvas[1];
      setDraftScreen(
        clampRectangleToCanvas(
          { ...drag.original, x: drag.original.x + dx, y: drag.original.y + dy },
          project.output_width,
          project.output_height,
        ),
      );
    }

    if (drag.kind === "resize-rectangle") {
      setDraftScreen(
        resizeRectangleToCanvas(
          { ...drag.original, width: x - drag.original.x, height: y - drag.original.y },
          project.output_width,
          project.output_height,
        ),
      );
    }

    if (drag.kind === "polygon-vertex") {
      const nextPoint = clampPolygonPoint([x, y], project.output_width, project.output_height);
      const polygon_points = drag.original.polygon_points.map((point, index) =>
        index === drag.index ? nextPoint : point,
      );
      setDraftScreen({ ...drag.original, polygon_points });
    }
  }

  function endPointer(event: PointerEvent<SVGSVGElement>) {
    if (drag?.pointerId === event.pointerId) {
      try {
        event.currentTarget.releasePointerCapture(event.pointerId);
      } catch {
        // Pointer capture may already be released by the browser.
      }
      setDrag(null);
    }
  }

  async function saveDraft() {
    if (!draftScreen) return;
    await onSaveScreen(draftScreen);
  }

  function cancelDraft() {
    setDraftScreen(selectedScreen ? cloneScreen(selectedScreen) : null);
  }

  function exportPreviewPng() {
    const svg = svgRef.current;
    if (!svg) return;

    const clone = svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.querySelectorAll(".editor-only").forEach((element) => element.remove());
    const source = new XMLSerializer().serializeToString(clone);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = project.output_width;
      canvas.height = project.output_height;
      const context = canvas.getContext("2d");
      if (!context) return;
      context.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      const link = document.createElement("a");
      link.download = `${project.slug}_stage_preview.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    };
    image.src = url;
  }

  return (
    <section className="panel stage-panel">
      <div className="panel-title">
        <Crosshair size={18} />
        <h3>{copy.title}</h3>
      </div>
      <div className="stage-meta">
        <span>{copy.outputCanvas}: {project.output_width} x {project.output_height}</span>
        <span>{copy.screenSurfaceCount(screens.length)}</span>
        {packageStale ? <span className="stage-stale"><AlertTriangle size={14} /> {copy.packageStale}</span> : null}
      </div>

      <div className="canvas-toolbar" aria-label={copy.title}>
        <div className="icon-button-group">
          <button type="button" className="icon-button" onClick={() => zoomBy(1.2)} title={copy.zoomIn} aria-label={copy.zoomIn}>
            <ZoomIn size={16} />
          </button>
          <button type="button" className="icon-button" onClick={() => zoomBy(1 / 1.2)} title={copy.zoomOut} aria-label={copy.zoomOut}>
            <ZoomOut size={16} />
          </button>
          <button type="button" className="icon-button" onClick={() => setView(defaultView)} title={copy.resetView} aria-label={copy.resetView}>
            <RotateCcw size={16} />
          </button>
          <button type="button" className="icon-button" onClick={fitCanvas} title={copy.fitCanvas} aria-label={copy.fitCanvas}>
            <Maximize2 size={16} />
          </button>
          <button type="button" className="icon-button" onClick={exportPreviewPng} title={copy.exportPreviewPng} aria-label={copy.exportPreviewPng}>
            <Download size={16} />
          </button>
        </div>
        <div className="canvas-toggles">
          <Toggle label={copy.showGrid} checked={toggles.grid} onChange={() => setToggle("grid")} />
          <Toggle label={copy.showSafeArea} checked={toggles.safeArea} onChange={() => setToggle("safeArea")} />
          <Toggle label={copy.showScreenNumbers} checked={toggles.numbers} onChange={() => setToggle("numbers")} />
          <Toggle label={copy.showCoordinates} checked={toggles.coordinates} onChange={() => setToggle("coordinates")} />
          <Toggle label={copy.showDimensions} checked={toggles.dimensions} onChange={() => setToggle("dimensions")} />
          <Toggle label={copy.showLabels} checked={toggles.labels} onChange={() => setToggle("labels")} />
        </div>
      </div>

      <div className="stage-canvas-shell" ref={shellRef}>
        <svg
          ref={svgRef}
          className={`stage-canvas ${drag?.kind === "pan" ? "panning" : ""}`}
          viewBox={`0 0 ${project.output_width} ${project.output_height}`}
          role="img"
          onPointerDown={beginPan}
          onPointerMove={handlePointerMove}
          onPointerUp={endPointer}
          onPointerCancel={endPointer}
          onPointerLeave={() => setTooltip(null)}
        >
          <rect data-pan-target="true" width={project.output_width} height={project.output_height} fill="#050608" />
          <g transform={transformMatrix()}>
            {toggles.grid ? <Grid width={project.output_width} height={project.output_height} /> : null}
            {displayScreens.map((screen, index) => {
              const points = pointsForScreen(screen);
              const safePoints = safeAreaPoints(screen);
              const bounds = screenBounds(screen);
              const color = issueScreens.has(screen.screen_name) ? "#fb7185" : palette[index % palette.length];
              const selected = selectedScreenId === screen.id;
              const labelX = bounds.minX + 20;
              const labelY = bounds.minY + 46;

              return (
                <g key={screen.id} className={selected ? "selected-screen" : ""}>
                  <polygon
                    points={toSvgPoints(points)}
                    fill={selected ? "rgba(250,204,21,0.18)" : "rgba(34,211,238,0.12)"}
                    stroke={selected ? "#facc15" : color}
                    strokeWidth="8"
                    vectorEffect="non-scaling-stroke"
                    onPointerDown={(event) => beginScreenPointer(event, screen)}
                    onPointerEnter={(event) => updateTooltip(event, screen.id)}
                    onPointerMove={(event) => updateTooltip(event, screen.id)}
                  />
                  {toggles.safeArea ? (
                    <polygon
                      points={toSvgPoints(safePoints)}
                      fill="none"
                      stroke="#fff"
                      strokeDasharray="24 18"
                      strokeWidth="5"
                      vectorEffect="non-scaling-stroke"
                      pointerEvents="none"
                    />
                  ) : null}
                  {toggles.numbers ? (
                    <text x={labelX} y={labelY} fill="#fff" fontSize="54" fontWeight="700" pointerEvents="none">
                      {index + 1}
                    </text>
                  ) : null}
                  {toggles.labels ? (
                    <text x={labelX + 72} y={labelY} fill="#e6edf5" fontSize="34" fontWeight="700" pointerEvents="none">
                      {screen.screen_name}
                    </text>
                  ) : null}
                  {toggles.coordinates ? (
                    <text x={labelX} y={labelY + 48} fill="#cbd5e1" fontSize="28" pointerEvents="none">
                      {copy.origin}: {Math.round(bounds.minX)}, {Math.round(bounds.minY)}
                    </text>
                  ) : null}
                  {toggles.dimensions ? (
                    <text x={labelX} y={labelY + 86} fill="#cbd5e1" fontSize="28" pointerEvents="none">
                      {copy.dimensions}: {Math.round(bounds.width)} x {Math.round(bounds.height)}
                    </text>
                  ) : null}
                  {selected && screen.surface_type === "rectangle" ? (
                    <circle
                      className="editor-only resize-handle"
                      cx={screen.x + screen.width}
                      cy={screen.y + screen.height}
                      r="20"
                      fill="#facc15"
                      stroke="#050608"
                      strokeWidth="6"
                      vectorEffect="non-scaling-stroke"
                      onPointerDown={(event) => beginResize(event, screen)}
                    />
                  ) : null}
                  {selected && screen.surface_type === "polygon"
                    ? screen.polygon_points.map(([x, y], pointIndex) => (
                        <circle
                          className="editor-only vertex-handle"
                          key={`${screen.id}-${pointIndex}`}
                          cx={x}
                          cy={y}
                          r="18"
                          fill="#facc15"
                          stroke="#050608"
                          strokeWidth="6"
                          vectorEffect="non-scaling-stroke"
                          onPointerDown={(event) => beginVertexDrag(event, screen, pointIndex)}
                        />
                      ))
                    : null}
                </g>
              );
            })}
          </g>
        </svg>

        {tooltipScreen ? (
          <div className="stage-tooltip" style={{ left: tooltip?.x, top: tooltip?.y }}>
            <strong>{tooltipScreen.screen_name}</strong>
            <span>{tooltipScreen.surface_type}</span>
            <span>{copy.origin}: {Math.round(screenBounds(tooltipScreen).minX)}, {Math.round(screenBounds(tooltipScreen).minY)}</span>
            <span>{tooltipScreen.surface_type === "polygon" ? copy.polygonBounds : copy.dimensions}: {Math.round(screenBounds(tooltipScreen).width)} x {Math.round(screenBounds(tooltipScreen).height)}</span>
            <span>{copy.safeArea}: {tooltipScreen.safe_area_ratio}</span>
            {tooltipScreen.notes ? <small>{tooltipScreen.notes}</small> : null}
          </div>
        ) : null}
      </div>

      <div className="stage-editor">
        {editorScreen && editorBounds ? (
          <>
            <div>
              <h4>{copy.selectedScreen}</h4>
              <strong>{editorScreen.screen_name}</strong>
              <span>{editorScreen.surface_type}</span>
              <span>{copy.origin}: {Math.round(editorBounds.minX)}, {Math.round(editorBounds.minY)}</span>
              <span>{copy.dimensions}: {Math.round(editorBounds.width)} x {Math.round(editorBounds.height)}</span>
            </div>
            <div className="editor-actions">
              <button className="primary-button" type="button" disabled={!draftDirty || saving} onClick={saveDraft}>
                <Save size={16} />
                {copy.saveEdits}
              </button>
              <button className="ghost-button compact" type="button" disabled={!draftDirty || saving} onClick={cancelDraft}>
                <RotateCcw size={16} />
                {copy.cancelEdits}
              </button>
            </div>
          </>
        ) : (
          <p className="muted">{screens.length ? copy.noScreenSelected : copy.noScreens}</p>
        )}
      </div>

      {screens.length ? (
        <div className="stage-legend">
          {displayScreens.map((screen, index) => {
            const hasIssue = issueScreens.has(screen.screen_name);
            const selected = selectedScreenId === screen.id;
            return (
              <button
                className={`stage-legend-item ${hasIssue ? "issue" : ""} ${selected ? "active" : ""}`}
                key={screen.id}
                type="button"
                onClick={() => onSelectScreen(screen.id)}
              >
                {hasIssue ? <AlertTriangle size={14} /> : selected ? <Check size={14} /> : <MonitorUp size={14} />}
                <span>{index + 1}</span>
                <strong>{screen.screen_name}</strong>
                <small>{screen.surface_type}</small>
                <small>{copy.safeArea} {screen.safe_area_ratio}</small>
                {hasIssue ? <em>{copy.qcIssue}</em> : null}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="muted">{copy.noScreens}</p>
      )}
    </section>
  );
}

function Grid({ width, height }: { width: number; height: number }) {
  const step = width >= 3000 ? 240 : 120;
  const vertical = [];
  const horizontal = [];
  for (let x = step; x < width; x += step) vertical.push(x);
  for (let y = step; y < height; y += step) horizontal.push(y);

  return (
    <g className="canvas-grid" pointerEvents="none">
      {vertical.map((x) => (
        <line key={`x-${x}`} x1={x} y1={0} x2={x} y2={height} />
      ))}
      {horizontal.map((y) => (
        <line key={`y-${y}`} x1={0} y1={y} x2={width} y2={y} />
      ))}
    </g>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label className="canvas-toggle">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span>{label}</span>
    </label>
  );
}

function cloneScreen(screen: Screen): Screen {
  return {
    ...screen,
    polygon_points: screen.polygon_points.map(([x, y]) => [x, y]),
  };
}

function screenToInput(screen: Screen) {
  return {
    screen_name: screen.screen_name,
    surface_type: screen.surface_type,
    x: screen.x,
    y: screen.y,
    width: screen.width,
    height: screen.height,
    polygon_points: screen.polygon_points,
    safe_area_ratio: screen.safe_area_ratio,
    notes: screen.notes,
  };
}
