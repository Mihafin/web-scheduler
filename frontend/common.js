/**
 * Общие утилиты для Web Scheduler
 */

const API = '/api';

// ============ HTTP ============

/**
 * Fetch JSON с обработкой ошибок
 * @param {string} url
 * @param {RequestInit} [opts]
 * @returns {Promise<any>}
 */
async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ============ Форматирование дат ============

/**
 * Дополнить число нулями до 2 символов
 * @param {number} n
 * @returns {string}
 */
function pad(n) {
  return String(n).padStart(2, '0');
}

/**
 * ISO → локальное время без секунд: YYYY-MM-DD HH:MM
 * @param {string} iso
 * @returns {string}
 */
function formatLocalNoSeconds(iso) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * ISO → значение для input[type="datetime-local"]: YYYY-MM-DDTHH:MM
 * @param {string} iso
 * @returns {string}
 */
function isoToLocalInputValue(iso) {
  const d = new Date(iso);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * Значение input[type="datetime-local"] → ISO
 * @param {string} val
 * @returns {string}
 */
function localInputToIso(val) {
  return new Date(val).toISOString();
}

/**
 * ISO → HH:MM (локальное время)
 * @param {string} iso
 * @returns {string}
 */
function hhmmLocal(iso) {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * Начало дня (локальное) → ISO
 * @param {Date} d
 * @returns {string}
 */
function startOfDayLocalISO(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0).toISOString();
}

/**
 * Начало следующего дня (локальное) → ISO
 * @param {Date} d
 * @returns {string}
 */
function nextDayStartLocalISO(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1, 0, 0, 0, 0).toISOString();
}

/**
 * Заменить все ISO-строки в сообщении на локальный формат без секунд
 * @param {string} msg
 * @returns {string}
 */
function beautifyErrorMessage(msg) {
  const isoRe = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})/g;
  return String(msg).replace(isoRe, (m) => {
    try { return formatLocalNoSeconds(m); } catch (_) { return m; }
  });
}

// ============ Дни недели ============

const WEEKDAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

/**
 * Форматировать дату: "Пн. 01.01.2025"
 * @param {Date} d
 * @returns {string}
 */
function fmtDay(d) {
  return `${WEEKDAYS[d.getDay()]}. ${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`;
}

// ============ HTML ============

/**
 * Экранировать HTML-спецсимволы
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  return String(str)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

// ============ API: Теги ============

/**
 * Загрузить все теги с их значениями
 * @returns {Promise<Array<{tag: object, values: object[]}>>}
 */
async function loadTagsWithValues() {
  const tags = await fetchJSON(`${API}/tags`);
  const result = [];
  for (const t of tags) {
    const values = await fetchJSON(`${API}/tags/${t.id}/values`);
    result.push({ tag: t, values });
  }
  return result;
}

/**
 * Создать тег
 * @param {string} name
 * @param {boolean} required
 * @param {boolean} unique_resource
 */
async function createTag(name, required, unique_resource) {
  return fetchJSON(`${API}/tags`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, required, unique_resource })
  });
}

/**
 * Обновить тег
 * @param {number} id
 * @param {object} payload
 */
async function updateTag(id, payload) {
  return fetchJSON(`${API}/tags/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

/**
 * Удалить тег
 * @param {number} id
 */
async function deleteTag(id) {
  const r = await fetch(`${API}/tags/${id}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(await r.text());
}

/**
 * Создать значение тега
 * @param {number} tagId
 * @param {string} value
 */
async function createTagValue(tagId, value) {
  return fetchJSON(`${API}/tags/${tagId}/values`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value })
  });
}

/**
 * Обновить значение тега
 * @param {number} id
 * @param {object} payload - { value, color }
 */
async function updateTagValue(id, payload) {
  return fetchJSON(`${API}/tags/values/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

/**
 * Удалить значение тега
 * @param {number} id
 */
async function deleteTagValue(id) {
  const r = await fetch(`${API}/tags/values/${id}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(await r.text());
}

// ============ Неделя ============

/**
 * Получить понедельник текущей недели
 * @param {Date} [now]
 * @returns {Date}
 */
function getMondayOfWeek(now = new Date()) {
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  return monday;
}

/**
 * Получить воскресенье недели по понедельнику
 * @param {Date} monday
 * @returns {Date}
 */
function getSundayOfWeek(monday) {
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return sunday;
}

/**
 * Форматировать дату для input[type="date"]: YYYY-MM-DD
 * @param {Date} d
 * @returns {string}
 */
function formatDateInput(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// ============ Сравнение строк ============

/**
 * Расстояние Левенштейна (edit distance) между двумя строками
 * @param {string} a
 * @param {string} b
 * @returns {number}
 */
function levenshteinDistance(a, b) {
  const matrix = [];
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  return matrix[b.length][a.length];
}

/**
 * Найти похожих клиентов (разница <= 3 символов)
 * @param {string} newName - имя для проверки
 * @param {Array<{name: string}>} existingClients - список существующих клиентов
 * @returns {Array<{name: string}>}
 */
function findSimilarClients(newName, existingClients) {
  const newLower = newName.toLowerCase();
  return existingClients.filter(client => {
    const existingLower = client.name.toLowerCase();
    const distance = levenshteinDistance(newLower, existingLower);
    return distance <= 3;
  });
}

