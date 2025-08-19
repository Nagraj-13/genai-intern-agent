import os 
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken
import google.generativeai as genai
from google.genai.types import HarmCategory, HarmBlockThreshold
from utils.utils import sanitize_json
from models import (
    BlogPost, UserProfile, SentimentAnalysis, KeyTopic, 
    KeywordSuggestion, TokenUsage, BlogAnalysisResult, SentimentType
)

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM Service using Google's Gemini Pro for blog analysis and recommendations.
    
    Gemini Pro was chosen for:
    1. Cost-effectiveness (free tier available)
    2. Good context window (up to 32k tokens)
    3. Strong reasoning capabilities for content analysis
    4. Built-in safety features
    5. Fast response times
    6. Structured output support
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL")  
        self.model = None
        self.tokenizer = None
        self.total_tokens_used = 0
        
        self.response_schemas = {
            "blog_analysis": {
                "type": "object",
                "properties": {
                    "sentiment": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "confidence": {"type": "number"},
                            "scores": {
                                "type": "object",
                                "properties": {
                                    "positive": {"type": "number"},
                                    "negative": {"type": "number"},
                                    "neutral": {"type": "number"}
                                },
                                "required": ["positive", "negative", "neutral"]
                            }
                        },
                        "required": ["type", "confidence", "scores"]
                    },
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "relevance": {"type": "number"},
                                "frequency": {"type": "integer"}
                            },
                            "required": ["topic", "relevance", "frequency"]
                        }
                    },
                    "keywords": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "keyword": {"type": "string"},
                                "relevance": {"type": "number"},
                                "context": {"type": "string"},
                                "similarity": {"type": "number"}
                            },
                            "required": ["keyword", "relevance", "context", "similarity"]
                        }
                    },
                    "readability": {"type": "number"}
                },
                "required": ["sentiment", "topics", "keywords", "readability"]
            },
            
            "keyword_recommendations": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "keyword": {"type": "string"},
                                "relevance": {"type": "number"},
                                "context": {"type": "string"},
                                "position": {"type": "integer"},
                                "similarity": {"type": "number"}
                            },
                            "required": ["keyword", "relevance", "context", "similarity"]
                        }
                    },
                    "weak_sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "integer"},
                                "end": {"type": "integer"},
                                "issue": {"type": "string"},
                                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                                "suggestion": {"type": "string"},
                                "confidence": {"type": "number"}
                            },
                            "required": ["start", "end", "issue", "severity", "suggestion", "confidence"]
                        }
                    },
                    "scores": {
                        "type": "object",
                        "properties": {
                            "overall": {"type": "number"},
                            "readability": {"type": "number"},
                            "relevance": {"type": "number"},
                            "engagement": {"type": "number"},
                            "seo": {"type": "number"}
                        },
                        "required": ["overall", "readability", "relevance", "engagement", "seo"]
                    }
                },
                "required": ["keywords", "weak_sections", "scores"]
            },
            
            "content_scoring": {
                "type": "object",
                "properties": {
                    "overall_score": {"type": "number"},
                    "breakdown": {
                        "type": "object",
                        "properties": {
                            "keyword_relevance": {"type": "number"},
                            "readability": {"type": "number"},
                            "user_alignment": {"type": "number"},
                            "structure": {"type": "number"},
                            "seo": {"type": "number"},
                            "engagement": {"type": "number"}
                        },
                        "required": ["keyword_relevance", "readability", "user_alignment", "structure", "seo", "engagement"]
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["overall_score", "breakdown", "recommendations"]
            }
        }
        
        self.prompts = {
            "analyze_blog": """Analyze this blog post:

Content: "{content}"

Return JSON with:
1. sentiment: {{type: "positive"|"negative"|"neutral", confidence: 0.0-1.0, scores: {{positive: 0.0-1.0, negative: 0.0-1.0, neutral: 0.0-1.0}}}}
2. topics: Array of max 5 {{topic: string, relevance: 0.0-1.0, frequency: integer}}
3. keywords: Array of max 10 {{keyword: string, relevance: 0.0-1.0, context: string, similarity: 0.0-1.0}}
4. readability: number 0-100

Be concise and precise with numeric values.""",

            "recommend_keywords": """Current draft: "{draft}"
Context: "{cursor_context}"
Profile: {user_profile}

Return JSON with:
1. keywords: Array of max 10 {{keyword: string, relevance: 0.0-1.0, context: string, position: integer, similarity: 0.0-1.0}}
2. weak_sections: Array {{start: int, end: int, issue: string, severity: "low"|"medium"|"high", suggestion: string, confidence: 0.0-1.0}}
3. scores: {{overall: 0-100, readability: 0-100, relevance: 0-100, engagement: 0-100, seo: 0-100}}

Focus on actionable improvements.""",

            "score_content": """Score this content:

Content: "{content}"
Profile: {user_profile}

Return JSON with:
1. overall_score: 0-100
2. breakdown: {{keyword_relevance: 0-100, readability: 0-100, user_alignment: 0-100, structure: 0-100, seo: 0-100, engagement: 0-100}}
3. recommendations: Array of max 5 specific actionable strings

Be precise with scores 0-100."""
        }
    
    async def initialize(self):
        """Initialize the Gemini model"""
        try:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            
            genai.configure(api_key=self.api_key)
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
            logger.info(f"LLM Service initialized with {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {str(e)}")
            raise
    
    def _optimize_content_length(self, content: str, max_tokens: int = 1500) -> str:
        """Optimize content length to prevent token overflow"""
        if not content:
            return content
            
        current_tokens = self.count_tokens(content)
        if current_tokens <= max_tokens:
            return content
    
        char_per_token = len(content) / current_tokens
        target_chars = int(max_tokens * char_per_token * 0.9) 

        if len(content) > target_chars:
            truncated = content[:target_chars]
            last_space = truncated.rfind(' ')
            if last_space > target_chars * 0.8:  
                content = truncated[:last_space] + "..."
            else:
                content = truncated + "..."
        
        return content
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text.split()) * 1.3  
    
    def _fix_truncated_json(self, text: str) -> str:
        """Fix truncated JSON by adding missing closing braces/brackets"""
        if not text.strip():
            return text
        
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        

        fixed_text = text
        if open_braces > close_braces:
            fixed_text += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            fixed_text += ']' * (open_brackets - close_brackets)
        
        # Try to remove trailing comma if present
        fixed_text = fixed_text.rstrip().rstrip(',')
        
        return fixed_text
    
    def _fix_json_response(self, text: str) -> str:
        """Fix common JSON formatting issues"""
        if not text.strip():
            return text
        
        # Remove any markdown code block markers
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Fix common issues
        fixes = [
            # Remove trailing commas
            (r',(\s*[}\]])', r'\1'),
            # Fix unescaped quotes in strings (basic fix)
            (r'(?<!\\)"(?=[^,}\]]*[,}\]])', r'\\"'),
        ]
        
        import re
        fixed_text = text
        for pattern, replacement in fixes:
            fixed_text = re.sub(pattern, replacement, fixed_text)
        
        # Try the truncated JSON fix as well
        fixed_text = self._fix_truncated_json(fixed_text)
        
        return fixed_text
    
    def _validate_and_sanitize_response(self, response_data: Dict[str, Any], schema_key: str) -> Dict[str, Any]:
        """Validate and sanitize response data to ensure values are within expected ranges"""
        try:
            if schema_key == "blog_analysis":
                # Sanitize sentiment scores
                if "sentiment" in response_data:
                    sentiment = response_data["sentiment"]
                    if "confidence" in sentiment:
                        sentiment["confidence"] = max(0.0, min(1.0, float(sentiment["confidence"])))
                    
                    if "scores" in sentiment:
                        for score_type in ["positive", "negative", "neutral"]:
                            if score_type in sentiment["scores"]:
                                sentiment["scores"][score_type] = max(0.0, min(1.0, float(sentiment["scores"][score_type])))
                
                # Sanitize topics and limit to 5 items
                if "topics" in response_data:
                    response_data["topics"] = response_data["topics"][:5]  # Limit to 5 items
                    for topic in response_data["topics"]:
                        if "relevance" in topic:
                            topic["relevance"] = max(0.0, min(1.0, float(topic["relevance"])))
                        if "frequency" in topic:
                            topic["frequency"] = max(1, int(topic["frequency"]))
                
                # Sanitize keywords and limit to 10 items
                if "keywords" in response_data:
                    response_data["keywords"] = response_data["keywords"][:10]  # Limit to 10 items
                    for keyword in response_data["keywords"]:
                        if "relevance" in keyword:
                            keyword["relevance"] = max(0.0, min(1.0, float(keyword["relevance"])))
                        if "similarity" in keyword:
                            keyword["similarity"] = max(0.0, min(1.0, float(keyword["similarity"])))
                
                # Sanitize readability
                if "readability" in response_data:
                    response_data["readability"] = max(0, min(100, int(float(response_data["readability"]))))
            
            elif schema_key == "keyword_recommendations":
                # Sanitize keywords and limit to 10 items
                if "keywords" in response_data:
                    response_data["keywords"] = response_data["keywords"][:10]  # Limit to 10 items
                    for keyword in response_data["keywords"]:
                        if "relevance" in keyword:
                            keyword["relevance"] = max(0.0, min(1.0, float(keyword["relevance"])))
                        if "similarity" in keyword:
                            keyword["similarity"] = max(0.0, min(1.0, float(keyword["similarity"])))
                        if "position" in keyword:
                            keyword["position"] = max(0, int(keyword.get("position", 0)))
                
                # Sanitize weak sections (no hard limit, but validate data)
                if "weak_sections" in response_data:
                    for section in response_data["weak_sections"]:
                        if "confidence" in section:
                            section["confidence"] = max(0.0, min(1.0, float(section["confidence"])))
                        if "start" in section:
                            section["start"] = max(0, int(section["start"]))
                        if "end" in section:
                            section["end"] = max(0, int(section["end"]))
                
                # Sanitize scores
                if "scores" in response_data:
                    for score_type in ["overall", "readability", "relevance", "engagement", "seo"]:
                        if score_type in response_data["scores"]:
                            response_data["scores"][score_type] = max(0, min(100, int(float(response_data["scores"][score_type]))))
            
            elif schema_key == "content_scoring":
                # Sanitize overall score
                if "overall_score" in response_data:
                    response_data["overall_score"] = max(0, min(100, int(float(response_data["overall_score"]))))
                
                # Sanitize breakdown scores
                if "breakdown" in response_data:
                    for score_type in ["keyword_relevance", "readability", "user_alignment", "structure", "seo", "engagement"]:
                        if score_type in response_data["breakdown"]:
                            response_data["breakdown"][score_type] = max(0, min(100, int(float(response_data["breakdown"][score_type]))))
                
                # Limit recommendations to 5 items
                if "recommendations" in response_data:
                    response_data["recommendations"] = response_data["recommendations"][:5]
            
            return response_data
            
        except Exception as e:
            logger.warning(f"Error sanitizing response data: {e}")
            return response_data  # Return original if sanitization fails
    
    async def generate_structured_response(self, prompt: str, schema_key: str) -> tuple[Dict[str, Any], TokenUsage]:
        """Generate structured response using Gemini's response schema"""
        try:
            prompt_tokens = self.count_tokens(prompt)

            # Configure generation with response schema - increased token limit
            config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.9,
                top_k=40,
                max_output_tokens=4096,  # Increased from 2048
                response_mime_type="application/json",
                response_schema=self.response_schemas[schema_key]
            )

            response = await self.model.generate_content_async(prompt, generation_config=config)
            
            # Better handling of response extraction
            response_text = ""
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Check finish reason
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    logger.info(f"Response finish reason: {finish_reason}")
                    
                    # Handle different finish reasons
                    if finish_reason == 2:  # MAX_TOKENS
                        logger.warning("Response was truncated due to max tokens limit")
                    elif finish_reason == 3:  # SAFETY
                        logger.warning("Response was blocked due to safety filters")
                        raise ValueError("Response blocked by safety filters")
                    elif finish_reason == 4:  # RECITATION
                        logger.warning("Response was blocked due to recitation filters")
                        raise ValueError("Response blocked by recitation filters")
                
                # Extract content even if truncated
                if candidate.content and candidate.content.parts:
                    response_text = "".join(
                        [p.text for p in candidate.content.parts if hasattr(p, "text") and p.text]
                    )
                
                # If we got truncated content, try to make it valid JSON
                if finish_reason == 2 and response_text:
                    response_text = self._fix_truncated_json(response_text)
            
            if not response_text:
                logger.warning(f"No response text extracted, using fallback")
                raise ValueError(f"Model returned no content. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")

            # Parse JSON response
            try:
                response_data = json.loads(response_text)
                # Validate and sanitize the response
                response_data = self._validate_and_sanitize_response(response_data, schema_key)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response (first 500 chars): {response_text[:500]}")
                
                # Try to fix common JSON issues
                fixed_text = self._fix_json_response(response_text)
                if fixed_text != response_text:
                    try:
                        response_data = json.loads(fixed_text)
                        response_data = self._validate_and_sanitize_response(response_data, schema_key)
                        logger.info("Successfully fixed and parsed JSON response")
                    except json.JSONDecodeError:
                        logger.error("Could not fix JSON response, using fallback")
                        response_data = self._get_fallback_response(schema_key)
                else:
                    response_data = self._get_fallback_response(schema_key)

            completion_tokens = self.count_tokens(response_text) if response_text else 100
            total_tokens = prompt_tokens + completion_tokens
            self.total_tokens_used += total_tokens
            
            # Updated cost calculation for Gemini pricing
            cost_estimate = (prompt_tokens / 1000000 * 0.125) + (completion_tokens / 1000000 * 0.375)

            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_estimate=cost_estimate,
                model_used=self.model_name,
            )

            return response_data, token_usage

        except Exception as e:
            logger.error(f"Error generating structured response: {str(e)}")
            # Return fallback response instead of raising
            fallback_data = self._get_fallback_response(schema_key)
            token_usage = TokenUsage(
                prompt_tokens=self.count_tokens(prompt),
                completion_tokens=100,  # Estimate
                total_tokens=self.count_tokens(prompt) + 100,
                cost_estimate=0.0,
                model_used=self.model_name,
            )
            return fallback_data, token_usage
    
    async def analyze_blog_post(self, blog_post: BlogPost) -> BlogAnalysisResult:
        """Analyze a single blog post using structured output"""
        try:
        
            optimized_content = self._optimize_content_length(blog_post.content, max_tokens=1200)
            
            prompt = self.prompts["analyze_blog"].format(
                content=optimized_content
            )
        
            logger.info(f"Analyzing blog post (original length: {len(blog_post.content)}, optimized: {len(optimized_content)})")
        
            response_data, token_usage = await self.generate_structured_response(
                prompt, "blog_analysis"
            )
            
            analysis_result = self._format_analysis_result(response_data, blog_post, token_usage)
            
            logger.info(f"Blog analysis completed. Tokens used: {token_usage.total_tokens}")
            return analysis_result
        
        except Exception as e:
            logger.error(f"Error analyzing blog post: {str(e)}")
            raise

    async def recommend_keywords(
        self, 
        draft: str, 
        cursor_context: Optional[str] = None,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Generate keyword recommendations using structured output"""
        try:
            profile_str = json.dumps(user_profile.dict()) if user_profile else "{}"
            
            optimized_draft = self._optimize_content_length(draft, max_tokens=800)
            optimized_context = self._optimize_content_length(cursor_context or "", max_tokens=200)
            
            prompt = self.prompts["recommend_keywords"].format(
                draft=optimized_draft,
                cursor_context=optimized_context,
                user_profile=profile_str
            )
            
            logger.info("Generating keyword recommendations")
            
            response_data, token_usage = await self.generate_structured_response(
                prompt, "keyword_recommendations"
            )
            
       
            formatted_result = self._format_keyword_result(response_data, token_usage)
            
            logger.info(f"Keyword recommendations completed. Tokens used: {token_usage.total_tokens}")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error generating keyword recommendations: {str(e)}")
            raise
    
    async def score_content(
        self, 
        content: str, 
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Score content using structured output"""
        try:
            profile_str = json.dumps(user_profile.dict()) if user_profile else "{}"
            
            optimized_content = self._optimize_content_length(content, max_tokens=1000)
            
            prompt = self.prompts["score_content"].format(
                content=optimized_content,
                user_profile=profile_str
            )
            
            logger.info("Scoring content")
            
            response_data, token_usage = await self.generate_structured_response(
                prompt, "content_scoring"
            )
            
            response_data["token_usage"] = token_usage.dict()
            
            logger.info(f"Content scoring completed. Score: {response_data.get('overall_score', 0)}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error scoring content: {str(e)}")
            raise
    
    def _format_analysis_result(self, result: Dict, blog_post: BlogPost, token_usage: TokenUsage) -> Dict[str, Any]:
        """Format analysis result to match expected structure"""
        sentiment_data = result.get("sentiment", {})
        
        return {
            "sentiment": SentimentAnalysis(
                sentiment=SentimentType(sentiment_data.get("type", "neutral")),
                confidence_score=sentiment_data.get("confidence", 0.5),
                positive_score=sentiment_data.get("scores", {}).get("positive", 0.0),
                negative_score=sentiment_data.get("scores", {}).get("negative", 0.0),
                neutral_score=sentiment_data.get("scores", {}).get("neutral", 1.0)
            ),
            "key_topics": [
                KeyTopic(
                    topic=topic["topic"],
                    relevance_score=topic["relevance"],
                    frequency=topic["frequency"]
                )
                for topic in result.get("topics", [])
            ],
            "keyword_suggestions": [
                KeywordSuggestion(
                    keyword=kw["keyword"],
                    relevance_score=kw["relevance"],
                    context=kw["context"],
                    semantic_similarity=kw["similarity"]
                )
                for kw in result.get("keywords", [])
            ],
            "readability_score": result.get("readability", 50),
            "word_count": len(blog_post.content.split()),
            "estimated_reading_time": max(1, len(blog_post.content.split()) // 200),
            "token_usage": token_usage.dict()
        }
    
    def _format_keyword_result(self, result: Dict, token_usage: TokenUsage) -> Dict[str, Any]:  
        """Format keyword recommendation result"""


        scores_data = result.get("scores", {})


        formatted_scores = {
            "overall_score": scores_data.get("overall", 70),
            "readability_score": scores_data.get("readability", 65), 
            "relevance_score": scores_data.get("relevance", 75),
            "engagement_score": scores_data.get("engagement", 70),
            "seo_score": scores_data.get("seo", 65)
        }


        formatted_weak_sections = []
        for section in result.get("weak_sections", []):
            formatted_section = {
                "start_position": section.get("start", 0),
                "end_position": section.get("end", 0),
                "issue_type": section.get("issue", "general"),
                "severity": section.get("severity", "medium"),
                "suggestion": section.get("suggestion", ""),
                "confidence": section.get("confidence", 0.7)  
            }
            formatted_weak_sections.append(formatted_section)

        return {
            "keywords": [
                KeywordSuggestion(
                    keyword=kw["keyword"],
                    relevance_score=kw["relevance"],
                    context=kw["context"],
                    position_suggestion=kw.get("position"),
                    semantic_similarity=kw["similarity"]
                )
               for kw in result.get("keywords", [])
            ],
            "weak_sections": formatted_weak_sections, 
            "realtime_score": formatted_scores,  
            "token_usage": token_usage.dict(),
            "suggestions_context": "Real-time analysis based on current draft"
        }  
        
    def _get_fallback_response(self, schema_key: str) -> Dict[str, Any]:
        """Get fallback response based on schema type"""
        fallbacks = {
            "blog_analysis": {
                "sentiment": {"type": "neutral", "confidence": 0.5, "scores": {"positive": 0.3, "negative": 0.2, "neutral": 0.5}},
                "topics": [{"topic": "general content", "relevance": 0.7, "frequency": 1}],
                "keywords": [{"keyword": "content", "relevance": 0.6, "context": "general", "similarity": 0.5}],
                "readability": 60
            },
            "keyword_recommendations": {
                "keywords": [{"keyword": "improvement", "relevance": 0.7, "context": "general", "similarity": 0.6}],
                "weak_sections": [],
                "scores": {"overall": 70, "readability": 65, "relevance": 75, "engagement": 70, "seo": 65}
            },
            "content_scoring": {
                "overall_score": 70,
                "breakdown": {
                    "keyword_relevance": 70,
                    "readability": 75,
                    "user_alignment": 65,
                    "structure": 70,
                    "seo": 60,
                    "engagement": 75
                },
                "recommendations": ["Consider adding more specific keywords", "Improve content structure"]
            }
        }
        return fallbacks.get(schema_key, {})
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for LLM service"""
        try:
            if not self.model:
                return {"status": "unhealthy", "reason": "Model not initialized"}
         
            test_response, _ = await self.generate_structured_response(
                "Test prompt for health check", "content_scoring"
            )
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "total_tokens_used": self.total_tokens_used,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "model_name": self.model_name,
            "estimated_cost": self.total_tokens_used / 1000000 * 0.25  
        }