# CodeReviewAI

CodeReviewAI is a Python-based backend service built with FastAPI that automates the process of reviewing coding assignments. It integrates OpenAI's GPT API for code analysis and the GitHub API for repository access, providing a streamlined way to review small repositories. The service leverages Redis for caching and is designed to be easily deployable using Docker.

## Features
- Analyze code from GitHub repositories using OpenAI's GPT API.
- Caching mechanism for efficiency using Redis.
- Single POST endpoint for submitting code review requests.
- Easy setup with Docker Compose and Poetry.

## Minimum Requirements
- Python 3.9+
- GitHub access token for repository access.
- OpenAI API key for code analysis.
- Redis for caching responses.
---

## Steps to Run the Project

1. **Replace in `.env` File**

   Paste the following environment variables into a `.env` file:
   ```.env
   GITHUB_ACCESS_TOKEN=your_github_key
   OPENAI_API=your_openai_key
   
2. **Build and Start the Project**  
Run the following commands:  
```bash
docker-compose build
docker-compose up
```

3. Try with Postman
``` 
POST http://localhost:8000/review/

{
    "task_requirements": "Read readme file and make all instructions",
    "git_hub_url": "https://github.com/sarcasticadmin/empty-repo",
    "developer_level": "junior"
}
```


## Second task
To handle high traffic (e.g., 100+ new review requests per minute) and large repositories (100+ files), the following approaches can be adopted:

1. **Queue-Based Task Processing**:  
   Instead of reviewing files directly on API requests, tasks can be added to a queue (e.g., RabbitMQ, SQS, or Celery) for processing. Workers can then process these tasks asynchronously. This setup allows for horizontal scaling by adding more workers to increase throughput.

2. **OpenAI and GitHub multiple accounts**
   For high traffic and high costs of this API we can use different accounts for reducing cost of this services and avoid rate limits to provide good system reliability.

3. **Large Repos**
   Just check files with code and configuration. Avoid different files with content or some not neccesary information. Also can make filtration of this files using OpenAI API depending on file_names
