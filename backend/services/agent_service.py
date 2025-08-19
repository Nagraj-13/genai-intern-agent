import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from models import (
    BlogPost, UserProfile, BlogAnalysisResult, 
    KeywordRecommendationResponse, AgentSession,
    AgentSuggestion, RealtimeScore, WeakSection
)

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the Langraph agent"""
    session_id: str
    user_profile: Dict[str, Any]
    current_draft: str
    cursor_position: int
    previous_suggestions: List[Dict[str, Any]]
    analysis_history: List[Dict[str, Any]]
    current_score: Dict[str, float]
    iteration_count: int
    last_updated: str

class AgentAction(Enum):
    """Available agent actions"""
    ANALYZE_DRAFT = "analyze_draft"
    GENERATE_KEYWORDS = "generate_keywords"
    SCORE_CONTENT = "score_content"
    IDENTIFY_WEAKNESSES = "identify_weaknesses"
    REFINE_SUGGESTIONS = "refine_suggestions"
    FINALIZE_RESPONSE = "finalize_response"

@dataclass
class AnalysisContext:
    """Context for content analysis"""
    content: str
    user_profile: Optional[UserProfile]
    cursor_position: int
    previous_analysis: List[Dict[str, Any]]
    session_metadata: Dict[str, Any]

class AgentOrchestrator:
    """
    Langraph-based agentic orchestrator for blog writing assistance.
    
    This agent operates in real-time during blog writing by:
    1. Continuously analyzing evolving drafts
    2. Learning from historical blog analysis patterns
    3. Providing contextual keyword suggestions
    4. Identifying and highlighting weak sections
    5. Adapting recommendations based on user profile
    """
    
    def __init__(self, llm_service, scoring_service):
        self.llm_service = llm_service
        self.scoring_service = scoring_service
        self.active_sessions: Dict[str, AgentSession] = {}
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.historical_patterns: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize Langraph workflow
        self.memory = MemorySaver()
        self.workflow = self._build_workflow()
        
        logger.info("Agent Orchestrator initialized with Langraph workflow")
    
    def _build_workflow(self) -> StateGraph:
        """Build the Langraph workflow for agentic processing"""
        
        workflow = StateGraph(AgentState)
        
        # Define nodes (agent functions)
        workflow.add_node("analyze_draft", self._analyze_draft_node)
        workflow.add_node("generate_keywords", self._generate_keywords_node)
        workflow.add_node("score_content", self._score_content_node)
        workflow.add_node("identify_weaknesses", self._identify_weaknesses_node)
        workflow.add_node("refine_suggestions", self._refine_suggestions_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # Define workflow edges
        workflow.set_entry_point("analyze_draft")
        
        workflow.add_edge("analyze_draft", "generate_keywords")
        workflow.add_edge("generate_keywords", "score_content")
        workflow.add_edge("score_content", "identify_weaknesses")
        workflow.add_edge("identify_weaknesses", "refine_suggestions")
        workflow.add_edge("refine_suggestions", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        # Add conditional edges for iterative refinement
        workflow.add_conditional_edges(
            "finalize_response",
            self._should_iterate,
            {
                "continue": "analyze_draft",
                "end": END
            }
        )
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _analyze_draft_node(self, state: AgentState) -> AgentState:
        """Analyze the current draft"""
        try:
            logger.info(f"Analyzing draft for session {state['session_id']}")
            
            # Get analysis from LLM
            user_profile = UserProfile(**state['user_profile']) if state['user_profile'] else None
            analysis = await self.llm_service.recommend_keywords(
                state['current_draft'],
                cursor_context=self._get_cursor_context(state['current_draft'], state['cursor_position']),
                user_profile=user_profile
            )
            
            # Update state
            state['analysis_history'].append({
                "timestamp": datetime.utcnow().isoformat(),
                "analysis": analysis,
                "draft_length": len(state['current_draft'])
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in analyze_draft_node: {str(e)}")
            return state
    
    async def _generate_keywords_node(self, state: AgentState) -> AgentState:
        """Generate contextual keyword suggestions"""
        try:
            logger.info(f"Generating keywords for session {state['session_id']}")
            
            # Use historical patterns for better suggestions
            historical_context = self._get_historical_context(state['user_profile'])
            
            # Enhanced keyword generation with context
            current_analysis = state['analysis_history'][-1]['analysis'] if state['analysis_history'] else {}
            keywords = current_analysis.get('keywords', [])
            
            # Apply historical learning
            refined_keywords = self._apply_historical_learning(keywords, historical_context)
            
            # Update state
            state['previous_suggestions'].append({
                "timestamp": datetime.utcnow().isoformat(),
                "keywords": refined_keywords,
                "context": "historical_pattern_applied"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Error in generate_keywords_node: {str(e)}")
            return state
    
    async def _score_content_node(self, state: AgentState) -> AgentState:
        """Score the current content"""
        try:
            logger.info(f"Scoring content for session {state['session_id']}")
            
            user_profile = UserProfile(**state['user_profile']) if state['user_profile'] else None
            score_result = await self.scoring_service.calculate_comprehensive_score(
                state['current_draft'], user_profile
            )
            
            # Update state
            state['current_score'] = score_result['breakdown']
            
            return state
            
        except Exception as e:
            logger.error(f"Error in score_content_node: {str(e)}")
            return state
    
    async def _identify_weaknesses_node(self, state: AgentState) -> AgentState:
        """Identify weak sections in the content"""
        try:
            logger.info(f"Identifying weaknesses for session {state['session_id']}")
            weak_sections = []
            content = state['current_draft']
            sentences = content.split('. ')
            for i, sentence in enumerate(sentences):
                if len(sentence) < 10:  # Too short
                    weak_sections.append({
                        "start_position": content.find(sentence),
                        "end_position": content.find(sentence) + len(sentence),
                        "issue_type": "sentence_too_short",
                        "severity": "medium",
                        "suggestion": "Consider expanding this sentence with more detail",
                        "confidence": 0.7
                    })
            
            # Store in current analysis
            if state['analysis_history']:
                state['analysis_history'][-1]['weak_sections'] = weak_sections
            
            return state
            
        except Exception as e:
            logger.error(f"Error in identify_weaknesses_node: {str(e)}")
            return state
    
    async def _refine_suggestions_node(self, state: AgentState) -> AgentState:
        """Refine suggestions based on context and history"""
        try:
            logger.info(f"Refining suggestions for session {state['session_id']}")
            
            # Get latest suggestions
            latest_suggestions = state['previous_suggestions'][-1] if state['previous_suggestions'] else {}
            keywords = latest_suggestions.get('keywords', [])
            
            # Apply contextual refinement
            refined_keywords = self._contextual_refinement(
                keywords, 
                state['current_draft'],
                state['cursor_position'],
                state['current_score']
            )
            
            # Update suggestions
            if state['previous_suggestions']:
                state['previous_suggestions'][-1]['refined_keywords'] = refined_keywords
            
            return state
            
        except Exception as e:
            logger.error(f"Error in refine_suggestions_node: {str(e)}")
            return state
    
    async def _finalize_response_node(self, state: AgentState) -> AgentState:
        """Finalize the response for the client"""
        try:
            logger.info(f"Finalizing response for session {state['session_id']}")
            
            # Prepare final response structure
            latest_analysis = state['analysis_history'][-1] if state['analysis_history'] else {}
            latest_suggestions = state['previous_suggestions'][-1] if state['previous_suggestions'] else {}
            
            # Create comprehensive response
            state['final_response'] = {
                "keywords": latest_suggestions.get('refined_keywords', []),
                "realtime_score": state['current_score'],
                "weak_sections": latest_analysis.get('weak_sections', []),
                "suggestions_context": f"Analysis iteration {state['iteration_count']}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state['iteration_count'] = state.get('iteration_count', 0) + 1
            state['last_updated'] = datetime.utcnow().isoformat()
            
            return state
            
        except Exception as e:
            logger.error(f"Error in finalize_response_node: {str(e)}")
            return state
    
    def _should_iterate(self, state: AgentState) -> str:
        """Determine if workflow should continue iterating"""
        # Simple iteration logic - can be made more sophisticated
        max_iterations = 2
        current_iterations = state.get('iteration_count', 0)
        
        if current_iterations < max_iterations:
            # Check if content changed significantly
            if self._content_changed_significantly(state):
                return "continue"
        
        return "end"
    
    def _content_changed_significantly(self, state: AgentState) -> bool:
        """Check if content has changed significantly since last analysis"""
        if len(state['analysis_history']) < 2:
            return False
        
        current_length = len(state['current_draft'])
        previous_length = state['analysis_history'][-2].get('draft_length', 0)
        
        # Consider significant if 20% change in length
        change_ratio = abs(current_length - previous_length) / max(previous_length, 1)
        return change_ratio > 0.2
    
    def _get_cursor_context(self, content: str, cursor_position: int, context_size: int = 100) -> str:
        """Get text context around cursor position"""
        start = max(0, cursor_position - context_size)
        end = min(len(content), cursor_position + context_size)
        return content[start:end]
    
    def _get_historical_context(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical patterns for the user"""
        user_id = user_profile.get('user_id', 'default')
        return self.historical_patterns.get(user_id, [])
    
    def _apply_historical_learning(self, keywords: List[Dict], historical_context: List[Dict]) -> List[Dict]:
        """Apply historical learning to improve keyword suggestions"""
        if not historical_context:
            return keywords
        
        # Simple implementation - boost keywords that worked well historically
        for keyword in keywords:
            for historical in historical_context:
                if keyword.get('keyword') in historical.get('successful_keywords', []):
                    keyword['relevance_score'] = min(1.0, keyword.get('relevance_score', 0.5) * 1.2)
        
        return keywords
    
    def _contextual_refinement(self, keywords: List[Dict], content: str, cursor_position: int, current_score: Dict) -> List[Dict]:
        """Apply contextual refinement to keywords"""
        refined_keywords = []
        
        for keyword in keywords:
            # Boost keywords that improve low-scoring areas
            relevance = keyword.get('relevance_score', 0.5)
            
            # If readability is low, boost readability-improving keywords
            if current_score.get('readability', 70) < 60:
                if any(term in keyword.get('keyword', '').lower() for term in ['simple', 'clear', 'easy']):
                    relevance *= 1.3
            
            # If SEO score is low, boost SEO keywords
            if current_score.get('seo', 70) < 60:
                if any(term in keyword.get('keyword', '').lower() for term in ['keyword', 'search', 'optimize']):
                    relevance *= 1.2
            
            keyword['relevance_score'] = min(1.0, relevance)
            refined_keywords.append(keyword)
        
        # Sort by relevance
        refined_keywords.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return refined_keywords[:10]  # Return top 10
    
    async def start_session(self, user_profile: UserProfile) -> str:
        """Start a new agentic writing session"""
        try:
            session_id = str(uuid.uuid4())
            
            session = AgentSession(
                session_id=session_id,
                user_profile=user_profile,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            self.active_sessions[session_id] = session
            
            logger.info(f"Started new agent session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
            raise
    
    async def update_draft(self, session_id: str, draft_text: str, cursor_position: Optional[int] = None) -> Dict[str, Any]:
        """Update draft and get real-time suggestions using Langraph workflow"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            session.current_draft = draft_text
            session.last_updated = datetime.utcnow()
            
            # Create initial state for Langraph workflow
            initial_state = AgentState(
                session_id=session_id,
                user_profile=session.user_profile.dict(),
                current_draft=draft_text,
                cursor_position=cursor_position or 0,
                previous_suggestions=[],
                analysis_history=[],
                current_score={},
                iteration_count=0,
                last_updated=datetime.utcnow().isoformat()
            )
            
            # Execute Langraph workflow
            config = {"configurable": {"thread_id": session_id}}
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            # Extract response from final state
            response = final_state.get('final_response', {})
            
            # Update session history
            session.suggestion_history.append(response)
            
            logger.info(f"Updated draft for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error updating draft: {str(e)}")
            raise
    
    async def analyze_blog_posts(self, blog_posts: List[BlogPost]) -> List[BlogAnalysisResult]:
        """Analyze multiple blog posts and learn patterns"""
        try:
            results = []
            
            for blog_post in blog_posts:
                # Analyze individual post
                analysis = await self.llm_service.analyze_blog_post(blog_post)
                
                # Convert to BlogAnalysisResult
                result = BlogAnalysisResult(**analysis)
                results.append(result)
                
                # Store patterns for learning
                await self._store_analysis_pattern(blog_post, analysis)
            
            logger.info(f"Analyzed {len(blog_posts)} blog posts")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing blog posts: {str(e)}")
            raise
    
    async def recommend_keywords(
        self, 
        current_draft: str, 
        cursor_context: Optional[str] = None,
        user_profile: Optional[UserProfile] = None
    ) -> KeywordRecommendationResponse:
        """Generate keyword recommendations (non-session based)"""
        try:
            # Use LLM service directly for non-session recommendations
            result = await self.llm_service.recommend_keywords(
                current_draft, cursor_context, user_profile
            )
            
            # Convert to proper response format
            return KeywordRecommendationResponse(
                keywords=result['keywords'],
                realtime_score=RealtimeScore(**result['realtime_score']),
                weak_sections=[WeakSection(**ws) for ws in result['weak_sections']],
                token_usage=result['token_usage'],
                suggestions_context=result['suggestions_context'],
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    async def _store_analysis_pattern(self, blog_post: BlogPost, analysis: Dict[str, Any]):
        """Store analysis patterns for historical learning"""
        try:
            # Extract successful keywords (high relevance)
            successful_keywords = [
                kw.keyword for kw in analysis.get('keyword_suggestions', [])
                if kw.relevance_score > 0.7
            ]
            
            pattern = {
                "timestamp": datetime.utcnow().isoformat(),
                "content_length": len(blog_post.content),
                "successful_keywords": successful_keywords,
                "readability_score": analysis.get('readability_score', 0),
                "topics": [topic.topic for topic in analysis.get('key_topics', [])],
                "sentiment": analysis.get('sentiment', {}).sentiment if analysis.get('sentiment') else 'neutral'
            }
            
            # Store pattern
            user_key = 'general'  # Could be user-specific
            if user_key not in self.historical_patterns:
                self.historical_patterns[user_key] = []
            
            self.historical_patterns[user_key].append(pattern)
            
            # Keep only recent patterns (last 100)
            self.historical_patterns[user_key] = self.historical_patterns[user_key][-100:]
            
        except Exception as e:
            logger.error(f"Error storing analysis pattern: {str(e)}")
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End an agentic writing session"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.active_sessions[session_id]
            session.is_active = False
            
            # Generate session summary
            summary = {
                "session_duration": (datetime.utcnow() - session.created_at).total_seconds(),
                "total_suggestions": len(session.suggestion_history),
                "final_draft_length": len(session.current_draft),
                "average_score": self._calculate_average_score(session.score_history)
            }
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Ended session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            raise
    
    def _calculate_average_score(self, score_history: List[RealtimeScore]) -> float:
        """Calculate average score from history"""
        if not score_history:
            return 0.0
        
        total = sum(score.overall_score for score in score_history)
        return total / len(score_history)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent orchestrator status"""
        return {
            "active_sessions": len(self.active_sessions),
            "total_patterns_stored": sum(len(patterns) for patterns in self.historical_patterns.values()),
            "workflow_status": "healthy",
            "last_check": datetime.utcnow().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for agent orchestrator"""
        try:
            return {
                "status": "healthy",
                "active_sessions": len(self.active_sessions),
                "workflow_initialized": self.workflow is not None,
                "memory_status": "active",
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": str(e),
                "last_check": datetime.utcnow().isoformat()
            }