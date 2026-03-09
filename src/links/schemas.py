from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(None, description="Custom alias (optional)")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (optional)")

class LinkResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True