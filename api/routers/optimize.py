from fastapi import APIRouter, BackgroundTasks, HTTPException
from api.models import OptimizeRequest, SubmitResponse, JobStatusResponse
import api.job_store as job_store
from api.optimizer import run_optimization

router = APIRouter(prefix="/api", tags=["optimize"])


@router.post("/optimize", response_model=SubmitResponse)
async def submit_optimization(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
):
    job = job_store.create_job()
    background_tasks.add_task(run_optimization, job.job_id, request)
    return SubmitResponse(job_id=job.job_id)


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        result=job.result,
        error=job.error,
    )


@router.delete("/job/{job_id}", status_code=204)
async def cancel_job(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job_store.set_cancelled(job.job_id)
