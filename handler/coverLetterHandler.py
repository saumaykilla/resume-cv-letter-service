import os
import asyncio
import time

from pydantic import BaseModel
from models.ResumeModel import Resume
from google import genai
from utils.logger import get_logger, PerformanceLogger

logger = get_logger("cover_letter_handler")


class AICoverLetter(BaseModel):
    coverLetter: str
    resumeName: str

async def generateCoverLetter(resume: Resume, jobDescription: str):
    logger.info("📄 Starting cover letter generation")
    start_time = time.time()

    def _generate_sync():
        logger.info("🤖 Starting Gemini API call for cover letter generation")
        
        try:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                logger.error("🔑 GEMINI_API_KEY not found in environment variables")
                raise ValueError("GEMINI_API_KEY not configured")
            
            client = genai.Client(api_key=api_key)
            config = {
                'response_mime_type': 'application/json',
                'response_schema': AICoverLetter
            }

            logger.info("📤 Sending request to Gemini API for cover letter")
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=f"Generate a cover letter for the job description: {jobDescription} using the resume: {resume}. Make sure to use the resume name from the resume object to personalize the cover letter. Set resumeName to the company name from the job description.",
                config=config
            )
            
            duration = time.time() - start_time
            PerformanceLogger.log_api_call(
                logger, 
                "Gemini", 
                "cover_letter_generation", 
                duration, 
                success=True
            )
            return response.parsed
            
        except Exception as e:
            duration = time.time() - start_time
            PerformanceLogger.log_api_call(
                logger, 
                "Gemini", 
                "cover_letter_generation", 
                duration, 
                success=False,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            logger.error(
                "💥 Cover letter generation failed",
                duration=f"{duration:.3f}s",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise

    try:
        result = await asyncio.to_thread(_generate_sync)
        logger.info("✅ Cover letter generation process completed successfully")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "💥 Cover letter generation process failed",
            duration=f"{duration:.3f}s",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
