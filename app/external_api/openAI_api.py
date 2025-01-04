
from openai import OpenAI, RateLimitError
from app.schemas import RepositoryFile
from app.redis_client import Redis_client
import json

import base64

import os
from app.config import settings


OPENAI_API = settings.OPENAI_API


client = OpenAI(api_key=OPENAI_API)


async def write_review(file: RepositoryFile, general_task: str, redis_key:str, redis_client: Redis_client):
    assert redis_client is not None

    review = call_to_openai_api(base64.b64decode(file.content).decode('utf-8'), general_task)
    await redis_client.write_file_review_to_redis(redis_key, review)


def write_general_review(file_reviews: str):
    prompt = """
    You are an expert code reviewer. Based on the following file reviews, please provide a **general review for the entire repository**. Your response should be a **valid JSON object** with the following format:

    {
      "message": "your review message",
      "grade": "integer between 0 and 5"
    }
    
    - The **"message"** should provide a concise summary of the strengths and weaknesses of the repository, based on the individual file reviews.
    - The **"grade"** should be an integer between 0 and 5:
      - 0: Completely inadequate.
      - 1: Poor, with major issues.
      - 2: Fair, but needs a lot of improvement.
      - 3: Decent, with room for improvement.
      - 4: Good, but with minor improvements needed.
      - 5: Excellent, no improvements needed.
    - Please **do not** return any other text or explanations. The response **must be strictly in the JSON format** shown above.
    
    Here are the reviews for individual files:
    
    {file_reviews}
    
    Please generate the general review for the repository as a JSON object.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are software engineer with 10 years of expirience",
                },
                {"role": "user", "content": prompt},
            ],
        )
        openai_review = response.choices[0].message.content

        review_json = json.loads(str(openai_review))

        if isinstance(review_json, dict) and "message" in review_json and "grade" in review_json:
            return review_json
        else:
            raise ValueError("Response format is incorrect. It must contain 'message' and 'grade'.")
    except RateLimitError:
        print("OpenAI rate limit reached.")
        return {"error": "Rate limit reached. Please try again later."}
    except json.JSONDecodeError:
        print("Error decoding the OpenAI response.")
        return {"error": "Failed to decode the OpenAI response into JSON."}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": f"An error occurred: {e}"}
    


def call_to_openai_api(file_content: str, requirements: str) -> str:
    prompt = f"""
                Analyze the following code based on the task requirements:  
                ### Task Requirements:  
                {requirements}

                ### Code File:  
                {file_content}

                Provide a short response (up to 100 words) covering:  
                1. Compliance with the task requirements.  
                2. Key issues or bugs.  
                3. Suggestions for improvement.  

                Be concise and precise.
            """
    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are software engineer with 10 years of expirience",
                },
                {"role": "user", "content": prompt},
            ],
        )
    except RateLimitError:
        print("OpenAI rate limit reached.")

    return str(completion.choices[0].message.content)
