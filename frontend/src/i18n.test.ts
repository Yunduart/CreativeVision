import { describe, expect, it } from "vitest";

import { defaultLanguage, languages, makeCopy } from "./i18n";

describe("i18n copy", () => {
  it("defines English as the default language and Chinese as an option", () => {
    expect(defaultLanguage).toBe("en");
    expect(languages.map((language) => language.code)).toEqual(["en", "zh"]);
  });

  it("returns English interface copy", () => {
    const copy = makeCopy("en");

    expect(copy.brandSubtitle).toBe("Stage visual production console");
    expect(copy.createProject).toBe("Create Project");
    expect(copy.generatePackage).toBe("Generate production package");
    expect(copy.loadedProjects(2)).toBe("Loaded 2 projects.");
    expect(copy.generatedFiles(10, "C:/exports/Demo")).toBe("Generated 10 files into C:/exports/Demo.");
  });

  it("returns Chinese interface copy", () => {
    const copy = makeCopy("zh");

    expect(copy.brandSubtitle).toBe("\u821e\u53f0\u89c6\u89c9\u751f\u4ea7\u63a7\u5236\u53f0");
    expect(copy.createProject).toBe("\u521b\u5efa\u9879\u76ee");
    expect(copy.generatePackage).toBe("\u751f\u6210\u5236\u4f5c\u5305");
    expect(copy.loadedProjects(2)).toBe("\u5df2\u52a0\u8f7d 2 \u4e2a\u9879\u76ee\u3002");
    expect(copy.generatedFiles(10, "C:/exports/Demo")).toBe(
      "\u5df2\u751f\u6210 10 \u4e2a\u6587\u4ef6\u5230 C:/exports/Demo\u3002",
    );
  });
});
