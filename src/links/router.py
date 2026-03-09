import random
import string
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from fastapi_cache.decorator import cache
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timezone
from auth.db import User
from sqlalchemy import select, and_
from database import async_session_maker
from links.schemas import LinkCreate, LinkResponse
from depends import optional_current_user, current_active_user
from links.models import Link
from fastapi_cache import FastAPICache

router = APIRouter(prefix="/links", tags=["links"])

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@router.post("/shorten", response_model=LinkResponse)
async def create_short_link(
    link_data: LinkCreate,
    user: Optional[User] = Depends(optional_current_user)
):
    
    if link_data.custom_alias:
        short_code = link_data.custom_alias

        async with async_session_maker() as session:
            query = select(Link).where(Link.short_code == short_code)
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom alias already exists"
                )
    else:
        short_code = generate_short_code()
    
    new_link = Link(
        original_url=str(link_data.original_url),
        short_code=short_code,
        user_id=user.id if user else None,
        expires_at=link_data.expires_at 
    )
    
    async with async_session_maker() as session:
        session.add(new_link)
        await session.commit()
        await session.refresh(new_link)
    
    return LinkResponse(
        short_code=new_link.short_code,
        original_url=new_link.original_url,
        created_at=new_link.created_at,
        expires_at=new_link.expires_at
    )



@router.get("/search")
#@cache(expire=60)
async def search_links(original_url: str):
    
    async with async_session_maker() as session:
        query = select(Link).where(Link.original_url.contains(original_url))
        result = await session.execute(query)
        links = result.scalars().all()


        return [
            {
                "short_code": link.short_code,
                "original_url": link.original_url,
                "created_at": link.created_at,
                "access_count": link.access_count
            }
            for link in links
        ]




@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    user: User = Depends(current_active_user)
):

    async with async_session_maker() as session:
        query = select(Link).where(Link.short_code == short_code)
        result = await session.execute(query)
        link = result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )
        
        if link.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own links"
            )
        
        await session.delete(link)
        await session.commit()
    await FastAPICache.clear(namespace="fastapi-cache")

    return None 



@router.put("/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    link_data: LinkCreate,
    user: User = Depends(current_active_user)
):
    async with async_session_maker() as session:
        query = select(Link).where(Link.short_code == short_code)
        result = await session.execute(query)
        link = result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )
        
        if link.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own links"
            )
        
        link.original_url = str(link_data.original_url)
        await session.commit()
        await session.refresh(link)

    await FastAPICache.clear(namespace="fastapi-cache")
    
    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        expires_at=link.expires_at
    )



@router.get("/{short_code}")
#@cache(expire=300)
async def redirect_to_original(short_code: str):
    async with async_session_maker() as session:
        query = select(Link).where(Link.short_code == short_code)
        result = await session.execute(query)
        link = result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )

        if link.expires_at and link.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This link has expired"
            )
        
        link.access_count += 1
        link.last_accessed_at = func.now()
        await session.commit()
    
    return RedirectResponse(url=link.original_url, status_code=307)



@router.get("/{short_code}/stats")
#@cache(expire=30)
async def get_link_stats(short_code: str):
    async with async_session_maker() as session:
        query = select(Link).where(Link.short_code == short_code)
        result = await session.execute(query)
        link = result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )
        
        return {
            "original_url": link.original_url,
            "short_code": link.short_code,
            "created_at": link.created_at,
            "access_count": link.access_count,
            "last_accessed_at": link.last_accessed_at,
            "expires_at": link.expires_at
        }


@router.get("/expired")
async def get_expired_links():
    async with async_session_maker() as session:
        current_time = datetime.now(timezone.utc)
        
        query = select(Link).where(
            and_(
                Link.expires_at.is_not(None),
                Link.expires_at < current_time
            )
        ).order_by(Link.expires_at.desc())
        
        result = await session.execute(query)
        expired_links = result.scalars().all()
        
        return [
            {
                "short_code": link.short_code,
                "original_url": link.original_url,
                "created_at": link.created_at,
                "expires_at": link.expires_at,
                "access_count": link.access_count,
                "last_accessed_at": link.last_accessed_at,
                "user_id": link.user_id,
                "days_expired": (current_time - link.expires_at).days
            }
            for link in expired_links
        ]



@router.get("/{short_code}/expired")
async def check_link_expired(short_code: str):
    async with async_session_maker() as session:
        query = select(Link).where(Link.short_code == short_code)
        result = await session.execute(query)
        link = result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )
        
        if not link.expires_at:
            return {
                "short_code": link.short_code,
                "expired": False,
                "message": "This link never expires"
            }
        
        current_time = datetime.now(timezone.utc)
        expired = link.expires_at < current_time
        
        return {
            "short_code": link.short_code,
            "expired": expired,
            "expires_at": link.expires_at,
            "days_remaining": None if expired else (link.expires_at - current_time).days,
            "days_expired": (current_time - link.expires_at).days if expired else None
        }
