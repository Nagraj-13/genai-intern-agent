import os
import jwt
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

async def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token or API key
    
    Supports both:
    1. JWT tokens for user authentication
    2. API keys for service-to-service communication
    """
    try:
        # Check if it's an API key first
        api_key = os.getenv("API_KEY", "MOCK_API_KEY")
        if token == api_key:
            return {
                "valid": True,
                "type": "api_key",
                "user_id": "api_user",
                "permissions": ["read", "write", "analyze"]
            }
        
        # Try JWT token verification
        jwt_secret = os.getenv("JWT_SECRET", "your-jwt-secret-here")
        
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            
           
            if payload.get("exp") and datetime.utcnow().timestamp() > payload["exp"]:
                raise AuthenticationError("Token has expired")
            
            return {
                "valid": True,
                "type": "jwt",
                "user_id": payload.get("user_id", "unknown"),
                "permissions": payload.get("permissions", ["read"]),
                "payload": payload
            }
            
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid JWT token: {str(e)}")
    
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationError("Authentication failed")

def generate_jwt_token(user_id: str, permissions: list = None, expires_in_hours: int = 24) -> str:
    """Generate a JWT token for testing purposes"""
    if permissions is None:
        permissions = ["read", "write"]
    
    jwt_secret = os.getenv("JWT_SECRET", "your-jwt-secret-here")
    
    payload = {
        "user_id": user_id,
        "permissions": permissions,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours)
    }
    
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return token

def create_test_api_key() -> str:
    """Create a test API key for development"""
    return os.getenv("API_KEY", "test-api-key-12345")

def setup_auth_environment():
    """Setup authentication environment variables if not present"""
    if not os.getenv("API_KEY"):
        os.environ["API_KEY"] = "dev-api-key-genai-blog-system"
        logger.info("Set development API key")
    
    if not os.getenv("JWT_SECRET"):
        os.environ["JWT_SECRET"] = "dev-jwt-secret-blog-agent-system"
        logger.info("Set development JWT secret")

setup_auth_environment()