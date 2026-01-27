
import redis.asyncio as redis
from typing import Optional, Any, Callable
from functools import wraps
import json
import hashlib
from app.core.config import settings
from loguru import logger
from fastapi import Request, Response

class CacheService:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.ttl = 60 # Default TTL 60 seconds

    async def connect(self):
        if not self.redis:
            try:
                # Use REDIS_URL from settings
                url = settings.REDIS_URL or f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                self.redis = redis.from_url(url, encoding="utf-8", decode_responses=True)
                await self.redis.ping()
                logger.info("Connected to Redis Cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis = None

    async def close(self):
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        try:
            val = await self.redis.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 60):
        if not self.redis:
            return
        
        # Custom serializer for datetime objects
        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            from datetime import date, datetime
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            await self.redis.setex(key, ttl, json.dumps(value, default=json_serial))
        except Exception as e:
            logger.error(f"Cache SET error: {e}")

    # Decorator for FastAPI routes
    def cached(self, expire: int = 60):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Attempt to retrieve 'request' object from kwargs if present (for simple key gen)
                # This is a naive implementation; for prod, specialized libraries like fastapi-cache are better.
                # Here we construct a key based on function name and args.
                
                # Check connection
                if not self.redis:
                     await self.connect()
                
                # We skip 'db' session args or 'current_user' if we want global cache
                # But typically dashboard stats are USER specific or GLOBAL?
                # The dashboard stats in dashboard.py has a 'is_universal_access' logic.
                # So cache key MUST include user_id or role if output varies by user.
                
                # Strategy: Let's assume dashboard-stats is cached "Per User ID" or "Per Role"
                # We'll extract kwargs to build key.
                
                key_parts = [func.__name__]
                
                # Helper to extract relevant args 
                for k, v in kwargs.items():
                    if k in ['db', 'request', 'response']: continue
                    # For current_user, use specific ID
                    if k == 'current_user':
                        key_parts.append(str(v.id))
                    else:
                        key_parts.append(str(v))
                        
                key_str = ":".join(key_parts)
                cache_key = f"cache:{hashlib.md5(key_str.encode()).hexdigest()}"
                
                cached_val = await self.get(cache_key)
                if cached_val:
                    logger.debug(f"Cache HIT for {cache_key}")
                    return cached_val
                
                result = await func(*args, **kwargs)
                
                await self.set(cache_key, result, expire)
                return result
            return wrapper
        return decorator

# Singleton
cache_service = CacheService()
