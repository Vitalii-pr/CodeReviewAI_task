from typing import Optional, List

from pydantic import BaseModel, HttpUrl, Field
from enum import StrEnum


class DevLevel(StrEnum):
    junior = "junior"
    middle = "middle"
    senior = "senior"


class ReviewRequest(BaseModel):
    task_requirements: str = ""
    git_hub_url: HttpUrl
    developer_level: DevLevel


class RepositoryFile(BaseModel):
    file_name: str
    file_url: str
    sha: str
    content: str = ""

class RepositoryInfo(BaseModel):
    repository_hash: str

class RepositoryInfoWithFiles(RepositoryInfo):
    repository_files: List[RepositoryFile]

class ReviewResponse(BaseModel):
    message: str
    level: DevLevel
    grade: Optional[int] = Field(None, ge=0, le=5)
    repository: RepositoryInfo
    file_names: List[str]
