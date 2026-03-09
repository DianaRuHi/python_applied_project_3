from celery import Celery
from sqlalchemy import select, delete
from datetime import datetime, timedelta
import asyncio
import os

from config import REDIS_URL
from database import async_session_maker
from links.models import Link

celery = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.tasks"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    beat_schedule={
        "delete-expired-links-every-hour": {
            "task": "tasks.tasks.delete_expired_links",
            "schedule": timedelta(hours=1),
        },
        "cleanup-unused-links-daily": {
            "task": "tasks.tasks.cleanup_unused_links",
            "schedule": timedelta(hours=24),
            "args": (30,)
        }
    }
)

@celery.task
def delete_expired_links():
    print(f"[{datetime.now()}] Running expired links cleanup")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_delete_expired_links_async())
    loop.close()
    
    print(f"[{datetime.now()}] Deleted {result} expired links")
    return result

async def _delete_expired_links_async():
    from links.models import Link
    from database import async_session_maker
    from datetime import datetime
    
    async with async_session_maker() as session:
        query = select(Link).where(Link.expires_at < datetime.now())
        result = await session.execute(query)
        expired_links = result.scalars().all()
        
        count = len(expired_links)
        
        for link in expired_links:
            await session.delete(link)
        
        await session.commit()
        return count

@celery.task
def cleanup_unused_links(days: int = 30):
    print(f"[{datetime.now()}] Cleaning unused links older than {days} days")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_cleanup_unused_links_async(days))
    loop.close()
    
    print(f"[{datetime.now()}] Deleted {result} unused links")
    return result

async def _cleanup_unused_links_async(days: int):
    from links.models import Link
    from database import async_session_maker

    threshold_date = datetime.now() - timedelta(days=days)
    
    async with async_session_maker() as session:
        query = select(Link).where(
            (Link.last_accessed_at < threshold_date) | 
            ((Link.last_accessed_at.is_(None)) & (Link.created_at < threshold_date))
        )
        result = await session.execute(query)
        unused_links = result.scalars().all()
        
        count = len(unused_links)
        
        for link in unused_links:
            print(f"Deleting unused link: {link.short_code} - last accessed: {link.last_accessed_at}")
            await session.delete(link)
        
        await session.commit()
        return count

