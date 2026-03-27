const INTAKE_ENDPOINT = "http://127.0.0.1:8765/intake";
const DEFAULT_TITLE = "Send to Resume Tailor";
const BADGE_CLEAR_DELAY_MS = 4500;

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) {
    return;
  }

  if (!tab.url || !/^https?:/i.test(tab.url)) {
    setBadge(tab.id, "ERR", "#b91c1c", "Open a job posting page before sending it.");
    clearBadgeLater(tab.id);
    return;
  }

  try {
    setBadge(tab.id, "...", "#1d4ed8", "Capturing the current job posting...");

    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractJobPageData,
    });
    const payload = injectionResults?.[0]?.result;

    if (!payload) {
      throw new Error("The page did not return any capture data.");
    }

    const response = await fetch(INTAKE_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const rawResponseText = await response.text();
    let parsedResponse = null;
    if (rawResponseText) {
      try {
        parsedResponse = JSON.parse(rawResponseText);
      } catch (error) {
        parsedResponse = null;
      }
    }

    if (!response.ok) {
      const detail = parsedResponse?.detail || rawResponseText || `HTTP ${response.status}`;
      throw new Error(detail);
    }

    console.info("Resume Tailor intake saved:", parsedResponse);
    setBadge(
      tab.id,
      "OK",
      "#15803d",
      parsedResponse?.message || "Saved to the local Resume Tailor queue."
    );
  } catch (error) {
    console.error("Resume Tailor capture failed:", error);
    const message = error && error.message ? error.message : "Unknown error";
    setBadge(tab.id, "ERR", "#b91c1c", `Send to Resume Tailor failed: ${message}`);
  }

  clearBadgeLater(tab.id);
});

function setBadge(tabId, text, color, title) {
  chrome.action.setBadgeText({ tabId, text });
  chrome.action.setBadgeBackgroundColor({ tabId, color });
  chrome.action.setTitle({ tabId, title: title || DEFAULT_TITLE });
}

function clearBadgeLater(tabId) {
  setTimeout(() => {
    chrome.action.setBadgeText({ tabId, text: "" });
    chrome.action.setTitle({ tabId, title: DEFAULT_TITLE });
  }, BADGE_CLEAR_DELAY_MS);
}

function extractJobPageData() {
  const DESCRIPTION_SELECTORS = [
    "#jobDescriptionText",
    "[data-testid='job-description']",
    "[data-testid='JobDescription']",
    "[data-testid*='job-description']",
    "[data-testid*='jobDescription']",
    ".show-more-less-html__markup",
    ".jobs-description",
    ".jobs-box__html-content",
    ".description__text",
    "[id*='jobDescription']",
    "[id*='job-description']",
    "[class*='job-description']",
    "[class*='jobDescription']",
    "article",
    "main",
    "[role='main']"
  ];
  const TITLE_SELECTORS = [
    "h1",
    "[data-testid='job-title']",
    "[data-testid='jobTitle']",
    "[class*='job-title']",
    "[class*='jobTitle']"
  ];
  const COMPANY_SELECTORS = [
    "[data-testid='company-name']",
    "[data-testid='companyName']",
    "[data-testid*='company']",
    "[class*='company']",
    "[class*='employer']",
    "[class*='subtitle']"
  ];

  function normalizeInlineText(value) {
    return (value || "")
      .replace(/\u00a0/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function normalizeBlockText(value) {
    if (!value) {
      return "";
    }

    const lines = String(value)
      .replace(/\u00a0/g, " ")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .split("\n")
      .map((line) => line.replace(/[ \t\f\v]+/g, " ").trim());

    const cleanedLines = [];
    let previousBlank = false;
    for (const line of lines) {
      if (line) {
        cleanedLines.push(line);
        previousBlank = false;
        continue;
      }

      if (cleanedLines.length > 0 && !previousBlank) {
        cleanedLines.push("");
        previousBlank = true;
      }
    }

    return cleanedLines.join("\n").trim();
  }

  function htmlToText(html) {
    if (!html) {
      return "";
    }

    const container = document.createElement("div");
    container.innerHTML = html;
    return normalizeBlockText(container.innerText || container.textContent || "");
  }

  function isJobPostingType(typeValue) {
    if (Array.isArray(typeValue)) {
      return typeValue.some(isJobPostingType);
    }

    return typeof typeValue === "string" && typeValue.toLowerCase() === "jobposting";
  }

  function collectJobPostingNodes(value, results) {
    if (!value) {
      return;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        collectJobPostingNodes(item, results);
      }
      return;
    }

    if (typeof value !== "object") {
      return;
    }

    if (isJobPostingType(value["@type"])) {
      results.push(value);
    }

    for (const nestedValue of Object.values(value)) {
      if (nestedValue && typeof nestedValue === "object") {
        collectJobPostingNodes(nestedValue, results);
      }
    }
  }

  function findStructuredJobPosting() {
    const scripts = document.querySelectorAll("script[type='application/ld+json']");
    const results = [];

    for (const script of scripts) {
      try {
        const parsed = JSON.parse(script.textContent || "");
        collectJobPostingNodes(parsed, results);
      } catch (error) {
        continue;
      }
    }

    return results[0] || null;
  }

  function extractOrganizationName(value) {
    if (!value) {
      return "";
    }

    if (typeof value === "string") {
      return normalizeInlineText(value);
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        const name = extractOrganizationName(item);
        if (name) {
          return name;
        }
      }
      return "";
    }

    return normalizeInlineText(value.name || value.legalName || "");
  }

  function firstTextFromSelectors(selectors, maxLength) {
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const element of elements) {
        const text = normalizeInlineText(element.innerText || element.textContent || "");
        if (!text) {
          continue;
        }

        if (!maxLength || text.length <= maxLength) {
          return text;
        }
      }
    }

    return "";
  }

  function collectDescriptionCandidates(selectors) {
    const candidates = [];
    const seen = new Set();

    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      for (const element of elements) {
        const text = normalizeBlockText(element.innerText || element.textContent || "");
        if (!text || text.length < 200) {
          continue;
        }

        const fingerprint = text.slice(0, 400);
        if (seen.has(fingerprint)) {
          continue;
        }

        seen.add(fingerprint);
        candidates.push({ label: selector, text });
      }
    }

    return candidates;
  }

  function scoreDescription(candidate) {
    const text = candidate.text || "";
    let score = text.length;

    if (/jobDescriptionText|job-description|jobDescription/i.test(candidate.label)) {
      score += 4000;
    } else if (/description/i.test(candidate.label)) {
      score += 2000;
    } else if (/article|main/i.test(candidate.label)) {
      score += 500;
    }

    if (text.length < 250) {
      score -= 3000;
    }

    if (/responsibilities|qualifications|requirements|about the role|what you'll do/i.test(text)) {
      score += 500;
    }

    return score;
  }

  function pickBestDescription(candidates) {
    let bestText = "";
    let bestScore = Number.NEGATIVE_INFINITY;

    for (const candidate of candidates) {
      const score = scoreDescription(candidate);
      if (score > bestScore) {
        bestScore = score;
        bestText = candidate.text;
      }
    }

    return bestText;
  }

  function splitTitleParts(title, source) {
    const normalizedTitle = title.replace(/\u2014|\u2013/g, " - ");
    const separators = [" | ", " - ", " @ ", ":"];
    let parts = [normalizedTitle];

    for (const separator of separators) {
      if (normalizedTitle.includes(separator)) {
        parts = normalizedTitle.split(separator);
        break;
      }
    }

    const sourcePattern = source
      ? new RegExp(source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i")
      : null;
    const filtered = parts
      .map((part) => normalizeInlineText(part))
      .filter(Boolean)
      .filter((part) => !sourcePattern || !sourcePattern.test(part))
      .filter((part) => !/jobs?|careers?|linkedin|indeed|greenhouse|lever/i.test(part));

    return {
      roleGuess: filtered[0] || "",
      companyGuess: filtered[1] || ""
    };
  }

  function pickFirstMeaningful(candidates, validator) {
    for (const candidate of candidates) {
      const cleaned = normalizeInlineText(candidate);
      if (cleaned && (!validator || validator(cleaned))) {
        return cleaned;
      }
    }

    return "";
  }

  function isLikelyRoleTitle(value) {
    return value.length >= 3 && value.length <= 160 && !/apply now|sign in|log in/i.test(value);
  }

  function isLikelyCompany(value) {
    return value.length >= 2 && value.length <= 160 && !/jobs?|careers?|linkedin|indeed|greenhouse|lever/i.test(value);
  }

  const source = window.location.hostname.replace(/^www\./i, "");
  const pageUrl = window.location.href;
  const pageTitle = normalizeInlineText(document.title);
  const rawVisibleText = normalizeBlockText(document.body ? document.body.innerText : "");
  const structuredJobPosting = findStructuredJobPosting();
  const titleParts = splitTitleParts(pageTitle, source);
  const metaTitle = normalizeInlineText(
    document.querySelector("meta[property='og:title']")?.content ||
      document.querySelector("meta[name='twitter:title']")?.content ||
      ""
  );

  const roleTitle = pickFirstMeaningful(
    [
      structuredJobPosting?.title,
      firstTextFromSelectors(TITLE_SELECTORS, 160),
      metaTitle,
      titleParts.roleGuess,
      pageTitle
    ],
    isLikelyRoleTitle
  );

  const company = pickFirstMeaningful(
    [
      extractOrganizationName(structuredJobPosting?.hiringOrganization),
      firstTextFromSelectors(COMPANY_SELECTORS, 160),
      titleParts.companyGuess
    ],
    isLikelyCompany
  );

  const descriptionCandidates = [
    { label: "jsonld", text: htmlToText(structuredJobPosting?.description || "") },
    ...collectDescriptionCandidates(DESCRIPTION_SELECTORS),
    { label: "body", text: rawVisibleText }
  ].filter((candidate) => candidate.text);

  const jobDescriptionText = pickBestDescription(descriptionCandidates) || rawVisibleText;

  return {
    page_url: pageUrl,
    page_title: pageTitle,
    source,
    role_title: roleTitle,
    company,
    job_description_text: jobDescriptionText,
    raw_visible_text: rawVisibleText
  };
}
