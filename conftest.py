import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, delete
from typing import AsyncGenerator

from main import app, get_session, Book


def get_test_database_url() -> str:
    """Формирует URL для тестовой БД из переменных окружения."""
    password = os.getenv("POSTGRES_PASSWORD", "test_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    db_name = os.getenv("POSTGRES_DB", "test_db")
    user = os.getenv("POSTGRES_USER", "test_user")
    
    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db_name}"


TEST_DATABASE_URL = get_test_database_url()

# Создаем отдельный движок для тестов
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Создает таблицы в тестовой БД перед запуском всех тестов.
    Удаляет таблицы после завершения всех тестов.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    """
    Очищает таблицу books перед каждым тестом.
    Это гарантирует, что тесты не влияют друг на друга.
    """
    async with AsyncSession(test_engine) as session:
        await session.exec(delete(Book))
        await session.commit()
    
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Создает асинхронный HTTP клиент для тестов.
    Подменяет зависимость get_session, чтобы эндпоинты
    использовали тестовый движок вместо основного.
    """
    async def override_get_session():
        async with AsyncSession(test_engine) as session:
            yield session
    
    # Подменяем зависимость в приложении
    app.dependency_overrides[get_session] = override_get_session
    
    # Создаем асинхронный клиент
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Очищаем подмену после теста
    app.dependency_overrides.clear()
