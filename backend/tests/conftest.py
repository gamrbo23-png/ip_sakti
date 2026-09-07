"""
Pytest configuration and global fixtures.
"""
import pytest
import pytest_asyncio
from app.database import init_extensions, engine, Base


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Ensure tables are created before running tests."""
    await init_extensions()
    yield
