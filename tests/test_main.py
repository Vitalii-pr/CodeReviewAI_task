# tests/test_main.py
import pytest
from app.config import Settings
from unittest.mock import patch, Mock, AsyncMock
import os
import base64
from dotenv import load_dotenv
import app.schemas as schema
import app.external_api.github_api as gh_api
import app.external_api.openAI_api as openAI_api
import app.helpers.file_and_openai as helpers


def test_settings():
    settings = Settings()
    load_dotenv('.env')
    assert settings.OPENAI_API == os.getenv('OPENAI_API')
    assert settings.GITHUB_ACCESS_TOKEN == os.getenv('GITHUB_ACCESS_TOKEN')

@pytest.fixture()
def review_request():
    task_requirements = "Read readme file and make all instructions"
    git_hub_url = 'https://github.com/sarcasticadmin/empty-repo'
    developer_level = "junior"
    schema.ReviewRequest(task_requirements, git_hub_url, developer_level)

def test_get_file_extension():
    assert gh_api.get_file_extension("file.py") is True
    assert gh_api.get_file_extension("file.txt") is False

def test_split_github_url_valid():
    github_url = "https://github.com/sarcasticadmin/empty-repo"
    owner, repo, path = gh_api.split_github_url(github_url)
    assert owner == "sarcasticadmin"
    assert repo == "empty-repo"
    assert path == ""



@patch("requests.get")
def test_get_file_object_with_content(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"content": "dummy content"}
    mock_get.return_value = mock_response
    
    file_name = "test.py"
    file_url = "https://github.com/sarcasticadmin/empty-repo"
    sha = "sha123"
    gh_token = "fake-token"
    
    file_object = gh_api.get_file_object_with_content(file_name, file_url, sha, gh_token)
    
    assert file_object.file_name == file_name
    assert file_object.content == "dummy content"



@patch("requests.get")
def test_get_repository_files_with_content(mock_get):
    # Mocking the response for the API call to list files
    mock_response = Mock()
    mock_response.json.return_value = [{"type": "file", "name": "test.py", "url": "https://api.github.com/test", "sha": "sha123"}]
    mock_get.return_value = mock_response
    
    owner = "sarcasticadmin"
    repo_name = "empty-repo"
    path = ""
    gh_token = "fake-token"
    
    files = gh_api.get_repository_files_with_content(owner, repo_name, path, gh_token)
    
    assert len(files) == 1
    assert files[0].file_name == "test.py"
    assert files[0].content == "Error when trying to get content from file" 


@patch("requests.get")
def test_get_repository_hash(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = [{"commit": {"sha": "commit_sha123"}}]
    mock_get.return_value = mock_response
    
    owner = "sarcasticadmin"
    repo_name = "empty-repo"
    gh_token = "fake-token"
    
    sha = gh_api.get_repository_hash(owner, repo_name, gh_token)
    
    assert sha == "commit_sha123"
    
@patch("app.external_api.openAI_api.client.chat.completions.create")
def test_call_to_openai_api(mock_openai):
    file_content = "def add(a, b): return a + b"
    requirements = "Check for bugs and optimize."


    mock_openai.return_value = Mock(choices=[Mock(message=Mock(content="Code looks good, no issues."))])

    result = openAI_api.call_to_openai_api(file_content, requirements)
    

    assert result == "Code looks good, no issues."

@pytest.fixture
def sample_files():
    # Mock the base64 content of files. The content here should be properly encoded.
    file1_content = base64.b64encode(b"def add(a, b): return a + b").decode('utf-8')
    file2_content = base64.b64encode(b"def subtract(a, b): return a - b").decode('utf-8')

    return [
        schema.RepositoryFile(file_name="file1.py", file_url="https://api.github.com/file1", sha="sha123", content=file1_content),
        schema.RepositoryFile(file_name="file2.py", file_url="https://api.github.com/file2", sha="sha456", content=file2_content)
    ]


@pytest.fixture
def mock_redis():
    redis_client = AsyncMock()
    redis_client.generate_file_key.return_value = "redis_key"
    redis_client.exists.return_value = False 
    redis_client.get_file_review_from_redis.return_value = "This is a code review"
    return redis_client


@patch("app.external_api.openAI_api.write_review")
async def test_get_review_on_all_files_and_store_to_redis(mock_write_review, sample_files, mock_redis):

    mock_write_review.return_value = None

    task_requirements = "Check if the code follows the task requirements."
    

    redis_keys = await helpers.get_review_on_all_files_and_store_to_redis(task_requirements, sample_files, mock_redis)


    mock_redis.generate_file_key.assert_called_with("file2.py", "sha456")
    mock_redis.exists.assert_called()


    assert len(redis_keys) == 2 


async def test_get_review_from_redis(sample_files, mock_redis):
    redis_keys = ["redis_key1", "redis_key2"]


    all_reviews = await helpers.get_review_from_redis(redis_keys, mock_redis)


    mock_redis.get_file_review_from_redis.assert_any_call("redis_key1")
    mock_redis.get_file_review_from_redis.assert_any_call("redis_key2")

    # Check that the function concatenated the reviews correctly
    assert all_reviews == "This is a code review--This is a code review--"