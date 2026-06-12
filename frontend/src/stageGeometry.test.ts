import { describe, expect, it } from "vitest";

import {
  clampPolygonPoint,
  clampRectangleToCanvas,
  pointsForScreen,
  resizeRectangleToCanvas,
  safeAreaPoints,
  screenBounds,
  toSvgPoints,
} from "./stageGeometry";

describe("stage geometry", () => {
  it("converts rectangle screens to polygon points", () => {
    const points = pointsForScreen({
      screen_name: "Main",
      surface_type: "rectangle",
      x: 10,
      y: 20,
      width: 100,
      height: 50,
      polygon_points: [],
      safe_area_ratio: 0.9,
    });

    expect(points).toEqual([
      [10, 20],
      [110, 20],
      [110, 70],
      [10, 70],
    ]);
  });

  it("uses polygon screen points directly", () => {
    const points = pointsForScreen({
      screen_name: "Diamond",
      surface_type: "polygon",
      x: 0,
      y: 0,
      width: 100,
      height: 100,
      polygon_points: [
        [50, 0],
        [100, 50],
        [50, 100],
        [0, 50],
      ],
      safe_area_ratio: 0.8,
    });

    expect(points).toEqual([
      [50, 0],
      [100, 50],
      [50, 100],
      [0, 50],
    ]);
  });

  it("scales safe area points toward the screen center", () => {
    const points = safeAreaPoints({
      screen_name: "Main",
      surface_type: "rectangle",
      x: 0,
      y: 0,
      width: 100,
      height: 50,
      polygon_points: [],
      safe_area_ratio: 0.8,
    });

    expect(points).toEqual([
      [10, 5],
      [90, 5],
      [90, 45],
      [10, 45],
    ]);
  });

  it("formats SVG point strings", () => {
    expect(toSvgPoints([[10, 20], [30, 40]])).toBe("10,20 30,40");
  });

  it("returns rectangle and polygon bounds for display sizing", () => {
    expect(screenBounds({
      screen_name: "Main",
      surface_type: "rectangle",
      x: 10,
      y: 20,
      width: 100,
      height: 50,
      polygon_points: [],
      safe_area_ratio: 0.9,
    })).toEqual({ minX: 10, minY: 20, maxX: 110, maxY: 70, width: 100, height: 50 });

    expect(screenBounds({
      screen_name: "Wedge",
      surface_type: "polygon",
      x: 0,
      y: 0,
      width: 0,
      height: 0,
      polygon_points: [[100, 50], [360, 120], [260, 310], [80, 250]],
      safe_area_ratio: 0.9,
    })).toEqual({ minX: 80, minY: 50, maxX: 360, maxY: 310, width: 280, height: 260 });
  });

  it("clamps rectangle moves and resizes inside the canvas with integer pixels", () => {
    expect(clampRectangleToCanvas({
      screen_name: "Main",
      surface_type: "rectangle",
      x: 760.8,
      y: -20.3,
      width: 300,
      height: 200,
      polygon_points: [],
      safe_area_ratio: 0.9,
    }, 1000, 500)).toMatchObject({ x: 700, y: 0, width: 300, height: 200 });

    expect(resizeRectangleToCanvas({
      screen_name: "Main",
      surface_type: "rectangle",
      x: 900,
      y: 420,
      width: 200,
      height: 120,
      polygon_points: [],
      safe_area_ratio: 0.9,
    }, 1000, 500)).toMatchObject({ x: 900, y: 420, width: 100, height: 80 });
  });

  it("clamps polygon vertices inside the canvas with integer pixels", () => {
    expect(clampPolygonPoint([1280.6, -30.2], 1280, 720)).toEqual([1280, 0]);
  });
});
