import { AlertTriangle, Crosshair, MonitorUp } from "lucide-react";

import type { Project, QCResult, Screen } from "./api";
import { pointsForScreen, safeAreaPoints, toSvgPoints } from "./stageGeometry";

interface StagePreviewProps {
  project: Project | null;
  screens: Screen[];
  qc: QCResult | null;
  copy: {
    title: string;
    outputCanvas: string;
    noScreens: string;
    safeArea: string;
    qcIssue: string;
    screenSurfaceCount: (count: number) => string;
  };
}

const palette = ["#22d3ee", "#f472b6", "#a3e635", "#facc15", "#c084fc", "#fb7185"];

export function StagePreview({ project, screens, qc, copy }: StagePreviewProps) {
  if (!project) return null;
  const issueScreens = new Set(qc?.issues.map((issue) => issue.screen_name).filter(Boolean) ?? []);

  return (
    <section className="panel stage-panel">
      <div className="panel-title"><Crosshair size={18} /><h3>{copy.title}</h3></div>
      <div className="stage-meta">
        <span>{copy.outputCanvas}: {project.output_width} x {project.output_height}</span>
        <span>{copy.screenSurfaceCount(screens.length)}</span>
      </div>
      <div className="stage-canvas-shell">
        <svg className="stage-canvas" viewBox={`0 0 ${project.output_width} ${project.output_height}`} role="img">
          <rect width={project.output_width} height={project.output_height} fill="#050608" />
          {screens.map((screen, index) => {
            const points = pointsForScreen(screen);
            const safePoints = safeAreaPoints(screen);
            const color = issueScreens.has(screen.screen_name) ? "#fb7185" : palette[index % palette.length];
            return (
              <g key={screen.id}>
                <polygon points={toSvgPoints(points)} fill="rgba(34,211,238,0.12)" stroke={color} strokeWidth="8" />
                <polygon points={toSvgPoints(safePoints)} fill="none" stroke="#fff" strokeDasharray="24 18" strokeWidth="5" />
                <text x={points[0][0] + 36} y={points[0][1] + 64} fill="#fff" fontSize="54" fontWeight="700">{index + 1}</text>
              </g>
            );
          })}
        </svg>
      </div>
      {screens.length ? (
        <div className="stage-legend">
          {screens.map((screen, index) => {
            const hasIssue = issueScreens.has(screen.screen_name);
            return (
              <div className={`stage-legend-item ${hasIssue ? "issue" : ""}`} key={screen.id}>
                {hasIssue ? <AlertTriangle size={14} /> : <MonitorUp size={14} />}
                <span>{index + 1}</span>
                <strong>{screen.screen_name}</strong>
                <small>{screen.surface_type}</small>
                <small>{copy.safeArea} {screen.safe_area_ratio}</small>
                {hasIssue ? <em>{copy.qcIssue}</em> : null}
              </div>
            );
          })}
        </div>
      ) : <p className="muted">{copy.noScreens}</p>}
    </section>
  );
}
