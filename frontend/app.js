import {
  buildProjectRecommendationsHtml,
  buildProjectRecommendationsText,
} from "./rendering.js";
import {
  buildButtonLabel,
  createRequestState,
  isAnyRequestPending,
  looksLikeStandaloneUrl,
  validateGitHubUsername,
  validateJobDescriptionInput,
  validateRecommendationInput,
} from "./workflow.js";

const form = document.getElementById("resume-form");
const formStatus = document.getElementById("form-status");
const githubUsernameInput = document.getElementById("github-username");
const jobDescriptionUrlInput = document.getElementById("job-description-url");
const jobDescriptionTextInput = document.getElementById("job-description");
const githubOutput = document.getElementById("github-output");
const jobDescriptionOutput = document.getElementById("job-description-output");
const recommendationsOutput = document.getElementById("recommendations-output");
const recommendationsTextOutput = document.getElementById("recommendations-text-output");
const fetchGitHubButton = document.getElementById("fetch-github");
const parseJobDescriptionButton = document.getElementById("parse-job-description");
const copyAllButton = document.getElementById("copy-all-bullets");

let latestRecommendations = [];
let autoJobDescriptionTimer = null;

const requestState = createRequestState();
const defaultFormStatus =
  "Add a GitHub username and target job description to get ranked projects with copy-pasteable bullets.";

function setFormStatus(message, tone = "neutral") {
  formStatus.textContent = message;
  formStatus.dataset.tone = tone;
}

function setButtonPending(button, isPending, idleLabel, loadingLabel) {
  button.disabled = isPending;
  button.textContent = buildButtonLabel(isPending, idleLabel, loadingLabel);
}

function setAppBusyState() {
  const recommendInFlight = requestState.recommend;

  setButtonPending(fetchGitHubButton, requestState.github || recommendInFlight, "Fetch Projects", "Fetching...");
  setButtonPending(
    parseJobDescriptionButton,
    requestState.jobDescription || recommendInFlight,
    "Fetch JD",
    "Fetching..."
  );
  setButtonPending(
    form.querySelector('button[type="submit"]'),
    recommendInFlight,
    "Rank Projects + Draft Bullets",
    "Ranking..."
  );

  copyAllButton.disabled = recommendInFlight || latestRecommendations.length === 0;
  form.classList.toggle("is-busy", isAnyRequestPending(requestState));
}

function setRecommendations(projects) {
  latestRecommendations = Array.isArray(projects) ? projects : [];
  recommendationsOutput.innerHTML = buildProjectRecommendationsHtml(latestRecommendations);
  recommendationsTextOutput.textContent =
    buildProjectRecommendationsText(latestRecommendations) || "Copy-ready project bullets will appear here.";
  setAppBusyState();
}

async function copyText(text, successLabel, button) {
  try {
    await navigator.clipboard.writeText(text);
    const idleLabel = button.dataset.idleLabel || button.textContent;
    button.textContent = successLabel;
    window.setTimeout(() => {
      button.textContent = idleLabel;
    }, 1200);
  } catch {
    button.textContent = "Unavailable";
  }
}

async function fetchGitHubPreview() {
  const githubUsername = githubUsernameInput.value.trim();
  const validationError = validateGitHubUsername(githubUsername);

  if (validationError) {
    githubOutput.textContent = validationError;
    setFormStatus(validationError, "error");
    return;
  }

  requestState.github = true;
  setAppBusyState();
  setFormStatus("Fetching GitHub projects...", "loading");
  githubOutput.textContent = "Fetching GitHub projects...";

  try {
    const response = await fetch(`http://127.0.0.1:8000/github/${encodeURIComponent(githubUsername)}`);

    if (!response.ok) {
      const errorPayload = await response.json();
      throw new Error(errorPayload.detail || "GitHub preview failed");
    }

    const data = await response.json();
    githubOutput.textContent = data.summary || "No repositories found for this user.";
    setFormStatus("GitHub project summary loaded.", "success");
  } catch (error) {
    githubOutput.textContent =
      error.message || "Unable to fetch GitHub projects right now. Check the backend connection and username.";
    setFormStatus(githubOutput.textContent, "error");
  } finally {
    requestState.github = false;
    setAppBusyState();
  }
}

async function parseJobDescriptionPreview() {
  const jobDescriptionText = jobDescriptionTextInput.value.trim();
  const jobDescriptionUrl = jobDescriptionUrlInput.value.trim();
  const validationError = validateJobDescriptionInput(jobDescriptionText, jobDescriptionUrl);

  if (validationError) {
    jobDescriptionOutput.textContent = validationError;
    setFormStatus(validationError, "error");
    return;
  }

  requestState.jobDescription = true;
  setAppBusyState();
  setFormStatus("Preparing the job description...", "loading");
  jobDescriptionOutput.textContent = "Preparing job description...";

  try {
    const response = await fetch("http://127.0.0.1:8000/parse-job-description", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        jobDescriptionText,
        jobDescriptionUrl,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Job description parse failed");
    }

    jobDescriptionOutput.textContent = [
      `Source: ${data.source}${data.url ? ` (${data.url})` : ""}`,
      `Line count: ${data.lineCount}`,
      "",
      "Content preview:",
      data.content.slice(0, 1200),
    ].join("\n");

    if (data.content && data.source === "url") {
      jobDescriptionTextInput.value = data.content;
    }
    setFormStatus("Job description prepared successfully.", "success");
  } catch (error) {
    jobDescriptionOutput.textContent =
      error.message || "Unable to fetch or clean the job description right now.";
    setFormStatus(jobDescriptionOutput.textContent, "error");
  } finally {
    requestState.jobDescription = false;
    setAppBusyState();
  }
}

function scheduleJobDescriptionAutoFetch() {
  const jobDescriptionText = jobDescriptionTextInput.value.trim();
  const jobDescriptionUrl = jobDescriptionUrlInput.value.trim();
  const validationError = validateJobDescriptionInput(jobDescriptionText, jobDescriptionUrl);

  if (validationError || !jobDescriptionUrl) {
    return;
  }

  window.clearTimeout(autoJobDescriptionTimer);
  autoJobDescriptionTimer = window.setTimeout(() => {
    parseJobDescriptionPreview();
  }, 250);
}

function maybePromoteJobLinkFromTextarea() {
  const value = jobDescriptionTextInput.value.trim();
  if (!looksLikeStandaloneUrl(value)) {
    return;
  }

  jobDescriptionUrlInput.value = value;
  jobDescriptionTextInput.value = "";
  scheduleJobDescriptionAutoFetch();
}

async function rankProjectsAndDraftBullets(event) {
  event.preventDefault();

  const githubUsername = githubUsernameInput.value.trim();
  const jobDescription = jobDescriptionTextInput.value.trim();
  const validationError = validateRecommendationInput(githubUsername, jobDescription);

  if (validationError) {
    setFormStatus(validationError, "error");
    return;
  }

  requestState.recommend = true;
  setAppBusyState();
  setFormStatus("Ranking projects and drafting resume bullets...", "loading");
  setRecommendations([]);
  recommendationsTextOutput.textContent = "Ranking projects and drafting copy-pasteable bullets...";

  try {
    const response = await fetch("http://127.0.0.1:8000/recommend-projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        githubUsername,
        jobDescription,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Project recommendations failed");
    }

    setRecommendations(data.rankedProjects || []);
    setFormStatus("Ranked project bullets are ready to copy into your resume.", "success");
  } catch (error) {
    recommendationsOutput.innerHTML =
      '<p class="recommendations-empty">Unable to generate ranked project bullets right now.</p>';
    recommendationsTextOutput.textContent = error.message || "Project recommendations failed.";
    setFormStatus(recommendationsTextOutput.textContent, "error");
  } finally {
    requestState.recommend = false;
    setAppBusyState();
  }
}

fetchGitHubButton.dataset.idleLabel = "Fetch Projects";
parseJobDescriptionButton.dataset.idleLabel = "Fetch JD";
copyAllButton.dataset.idleLabel = "Copy All Bullets";

fetchGitHubButton.addEventListener("click", fetchGitHubPreview);
parseJobDescriptionButton.addEventListener("click", parseJobDescriptionPreview);
jobDescriptionUrlInput.addEventListener("change", scheduleJobDescriptionAutoFetch);
jobDescriptionUrlInput.addEventListener("paste", () => {
  window.setTimeout(scheduleJobDescriptionAutoFetch, 0);
});
jobDescriptionTextInput.addEventListener("blur", maybePromoteJobLinkFromTextarea);
jobDescriptionTextInput.addEventListener("paste", () => {
  window.setTimeout(maybePromoteJobLinkFromTextarea, 0);
});
form.addEventListener("submit", rankProjectsAndDraftBullets);
copyAllButton.addEventListener("click", () => {
  copyText(buildProjectRecommendationsText(latestRecommendations), "Copied All", copyAllButton);
});
recommendationsOutput.addEventListener("click", (event) => {
  const button = event.target.closest(".project-copy-button");
  if (!button) {
    return;
  }

  const projectName = button.dataset.projectName || "";
  const project = latestRecommendations.find((entry) => entry.name === projectName);
  if (!project) {
    return;
  }

  button.dataset.idleLabel = "Copy Bullets";
  const text = (project.bullets || []).map((bullet) => `● ${bullet}`).join("\n");
  copyText(text, "Copied", button);
});

setRecommendations([]);
setFormStatus(defaultFormStatus, "neutral");
setAppBusyState();
