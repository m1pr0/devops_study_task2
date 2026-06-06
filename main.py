import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, Field, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

def get_database_url() -> str:

    secret_file = os.getenv("DB_PASSWORD_FILE", "/run/secrets/db-password")
    
    if os.path.exists(secret_file):

        with open(secret_file, "r") as f:
            password = f.read().strip()
    else:

        password = os.getenv("DB_PASSWORD", "mysecretpassword")

    host = os.getenv("POSTGRES_HOST", "localhost")
    db_name = os.getenv("POSTGRES_DB", "example")
    user = os.getenv("POSTGRES_USER", "postgres")

    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db_name}"


DATABASE_URL = get_database_url()


engine = create_async_engine(DATABASE_URL, echo=False)


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
    # ИСПРАВЛЕНИЕ: используем execute и scalars().all() вместо exec()
    result = await session.execute(select(Book))
    return result.scalars().all()

@app.post("/books", response_model=Book, status_code=201)
async def add_book(book: Book, session: AsyncSession = Depends(get_session)):
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book
