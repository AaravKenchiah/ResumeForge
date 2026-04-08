import test from "node:test";
import assert from "node:assert/strict";

import { buildDiffHtml, buildLineDiffRows, summarizeDiffRows } from "../../frontend/diffing.js";

test("buildLineDiffRows marks changed, added, removed, and unchanged lines", () => {
  const rows = buildLineDiffRows(
    "SUMMARY\nBuilt APIs\nEDUCATION",
    "SUMMARY\nBuilt scalable APIs\nEDUCATION\nAWS Certified"
  );

  assert.equal(rows[0].status, "unchanged");
  assert.equal(rows[1].status, "changed");
  assert.equal(rows[2].status, "unchanged");
  assert.equal(rows[3].status, "added");
});

test("summarizeDiffRows counts each diff status", () => {
  const summary = summarizeDiffRows([
    { status: "unchanged" },
    { status: "changed" },
    { status: "changed" },
    { status: "added" },
    { status: "removed" },
  ]);

  assert.deepEqual(summary, {
    unchanged: 1,
    changed: 2,
    added: 1,
    removed: 1,
  });
});

test("buildDiffHtml renders comparison columns", () => {
  const html = buildDiffHtml(
    buildLineDiffRows("SUMMARY\nBuilt APIs", "SUMMARY\nBuilt scalable APIs")
  );

  assert.match(html, /Original Resume/);
  assert.match(html, /Tailored Resume/);
  assert.match(html, /diff-row--changed/);
  assert.match(html, /Built scalable APIs/);
});
