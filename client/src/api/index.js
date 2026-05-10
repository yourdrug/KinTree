/**
 * api/index.js
 */

import { http } from "@/api/client";
import { ENDPOINTS as EP } from "@/api/endpoints";

// ─── Helpers ───────────────────────────────────────────────────────────────────

export function toPartialDate(value) {
  if (!value) return null;
  // Пустая строка — не дата
  if (typeof value === "string" && value.trim() === "") return null;
  if (typeof value === "object" && "year" in value) return value;
  if (typeof value === "string" && value.includes("-")) {
    const [year, month, day] = value.split("-").map(Number);
    return { year: year || null, month: month || null, day: day || null };
  }
  const year = Number(value);
  return isNaN(year) ? null : { year, month: null, day: null };
}

export function fromPartialDate(pd) {
  if (!pd) return "";
  if (typeof pd === "string") return pd;
  const { year, month, day } = pd;
  if (!year) return "";
  const mm = String(month || 1).padStart(2, "0");
  const dd = String(day || 1).padStart(2, "0");
  return `${year}-${mm}-${dd}`;
}

export function formatPartialDate(pd) {
  if (!pd) return null;
  if (typeof pd === "string") return pd;
  const { year, month, day } = pd;
  if (!year) return null;
  if (!month) return String(year);
  const date = new Date(year, month - 1, day || 1);
  const opts = day
    ? { day: "numeric", month: "long", year: "numeric" }
    : { month: "long", year: "numeric" };
  return date.toLocaleDateString("ru-RU", opts);
}

// ─── Families ──────────────────────────────────────────────────────────────────

export const familiesApi = {
  list: (params = {}) =>
    http.get(EP.families.list(), { params }).then((r) => r.data),

  get: (familyId) =>
    http.get(EP.families.get(familyId)).then((r) => r.data),

  create: (data) =>
    http.post(EP.families.create(), data).then((r) => r.data),

  update: (familyId, data) =>
    http.put(EP.families.update(familyId), data).then((r) => r.data),

  patch: (familyId, data) =>
    http.patch(EP.families.patch(familyId), data).then((r) => r.data),

  delete: (familyId) =>
    http.delete(EP.families.delete(familyId)).then(() => undefined),
};

// ─── Persons ───────────────────────────────────────────────────────────────────

/**
 * Whitelist допустимых полей для CREATE/UPDATE.
 * Только то что принимает сервер в CreatePersonRequest / UpdatePersonRequest.
 */
const PERSON_API_FIELDS = new Set([
  "gender",
  "family_id",
  "first_name",
  "last_name",
  "birth_date",
  "death_date",
  "birth_date_raw",
  "death_date_raw",
]);

function normalizePersonPayload(data) {
  const payload = {
    gender:         data.gender || "MALE",
    family_id:      data.family_id,
    first_name:     data.first_name || null,
    last_name:      data.last_name  || null,
    birth_date:     toPartialDate(data.birth_date),
    death_date:     toPartialDate(data.death_date),
    birth_date_raw: data.birth_date_raw || null,
    death_date_raw: data.death_date_raw || null,
  };

  // Убираем null-значения
  if (!payload.birth_date)     delete payload.birth_date;
  if (!payload.death_date)     delete payload.death_date;
  if (!payload.birth_date_raw) delete payload.birth_date_raw;
  if (!payload.death_date_raw) delete payload.death_date_raw;
  if (!payload.family_id)      delete payload.family_id;

  return payload;
}

/**
 * FIX: PATCH использует whitelist вместо blacklist.
 * Только поля из PERSON_API_FIELDS попадают в запрос.
 * Это гарантирует что клиентские поля (is_alive, spouse_ids, child_ids и т.д.)
 * никогда не попадут на сервер.
 */
function buildPatchPayload(data) {
  const patch = {};

  // Берём только разрешённые поля
  for (const key of PERSON_API_FIELDS) {
    if (!(key in data)) continue;
    if (key === "family_id") continue; // никогда не патчим family_id

    let value = data[key];

    // Нормализуем даты
    if (key === "birth_date" || key === "death_date") {
      value = toPartialDate(value);
      if (!value) continue; // не отправляем null даты в PATCH
    }

    if (value !== null && value !== undefined) {
      patch[key] = value;
    }
  }

  return patch;
}

export const personsApi = {
  list: (params = {}) =>
    http.get(EP.persons.list(), { params }).then((r) => r.data),

  async listByFamily(familyId, extra = {}) {
    const page = await this.list({ family_id: familyId, limit: 500, ...extra });
    return page.result ?? [];
  },

  get: (personId) =>
    http.get(EP.persons.get(personId)).then((r) => r.data),

  create: (data) => {
    const payload = normalizePersonPayload(data);
    return http.post(EP.persons.create(), payload).then((r) => r.data);
  },

  update: (personId, data) => {
    const payload = normalizePersonPayload(data);
    delete payload.family_id;
    return http.put(EP.persons.update(personId), payload).then((r) => r.data);
  },

  // FIX: используем whitelist вместо удаления конкретных полей
  patch: (personId, data) => {
    const patch = buildPatchPayload(data);
    return http.patch(EP.persons.patch(personId), patch).then((r) => r.data);
  },

  delete: (personId) =>
    http.delete(EP.persons.delete(personId)).then(() => undefined),
};

// ─── Relations ─────────────────────────────────────────────────────────────────

export const relationsApi = {
  getGraph: (familyId) =>
    http.get(EP.relations.graph(familyId)).then((r) => r.data),

  addParentChild: (data) =>
    http.post(EP.relations.parentChild(), data).then((r) => r.data),

  removeParentChild: (parentId, childId) =>
    http.delete(EP.relations.removeParentChild(parentId, childId)).then(() => undefined),

  addSpouse: (data) =>
    http.post(EP.relations.spouses(), data).then((r) => r.data),

  divorce: (data) =>
    http.post(EP.relations.divorce(), data).then((r) => r.data),

  removeSpouse: (personAId, personBId) =>
    http.delete(EP.relations.removeSpouse(personAId, personBId)).then(() => undefined),
};

// ─── High-level helpers ────────────────────────────────────────────────────────

export async function loadFamilyTree(familyId) {
  const [family, personsPage, graph] = await Promise.all([
    familiesApi.get(familyId),
    personsApi.list({ family_id: familyId, limit: 500 }),
    relationsApi.getGraph(familyId),
  ]);

  const rawPersons = personsPage.result ?? [];
  const enriched = enrichPersonsFromGraph(rawPersons, graph);

  return { family, persons: enriched, graph };
}

export function enrichPersonsFromGraph(persons, graph) {
  if (!graph) return persons;

  const parentChildEdges = (graph.edges || []).filter((e) => e.type === "parent_child");
  const spouseEdges = (graph.edges || []).filter((e) => e.type === "spouse");

  const parentIds = {};
  const childIds = {};
  parentChildEdges.forEach(({ source_id, target_id }) => {
    if (!parentIds[target_id]) parentIds[target_id] = [];
    parentIds[target_id].push(source_id);
    if (!childIds[source_id]) childIds[source_id] = [];
    childIds[source_id].push(target_id);
  });

  const spouseMap = {};
  spouseEdges.forEach(({ source_id, target_id }) => {
    if (!spouseMap[source_id]) spouseMap[source_id] = [];
    spouseMap[source_id].push(target_id);
    if (!spouseMap[target_id]) spouseMap[target_id] = [];
    spouseMap[target_id].push(source_id);
  });

  const generations = computeGenerations(persons, parentChildEdges);

  return persons.map((p) => ({
    ...p,
    parent_ids: parentIds[p.id] || [],
    child_ids: childIds[p.id] || [],
    spouse_ids: spouseMap[p.id] || [],
    partner_id: (spouseMap[p.id] || [])[0] || null,
    generation: generations[p.id] ?? 0,
  }));
}

function computeGenerations(persons, parentChildEdges) {
  const generations = {};

  const hasParent = new Set(parentChildEdges.map((e) => e.target_id));
  const roots = persons.filter((p) => !hasParent.has(p.id));

  const queue = roots.map((r) => ({ id: r.id, gen: 0 }));
  const visited = new Set();

  const childMap = {};
  parentChildEdges.forEach(({ source_id, target_id }) => {
    if (!childMap[source_id]) childMap[source_id] = [];
    childMap[source_id].push(target_id);
  });

  while (queue.length > 0) {
    const { id, gen } = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);
    generations[id] = gen;
    (childMap[id] || []).forEach((childId) => {
      if (!visited.has(childId)) queue.push({ id: childId, gen: gen + 1 });
    });
  }

  persons.forEach((p) => {
    if (!(p.id in generations)) generations[p.id] = 0;
  });

  return generations;
}

export async function createPersonAsChild(personData, parentId) {
  const person = await personsApi.create(personData);
  await relationsApi.addParentChild({
    parent_id: parentId,
    child_id: person.id,
    relation_type: "BIOLOGICAL",
  });
  return person;
}

export async function createPersonAsSpouse(personData, partnerId) {
  const person = await personsApi.create(personData);
  await relationsApi.addSpouse({
    person_a_id: person.id,
    person_b_id: partnerId,
    marriage_status: "MARRIED",
  });
  return person;
}
