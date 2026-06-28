-- Создание таблицы visits, если она не существует
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    count INT NOT NULL
);

-- Инициализация начального значения (только если строка с id=1 отсутствует)
INSERT INTO visits (id, count)
SELECT 1, 0
WHERE NOT EXISTS (SELECT 1 FROM visits WHERE id = 1);