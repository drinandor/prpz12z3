import pytest
from app import app, get_db_connection, cache

@pytest.fixture(autouse=True)
def setup_database():
    """Автоматическое создание таблицы visits в тестовой БД перед тестами"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            count INT NOT NULL
        );
    """)
    cur.execute("SELECT COUNT(*) FROM visits;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO visits (id, count) VALUES (1, 0);")
    conn.commit()
    cur.close()
    conn.close()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_db_connection():
    """Тест подключения к PostgreSQL"""
    conn = get_db_connection()
    assert conn is not None
    conn.close()

def test_redis_connection():
    """Тест записи и чтения данных из Redis"""
    cache.set("test_pipeline_key", "active")
    value = cache.get("test_pipeline_key")
    assert value == "active"

def test_index_page(client):
    """Тест доступности главной страницы сайта (должна вернуть код 200)"""
    response = client.get('/')
    assert response.status_code == 200