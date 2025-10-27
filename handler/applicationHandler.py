import asyncio
import os
from typing import Tuple
from fastapi import Request
import requests
from dotenv import load_dotenv
from models.ResumeModel import  Resume

load_dotenv()

def createApplication(
    resume: dict,   
    resumeName: str,
    coverLetter: str,
    jobDescription: str,
    oldMetric: int,
    newMetric: int,
    request: Request
) -> str | None:

    # Check for authenticated user in request state
    if not hasattr(request.state, "user") or not request.state.user:
        return None

    mutation = """
    mutation CreateApplication($input: CreateApplicationInput!) {
      createApplication(input: $input) {
        id
      }
    }
    """

    input_data = {
        "jobDescription": jobDescription,
        "resumeName": resumeName,
        "resume": resume,
        "oldMetric": oldMetric,
        "newMetric": newMetric,
        "coverLetter": coverLetter,
        "status": "Applied",
    }

    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": auth_header,
    }

    url = os.environ.get("APPSYNC_URL")
    if not url:
        raise Exception("APPSYNC_URL not found in environment variables")

    try:
        response = requests.post(
            url,
            json={"query": mutation, "variables": {"input": input_data}},
            headers=headers,
            timeout=10,  # add timeout to prevent hanging
        )
        response.raise_for_status()
    except requests.RequestException as e:
        # Log or raise more descriptive error for upstream handling
        print(f"Failed to call AppSync: {str(e)}")
        raise Exception(f"Failed to call AppSync: {str(e)}")

    result = response.json()

    if "errors" in result:
        print(f"GraphQL error: {result['errors']}")
        raise Exception(f"GraphQL error: {result['errors']}")

    return result["data"]["createApplication"]["id"]


