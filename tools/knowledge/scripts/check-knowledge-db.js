const fs = require("node:fs");
const path = require("node:path");
const {
  DATABASE_PATH,
  REPOSITORY_ROOT,
  getCatalogRows,
  getCharacterSourceRows,
  getConfiguredExcludedEpisodePages,
  getEpisodeReviewRows,
  getMainStoryRouteComparison,
  listCleanCharacterFiles,
  loadMainStoryCatalog,
  loadMainStoryRouteComparison,
  openKnowledgeDatabase,
} = require("./knowledge-db");
const {
  CORE_TERMS_DOCUMENT_ID,
  CORE_TERMS_DOCUMENT_PATH,
  CORE_TERMS_DOCUMENT_RELATIVE_PATH,
  CORE_TERMS_MANIFEST_ID,
  getCoreTermRows,
  getCoreTermsDatabaseSummary,
  loadCoreTermsManifest,
  normalizeSearchTerm,
  resolveReference,
  validateCoreTermsManifest,
} = require("./glossary-db");

const REQUIRED_OUTPUTS = [
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "sources", "bilibili_main_story_BV17M4y1w7rr.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "sources", "huiji_character_source_index_v0.1.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "videos", "main_story_catalog_v0.1.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "reviews", "main_story_core_01_03_review_queue_v0.1.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "reviews", "main_story_2_p09_p10_route_comparison_v0.1.md"),
];

function fail(message) {
  console.error(`检查失败：${message}`);
  process.exitCode = 1;
}

function sameNumberList(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

if (!fs.existsSync(DATABASE_PATH)) {
  fail("本地 SQLite 数据库尚未初始化。请先运行 init-knowledge-db.js。");
} else {
  const catalog = loadMainStoryCatalog();
  const routeComparisonSeed = loadMainStoryRouteComparison();
  const coreTermsManifest = validateCoreTermsManifest(loadCoreTermsManifest());
  const database = openKnowledgeDatabase();

  try {
    const integrityResult = database.prepare("PRAGMA integrity_check").get();
    if (integrityResult.integrity_check !== "ok") {
      fail(`SQLite 完整性检查失败：${integrityResult.integrity_check}`);
    }
    const foreignKeyProblems = database.prepare("PRAGMA foreign_key_check").all();
    if (foreignKeyProblems.length > 0) {
      fail(`SQLite 存在 ${foreignKeyProblems.length} 条外键孤儿记录。`);
    }
    const unownedTerms = database
      .prepare("SELECT term_id FROM glossary_terms WHERE manifest_id = ''")
      .all();
    if (unownedTerms.length > 0) {
      fail(
        `SQLite 仍有 ${unownedTerms.length} 个未归属术语：` +
          unownedTerms.map((term) => term.term_id).join("、")
      );
    }

    // 标题和别名共同构成全库检索入口，任意清单之间都不得出现规范化后的歧义。
    const searchEntries = database
      .prepare(`
        SELECT term_id, manifest_id, title AS value, 'title' AS value_type
        FROM glossary_terms
        UNION ALL
        SELECT term.term_id, term.manifest_id, alias.alias AS value, 'alias' AS value_type
        FROM glossary_aliases AS alias
        INNER JOIN glossary_terms AS term ON term.term_id = alias.term_id
      `)
      .all();
    const searchEntriesByKey = new Map();
    for (const entry of searchEntries) {
      const key = normalizeSearchTerm(entry.value);
      if (!searchEntriesByKey.has(key)) {
        searchEntriesByKey.set(key, []);
      }
      searchEntriesByKey.get(key).push(entry);
    }
    for (const [key, entries] of searchEntriesByKey.entries()) {
      if (entries.length < 2) {
        continue;
      }
      fail(
        `术语全库检索词冲突“${key}”：` +
          entries
            .map(
              (entry) =>
                `${entry.manifest_id}/${entry.term_id}/${entry.value_type}:${entry.value}`
            )
            .join("；")
      );
    }
    const source = database.prepare("SELECT source_id FROM source_records WHERE source_id = ?").get(catalog.source.id);
    const rows = getCatalogRows(database, catalog.source.id);
    const characterSources = getCharacterSourceRows(database);
    const reviewRows = getEpisodeReviewRows(database, catalog.source.id);
    const routeComparison = getMainStoryRouteComparison(database, routeComparisonSeed.comparison_id);
    // 角色数量随采集结果变化，不能把知识库校验固定写死为某个历史数量。
    const expectedCharacterSourceCount = listCleanCharacterFiles().length;
    const excluded = rows.filter((row) => row.editorial_status === "excluded");
    const priority = rows.filter((row) => row.priority_batch === "core_chapters_01_03");
    // 排除与首批队列均从目录规则推导，避免 P08 等人工确认项再次被硬编码遗漏。
    const configuredExcludedPages = getConfiguredExcludedEpisodePages(catalog);
    const actualExcludedPages = excluded.map((row) => row.episode_no).sort((left, right) => left - right);
    const priorityRange = catalog.editorial_rules?.priority_episode_range || [];
    const expectedPriorityPages = catalog.episodes
      .filter(
        (episode) =>
          priorityRange.length === 2 &&
          episode.page >= priorityRange[0] &&
          episode.page <= priorityRange[1] &&
          !configuredExcludedPages.includes(episode.page)
      )
      .map((episode) => episode.page);
    const actualPriorityPages = priority.map((row) => row.episode_no).sort((left, right) => left - right);
    const p01Review = reviewRows.find((review) => review.episode_no === 1);
    const p02Review = reviewRows.find((review) => review.episode_no === 2);
    const p03Review = reviewRows.find((review) => review.episode_no === 3);
    const p04Review = reviewRows.find((review) => review.episode_no === 4);
    const p05Review = reviewRows.find((review) => review.episode_no === 5);
    const p06Review = reviewRows.find((review) => review.episode_no === 6);
    const p07Review = reviewRows.find((review) => review.episode_no === 7);
    const p08Review = reviewRows.find((review) => review.episode_no === 8);
    const p09Review = reviewRows.find((review) => review.episode_no === 9);
    const p10Review = reviewRows.find((review) => review.episode_no === 10);
    const coreTermRows = getCoreTermRows(database, CORE_TERMS_MANIFEST_ID);
    const coreTermSummary = getCoreTermsDatabaseSummary(
      database,
      CORE_TERMS_MANIFEST_ID
    );

    if (!source) {
      fail(`缺少来源记录：${catalog.source.id}`);
    }
    // P09／P10 对照只保存人工确认前的候选结构，必须存在于 SQLite 且保持两条路线的证据边界。
    if (
      !routeComparison ||
      routeComparison.source_id !== catalog.source.id ||
      routeComparison.review_status !== "pending_human_confirmation" ||
      routeComparison.entries.length !== (routeComparisonSeed.entries || []).length
    ) {
      fail("P09／P10 路线对照记录缺失、状态错误或条目数量不一致。");
    } else {
      const allowedClassifications = new Set([
        "common_candidate",
        "route_difference_candidate",
        "unclassified",
      ]);
      for (const entry of routeComparison.entries) {
        const hasP09Evidence = entry.p09_evidence.some((evidence) => evidence.episode_no === 9);
        const hasP10Evidence = entry.p10_evidence.some((evidence) => evidence.episode_no === 10);
        if (
          !allowedClassifications.has(entry.classification) ||
          !hasP09Evidence ||
          !hasP10Evidence ||
          !entry.character_followup.length
        ) {
          fail(`路线对照项 ${entry.comparison_no} 的分类、证据边界或角色补全待办不完整。`);
        }
      }
    }
    if (rows.length !== 85) {
      fail(`目录分集数量应为 85，实际为 ${rows.length}。`);
    }
    if (!sameNumberList(actualExcludedPages, configuredExcludedPages)) {
      fail(`排除分集与目录规则不一致：实际 P${actualExcludedPages.join("、P")}。`);
    }
    if (!sameNumberList(actualPriorityPages, expectedPriorityPages)) {
      fail(`前三章首批队列与目录规则不一致：实际 P${actualPriorityPages.join("、P")}。`);
    }
    // P05-P06 必须保持为局部可选分支，不能再次被目录导出为主线本体或结局线。
    const configuredOptionalBranches = catalog.editorial_rules?.optional_branch_parent_chapters || {};
    for (const [pageText, parentChapter] of Object.entries(configuredOptionalBranches)) {
      const page = Number.parseInt(pageText, 10);
      const row = rows.find((episode) => episode.episode_no === page);
      if (
        !row ||
        row.content_kind !== "optional_branch" ||
        row.chapter_number !== parentChapter ||
        !row.route_note.includes("不影响主线走向或结局") ||
        !row.route_note.includes("完整逐段录入")
      ) {
        fail(`P${String(page).padStart(2, "0")} 的可选分支分类缺失或不完整。`);
      }
    }
    // P07 是区域讨伐结束后的黑核回收后续，必须与 P05-P06 的区域选择分支分开分类。
    const configuredRegionalFollowups = catalog.editorial_rules?.regional_followup_parent_chapters || {};
    for (const [pageText, parentChapter] of Object.entries(configuredRegionalFollowups)) {
      const page = Number.parseInt(pageText, 10);
      const row = rows.find((episode) => episode.episode_no === page);
      if (
        !row ||
        row.content_kind !== "regional_followup" ||
        row.chapter_number !== parentChapter ||
        !row.route_note.includes("每个区域讨伐结束") ||
        !row.route_note.includes("完整")
      ) {
        fail(`P${String(page).padStart(2, "0")} 的区域讨伐后续分类缺失或不完整。`);
      }
    }
    if (!p01Review || p01Review.review_status !== "context_only" || p01Review.segments.length !== 1) {
      fail("P01 新手引导的范围确认或时间码记录缺失。");
    }
    // P02 已有部分片段获得用户人工确认，其余片段仍不能直接转为正式知识。
    if (!p02Review || p02Review.review_status !== "partially_human_confirmed") {
      fail("P02 游戏背景主线的部分人工确认审核记录缺失。");
    }
    // P03 已完成全片首轮审核并取得局部人工确认；跨结局结论仍必须等待主线 1 审核完成与用户补充。
    if (
      !p03Review ||
      p03Review.review_status !== "partially_human_confirmed" ||
      p03Review.segments.length !== 11 ||
      p03Review.segments.at(-1)?.end_second !== 4048
    ) {
      fail("P03 结局 1 的全片首轮审核记录缺失或不完整。");
    }
    // P04 按十二分钟分段独立审核，当前已完成全片，仍不得混入其他结局线结论。
    if (
      !p04Review ||
      p04Review.review_status !== "pending_human_confirmation" ||
      p04Review.segments.length !== 4 ||
      p04Review.segments[0]?.end_second !== 720 ||
      p04Review.segments.at(-1)?.end_second !== 2624
    ) {
      fail("P04 结局 2 的全片 00:00–43:44 审核记录缺失或不完整。");
    }
    // P05 已完成地区结构级审核；九个旧时间段继续保留逐句校订素材。
    if (
      !p05Review ||
      p05Review.review_status !== "human_reviewed_structure" ||
      p05Review.segments.length !== 9 ||
      p05Review.segments[0]?.end_second !== 720 ||
      p05Review.segments.at(-1)?.end_second !== 5936
    ) {
      fail("P05 东方古街区域剧情分支的全片 00:00–01:38:56 审核记录缺失或不完整。");
    }
    // P06 已按任务交接、中央城区独有段与共同后续完成结构级审核。
    if (
      !p06Review ||
      p06Review.review_status !== "human_reviewed_structure" ||
      p06Review.segments.length !== 3 ||
      p06Review.segments[0]?.end_second !== 400 ||
      p06Review.segments[1]?.start_second !== 400 ||
      p06Review.segments[1]?.end_second !== 1190 ||
      p06Review.segments[2]?.start_second !== 1190 ||
      p06Review.segments.at(-1)?.end_second !== 1517
    ) {
      fail("P06 中央城区区域剧情分支的全片 00:00–25:17 审核记录缺失或不完整。");
    }
    // P07 已完成全片结构、实际路线与主要人物视觉审核；少数具体好感度回答仍保留为未确认。
    if (
      !p07Review ||
      p07Review.review_status !== "human_reviewed_structure" ||
      p07Review.segments.length !== 7 ||
      p07Review.segments[0]?.start_second !== 0 ||
      p07Review.segments[0]?.end_second !== 44 ||
      p07Review.segments[1]?.start_second !== 45 ||
      p07Review.segments[5]?.start_second !== 510 ||
      p07Review.segments[6]?.start_second !== 605 ||
      p07Review.segments.at(-1)?.end_second !== 689
    ) {
      fail("P07 黑核回收后续的全片 00:00–11:29 审核记录缺失或不完整。");
    }
    if (!p08Review || p08Review.review_status !== "excluded" || !actualExcludedPages.includes(8)) {
      fail("P08 人工确认排除记录缺失。");
    }
    // P09 是主线剧情 2 的独立开场，当前验证已完成的全片十段，不能与主线 1 混写。
    if (
      !p09Review ||
      p09Review.review_status !== "pending_human_confirmation" ||
      p09Review.segments.length !== 10 ||
      p09Review.segments[0]?.start_second !== 0 ||
      p09Review.segments[0]?.end_second !== 720 ||
      p09Review.segments[1]?.start_second !== 720 ||
      p09Review.segments[1]?.end_second !== 1440 ||
      p09Review.segments[2]?.start_second !== 1440 ||
      p09Review.segments[2]?.end_second !== 2160 ||
      p09Review.segments[3]?.start_second !== 2160 ||
      p09Review.segments[3]?.end_second !== 2880 ||
      p09Review.segments[4]?.start_second !== 2880 ||
      p09Review.segments[4]?.end_second !== 3600 ||
      p09Review.segments[5]?.start_second !== 3600 ||
      p09Review.segments[5]?.end_second !== 4320 ||
      p09Review.segments[6]?.start_second !== 4320 ||
      p09Review.segments[6]?.end_second !== 5040 ||
      p09Review.segments[7]?.start_second !== 5040 ||
      p09Review.segments[7]?.end_second !== 5760 ||
      p09Review.segments[8]?.start_second !== 5760 ||
      p09Review.segments[8]?.end_second !== 6480 ||
      p09Review.segments[9]?.start_second !== 6480 ||
      p09Review.segments[9]?.end_second !== 7081
    ) {
      fail("P09 主线剧情 2 的全片十段审核记录缺失或不完整。");
    }
    // P10 是主线剧情 2 的另一条结局路线，当前验证已完成全片十段。
    if (
      !p10Review ||
      p10Review.review_status !== "pending_human_confirmation" ||
      p10Review.segments.length !== 10 ||
      p10Review.segments[0]?.start_second !== 0 ||
      p10Review.segments[0]?.end_second !== 720 ||
      p10Review.segments[1]?.start_second !== 720 ||
      p10Review.segments[1]?.end_second !== 1440 ||
      p10Review.segments[2]?.start_second !== 1440 ||
      p10Review.segments[2]?.end_second !== 2160 ||
      p10Review.segments[3]?.start_second !== 2160 ||
      p10Review.segments[3]?.end_second !== 2880 ||
      p10Review.segments[4]?.start_second !== 2880 ||
      p10Review.segments[4]?.end_second !== 3600 ||
      p10Review.segments[5]?.start_second !== 3600 ||
      p10Review.segments[5]?.end_second !== 4320 ||
      p10Review.segments[6]?.start_second !== 4320 ||
      p10Review.segments[6]?.end_second !== 5040 ||
      p10Review.segments[7]?.start_second !== 5040 ||
      p10Review.segments[7]?.end_second !== 5760 ||
      p10Review.segments[8]?.start_second !== 5760 ||
      p10Review.segments[8]?.end_second !== 6480 ||
      p10Review.segments[9]?.start_second !== 6480 ||
      p10Review.segments[9]?.end_second !== 6891
    ) {
      fail("P10 主线剧情 2 结局 2 的全片十段审核记录缺失或不完整。");
    }
    if (characterSources.length !== expectedCharacterSourceCount) {
      fail(`灰机角色来源应为 ${expectedCharacterSourceCount} 条，实际为 ${characterSources.length}。`);
    }

    // 核心术语必须与已提交 JSON 种子逐项一致；不把待审核术语自动提升为确认事实。
    const expectedTermCount = coreTermsManifest.terms.length;
    const expectedAliasCount = coreTermsManifest.terms.reduce(
      (total, term) => total + term.aliases.length,
      0
    );
    const expectedReferenceCount = coreTermsManifest.terms.reduce(
      (total, term) => total + term.references.length,
      0
    );
    const expectedRelationCount = coreTermsManifest.terms.reduce(
      (total, term) => total + term.relations.length,
      0
    );
    if (
      coreTermSummary.termCount !== expectedTermCount ||
      coreTermSummary.aliasCount !== expectedAliasCount ||
      coreTermSummary.referenceCount !== expectedReferenceCount ||
      coreTermSummary.relationCount !== expectedRelationCount
    ) {
      fail(
        `核心术语 SQLite 计数与种子不一致：` +
          `术语 ${coreTermSummary.termCount}/${expectedTermCount}，` +
          `别名 ${coreTermSummary.aliasCount}/${expectedAliasCount}，` +
          `引用 ${coreTermSummary.referenceCount}/${expectedReferenceCount}，` +
          `关系 ${coreTermSummary.relationCount}/${expectedRelationCount}。`
      );
    }
    if (
      !coreTermSummary.document ||
      coreTermSummary.document.document_id !== CORE_TERMS_DOCUMENT_ID ||
      coreTermSummary.document.document_type !== "glossary" ||
      coreTermSummary.document.layer !== "curated" ||
      coreTermSummary.document.file_path !== CORE_TERMS_DOCUMENT_RELATIVE_PATH
    ) {
      fail("核心术语 Markdown 尚未正确登记到 knowledge_documents。");
    }
    if (!fs.existsSync(CORE_TERMS_DOCUMENT_PATH)) {
      fail(`核心术语 Markdown 文件不存在：${CORE_TERMS_DOCUMENT_RELATIVE_PATH}`);
    } else {
      const glossaryMarkdown = fs.readFileSync(CORE_TERMS_DOCUMENT_PATH, "utf8");
      const requiredMetadata = [
        "manifest_id: core-terms-v0.1",
        "status: active",
        `- ${expectedTermCount} 个规范术语。`,
        `- ${expectedAliasCount} 个可检索别名。`,
        `- ${expectedReferenceCount} 条来源引用。`,
        `- ${expectedRelationCount} 条术语关系。`,
      ];
      for (const metadata of requiredMetadata) {
        if (!glossaryMarkdown.includes(metadata)) {
          fail(`核心术语 Markdown 元数据或计数漂移：${metadata}`);
        }
      }
      for (const term of coreTermsManifest.terms) {
        if (
          !glossaryMarkdown.includes(`| ${term.title} |`) ||
          !glossaryMarkdown.includes(term.canonical_summary)
        ) {
          fail(`核心术语 Markdown 缺少规范词或定义：${term.term_id}`);
        }
      }
    }

    const getAliases = database.prepare(`
      SELECT alias, alias_type, notes
      FROM glossary_aliases
      WHERE term_id = ?
      ORDER BY alias
    `);
    const getReferences = database.prepare(`
      SELECT
        reference_id, reference_no, reference_type, source_locator,
        source_id, document_id, source_section, evidence_role,
        review_status, notes
      FROM glossary_term_references
      WHERE term_id = ?
      ORDER BY reference_no
    `);
    const getRelations = database.prepare(`
      SELECT related_term_id, relation_type, notes
      FROM glossary_relations
      WHERE term_id = ?
      ORDER BY related_term_id, relation_type
    `);

    for (const expectedTerm of coreTermsManifest.terms) {
      const storedTerm = coreTermRows.find(
        (term) => term.term_id === expectedTerm.term_id
      );
      if (
        !storedTerm ||
        storedTerm.title !== expectedTerm.title ||
        storedTerm.domain !== expectedTerm.domain ||
        storedTerm.knowledge_layer !== expectedTerm.knowledge_layer ||
        storedTerm.review_status !== expectedTerm.review_status ||
        (storedTerm.canonical_summary || "") !== expectedTerm.canonical_summary ||
        storedTerm.usage_note !== expectedTerm.usage_note ||
        storedTerm.sort_order !== expectedTerm.sort_order ||
        storedTerm.notes !== expectedTerm.notes
      ) {
        fail(`核心术语未按种子写入或字段漂移：${expectedTerm.term_id}`);
        continue;
      }

      // SQLite 的默认二进制排序与 JavaScript 的中文 localeCompare 顺序可能不同。
      // 两侧使用同一个确定性比较器，避免把正确数据误报成字段漂移。
      const compareAlias = (left, right) =>
        left.alias < right.alias ? -1 : left.alias > right.alias ? 1 : 0;
      const storedAliases = getAliases.all(expectedTerm.term_id).sort(compareAlias);
      const expectedAliases = [...expectedTerm.aliases].sort(compareAlias);
      if (
        storedAliases.length !== expectedAliases.length ||
        storedAliases.some(
          (alias, index) =>
            alias.alias !== expectedAliases[index].alias ||
            alias.alias_type !== expectedAliases[index].alias_type ||
            alias.notes !== expectedAliases[index].notes
        )
      ) {
        fail(`核心术语别名与种子不一致：${expectedTerm.term_id}`);
      }

      const storedReferences = getReferences.all(expectedTerm.term_id);
      if (storedReferences.length !== expectedTerm.references.length) {
        fail(`核心术语来源引用数量不一致：${expectedTerm.term_id}`);
      } else {
        for (const [referenceIndex, reference] of expectedTerm.references.entries()) {
          const storedReference = storedReferences[referenceIndex];
          const expectedResolvedReference = resolveReference(database, reference);
          if (
            storedReference.reference_id !== reference.reference_id ||
            storedReference.reference_no !== referenceIndex + 1 ||
            storedReference.reference_type !== reference.reference_type ||
            storedReference.source_locator !==
              expectedResolvedReference.sourceLocator ||
            storedReference.source_id !== expectedResolvedReference.sourceId ||
            storedReference.document_id !== expectedResolvedReference.documentId ||
            storedReference.source_section !== reference.source_section ||
            storedReference.evidence_role !== reference.evidence_role ||
            storedReference.review_status !==
              (reference.review_status || expectedTerm.review_status) ||
            storedReference.notes !== reference.notes
          ) {
            fail(
              `核心术语第 ${referenceIndex + 1} 条来源引用字段漂移：${expectedTerm.term_id}`
            );
          }
          if (
            ["wiki_story_page", "wiki_character_page", "video_supplement"].includes(
              reference.reference_type
            ) &&
            !storedReference.source_id
          ) {
            fail(
              `核心术语来源没有解析到 source_records：${expectedTerm.term_id} / ${reference.source_locator}`
            );
          }
          if (
            ["curated_document", "project_document"].includes(
              reference.reference_type
            )
          ) {
            const localPath = storedReference.source_locator.split("#", 1)[0];
            if (
              !localPath ||
              !fs.existsSync(
                path.join(REPOSITORY_ROOT, ...localPath.replace(/\\/g, "/").split("/"))
              )
            ) {
              fail(
                `核心术语本地文档引用不存在：${expectedTerm.term_id} / ${localPath || "未填写"}`
              );
            }
          }
        }
      }

      const storedRelations = getRelations.all(expectedTerm.term_id);
      const expectedRelations = [...expectedTerm.relations].sort((left, right) =>
        `${left.related_term_id}:${left.relation_type}`.localeCompare(
          `${right.related_term_id}:${right.relation_type}`
        )
      );
      if (
        storedRelations.length !== expectedRelations.length ||
        storedRelations.some(
          (relation, index) =>
            relation.related_term_id !== expectedRelations[index].related_term_id ||
            relation.relation_type !== expectedRelations[index].relation_type ||
            relation.notes !== expectedRelations[index].notes
        )
      ) {
        fail(`核心术语关系与种子不一致：${expectedTerm.term_id}`);
      }
    }

    for (const outputPath of REQUIRED_OUTPUTS) {
      if (!fs.existsSync(outputPath)) {
        fail(`缺少导出文档：${outputPath}`);
      }
    }

    if (!process.exitCode) {
      console.log("本地知识库数据库检查通过。");
      console.log(`来源记录：${source.source_id}`);
      console.log(`分集目录：${rows.length}`);
      console.log(`排除分集：${excluded.length}`);
      console.log(`首批队列：${priority.length}`);
      console.log(`人工审核记录：${reviewRows.length}`);
      console.log(`灰机角色来源：${characterSources.length}`);
      console.log(`核心术语：${coreTermSummary.termCount}`);
      console.log(`术语来源引用：${coreTermSummary.referenceCount}`);
    }
  } finally {
    database.close();
  }
}
