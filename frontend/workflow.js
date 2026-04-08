/**
 * Frontend workflow helpers for validation and loading state management.
 */

export function hasMeaningfulText(value) {
  return Boolean(value && value.trim());
}

export function isValidHttpUrl(value) {
  if (!hasMeaningfulText(value)) {
    return false;
  }

  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function looksLikeStandaloneUrl(value) {
  const trimmed = value.trim();
  return Boolean(trimmed) && !trimmed.includes("\n") && isValidHttpUrl(trimmed);
}

export function validateGitHubUsername(username) {
  if (!hasMeaningfulText(username)) {
    return "Enter a GitHub username to preview projects.";
  }

  return "";
}

export function validateResumeInput(resumeText, resumeFile) {
  if (!hasMeaningfulText(resumeText) && !resumeFile) {
    return "Paste resume text or upload a .txt, .md, or .pdf file first.";
  }

  return "";
}

export function validateJobDescriptionInput(jobDescriptionText, jobDescriptionUrl) {
  if (!hasMeaningfulText(jobDescriptionText) && !hasMeaningfulText(jobDescriptionUrl)) {
    return "Paste a job description or provide a job-posting URL first.";
  }

  if (hasMeaningfulText(jobDescriptionUrl) && !isValidHttpUrl(jobDescriptionUrl)) {
    return "Enter a valid http:// or https:// job-posting URL.";
  }

  return "";
}

export function validateTailorInput(resumeText, jobDescriptionText) {
  if (!hasMeaningfulText(resumeText) && !hasMeaningfulText(jobDescriptionText)) {
    return "Add both resume text and a job description before generating a tailored resume.";
  }

  if (!hasMeaningfulText(resumeText)) {
    return "Add resume text or parse a resume file before generating.";
  }

  if (!hasMeaningfulText(jobDescriptionText)) {
    return "Add a job description or fetch one from a URL before generating.";
  }

  return "";
}

export function validateRecommendationInput(githubUsername, jobDescriptionText) {
  if (!hasMeaningfulText(githubUsername) && !hasMeaningfulText(jobDescriptionText)) {
    return "Add a GitHub username and a job description before ranking projects.";
  }

  if (!hasMeaningfulText(githubUsername)) {
    return "Add a GitHub username before ranking projects.";
  }

  if (!hasMeaningfulText(jobDescriptionText)) {
    return "Add a job description or fetch one from a URL before ranking projects.";
  }

  return "";
}

export function createRequestState() {
  return {
    github: false,
    resume: false,
    jobDescription: false,
    tailor: false,
    recommend: false,
    gapAnalysis: false,
    docx: false,
  };
}

export function isAnyRequestPending(state) {
  return Object.values(state).some(Boolean);
}

export function buildButtonLabel(isPending, idleLabel, loadingLabel) {
  return isPending ? loadingLabel : idleLabel;
}
