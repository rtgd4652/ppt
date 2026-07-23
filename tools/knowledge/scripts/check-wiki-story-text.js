const fs = require("node:fs");
const path = require("node:path");
const { openKnowledgeDatabase, REPOSITORY_ROOT } = require("./knowledge-db");
const {
  getWikiStoryRows,
  loadStoryCuratedManifest,
  loadStoryManualCorrections,
  loadStoryManifest,
  syncWikiStorySources,
} = require("./story-source-db");

function fail(message) {
  console.error(`检查失败：${message}`);
  process.exitCode = 1;
}

const manifest = loadStoryManifest();
const database = openKnowledgeDatabase();

try {
  // 先同步再验证，保证文件、清单与 SQLite 使用同一份当前状态。
  syncWikiStorySources(database);
  const rows = getWikiStoryRows(database);
  const entries = Array.isArray(manifest.pages) ? manifest.pages : [];
  const manualCorrections = loadStoryManualCorrections();
  const curatedManifest = loadStoryCuratedManifest();

  for (const entry of entries) {
    const row = rows.find((item) => item.title === entry.title);
    if (!row) {
      fail(`SQLite 缺少剧情页：${entry.title}`);
      continue;
    }

    if (entry.status === "collected") {
      for (const relative of [row.raw_file_path, row.clean_file_path, row.index_file_path]) {
        if (!relative || !fs.existsSync(path.join(REPOSITORY_ROOT, relative))) {
          fail(`${entry.title} 缺少已登记输出：${relative || "未填写路径"}`);
        }
      }

      const cleanPath = path.join(REPOSITORY_ROOT, row.clean_file_path);
      const clean = fs.readFileSync(cleanPath, "utf8");
      if (!clean.startsWith("---\n") || !clean.includes("# 剧情正文（清洗版）")) {
        fail(`${entry.title} 的 clean 剧情文档缺少 Front Matter 或正文标记。`);
      }

      const indexPath = path.join(REPOSITORY_ROOT, row.index_file_path);
      const sourceIndex = JSON.parse(fs.readFileSync(indexPath, "utf8"));
      const expectedChoiceTreeCount = Array.isArray(sourceIndex.choice_trees) ? sourceIndex.choice_trees.length : 0;
      if (Number(row.choice_tree_count) !== expectedChoiceTreeCount) {
        fail(`${entry.title} 的 SQLite 选择树索引与来源索引不一致。`);
      }

      for (const [treeIndex, tree] of (sourceIndex.choice_trees || []).entries()) {
        if (!Array.isArray(tree.options) || tree.options.length < 2) {
          fail(`${entry.title} 的第 ${treeIndex + 1} 个选择树缺少至少两个选项。`);
        }
        if (!["html_tab", "linear_text"].includes(tree.source_structure)) {
          fail(`${entry.title} 的第 ${treeIndex + 1} 个选择树缺少可追溯的来源结构。`);
        }
        if (!["player_or_dialogue_choice", "state_condition", "source_version"].includes(tree.branch_type)) {
          fail(`${entry.title} 的第 ${treeIndex + 1} 个选择树类别无效。`);
        }
        // 只有经“重复菜单 + 明确退出项”验证的树才能标为可重复。
        if (tree.repeatable && !tree.exit_option) {
          fail(`${entry.title} 的第 ${treeIndex + 1} 个可重复选择树缺少退出选项。`);
        }
        if (!tree.repeatable && tree.exit_option) {
          fail(`${entry.title} 的第 ${treeIndex + 1} 个一次性分支不应附带退出选项。`);
        }
      }
    }
  }

  for (const claim of manualCorrections.claims || []) {
    const stored = database.prepare("SELECT claim_id FROM claims WHERE claim_id = ?").get(claim.claim_id);
    if (!stored) {
      fail(`SQLite 缺少人工剧情修正：${claim.claim_id}`);
    }
  }

  for (const document of curatedManifest.documents || []) {
    const filePath = String(document.file_path || "").trim();
    if (!filePath || !fs.existsSync(path.join(REPOSITORY_ROOT, filePath))) {
      fail(`剧情整理清单缺少文件：${filePath || "未填写路径"}`);
      continue;
    }
    const stored = database
      .prepare("SELECT file_path, layer, document_status FROM knowledge_documents WHERE file_path = ?")
      .get(filePath);
    if (!stored || stored.layer !== "curated" || stored.document_status !== (document.document_status || "source_structured")) {
      fail(`SQLite 未正确登记剧情整理：${filePath}`);
    }
  }

  if (!process.exitCode) {
    console.log("Wiki 剧情文本检查通过。");
    console.log(`清单页面：${entries.length}`);
    console.log(`数据库剧情页：${rows.length}`);
    console.log(`已采集页面：${rows.filter((row) => row.collection_status === "collected").length}`);
  }
} finally {
  database.close();
}
