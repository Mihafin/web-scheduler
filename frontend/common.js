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
 * Расписание студии: время в БД — UTC-метки (часы/минуты = «на стене студии»), без привязки к поясу браузера.
 * datetime-local (YYYY-MM-DDTHH:MM) → ISO с теми же числами в UTC (…Z).
 * @param {string} val
 * @returns {string}
 */
function studioDatetimeLocalToIso(val) {
  if (!val) return '';
  const [datePart, timePart = '00:00'] = val.split('T');
  const [y, m, d] = datePart.split('-').map(Number);
  const [hh, mm] = timePart.split(':').map(Number);
  return new Date(Date.UTC(y, m - 1, d, hh, mm || 0, 0, 0)).toISOString();
}

/**
 * ISO (UTC-метка расписания) → значение для input[type="datetime-local"]
 * @param {string} iso
 * @returns {string}
 */
function isoToStudioDatetimeLocal(iso) {
  const d = new Date(iso);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}T${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

/**
 * UTC-метка расписания → YYYY-MM-DD HH:MM (по UTC-компонентам)
 * @param {string} iso
 * @returns {string}
 */
function formatStudioNoSeconds(iso) {
  const d = new Date(iso);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

/**
 * UTC-метка расписания → HH:MM
 * @param {string} iso
 * @returns {string}
 */
function hhmmStudio(iso) {
  const d = new Date(iso);
  return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

/**
 * Строка input[type="date"] YYYY-MM-DD → начало этого календарного дня как UTC-метка (для фильтра API)
 * @param {string} yyyyMmDd
 * @returns {string}
 */
function studioDateInputStartIso(yyyyMmDd) {
  const [y, m, d] = yyyyMmDd.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d, 0, 0, 0, 0)).toISOString();
}

/**
 * Строка input[type="date"] → начало следующего календарного дня (полуоткрытый интервал «по»)
 * @param {string} yyyyMmDd
 * @returns {string}
 */
function studioDateInputNextDayStartIso(yyyyMmDd) {
  const [y, m, d] = yyyyMmDd.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d + 1, 0, 0, 0, 0)).toISOString();
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
 * Значение input[type="datetime-local"] → ISO (локаль браузера)
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
    try { return formatStudioNoSeconds(m); } catch (_) { return m; }
  });
}

// ============ Дни недели ============

const WEEKDAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

/**
 * Заголовок дня для отчёта: «Пн. dd.mm.yyyy» по UTC-метке полуночи
 * @param {Date} d — момент, UTC-компоненты = дата дня
 * @returns {string}
 */
function fmtStudioDay(d) {
  return `${WEEKDAYS[d.getUTCDay()]}. ${pad(d.getUTCDate())}.${pad(d.getUTCMonth() + 1)}.${d.getUTCFullYear()}`;
}

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
 * Jaro similarity между двумя строками (0..1)
 * @param {string} s1
 * @param {string} s2
 * @returns {number}
 */
function jaroSimilarity(s1, s2) {
  if (s1 === s2) return 1.0;
  if (s1.length === 0 || s2.length === 0) return 0.0;

  const matchWindow = Math.max(0, Math.floor(Math.max(s1.length, s2.length) / 2) - 1);
  const s1Matches = new Array(s1.length).fill(false);
  const s2Matches = new Array(s2.length).fill(false);

  let matches = 0;
  let transpositions = 0;

  // Найти совпадающие символы
  for (let i = 0; i < s1.length; i++) {
    const start = Math.max(0, i - matchWindow);
    const end = Math.min(i + matchWindow + 1, s2.length);

    for (let j = start; j < end; j++) {
      if (s2Matches[j] || s1[i] !== s2[j]) continue;
      s1Matches[i] = true;
      s2Matches[j] = true;
      matches++;
      break;
    }
  }

  if (matches === 0) return 0.0;

  // Подсчёт транспозиций
  let k = 0;
  for (let i = 0; i < s1.length; i++) {
    if (!s1Matches[i]) continue;
    while (!s2Matches[k]) k++;
    if (s1[i] !== s2[k]) transpositions++;
    k++;
  }

  return (matches / s1.length + matches / s2.length + (matches - transpositions / 2) / matches) / 3;
}

/**
 * Jaro-Winkler similarity — улучшенный Jaro для имён (даёт бонус за общий префикс)
 * @param {string} s1
 * @param {string} s2
 * @param {number} [p=0.1] - scaling factor (обычно 0.1)
 * @returns {number}
 */
function jaroWinklerSimilarity(s1, s2, p = 0.1) {
  const jaro = jaroSimilarity(s1, s2);
  
  // Найти длину общего префикса (макс. 4 символа)
  let prefixLen = 0;
  const maxPrefix = Math.min(4, s1.length, s2.length);
  for (let i = 0; i < maxPrefix; i++) {
    if (s1[i] === s2[i]) prefixLen++;
    else break;
  }

  return jaro + prefixLen * p * (1 - jaro);
}

/**
 * Нормализовать строку для сравнения
 * @param {string} str
 * @returns {string}
 */
function normalizeForComparison(str) {
  return str.toLowerCase().replace(/ё/g, 'е').trim();
}

/**
 * Разбить строку на слова
 * @param {string} str
 * @returns {string[]}
 */
function splitWords(str) {
  return str.split(/\s+/).filter(w => w.length > 0);
}

/**
 * Проверить совпадение слов (без учёта порядка)
 * @param {string} a
 * @param {string} b
 * @returns {boolean}
 */
function haveSameWords(a, b) {
  const wordsA = splitWords(normalizeForComparison(a)).sort().join(' ');
  const wordsB = splitWords(normalizeForComparison(b)).sort().join(' ');
  return wordsA === wordsB;
}

/**
 * Проверить, похожи ли два слова (для поиска опечаток)
 * Использует комбинацию: Jaro-Winkler и нормализованный Левенштейн
 * @param {string} word1
 * @param {string} word2
 * @returns {boolean}
 */
function areWordsSimilar(word1, word2) {
  if (word1 === word2) return true;
  
  // Jaro-Winkler >= 0.85 — хорошее совпадение для имён
  const jw = jaroWinklerSimilarity(word1, word2);
  if (jw >= 0.85) return true;
  
  // Нормализованный Левенштейн: допускаем 1-2 ошибки в зависимости от длины
  const maxLen = Math.max(word1.length, word2.length);
  const distance = levenshteinDistance(word1, word2);
  
  // Для коротких слов (до 5 букв) допускаем 1 ошибку
  // Для длинных слов допускаем до 20% ошибок
  if (maxLen <= 5) {
    return distance <= 1;
  }
  return distance / maxLen <= 0.2;
}

/**
 * Найти похожих клиентов
 * 
 * Критерии совпадения:
 * 1. Полное совпадение (без учёта регистра и пробелов)
 * 2. Слова в разном порядке: "Анна Булочкина" = "Булочкина Анна"
 * 3. Похожие слова (опечатки): "Анна Булочкна" ≈ "Анна Булочкина"
 * 4. Комбинация: похожие слова в любом порядке
 * 
 * @param {string} newName - имя для проверки
 * @param {Array<{name: string}>} existingClients - список существующих клиентов
 * @returns {Array<{name: string, similarity: number}>}
 */
function findSimilarClients(newName, existingClients) {
  const newNorm = normalizeForComparison(newName);
  const newWords = splitWords(newNorm);
  
  if (newWords.length === 0) return [];
  
  const results = [];
  
  for (const client of existingClients) {
    const existingNorm = normalizeForComparison(client.name);
    const existingWords = splitWords(existingNorm);
    
    if (existingWords.length === 0) continue;
    
    // Проверка 1: Полное совпадение нормализованных строк
    if (newNorm.replace(/\s+/g, '') === existingNorm.replace(/\s+/g, '')) {
      results.push({ ...client, similarity: 1.0 });
      continue;
    }
    
    // Проверка 2: Слова в разном порядке (точное совпадение)
    if (haveSameWords(newName, client.name)) {
      results.push({ ...client, similarity: 0.99 });
      continue;
    }
    
    // Проверка 3: Пословное нечёткое совпадение
    // Каждое слово из нового имени должно найти похожее в существующем
    // и наоборот (чтобы "Анна" не совпадала с "Анна Булочкина")
    
    // Проверяем, что количество слов примерно совпадает
    if (Math.abs(newWords.length - existingWords.length) > 1) continue;
    
    // Для каждого нового слова ищем похожее среди существующих
    const usedExisting = new Set();
    let allNewWordsMatched = true;
    let totalSimilarity = 0;
    
    for (const newWord of newWords) {
      let bestMatch = null;
      let bestSim = 0;
      
      for (let i = 0; i < existingWords.length; i++) {
        if (usedExisting.has(i)) continue;
        
        const existingWord = existingWords[i];
        if (areWordsSimilar(newWord, existingWord)) {
          const sim = jaroWinklerSimilarity(newWord, existingWord);
          if (sim > bestSim) {
            bestSim = sim;
            bestMatch = i;
          }
        }
      }
      
      if (bestMatch !== null) {
        usedExisting.add(bestMatch);
        totalSimilarity += bestSim;
      } else {
        allNewWordsMatched = false;
        break;
      }
    }
    
    // Также проверяем, что не осталось лишних слов в существующем имени
    const allExistingWordsMatched = usedExisting.size === existingWords.length || 
                                     existingWords.length - usedExisting.size <= 1;
    
    if (allNewWordsMatched && allExistingWordsMatched) {
      const avgSimilarity = totalSimilarity / newWords.length;
      // Только если средняя похожесть слов достаточно высока
      if (avgSimilarity >= 0.8) {
        results.push({ ...client, similarity: avgSimilarity });
      }
    }
  }
  
  // Сортируем по убыванию похожести
  results.sort((a, b) => b.similarity - a.similarity);
  
  return results;
}

