import os
import asyncio
import time
from typing import List

from pydantic import BaseModel

from google import genai
from models.ResumeModel import Resume
from utils.logger import get_logger, PerformanceLogger

logger = get_logger("resume_handler")

class AIResume(BaseModel):
    resume: Resume
    oldMetric: int
    newMetric: int



async def geminiResult(resume: Resume, keywords: List[str]):
    def _generate_sync():
        logger.info("🤖 Starting Gemini API call for resume optimization")
        start_time = time.time()
        
        try:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                logger.error("🔑 GEMINI_API_KEY not found in environment variables")
                raise ValueError("GEMINI_API_KEY not configured")
            
            client = genai.Client(api_key=api_key)
            config = {
                'response_mime_type': 'application/json',
                'response_schema': AIResume
            }
            prompt = f"""
            You are an expert resume tailoring assistant. 
            Your task is to create a professional resume that aligns with the job desctiption
            The keywords are: {keywords}
            The resume is: {resume}

            **Output:**  
            
            Ensure all descriptions incorporate relevant keywords naturally while highlighting the user's actual 
            experience and qualifications that match the job requirements.

            Return the same object format as the original resume, with updated descriptions and return **only** the updated object 
            (no additional explanations). 

            Also give me the ats score based on the job description for the resume provided and the new rewritten
            resume in oldMetric and newMetric field 

            """
            
            logger.info("📤 Sending request to Gemini API", keyword_count=len(keywords))
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt],
                config=config
            )
            
            duration = time.time() - start_time
            PerformanceLogger.log_api_call(
                logger, 
                "Gemini", 
                "resume_optimization", 
                duration, 
                success=True,
                keyword_count=len(keywords)
            )
            return response.parsed
            
        except Exception as e:
            duration = time.time() - start_time
            PerformanceLogger.log_api_call(
                logger, 
                "Gemini", 
                "resume_optimization", 
                duration, 
                success=False,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            logger.error(
                "💥 Gemini API call failed",
                duration=f"{duration:.3f}s",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise

    return await asyncio.to_thread(_generate_sync)

async def generateResume(resume: Resume, keywords: List[str]):
    logger.info("📝 Starting resume optimization process", keyword_count=len(keywords))
    start_time = time.time()
    
    try:
        # Async call to geminiResult
        result = await geminiResult(resume, keywords)
        response = result.model_dump()
        
        logger.info("⚙️ Processing Gemini response")
        
        optimized_role_details = resume.roleDetails.model_copy(update={
            "summary": response['resume']['roleDetails']['summary']
        })

        optimizedResume: Resume = Resume(
            personalDetails=resume.personalDetails,
            roleDetails=optimized_role_details,
            education=response['resume']['education'],
            workExperience=response['resume']['workExperience'],
            customSections=response['resume']['customSections'],
            skills=response['resume']['skills'],
            sectionOrder=resume.sectionOrder,
            template=resume.template,
        )

        output: AIResume = AIResume(
            resume=optimizedResume.model_dump(),
            oldMetric=response['oldMetric'],
            newMetric=response['newMetric'],
        )
        
        duration = time.time() - start_time
        improvement = response['newMetric'] - response['oldMetric']
        
        # Beautiful success logging with performance indicators
        if improvement > 0:
            logger.info(
                "🎉 Resume optimization completed successfully",
                duration=f"{duration:.3f}s",
                old_metric=response['oldMetric'],
                new_metric=response['newMetric'],
                improvement=f"+{improvement}",
                performance="EXCELLENT" if improvement > 10 else "GOOD" if improvement > 5 else "MODERATE"
            )
        else:
            logger.warning(
                "⚠️ Resume optimization completed with no improvement",
                duration=f"{duration:.3f}s",
                old_metric=response['oldMetric'],
                new_metric=response['newMetric'],
                improvement=improvement
            )
        
        return output
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "💥 Resume optimization failed",
            duration=f"{duration:.3f}s",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise