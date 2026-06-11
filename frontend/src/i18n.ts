export type LanguageCode = "en" | "zh";

export const defaultLanguage: LanguageCode = "en";
export const languages: Array<{ code: LanguageCode; label: string }> = [
  { code: "en", label: "EN" },
  { code: "zh", label: "\u4e2d\u6587" },
];

export interface Copy {
  brandSubtitle: string;
  refreshProjects: string;
  localMvp: string;
  createFirstProject: string;
  working: string;
  screens: string;
  qc: string;
  artifacts: string;
  codec: string;
  pass: string;
  issues: (count: number) => string;
  notRun: string;
  createProject: string;
  projectName: string;
  clientName: string;
  frameRate: string;
  outputWidth: string;
  outputHeight: string;
  playbackSoftware: string;
  onsiteNotes: string;
  addScreenSurface: string;
  screenName: string;
  surfaceType: string;
  rectangle: string;
  polygonIrregular: string;
  width: string;
  height: string;
  safeAreaRatio: string;
  polygonPoints: string;
  notes: string;
  addScreen: string;
  qcChecker: string;
  allChecksPassed: string;
  issueFound: (count: number) => string;
  qcNotRun: string;
  qcDescription: string;
  generatePackage: string;
  generatedArtifacts: string;
  artifactEmpty: string;
  artifactLabel: string;
  artifactType: string;
  artifactPath: string;
  artifactSize: string;
  artifactCreated: string;
  artifactAction: string;
  download: string;
  downloadZip: string;
  screenSurfaces: string;
  stagePreview: string;
  outputCanvas: string;
  noScreens: string;
  safeArea: string;
  qcIssue: string;
  qcChecklist: string;
  screenSurfaceCount: (count: number) => string;
  safePrefix: string;
  loadingWorkspace: string;
  loadedProjects: (count: number) => string;
  loadProjectsFailed: string;
  loadProjectDetailFailed: string;
  createdProject: (name: string) => string;
  createProjectFailed: string;
  addedScreen: (name: string) => string;
  addScreenFailed: string;
  generatedFiles: (count: number, path: string | null | undefined) => string;
  generationFailed: string;
  artifactLabels: Record<string, string>;
}

const artifactLabelsEn: Record<string, string> = {
  "QC report": "QC report",
  "Screen spec": "Screen spec",
  "Screen spec JSON": "Screen spec JSON",
  "Full pixel map": "Full pixel map",
  "Numbered pixel map": "Numbered pixel map",
  "Safe area pixel map": "Safe area pixel map",
  "SVG mask": "SVG mask",
  "Mapping JSON": "Mapping JSON",
  "AE README": "AE README",
  "AE JSX script": "AE JSX script",
  "C4D README": "C4D README",
  "C4D Python script": "C4D Python script",
  "Export presets": "Export presets",
  "FFmpeg proxy commands": "FFmpeg proxy commands",
  "Delivery spec": "Delivery spec",
  "Onsite runbook": "Onsite runbook",
  "Playback spec": "Playback spec",
};

const artifactLabelsZh: Record<string, string> = {
  "QC report": "QC \u62a5\u544a",
  "Screen spec": "\u5c4f\u5e55\u89c4\u683c",
  "Screen spec JSON": "\u5c4f\u5e55\u89c4\u683c JSON",
  "Full pixel map": "\u5b8c\u6574\u50cf\u7d20\u56fe",
  "Numbered pixel map": "\u5e26\u7f16\u53f7\u50cf\u7d20\u56fe",
  "Safe area pixel map": "\u5b89\u5168\u533a\u50cf\u7d20\u56fe",
  "SVG mask": "SVG \u906e\u7f69",
  "Mapping JSON": "Mapping JSON",
  "AE README": "AE README",
  "AE JSX script": "AE JSX \u811a\u672c",
  "C4D README": "C4D README",
  "C4D Python script": "C4D Python \u811a\u672c",
  "Export presets": "\u5bfc\u51fa\u9884\u8bbe",
  "FFmpeg proxy commands": "FFmpeg \u4ee3\u7406\u547d\u4ee4",
  "Delivery spec": "\u4ea4\u4ed8\u89c4\u683c",
  "Onsite runbook": "\u73b0\u573a\u6267\u884c\u624b\u518c",
  "Playback spec": "\u64ad\u653e\u89c4\u683c",
};

export function makeCopy(language: LanguageCode): Copy {
  if (language === "zh") {
    return {
      brandSubtitle: "\u821e\u53f0\u89c6\u89c9\u751f\u4ea7\u63a7\u5236\u53f0",
      refreshProjects: "\u5237\u65b0\u9879\u76ee",
      localMvp: "\u672c\u5730 MVP",
      createFirstProject: "\u521b\u5efa\u7b2c\u4e00\u4e2a\u9879\u76ee",
      working: "\u5904\u7406\u4e2d...",
      screens: "\u5c4f\u5e55",
      qc: "\u8d28\u68c0",
      artifacts: "\u4ea7\u7269",
      codec: "\u7f16\u7801",
      pass: "\u901a\u8fc7",
      issues: (count) => `${count} \u4e2a\u95ee\u9898`,
      notRun: "\u672a\u8fd0\u884c",
      createProject: "\u521b\u5efa\u9879\u76ee",
      projectName: "\u9879\u76ee\u540d\u79f0",
      clientName: "\u5ba2\u6237\u540d\u79f0",
      frameRate: "\u5e27\u7387",
      outputWidth: "\u8f93\u51fa\u5bbd\u5ea6",
      outputHeight: "\u8f93\u51fa\u9ad8\u5ea6",
      playbackSoftware: "\u64ad\u653e\u8f6f\u4ef6",
      onsiteNotes: "\u73b0\u573a\u5907\u6ce8",
      addScreenSurface: "\u6dfb\u52a0\u5c4f\u5e55\u8868\u9762",
      screenName: "\u5c4f\u5e55\u540d\u79f0",
      surfaceType: "\u8868\u9762\u7c7b\u578b",
      rectangle: "\u77e9\u5f62",
      polygonIrregular: "\u591a\u8fb9\u5f62 / \u5f02\u5f62",
      width: "\u5bbd\u5ea6",
      height: "\u9ad8\u5ea6",
      safeAreaRatio: "\u5b89\u5168\u533a\u6bd4\u4f8b",
      polygonPoints: "\u591a\u8fb9\u5f62\u70b9\u4f4d",
      notes: "\u5907\u6ce8",
      addScreen: "\u6dfb\u52a0\u5c4f\u5e55",
      qcChecker: "\u8d28\u68c0\u68c0\u67e5",
      allChecksPassed: "\u5168\u90e8\u68c0\u67e5\u901a\u8fc7",
      issueFound: (count) => `\u53d1\u73b0 ${count} \u4e2a\u95ee\u9898`,
      qcNotRun: "\u8d28\u68c0\u5c1a\u672a\u8fd0\u884c",
      qcDescription: "\u68c0\u67e5\u5c3a\u5bf8\u3001\u753b\u5e03\u8fb9\u754c\u3001\u5c4f\u5e55\u91cd\u53e0\u548c\u7f3a\u5931\u5b57\u6bb5\u3002",
      generatePackage: "\u751f\u6210\u5236\u4f5c\u5305",
      generatedArtifacts: "\u751f\u6210\u4ea7\u7269",
      artifactEmpty: "\u751f\u6210\u5236\u4f5c\u5305\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a\u6587\u4ef6\u6e05\u5355\u548c\u4e0b\u8f7d\u5165\u53e3\u3002",
      artifactLabel: "\u540d\u79f0",
      artifactType: "\u7c7b\u578b",
      artifactPath: "\u76f8\u5bf9\u8def\u5f84",
      artifactSize: "\u5927\u5c0f",
      artifactCreated: "\u521b\u5efa\u65f6\u95f4",
      artifactAction: "\u64cd\u4f5c",
      download: "\u4e0b\u8f7d",
      downloadZip: "\u4e0b\u8f7d ZIP",
      screenSurfaces: "\u5c4f\u5e55\u8868\u9762",
      stagePreview: "\u821e\u53f0\u753b\u5e03\u9884\u89c8",
      outputCanvas: "\u8f93\u51fa\u753b\u5e03",
      noScreens: "\u6dfb\u52a0\u5c4f\u5e55\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a mapping \u9884\u89c8\u3002",
      safeArea: "\u5b89\u5168\u533a",
      qcIssue: "\u8d28\u68c0\u95ee\u9898",
      qcChecklist: "\u8d28\u68c0\u6e05\u5355",
      screenSurfaceCount: (count) => `${count} \u4e2a\u5c4f\u5e55\u8868\u9762`,
      safePrefix: "\u5b89\u5168\u533a",
      loadingWorkspace: "\u6b63\u5728\u52a0\u8f7d\u672c\u5730\u5de5\u4f5c\u533a...",
      loadedProjects: (count) => `\u5df2\u52a0\u8f7d ${count} \u4e2a\u9879\u76ee\u3002`,
      loadProjectsFailed: "\u52a0\u8f7d\u9879\u76ee\u5931\u8d25\u3002",
      loadProjectDetailFailed: "\u52a0\u8f7d\u9879\u76ee\u8be6\u60c5\u5931\u8d25\u3002",
      createdProject: (name) => `\u5df2\u521b\u5efa\u9879\u76ee ${name}\u3002`,
      createProjectFailed: "\u521b\u5efa\u9879\u76ee\u5931\u8d25\u3002",
      addedScreen: (name) => `\u5df2\u6dfb\u52a0\u5c4f\u5e55 ${name}\u3002`,
      addScreenFailed: "\u6dfb\u52a0\u5c4f\u5e55\u5931\u8d25\u3002",
      generatedFiles: (count, path) => `\u5df2\u751f\u6210 ${count} \u4e2a\u6587\u4ef6\u5230 ${path ?? "\u8f93\u51fa\u76ee\u5f55"}\u3002`,
      generationFailed: "\u751f\u6210\u5931\u8d25\u3002",
      artifactLabels: artifactLabelsZh,
    };
  }

  return {
    brandSubtitle: "Stage visual production console",
    refreshProjects: "Refresh projects",
    localMvp: "Local MVP",
    createFirstProject: "Create the first project",
    working: "Working...",
    screens: "Screens",
    qc: "QC",
    artifacts: "Artifacts",
    codec: "Codec",
    pass: "Pass",
    issues: (count) => `${count} issues`,
    notRun: "Not run",
    createProject: "Create Project",
    projectName: "Project name",
    clientName: "Client name",
    frameRate: "Frame rate",
    outputWidth: "Output width",
    outputHeight: "Output height",
    playbackSoftware: "Playback software",
    onsiteNotes: "Onsite notes",
    addScreenSurface: "Add Screen Surface",
    screenName: "Screen name",
    surfaceType: "Surface type",
    rectangle: "Rectangle",
    polygonIrregular: "Polygon / irregular",
    width: "Width",
    height: "Height",
    safeAreaRatio: "Safe area ratio",
    polygonPoints: "Polygon points",
    notes: "Notes",
    addScreen: "Add screen",
    qcChecker: "QC Checker",
    allChecksPassed: "All checks passed",
    issueFound: (count) => `${count} issue(s) found`,
    qcNotRun: "QC has not run",
    qcDescription: "Checks cover dimensions, canvas bounds, overlaps, and missing fields.",
    generatePackage: "Generate production package",
    generatedArtifacts: "Generated Artifacts",
    artifactEmpty: "Generate a package to show files and download actions here.",
    artifactLabel: "Label",
    artifactType: "Type",
    artifactPath: "Relative path",
    artifactSize: "Size",
    artifactCreated: "Created",
    artifactAction: "Action",
    download: "Download",
    downloadZip: "Download ZIP",
    screenSurfaces: "Screen Surfaces",
    stagePreview: "Stage Canvas Preview",
    outputCanvas: "Output canvas",
    noScreens: "Add screens to see the mapping preview here.",
    safeArea: "safe",
    qcIssue: "QC issue",
    qcChecklist: "QC Checklist",
    screenSurfaceCount: (count) => `${count} screen surface${count === 1 ? "" : "s"}`,
    safePrefix: "safe",
    loadingWorkspace: "Loading local workspace...",
    loadedProjects: (count) => `Loaded ${count} project${count === 1 ? "" : "s"}.`,
    loadProjectsFailed: "Failed to load projects.",
    loadProjectDetailFailed: "Failed to load project detail.",
    createdProject: (name) => `Created project ${name}.`,
    createProjectFailed: "Failed to create project.",
    addedScreen: (name) => `Added screen ${name}.`,
    addScreenFailed: "Failed to add screen.",
    generatedFiles: (count, path) => `Generated ${count} files into ${path}.`,
    generationFailed: "Generation failed.",
    artifactLabels: artifactLabelsEn,
  };
}
