"""Advanced rate limiting with quota management."""
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import asyncio

class QuotaType(str, Enum):
    MONTHLY = "monthly"
    DAILY = "daily"
    HOURLY = "hourly"
    PER_MINUTE = "per_minute"

class QuotaManager:
    """Manages usage quotas per tenant."""
    
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
    
    async def check_quota(self, tenant_id: str, resource_type: str, 
                         quota_type: QuotaType) -> tuple[bool, dict]:
        """Check if tenant has remaining quota."""
        quota_key = f"quota:{tenant_id}:{resource_type}:{quota_type.value}"
        
        # Get quota limit from DB
        limit = await self._get_quota_limit(tenant_id, resource_type, quota_type)
        
        # Get current usage
        current = int(await self.redis.get(quota_key) or 0)
        
        if current >= limit:
            return False, {
                "limit": limit,
                "used": current,
                "remaining": 0
            }
        
        # Increment usage
        await self.redis.incr(quota_key)
        await self._set_expiry(quota_key, quota_type)
        
        return True, {
            "limit": limit,
            "used": current + 1,
            "remaining": limit - current - 1
        }
    
    async def _get_quota_limit(self, tenant_id: str, resource_type: str, 
                               quota_type: QuotaType) -> int:
        """Get quota limit for resource type."""
        # Would query database for actual limits
        limits = {
            "resume_parsing": {
                QuotaType.MONTHLY: 1000,
                QuotaType.DAILY: 100,
            },
            "api_calls": {
                QuotaType.HOURLY: 10000,
                QuotaType.PER_MINUTE: 100,
            }
        }
        return limits.get(resource_type, {}).get(quota_type, 1000)
    
    async def _set_expiry(self, key: str, quota_type: QuotaType):
        """Set key expiry based on quota type."""
        expiry = {
            QuotaType.MONTHLY: 30 * 24 * 3600,
            QuotaType.DAILY: 24 * 3600,
            QuotaType.HOURLY: 3600,
            QuotaType.PER_MINUTE: 60,
        }
        await self.redis.expire(key, expiry.get(quota_type, 3600))
    
    async def reset_monthly_quota(self, tenant_id: str):
        """Reset monthly quota for tenant."""
        pattern = f"quota:{tenant_id}:*:monthly"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

class ConcurrencyLimiter:
    """Limit concurrent operations."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def acquire(self, tenant_id: str, operation: str, max_concurrent: int = 10) -> bool:
        """Acquire concurrency slot."""
        key = f"concurrent:{tenant_id}:{operation}"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, 3600)
        
        if current > max_concurrent:
            await self.redis.decr(key)
            return False
        
        return True
    
    async def release(self, tenant_id: str, operation: str):
        """Release concurrency slot."""
        key = f"concurrent:{tenant_id}:{operation}"
        current = await self.redis.get(key)
        if current and int(current) > 0:
            await self.redis.decr(key)
