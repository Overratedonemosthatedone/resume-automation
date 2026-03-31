"""
Background queue worker that turns staged intake JSON into tailored resumes.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from loguru import logger

import config
from document_generators import DocxGenerator, FileManager, PdfGenerator
from tailor_client_haiku_optimized import ResumeTC as CachedResumeTailor


def utc_now_iso() -> str:
    """Return a UTC ISO timestamp for queue lifecycle fields."""
    return datetime.now(timezone.utc).isoformat()


def clean_single_line(value: str | None) -> str:
    """Normalize single-line strings into a compact representation."""
    if value is None:
        return ""
    return " ".join(str(value).replace("\u00a0", " ").split()).strip()


def clean_block_text(value: str | None) -> str:
    """Normalize multi-line text while preserving simple paragraph breaks."""
    if value is None:
        return ""

    lines = (
        str(value)
        .replace("\u00a0", " ")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )

    cleaned_lines: list[str] = []
    previous_blank = False
    for raw_line in lines:
        line = " ".join(raw_line.split()).strip()
        if line:
            cleaned_lines.append(line)
            previous_blank = False
            continue

        if cleaned_lines and not previous_blank:
            cleaned_lines.append("")
            previous_blank = True

    return "\n".join(cleaned_lines).strip()


class JobQueueProcessor:
    """Process staged intake files one batch at a time when explicitly triggered."""

    def __init__(
        self,
        pending_dir: Path | None = None,
        processed_dir: Path | None = None,
        failed_dir: Path | None = None,
        base_resume_path: Path | None = None,
        poll_interval: float | None = None,
        tailor_client_factory: Callable[..., CachedResumeTailor] | None = None,
    ) -> None:
        self.pending_dir = Path(pending_dir or config.JOB_QUEUE_PENDING_PATH)
        self.processed_dir = Path(processed_dir or config.JOB_QUEUE_PROCESSED_PATH)
        self.failed_dir = Path(failed_dir or config.JOB_QUEUE_FAILED_PATH)
        self.base_resume_path = Path(base_resume_path or config.BASE_RESUME_PATH)
        self.poll_interval = poll_interval or config.JOB_QUEUE_POLL_SECONDS
        self.tailor_client_factory = tailor_client_factory or CachedResumeTailor

        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        self._file_manager = FileManager(config.RESUME_OUTPUT_PATH)
        self._tailor_client = None
        self._base_resume_cache: str | None = None
        self._thread: threading.Thread | None = None
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._active_paths: set[str] = set()
        self._state_lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Return whether the worker thread is currently alive."""
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        """Start the background worker if it is not already running."""
        if self.is_running:
            return

        self._stop_event.clear()
        self._wake_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="resume-job-queue-worker",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Job queue worker started. Waiting for manual batch triggers for {}",
            self.pending_dir,
        )

    def stop(self, timeout: float = 5.0) -> None:
        """Request a graceful stop for the background worker."""
        if not self._thread:
            return

        self._stop_event.set()
        self._wake_event.set()
        self._thread.join(timeout=timeout)
        if self._thread.is_alive():
            logger.warning("Job queue worker did not stop within {} seconds.", timeout)
        else:
            logger.info("Job queue worker stopped.")

    def notify(self) -> None:
        """Ask the worker to drain the current pending queue once."""
        self._wake_event.set()

    def describe_runtime_state(self) -> dict[str, object]:
        """Expose worker status for health checks and debugging."""
        with self._state_lock:
            active_jobs = len(self._active_paths)

        return {
            "worker_running": self.is_running,
            "pending_dir": str(self.pending_dir),
            "processed_dir": str(self.processed_dir),
            "failed_dir": str(self.failed_dir),
            "active_jobs": active_jobs,
        }

    def _run_loop(self) -> None:
        """Wait for explicit batch requests and then drain the pending queue."""
        while not self._stop_event.is_set():
            self._wake_event.wait()
            self._wake_event.clear()
            if self._stop_event.is_set():
                break

            processed_any = self._drain_pending_queue()
            if processed_any:
                logger.info("Manual batch processing finished.")

    def _drain_pending_queue(self) -> bool:
        """Scan the pending directory and process any available intake files."""
        processed_any = False

        for path in sorted(self.pending_dir.glob("*.json")):
            if not self._claim_path(path):
                continue

            processed_any = True
            try:
                self.process_file(path)
            finally:
                self._release_path(path)

        return processed_any

    def _claim_path(self, path: Path) -> bool:
        """Mark a path as active so the worker will not process it twice."""
        resolved = str(path.resolve())
        with self._state_lock:
            if resolved in self._active_paths:
                return False
            self._active_paths.add(resolved)
        return True

    def _release_path(self, path: Path) -> None:
        """Clear the active marker once processing has finished."""
        resolved = str(path.resolve())
        with self._state_lock:
            self._active_paths.discard(resolved)

    def process_file(self, path: Path) -> dict[str, object]:
        """Process a single staged intake JSON file end to end."""
        path = Path(path)
        logger.info("Tailoring started for intake file: {}", path)

        record: dict[str, object] | None = None
        artifacts: dict[str, str] = {}

        try:
            record = self._load_record(path)
            current_status = clean_single_line(record.get("status"))

            if current_status == "complete":
                final_path = self._move_to_directory(path, self.processed_dir)
                logger.warning(
                    "Found a completed intake file in pending; moved it to processed: {}",
                    final_path,
                )
                return {"status": "already_complete", "final_path": str(final_path)}

            if current_status == "failed":
                final_path = self._move_to_directory(path, self.failed_dir)
                logger.warning(
                    "Found a failed intake file in pending; moved it to failed: {}",
                    final_path,
                )
                return {"status": "already_failed", "final_path": str(final_path)}

            record = self._prepare_record(record)
            record["status"] = "processing"
            record["processing_started_at"] = utc_now_iso()
            record["error_message"] = None
            self._write_record(path, record)

            tailoring_request = self._build_tailoring_request(record)
            logger.info(
                "Running tailoring engine for '{}' at '{}'",
                tailoring_request["role_title"],
                tailoring_request["company"],
            )

            tailored_text = self._get_tailor_client().tailor(
                job_title=tailoring_request["role_title"],
                job_description=tailoring_request["job_description_text"],
                job_requirements=tailoring_request["job_requirements_text"],
            )

            docx_generator = DocxGenerator()
            docx_generator.parse_and_add_resume(tailored_text)
            pdf_generator = PdfGenerator()
            created_at = self._get_output_date(record)

            docx_path = self._file_manager.save_docx_resume(
                docx_generator=docx_generator,
                company=tailoring_request["company"],
                job_title=tailoring_request["role_title"],
                source=tailoring_request["source"],
                source_url=tailoring_request["page_url"],
                created_at=created_at,
            )
            artifacts["docx"] = str(docx_path.resolve())

            pdf_path = self._file_manager.save_pdf_resume(
                pdf_generator=pdf_generator,
                resume_text=tailored_text,
                company=tailoring_request["company"],
                job_title=tailoring_request["role_title"],
                source=tailoring_request["source"],
                source_url=tailoring_request["page_url"],
                created_at=created_at,
            )
            artifacts["pdf"] = str(pdf_path.resolve())

            metadata_path = pdf_path.with_suffix(".json")
            if metadata_path.exists():
                artifacts["metadata"] = str(metadata_path.resolve())

            record["status"] = "complete"
            record["processed_at"] = utc_now_iso()
            record["error_message"] = None
            record["output_artifacts"] = artifacts
            record["tailoring_engine"] = "tailor_client_haiku_optimized.ResumeTC.tailor"
            self._write_record(path, record)

            final_path = self._move_to_directory(path, self.processed_dir)
            logger.info("Tailoring succeeded for intake file: {}", final_path.name)
            logger.info("Generated resume artifacts: {}", artifacts)
            logger.info("Moved intake JSON to processed: {}", final_path)
            return {
                "status": "complete",
                "final_path": str(final_path),
                "output_artifacts": artifacts,
            }

        except Exception as exc:
            if isinstance(exc, (ValueError, FileNotFoundError, RuntimeError)):
                logger.error("Tailoring failed for intake file {}: {}", path, exc)
            else:
                logger.exception("Tailoring failed for intake file {}: {}", path, exc)
            final_path = self._handle_failure(path, record, str(exc), artifacts)
            return {
                "status": "failed",
                "final_path": str(final_path),
                "output_artifacts": artifacts,
                "error_message": str(exc),
            }

    def _load_record(self, path: Path) -> dict[str, object]:
        """Load an intake record from disk."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed intake JSON: {exc}") from exc

    def _write_record(self, path: Path, record: dict[str, object]) -> None:
        """Persist an updated intake record back to disk."""
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _prepare_record(self, record: dict[str, object]) -> dict[str, object]:
        """Normalize the stored intake fields before validation."""
        page_url = clean_single_line(record.get("page_url"))
        page_title = clean_single_line(record.get("page_title"))
        source = clean_single_line(record.get("source")) or self._derive_source_from_url(page_url)
        company = clean_single_line(record.get("company")) or source or "Unknown"
        role_title = clean_single_line(record.get("role_title")) or page_title or "Unknown Role"
        job_description_text = clean_block_text(record.get("job_description_text"))
        raw_visible_text = clean_block_text(record.get("raw_visible_text"))

        normalized = dict(record)
        normalized["page_url"] = page_url
        normalized["page_title"] = page_title
        normalized["source"] = source
        normalized["company"] = company
        normalized["role_title"] = role_title
        normalized["job_description_text"] = job_description_text or raw_visible_text
        normalized["raw_visible_text"] = raw_visible_text or job_description_text
        normalized["status"] = clean_single_line(record.get("status")) or "pending"
        return normalized

    def _build_tailoring_request(self, record: dict[str, object]) -> dict[str, str]:
        """Validate a normalized record and map it into the tailor client inputs."""
        job_description_text = clean_block_text(record.get("job_description_text"))
        raw_visible_text = clean_block_text(record.get("raw_visible_text"))
        page_url = clean_single_line(record.get("page_url"))
        page_title = clean_single_line(record.get("page_title"))
        company = clean_single_line(record.get("company")) or "Unknown"
        role_title = clean_single_line(record.get("role_title")) or page_title or "Unknown Role"
        source = clean_single_line(record.get("source")) or self._derive_source_from_url(page_url) or "Unknown"

        if not page_url:
            raise ValueError("Missing page_url in intake JSON.")

        if not page_title:
            raise ValueError("Missing page_title in intake JSON.")

        if not job_description_text:
            raise ValueError("Missing job_description_text and raw_visible_text in intake JSON.")

        if len(job_description_text) < config.MIN_DESCRIPTION_LENGTH and len(raw_visible_text) < config.MIN_DESCRIPTION_LENGTH:
            raise ValueError(
                "Captured job text is too short to tailor reliably. "
                f"Need at least {config.MIN_DESCRIPTION_LENGTH} characters of description text."
            )

        job_requirements_text = self._derive_job_requirements(job_description_text, raw_visible_text)
        if len(job_requirements_text) < config.MIN_REQUIREMENTS_LENGTH:
            job_requirements_text = job_description_text

        return {
            "page_url": page_url,
            "page_title": page_title,
            "company": company,
            "role_title": role_title,
            "source": source,
            "job_description_text": job_description_text,
            "job_requirements_text": job_requirements_text,
        }

    def _derive_job_requirements(self, job_description_text: str, raw_visible_text: str) -> str:
        """Extract a best-effort requirements section for the existing tailor interface."""
        source_text = job_description_text or raw_visible_text
        lowered = source_text.lower()
        headings = (
            "requirements",
            "qualifications",
            "basic qualifications",
            "preferred qualifications",
            "what you bring",
            "what we're looking for",
            "experience you'll bring",
            "you have",
            "must have",
            "skills and experience",
        )
        stop_markers = (
            "benefits",
            "about us",
            "about the company",
            "compensation",
            "salary",
            "equal opportunity",
            "eeo statement",
            "why join",
            "responsibilities",
            "what you'll do",
        )

        start_index = -1
        for heading in headings:
            candidate = lowered.find(heading)
            if candidate != -1 and (start_index == -1 or candidate < start_index):
                start_index = candidate

        if start_index == -1:
            return source_text

        end_index = len(source_text)
        tail_text = lowered[start_index + 1 :]
        for marker in stop_markers:
            candidate = tail_text.find(marker)
            if candidate == -1:
                continue
            absolute_index = start_index + 1 + candidate
            if absolute_index > start_index:
                end_index = min(end_index, absolute_index)

        requirements = source_text[start_index:end_index].strip()
        return requirements or source_text

    def _get_output_date(self, record: dict[str, object]) -> str | None:
        """Return the YYYY-MM-DD date used by the existing FileManager naming logic."""
        captured_at = clean_single_line(record.get("captured_at"))
        if not captured_at:
            return None

        try:
            parsed = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            if "T" in captured_at:
                return captured_at.split("T", 1)[0]
            return captured_at or None

    def _get_tailor_client(self):
        """Reuse one ResumeTC client so prompt caching stays warm across jobs."""
        if self._tailor_client is None:
            self._tailor_client = self.tailor_client_factory(
                base_resume_text=self._load_base_resume_text(),
            )
        return self._tailor_client

    def _load_base_resume_text(self) -> str:
        """Load the source resume used by the existing tailoring engine."""
        if self._base_resume_cache is None:
            if not self.base_resume_path.exists():
                raise FileNotFoundError(
                    f"Base resume file not found: {self.base_resume_path}"
                )

            self._base_resume_cache = self.base_resume_path.read_text(encoding="utf-8").strip()
            if not self._base_resume_cache:
                raise ValueError(
                    f"Base resume file is empty: {self.base_resume_path}"
                )

        return self._base_resume_cache

    def _handle_failure(
        self,
        path: Path,
        record: dict[str, object] | None,
        error_message: str,
        artifacts: dict[str, str],
    ) -> Path:
        """Persist failure details and move the intake JSON into the failed folder."""
        if record is not None:
            record["status"] = "failed"
            record["failed_at"] = utc_now_iso()
            record["error_message"] = error_message
            if artifacts:
                record["output_artifacts"] = artifacts

            try:
                self._write_record(path, record)
            except Exception as write_error:
                logger.error(
                    "Failed to write failure details back to {}: {}",
                    path,
                    write_error,
                )

        final_path = self._move_to_directory(path, self.failed_dir)
        logger.info("Moved intake JSON to failed: {}", final_path)
        return final_path

    def _move_to_directory(self, path: Path, target_dir: Path) -> Path:
        """Move a queue file into its final lifecycle directory without overwriting."""
        path = Path(path)
        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / path.name
        suffix = 1

        while destination.exists():
            destination = target_dir / f"{path.stem}__{suffix}{path.suffix}"
            suffix += 1

        return path.replace(destination)

    @staticmethod
    def _derive_source_from_url(page_url: str) -> str:
        """Derive a source hostname when the intake payload omitted one."""
        hostname = (urlparse(page_url).hostname or "").lower()
        return hostname.removeprefix("www.")
