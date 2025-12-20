"""APScheduler-based task scheduler for periodic data refresh."""

import logging
from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services.cache import cache, CacheKeys

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Scheduler service for managing periodic tasks.
    
    Uses APScheduler to run data refresh jobs at configurable intervals.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.settings = get_settings()
        self._started = False
    
    def start(self):
        """Start the scheduler and register default jobs."""
        if self._started:
            logger.warning("Scheduler already started")
            return
        
        # Register default refresh jobs
        self._register_default_jobs()
        
        # Start scheduler
        self.scheduler.start()
        self._started = True
        logger.info("Scheduler started with default jobs")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            logger.info("Scheduler shutdown")
    
    def _register_default_jobs(self):
        """Register default data refresh jobs."""
        
        # Scolarité: refresh every hour
        self.scheduler.add_job(
            refresh_scolarite_cache,
            IntervalTrigger(hours=1),
            id="refresh_scolarite",
            name="Refresh Scolarité Data",
            replace_existing=True,
        )
        
        # Recrutement: refresh daily at 2 AM
        self.scheduler.add_job(
            refresh_recrutement_cache,
            CronTrigger(hour=2, minute=0),
            id="refresh_recrutement",
            name="Refresh Recrutement Data",
            replace_existing=True,
        )
        
        # Budget: refresh daily at 3 AM
        self.scheduler.add_job(
            refresh_budget_cache,
            CronTrigger(hour=3, minute=0),
            id="refresh_budget",
            name="Refresh Budget Data",
            replace_existing=True,
        )
        
        # EDT: refresh every hour
        self.scheduler.add_job(
            refresh_edt_cache,
            IntervalTrigger(hours=1),
            id="refresh_edt",
            name="Refresh EDT Data",
            replace_existing=True,
        )
        
        logger.info("Registered 4 default refresh jobs")
    
    def add_job(
        self,
        func: Callable,
        trigger: str = "interval",
        **trigger_args
    ) -> str:
        """
        Add a custom job to the scheduler.
        
        Args:
            func: The function to run
            trigger: 'interval' or 'cron'
            **trigger_args: Arguments for the trigger
            
        Returns:
            Job ID
        """
        if trigger == "interval":
            trigger_obj = IntervalTrigger(**trigger_args)
        elif trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")
        
        job = self.scheduler.add_job(func, trigger_obj)
        logger.info(f"Added job {job.id}")
        return job.id
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler."""
        self.scheduler.remove_job(job_id)
        logger.info(f"Removed job {job_id}")
    
    def get_jobs(self) -> list[dict]:
        """Get list of scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        return jobs
    
    async def run_job_now(self, job_id: str):
        """Manually trigger a job immediately."""
        job = self.scheduler.get_job(job_id)
        if job:
            await job.func()
            logger.info(f"Manually ran job {job_id}")
        else:
            logger.warning(f"Job {job_id} not found")


# Refresh functions
async def refresh_scolarite_cache():
    """Refresh scolarité data in cache."""
    logger.info("Starting scolarité cache refresh")
    try:
        settings = get_settings()
        # Import here to avoid circular imports
        from app.adapters.scodoc import ScoDocAdapter
        
        adapter = ScoDocAdapter(
            base_url=settings.scodoc_base_url,
            username=settings.scodoc_username,
            password=settings.scodoc_password,
            department=settings.scodoc_department
        )
        
        # Fetch fresh data
        indicators = await adapter.get_data()
        etudiants = await adapter.get_etudiants()
        
        # Store in cache with TTL
        ttl = settings.cache_ttl_scolarite
        
        await cache.set(CacheKeys.scolarite_indicators(None, settings.scodoc_department), indicators, ttl)
        
        # Store refresh timestamp
        await cache.set_raw(
            CacheKeys.last_refresh("scolarite"),
            {"timestamp": datetime.now().isoformat()},
            ttl=None  # No expiry for timestamp
        )
        
        logger.info("Scolarité cache refresh completed")
    except Exception as e:
        logger.error(f"Scolarité cache refresh failed: {e}")


async def refresh_recrutement_cache():
    """Refresh recrutement data in cache."""
    logger.info("Starting recrutement cache refresh")
    try:
        from app.adapters.parcoursup import ParcoursupAdapter
        
        adapter = ParcoursupAdapter()
        
        # Fetch fresh data (will yield mock if no file, or empty indicators if real)
        # For a better implementation, this should fetch from DB if needed
        indicators = await adapter.get_data()
        
        # Store in cache with TTL
        settings = get_settings()
        ttl = settings.cache_ttl_recrutement
        
        await cache.set(CacheKeys.recrutement_indicators(None, "RT"), indicators, ttl)
        
        # Store refresh timestamp
        await cache.set_raw(
            CacheKeys.last_refresh("recrutement"),
            {"timestamp": datetime.now().isoformat()},
            ttl=None
        )
        
        logger.info("Recrutement cache refresh completed")
    except Exception as e:
        logger.error(f"Recrutement cache refresh failed: {e}")


async def refresh_budget_cache():
    """Refresh budget data in cache."""
    logger.info("Starting budget cache refresh")
    try:
        from app.adapters.excel import ExcelAdapter
        
        adapter = ExcelAdapter()
        
        # Fetch fresh data
        indicators = await adapter.get_data()
        
        # Store in cache with TTL
        settings = get_settings()
        ttl = settings.cache_ttl_budget
        
        await cache.set(CacheKeys.budget_indicators(None, "RT"), indicators, ttl)
        
        # Store refresh timestamp
        await cache.set_raw(
            CacheKeys.last_refresh("budget"),
            {"timestamp": datetime.now().isoformat()},
            ttl=None
        )
        
        logger.info("Budget cache refresh completed")
    except Exception as e:
        logger.error(f"Budget cache refresh failed: {e}")


async def refresh_edt_cache():
    """Refresh EDT data in cache."""
    logger.info("Starting EDT cache refresh")
    try:
        from app.adapters.scodoc import ScoDocAdapter
        settings = get_settings()
        
        adapter = ScoDocAdapter(
            base_url=settings.scodoc_base_url,
            username=settings.scodoc_username,
            password=settings.scodoc_password,
            department=settings.scodoc_department
        )
        
        # Fetch fresh data
        # Note: EDT indicators currently might not be fully implemented in adapter.get_data()
        # but this at least calls the existing base method.
        try:
            indicators = await adapter.get_data()
            
            # Store in cache with TTL
            ttl = settings.cache_ttl_edt
            
            await cache.set(CacheKeys.edt_indicators(settings.scodoc_department), indicators, ttl)
        except Exception as e:
            logger.warning(f"EDT indicators not available through adapter.get_data(): {e}")
        
        # Store refresh timestamp
        await cache.set_raw(
            CacheKeys.last_refresh("edt"),
            {"timestamp": datetime.now().isoformat()},
            ttl=None
        )
        
        logger.info("EDT cache refresh completed")
    except Exception as e:
        logger.error(f"EDT cache refresh failed: {e}")


# Global scheduler instance
scheduler = SchedulerService()
