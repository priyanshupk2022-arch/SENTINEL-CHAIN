import pytest
import asyncio
from backend.app.engine.cli_runner import BrightDataCliRunner, CliExecutionResult
from backend.app.engine.queue_manager import ScraperQueueManager, QueueJob, QueueJobType, JobStatus

@pytest.mark.asyncio
async def test_cli_runner_argument_safety():
    runner = BrightDataCliRunner()
    args = runner.build_heal_command(
        collector_id="c_test123",
        target_url="http://127.0.0.1:8000/api/proxy/target",
        repair_prompt="Fix selector --force-flag-injection"
    )
    assert any("npx" in arg for arg in args)
    assert "scraper" in args
    assert "heal" in args
    assert "c_test123" in args
    assert "--" in args
    delimiter_idx = args.index("--")
    assert args[delimiter_idx + 1] == "Fix selector --force-flag-injection"

@pytest.mark.asyncio
async def test_queue_manager_singleton_processing():
    queue_mgr = ScraperQueueManager()
    await queue_mgr.start()

    results = []

    async def mock_task(job: QueueJob):
        await asyncio.sleep(0.02)
        results.append(job.job_id)
        return {"status": "success", "job_id": job.job_id}

    queue_mgr.register_handler(QueueJobType.LOGIN, mock_task)

    job1 = await queue_mgr.enqueue_job(QueueJobType.LOGIN, {"collector_id": "c_1", "url": "http://example.com/1"})
    job2 = await queue_mgr.enqueue_job(QueueJobType.LOGIN, {"collector_id": "c_2", "url": "http://example.com/2"})

    assert job1.status in [JobStatus.QUEUED, JobStatus.PROCESSING]
    assert job2.status in [JobStatus.QUEUED, JobStatus.PROCESSING]

    res1 = await queue_mgr.wait_for_job(job1.job_id, timeout=2.0)
    res2 = await queue_mgr.wait_for_job(job2.job_id, timeout=2.0)

    assert res1.status == JobStatus.COMPLETED
    assert res2.status == JobStatus.COMPLETED
    assert results == [job1.job_id, job2.job_id]

    await queue_mgr.stop()
