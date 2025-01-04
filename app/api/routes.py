from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas import ReviewRequest, ReviewResponse

from app.helpers.file_and_openai import get_general_review_for_files

router = APIRouter()

@router.post("/review", response_model=ReviewResponse)
async def review_task(task_review: ReviewRequest, request: Request):
    redis_client = request.app.state.redis_client

    result = await get_general_review_for_files(task_review, redis_client)

    return JSONResponse(content = result.model_dump(), status_code=200)

