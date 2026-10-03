import psycopg2

# Вставьте сюда ваш пароль (в кавычках!)
DB_PASSWORD = "Ali07" 

# SQL-скрипт для создания таблиц
SQL_SCRIPT = """
-- 1. Создаем ENUM (перечисление) для типов атак
CREATE TYPE attack_type_enum AS ENUM ('DDoS', 'BruteForce', 'SQLInjection', 'XSS');

-- 2. Создаем таблицу Моделей (Models)
CREATE TABLE models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (model_name, version)
);

-- 3. Создаем таблицу Экспериментов (Experiments)
CREATE TABLE experiments (
    experiment_id SERIAL PRIMARY KEY,
    model_id INT NOT NULL,
    attack_type attack_type_enum NOT NULL,
    accuracy NUMERIC(5, 2) CHECK (accuracy > 0 AND accuracy <= 100),
    is_successful BOOLEAN DEFAULT FALSE,
    start_time TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_model
        FOREIGN KEY (model_id) 
        REFERENCES models (model_id)
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);
"""

try:
    conn = psycopg2.connect(
        dbname="lab1_db",
        user="postgres",
        password=DB_PASSWORD,
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    
    # Выполняем скрипт
    cur.execute(SQL_SCRIPT)
    conn.commit() # Сохраняем изменения
    
    print(" Таблицы успешно созданы!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(" Ошибка:", e)