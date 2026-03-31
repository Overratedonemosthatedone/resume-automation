const PROCESS_BATCH_ENDPOINT = "http://127.0.0.1:8765/process-batch";
const QUEUE_STATUS_ENDPOINT = "http://127.0.0.1:8765/queue-status";

const captureButton = document.getElementById("captureButton");
const processButton = document.getElementById("processButton");
const pendingCount = document.getElementById("pendingCount");
const statusMessage = document.getElementById("statusMessage");

document.addEventListener("DOMContentLoaded", async () => {
  captureButton.addEventListener("click", handleCaptureClick);
  processButton.addEventListener("click", handleProcessClick);
  await loadQueueStatus();
});

async function handleCaptureClick() {
  setBusy(true);
  setStatus("Capturing the current job posting...");

  try {
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.runtime.sendMessage({
      type: "capture-tab",
      tabId: activeTab?.id,
      tabUrl: activeTab?.url
    });

    if (!response?.ok) {
      throw new Error(response?.error || "Capture failed.");
    }

    setStatus(response.result?.message || "Saved to the local Resume Tailor queue.");
    await loadQueueStatus();
  } catch (error) {
    const message = error && error.message ? error.message : "Capture failed.";
    setStatus(message, true);
  } finally {
    setBusy(false);
  }
}

async function handleProcessClick() {
  setBusy(true);
  setStatus("Triggering queue processing...");

  try {
    const response = await fetch(PROCESS_BATCH_ENDPOINT, {
      method: "POST"
    });
    const parsedResponse = await parseResponse(response);

    if (!response.ok) {
      const detail = parsedResponse?.detail || `HTTP ${response.status}`;
      throw new Error(detail);
    }

    setStatus(parsedResponse?.message || "Queue processing triggered.");
    await loadQueueStatus();
  } catch (error) {
    const message = error && error.message ? error.message : "Processing failed.";
    setStatus(message, true);
  } finally {
    setBusy(false);
  }
}

async function loadQueueStatus() {
  try {
    const response = await fetch(QUEUE_STATUS_ENDPOINT);
    const parsedResponse = await parseResponse(response);

    if (!response.ok) {
      const detail = parsedResponse?.detail || `HTTP ${response.status}`;
      throw new Error(detail);
    }

    pendingCount.textContent = String(parsedResponse?.pending ?? 0);
  } catch (error) {
    pendingCount.textContent = "--";
    if (!statusMessage.textContent || statusMessage.textContent === "Ready.") {
      const message = error && error.message ? error.message : "Queue status unavailable.";
      setStatus(`Queue status unavailable: ${message}`, true);
    }
  }
}

async function parseResponse(response) {
  const rawResponseText = await response.text();

  if (!rawResponseText) {
    return null;
  }

  try {
    return JSON.parse(rawResponseText);
  } catch (error) {
    return { detail: rawResponseText };
  }
}

function setBusy(isBusy) {
  captureButton.disabled = isBusy;
  processButton.disabled = isBusy;
}

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}
