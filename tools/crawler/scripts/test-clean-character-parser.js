const assert = require("node:assert/strict");
const { CleanCharacterParser } = require("../src/clean-character-parser");

const parser = new CleanCharacterParser();

// 连续的角色分类导航墙应被整体移除。
const navigationPollution = [
  "神器正文保留。",
  "神器使",
  "战士",
  "物理",
  "联动",
  "法术",
  "坦克",
  "异界体",
  "后续正文保留。",
].join("\n");
assert.equal(parser.cleanBlock(navigationPollution), "神器正文保留。\n后续正文保留。");

// 正文中偶然出现的短分类词不应被误删。
const legitimateText = [
  "她是一名战士。",
  "物理",
  "这一词在资料说明中单独出现。",
].join("\n");
assert.equal(parser.cleanBlock(legitimateText), legitimateText);

// 没有“神器使”起始标签的普通列表不应被当成导航墙。
const ordinaryList = ["战士", "物理", "法术", "辅助", "射手", "坦克"].join("\n");
assert.equal(parser.cleanBlock(ordinaryList), ordinaryList);

console.log("CleanCharacterParser 导航标签清洗测试通过（3/3）。");
