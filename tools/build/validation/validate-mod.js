#!/usr/bin/env node

/*
 * 《神器使》Stellaris Mod 静态验证入口。
 *
 * 设计原则：
 * 1. 只读取文件，不修改运行内容。
 * 2. 默认把尚未统一制作的正式图标记为警告，不阻断当前开发。
 * 3. 使用 --strict-art 时，正式图标缺口会成为阻断项，供未来封版使用。
 */

const fs = require("node:fs");
const path = require("node:path");

const SCRIPT_EXTENSIONS = new Set([".txt", ".gfx", ".asset", ".gui", ".mod"]);
const PROJECT_MARKERS = [
  "aemusa",
  "aemod",
  "artifact",
  "destiny_lord",
  "white_night",
  "seth",
  "yutong",
  "rabi",
  "antoniva",
  "yanhua",
];

const args = process.argv.slice(2);
const strictArt = args.includes("--strict-art");
const requestedRoot = args.find((arg) => !arg.startsWith("--"));
const repositoryRoot = path.resolve(__dirname, "..", "..", "..");
const modRoot = path.resolve(requestedRoot || path.join(repositoryRoot, "mod"));

const errors = [];
const warnings = [];
const artGaps = [];

function toDisplayPath(filePath) {
  const relative = path.relative(repositoryRoot, filePath);
  return (relative || ".").split(path.sep).join("/");
}

function addError(code, filePath, message) {
  errors.push({ code, file: toDisplayPath(filePath), message });
}

function addWarning(code, filePath, message) {
  warnings.push({ code, file: toDisplayPath(filePath), message });
}

function addArtGap(kind, id, expected) {
  artGaps.push({ kind, id, expected: expected.split(path.sep).join("/") });
}

function listFiles(directory) {
  if (!fs.existsSync(directory)) {
    return [];
  }

  const result = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      result.push(...listFiles(fullPath));
    } else if (entry.isFile()) {
      result.push(fullPath);
    }
  }
  return result;
}

function hasUtf8Bom(buffer) {
  return buffer.length >= 3 && buffer[0] === 0xef && buffer[1] === 0xbb && buffer[2] === 0xbf;
}

function decodeUtf8(buffer) {
  const text = buffer.toString("utf8");
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

// 忽略字符串和 # 行注释后统计花括号，避免注释中的示例造成误报。
function validateBraces(text, filePath) {
  let depth = 0;
  let inQuote = false;
  let inComment = false;
  let escaped = false;
  let line = 1;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];

    if (char === "\n") {
      line += 1;
      inComment = false;
      escaped = false;
      continue;
    }
    if (inComment) {
      continue;
    }
    if (!inQuote && char === "#") {
      inComment = true;
      continue;
    }
    if (inQuote && char === "\\" && !escaped) {
      escaped = true;
      continue;
    }
    if (char === '"' && !escaped) {
      inQuote = !inQuote;
      continue;
    }
    escaped = false;
    if (inQuote) {
      continue;
    }
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth < 0) {
        addError("brace-underflow", filePath, `第 ${line} 行出现多余的右花括号。`);
        return;
      }
    }
  }

  if (inQuote) {
    addError("unterminated-quote", filePath, "存在未闭合的双引号字符串。");
  }
  if (depth !== 0) {
    addError("brace-mismatch", filePath, `花括号未配平，最终层级为 ${depth}。`);
  }
}

function isProjectOwnedReference(reference) {
  const normalized = reference.toLowerCase();
  return PROJECT_MARKERS.some((marker) => normalized.includes(marker));
}

function extractTopLevelKeys(text) {
  const keys = [];
  const expression = /^([A-Za-z0-9_]+)\s*=\s*\{/gm;
  let match;
  while ((match = expression.exec(text)) !== null) {
    keys.push(match[1]);
  }
  return keys;
}

function validateDescriptor() {
  const descriptorPath = path.join(modRoot, "descriptor.mod");
  if (!fs.existsSync(descriptorPath)) {
    addError("missing-descriptor", descriptorPath, "缺少 descriptor.mod，启动器无法加载模组。");
    return;
  }

  const text = decodeUtf8(fs.readFileSync(descriptorPath));
  if (!/^version\s*=\s*"[^"]+"/m.test(text)) {
    addError("missing-version", descriptorPath, "缺少 version 字段。");
  }
  if (!/^supported_version\s*=\s*"[^"]+"/m.test(text)) {
    addError("missing-supported-version", descriptorPath, "缺少 supported_version 字段。");
  }
}

function validateScripts(scriptFiles) {
  for (const filePath of scriptFiles) {
    const buffer = fs.readFileSync(filePath);
    if (hasUtf8Bom(buffer)) {
      addError("unexpected-bom", filePath, "非本地化脚本带有 UTF-8 BOM。");
    }

    const text = decodeUtf8(buffer);
    validateBraces(text, filePath);
    if (/\btrade_value\s*=/.test(text)) {
      addError("legacy-resource-key", filePath, "仍存在 Stellaris 4.4.3 无效资源键 trade_value，应使用 trade。");
    }
  }
}

function validateLocalisation(localisationFiles) {
  const seenKeys = new Map();

  for (const filePath of localisationFiles) {
    const buffer = fs.readFileSync(filePath);
    if (!hasUtf8Bom(buffer)) {
      addError("missing-localisation-bom", filePath, "本地化文件必须保留 UTF-8 BOM。");
    }

    const text = decodeUtf8(buffer);
    const firstContentLine = text.split(/\r?\n/).find((line) => line.trim() && !line.trim().startsWith("#"));
    if (!firstContentLine || !/^l_[a-z_]+:\s*$/.test(firstContentLine.trim())) {
      addError("invalid-localisation-header", filePath, "缺少合法的 l_<language>: 文件头。");
    }

    const lines = text.split(/\r?\n/);
    for (let index = 0; index < lines.length; index += 1) {
      const match = lines[index].match(/^\s*([A-Za-z0-9_.-]+):(?:\d+)?\s+/);
      if (!match || match[1].startsWith("l_")) {
        continue;
      }
      const key = match[1];
      const location = `${toDisplayPath(filePath)}:${index + 1}`;
      if (seenKeys.has(key)) {
        addError("duplicate-localisation-key", filePath, `本地化键 ${key} 重复；首次出现于 ${seenKeys.get(key)}。`);
      } else {
        seenKeys.set(key, location);
      }
    }
  }
}

function validateTextureReferences(scriptFiles) {
  const textureExpression = /texturefile\s*=\s*"([^"]+)"/gi;

  for (const filePath of scriptFiles) {
    if (path.extname(filePath).toLowerCase() !== ".gfx") {
      continue;
    }
    const text = decodeUtf8(fs.readFileSync(filePath));
    let match;
    while ((match = textureExpression.exec(text)) !== null) {
      const reference = match[1].replaceAll("/", path.sep);
      const expectedPath = path.join(modRoot, reference);
      if (!fs.existsSync(expectedPath) && isProjectOwnedReference(match[1])) {
        addError("missing-project-texture", filePath, `项目自有贴图不存在：${match[1]}`);
      }
    }
  }
}

function validateShipDesignReferences(allTextFiles) {
  const allText = allTextFiles.map((filePath) => decodeUtf8(fs.readFileSync(filePath))).join("\n");
  const componentKeys = new Set();
  const sectionKeys = new Set();

  for (const match of allText.matchAll(/\bkey\s*=\s*"([^"]+)"/g)) {
    componentKeys.add(match[1]);
  }
  for (const filePath of listFiles(path.join(modRoot, "common", "section_templates"))) {
    const text = decodeUtf8(fs.readFileSync(filePath));
    for (const match of text.matchAll(/\bkey\s*=\s*"([^"]+)"/g)) {
      sectionKeys.add(match[1]);
    }
  }

  const designRoot = path.join(modRoot, "common", "global_ship_designs");
  for (const filePath of listFiles(designRoot)) {
    const text = decodeUtf8(fs.readFileSync(filePath));
    for (const match of text.matchAll(/required_component\s*=\s*"([^"]+)"/g)) {
      if (isProjectOwnedReference(match[1]) && !componentKeys.has(match[1])) {
        addError("missing-required-component", filePath, `找不到项目必需部件：${match[1]}`);
      }
    }
    for (const match of text.matchAll(/template\s*=\s*"([^"]+)"/g)) {
      if (isProjectOwnedReference(match[1]) && !sectionKeys.has(match[1])) {
        addError("missing-section-template", filePath, `找不到项目区段模板：${match[1]}`);
      }
    }
  }
}

function collectDeferredArtGaps(allFiles) {
  const jobsRoot = path.join(modRoot, "common", "pop_jobs");
  for (const filePath of listFiles(jobsRoot).filter((file) => path.extname(file).toLowerCase() === ".txt")) {
    const text = decodeUtf8(fs.readFileSync(filePath));
    for (const job of extractTopLevelKeys(text)) {
      const jobIcon = path.join("gfx", "interface", "icons", "jobs", `job_${job}.dds`);
      const modifierIcon = path.join("gfx", "interface", "icons", "modifiers", `mod_job_${job}_add.dds`);
      if (!fs.existsSync(path.join(modRoot, jobIcon))) {
        addArtGap("岗位图标", job, jobIcon);
      }
      if (!fs.existsSync(path.join(modRoot, modifierIcon))) {
        addArtGap("岗位修正图标", job, modifierIcon);
      }
    }
  }

  const traitsRoot = path.join(modRoot, "common", "traits");
  for (const filePath of listFiles(traitsRoot).filter((file) => path.extname(file).toLowerCase() === ".txt")) {
    const text = decodeUtf8(fs.readFileSync(filePath));
    for (const trait of extractTopLevelKeys(text)) {
      const traitIcon = path.join("gfx", "interface", "icons", "traits", `${trait}.dds`);
      if (!fs.existsSync(path.join(modRoot, traitIcon))) {
        addArtGap("特质图标", trait, traitIcon);
      }
    }
  }

  const interfaceText = allFiles
    .filter((filePath) => path.extname(filePath).toLowerCase() === ".gfx")
    .map((filePath) => decodeUtf8(fs.readFileSync(filePath)))
    .join("\n");
  const megastructureRoot = path.join(modRoot, "common", "megastructures");
  for (const filePath of listFiles(megastructureRoot).filter((file) => path.extname(file).toLowerCase() === ".txt")) {
    const text = decodeUtf8(fs.readFileSync(filePath));
    for (const megastructure of extractTopLevelKeys(text)) {
      const spriteName = `GFX_${megastructure}_outliner_icon`;
      const escapedName = spriteName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      if (!new RegExp(`name\\s*=\\s*"${escapedName}"`).test(interfaceText)) {
        addArtGap("巨构总览图标", megastructure, `interface sprite ${spriteName}`);
      }
    }
  }
}

function printIssues(title, issues) {
  console.log(`\n${title}：${issues.length}`);
  for (const issue of issues) {
    console.log(`- [${issue.code}] ${issue.file}：${issue.message}`);
  }
}

function printArtGaps() {
  console.log(`\n暂缓美术缺口：${artGaps.length}`);
  const groups = new Map();
  for (const gap of artGaps) {
    if (!groups.has(gap.kind)) {
      groups.set(gap.kind, []);
    }
    groups.get(gap.kind).push(gap);
  }
  for (const [kind, gaps] of groups.entries()) {
    console.log(`- ${kind}：${gaps.length}`);
    for (const gap of gaps) {
      console.log(`  - ${gap.id} -> ${gap.expected}`);
    }
  }
}

function main() {
  console.log("《神器使》Stellaris Mod 静态验证");
  console.log(`运行目录：${modRoot}`);
  console.log(`美术模式：${strictArt ? "严格" : "暂缓（仅警告）"}`);

  if (!fs.existsSync(modRoot) || !fs.statSync(modRoot).isDirectory()) {
    console.error("\n验证失败：指定的 Mod 目录不存在。");
    process.exitCode = 1;
    return;
  }

  const allFiles = listFiles(modRoot);
  const scriptFiles = allFiles.filter((filePath) => SCRIPT_EXTENSIONS.has(path.extname(filePath).toLowerCase()));
  const localisationFiles = allFiles.filter((filePath) => path.extname(filePath).toLowerCase() === ".yml");
  const allTextFiles = allFiles.filter((filePath) => path.extname(filePath).toLowerCase() === ".txt");

  validateDescriptor();
  validateScripts(scriptFiles);
  validateLocalisation(localisationFiles);
  validateTextureReferences(scriptFiles);
  validateShipDesignReferences(allTextFiles);
  collectDeferredArtGaps(allFiles);

  printIssues("阻断错误", errors);
  printIssues("普通警告", warnings);
  printArtGaps();

  console.log("\n检查摘要");
  console.log(`- 脚本文件：${scriptFiles.length}`);
  console.log(`- 本地化文件：${localisationFiles.length}`);
  console.log(`- 阻断错误：${errors.length}`);
  console.log(`- 普通警告：${warnings.length}`);
  console.log(`- 暂缓美术缺口：${artGaps.length}`);

  if (errors.length > 0 || (strictArt && artGaps.length > 0)) {
    console.log("- 结果：未通过");
    process.exitCode = 1;
  } else {
    console.log("- 结果：通过（美术缺口按当前决策暂缓）");
  }
}

main();
