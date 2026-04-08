/**
 * Frontend helpers for rendering skill-gap analysis results.
 */

import { escapeHtml } from "./rendering.js";

export function buildSkillChip(label, tone = "neutral") {
  return `<span class="skill-chip skill-chip--${tone}">${escapeHtml(label)}</span>`;
}

export function buildGapAnalysisHtml(analysis) {
  if (!analysis || (!analysis.matchCount && !analysis.missingCount)) {
    return '<p class="gap-empty">No skill-gap analysis yet. Generate a tailored resume or run a gap analysis first.</p>';
  }

  const matched = (analysis.matchedSkills || []).map((skill) => buildSkillChip(skill, "matched")).join("");
  const missing = (analysis.missingSkills || []).map((skill) => buildSkillChip(skill, "missing")).join("");

  return `
    <div class="gap-block">
      <h3 class="gap-heading">Matched Skills</h3>
      <div class="gap-chip-row">${matched || '<span class="gap-fallback">No matched skills detected.</span>'}</div>
    </div>
    <div class="gap-block">
      <h3 class="gap-heading">Missing Skills</h3>
      <div class="gap-chip-row">${missing || '<span class="gap-fallback">No missing skills detected.</span>'}</div>
    </div>
  `;
}

export function buildGapSummaryText(analysis) {
  if (!analysis) {
    return "No skill-gap analysis yet.";
  }

  return `${analysis.matchCount || 0} matched, ${analysis.missingCount || 0} missing skills`;
}
