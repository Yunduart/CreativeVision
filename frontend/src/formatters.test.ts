import { describe, expect, it } from "vitest";

import { formatFileSize, formatFrameRate } from "./formatters";

describe("production package formatters", () => {
  it("formats frame rates without padding artifacts", () => {
    expect(formatFrameRate(25)).toBe("25fps");
    expect(formatFrameRate(30)).toBe("30fps");
    expect(formatFrameRate(29.97)).toBe("29.97fps");
  });

  it("formats artifact file sizes for review tables", () => {
    expect(formatFileSize(0)).toBe("0 B");
    expect(formatFileSize(512)).toBe("512 B");
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(2_621_440)).toBe("2.5 MB");
  });
});
