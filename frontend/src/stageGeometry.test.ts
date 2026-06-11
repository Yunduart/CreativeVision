import { describe, expect, it } from "vitest";

import { pointsForScreen, safeAreaPoints, toSvgPoints } from "./stageGeometry";

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
});
