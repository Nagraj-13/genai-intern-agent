from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class BlogPost(BaseModel):
    """Individual blog post model"""
    title: Optional[str] = None
    content: str = Field(..., min_length=10)
    tags: Optional[List[str]] = []
    author: Optional[str] = None
    created_at: Optional[datetime] = None

class UserProfile(BaseModel):
    """User profile for personalized recommendations"""
    user_id: str
    preferred_topics: List[str] = Field(default_factory=list)
    reading_level: str = Field(default="intermediate", pattern="^(beginner|intermediate|advanced)$")
    writing_style: str = Field(default="formal", pattern="^(casual|formal|technical|creative)$")
    target_audience: Optional[str] = None
    expertise_areas: List[str] = Field(default_factory=list)
    content_goals: Optional[Dict[str, Any]] = None

class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    sentiment: SentimentType
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    positive_score: float = Field(..., ge=0.0, le=1.0)
    negative_score: float = Field(..., ge=0.0, le=1.0)
    neutral_score: float = Field(..., ge=0.0, le=1.0)

class KeyTopic(BaseModel):
    """Extracted key topic"""
    topic: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    frequency: int = Field(..., ge=1)

class KeywordSuggestion(BaseModel):
    """Keyword suggestion with metadata"""
    keyword: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    context: str
    position_suggestion: Optional[int] = None
    semantic_similarity: float = Field(..., ge=0.0, le=1.0)
    
class TokenUsage(BaseModel):
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    model_used: str

class BlogAnalysisResult(BaseModel):
    """Analysis result for a single blog post"""
    blog_id: Optional[str] = None
    sentiment: SentimentAnalysis
    key_topics: List[KeyTopic]
    keyword_suggestions: List[KeywordSuggestion]
    readability_score: float = Field(..., ge=0.0, le=100.0)
    word_count: int
    estimated_reading_time: int
    token_usage: TokenUsage   # ✅ use model, not Dict[str, int]


class BlogAnalysisRequest(BaseModel):
    """Request model for blog analysis"""
    blog_posts: List[BlogPost] = Field(..., min_items=1, max_items=50)
    analysis_depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    include_keywords: bool = True
    include_sentiment: bool = True
    include_topics: bool = True

class BlogAnalysisResponse(BaseModel):
    """Response model for blog analysis"""
    results: List[BlogAnalysisResult]
    total_posts_analyzed: int
    total_tokens_used: int = 0
    processing_time_ms: float = 0.0
    timestamp: datetime

class KeywordRecommendationRequest(BaseModel):
    """Request model for keyword recommendations"""
    current_draft: str = Field(..., min_length=1)
    cursor_context: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    max_suggestions: int = Field(default=10, ge=1, le=50)
    context_window: int = Field(default=100, ge=50, le=500)

class RealtimeScore(BaseModel):
    """Real-time scoring metrics"""
    overall_score: float = Field(..., ge=0.0, le=100.0)
    readability_score: float = Field(..., ge=0.0, le=100.0)
    relevance_score: float = Field(..., ge=0.0, le=100.0)
    engagement_score: float = Field(..., ge=0.0, le=100.0)
    seo_score: float = Field(..., ge=0.0, le=100.0)

class WeakSection(BaseModel):
    """Identified weak section in the text"""
    start_position: int
    end_position: int
    issue_type: str
    severity: str = Field(..., pattern="^(low|medium|high)$")
    suggestion: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class KeywordRecommendationResponse(BaseModel):
    """Response model for keyword recommendations"""
    keywords: List[KeywordSuggestion]
    realtime_score: RealtimeScore
    weak_sections: List[WeakSection] = Field(default_factory=list)
    token_usage: TokenUsage
    suggestions_context: str
    timestamp: datetime

class AgentSession(BaseModel):
    """Agentic writing session"""
    session_id: str
    user_profile: UserProfile
    current_draft: str = ""
    suggestion_history: List[Dict[str, Any]] = Field(default_factory=list)
    score_history: List[RealtimeScore] = Field(default_factory=list)
    created_at: datetime
    last_updated: datetime
    is_active: bool = True

class AgentSuggestion(BaseModel):
    """Agent suggestion during writing"""
    suggestion_type: str = Field(..., pattern="^(keyword|improvement|structure|style)$")
    content: str
    position: Optional[int] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    priority: str = Field(..., pattern="^(low|medium|high)$")

class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    keyword_relevance: float = Field(..., ge=0.0, le=100.0)
    readability: float = Field(..., ge=0.0, le=100.0)
    user_profile_alignment: float = Field(..., ge=0.0, le=100.0)
    content_structure: float = Field(..., ge=0.0, le=100.0)
    seo_optimization: float = Field(..., ge=0.0, le=100.0)
    engagement_potential: float = Field(..., ge=0.0, le=100.0)



class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "Operation successful"
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    token_usage: Optional[TokenUsage] = None


class BlogAnalysisRequest(BlogAnalysisRequest):
    @validator('blog_posts')
    def validate_blog_posts(cls, v):
        if not v:
            raise ValueError('At least one blog post is required')
        for post in v:
            if len(post.content.strip()) < 10:
                raise ValueError('Blog post content must be at least 10 characters')
        return v

class KeywordRecommendationRequest(KeywordRecommendationRequest):
    @validator('current_draft')
    def validate_draft(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Draft content cannot be empty')
        return v

class UserProfile(UserProfile):
    @validator('reading_level')
    def validate_reading_level(cls, v):
        valid_levels = ['beginner', 'intermediate', 'advanced']
        if v not in valid_levels:
            raise ValueError(f'Reading level must be one of: {valid_levels}')
        return v
    
    @validator('writing_style')
    def validate_writing_style(cls, v):
        valid_styles = ['casual', 'formal', 'technical', 'creative']
        if v not in valid_styles:
            raise ValueError(f'Writing style must be one of: {valid_styles}')
        return v
    
