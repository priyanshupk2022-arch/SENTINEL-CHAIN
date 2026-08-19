import asyncio
import uuid
import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field

logger = logging.getLogger("sentinel.queue_manager")

class QueueJobType(str, Enum):
    RUN_SCRAPER = "RUN_SCRAPER"
    HEAL_SCRAPER = "HEAL_SCRAPER"
    APPROVE_SCRAPER = "APPROVE_SCRAPER"
    COLLECT_EVIDENCE = "COLLECT_EVIDENCE"
    DIAGNOSE_REPAIR = "DIAGNOSE_REPAIR"
    LOGIN = "LOGIN"

JobType = QueueJobType

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    RUNNING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class QueueJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: QueueJobType
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

CLIJob = QueueJob

class ScraperQueueManager:
    _instance: Optional["ScraperQueueManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ScraperQueueManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._queue: Optional[asyncio.Queue[QueueJob]] = None
        self._jobs: Dict[str, QueueJob] = {}
        self._events: Dict[str, asyncio.Event] = {}
        self._handlers: Dict[QueueJobType, Callable[[QueueJob], Awaitable[Any]]] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._initialized = True

    def _ensure_queue(self) -> asyncio.Queue[QueueJob]:
        try:
            cur_loop = asyncio.get_running_loop()
        except RuntimeError:
            cur_loop = None

        if self._queue is None or self._loop != cur_loop:
            self._queue = asyncio.Queue()
            self._loop = cur_loop
            self._events.clear()
        return self._queue

    def register_handler(self, job_type: QueueJobType, handler: Callable[[QueueJob], Awaitable[Any]]) -> None:
        self._handlers[job_type] = handler

    async def start(self) -> None:
        self._ensure_queue()
        if self._running and self._worker_task and not self._worker_task.done():
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("ScraperQueueManager worker loop started.")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        logger.info("ScraperQueueManager stopped.")

    async def enqueue_job(self, job_type: QueueJobType, payload: Dict[str, Any]) -> QueueJob:
        q = self._ensure_queue()
        job = QueueJob(job_type=job_type, payload=payload)
        self._jobs[job.job_id] = job
        self._events[job.job_id] = asyncio.Event()
        
        # Ensure worker is running
        if not self._running or not self._worker_task or self._worker_task.done():
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())

        await q.put(job)
        logger.info(f"Enqueued job {job.job_id} of type {job.job_type}")
        return job

    async def wait_for_job(self, job_id: str, timeout: float = 180.0) -> QueueJob:
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self._jobs[job_id]
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            return job

        event = self._events.get(job_id)
        if not event:
            event = asyncio.Event()
            self._events[job_id] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.error = f"Execution timed out after {timeout}s"
            raise TimeoutError(job.error)

        return self._jobs[job_id]

    def get_job(self, job_id: str) -> Optional[QueueJob]:
        return self._jobs.get(job_id)

    async def _worker_loop(self) -> None:
        q = self._ensure_queue()
        while self._running:
            try:
                job = await q.get()
                job.status = JobStatus.PROCESSING
                job.started_at = time.time()
                logger.info(f"Processing job {job.job_id} [{job.job_type}]")

                handler = self._handlers.get(job.job_type)
                if handler:
                    try:
                        result = await handler(job)
                        job.result = result
                        job.status = JobStatus.COMPLETED
                    except Exception as e:
                        logger.error(f"Job {job.job_id} failed with exception: {e}")
                        job.error = str(e)
                        job.status = JobStatus.FAILED
                else:
                    logger.warning(f"No handler registered for {job.job_type}")
                    job.error = f"No handler registered for {job.job_type}"
                    job.status = JobStatus.FAILED

                job.completed_at = time.time()
                q.task_done()

                # Signal completion
                event = self._events.get(job.job_id)
                if event:
                    event.set()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[QUEUE_WORKER_ERROR] Unhandled exception in worker loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)

# Aliases
CLIQueueWorker = ScraperQueueManager
CLIQueue = ScraperQueueManager
