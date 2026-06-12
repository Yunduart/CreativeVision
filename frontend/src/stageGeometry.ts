import type { SurfaceType } from "./api";

export type Point = [number, number];

export interface StageScreenGeometry {
  screen_name: string;
  surface_type: SurfaceType;
  x: number;
  y: number;
  width: number;
  height: number;
  polygon_points: number[][];
  safe_area_ratio: number;
}

export function pointsForScreen(screen: StageScreenGeometry): Point[] {
  if (screen.surface_type === "polygon" && screen.polygon_points.length >= 3) {
    return screen.polygon_points.map(([x, y]) => [x, y]);
  }

  return [
    [screen.x, screen.y],
    [screen.x + screen.width, screen.y],
    [screen.x + screen.width, screen.y + screen.height],
    [screen.x, screen.y + screen.height],
  ];
}

export function safeAreaPoints(screen: StageScreenGeometry): Point[] {
  const points = pointsForScreen(screen);
  const bounds = boundsForPoints(points);
  const centerX = bounds.minX + (bounds.maxX - bounds.minX) / 2;
  const centerY = bounds.minY + (bounds.maxY - bounds.minY) / 2;

  return points.map(([x, y]) => [
    roundPoint(centerX + (x - centerX) * screen.safe_area_ratio),
    roundPoint(centerY + (y - centerY) * screen.safe_area_ratio),
  ]);
}

export function toSvgPoints(points: Point[]): string {
  return points.map(([x, y]) => `${x},${y}`).join(" ");
}

export function boundsForPoints(points: Point[]) {
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
  };
}

export function screenBounds(screen: StageScreenGeometry) {
  const bounds = boundsForPoints(pointsForScreen(screen));
  return {
    ...bounds,
    width: bounds.maxX - bounds.minX,
    height: bounds.maxY - bounds.minY,
  };
}

export function clampRectangleToCanvas<T extends StageScreenGeometry>(
  screen: T,
  canvasWidth: number,
  canvasHeight: number,
): T {
  const width = Math.max(1, Math.min(roundPixel(screen.width), canvasWidth));
  const height = Math.max(1, Math.min(roundPixel(screen.height), canvasHeight));
  return {
    ...screen,
    x: clampPixel(screen.x, 0, canvasWidth - width),
    y: clampPixel(screen.y, 0, canvasHeight - height),
    width,
    height,
  };
}

export function resizeRectangleToCanvas<T extends StageScreenGeometry>(
  screen: T,
  canvasWidth: number,
  canvasHeight: number,
): T {
  const x = clampPixel(screen.x, 0, Math.max(0, canvasWidth - 1));
  const y = clampPixel(screen.y, 0, Math.max(0, canvasHeight - 1));
  return {
    ...screen,
    x,
    y,
    width: Math.max(1, Math.min(roundPixel(screen.width), canvasWidth - x)),
    height: Math.max(1, Math.min(roundPixel(screen.height), canvasHeight - y)),
  };
}

export function clampPolygonPoint(point: Point, canvasWidth: number, canvasHeight: number): Point {
  return [clampPixel(point[0], 0, canvasWidth), clampPixel(point[1], 0, canvasHeight)];
}

function clampPixel(value: number, min: number, max: number): number {
  return Math.min(Math.max(roundPixel(value), min), max);
}

function roundPixel(value: number): number {
  return Math.round(value);
}

function roundPoint(value: number): number {
  return Math.round(value * 100) / 100;
}
