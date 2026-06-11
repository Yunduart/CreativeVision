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

function roundPoint(value: number): number {
  return Math.round(value * 100) / 100;
}
