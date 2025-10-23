## REST API

Базовый префикс: `/api`

Все эндпоинты предполагают, что доступ к сайту защищён Nginx Basic Auth. Приложение само ролей не вводит.

### Здоровье

- GET `/api/health` → `{ status: "ok" }`

### Расписания

- GET `/api/schedules?from=ISO&to=ISO&tag_value_ids=1,2,3`
  - Фильтрация по интервалу времени (пересечение по полуоткрытому интервалу `[from, to)`).
  - Фильтрация по значениям тегов: И между группами тегов, ИЛИ внутри группы.
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
  - Ответ: `[{ id, tagId, value, color }]`

- POST `/api/tags/{tagId}/values`
  - Тело: `{ value: string, color?: string }`
  - Ответ: `{ id, tagId, value, color }`

- PUT `/api/tag-values/{id}`
  - Тело: `{ value?: string, color?: string }`
  - Ответ: `{ id, tagId, value, color }`

- DELETE `/api/tag-values/{id}` → 204

### Форматы данных

- Времена передаются и возвращаются в ISO‑8601 строках (например, `2025-10-18T09:00:00+03:00`)
- Пересечение по времени — полуоткрытый интервал `[from, to)`.
- Параметр `tag_value_ids`: значения группируются по `tagId`; событие проходит фильтр, если содержит хотя бы одно значение из каждой группы.
- При создании/редактировании события:
  - проверяются «обязательные» теги (должно быть выбрано хотя бы одно значение каждого такого тега)
  - для тегов «уникальный ресурс» проверяются пересечения по времени; в случае пересечения — 400 с описанием


