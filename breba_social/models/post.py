from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


# =========================
# DB models
# =========================
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uri: str = Field(index=True, unique=True)  # at://did:plc:.../app.bsky.feed.post/<rkey>
    cid: str = Field(index=True)
    did: str = Field(index=True)
    collection: str = Field(index=True)
    rkey: str
    time_us: int = Field(index=True)
    created_at: datetime = Field(index=True)
    langs_json: Optional[str] = None  # store as JSON string
    text: Optional[str] = None  # convenience
    reply_root_uri: Optional[str] = Field(default=None, index=True)
    reply_parent_uri: Optional[str] = Field(default=None, index=True)
    record_json: str  # full record as JSON string
    raw_json: str  # full Jetstream envelope as JSON string