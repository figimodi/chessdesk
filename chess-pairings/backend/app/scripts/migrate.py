import asyncio

from app.core.migrations import run_migrations


if __name__ == "__main__":
    asyncio.run(run_migrations())
