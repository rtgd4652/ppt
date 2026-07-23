const { Parser } = require("./parser");

class StoryParser {
  constructor() {
    // 复用通用 HTML→Markdown 工具；本类不联网，只处理已经取得的 Wiki 页面数据。
    this.rawParser = new Parser();
  }

  // 生成可追溯的 raw 层。它保留页面转换后的完整文本，不把自动清洗结果当作原始资料。
  parseRaw(page) {
    const plainMarkdown = this.rawParser.htmlToMarkdown(page.html || "");
    const frontmatter = this.buildFrontmatter({
      title: page.title,
      type: "story_raw",
      source: ["Huiji Wiki"],
      sourceUrl: page.sourceUrl || "",
      pageId: page.pageid || "",
      lastSync: page.lastSync || "",
      categories: page.categories || [],
    });

    return {
      plainMarkdown,
      markdown: [
        frontmatter,
        "# 页面自动转换正文",
        plainMarkdown || "暂无可转换的页面正文。",
      ].join("\n\n").trim() + "\n",
    };
  }

  // 生成可供知识库阅读的 clean 层。此处只做机械清洗，不自动补写剧情，也不替代人工摘要。
  parseStory(page, rawResult, options = {}) {
    const plainMarkdown = rawResult?.plainMarkdown || this.rawParser.htmlToMarkdown(page.html || "");
    // 优先读取 Wiki 原始 HTML 的 Tab 面板关系；普通 Markdown 转换会丢失“选项对应哪段对白”的边界。
    const htmlChoiceResult = this.convertStoryHtmlWithChoiceTrees(page.html || "", plainMarkdown);
    const machineCleanMarkdown = this.cleanStoryMarkdown(htmlChoiceResult.markdown);
    // HTML 中没有保留结构的旧式选择，再使用严格的重复回答核对作为安全回退。
    const fallbackChoiceTreeResult = this.structureChoiceTrees(machineCleanMarkdown);
    const cleanMarkdown = this.normalizeResidualChoiceConditions(fallbackChoiceTreeResult.markdown);
    const choiceTrees = [...htmlChoiceResult.choiceTrees, ...fallbackChoiceTreeResult.choiceTrees].map((tree, index) => ({
      ...tree,
      tree_index: index + 1,
    }));
    const sections = this.rawParser.extractSections(cleanMarkdown);
    const frontmatter = this.buildFrontmatter({
      title: page.title,
      type: "story",
      source: ["Huiji Wiki"],
      sourceUrl: page.sourceUrl || "",
      pageId: page.pageid || "",
      lastSync: page.lastSync || "",
      storyScope: options.storyScope || "unclassified",
      route: options.route || "",
      chapter: options.chapter || "",
      day: options.day || "",
      categories: page.categories || [],
      legacyVideoEvidence: options.legacyVideoEvidence || [],
      manualStructureReference: options.manualStructureReference || "",
    });

    const metadata = [
      `- 页面标题：${page.title || "未知"}`,
      `- 来源页面：${page.sourceUrl || "未知"}`,
      `- 页面修订时间：${page.touched || "未知"}`,
      `- 剧情范围：${options.storyScope || "待分类"}`,
      `- 路线：${options.route || "待确认"}`,
      `- 章节：${options.chapter || "待确认"}`,
      `- 天数／阶段：${options.day || "待确认"}`,
    ];

    if (Array.isArray(options.legacyVideoEvidence) && options.legacyVideoEvidence.length) {
      metadata.push(`- 既有视频补充记录：${options.legacyVideoEvidence.join("；")}`);
    }

    // 人工结构注记独立于 Wiki 原文，避免清洗器把人工确认误当成自动采集结果。
    const manualStructureBlock = options.manualStructureNote
      ? [
          "# 人工结构注记",
          options.manualStructureNote,
          options.manualStructureReference
            ? `- 详细依据：${options.manualStructureReference}`
            : "",
        ]
          .filter(Boolean)
          .join("\n\n")
      : "";

    const markdown = [
      frontmatter,
      "# 来源与范围",
      metadata.join("\n"),
      manualStructureBlock,
      "# 剧情正文（清洗版）",
      cleanMarkdown || "暂无可清洗的页面正文。",
      "# 采集边界",
      "- 本页以灰机 Wiki 已公开文本为主来源，仅做结构与格式清洗。",
      "- 本页不自动生成剧情结论、人物动机或路线共通性判断。",
      "- 旧视频抽样仅可作为补充视觉或人工确认线索，不能覆盖本页文本。",
    ].join("\n\n");

    return {
      markdown: `${markdown.trim()}\n`,
      cleanMarkdown,
      choiceTrees,
      sections: sections.map((section) => ({
        level: section.level,
        title: section.title,
        character_count: section.content.length,
      })),
    };
  }

  // 清洗仅删除明显的页面导航残留、空白和重复行，保留剧情正文、标题和段落顺序。
  cleanStoryMarkdown(markdown) {
    const navigationOnlyLines = new Set([
      "目录",
      "导航菜单",
      "页面导航",
      "返回顶部",
      "编辑",
      "查看历史",
      "讨论",
    ]);
    const fileOnlyPattern = /^(?:File|文件):.+\.(?:png|jpe?g|gif|webp|svg|ogg|mp3|wav)$/i;
    const visualAssetPrefix = /^(?:(?:Dialogue[ _-]?icon|CG|Alter[ _-]?selector|Buliding[ _-]?part|Fight[ _-]?level|Monster[ _-]?mini[ _-]?icon|Icon[ _-]?Boss[ _-]?style|Item[ _-]?rare|Mission[ _-]?type[ _-]?Main|手账(?:CG|text))[\s\S]*?\.(?:png|jpe?g|gif|webp|svg)\s*)/i;
    const inlineInfoIcon = /(?:^|\s)Info[ _-]?.{0,60}?icon\.(?:png|jpe?g|gif|webp|svg)\s*/gi;
    const lines = String(markdown || "")
      .replace(/\u00a0/g, " ")
      .split(/\r?\n/)
      // 剧情页会把头像、CG 与按钮图片的 alt 文本混入正文；只剥离文件名，保留同一行紧随其后的说明文字。
      .map((line) => line.replace(visualAssetPrefix, "").replace(inlineInfoIcon, " ").replace(/[ \t]+/g, " ").trim())
      .filter((line) => !navigationOnlyLines.has(line))
      .filter((line) => !/^-\s*(?:目录|上一天|下一天|返回顶部|返回剧情目录)\s*$/.test(line))
      .filter((line) => line !== "|")
      .filter((line) => !fileOnlyPattern.test(line));

    const withoutLeadingNavigation = [];
    let reachedStoryHeading = false;
    for (const line of lines) {
      if (/^#{2,4}\s+/.test(line)) {
        reachedStoryHeading = true;
      }
      // Wiki 顶部的相邻剧情页、终局页链接会被转换为项目符号；它们位于首个正文标题前，不应混入剧情正文。
      if (!reachedStoryHeading && /^-\s+/.test(line)) {
        continue;
      }
      withoutLeadingNavigation.push(line);
    }

    const deduplicated = [];
    for (const line of withoutLeadingNavigation) {
      // MediaWiki 的移动端导航偶尔会连续重复同一行；只去除紧邻重复，不合并正文中的重复台词。
      if (line && line === deduplicated.at(-1)) {
        continue;
      }
      deduplicated.push(line);
    }

    const compact = deduplicated
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .replace(/(^|\n)\|\s*(?=\n|$)/g, "$1")
      .trim();

    return this.removeAdjacentDuplicateBlocks(compact);
  }

  // 在原始 HTML 中直接读取 nav-tabs / tab-content 的对应关系，避免通用 Markdown 转换把各分支压成连续文本。
  // 对不含 Tab 结构的旧式页面，后续仍保留严格的线性化选择树回退识别。
  convertStoryHtmlWithChoiceTrees(html, fallbackMarkdown) {
    if (!html) {
      return { markdown: fallbackMarkdown, choiceTrees: [] };
    }

    const extraction = this.extractTabChoiceTrees(html);
    if (!extraction.choiceTrees.length) {
      return { markdown: fallbackMarkdown, choiceTrees: [] };
    }

    let markdown = this.rawParser.htmlToMarkdown(extraction.html);
    for (const tree of extraction.choiceTrees) {
      markdown = markdown.replace(tree.placeholder, this.renderHtmlChoiceTree(tree));
    }

    return {
      markdown,
      choiceTrees: extraction.choiceTrees.map((tree) => ({
        source_structure: "html_tab",
        branch_type: tree.branch_type,
        repeatable: tree.repeatable,
        options: tree.options,
        exit_option: tree.exit_option || "",
        has_shared_continuation: Boolean(tree.has_shared_continuation),
        extraction_status: "parsed_from_html_tab",
        // 嵌套战斗或对话分支必须保留父子关系，不能只记录最外层 Tab。
        parent_tree_index: tree.parent_tree_index || null,
        parent_option: tree.parent_option || "",
        depth: tree.depth || 0,
      })),
    };
  }

  extractTabChoiceTrees(html) {
    const state = {
      next_tree_index: 1,
      choice_trees: [],
    };
    const normalizedHtml = this.extractTabChoiceTreesFromFragment(String(html || ""), state, null, 0);

    // 被合并为“可重复询问 + 退出项”的第二组菜单不应单独计数；
    // 同时把父节点编号重新映射为对外稳定的连续索引。
    const retainedTrees = state.choice_trees.filter((tree) => !tree.omitted);
    const indexMap = new Map(retainedTrees.map((tree, index) => [tree.tree_index, index + 1]));

    return {
      html: normalizedHtml,
      choiceTrees: retainedTrees.map((tree, index) => ({
        ...tree,
        tree_index: index + 1,
        parent_tree_index: tree.parent_tree_index
          ? indexMap.get(tree.parent_tree_index) || null
          : null,
      })),
    };
  }

  // 灰机 Wiki 的 S2tab/Ttab 模板会把后续战斗 Tab 嵌在前一场胜利分支的 HTML 中。
  // 旧实现只处理最外层容器，导致“剧情战胜利”正文里混入尚未结构化的下一层分支。
  // 这里按 HTML 片段递归解析：父分支保存子选择树占位符，最终再按父子顺序展开为 Markdown。
  extractTabChoiceTreesFromFragment(html, state, parentTreeIndex, depth, parentOption = "") {
    const source = String(html || "");
    const segments = [];
    let cursor = 0;

    while (cursor < source.length) {
      const candidate = this.findNextTabChoiceTree(source, cursor);
      if (!candidate) {
        segments.push({ type: "html", content: source.slice(cursor) });
        break;
      }

      segments.push({ type: "html", content: source.slice(cursor, candidate.nav_start) });

      const treeIndex = state.next_tree_index;
      state.next_tree_index += 1;
      const tree = {
        tree_index: treeIndex,
        parent_tree_index: parentTreeIndex,
        parent_option: parentOption,
        depth,
        placeholder: `__STORY_CHOICE_TREE_${treeIndex - 1}__`,
        options: candidate.branches.map((branch) => branch.option),
        branches: [],
        branch_type: this.classifyHtmlTabBranch(candidate.branches.map((branch) => branch.option)),
        // 单独一组 Tab 只能证明存在分支，不能证明该选项可以被反复询问。
        repeatable: false,
        exit_option: "",
        exit_response: "",
        has_shared_continuation: false,
      };
      state.choice_trees.push(tree);

      tree.branches = candidate.branches.map((branch) => {
        const nestedHtml = this.extractTabChoiceTreesFromFragment(
          branch.inner_html,
          state,
          treeIndex,
          depth + 1,
          branch.option
        );
        return {
          option: branch.option,
          // 嵌套树保留为占位符，稍后由 convertStoryHtmlWithChoiceTrees 从外到内展开。
          response: this.cleanStoryMarkdown(this.rawParser.htmlToMarkdown(nestedHtml)),
        };
      });

      segments.push({ type: "tree", tree });
      cursor = candidate.content_bounds.end;
    }

    const normalizedSegments = this.mergeRepeatableTabChoiceSegments(segments);
    return normalizedSegments
      .map((segment) => {
        if (segment.type === "html") {
          return segment.content;
        }
        return `<p>${segment.tree.placeholder}</p>`;
      })
      .join("");
  }

  // 从指定位置寻找下一棵可验证的 Tab 选择树。无效或只含展示内容的 Tab 会被跳过。
  findNextTabChoiceTree(html, startIndex) {
    const source = String(html || "");
    const navPattern = /<ul\b[^>]*>/gi;
    navPattern.lastIndex = Math.max(0, startIndex);
    let match;

    while ((match = navPattern.exec(source))) {
      if (!this.hasHtmlClass(match[0], "nav-tabs")) {
        continue;
      }

      const navStart = match.index;
      const navBounds = this.findMatchingHtmlTag(source, navStart, "ul");
      if (!navBounds) {
        continue;
      }
      const contentStart = this.findTabContentStart(source, navBounds.end);
      if (!contentStart || contentStart.start - navBounds.end > 4000) {
        navPattern.lastIndex = navBounds.end;
        continue;
      }
      const contentBounds = this.findMatchingHtmlTag(source, contentStart.start, "div");
      if (!contentBounds) {
        navPattern.lastIndex = navBounds.end;
        continue;
      }

      const options = this.extractTabOptions(source.slice(navStart, navBounds.end));
      const panes = this.extractTabPanes(source, contentBounds);
      const branches = options
        .map((option, index) => {
          const pane = panes.find((candidate) => candidate.id && option.target_id === candidate.id) || panes[index];
          if (!pane) {
            return null;
          }
          return {
            option: option.label,
            inner_html: pane.inner_html,
          };
        })
        .filter(Boolean);

      if (options.length >= 2 && branches.length === options.length) {
        return {
          nav_start: navStart,
          content_bounds: contentBounds,
          branches,
        };
      }

      navPattern.lastIndex = navBounds.end;
    }

    return null;
  }

  // Wiki 会把“可重复询问的若干选项”与“相同选项加一个退出选项”分别制作为两组 Tab。
  // 只有所有旧选项的回答逐项完全一致、且中间文本明确说明“如果你的选择是”时才合并，避免误删剧情内容。
  mergeRepeatableTabChoiceSegments(segments) {
    const normalized = [...segments];

    for (let index = 0; index <= normalized.length - 3; index += 1) {
      const first = normalized[index];
      const bridge = normalized[index + 1];
      const second = normalized[index + 2];
      if (first.type !== "tree" || bridge.type !== "html" || second.type !== "tree") {
        continue;
      }
      if (!this.isRepeatableTabChoicePair(first.tree, bridge.content, second.tree)) {
        continue;
      }

      const exitBranch = second.tree.branches.at(-1);
      // 原地保留第一组菜单的树编号与占位符；第二组只是同一菜单加入退出项后的重复展示。
      // 这样嵌套树的父子索引不会因合并而失去可追溯性。
      first.tree.repeatable = true;
      first.tree.exit_option = exitBranch.option;
      first.tree.exit_response = exitBranch.response;
      first.tree.has_shared_continuation = false;
      second.tree.omitted = true;
      normalized.splice(index, 3, first);
      index = Math.max(-1, index - 2);
    }

    return normalized;
  }

  isRepeatableTabChoicePair(firstTree, bridgeHtml, secondTree) {
    if (!firstTree || !secondTree) {
      return false;
    }
    if (firstTree.options.length < 2 || secondTree.options.length !== firstTree.options.length + 1) {
      return false;
    }
    if (!firstTree.options.every((option, index) => option === secondTree.options[index])) {
      return false;
    }
    if (!firstTree.options.every((option, index) => {
      const firstBranch = firstTree.branches[index];
      const secondBranch = secondTree.branches[index];
      return firstBranch && secondBranch && this.areEquivalentChoiceResponses(firstBranch.response, secondBranch.response);
    })) {
      return false;
    }

    const bridgeText = this.htmlFragmentToText(bridgeHtml);
    return (
      bridgeText.includes("如果你的选择是") &&
      firstTree.options.every((option) => bridgeText.includes(option))
    );
  }

  areEquivalentChoiceResponses(firstResponse, secondResponse) {
    const normalize = (value) => String(value || "").replace(/\s+/g, " ").trim();
    return normalize(firstResponse) === normalize(secondResponse);
  }

  findTabContentStart(html, startIndex) {
    const divPattern = /<div\b[^>]*>/gi;
    divPattern.lastIndex = startIndex;
    let match;
    while ((match = divPattern.exec(html))) {
      if (match.index - startIndex > 4000) {
        return null;
      }
      if (this.hasHtmlClass(match[0], "tab-content")) {
        return { start: match.index, open_end: divPattern.lastIndex };
      }
    }
    return null;
  }

  findMatchingHtmlTag(html, startIndex, tagName) {
    const tagPattern = new RegExp(`<\\/?${tagName}\\b[^>]*>`, "gi");
    tagPattern.lastIndex = startIndex;
    let depth = 0;
    let match;
    while ((match = tagPattern.exec(html))) {
      const tag = match[0];
      if (/^<\//.test(tag)) {
        depth -= 1;
        if (depth === 0) {
          return {
            start: startIndex,
            open_end: this.findHtmlTagEnd(html, startIndex),
            close_start: match.index,
            end: tagPattern.lastIndex,
          };
        }
        continue;
      }
      if (!/\/>$/.test(tag)) {
        depth += 1;
      }
    }
    return null;
  }

  findHtmlTagEnd(html, startIndex) {
    let quote = "";
    for (let index = startIndex; index < html.length; index += 1) {
      const character = html[index];
      if (quote) {
        if (character === quote) {
          quote = "";
        }
        continue;
      }
      if (character === '"' || character === "'") {
        quote = character;
      } else if (character === ">") {
        return index + 1;
      }
    }
    return -1;
  }

  extractTabOptions(navHtml) {
    const options = [];
    const linkPattern = /<a\b([^>]*)>([\s\S]*?)<\/a>/gi;
    let match;
    while ((match = linkPattern.exec(navHtml))) {
      const href = this.readHtmlAttribute(match[1], "href");
      const label = this.htmlFragmentToText(match[2]);
      if (!href.startsWith("#") || !label) {
        continue;
      }
      options.push({
        target_id: href.slice(1),
        label,
      });
    }
    return options;
  }

  extractTabPanes(html, contentBounds) {
    const panes = [];
    const divPattern = /<div\b[^>]*>/gi;
    divPattern.lastIndex = contentBounds.open_end;
    let match;
    while ((match = divPattern.exec(html)) && match.index < contentBounds.close_start) {
      if (this.readHtmlAttribute(match[0], "role") !== "tabpanel") {
        continue;
      }
      const paneBounds = this.findMatchingHtmlTag(html, match.index, "div");
      if (!paneBounds || paneBounds.end > contentBounds.close_start) {
        continue;
      }
      panes.push({
        id: this.readHtmlAttribute(match[0], "id"),
        inner_html: html.slice(paneBounds.open_end, paneBounds.close_start),
      });
      divPattern.lastIndex = paneBounds.end;
    }
    return panes;
  }

  readHtmlAttribute(tag, attributeName) {
    const escapedName = String(attributeName).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(`\\b${escapedName}\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)'|([^\\s>]+))`, "i");
    const match = pattern.exec(String(tag || ""));
    return match ? match[1] || match[2] || match[3] || "" : "";
  }

  hasHtmlClass(tag, className) {
    return this.readHtmlAttribute(tag, "class").split(/\s+/).includes(className);
  }

  htmlFragmentToText(html) {
    // 选项标签中也可能混入资源图标的 alt 文本；与正文使用同一清洗规则，
    // 例如将“花费 Info 情报 icon.png 情报60处理”还原为可读的“花费 情报60处理”。
    return this.cleanStoryMarkdown(this.rawParser.htmlToMarkdown(String(html || "")))
      .replace(/\s+/g, " ")
      .trim();
  }

  classifyHtmlTabBranch(options) {
    const labels = options.map((option) => String(option || "").trim());
    // “改版前/后”是 Wiki 对照资料，不是玩家可选路径，也不是游戏内状态。
    if (labels.length >= 2 && labels.every((label) => /^(?:改版前|改版后|旧版|新版)$/.test(label))) {
      return "source_version";
    }

    // 只有每一项都明确描述已记录的游戏状态时才标为状态分支。
    // 不把普通对话中的“会/不会”“愿意/不愿意”等玩家回答误判为状态。
    // 部分页面直接用“中央庭信任度已满／未满”或“战胜／未战胜某敌人”表达前置状态。
    // 只接受明确的完成态、解锁态或满值态后缀，避免把“同意／不同意”等普通回答误判为状态。
    const statePattern = /^(?:[（(].*(?:当前|一周目|多周目|已|未).*[）)]|(?:剧情战|战斗)(?:胜利|失败|战败)|(?:未)?战胜.+|(?:未)?全黑核|.*黑核(?:已丢失|未丢失|已获得|未获得)|(?:未)?集齐.+黑核|(?:已|未)解放.+|.+要求(?:已|未)?达成|.+(?:已满|未满|已达成|未达成|已完成|未完成|已开启|未开启|已解锁|未解锁)|(?:未)?满足.+条件|.+(?:死亡|存活)[（(].+[）)]|第[一二三四五六七0-9]+天(?:已|未|让|未让|选择|未选择).+|.+剧情选择.+|.+被.+(?:占领|攻占))$/;
    return labels.every((label) => statePattern.test(label))
      ? "state_condition"
      : "player_or_dialogue_choice";
  }

  lastMeaningfulLine(lines) {
    return [...lines].reverse().find((line) => String(line || "").trim()) || "";
  }

  renderHtmlChoiceTree(tree) {
    const branchLabel =
      tree.branch_type === "state_condition"
        ? "状态分支"
        : tree.branch_type === "source_version"
          ? "版本对照"
          : "选择分支";
    const itemLabel =
      tree.branch_type === "state_condition"
        ? "条件"
        : tree.branch_type === "source_version"
          ? "版本"
          : "选项";
    const nestingDescription = tree.parent_option
      ? `嵌套${branchLabel}：仅在上一层选择“${this.stripOuterChoiceQuotes(tree.parent_option)}”后出现；页面 Tab 结构已保留。`
      : `${tree.repeatable ? "可重复" : ""}${branchLabel}：页面 Tab 结构已保留；每项均对应下方独立来源文本。`;
    const rendered = [
      `> ${nestingDescription}`,
      "",
    ];

    for (const branch of tree.branches) {
      rendered.push(`#### ${itemLabel}：${branch.option}`, "", branch.response, "");
    }
    if (tree.exit_option && tree.exit_response) {
      rendered.push(`#### 结束选项：${tree.exit_option}`, "", tree.exit_response, "");
    }
    return this.trimBlankLines(rendered).join("\n");
  }

  structureChoiceTrees(markdown) {
    const lines = String(markdown || "").split(/\r?\n/);
    const choiceTrees = [];
    let markerIndex = 0;

    while (markerIndex < lines.length) {
      const conditionTokens = this.extractChoiceConditionTokens(lines[markerIndex]);
      if (conditionTokens.length < 2) {
        markerIndex += 1;
        continue;
      }

      const initialMenu = this.findMatchingChoiceMenuBefore(lines, markerIndex, conditionTokens);
      if (!initialMenu) {
        markerIndex += 1;
        continue;
      }

      const initialResponses = this.collectResponsesUntilReturnPrompt(
        lines,
        initialMenu.end + 1,
        markerIndex,
        initialMenu.options.length
      );
      if (!initialResponses) {
        markerIndex += 1;
        continue;
      }

      const repeatMenu = this.findMatchingChoiceMenuAfter(lines, markerIndex + 1, conditionTokens);
      if (!repeatMenu) {
        markerIndex += 1;
        continue;
      }

      const exitMarkerIndex = this.findExitConditionAfter(
        lines,
        repeatMenu.end + 1,
        repeatMenu.options,
        initialMenu.options
      );
      if (exitMarkerIndex < 0) {
        markerIndex += 1;
        continue;
      }

      const repeatedResponses = this.collectResponsesUntilReturnPrompt(
        lines,
        repeatMenu.end + 1,
        exitMarkerIndex,
        initialMenu.options.length
      );
      if (!repeatedResponses || !this.areEquivalentResponseGroups(initialResponses.responses, repeatedResponses.responses)) {
        markerIndex += 1;
        continue;
      }

      const exitTokens = this.extractChoiceConditionTokens(lines[exitMarkerIndex]);
      const exitOption = repeatMenu.options.find((option) =>
        exitTokens.some((token) => this.choiceOptionMatchesToken(option, token))
      );
      if (!exitOption) {
        markerIndex += 1;
        continue;
      }

      const sharedContinuation = this.trimBlankLines(
        lines.slice(repeatedResponses.endIndex + 1, exitMarkerIndex)
      );
      const renderedTree = this.renderChoiceTree(
        initialMenu.options,
        initialResponses.responses,
        sharedContinuation,
        exitOption
      );

      // 结束条件已由渲染后的“结束选项”完整表达，因此同时移除原条件行；其后的实际对白保持原样。
      lines.splice(initialMenu.start, exitMarkerIndex - initialMenu.start + 1, ...renderedTree);
      choiceTrees.push({
        tree_index: choiceTrees.length + 1,
        source_structure: "linear_text",
        branch_type: "player_or_dialogue_choice",
        repeatable: true,
        options: initialMenu.options,
        exit_option: exitOption,
        has_shared_continuation: sharedContinuation.length > 0,
        extraction_status: "verified_by_repeated_response_blocks",
      });
      markerIndex = initialMenu.start + renderedTree.length;
    }

    return {
      markdown: this.removeAdjacentDuplicateBlocks(lines.join("\n").replace(/\n{3,}/g, "\n\n").trim()),
      choiceTrees,
    };
  }

  // 识别“如果你的选择是……”的条件行。嵌套书名号场景只提取最内层的实际选项文本。
  extractChoiceConditionTokens(line) {
    const text = String(line || "").trim();
    if (!text.startsWith("如果你的选择是")) {
      return [];
    }

    return [...text.matchAll(/「([^「」]+)」/g)].map((match) => match[1].trim()).filter(Boolean);
  }

  findMatchingChoiceMenuBefore(lines, markerIndex, conditionTokens) {
    let matched = null;
    for (let index = 0; index < markerIndex; index += 1) {
      const menu = this.readChoiceMenu(lines, index);
      if (!menu) {
        continue;
      }
      if (this.menuMatchesConditionTokens(menu.options, conditionTokens)) {
        matched = menu;
      }
      index = menu.end;
    }
    return matched;
  }

  findMatchingChoiceMenuAfter(lines, startIndex, conditionTokens) {
    const endIndex = Math.min(lines.length, startIndex + 80);
    for (let index = startIndex; index < endIndex; index += 1) {
      const menu = this.readChoiceMenu(lines, index);
      if (!menu) {
        continue;
      }
      if (this.menuMatchesConditionTokens(menu.options, conditionTokens)) {
        return menu;
      }
      index = menu.end;
    }
    return null;
  }

  readChoiceMenu(lines, startIndex) {
    if (!/^\s*-\s+\S/.test(lines[startIndex] || "")) {
      return null;
    }

    const options = [];
    let index = startIndex;
    let lastOptionIndex = startIndex;
    while (index < lines.length) {
      const line = String(lines[index] || "").trim();
      if (!line) {
        index += 1;
        continue;
      }
      const match = /^-\s+(.+)$/.exec(line);
      if (!match) {
        break;
      }
      options.push(match[1].trim());
      lastOptionIndex = index;
      index += 1;
    }

    return options.length >= 2 ? { start: startIndex, end: lastOptionIndex, options } : null;
  }

  menuMatchesConditionTokens(options, conditionTokens) {
    return conditionTokens.every((token) => options.some((option) => this.choiceOptionMatchesToken(option, token)));
  }

  choiceOptionMatchesToken(option, token) {
    const normalizedOption = this.normalizeChoiceText(option);
    const normalizedToken = this.normalizeChoiceText(token);
    return normalizedOption === normalizedToken || normalizedOption.includes(normalizedToken);
  }

  normalizeChoiceText(value) {
    return String(value || "")
      .replace(/[「」『』“”"'‘’]/g, "")
      .replace(/[。！？!?…\s]/g, "")
      .trim();
  }

  collectResponsesUntilReturnPrompt(lines, startIndex, endIndex, expectedCount) {
    const returnIndexes = [];
    for (let index = startIndex; index < endIndex; index += 1) {
      if (this.isReturnPrompt(lines[index])) {
        returnIndexes.push(index);
      }
    }
    if (returnIndexes.length < expectedCount) {
      return null;
    }

    const responses = [];
    let cursor = startIndex;
    for (const returnIndex of returnIndexes.slice(0, expectedCount)) {
      const response = this.trimBlankLines(lines.slice(cursor, returnIndex));
      if (!response.length) {
        return null;
      }
      responses.push(response);
      cursor = returnIndex + 1;
    }

    return {
      responses,
      endIndex: returnIndexes[expectedCount - 1],
    };
  }

  isReturnPrompt(line) {
    const text = String(line || "").replace(/\s+/g, "").trim();
    return /(?:还想知道(?:别的)?事吗|还有什么(?:问题|想问的)|还需要了解|还要知道).*[？?]?$/.test(text);
  }

  findExitConditionAfter(lines, startIndex, menuOptions, repeatedOptions) {
    const extraOptions = menuOptions.filter(
      (option) => !repeatedOptions.some((repeated) => this.normalizeChoiceText(repeated) === this.normalizeChoiceText(option))
    );
    if (!extraOptions.length) {
      return -1;
    }

    const endIndex = Math.min(lines.length, startIndex + 320);
    for (let index = startIndex; index < endIndex; index += 1) {
      const tokens = this.extractChoiceConditionTokens(lines[index]);
      if (tokens.length !== 1) {
        continue;
      }
      if (extraOptions.some((option) => this.choiceOptionMatchesToken(option, tokens[0]))) {
        return index;
      }
    }
    return -1;
  }

  areEquivalentResponseGroups(firstGroup, secondGroup) {
    return firstGroup.length === secondGroup.length && firstGroup.every((response, index) => {
      return this.normalizeResponseBlock(response) === this.normalizeResponseBlock(secondGroup[index]);
    });
  }

  normalizeResponseBlock(lines) {
    return lines.join(" ").replace(/[\s，,。！？!?…“”"'‘’]/g, "").trim();
  }

  trimBlankLines(lines) {
    const result = [...lines];
    while (result.length && !String(result[0] || "").trim()) {
      result.shift();
    }
    while (result.length && !String(result.at(-1) || "").trim()) {
      result.pop();
    }
    return result;
  }

  renderChoiceTree(options, responses, sharedContinuation, exitOption) {
    const rendered = [
      "> 分支结构：以下选项可分别选择；每项回答后会返回选项列表。",
      "",
    ];

    for (let index = 0; index < options.length; index += 1) {
      rendered.push(`#### 选项：${options[index]}`, "", ...responses[index], "", "> 返回选项列表。", "");
    }

    if (sharedContinuation.length) {
      rendered.push("#### 完成前置选项后的共同内容", "", ...sharedContinuation, "");
    }

    rendered.push(`> 结束选项：选择「${this.stripOuterChoiceQuotes(exitOption)}」后，进入后续主线。`, "");
    return this.trimBlankLines(rendered);
  }

  stripOuterChoiceQuotes(option) {
    return String(option || "").replace(/^「|」$/g, "").trim();
  }

  // 未满足“重复回答可核对”条件的分支不强行重排，只将条件行标记为分支条件，保留来源顺序。
  normalizeResidualChoiceConditions(markdown) {
    return String(markdown || "")
      .split(/\r?\n/)
      .map((line) => {
        const tokens = this.extractChoiceConditionTokens(line);
        if (!tokens.length) {
          return line;
        }
        if (tokens.length === 1) {
          return `> 分支条件：选择「${tokens[0]}」后进入后续主线。`;
        }
        return `> 分支条件：${String(line || "").trim()}`;
      })
      .join("\n");
  }

  removeAdjacentDuplicateBlocks(markdown) {
    const blocks = String(markdown || "").split(/\n{2,}/);
    const result = [];

    for (const rawBlock of blocks) {
      const block = rawBlock.trim();
      if (!block) {
        continue;
      }

      const previous = result.at(-1) || "";
      const normalizedBlock = block.replace(/\s+/g, " ");
      const normalizedPrevious = previous.replace(/\s+/g, " ");
      if (!block.startsWith("#") && normalizedBlock === normalizedPrevious) {
        continue;
      }
      result.push(block);
    }

    return result.join("\n\n").trim();
  }

  buildFrontmatter(data) {
    const lines = ["---"];
    lines.push(`title: ${this.yamlScalar(data.title)}`);
    lines.push(`type: ${this.yamlScalar(data.type)}`);
    lines.push("source:");
    for (const source of data.source || []) {
      lines.push(`  - ${this.yamlScalar(source)}`);
    }
    lines.push(`source_url: ${this.yamlScalar(data.sourceUrl)}`);
    lines.push(`page_id: ${this.yamlScalar(data.pageId)}`);
    lines.push(`last_sync: ${this.yamlScalar(data.lastSync)}`);

    if (data.storyScope !== undefined) {
      lines.push(`story_scope: ${this.yamlScalar(data.storyScope)}`);
      lines.push(`route: ${this.yamlScalar(data.route)}`);
      lines.push(`chapter: ${this.yamlScalar(data.chapter)}`);
      lines.push(`day: ${this.yamlScalar(data.day)}`);
    }

    lines.push("categories:");
    for (const category of data.categories || []) {
      lines.push(`  - ${this.yamlScalar(category)}`);
    }

    if (data.legacyVideoEvidence !== undefined) {
      lines.push("legacy_video_evidence:");
      for (const evidence of data.legacyVideoEvidence || []) {
        lines.push(`  - ${this.yamlScalar(evidence)}`);
      }
    }

    if (data.manualStructureReference !== undefined) {
      lines.push(`manual_structure_reference: ${this.yamlScalar(data.manualStructureReference)}`);
    }

    lines.push("---");
    return lines.join("\n");
  }

  yamlScalar(value) {
    return JSON.stringify(String(value ?? ""));
  }
}

module.exports = {
  StoryParser,
};
