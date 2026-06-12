export type SurfaceType = "rectangle" | "polygon";

export interface Project {
  id: number;
  slug: string;
  project_name: string;
  client_name: string;
  frame_rate: number;
  output_width: number;
  output_height: number;
  playback_software: string;
  codec_requirement: string;
  onsite_notes: string;
  output_path?: string | null;
}

export interface ProjectInput {
  project_name: string;
  client_name: string;
  frame_rate: number;
  output_width: number;
  output_height: number;
  playback_software: string;
  codec_requirement: string;
  onsite_notes: string;
}

export interface Screen {
  id: number;
  project_id: number;
  screen_name: string;
  surface_type: SurfaceType;
  x: number;
  y: number;
  width: number;
  height: number;
  polygon_points: number[][];
  safe_area_ratio: number;
  notes: string;
}

export type ScreenInput = Omit<Screen, "id" | "project_id">;

export interface QCIssue {
  code: string;
  severity: "error" | "warning";
  message: string;
  screen_name?: string | null;
}

export interface QCCheck {
  code: string;
  label: string;
  passed: boolean;
  severity: "info" | "warning" | "error";
  message: string;
}

export interface QCResult {
  passed: boolean;
  checks: QCCheck[];
  issues: QCIssue[];
}

export interface Artifact {
  label: string;
  path: string;
  kind: string;
  relative_path: string;
  created_at: string;
  size_bytes: number;
}

export interface GenerateResult {
  project: Project;
  artifacts: Artifact[];
  qc: QCResult;
}

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/projects"),
  createProject: (payload: ProjectInput) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  listScreens: (projectId: number) => request<Screen[]>(`/projects/${projectId}/screens`),
  createScreen: (projectId: number, payload: ScreenInput) =>
    request<Screen>(`/projects/${projectId}/screens`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateScreen: (projectId: number, screenId: number, payload: ScreenInput) =>
    request<Screen>(`/projects/${projectId}/screens/${screenId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getQc: (projectId: number) => request<QCResult>(`/projects/${projectId}/qc`),
  listArtifacts: (projectId: number) => request<Artifact[]>(`/projects/${projectId}/artifacts`),
  generate: (projectId: number) =>
    request<GenerateResult>(`/projects/${projectId}/generate`, { method: "POST" }),
  packageZipUrl: (projectId: number) => `${API_BASE}/projects/${projectId}/package.zip`,
  artifactDownloadUrl: (projectId: number, relativePath: string) =>
    `${API_BASE}/projects/${projectId}/artifacts/${relativePath
      .split("/")
      .map((part) => encodeURIComponent(part))
      .join("/")}`,
};
