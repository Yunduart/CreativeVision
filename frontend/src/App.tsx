import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clapperboard,
  Download,
  FileCode2,
  FolderTree,
  Gauge,
  Layers3,
  MonitorUp,
  Play,
  Plus,
  RefreshCw,
} from "lucide-react";

import { api, Artifact, Project, ProjectInput, QCResult, Screen, ScreenInput } from "./api";
import { formatCreatedAt, formatFileSize, formatFrameRate } from "./formatters";
import { defaultLanguage, LanguageCode, languages, makeCopy } from "./i18n";
import { StagePreview } from "./StagePreview";

const defaultProject: ProjectInput = {
  project_name: "Graduation Stage Mapping Demo",
  client_name: "THE VISION",
  frame_rate: 25,
  output_width: 3840,
  output_height: 1080,
  playback_software: "Resolume Arena",
  codec_requirement: "DXV3",
  onsite_notes: "Confirm processor routing, output port order, and backup playback machine onsite.",
};

const defaultScreen: ScreenInput = {
  screen_name: "Main LED",
  surface_type: "rectangle",
  x: 0,
  y: 0,
  width: 1920,
  height: 1080,
  polygon_points: [],
  safe_area_ratio: 0.9,
  notes: "Primary canvas for hero visuals.",
};

function parsePolygonPoints(value: string): number[][] {
  if (!value.trim()) return [];
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [x, y] = line.split(",").map((part) => Number(part.trim()));
      return [x, y];
    })
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
}

function formatPoints(points: number[][]): string {
  return points.map(([x, y]) => `${x}, ${y}`).join("\n");
}

function useActiveProject(projects: Project[]) {
  const [activeId, setActiveId] = useState<number | null>(null);
  const activeProject = useMemo(
    () => projects.find((project) => project.id === activeId) ?? projects[0] ?? null,
    [activeId, projects],
  );

  useEffect(() => {
    if (!activeId && projects[0]) setActiveId(projects[0].id);
  }, [activeId, projects]);

  return { activeProject, setActiveId };
}

export function App() {
  const [language, setLanguage] = useState<LanguageCode>(() => {
    const stored = window.localStorage.getItem("vj-os.language");
    return stored === "zh" || stored === "en" ? stored : defaultLanguage;
  });
  const copy = useMemo(() => makeCopy(language), [language]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [screens, setScreens] = useState<Screen[]>([]);
  const [qc, setQc] = useState<QCResult | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [projectForm, setProjectForm] = useState<ProjectInput>(defaultProject);
  const [screenForm, setScreenForm] = useState<ScreenInput>(defaultScreen);
  const [polygonDraft, setPolygonDraft] = useState("");
  const [status, setStatus] = useState(copy.loadingWorkspace);
  const [busy, setBusy] = useState(false);
  const { activeProject, setActiveId } = useActiveProject(projects);

  useEffect(() => {
    window.localStorage.setItem("vj-os.language", language);
    setStatus(copy.loadedProjects(projects.length));
  }, [copy, language]);

  async function loadProjects() {
    setBusy(true);
    try {
      const nextProjects = await api.listProjects();
      setProjects(nextProjects);
      setStatus(copy.loadedProjects(nextProjects.length));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : copy.loadProjectsFailed);
    } finally {
      setBusy(false);
    }
  }

  async function loadProjectDetail(projectId: number) {
    const [nextScreens, nextQc, nextArtifacts] = await Promise.all([
      api.listScreens(projectId),
      api.getQc(projectId),
      api.listArtifacts(projectId),
    ]);
    setScreens(nextScreens);
    setQc(nextQc);
    setArtifacts(nextArtifacts);
  }

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (!activeProject) return;
    loadProjectDetail(activeProject.id).catch((error) => {
      setStatus(error instanceof Error ? error.message : copy.loadProjectDetailFailed);
    });
  }, [activeProject?.id]);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      const project = await api.createProject(projectForm);
      const nextProjects = await api.listProjects();
      setProjects(nextProjects);
      setActiveId(project.id);
      await loadProjectDetail(project.id);
      setStatus(copy.createdProject(project.project_name));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : copy.createProjectFailed);
    } finally {
      setBusy(false);
    }
  }

  async function createScreen(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeProject) return;
    setBusy(true);
    try {
      const payload = {
        ...screenForm,
        polygon_points: screenForm.surface_type === "polygon" ? parsePolygonPoints(polygonDraft) : [],
      };
      await api.createScreen(activeProject.id, payload);
      await loadProjectDetail(activeProject.id);
      setStatus(copy.addedScreen(payload.screen_name));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : copy.addScreenFailed);
    } finally {
      setBusy(false);
    }
  }

  async function runGeneration() {
    if (!activeProject) return;
    setBusy(true);
    try {
      const result = await api.generate(activeProject.id);
      setArtifacts(result.artifacts);
      setQc(result.qc);
      const nextProjects = await api.listProjects();
      setProjects(nextProjects);
      await loadProjectDetail(activeProject.id);
      setStatus(copy.generatedFiles(result.artifacts.length, result.project.output_path));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : copy.generationFailed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Layers3 size={22} />
          </div>
          <div>
            <h1>VJ Project OS</h1>
            <p>{copy.brandSubtitle}</p>
          </div>
        </div>

        <button className="ghost-button" type="button" onClick={loadProjects} disabled={busy}>
          <RefreshCw size={16} />
          {copy.refreshProjects}
        </button>

        <div className="project-list">
          {projects.map((project) => (
            <button
              className={`project-button ${activeProject?.id === project.id ? "active" : ""}`}
              key={project.id}
              type="button"
              onClick={() => setActiveId(project.id)}
            >
              <span>{project.project_name}</span>
              <small>{project.output_width} x {project.output_height} / {formatFrameRate(project.frame_rate)}</small>
            </button>
          ))}
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <div className="eyebrow">{copy.localMvp}</div>
            <h2>{activeProject ? activeProject.project_name : copy.createFirstProject}</h2>
          </div>
          <div className="topbar-actions">
            <div className="language-toggle" aria-label="Language switcher">
              {languages.map((item) => (
                <button
                  key={item.code}
                  type="button"
                  className={language === item.code ? "active" : ""}
                  onClick={() => setLanguage(item.code)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <div className="status-pill">{busy ? copy.working : status}</div>
          </div>
        </header>

        <section className="metrics">
          <Metric icon={<MonitorUp size={18} />} label={copy.screens} value={screens.length.toString()} />
          <Metric
            icon={<Gauge size={18} />}
            label={copy.qc}
            value={qc ? (qc.passed ? copy.pass : copy.issues(qc.issues.length)) : copy.notRun}
          />
          <Metric icon={<FileCode2 size={18} />} label={copy.artifacts} value={artifacts.length.toString()} />
          <Metric icon={<Clapperboard size={18} />} label={copy.codec} value={activeProject?.codec_requirement ?? "-"} />
        </section>

        <StagePreview
          project={activeProject}
          screens={screens}
          qc={qc}
          copy={{
            title: copy.stagePreview,
            outputCanvas: copy.outputCanvas,
            noScreens: copy.noScreens,
            safeArea: copy.safeArea,
            qcIssue: copy.qcIssue,
            screenSurfaceCount: copy.screenSurfaceCount,
          }}
        />

        <div className="grid two">
          <section className="panel">
            <div className="panel-title">
              <FolderTree size={18} />
              <h3>{copy.createProject}</h3>
            </div>
            <form className="form-grid" onSubmit={createProject}>
              <Field label={copy.projectName}>
                <input value={projectForm.project_name} onChange={(event) => setProjectForm({ ...projectForm, project_name: event.target.value })} />
              </Field>
              <Field label={copy.clientName}>
                <input value={projectForm.client_name} onChange={(event) => setProjectForm({ ...projectForm, client_name: event.target.value })} />
              </Field>
              <Field label={copy.frameRate}>
                <input type="number" value={projectForm.frame_rate} onChange={(event) => setProjectForm({ ...projectForm, frame_rate: Number(event.target.value) })} />
              </Field>
              <Field label={copy.outputWidth}>
                <input type="number" value={projectForm.output_width} onChange={(event) => setProjectForm({ ...projectForm, output_width: Number(event.target.value) })} />
              </Field>
              <Field label={copy.outputHeight}>
                <input type="number" value={projectForm.output_height} onChange={(event) => setProjectForm({ ...projectForm, output_height: Number(event.target.value) })} />
              </Field>
              <Field label={copy.playbackSoftware}>
                <input value={projectForm.playback_software} onChange={(event) => setProjectForm({ ...projectForm, playback_software: event.target.value })} />
              </Field>
              <Field label={copy.codec}>
                <input value={projectForm.codec_requirement} onChange={(event) => setProjectForm({ ...projectForm, codec_requirement: event.target.value })} />
              </Field>
              <Field label={copy.onsiteNotes} wide>
                <textarea value={projectForm.onsite_notes} onChange={(event) => setProjectForm({ ...projectForm, onsite_notes: event.target.value })} />
              </Field>
              <button className="primary-button" type="submit" disabled={busy}>
                <Plus size={16} />
                {copy.createProject}
              </button>
            </form>
          </section>

          <section className="panel">
            <div className="panel-title">
              <MonitorUp size={18} />
              <h3>{copy.addScreenSurface}</h3>
            </div>
            <form className="form-grid" onSubmit={createScreen}>
              <Field label={copy.screenName}>
                <input value={screenForm.screen_name} onChange={(event) => setScreenForm({ ...screenForm, screen_name: event.target.value })} />
              </Field>
              <Field label={copy.surfaceType}>
                <select
                  value={screenForm.surface_type}
                  onChange={(event) => {
                    const surfaceType = event.target.value as ScreenInput["surface_type"];
                    setScreenForm({ ...screenForm, surface_type: surfaceType });
                    if (surfaceType === "polygon" && !polygonDraft) {
                      setPolygonDraft(formatPoints([[2600, 140], [2920, 460], [2600, 780], [2280, 460]]));
                    }
                  }}
                >
                  <option value="rectangle">{copy.rectangle}</option>
                  <option value="polygon">{copy.polygonIrregular}</option>
                </select>
              </Field>
              <Field label="X">
                <input type="number" value={screenForm.x} onChange={(event) => setScreenForm({ ...screenForm, x: Number(event.target.value) })} />
              </Field>
              <Field label="Y">
                <input type="number" value={screenForm.y} onChange={(event) => setScreenForm({ ...screenForm, y: Number(event.target.value) })} />
              </Field>
              <Field label={copy.width}>
                <input type="number" value={screenForm.width} onChange={(event) => setScreenForm({ ...screenForm, width: Number(event.target.value) })} />
              </Field>
              <Field label={copy.height}>
                <input type="number" value={screenForm.height} onChange={(event) => setScreenForm({ ...screenForm, height: Number(event.target.value) })} />
              </Field>
              <Field label={copy.safeAreaRatio}>
                <input
                  type="number"
                  min="0.1"
                  max="1"
                  step="0.01"
                  value={screenForm.safe_area_ratio}
                  onChange={(event) => setScreenForm({ ...screenForm, safe_area_ratio: Number(event.target.value) })}
                />
              </Field>
              {screenForm.surface_type === "polygon" ? (
                <Field label={copy.polygonPoints} wide>
                  <textarea value={polygonDraft} onChange={(event) => setPolygonDraft(event.target.value)} />
                </Field>
              ) : null}
              <Field label={copy.notes} wide>
                <textarea value={screenForm.notes} onChange={(event) => setScreenForm({ ...screenForm, notes: event.target.value })} />
              </Field>
              <button className="primary-button" type="submit" disabled={!activeProject || busy}>
                <Plus size={16} />
                {copy.addScreen}
              </button>
            </form>
          </section>
        </div>

        <div className="grid two">
          <section className="panel">
            <div className="panel-title">
              <Gauge size={18} />
              <h3>{copy.qcChecker}</h3>
            </div>
            <div className="qc-state">
              {qc?.passed ? <CheckCircle2 size={22} /> : <AlertTriangle size={22} />}
              <span>{qc ? (qc.passed ? copy.allChecksPassed : copy.issueFound(qc.issues.length)) : copy.qcNotRun}</span>
            </div>
            <div className="check-list" aria-label={copy.qcChecklist}>
              {qc?.checks?.length ? (
                qc.checks.map((check) => (
                  <div className={`check-row ${check.passed ? "pass" : check.severity}`} key={check.code}>
                    {check.passed ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                    <div>
                      <strong>{check.label}</strong>
                      <span>{check.message}</span>
                    </div>
                  </div>
                ))
              ) : null}
            </div>
            <div className="issue-list">
              {qc?.issues.length ? (
                qc.issues.map((issue, index) => (
                  <div className={`issue ${issue.severity}`} key={`${issue.code}-${index}`}>
                    <strong>{issue.code}</strong>
                    <span>{issue.screen_name ? `${issue.screen_name}: ` : ""}{issue.message}</span>
                  </div>
                ))
              ) : (
                <p className="muted">{copy.qcDescription}</p>
              )}
            </div>
            <button className="primary-button" type="button" onClick={runGeneration} disabled={!activeProject || busy}>
              <Play size={16} />
              {copy.generatePackage}
            </button>
          </section>

          <section className="panel">
            <div className="panel-title">
              <FileCode2 size={18} />
              <h3>{copy.generatedArtifacts}</h3>
            </div>
            {activeProject && artifacts.length ? (
              <a className="download-link package-download" href={api.packageZipUrl(activeProject.id)}>
                <Download size={16} />
                {copy.downloadZip}
              </a>
            ) : null}
            <div className="artifact-table" role="table" aria-label={copy.generatedArtifacts}>
              {artifacts.length ? (
                <>
                  <div className="artifact-row artifact-header" role="row">
                    <span>{copy.artifactLabel}</span>
                    <span>{copy.artifactType}</span>
                    <span>{copy.artifactPath}</span>
                    <span>{copy.artifactSize}</span>
                    <span>{copy.artifactCreated}</span>
                    <span>{copy.artifactAction}</span>
                  </div>
                  {artifacts.map((artifact) => (
                    <div className="artifact-row" role="row" key={artifact.relative_path}>
                      <strong>{copy.artifactLabels[artifact.label] ?? artifact.label}</strong>
                      <span>{artifact.kind}</span>
                      <code>{artifact.relative_path}</code>
                      <span>{formatFileSize(artifact.size_bytes)}</span>
                      <span>{formatCreatedAt(artifact.created_at)}</span>
                      {activeProject ? (
                        <a className="download-link" href={api.artifactDownloadUrl(activeProject.id, artifact.relative_path)}>
                          <Download size={14} />
                          {copy.download}
                        </a>
                      ) : null}
                    </div>
                  ))}
                </>
              ) : (
                <p className="muted">{copy.artifactEmpty}</p>
              )}
            </div>
          </section>
        </div>

        <section className="panel">
          <div className="panel-title">
            <MonitorUp size={18} />
            <h3>{copy.screenSurfaces}</h3>
          </div>
          <div className="screen-table">
            {screens.map((screen) => (
              <div className="screen-row" key={screen.id}>
                <strong>{screen.screen_name}</strong>
                <span>{screen.surface_type}</span>
                <span>{screen.x}, {screen.y}</span>
                <span>{screen.width} x {screen.height}</span>
                <span>{copy.safePrefix} {screen.safe_area_ratio}</span>
                <small>{screen.notes}</small>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="metric">
      <div>{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Field({ label, children, wide = false }: { label: string; children: ReactNode; wide?: boolean }) {
  return (
    <label className={`field ${wide ? "wide" : ""}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}
