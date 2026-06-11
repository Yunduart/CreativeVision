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

    expect(copy.brandSubtitle).toBe("舞台视觉生产控制台");
    expect(copy.createProject).toBe("创建项目");
    expect(copy.generatePackage).toBe("生成制作包");
    expect(copy.loadedProjects(2)).toBe("已加载 2 个项目。");
    expect(copy.generatedFiles(10, "C:/exports/Demo")).toBe("已生成 10 个文件到 C:/exports/Demo。");
  });
});
