"""Redis cache service for data caching."""

import json
import logging
import re
import unicodedata
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
    
    async def get_list(self, key: str, model_class: Type[T]) -> Optional[list[T]]:
        """
        Get a cached list of Pydantic models.
        
        Args:
            key: Cache key
            model_class: Pydantic model class for deserialization
            
        Returns:
            List of deserialized models or None if not found/error
        """
        if not self.is_connected:
            return None
        
        try:
            data = await self._client.get(key)
            if data:
                logger.debug(f"Cache HIT (list): {key}")
                items = json.loads(data)
                return [model_class.model_validate(item) for item in items]
            logger.debug(f"Cache MISS (list): {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get_list error for {key}: {e}")
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
    
    async def set_list(
        self, 
        key: str, 
        value: list[BaseModel], 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a list of Pydantic models.
        
        Args:
            key: Cache key
            value: List of Pydantic models to cache
            ttl: Time-to-live in seconds (None = no expiry)
            
        Returns:
            True if successful
        """
        if not self.is_connected:
            return False
        
        try:
            data = json.dumps([item.model_dump() for item in value])
            if ttl:
                await self._client.setex(key, ttl, data)
            else:
                await self._client.set(key, data)
            logger.debug(f"Cache SET (list): {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set_list error for {key}: {e}")
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
    ALERTES = "alertes"
    INDICATEURS = "indicateurs"
    
    # TTL values (seconds)
    TTL_SHORT = 300      # 5 minutes
    TTL_MEDIUM = 1800    # 30 minutes
    TTL_LONG = 3600      # 1 hour
    TTL_STUDENT = 600    # 10 minutes for individual student data

    @staticmethod
    def _key_part(value: Optional[str]) -> str:
        if value is None:
            return "all"
        value = str(value).strip()
        if not value:
            return "all"
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
        return normalized or "all"
    
    @staticmethod
    def alertes_list(
        department: str,
        semestre: Optional[str] = None,
        *,
        niveau: Optional[str] = None,
        type_alerte: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"alertes:{department}:list:{sem}"
        if any([niveau, type_alerte, formation, modalite]):
            n = CacheKeys._key_part(niveau)
            t = CacheKeys._key_part(type_alerte)
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{n}:{t}:{f}:{m}"
        return base
    
    @staticmethod
    def alertes_stats(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"alertes:{department}:stats:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def fiche_etudiant(department: str, etudiant_id: str) -> str:
        return f"alertes:{department}:fiche:{etudiant_id}"
    
    @staticmethod
    def indicateurs_tableau_bord(
        department: str,
        annee: Optional[str] = None,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        a = annee or "current"
        s = semestre or "all"
        base = f"indicateurs:{department}:tableau_bord:{a}:{s}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_statistiques(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:statistiques:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_taux_validation(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:taux_validation:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_mentions(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:mentions:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_modules(
        department: str,
        semestre: Optional[str] = None,
        tri: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        sort_by = tri or "taux_echec"
        base = f"indicateurs:{department}:modules:{sem}:{sort_by}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_absenteisme(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:absenteisme:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_comparaison(department: str, nb_annees: int = 5) -> str:
        return f"indicateurs:{department}:comparaison:{nb_annees}"
    
    @staticmethod
    def indicateurs_type_bac(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:type_bac:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_boursiers(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:boursiers:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
    @staticmethod
    def indicateurs_predictifs(
        department: str,
        semestre: Optional[str] = None,
        *,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> str:
        sem = semestre or "all"
        base = f"indicateurs:{department}:predictifs:{sem}"
        if any([formation, modalite]):
            f = CacheKeys._key_part(formation)
            m = CacheKeys._key_part(modalite)
            return f"{base}:{f}:{m}"
        return base
    
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
