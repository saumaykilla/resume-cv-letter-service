from typing import List
from google import genai
from google.genai import types
from pinecone import Pinecone, ServerlessSpec
from fastapi import HTTPException
import hashlib
import os
import time
from dotenv import load_dotenv
from utils.logger import get_logger, PerformanceLogger

logger = get_logger("keywords_handler")

load_dotenv()

# Initialize Gemini client
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    logger.info("🤖 Gemini client initialized successfully")
except Exception as e:
    logger.error("💥 Failed to initialize Gemini client", error=str(e))
    raise

# Initialize Pinecone client
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "jd-keywords"
    logger.info("🌲 Pinecone client initialized successfully")
except Exception as e:
    logger.error("💥 Failed to initialize Pinecone client", error=str(e))
    raise

# Create index if not exists
try:
    if index_name not in [i.name for i in pc.list_indexes()]:
        logger.info("🏗️ Creating new Pinecone index", index_name=index_name)
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        logger.info("✅ Pinecone index created successfully")
    else:
        logger.info("✅ Pinecone index already exists", index_name=index_name)
except Exception as e:
    logger.error("💥 Failed to create/verify Pinecone index", error=str(e))
    raise

index = pc.Index(index_name)


# --- Helper to get embeddings using Gemini ---
def get_embedding(text: str):
    logger.info("🔍 Generating embedding for text", text_length=len(text))
    start_time = time.time()
    
    try:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[text],
            config={
                "output_dimensionality": 1536
            }
        )
        duration = time.time() - start_time
        PerformanceLogger.log_api_call(
            logger, 
            "Gemini", 
            "embedding_generation", 
            duration, 
            success=True,
            text_length=len(text)
        )
        return result.embeddings[0].values
    except Exception as e:
        duration = time.time() - start_time
        PerformanceLogger.log_api_call(
            logger, 
            "Gemini", 
            "embedding_generation", 
            duration, 
            success=False,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        logger.error(
            "💥 Failed to generate embedding",
            duration=f"{duration:.3f}s",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise



# --- Helper to extract keywords using Gemini ---
def extract_keywords_from_gemini(text: str):
    logger.info("🔍 Extracting keywords using Gemini", text_length=len(text))
    start_time = time.time()
    
    try:
        config = {
            'response_mime_type': 'application/json',
            'response_schema': {
                "type": "array",
                "items": {"type": "string"}
            }
        }
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Extract concise and relevant keywords from this job description:\n{text}\nReturn only a comma-separated list of keywords.",
        config=config
        )
        
        result = response.parsed
        duration = time.time() - start_time
        PerformanceLogger.log_api_call(
            logger, 
            "Gemini", 
            "keyword_extraction", 
            duration, 
            success=True,
            keyword_count=len(result)
        )
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        PerformanceLogger.log_api_call(
            logger, 
            "Gemini", 
            "keyword_extraction", 
            duration, 
            success=False,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        logger.error(
            "💥 Failed to extract keywords from Gemini",
            duration=f"{duration:.3f}s",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
    


async def keywordsExtract(job_description: str):
    logger.info("🔍 Starting keyword extraction process", job_description_length=len(job_description))
    start_time = time.time()
    
    try:
        jd_hash = hashlib.sha256(job_description.encode()).hexdigest()
        logger.info("🔐 Generated job description hash", hash=jd_hash[:8])

        # Get embedding for semantic search
        embedding = get_embedding(job_description)

        # Query Pinecone for similar JD
        logger.info("🌲 Querying Pinecone for similar job descriptions")
        results = index.query(vector=embedding, top_k=1, include_metadata=True)

        if results["matches"] and results["matches"][0]["score"] > 0.9:
            keywords = results["matches"][0]["metadata"]["keywords"]
            source = "pinecone"
            logger.info(
                "🎯 Found similar job description in Pinecone",
                score=results["matches"][0]["score"],
                keyword_count=len(keywords)
            )
        else:
            keywords = extract_keywords_from_gemini(job_description)
            source = "gemini"
            logger.info(
                "🆕 No similar job description found, using Gemini",
                top_score=results["matches"][0]["score"] if results["matches"] else 0,
                keyword_count=len(keywords)
            )
        
        # Store in Pinecone
        logger.info("💾 Storing job description in Pinecone")
        index.upsert(vectors=[{
            "id": jd_hash, 
            "values": embedding, 
            "metadata": {
                "keywords": keywords, 
                "job_description": job_description
            }
        }])

        duration = time.time() - start_time
        logger.info(
            "🎉 Keyword extraction completed successfully",
            duration=f"{duration:.3f}s",
            source=source,
            keyword_count=len(keywords)
        )
        
        return {"keywords": keywords, "source": source}
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "💥 Keyword extraction failed",
            duration=f"{duration:.3f}s",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Keyword optimizer error: {e}")
