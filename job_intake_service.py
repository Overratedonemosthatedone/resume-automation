"""
Local FastAPI intake service for browser-captured job postings.
"""
from __future__ import annotations

import json
import re
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from loguru import logger

import config
from job_queue_processor import JobQueueProcessor

QUEUE_DIR = Path(config.JOB_QUEUE_PENDING_PATH)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)
queue_processor = JobQueueProcessor()


def log_runtime_configuration() -> None:
    """Log a small masked fingerprint for key runtime settings."""
    logger.info(
        "Configured Anthropic API key fingerprint: {}",
        config.mask_secret(config.ANTHROPIC_API_KEY),
    )


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    """Expose the API lifecycle while leaving queue processing as a manual action."""
    log_runtime_configuration()
    try:
        yield
    finally:
        queue_processor.stop()

app = FastAPI(
    title="Resume Tailor Intake Service",
    version="0.1.0",
    description="Receives browser captures and stages one normalized JSON file per job.",
    lifespan=app_lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IntakePayload(BaseModel):
    """Raw browser payload received from the local Chrome extension."""

    source: str | None = None
    page_url: str | None = None
    page_title: str | None = None
    company: str | None = None
    role_title: str | None = None
    job_description_text: str | None = None
    raw_visible_text: str | None = None

    model_config = ConfigDict(extra="allow")


class IntakeRecord(BaseModel):
    """Normalized job capture written to the pending queue."""

    captured_at: str
    source: str
    page_url: str
    page_title: str
    company: str
    role_title: str
    job_description_text: str
    raw_visible_text: str
    status: str = "pending"


class IntakeResponse(BaseModel):
    """Small response payload so the extension can confirm success."""

    status: str
    saved_path: str
    queue_status: str
    tailoring_started: bool
    processing_mode: str
    message: str


class QueueStatusResponse(BaseModel):
    """Return the number of staged jobs waiting in the pending queue."""

    pending: int


class ProcessBatchResponse(BaseModel):
    """Confirm that the queue worker was asked to drain the pending batch."""

    status: str
    pending: int
    worker_running: bool
    message: str


def clean_single_line(value: str | None) -> str:
    """Normalize a single-line text field into a compact string."""
    if value is None:
        return ""

    text = str(value).replace("\u00a0", " ").strip()
    return re.sub(r"\s+", " ", text)


def clean_block_text(value: str | None) -> str:
    """Normalize multi-line text while keeping paragraph breaks readable."""
    if value is None:
        return ""

    text = str(value).replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in text.split("\n")]

    cleaned_lines: list[str] = []
    previous_blank = False
    for line in lines:
        if line:
            cleaned_lines.append(line)
            previous_blank = False
            continue

        if cleaned_lines and not previous_blank:
            cleaned_lines.append("")
            previous_blank = True

    return "\n".join(cleaned_lines).strip()


def normalize_source(source: str | None, page_url: str) -> str:
    """Prefer the provided source, otherwise derive it from the hostname."""
    cleaned_source = clean_single_line(source)
    if cleaned_source:
        return cleaned_source

    parsed = urlparse(page_url)
    hostname = (parsed.hostname or "").lower()
    return hostname.removeprefix("www.")


def slugify_component(value: str, fallback: str) -> str:
    """Build a filesystem-safe filename component."""
    normalized = clean_single_line(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return (slug[:60] or fallback)


def build_output_path(record: IntakeRecord) -> Path:
    """Create a deterministic-but-unique filename inside the pending queue."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d__%H%M%S")
    company = slugify_component(record.company, "unknown-company")
    role_title = slugify_component(record.role_title, "unknown-role")
    source = slugify_component(record.source, "unknown-source")
    base_name = f"{timestamp}__{company}__{role_title}__{source}"
    output_path = QUEUE_DIR / f"{base_name}.json"

    suffix = 1
    while output_path.exists():
        output_path = QUEUE_DIR / f"{base_name}__{suffix}.json"
        suffix += 1

    return output_path


def get_pending_queue_count() -> int:
    """Count staged intake JSON files that are still waiting in pending."""
    return sum(1 for _ in QUEUE_DIR.glob("*.json"))


def normalize_payload(payload: IntakePayload) -> IntakeRecord:
    """Convert raw browser data into the stable intake structure."""
    page_url = clean_single_line(payload.page_url)
    page_title = clean_single_line(payload.page_title)
    company = clean_single_line(payload.company)
    role_title = clean_single_line(payload.role_title)
    raw_visible_text = clean_block_text(payload.raw_visible_text)
    job_description_text = clean_block_text(payload.job_description_text) or raw_visible_text

    return IntakeRecord(
        captured_at=datetime.now(timezone.utc).isoformat(),
        source=normalize_source(payload.source, page_url),
        page_url=page_url,
        page_title=page_title,
        company=company,
        role_title=role_title,
        job_description_text=job_description_text,
        raw_visible_text=raw_visible_text or job_description_text,
        status="pending",
    )


@app.get("/health")
def health_check() -> dict[str, object]:
    """Lightweight sanity check for local setup."""
    return {
        "status": "ok",
        "queue_dir": str(QUEUE_DIR),
        **queue_processor.describe_runtime_state(),
    }


@app.get("/queue-status", response_model=QueueStatusResponse)
def queue_status() -> QueueStatusResponse:
    """Expose the current pending queue depth for the local extension popup."""
    return QueueStatusResponse(pending=get_pending_queue_count())


@app.post("/process-batch", response_model=ProcessBatchResponse)
def process_batch() -> ProcessBatchResponse:
    """Wake the queue worker so it drains all currently staged pending jobs."""
    pending = get_pending_queue_count()

    if pending == 0:
        return ProcessBatchResponse(
            status="idle",
            pending=0,
            worker_running=queue_processor.is_running,
            message="No pending jobs to process.",
        )

    try:
        queue_processor.start()
        queue_processor.notify()
    except Exception as exc:
        logger.exception("Failed to trigger batch processing: {}", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger batch processing.",
        ) from exc

    logger.info(
        "Manual batch processing requested for {} pending intake file(s).",
        pending,
    )

    message = (
        f"Queue processing triggered for {pending} pending job(s)."
    )
    return ProcessBatchResponse(
        status="processing_started",
        pending=pending,
        worker_running=queue_processor.is_running,
        message=message,
    )


@app.post("/intake", response_model=IntakeResponse)
def intake_job(payload: IntakePayload) -> IntakeResponse:
    """Receive a browser capture and stage it as a pending queue item."""
    logger.info(
        "Intake received: source='{}' url='{}' title='{}'",
        clean_single_line(payload.source),
        clean_single_line(payload.page_url),
        clean_single_line(payload.page_title),
    )
    record = normalize_payload(payload)
    output_path = build_output_path(record)
    output_path.write_text(
        json.dumps(record.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info("Saved normalized intake JSON to {}", output_path)
    print(output_path, flush=True)

    return IntakeResponse(
        status="saved",
        saved_path=str(output_path),
        queue_status="pending",
        tailoring_started=False,
        processing_mode="manual_batch_trigger",
        message="Capture saved to the pending queue. Trigger a batch when you're ready to process it.",
    )


def configure_logging() -> None:
    """Configure human-readable console and file logging for local runs."""
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format=config.LOG_CONSOLE_FORMAT,
        level=config.LOG_LEVEL,
    )
    logger.add(
        str(config.LOG_PATH / "job_intake_service_{time}.log"),
        rotation=config.LOG_MAX_BYTES,
        retention=f"{config.LOG_BACKUP_COUNT} days",
        compression="zip",
        level="DEBUG",
        format=config.LOG_FILE_FORMAT,
    )


if __name__ == "__main__":
    import uvicorn

    configure_logging()
    uvicorn.run(
        app,
        host=config.JOB_INTAKE_HOST,
        port=config.JOB_INTAKE_PORT,
        reload=False,
    )
