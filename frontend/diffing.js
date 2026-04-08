/**
 * Helpers for line-level resume diffing.
 */

import { escapeHtml, normalizeResumeText } from "./rendering.js";

export function buildLineDiffRows(originalText, tailoredText) {
  const originalLines = normalizeResumeText(originalText).split("\n").filter(Boolean);
  const tailoredLines = normalizeResumeText(tailoredText).split("\n").filter(Boolean);
  const maxLength = Math.max(originalLines.length, tailoredLines.length);
  const rows = [];

  for (let index = 0; index < maxLength; index += 1) {
    const originalLine = originalLines[index] || "";
    const tailoredLine = tailoredLines[index] || "";

    let status = "unchanged";
    if (!originalLine && tailoredLine) {
      status = "added";
    } else if (originalLine && !tailoredLine) {
      status = "removed";
    } else if (originalLine !== tailoredLine) {
      status = "changed";
    }

    rows.push({
      lineNumber: index + 1,
      originalLine,
      tailoredLine,
      status,
    });
  }

  return rows;
}

export function summarizeDiffRows(rows) {
  return rows.reduce(
    (summary, row) => {
      summary[row.status] += 1;
      return summary;
    },
    { unchanged: 0, changed: 0, added: 0, removed: 0 }
  );
}

export function buildDiffHtml(rows) {
  if (!rows.length) {
    return '<p class="diff-empty">Generate a tailored resume to compare changes.</p>';
  }

  const body = rows
    .map(
      (row) => `
        <div class="diff-row diff-row--${row.status}">
          <div class="diff-cell diff-line-number">${row.lineNumber}</div>
          <div class="diff-cell diff-original">${escapeHtml(row.originalLine || " ")}</div>
          <div class="diff-cell diff-tailored">${escapeHtml(row.tailoredLine || " ")}</div>
        </div>
      `
    )
    .join("");

  return `
    <div class="diff-grid diff-grid--header">
      <div class="diff-cell diff-line-number">#</div>
      <div class="diff-cell diff-original">Original Resume</div>
      <div class="diff-cell diff-tailored">Tailored Resume</div>
    </div>
    <div class="diff-grid">${body}</div>
  `;
}
