import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Field, create_async_engine, AsyncSession, select

def get_database_url() -> str:
    """
    Формирует URL подключения к БД.
    Если запущено в Docker, читает пароль из файла секрета.
    Если локально, использует переменные окружения или значения по умолчанию.
    """
    # Путь к файлу секрета (стандартный для Docker или из переменной окружения)
    secret_file = os.getenv("DB_PASSWORD_FILE", "/run/secrets/db-password")
    
    if os.path.exists(secret_file):
        # Читаем пароль из файла. 
        # ВАЖНО: .strip() убирает скрытые переносы строк (\n), которые часто ломают подключение!
        with open(secret_file, "r") as f:
            password = f.read().strip()
    else:
        # Фоллбэк для локальной разработки без Docker
        password = os.getenv("DB_PASSWORD", "mysecretpassword")

    host = os.getenv("POSTGRES_HOST", "localhost")
    db_name = os.getenv("POSTGRES_DB", "example")
    user = os.getenv("POSTGRES_USER", "postgres")

    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db_name}"

# Получаем итоговый URL
DATABASE_URL = get_database_url()

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# ... дальше твой код без изменений ...
class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author: str

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/books", response_model=list[Book])
async def get_books(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Book))
    return result.all()

@app.post("/books", response_model=Book, status_code=201)
async def add_book(book: Book, session: AsyncSession = Depends(get_session)):
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book
