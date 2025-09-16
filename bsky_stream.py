import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import List

import websockets
from sqlmodel import SQLModel, Session, select, create_engine

from breba_social.models import Post

# =========================
# Config (env vars)
# =========================
JETSTREAM_BASE = os.getenv("JETSTREAM_BASE", "wss://jetstream2.us-west.bsky.network/subscribe")
WANTED_COLLECTIONS = os.getenv("WANTED_COLLECTIONS", "app.bsky.feed.post")
WANTED_DIDS = ["did:plc:4aqzua5vsewimmusg66fyajl", "did:plc:tkldabrcwdul4fnvj64npa3k", "did:plc:ad43h6gvrhxl2pmy4twdptak"]
# default: start 7 hours back in microseconds like your example
DEFAULT_CURSOR_US = int((time.time() - 2 * 3600) * 1_000_000)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./feed.db")

engine = create_engine(DB_URL, echo=False,
                       connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})


def init_db():
    SQLModel.metadata.create_all(engine)


# =========================
# Jetstream consumer
# =========================
def build_ws_uri(cursor_us: int) -> str:
    from urllib.parse import urlencode

    params: List[tuple[str, str]] = []
    # multiple collections supported via comma or multiple keys—use multiple keys:
    for col in [c.strip() for c in WANTED_COLLECTIONS.split(",") if c.strip()]:
        params.append(("wantedCollections", col))
    params.append(("cursor", str(cursor_us)))
    for did in WANTED_DIDS:
        params.append(("wantedDids", did.strip()))
    return f"{JETSTREAM_BASE}?{urlencode(params, doseq=True)}"


async def consume_jetstream():
    # reconnect loop with backoff
    backoff = 1
    cursor_us = DEFAULT_CURSOR_US
    while True:
        uri = build_ws_uri(cursor_us)
        try:
            async with websockets.connect(uri, max_size=16 * 1024 * 1024) as ws:
                # reset backoff on successful connect
                backoff = 1
                while True:
                    msg = await ws.recv()
                    print(f"Received message: {msg}")  # Log the received message (msg)
                    try:
                        data = json.loads(msg)
                    except Exception:
                        continue

                    # We only care about commit create events for app.bsky.feed.post
                    if data.get("kind") != "commit":
                        continue
                    commit = data.get("commit") or {}
                    if commit.get("operation") != "create":
                        continue
                    collection = commit.get("collection")
                    if collection != "app.bsky.feed.post":
                        continue

                    did = data.get("did")
                    rkey = commit.get("rkey")
                    cid = commit.get("cid")
                    time_us = int(data.get("time_us"))
                    record = commit.get("record") or {}
                    created_at_str = record.get("createdAt")
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).astimezone(
                            timezone.utc)
                    except Exception:
                        created_at = datetime.now(tz=timezone.utc)

                    uri_at = f"at://{did}/{collection}/{rkey}"

                    langs = record.get("langs") or []
                    reply = record.get("reply") or {}
                    reply_root_uri = (reply.get("root") or {}).get("uri")
                    reply_parent_uri = (reply.get("parent") or {}).get("uri")
                    text = record.get("text")

                    post = Post(
                        uri=uri_at,
                        cid=cid,
                        did=did,
                        collection=collection,
                        rkey=rkey,
                        time_us=time_us,
                        created_at=created_at,
                        langs_json=json.dumps(langs) if langs else None,
                        text=text,
                        reply_root_uri=reply_root_uri,
                        reply_parent_uri=reply_parent_uri,
                        record_json=json.dumps(record, ensure_ascii=False),
                        raw_json=json.dumps(data, ensure_ascii=False),
                    )
                    # insert if not exists
                    try:
                        with Session(engine) as s:
                            # ignore duplicates by checking unique uri
                            exists = s.exec(select(Post.id).where(Post.uri == post.uri)).first()
                            if not exists:
                                s.add(post)
                                s.commit()
                                # update resume cursor to last successful received message
                                cursor_us = time_us
                    except Exception as e:
                        # don't crash the stream on DB hiccups
                        print(f"DB error: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"websocket error: {e}")
            # exponential backoff (cap at 30s)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    asyncio.run(consume_jetstream())
