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
  -- Время студии: ISO UTC (...Z), цифры часов/минут = «на стене» студии (см. фронт: timeZone UTC + Date.UTC)
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

-- ============================================================================
-- Клиенты
-- Справочник клиентов системы
-- ============================================================================
CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- Индекс для поиска клиентов по имени
CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name);

-- ============================================================================
-- Типы абонементов (шаблоны)
-- Предустановленные типы абонементов для быстрого добавления
-- ============================================================================
CREATE TABLE IF NOT EXISTS subscription_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  -- Количество занятий в абонементе
  lessons_count INTEGER NOT NULL,
  -- Срок действия в днях
  duration_days INTEGER NOT NULL
);

-- ============================================================================
-- Покупки абонементов (приход)
-- Запись о покупке абонемента клиентом
-- ============================================================================
CREATE TABLE IF NOT EXISTS subscription_purchases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  -- Количество купленных занятий
  lessons_count INTEGER NOT NULL,
  -- Дата покупки (ISO-8601)
  purchase_date TEXT NOT NULL,
  -- Дата окончания действия абонемента (ISO-8601)
  expiry_date TEXT NOT NULL,
  -- Комментарий (название абонемента, способ оплаты и т.д.)
  comment TEXT NULL,
  CONSTRAINT fk_purchase_client
    FOREIGN KEY (client_id)
    REFERENCES clients(id)
    ON DELETE CASCADE
);

-- Индексы для покупок
CREATE INDEX IF NOT EXISTS idx_purchases_client ON subscription_purchases(client_id);
CREATE INDEX IF NOT EXISTS idx_purchases_date ON subscription_purchases(purchase_date);

-- ============================================================================
-- Расходы абонементов (трата)
-- Запись об использовании одного занятия из абонемента
-- ============================================================================
CREATE TABLE IF NOT EXISTS subscription_expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  -- Дата расхода (ISO-8601)
  expense_date TEXT NOT NULL,
  -- Комментарий (название занятия, тренер и т.д.)
  comment TEXT NULL,
  CONSTRAINT fk_expense_client
    FOREIGN KEY (client_id)
    REFERENCES clients(id)
    ON DELETE CASCADE
);

-- Индексы для расходов
CREATE INDEX IF NOT EXISTS idx_expenses_client ON subscription_expenses(client_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON subscription_expenses(expense_date);

