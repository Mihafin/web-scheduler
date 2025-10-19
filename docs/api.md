## REST API

Базовый префикс: `/api`

Все эндпоинты предполагают, что доступ к сайту защищён Nginx Basic Auth. Приложение само ролей не вводит.

### Здоровье

- GET `/api/health` → `{ status: "ok" }`

### Расписания

- GET `/api/schedules?from=ISO&to=ISO&tag_value_ids=1,2,3`
  - Фильтрация по интервалу времени (пересекающемуся) и по списку значений тегов (любое из указанных)
  - Ответ: `[{ id, title, dateFrom, dateTo, tagValueIds: number[] }]`

- POST `/api/schedules`
  - Тело: `{ title: string, dateFrom: ISO8601, dateTo: ISO8601, tagValueIds?: number[] }`
  - Ответ: объект расписания с присвоенным `id`

- PUT `/api/schedules/{id}`
  - Тело: `{ title?: string, dateFrom?: ISO8601, dateTo?: ISO8601, tagValueIds?: number[] }`
  - Ответ: обновлённый объект расписания

- DELETE `/api/schedules/{id}` → 204

### Теги

- GET `/api/tags`
  - Ответ: `[{ id, name, required, unique_resource }]`

- POST `/api/tags`
  - Тело: `{ name: string, required?: boolean, unique_resource?: boolean }`
  - Ответ: `{ id, name, required, unique_resource }`

- PUT `/api/tags/{id}`
  - Тело: `{ name?: string, required?: boolean, unique_resource?: boolean }`
  - Ответ: `{ id, name, required, unique_resource }`

- DELETE `/api/tags/{id}` → 204

### Значения тегов

- GET `/api/tags/{tagId}/values`
  - Ответ: `[{ id, tagId, value }]`

- POST `/api/tags/{tagId}/values`
  - Тело: `{ value: string }`
  - Ответ: `{ id, tagId, value }`

- PUT `/api/tag-values/{id}`
  - Тело: `{ value: string }`
  - Ответ: `{ id, tagId, value }`

- DELETE `/api/tag-values/{id}` → 204

### Форматы данных

- Времена передаются и возвращаются в ISO‑8601 строках (например, `2025-10-18T09:00:00+03:00`)
- Фильтрация по интервалу — возвращаются события, у которых диапазон времени пересекается с `[from, to]`
- Параметр `tag_value_ids` — список идентификаторов через запятую; фильтр трактуется как «содержит любое из указанных значений»


