"""
Migration 002: Add provenance fields to agent_checkins
=======================================================
Adds:
  - observation_source    VARCHAR(50) DEFAULT 'agent_inferred'
  - observation_confidence FLOAT      DEFAULT 0.5
  - observation_text       TEXT       DEFAULT ''

Safe to run multiple times (uses IF NOT EXISTS / ignores duplicate column errors).
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import get_settings

settings = get_settings()

POSTGRES_MIGRATIONS = [
    """
    ALTER TABLE agent_checkins
    ADD COLUMN IF NOT EXISTS observation_source VARCHAR(50) NOT NULL DEFAULT 'agent_inferred'
    """,
    """
    ALTER TABLE agent_checkins
    ADD COLUMN IF NOT EXISTS observation_confidence FLOAT NOT NULL DEFAULT 0.5
    """,
    """
    ALTER TABLE agent_checkins
    ADD COLUMN IF NOT EXISTS observation_text TEXT NOT NULL DEFAULT ''
    """,
    # Index for faster memory queries by source
    """
    CREATE INDEX IF NOT EXISTS idx_checkins_source
    ON agent_checkins (observation_source)
    """,
    # Index for text search (basic)
    """
    CREATE INDEX IF NOT EXISTS idx_checkins_obs_text
    ON agent_checkins USING gin(to_tsvector('english', observation_text))
    """,
]

SQLITE_MIGRATIONS = [
    "ALTER TABLE agent_checkins ADD COLUMN observation_source VARCHAR(50) NOT NULL DEFAULT 'agent_inferred'",
    "ALTER TABLE agent_checkins ADD COLUMN observation_confidence FLOAT NOT NULL DEFAULT 0.5",
    "ALTER TABLE agent_checkins ADD COLUMN observation_text TEXT NOT NULL DEFAULT ''",
]


async def run_migration():
    engine = create_async_engine(settings.database_url, echo=False)
    is_sqlite = settings.database_url.startswith("sqlite")
    migrations = SQLITE_MIGRATIONS if is_sqlite else POSTGRES_MIGRATIONS

    async with engine.begin() as conn:
        for sql in migrations:
            try:
                await conn.execute(text(sql.strip()))
                print(f"✅ {sql.strip()[:60]}...")
            except Exception as e:
                err = str(e).lower()
                # Ignore "column already exists" errors
                if "already exists" in err or "duplicate column" in err:
                    print(f"⏭️  Already exists: {sql.strip()[:60]}...")
                else:
                    print(f"❌ Error: {e}")
                    raise

    await engine.dispose()
    print("\n✅ Migration 002 complete")


if __name__ == "__main__":
    asyncio.run(run_migration())
