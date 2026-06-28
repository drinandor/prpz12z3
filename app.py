import os
import sys
import time
from flask import Flask, render_template
import psycopg2
import redis

app = Flask(__name__)

# Загрузка настроек из переменных окружения
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Подключение к Redis
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_db_connection():
    """Безопасное подключение к БД с несколькими попытками"""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(2)
    raise Exception("Не удалось подключиться к PostgreSQL")

# Простая проверка связи с БД при старте
try:
    conn = get_db_connection()
    conn.close()
except Exception as e:
    print(f"Предупреждение при старте (БД еще не запущена): {e}")

@app.route('/')
def index():
    # Проверяем наличие значения в кэше Redis
    cached_count = cache.get("visit_count")
    
    if cached_count is not None:
        count = int(cached_count)
        source = "Redis (Кэш)"
    else:
        # Пытаемся получить соединение с БД
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Увеличиваем счетчик в БД
            cur.execute("UPDATE visits SET count = count + 1 WHERE id = 1 RETURNING count;")
            count = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Критическая ошибка подключения к БД: {e}. Завершение процесса для триггера restart: on-failure.")
            sys.exit(1) # Принудительно «роняем» контейнер приложения для перезапуска
        
        # Сохраняем в кэш Redis на 300 секунд (5 минут)
        cache.setex("visit_count", 5, count)
        source = "PostgreSQL (База данных)"

    return render_template('index.html', count=count, source=source)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)