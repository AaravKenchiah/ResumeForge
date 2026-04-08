import test from "node:test";
import assert from "node:assert/strict";

import { buildGapAnalysisHtml, buildGapSummaryText, buildSkillChip } from "../../frontend/gapAnalysis.js";

test("buildSkillChip renders escaped skill labels", () => {
  const html = buildSkillChip("C&C++", "matched");
  assert.match(html, /skill-chip--matched/);
  assert.match(html, /C&amp;C\+\+/);
});

test("buildGapAnalysisHtml renders matched and missing skill sections", () => {
  const html = buildGapAnalysisHtml({
    matchedSkills: ["python", "fastapi"],
    missingSkills: ["aws"],
    matchCount: 2,
    missingCount: 1,
  });

  assert.match(html, /Matched Skills/);
  assert.match(html, /skill-chip--matched/);
  assert.match(html, /skill-chip--missing/);
  assert.match(html, /aws/);
});

test("buildGapSummaryText renders concise counts", () => {
  assert.equal(buildGapSummaryText({ matchCount: 3, missingCount: 2 }), "3 matched, 2 missing skills");
});
