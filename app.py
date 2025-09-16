#!/usr/bin/env python3
import os
import time
import signal
import logging
from typing import Optional, Tuple

from dotenv import load_dotenv
from sqlmodel import Session, select, create_engine

from breba_social.agents import data_agent, view_agent
# Import your SQLModel model
from breba_social.models import Post  # assumes models.py defines class Post(SQLModel, table=True)

# -------------------------
# Config
# -------------------------
load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./feed.db")
POLL_INTERVAL_SEC = float(os.getenv("POLL_INTERVAL_SEC", "10.0"))
BATCH_LIMIT = int(os.getenv("BATCH_LIMIT", "200"))

# Create engine (sqlite needs check_same_thread=False)
engine = create_engine(
    DB_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("poller")

def filter_data(posts: list[Post]) -> None:
    filtered_posts = []
    for post in posts:
        if data_agent.filter_post(post):
            filtered_posts.append(post)

    if filtered_posts:
        view_agent.add_new_posts(filtered_posts)



# -------------------------
# Polling helpers
# -------------------------
def get_start_cursor(session: Session) -> Tuple[Optional[int], Optional[int]]:
    """
    Returns (last_time_us, last_id) to begin polling after.
    Starts at the current maximum so we only process *new* rows from now on.
    """
    # Get row with max time_us and highest id among those (stable tie-breaker)
    row = session.exec(
        select(Post).order_by(Post.time_us.desc(), Post.id.desc()).limit(1)
    ).first()

    if row is None:
        return None, None

    return row.time_us, row.id


def fetch_new_posts(
    session: Session, last_time_us: Optional[int], last_id: Optional[int]
) -> list[Post]:
    """
    Fetch posts strictly newer than the cursor, using (time_us, id) ordering.

    WHERE (time_us > last_time_us) OR (time_us = last_time_us AND id > last_id)
    If cursor is None (no prior rows), we just fetch nothing initially to avoid
    processing historical data; new inserts will appear on next polls.
    """
    if last_time_us is None:
        return []

    q = (
        select(Post)
        .where(
            (Post.time_us > last_time_us)
            | ((Post.time_us == last_time_us) & (Post.id > (last_id or 0)))
        )
        .order_by(Post.time_us.asc(), Post.id.asc())
        .limit(BATCH_LIMIT)
    )
    return list(session.exec(q))


# -------------------------
# Main loop
# -------------------------
_shutdown = False


def _handle_sig(signum, frame):
    global _shutdown
    _shutdown = True
    log.info("Received signal %s; shutting down...", signum)


def main():
    global _shutdown

    # Graceful shutdown on Ctrl+C / SIGTERM
    signal.signal(signal.SIGINT, _handle_sig)
    signal.signal(signal.SIGTERM, _handle_sig)

    log.info("Connecting to DB: %s", DB_URL)
    with Session(engine) as session:
        # last_time_us, last_id = get_start_cursor(session)

        # This should get all the posts from db
        last_time_us = 0
        last_id = 0
        log.info("Starting cursor: time_us=%s id=%s", last_time_us, last_id)

        backoff = 1.0
        while not _shutdown:
            try:
                new_posts = fetch_new_posts(session, last_time_us, last_id)

                if new_posts:
                    filter_data(new_posts)
                    for p in new_posts:
                        # Advance cursor for every processed row
                        last_time_us = p.time_us
                        last_id = p.id

                    log.info("Processed %d new post(s).", len(new_posts))
                    # Reset backoff on success
                    backoff = 1.0
                else:
                    # Nothing new; sleep the normal poll interval
                    time.sleep(POLL_INTERVAL_SEC)
                    continue

            except Exception as e:
                log.exception("Polling error: %s", e)
                # brief exponential backoff on errors
                time.sleep(min(backoff, 30.0))
                backoff = min(backoff * 2, 30.0)

    log.info("Exited cleanly.")


if __name__ == "__main__":
    main()
