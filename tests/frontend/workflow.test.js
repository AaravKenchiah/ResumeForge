import test from "node:test";
import assert from "node:assert/strict";

import {
  buildButtonLabel,
  createRequestState,
  hasMeaningfulText,
  isAnyRequestPending,
  isValidHttpUrl,
  looksLikeStandaloneUrl,
  validateRecommendationInput,
  validateGitHubUsername,
  validateJobDescriptionInput,
  validateResumeInput,
  validateTailorInput,
} from "../../frontend/workflow.js";

test("hasMeaningfulText ignores blank input", () => {
  assert.equal(hasMeaningfulText("   "), false);
  assert.equal(hasMeaningfulText("resume"), true);
});

test("isValidHttpUrl accepts http and https URLs only", () => {
  assert.equal(isValidHttpUrl("https://company.com/job"), true);
  assert.equal(isValidHttpUrl("http://company.com/job"), true);
  assert.equal(isValidHttpUrl("ftp://company.com/job"), false);
  assert.equal(isValidHttpUrl("not-a-url"), false);
});

test("looksLikeStandaloneUrl accepts single-line urls only", () => {
  assert.equal(looksLikeStandaloneUrl("https://company.com/job"), true);
  assert.equal(looksLikeStandaloneUrl("https://company.com/job\nmore"), false);
  assert.equal(looksLikeStandaloneUrl("job text"), false);
});

test("validateGitHubUsername requires a value", () => {
  assert.equal(validateGitHubUsername(""), "Enter a GitHub username to preview projects.");
  assert.equal(validateGitHubUsername("janedev"), "");
});

test("validateResumeInput requires text or file", () => {
  assert.equal(
    validateResumeInput("", null),
    "Paste resume text or upload a .txt, .md, or .pdf file first."
  );
  assert.equal(validateResumeInput("resume text", null), "");
  assert.equal(validateResumeInput("", { name: "resume.pdf" }), "");
});

test("validateJobDescriptionInput checks presence and url format", () => {
  assert.equal(
    validateJobDescriptionInput("", ""),
    "Paste a job description or provide a job-posting URL first."
  );
  assert.equal(
    validateJobDescriptionInput("", "company"),
    "Enter a valid http:// or https:// job-posting URL."
  );
  assert.equal(validateJobDescriptionInput("jd text", ""), "");
  assert.equal(validateJobDescriptionInput("", "https://company.com/job"), "");
});

test("validateTailorInput requires both resume and job description", () => {
  assert.equal(
    validateTailorInput("", ""),
    "Add both resume text and a job description before generating a tailored resume."
  );
  assert.equal(
    validateTailorInput("", "job description"),
    "Add resume text or parse a resume file before generating."
  );
  assert.equal(
    validateTailorInput("resume text", ""),
    "Add a job description or fetch one from a URL before generating."
  );
  assert.equal(validateTailorInput("resume text", "job description"), "");
});

test("validateRecommendationInput requires github username and job description", () => {
  assert.equal(
    validateRecommendationInput("", ""),
    "Add a GitHub username and a job description before ranking projects."
  );
  assert.equal(validateRecommendationInput("", "job description"), "Add a GitHub username before ranking projects.");
  assert.equal(
    validateRecommendationInput("janedev", ""),
    "Add a job description or fetch one from a URL before ranking projects."
  );
  assert.equal(validateRecommendationInput("janedev", "job description"), "");
});

test("request state helpers track pending work", () => {
  const state = createRequestState();
  assert.equal(isAnyRequestPending(state), false);
  state.resume = true;
  assert.equal(isAnyRequestPending(state), true);
});

test("buildButtonLabel switches labels based on pending state", () => {
  assert.equal(buildButtonLabel(true, "Fetch", "Fetching..."), "Fetching...");
  assert.equal(buildButtonLabel(false, "Fetch", "Fetching..."), "Fetch");
});
