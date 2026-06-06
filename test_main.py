import pytest


@pytest.mark.asyncio
async def test_get_books_empty(client):
    """GET /books — возвращает пустой список, когда книг нет."""
    response = await client.get("/books")
    assert response.status_code == 200
    assert response.json() == []
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_add_book(client):
    """POST /books — добавляет книгу и возвращает её."""
    payload = {"title": "Война и мир", "author": "Лев Толстой"}
    response = await client.post("/books", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["author"] == payload["author"]
    assert "id" in data  # БД добавляет id


@pytest.mark.asyncio
async def test_get_books_after_add(client):
    """GET /books — возвращает все добавленные книги."""
    book1 = {"title": "Преступление и наказание", "author": "Фёдор Достоевский"}
    book2 = {"title": "Мастер и Маргарита", "author": "Михаил Булгаков"}
    
    await client.post("/books", json=book1)
    await client.post("/books", json=book2)
    
    response = await client.get("/books")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    
    # Проверяем, что книги есть (без проверки id)
    titles = [book["title"] for book in data]
    assert book1["title"] in titles
    assert book2["title"] in titles


@pytest.mark.asyncio
async def test_add_book_missing_author(client):
    """POST /books — без обязательного поля author → 422."""
    payload = {"title": "Только название"}
    response = await client.post("/books", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_book_missing_title(client):
    """POST /books — без обязательного поля title → 422."""
    payload = {"author": "Только автор"}
    response = await client.post("/books", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_book_empty_body(client):
    """POST /books — пустое тело → 422."""
    response = await client.post("/books", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_book_extra_field(client):
    """POST /books — лишнее поле игнорируется, книга добавляется."""
    payload = {"title": "Test", "author": "Tester", "year": 2026}
    response = await client.post("/books", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == "Test"
    assert data["author"] == "Tester"
    assert "year" not in data  # Лишнее поле не возвращается


@pytest.mark.asyncio
async def test_add_multiple_books_with_same_title(client):
    """POST /books — можно добавить несколько книг с одинаковым названием."""
    book = {"title": "Дубль", "author": "Автор"}
    
    await client.post("/books", json=book)
    await client.post("/books", json=book)
    
    response = await client.get("/books")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    
    # Обе книги имеют одинаковое название
    assert data[0]["title"] == "Дубль"
    assert data[1]["title"] == "Дубль"