-- Web Scheduler: SQL-схема базы данных
-- Совместимо с SQLite 3.x
-- 
-- Для инициализации:
--   sqlite3 var/data.sqlite < docs/db-schema.sql

PRAGMA foreign_keys = ON;

-- ============================================================================
-- Таблица тегов
-- Теги — это категории для группировки значений (например: "зал", "тренер")
-- ============================================================================
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  -- Обязательный тег: событие должно иметь хотя бы одно значение этого тега
  required BOOLEAN NOT NULL DEFAULT 0,
  -- Уникальный ресурс: проверка пересечений по времени для событий с одинаковым значением
  unique_resource BOOLEAN NOT NULL DEFAULT 0
);

-- ============================================================================
-- Значения тегов
-- Конкретные значения внутри тега (например: tag "зал" → values "зал1", "зал2")
-- ============================================================================
CREATE TABLE IF NOT EXISTS tag_values (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tag_id INTEGER NOT NULL,
  value TEXT NOT NULL,
  -- HEX цвет для подсветки события в календаре (например: #FF5733)
  color TEXT NULL,
  CONSTRAINT fk_tag_values_tag
    FOREIGN KEY (tag_id)
    REFERENCES tags(id)
    ON DELETE CASCADE,
  CONSTRAINT uq_tag_value UNIQUE (tag_id, value)
);

-- ============================================================================
-- Расписания (события календаря)
-- ============================================================================
CREATE TABLE IF NOT EXISTS schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  -- Даты хранятся как ISO-8601 строки: YYYY-MM-DDTHH:MM:SS или с timezone
  date_from TEXT NOT NULL,
  date_to TEXT NOT NULL,
  -- Признак отмены события (отображается перечёркнутым, не удаляется)
  is_canceled BOOLEAN NOT NULL DEFAULT 0,
  -- Контактная информация (телефон, email и т.д.)
  contact TEXT NULL,
  CONSTRAINT ck_schedule_range CHECK (date_to >= date_from)
);

-- ============================================================================
-- Связующая таблица N—M: расписания ↔ значения тегов
-- Позволяет назначать событию несколько значений тегов
-- ============================================================================
CREATE TABLE IF NOT EXISTS schedule_tag_values (
  schedule_id INTEGER NOT NULL,
  tag_value_id INTEGER NOT NULL,
  PRIMARY KEY (schedule_id, tag_value_id),
  CONSTRAINT fk_stv_schedule
    FOREIGN KEY (schedule_id)
    REFERENCES schedules(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_stv_tag_value
    FOREIGN KEY (tag_value_id)
    REFERENCES tag_values(id)
    ON DELETE CASCADE
);

-- ============================================================================
-- Журнал аудита
-- Фиксирует все изменения данных (CREATE/UPDATE/DELETE)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  -- Время операции в UTC (ISO-8601: 2025-01-15T10:30:00Z)
  ts TEXT NOT NULL,
  -- Имя пользователя из заголовка X-Remote-User (может быть NULL)
  username TEXT NULL,
  -- Тип действия: CREATE, UPDATE, DELETE
  action TEXT NOT NULL,
  -- Имя сущности/таблицы: schedules, tags, tag_values
  entity TEXT NOT NULL,
  -- ID изменённой записи (может быть NULL для batch-операций)
  entity_id INTEGER NULL,
  -- Детали изменений (например: "title: old -> new; date_from: 2025-01-01 -> 2025-01-02")
  details TEXT NULL
);

-- ============================================================================
-- Индексы для ускорения запросов
-- ============================================================================

-- Быстрый поиск значений по тегу
CREATE INDEX IF NOT EXISTS idx_tag_values_tag_id ON tag_values(tag_id);

-- Фильтрация расписаний по датам
CREATE INDEX IF NOT EXISTS idx_schedules_from ON schedules(date_from);
CREATE INDEX IF NOT EXISTS idx_schedules_to ON schedules(date_to);

-- Поиск событий по значениям тегов
CREATE INDEX IF NOT EXISTS idx_stv_tag_value_id ON schedule_tag_values(tag_value_id);

-- Фильтрация аудита по времени
CREATE INDEX IF NOT EXISTS idx_audit_logs_ts ON audit_logs(ts);

-- Фильтрация аудита по сущности
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity);

