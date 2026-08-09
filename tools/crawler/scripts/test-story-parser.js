const assert = require("node:assert/strict");
const { StoryParser } = require("../src/story-parser");

// 回归场景：灰机 Wiki 某些旧页面没有及时闭合 tab-content，导致后续正文仍位于外层容器中。
// 解析器必须只替换实际的分支面板，不能把后续章节一起吞掉。
const malformedWikiHtml = `
<h2>分支前章节</h2>
<ul class="nav nav-tabs" role="tablist">
  <li><a href="#route-a">路线 A</a></li>
  <li><a href="#route-b">路线 B</a></li>
</ul>
<div class="tab-content">
  <div id="route-a" role="tabpanel" class="tab-pane active"><p>路线 A 正文</p></div>
  <div id="route-b" role="tabpanel" class="tab-pane"><p>路线 B 正文</p></div>
  <h2>分支后章节</h2>
  <p>这段正文必须被保留。</p>
</div>
`;

const parser = new StoryParser();
const result = parser.convertStoryHtmlWithChoiceTrees(malformedWikiHtml, "");

assert.equal(result.choiceTrees.length, 1, "应识别一棵选择树");
assert.deepEqual(result.choiceTrees[0].options, ["路线 A", "路线 B"]);
assert.match(result.markdown, /路线 A 正文/);
assert.match(result.markdown, /路线 B 正文/);
assert.match(result.markdown, /分支后章节/);
assert.match(result.markdown, /这段正文必须被保留/);

console.log("StoryParser 非规范 Tab 页面回归测试通过。");
