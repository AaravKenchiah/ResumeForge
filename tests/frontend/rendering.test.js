import test from "node:test";
import assert from "node:assert/strict";

import {
  buildProjectRecommendationsHtml,
  buildProjectRecommendationsText,
  buildMarkdownFileContent,
  buildMarkdownFilename,
  buildPrintDocument,
  buildResumeHtml,
  escapeHtml,
  isLikelyHeading,
  normalizeResumeText,
} from "../../frontend/rendering.js";

test("normalizeResumeText standardizes line endings and trims edges", () => {
  assert.equal(normalizeResumeText(" \r\nA\r\nB\r\n"), "A\nB");
});

test("isLikelyHeading detects uppercase headings but not bullets", () => {
  assert.equal(isLikelyHeading("EXPERIENCE"), true);
  assert.equal(isLikelyHeading("- Built APIs"), false);
});

test("escapeHtml escapes special characters", () => {
  assert.equal(escapeHtml("<Engineer & Builder>"), "&lt;Engineer &amp; Builder&gt;");
});

test("buildResumeHtml renders headings, paragraphs, and bullet lists", () => {
  const html = buildResumeHtml("JANE DOE\nEXPERIENCE\nSoftware Engineer\n- Built APIs\n- Improved latency");

  assert.match(html, /<h3 class="resume-heading">JANE DOE<\/h3>/);
  assert.match(html, /<h3 class="resume-heading">EXPERIENCE<\/h3>/);
  assert.match(html, /<p class="resume-line">Software Engineer<\/p>/);
  assert.match(html, /<ul class="resume-list">/);
  assert.match(html, /<li>Built APIs<\/li>/);
});

test("buildMarkdownFileContent preserves text and trailing newline", () => {
  assert.equal(buildMarkdownFileContent("A\r\nB"), "A\nB\n");
});

test("buildMarkdownFilename sanitizes prefix and stamp", () => {
  assert.equal(buildMarkdownFilename("Resume Forge", "2026-04-08"), "resume_forge_2026-04-08.md");
});

test("buildPrintDocument returns printable html", () => {
  const documentHtml = buildPrintDocument("Resume Export", "<h3 class=\"resume-heading\">EXPERIENCE</h3>");

  assert.match(documentHtml, /<title>Resume Export<\/title>/);
  assert.match(documentHtml, /class="page"/);
  assert.match(documentHtml, /EXPERIENCE/);
});

test("buildProjectRecommendationsHtml renders ranked project cards", () => {
  const html = buildProjectRecommendationsHtml([
    {
      rank: 1,
      name: "resume-forge",
      relevanceSummary: "Strong fit for an applied AI workflow role.",
      language: "Python",
      url: "https://github.com/test/resume-forge",
      bullets: ["Built a FastAPI workflow", "Connected GitHub and Gemini inputs"],
    },
  ]);

  assert.match(html, /Rank #1/);
  assert.match(html, /resume-forge/);
  assert.match(html, /Built a FastAPI workflow/);
});

test("buildProjectRecommendationsText returns copyable bullets", () => {
  const text = buildProjectRecommendationsText([
    {
      rank: 1,
      name: "resume-forge",
      relevanceSummary: "Strong fit.",
      bullets: ["Built a FastAPI workflow", "Connected GitHub and Gemini inputs"],
    },
  ]);

  assert.match(text, /#1 resume-forge/);
  assert.match(text, /● Built a FastAPI workflow/);
});
