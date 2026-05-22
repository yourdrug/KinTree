/**
 * src/api/index.js
 *
 * Единственный API-слой приложения.
 *
 * Ключевые изменения:
 *  - buildRelationMaps(graph) — строит per-person карту связей из graph.edges
 *    (parent_ids, child_ids, spouse_ids, sibling_ids, sibling_type_map)
 *    Используется вместо несуществующих полей person.parent_ids и т.д.
 *  - loadFamilyTree возвращает { family, persons, graph, relationMaps }
 *  - formatPartialDate / fromPartialDate — корректная работа с PartialDateSchema
 *  - toPartialDate — конвертация строки "YYYY-MM-DD" → { year, month, day }
 *  - relationsApi.addSiblingViaParents — добавить сиблинга через связи с родителями
 */

import axios from "axios";
import {http} from "@/api/client.js";

// ── Axios instance ────────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // Нормализуем ошибку: пробрасываем структуру { message, errors }
    const data = err.response?.data;
    if (data?.message) err.message = data.message;
    return Promise.reject(err);
  }
);

// ── Утилиты для PartialDateSchema ─────────────────────────────────────────────

/**
 * PartialDateSchema: { year: int|null, month: int|null, day: int|null }
 *
 * formatPartialDate({ year: 1990, month: 6, day: 15 }) → "15.06.1990"
 * formatPartialDate({ year: 1990, month: 6 })          → "06.1990"
 * formatPartialDate({ year: 1990 })                     → "1990"
 * formatPartialDate(null)                               → ""
 */
export function formatPartialDate(pd) {
  if (!pd || typeof pd !== "object") return "";
  const { year, month, day } = pd;
  if (!year && !month && !day) return "";

  if (day && month && year) {
    return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.${year}`;
  }
  if (month && year) {
    return `${String(month).padStart(2, "0")}.${year}`;
  }
  if (year) return String(year);
  if (month) return `месяц ${month}`;
  return "";
}

/**
 * Извлекает год из PartialDateSchema или null.
 */
export function getPartialYear(pd) {
  if (!pd || typeof pd !== "object") return null;
  return pd.year ?? null;
}

/**
 * toPartialDate("1990-06-15") → { year: 1990, month: 6, day: 15 }
 * toPartialDate("1990-06")   → { year: 1990, month: 6, day: null }
 * toPartialDate("")          → null
 * toPartialDate(null)        → null
 */
export function toPartialDate(str) {
  if (!str || typeof str !== "string") return null;
  const parts = str.split("-").map((p) => parseInt(p, 10));
  if (!parts[0] || isNaN(parts[0])) return null;
  return {
    year:  parts[0] || null,
    month: parts[1] || null,
    day:   parts[2] || null,
  };
}

/**
 * fromPartialDate({ year: 1990, month: 6, day: 15 }) → "1990-06-15"
 * fromPartialDate({ year: 1990, month: 6 })          → "1990-06"
 * fromPartialDate({ year: 1990 })                    → "1990"
 * fromPartialDate(null)                              → ""
 */
export function fromPartialDate(pd) {
  if (!pd || typeof pd !== "object") return "";
  const { year, month, day } = pd;
  if (!year) return "";
  if (month && day) return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  if (month)        return `${year}-${String(month).padStart(2, "0")}`;
  return String(year);
}

/**
 * Вычисляет возраст с учётом month/day.
 * Для умерших — возраст на момент смерти.
 * Возвращает null если данных недостаточно.
 */
export function computeAge(birthDate, deathDate) {
  if (!birthDate?.year) return null;

  const birthYear  = birthDate.year;
  const birthMonth = birthDate.month ?? 1;
  const birthDay   = birthDate.day   ?? 1;

  let endYear, endMonth, endDay;
  if (deathDate?.year) {
    endYear  = deathDate.year;
    endMonth = deathDate.month ?? 1;
    endDay   = deathDate.day   ?? 1;
  } else {
    const now = new Date();
    endYear   = now.getFullYear();
    endMonth  = now.getMonth() + 1;
    endDay    = now.getDate();
  }

  let age = endYear - birthYear;
  if (endMonth < birthMonth || (endMonth === birthMonth && endDay < birthDay)) {
    age -= 1;
  }
  return age >= 0 ? age : null;
}

// ── buildRelationMaps ─────────────────────────────────────────────────────────

/**
 * Строит per-person карту связей из graph.edges.
 *
 * Возвращает Map:
 *   personId → {
 *     parentIds:      string[]    — ID родителей
 *     childIds:       string[]    — ID детей
 *     spouseIds:      string[]    — ID супругов
 *     siblingIds:     string[]    — ID братьев/сестёр
 *     siblingTypeMap: Map<siblingId, "FULL"|"HALF"|"STEP">
 *     siblingParentsMap: Map<siblingId, string[]>  — shared_parent_ids
 *   }
 *
 * Это ЕДИНСТВЕННЫЙ правильный способ получить parent_ids/spouse_ids/sibling_ids
 * на клиенте — PersonResponse их не содержит.
 */
export function buildRelationMaps(graph) {
  /** @type {Map<string, {
   *   parentIds: string[], childIds: string[],
   *   spouseIds: string[], siblingIds: string[],
   *   siblingTypeMap: Map<string,string>,
   *   siblingParentsMap: Map<string,string[]>
   * }>} */
  const maps = new Map();

  const ensure = (id) => {
    if (!maps.has(id)) {
      maps.set(id, {
        parentIds:        [],
        childIds:         [],
        spouseIds:        [],
        siblingIds:       [],
        siblingTypeMap:   new Map(),
        siblingParentsMap: new Map(),
      });
    }
    return maps.get(id);
  };

  if (!graph?.edges) return maps;

  for (const edge of graph.edges) {
    switch (edge.type) {
      case "parent_child": {
        // source → родитель, target → ребёнок
        ensure(edge.source_id).childIds.push(edge.target_id);
        ensure(edge.target_id).parentIds.push(edge.source_id);
        break;
      }
      case "spouse": {
        ensure(edge.source_id).spouseIds.push(edge.target_id);
        ensure(edge.target_id).spouseIds.push(edge.source_id);
        break;
      }
      case "sibling": {
        const type    = edge.sibling_type ?? "FULL";
        const parents = edge.shared_parent_ids ?? [];

        const a = ensure(edge.source_id);
        if (!a.siblingIds.includes(edge.target_id)) {
          a.siblingIds.push(edge.target_id);
          a.siblingTypeMap.set(edge.target_id, type);
          a.siblingParentsMap.set(edge.target_id, parents);
        }

        const b = ensure(edge.target_id);
        if (!b.siblingIds.includes(edge.source_id)) {
          b.siblingIds.push(edge.source_id);
          b.siblingTypeMap.set(edge.source_id, type);
          b.siblingParentsMap.set(edge.source_id, parents);
        }
        break;
      }
      default:
        break;
    }
  }

  return maps;
}

/**
 * Получить связи конкретной персоны из карты.
 * Возвращает пустую структуру если персона не найдена.
 */
export function getPersonRelations(relationMaps, personId) {
  return (
    relationMaps.get(personId) ?? {
      parentIds:        [],
      childIds:         [],
      spouseIds:        [],
      siblingIds:       [],
      siblingTypeMap:   new Map(),
      siblingParentsMap: new Map(),
    }
  );
}

// ── Persons API ───────────────────────────────────────────────────────────────

/**
 * Конвертирует данные формы → payload для API.
 * birth_date / death_date: строка "YYYY-MM-DD" → PartialDateSchema
 */
function formToPersonPayload(form, familyId) {
  return {
    first_name: form.first_name?.trim() || null,
    last_name:  form.last_name?.trim()  || null,
    gender:     form.gender  || "MALE",
    birth_date: toPartialDate(form.birth_date),
    death_date: toPartialDate(form.death_date),
    ...(familyId ? { family_id: familyId } : {}),
  };
}

export const personsApi = {
  list:   (params)     => api.get("/persons/",         { params }).then((r) => r.data),
  get:    (id)         => api.get(`/persons/${id}`).then((r) => r.data),
  create: (data)       => api.post("/persons/", data).then((r) => r.data),
  patch:  (id, data)   => api.patch(`/persons/${id}`, data).then((r) => r.data),
  delete: (id)         => api.delete(`/persons/${id}`).then((r) => r.data),
};

// ── Families API ──────────────────────────────────────────────────────────────

export const familiesApi = {
  list:   (params) => http.get("/families/",      { params }).then((r) => r.data),
  get:    (id)     => http.get(`/families/${id}`).then((r) => r.data),
  create: (data)   => http.post("/families/", data).then((r) => r.data),
  patch:  (id, d)  => http.patch(`/families/${id}`, d).then((r) => r.data),
  delete: (id)     => http.delete(`/families/${id}`).then((r) => r.data),
};

// ── Relations API ─────────────────────────────────────────────────────────────

export const relationsApi = {
  /** POST /relations/parent-child */
  addParentChild: (data) =>
    api.post("/relations/parent-child", data).then((r) => r.data),

  /** DELETE /relations/parent-child/{parent_id}/{child_id} */
  removeParentChild: (parentId, childId) =>
    api.delete(`/relations/parent-child/${parentId}/${childId}`).then((r) => r.data),

  /** POST /relations/spouse */
  addSpouse: (data) =>
    api.post("/relations/spouse", data).then((r) => r.data),

  /** POST /relations/divorce */
  divorce: (data) =>
    api.post("/relations/divorce", data).then((r) => r.data),

  /** DELETE /relations/spouse/{a}/{b} */
  removeSpouse: (personAId, personBId) =>
    api.delete(`/relations/spouse/${personAId}/${personBId}`).then((r) => r.data),

  /** GET /relations/siblings/{person_id} */
  getSiblings: (personId) =>
    api.get(`/relations/siblings/${personId}`).then((r) => r.data),

  /** GET /relations/family-graph/{family_id} */
  getFamilyGraph: (familyId) =>
    api.get(`/relations/family-graph/${familyId}`).then((r) => r.data),

  /**
   * Добавить сиблинга: создать персону и связать её с теми же родителями что у relative.
   * parentIds берётся из relationMaps — не из person.parent_ids.
   *
   * @param {object}   personPayload  — данные новой персоны
   * @param {string[]} parentIds      — ID родителей relative (из getPersonRelations)
   * @param {string}   relationType   — "BIOLOGICAL" | "ADOPTED" | "STEP"
   * @returns {Promise<object>}       — созданная персона
   */
  addSiblingViaParents: async (personPayload, parentIds, relationType = "BIOLOGICAL") => {
    const newPerson = await personsApi.create(personPayload);
    if (parentIds.length === 0) {
      // Нет родителей — просто создаём персону без связей
      return newPerson;
    }
    await Promise.all(
      parentIds.map((pid) =>
        relationsApi.addParentChild({
          parent_id:     pid,
          child_id:      newPerson.id,
          relation_type: relationType,
        })
      )
    );
    return newPerson;
  },
};

// ── Composite operations ──────────────────────────────────────────────────────

/**
 * Создать персону и сразу назначить её ребёнком parentId.
 */
export async function createPersonAsChild(personPayload, parentId) {
  const person = await personsApi.create(personPayload);
  await relationsApi.addParentChild({
    parent_id:     parentId,
    child_id:      person.id,
    relation_type: "BIOLOGICAL",
  });
  return person;
}

/**
 * Создать персону и сразу назначить её супругом personId.
 */
export async function createPersonAsSpouse(personPayload, personId) {
  const person = await personsApi.create(personPayload);
  await relationsApi.addSpouse({
    person_a_id:    personId,
    person_b_id:    person.id,
    marriage_status: "MARRIED",
  });
  return person;
}

/**
 * Загрузить полное дерево семьи:
 * 1. GET /families/{id}
 * 2. GET /relations/family-graph/{id}   → graph.nodes + graph.edges + meta
 * 3. Строим relationMaps из edges
 * 4. Возвращаем { family, graph, nodes, relationMaps }
 *
 * nodes = graph.nodes — содержат generation, first_name, last_name, gender,
 * is_alive, birth_year, death_year, birth_date_raw. Используются как "members"
 * везде в UI (TreeCanvas, PersonSidebar, TreeConnections).
 *
 * persons (list) больше не нужен для отображения — только для CRUD-операций.
 */
export async function loadFamilyTree(familyId) {
  const [family, graph] = await Promise.all([
    familiesApi.get(familyId),
    relationsApi.getFamilyGraph(familyId),
  ]);

  const relationMaps = buildRelationMaps(graph);

  return {
    family,
    graph,
    nodes:        graph.nodes ?? [],
    relationMaps,
  };
}
