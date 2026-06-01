# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

books: list[dict] = []


class Book(BaseModel):
    title: str
    author: str


@app.get("/books")
def get_books():
    return books


@app.post("/books")
def add_book(book: Book):
    books.append(book.model_dump())
    return book
