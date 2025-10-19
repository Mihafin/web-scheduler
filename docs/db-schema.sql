PRAGMA foreign_keys = ON;

-- Таблица тегов
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

-- Значения тегов (например: tag «зал» → values «зал1», «зал2»)
CREATE TABLE IF NOT EXISTS tag_values (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tag_id INTEGER NOT NULL,
  value TEXT NOT NULL,
  color TEXT NULL,
  CONSTRAINT fk_tag_values_tag
    FOREIGN KEY (tag_id)
    REFERENCES tags(id)
    ON DELETE CASCADE,
  CONSTRAINT uq_tag_value UNIQUE (tag_id, value)
);

-- Расписания (диапазоны времени)
CREATE TABLE IF NOT EXISTS schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  date_from TEXT NOT NULL, -- ISO8601: YYYY-MM-DDTHH:MM:SSZ или локальное время
  date_to TEXT NOT NULL,
  CONSTRAINT ck_schedule_range CHECK (date_to >= date_from)
);

-- Связующая таблица N—M: расписания ↔ значения тегов
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

-- Индексы для ускорения фильтрации/поиска
CREATE INDEX IF NOT EXISTS idx_tag_values_tag_id ON tag_values(tag_id);
CREATE INDEX IF NOT EXISTS idx_schedules_from ON schedules(date_from);
CREATE INDEX IF NOT EXISTS idx_schedules_to ON schedules(date_to);
CREATE INDEX IF NOT EXISTS idx_stv_tag_value_id ON schedule_tag_values(tag_value_id);


