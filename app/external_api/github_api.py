import requests
import re

from typing import List
from fastapi import HTTPException

from app.schemas import RepositoryFile, RepositoryInfo, RepositoryInfoWithFiles
from app.external_api.gh_const import GITHUB_LINK_REGEX, ALLOWED_EXTENSIONS

from app.config import settings


class GitHubLinkException(Exception):
    def __init__(self, status_code: int, detail: str):
        """
        Custom exception for HTTP errors.

        Args:
            status_code (int): The HTTP status code for the error.
            detail (str): The error message to display.
        """
        self.status_code = status_code
        self.detail = detail

    def raise_http_exception(self) -> HTTPException:
        """Raise an HTTPException with the stored details."""
        raise HTTPException(status_code=self.status_code, detail=self.detail)


def get_file_extension(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def split_github_url(github_url: str) -> tuple[str,str,str]:
    """
    splitting provided github link and return (owner, repo, path)
    
    """
    match = re.match(GITHUB_LINK_REGEX, github_url)

    if match:
        owner = match.group(1)
        repo = match.group(2)
        path = match.group(3) if match.group(3) else ""
        return owner, repo, path
    else:
        raise GitHubLinkException(
            status_code=400,
            detail="GitHub link is not valid. Please provide valid link to GitHub (https://github.com/owner/repository) ",
        ).raise_http_exception()


def get_file_object_with_content(file_name:str, file_url:str, sha:str, gh_token:str) -> RepositoryFile:

    headers =  {"Authorization": f"Bearer {gh_token}"}
    try:
        result = requests.get(url=file_url, headers=headers)
        content = result.json()["content"]
    except:
        content = "Error when trying to get content from file"
    return RepositoryFile(file_name=file_name, file_url=file_url, sha=sha, content=content)

def get_repository_files_with_content(owner: str, repo_name: str, path: str, gh_token: str) -> List[RepositoryFile]:
    headers = {"Authorization": f"Bearer {gh_token}"}
    stack = [path]
    files: List[RepositoryFile] = []

    while stack:
        current_path = stack.pop()
        url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{current_path}"
        response = requests.get(url=url, headers=headers)
        items = response.json()
        for item in items:
            
            if item["type"] == "file" and get_file_extension(item["name"]):

                file_name= current_path + item["name"]
                file_url=item["url"]
                sha=item["sha"]

                retrieved_file = get_file_object_with_content(file_name, file_url, sha, gh_token)

                files.append(
                    retrieved_file
                )
            elif isinstance(item, dict) and item["type"] == "dir":
                stack.append(f"{current_path}/{item['name']}".lstrip("/"))

    return files

def get_repository_hash(owner:str, repo_name: str, gh_token: str) -> str:
    headers = {"Authorization": f"Bearer {gh_token}"}

    url = f"https://api.github.com/repos/{owner}/{repo_name}/branches"
    response = requests.get(url=url, headers=headers)
    info = response.json()[0]
    return info['commit']['sha']

def get_repository_version_with_files(git_hub_url: str, gh_token: str) -> RepositoryInfoWithFiles:
    owner, repository_name, path = split_github_url(git_hub_url)
    files = get_repository_files_with_content(owner, repository_name, path, gh_token)
    repository_hash = get_repository_hash(owner, repository_name, gh_token)

    return RepositoryInfoWithFiles(repository_hash=repository_hash, repository_files=files)
