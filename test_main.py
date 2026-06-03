# test_main.py
from fastapi.testclient import TestClient
from main import app, books

client = TestClient(app)


def setup_function():
    """Очищает хранилище книг перед каждым тестом."""
    books.clear()


def test_get_books_empty():
    """GET /books — возвращает пустой список, когда книг нет."""
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == []
    assert len(response.json()) == 0


def test_add_book():
    """POST /books — добавляет книгу и возвращает её."""
    payload = {"title": "Война и мир", "author": "Лев Толстой"}
    response = client.post("/books", json=payload)
    assert response.status_code == 200
    assert response.json() == payload
    # Книга действительно сохранилась в список
    assert len(books) == 1
    assert books[0] == payload


def test_get_books_after_add():
    """GET /books — возвращает все добавленные книги."""
    book1 = {"title": "Преступление и наказание", 
             "author": "Фёдор Достоевский"}
    book2 = {"title": "Мастер и Маргарита", "author": "Михаил Булгаков"}
    client.post("/books", json=book1)
    client.post("/books", json=book2)

    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == [book1, book2]
    assert len(response.json()) == 2


def test_add_book_missing_author():
    """POST /books — без обязательного поля author → 422."""
    payload = {"title": "Только название"}
    response = client.post("/books", json=payload)
    assert response.status_code == 422


def test_add_book_missing_title():
    """POST /books — без обязательного поля title → 422."""
    payload = {"author": "Только автор"}
    response = client.post("/books", json=payload)
    assert response.status_code == 422


def test_add_book_empty_body():
    """POST /books — пустое тело → 422."""
    response = client.post("/books", json={})
    assert response.status_code == 422


def test_add_book_extra_field():
    """POST /books — лишнее поле игнорируется, книга добавляется."""
    payload = {"title": "Test", "author": "Tester", "year": 2026}
    response = client.post("/books", json=payload)
    assert response.status_code == 200
    assert response.json() == {"title": "Test", "author": "Tester"}


def test_add_multiple_books_with_same_title():
    """POST /books — можно добавить несколько книг с одинаковым названием."""
    book = {"title": "Дубль", "author": "Автор"}
    client.post("/books", json=book)
    client.post("/books", json=book)
    response = client.get("/books")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json() == [book, book]
