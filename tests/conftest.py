import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.main import app
from app.core.db import get_db
from app.models.base import Base
from app.models.user import User
from app.core.security import create_access_token

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    # Create a test user with PFMEA Owner role
    user = User(id=1, email="owner@test.com", role_id=1, is_active=True)
    db_session.add(user)
    
    # Create a viewer user
    viewer = User(id=2, email="viewer@test.com", role_id=2, is_active=True)
    db_session.add(viewer)
    
    await db_session.commit()
    return user

@pytest.fixture
def valid_owner_token() -> str:
    # Role 1 = PFMEA Owner
    return create_access_token(subject="1", role_id="1")

@pytest.fixture
def valid_viewer_token() -> str:
    # Role 2 = Viewer
    return create_access_token(subject="2", role_id="2")

@pytest.fixture
def invalid_token() -> str:
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"
