import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession  # <-- Для консистентности берем из sqlmodel
from sqlmodel import SQLModel

from main import app, get_session, Book


def get_test_database_url() -> str:

    password = os.getenv("POSTGRES_PASSWORD", "test_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    db_name = os.getenv("POSTGRES_DB", "test_db")
    user = os.getenv("POSTGRES_USER", "test_user")

    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db_name}"


TEST_DATABASE_URL = get_test_database_url()


# 1. Создаем engine ВНУТРИ фикстуры, чтобы он попал в нужный event loop
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()  # Корректно закрываем соединения после всех тестов


# 2. Принимаем test_engine как аргумент
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(test_engine):
    """Создает таблицы один раз перед всеми тестами и удаляет после."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# 3. Принимаем test_engine как аргумент
@pytest_asyncio.fixture
async def session(test_engine):
    """
    Создает сессию внутри транзакции.
    После каждого теста транзакция откатывается (rollback), 
    что мгновенно очищает БД без явных DELETE запросов.
    """
    async with test_engine.begin() as conn:
        async_session = AsyncSession(bind=conn, expire_on_commit=False)
        yield async_session
        await async_session.rollback()


@pytest_asyncio.fixture
async def client(session):
    """Подменяет зависимость get_session на нашу тестовую сессию с rollback."""
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session


    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
    