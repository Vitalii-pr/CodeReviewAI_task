from app.schemas import RepositoryFile, ReviewRequest, ReviewResponse, RepositoryInfo
from app.external_api.github_api import get_repository_version_with_files
from app.external_api.openAI_api import write_review, write_general_review
from app.redis_client import Redis_client
import json
from app.config import settings

from typing import List

GITHUB_ACCESS_TOKEN = settings.GITHUB_ACCESS_TOKEN


async def get_review_on_all_files_and_store_to_redis(task_requirements: str, files: List[RepositoryFile], redis_client: Redis_client) -> List[str]:

    redis_keys = []

    for file in files:
        redis_key = redis_client.generate_file_key(file.file_name, file.sha)
        if not await redis_client.exists(redis_key):
            await write_review(file, task_requirements, redis_key, redis_client)
        redis_keys.append(redis_key)
    
    return redis_keys



async def get_review_from_redis(redis_keys: List[str], redis_client: Redis_client) -> str:
    all_results = ''
    for key in redis_keys:
        all_results += await redis_client.get_file_review_from_redis(key) or ""
        all_results += '--'
    return all_results


async def get_general_review_for_files(review_request: ReviewRequest, redis_client: Redis_client) -> ReviewResponse:
    print(GITHUB_ACCESS_TOKEN)

    repository_info = get_repository_version_with_files(str(review_request.git_hub_url), GITHUB_ACCESS_TOKEN)

    repository_redis_key = redis_client.generate_repo_key(repository_info.repository_hash)

    if await redis_client.exists(repository_redis_key):
        repo_review = await redis_client.redis_client.get(repository_redis_key)
        repo_review = ReviewResponse.model_validate(json.loads(repo_review))
        return repo_review
    
    redis_keys = await get_review_on_all_files_and_store_to_redis(review_request.task_requirements, repository_info.repository_files, redis_client)
    reviews = await get_review_from_redis(redis_keys, redis_client)
    general_review = write_general_review(reviews)

    file_names = [file.file_name for file in repository_info.repository_files]

    review_response =  ReviewResponse(message=general_review['message'], level = review_request.developer_level, grade=int(general_review['grade']), repository=RepositoryInfo(repository_hash=repository_info.repository_hash), file_names=file_names)

    await redis_client.redis_client.set(repository_redis_key, review_response.model_dump_json())

    return review_response
    




    
    
        

    


    
    

