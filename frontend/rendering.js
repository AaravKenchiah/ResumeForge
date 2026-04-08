/**
 * Pure helpers for rendering and exporting tailored resume output.
 */

export function normalizeResumeText(text) {
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
}

export function isLikelyHeading(line) {
  const trimmed = line.trim();
  if (!trimmed) {
    return false;
  }

  if (/^[-*•▪◦]\s+/.test(trimmed)) {
    return false;
  }

  const words = trimmed.split(/\s+/);
  return words.length <= 5 && trimmed === trimmed.toUpperCase() && /[A-Z]/.test(trimmed);
}

export function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function buildResumeHtml(text) {
  const normalized = normalizeResumeText(text);
  if (!normalized) {
    return "<p class=\"resume-empty\">Your tailored resume will appear here.</p>";
  }

  const lines = normalized.split("\n");
  const fragments = [];
  let inList = false;

  const closeListIfNeeded = () => {
    if (inList) {
      fragments.push("</ul>");
      inList = false;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeListIfNeeded();
      continue;
    }

    if (/^[-*•▪◦]\s+/.test(trimmed)) {
      if (!inList) {
        fragments.push("<ul class=\"resume-list\">");
        inList = true;
      }

      fragments.push(`<li>${escapeHtml(trimmed.replace(/^[-*•▪◦]\s+/, ""))}</li>`);
      continue;
    }

    closeListIfNeeded();

    if (isLikelyHeading(trimmed)) {
      fragments.push(`<h3 class="resume-heading">${escapeHtml(trimmed)}</h3>`);
      continue;
    }

    fragments.push(`<p class="resume-line">${escapeHtml(trimmed)}</p>`);
  }

  closeListIfNeeded();
  return fragments.join("");
}

export function buildMarkdownFileContent(text) {
  return `${normalizeResumeText(text)}\n`;
}

export function buildMarkdownFilename(prefix = "tailored_resume", stamp = "export") {
  const safePrefix = prefix.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  const safeStamp = stamp.toLowerCase().replace(/[^a-z0-9-]+/g, "_");
  return `${safePrefix || "tailored_resume"}_${safeStamp || "export"}.md`;
}

export function buildPrintDocument(title, bodyHtml) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>${escapeHtml(title)}</title>
    <style>
      body {
        margin: 0;
        padding: 0;
        background: #ffffff;
        color: #111111;
        font-family: Georgia, "Times New Roman", serif;
      }
      .page {
        width: 8.5in;
        min-height: 11in;
        margin: 0 auto;
        padding: 0.7in;
        box-sizing: border-box;
      }
      .resume-heading {
        margin: 1.2rem 0 0.45rem;
        font-size: 0.95rem;
        letter-spacing: 0.08em;
      }
      .resume-line,
      .resume-list {
        margin: 0.32rem 0;
        line-height: 1.45;
        font-size: 0.95rem;
      }
      .resume-list {
        padding-left: 1.2rem;
      }
      .resume-empty {
        color: #666666;
      }
      @page {
        size: letter;
        margin: 0;
      }
    </style>
  </head>
  <body>
    <main class="page">${bodyHtml}</main>
  </body>
</html>`;
}

export function buildProjectRecommendationsHtml(projects) {
  if (!Array.isArray(projects) || projects.length === 0) {
    return "<p class=\"recommendations-empty\">Ranked GitHub project bullets will appear here.</p>";
  }

  return projects
    .map((project) => {
      const bullets = (project.bullets || [])
        .map((bullet) => `<li>${escapeHtml(bullet)}</li>`)
        .join("");

      const meta = [project.language, project.url].filter(Boolean).map(escapeHtml).join(" · ");

      return `<article class="project-card">
        <div class="project-card-header">
          <div>
            <p class="project-rank">Rank #${escapeHtml(String(project.rank || ""))}</p>
            <h3 class="project-title">${escapeHtml(project.name || "Untitled Project")}</h3>
            ${meta ? `<p class="project-meta">${meta}</p>` : ""}
          </div>
          <button type="button" class="secondary-button project-copy-button" data-project-name="${escapeHtml(project.name || "")}">Copy Bullets</button>
        </div>
        ${
          project.relevanceSummary
            ? `<p class="project-summary">${escapeHtml(project.relevanceSummary)}</p>`
            : ""
        }
        <ul class="project-bullet-list">${bullets}</ul>
      </article>`;
    })
    .join("");
}

export function buildProjectRecommendationsText(projects) {
  if (!Array.isArray(projects) || projects.length === 0) {
    return "";
  }

  return projects
    .map((project) => {
      const lines = [
        `#${project.rank} ${project.name}`,
        project.relevanceSummary ? `Why it fits: ${project.relevanceSummary}` : "",
        ...(project.bullets || []).map((bullet) => `● ${bullet}`),
      ].filter(Boolean);

      return lines.join("\n");
    })
    .join("\n\n");
}
