from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from models import (
    BlogAnalysisRequest, BlogAnalysisResponse,
    KeywordRecommendationRequest, KeywordRecommendationResponse,
    BlogPost, UserProfile
)
from services.llm_service import LLMService
from services.agent_service import AgentOrchestrator
from services.scoring_service import BlogScoringService
from utils.auth import verify_token
from utils.retry import retry_with_exponential_backoff
from contextlib import asynccontextmanager

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await llm_service.initialize()
    logger.info("Backend services initialized successfully")
    
    yield  

    logger.info("Shutting down services...")

app = FastAPI(
    title="Agentic Blog Support System",
    description="Backend API for intelligent blog writing assistance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
llm_service = LLMService()
scoring_service = BlogScoringService()
agent_orchestrator = AgentOrchestrator(llm_service, scoring_service)



@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Agentic Blog Support System API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "llm": await llm_service.health_check(),
            "scoring": scoring_service.health_check(),
            "agent": agent_orchestrator.health_check()
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/analyze-blogs", response_model=BlogAnalysisResponse)
async def analyze_blogs(
    request: BlogAnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Analyze existing blog posts for sentiment, topics, and keywords
    """
    try:
        # Verify authentication
        print(credentials.credentials)
        await verify_token(credentials.credentials)
        
        logger.info(f"Analyzing {len(request.blog_posts)} blog posts")
        
        # Use retry mechanism for LLM calls
        analysis_results = await retry_with_exponential_backoff(
            agent_orchestrator.analyze_blog_posts,
            request.blog_posts,
            max_retries=3
        )
        
        logger.info("Blog analysis completed successfully")
        return BlogAnalysisResponse(
            results=analysis_results,
            total_posts_analyzed=len(request.blog_posts),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error analyzing blogs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/recommend-keywords", response_model=KeywordRecommendationResponse)
async def recommend_keywords(
    request: KeywordRecommendationRequest,
    # credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Get real-time keyword recommendations for blog writing
    """
    try:
        # Verify authentication
        # await verify_token(credentials.credentials)
        
        logger.info("Generating keyword recommendations")
        
        # Use retry mechanism for LLM calls
        recommendations = await retry_with_exponential_backoff(
            agent_orchestrator.recommend_keywords,
            request.current_draft,
            request.cursor_context,
            request.user_profile,
            max_retries=3
        )
        
        logger.info("Keyword recommendations generated successfully")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.post("/api/score-blog")
async def score_blog(
    blog_text: str,
    user_profile: Optional[UserProfile] = None,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Score a blog post based on multiple factors
    """
    try:
        # Verify authentication
        await verify_token(credentials.credentials)
        
        logger.info("Scoring blog post")
        
        score_result = await scoring_service.calculate_comprehensive_score(
            blog_text, user_profile
        )
        
        return {
            "score": score_result["overall_score"],
            "breakdown": score_result["breakdown"],
            "recommendations": score_result["recommendations"],
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error scoring blog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@app.get("/api/agent-status")
async def get_agent_status(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Get current status of the agentic workflow
    """
    try:
        # Verify authentication
        await verify_token(credentials.credentials)
        
        status = agent_orchestrator.get_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.post("/api/start-agent-session")
async def start_agent_session(
    user_profile: UserProfile,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Start a new agentic writing session
    """
    try:
        # Verify authentication
        await verify_token(credentials.credentials)
        
        session_id = await agent_orchestrator.start_session(user_profile)
        
        return {
            "session_id": session_id,
            "status": "active",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error starting agent session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session start failed: {str(e)}")

@app.post("/api/update-draft")
async def update_draft(
    session_id: str,
    draft_text: str,
    cursor_position: Optional[int] = None,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Update the current draft and get real-time suggestions
    """
    try:

        await verify_token(credentials.credentials)
        
        suggestions = await agent_orchestrator.update_draft(
            session_id, draft_text, cursor_position
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error updating draft: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Draft update failed: {str(e)}")

@app.delete("/api/end-session/{session_id}")
async def end_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    End an agentic writing session
    """
    try:
        # Verify authentication
        await verify_token(credentials.credentials)
        
        summary = await agent_orchestrator.end_session(session_id)
        
        return {
            "message": "Session ended successfully",
            "summary": summary,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session end failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000,reload=True)