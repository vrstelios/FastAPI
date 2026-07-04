import os
from http.client import responses

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from collections.abc import AsyncGenerator

from sqlalchemy.orm import join
from app.core.config import settings

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.main import app

DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST", settings.database_url_test)

pytest_plugins = ["anyio"]

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
    return engine

@pytest.fixture(scope="session")
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()

@pytest.fixture
async def db_session(test_engine, setup_database) -> AsyncGenerator[AsyncSession]:
    conn = await test_engine.connect()
    trans = await conn.begin()

    test_async_session = async_sessionmaker(
        bind=conn, class_=AsyncSession, expire_on_commit=False,
        join_transaction_mode="create_savepoint"
    )

    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await conn.close()

@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

async def create_test_user(client: AsyncClient, username: str = "testuser", email: str = "test@example.com", password: str ="testpassword123") -> dict:
       responses = await client.post(
           "/api/users",
           json={
               "username": username,
               "email": email,
               "password": password,
           },
       )
       assert responses.status_code == 201, f"Failed to create user: {responses.text}"
       return responses.json()

async def login_user(client: AsyncClient, email: str = "test@example.com", password: str ="testpassword123") -> str:
    response = await client.post(
        "/api/users/token",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    return response.json()["access_token"]

def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}