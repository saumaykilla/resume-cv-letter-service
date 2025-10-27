import asyncio
import os
import json
import uuid
from typing import Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from mangum import Mangum
from dotenv import load_dotenv
import uvicorn
from middleware.authMiddleware import AuthMiddleware
from google.genai.types import Part
from models.ResumeModel import RequestModel
from handler.keywordsExtractHandler import keywordsExtract
from handler.resumeHandler import generateResume
from handler.coverLetterHandler import generateCoverLetter
from fastapi.encoders import jsonable_encoder

from models.ResumeModel import Resume
from utils.logger import setup_logging, get_logger, RequestLogger
load_dotenv()
# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("main")

app = FastAPI()

app.add_middleware(AuthMiddleware)

@app.get('/')
async def root():
    logger.info("🏥 Health check endpoint accessed")
    return {"message":'Resume CV Letter Service'}


@app.post("/optimize")
async def optimizeApplication(request:Request,data:RequestModel):
    request_id = str(uuid.uuid4())
    
    with RequestLogger(logger, request_id, "/optimize") as req_logger:
        try:
            # Log request details
            logger.info(
                "📥 Optimize request received",
                request_id=request_id,
                has_resume=bool(data.resume),
                has_job_description=bool(data.jobDescription),
                job_description_length=len(data.jobDescription) if data.jobDescription else 0
            )
            
            if not hasattr(request.state, "user") or not request.state.user:
                logger.error(
                    "🚫 Unauthorized request",
                    request_id=request_id,
                )
                raise HTTPException(status_code=401, detail="Unauthorized")
            if not data.resume or not data.jobDescription:
                logger.warning(
                    "⚠️ Validation failed - missing required fields",
                    request_id=request_id,
                    has_resume=bool(data.resume),
                    has_job_description=bool(data.jobDescription)
                )
                raise HTTPException(status_code=400, detail="Resume or job description is required")
            
            resume = data.resume
            jobDescription = data.jobDescription
            
            # Extract keywords
            logger.info("🔍 Starting keyword extraction", request_id=request_id)
            keyword_data = await keywordsExtract(jobDescription)
            # Extract from result
            keywords = keyword_data["keywords"]
            source = keyword_data["source"]
            
            logger.info(
                "✅ Keywords extracted successfully",
                request_id=request_id,
                keyword_count=len(keywords),
                source=source
            )

            # Generate resume and cover letter
            logger.info("🚀 Starting resume and cover letter generation", request_id=request_id)
            results: Tuple[Resume,str]=await asyncio.gather(generateResume(resume,keywords),
                                                                    generateCoverLetter(resume,data.jobDescription))

            resumeData  = jsonable_encoder(results[0])
            coverLetterData = jsonable_encoder(results[1])
            
            improvement = resumeData['newMetric'] - resumeData['oldMetric']
            logger.info(
                "🎉 Generation completed successfully",
                request_id=request_id,
                source=source,
                old_metric=resumeData['oldMetric'],
                new_metric=resumeData['newMetric'],
                improvement=f"+{improvement}" if improvement > 0 else str(improvement),
                performance="EXCELLENT" if improvement > 10 else "GOOD" if improvement > 5 else "MODERATE" if improvement > 0 else "NO_IMPROVEMENT"
            )
            
            response = {
                'resume': resumeData['resume'],
                'coverLetter': coverLetterData['coverLetter'],
                'resumeName': coverLetterData['resumeName'],
                'oldMetric': resumeData['oldMetric'],
                'newMetric': resumeData['newMetric'],
            }
            
            logger.info("📤 Response prepared successfully", request_id=request_id)
            return JSONResponse(
                content=response
            )

        except HTTPException as e:
            logger.error(
                "🚫 HTTP exception occurred",
                request_id=request_id,
                status_code=e.status_code,
                detail=e.detail
            )
            raise
        except Exception as e:
            logger.error(
                "💥 Unexpected error occurred",
                request_id=request_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


handler = Mangum(app,lifespan="off")


if __name__ == "__main__":
    logger.info("🚀 Starting application server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
