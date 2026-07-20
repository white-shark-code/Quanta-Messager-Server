"""Reset database schema using asyncpg directly.

Сбрасывает схему базы данных через asyncpg.
"""

import asyncio
import os
import sys

server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(server_dir, "src")
sys.path.insert(0, src_dir)
os.chdir(server_dir)

from settings import cfg


async def reset_schema():
    """Drop and recreate public schema.

    Удаляет и пересоздаёт схему public.
    """
    import asyncpg

    # Build connection kwargs from DATABASE_URL
    url = cfg.DATABASE_URL
    # postgresql+asyncpg://user:pass@host:port/dbname
    url_no_driver = url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(url_no_driver)
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.execute("CREATE SCHEMA public")
    finally:
        await conn.close()


asyncio.run(reset_schema())
