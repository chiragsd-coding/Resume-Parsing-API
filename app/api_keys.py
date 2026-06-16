"""API Key management - generation, validation, rate limiting."""
import hashlib
import secrets
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status, Request

class ApiKeyManager:
    """Manages API key generation and validation."""
    
    PREFIX = "ats_"
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate API key and its hash."""
        raw_key = ApiKeyManager.PREFIX + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, key_hash
    
    @staticmethod
    def hash_api_key(key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    def extract_key_from_header(auth_header: str) -> str:
        """Extract API key from Authorization header."""
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        return auth_header[7:]

class RateLimiter:
    """Token bucket rate limiting."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(self, 
                               key_id: str, 
                               calls_limit: int, 
                               period_seconds: int) -> bool:
        """Check if request is within rate limit."""
        bucket_key = f"ratelimit:{key_id}"
        
        current = await self.redis.incr(bucket_key)
        if current == 1:
            await self.redis.expire(bucket_key, period_seconds)
        
        return current <= calls_limit
    
    async def get_remaining_calls(self, 
                                  key_id: str,
                                  calls_limit: int) -> int:
        """Get remaining calls in current period."""
        bucket_key = f"ratelimit:{key_id}"
        current = await self.redis.get(bucket_key)
        return max(0, calls_limit - (int(current or 0)))

async def verify_api_key(request: Request, redis_client):
    """Verify API key from request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    
    try:
        key = ApiKeyManager.extract_key_from_header(auth_header)
        key_hash = ApiKeyManager.hash_api_key(key)
        
        # Would check database for key_hash
        # For now, mock validation
        return {"api_key_id": "mock_id", "tenant_id": "tenant_123"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
