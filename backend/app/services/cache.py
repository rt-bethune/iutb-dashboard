"""Redis cache service for data caching."""

import json
import logging
from typing import Any, Optional, TypeVar, Type
from datetime import datetime

import redis.asyncio as redis
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class CacheService:
    """
    Redis-based cache service.
    
    Provides async methods for caching Pydantic models with TTL support.
    Falls back gracefully when Redis is unavailable.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis."""
        if not self.settings.cache_enabled:
            logger.info("Cache disabled in settings")
            return False
        
        try:
            self._client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.settings.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected and self._client is not None
    
    async def get(self, key: str, model_class: Type[T]) -> Optional[T]:
        """
        Get a cached value and deserialize to Pydantic model.
        
        Args:
            key: Cache key
            model_class: Pydantic model class for deserialization
            
        Returns:
            Deserialized model or None if not found/error
        """
        if not self.is_connected:
            return None
        
        try:
            data = await self._client.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return model_class.model_validate_json(data)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def get_raw(self, key: str) -> Optional[dict]:
        """Get raw JSON data from cache."""
        if not self.is_connected:
            return None
        
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get_raw error for {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: BaseModel, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a Pydantic model.
        
        Args:
            key: Cache key
            value: Pydantic model to cache
            ttl: Time-to-live in seconds (None = no expiry)
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            return False
        
        try:
            data = value.model_dump_json()
            if ttl:
                await self._client.setex(key, ttl, data)
            else:
                await self._client.set(key, data)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def set_raw(
        self, 
        key: str, 
        value: dict, 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache raw dictionary data."""
        if not self.is_connected:
            return False
        
        try:
            data = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, data)
            else:
                await self._client.set(key, data)
            return True
        except Exception as e:
            logger.error(f"Cache set_raw error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        if not self.is_connected:
            return False
        
        try:
            await self._client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.is_connected:
            return 0
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self._client.delete(*keys)
                logger.info(f"Cache DELETE pattern '{pattern}': {deleted} keys")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.is_connected:
            return {"connected": False}
        
        try:
            info = await self._client.info("stats")
            memory = await self._client.info("memory")
            keys = await self._client.dbsize()
            
            return {
                "connected": True,
                "keys": keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used": memory.get("used_memory_human", "N/A"),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}


# Cache key builders
class CacheKeys:
    """Cache key constants and builders."""
    
    # Prefixes
    SCOLARITE = "scolarite"
    RECRUTEMENT = "recrutement"
    BUDGET = "budget"
    EDT = "edt"
    
    @staticmethod
    def scolarite_indicators(annee: Optional[str] = None, department: Optional[str] = None) -> str:
        dept = department or "default"
        if annee:
            return f"scolarite:{dept}:indicators:{annee}"
        return f"scolarite:{dept}:indicators:current"
    
    @staticmethod
    def scolarite_etudiants(formation: Optional[str] = None, semestre: Optional[str] = None, department: Optional[str] = None) -> str:
        dept = department or "default"
        return f"scolarite:{dept}:etudiants:{formation or 'all'}:{semestre or 'all'}"
    
    @staticmethod
    def recrutement_indicators(annee: Optional[int] = None, department: Optional[str] = None) -> str:
        dept = department or "default"
        if annee:
            return f"recrutement:{dept}:indicators:{annee}"
        return f"recrutement:{dept}:indicators:current"
    
    @staticmethod
    def budget_indicators(annee: Optional[int] = None, department: Optional[str] = None) -> str:
        dept = department or "default"
        if annee:
            return f"budget:{dept}:indicators:{annee}"
        return f"budget:{dept}:indicators:current"
    
    @staticmethod
    def edt_indicators(annee: Optional[str] = None, department: Optional[str] = None) -> str:
        dept = department or "default"
        if annee:
            return f"edt:{dept}:indicators:{annee}"
        return f"edt:{dept}:indicators:current"
    
    @staticmethod
    def last_refresh(domain: str, department: Optional[str] = None) -> str:
        dept = department or "default"
        return f"{domain}:{dept}:last_refresh"


# Global cache instance
cache = CacheService()
