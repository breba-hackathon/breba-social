import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, select, create_engine

from models import Post

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./feed.db")

engine = create_engine(DB_URL, echo=False,
                       connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})


def init_db():
    SQLModel.metadata.create_all(engine)


# =========================
# FastAPI app + XRPC endpoint
# =========================
app = FastAPI(title="Bluesky Feed Generator (No-Registry)")

stop_event: asyncio.Event | None = None


# --- XRPC shape helpers ---
class FeedItem(BaseModel):
    post: str  # at://.../app.bsky.feed.post/<rkey>


class FeedSkeletonResponse(BaseModel):
    cursor: Optional[str] = None
    feed: List[FeedItem]


# Minimal feed: reverse-chronological from our DB.
# XRPC path per spec:
# GET /xrpc/app.bsky.feed.getFeedSkeleton?feed=<your-feed-uri>&limit=...&cursor=...
@app.get("/xrpc/app.bsky.feed.getFeedSkeleton", response_model=FeedSkeletonResponse)
def get_feed_skeleton(
        feed: str = Query(..., description="Your feed URI (ignored by this minimal generator)"),
        limit: int = Query(50, ge=1, le=100),
        cursor: Optional[str] = Query(None, description="Opaque cursor; here we use time_us"),
):
    try:
        with Session(engine) as s:
            q = select(Post).where(Post.collection == "app.bsky.feed.post")

            # paginate by time_us (strictly less than cursor)
            if cursor:
                try:
                    cursor_us = int(cursor)
                    q = q.where(Post.time_us < cursor_us)
                except ValueError:
                    pass

            q = q.order_by(Post.time_us.desc()).limit(limit)
            posts = list(s.exec(q))

            if not posts:
                return FeedSkeletonResponse(cursor=None, feed=[])

            next_cursor = str(posts[-1].time_us)  # oldest item in the page
            items = [FeedItem(post=p.uri) for p in posts]
            return FeedSkeletonResponse(cursor=next_cursor, feed=items)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


class PostFullOut(BaseModel):
    id: int
    uri: str
    cid: str
    did: str
    collection: str
    rkey: str
    time_us: int
    created_at: datetime
    langs: Optional[List[str]] = None
    text: Optional[str] = None
    reply_root_uri: Optional[str] = None
    reply_parent_uri: Optional[str] = None
    record: Dict[str, Any]
    raw: Optional[Dict[str, Any]] = None  # gated by include_raw


class PostsResponse(BaseModel):
    cursor: Optional[str] = None  # next page cursor (time_us of last item)
    items: List[PostFullOut]


@app.get("/posts", response_model=PostsResponse)
def list_posts(
        limit: int = Query(50, ge=1, le=200),
        cursor: Optional[int] = Query(None, description="Paginate: return items with time_us < cursor"),
        did: Optional[str] = Query(None, description="Filter by DID"),
        contains: Optional[str] = Query(None, description="Case-insensitive substring match on text"),
        include_raw: bool = Query(False, description="Include full Jetstream envelope in response"),
):
    try:
        with Session(engine) as s:
            q = select(Post).where(Post.collection == "app.bsky.feed.post")

            if did:
                q = q.where(Post.did == did)

            if cursor is not None:
                q = q.where(Post.time_us < int(cursor))

            # quick-and-dirty text filtering; for large datasets switch to FTS
            if contains:
                q = q.where(Post.text.ilike(f"%{contains}%"))

            q = q.order_by(Post.time_us.desc()).limit(limit)
            rows = list(s.exec(q))

            if not rows:
                return PostsResponse(cursor=None, items=[])

            next_cursor = str(rows[-1].time_us)

            items: List[PostFullOut] = []
            for r in rows:
                try:
                    langs = json.loads(r.langs_json) if r.langs_json else None
                except Exception:
                    langs = None
                try:
                    record = json.loads(r.record_json) if r.record_json else {}
                except Exception:
                    record = {}
                raw = None
                if include_raw:
                    try:
                        raw = json.loads(r.raw_json) if r.raw_json else {}
                    except Exception:
                        raw = {}

                items.append(PostFullOut(
                    id=r.id,
                    uri=r.uri,
                    cid=r.cid,
                    did=r.did,
                    collection=r.collection,
                    rkey=r.rkey,
                    time_us=r.time_us,
                    created_at=r.created_at,
                    langs=langs,
                    text=r.text,
                    reply_root_uri=r.reply_root_uri,
                    reply_parent_uri=r.reply_parent_uri,
                    record=record,
                    raw=raw,
                ))

            return PostsResponse(cursor=next_cursor, items=items)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
def health():
    return {
        "ok": True,
        "db": DB_URL,
    }


@app.get("/stats")
def stats():
    with Session(engine) as s:
        total = s.exec(select(Post.id)).all()
        last = s.exec(select(Post).order_by(Post.time_us.desc()).limit(1)).first()
    return {
        "count": len(total),
        "latest_time_us": getattr(last, "time_us", None),
        "latest_uri": getattr(last, "uri", None),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
