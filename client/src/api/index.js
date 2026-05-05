/**
 * api/index.js
 *
 * Все API-вызовы приложения.
 * Использует ENDPOINTS для URL — никаких строк вручную.
 *
 * Структура каждого метода:
 *   http.<method>(EP.<resource>.<action>(...params), data?)
 *     .then(r => r.data)
 *
 * Компоненты и хуки импортируют отсюда — никогда напрямую из http.
 */

import { http } from "@/api/client";
import { ENDPOINTS as EP } from "@/api/endpoints";

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

export const personsApi = {
  list: (params = {}) =>
    http.get(EP.persons.list(), { params }).then((r) => r.data),

  async listByFamily(familyId, extra = {}) {
    const page = await this.list({ family_id: familyId, limit: 500, ...extra });
    return page.result ?? [];
  },

  get: (personId) =>
    http.get(EP.persons.get(personId)).then((r) => r.data),

  create: (data) =>
    http.post(EP.persons.create(), data).then((r) => r.data),

  update: (personId, data) =>
    http.put(EP.persons.update(personId), data).then((r) => r.data),

  patch: (personId, data) =>
    http.patch(EP.persons.patch(personId), data).then((r) => r.data),

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
  const [family, persons, graph] = await Promise.all([
    familiesApi.get(familyId),
    personsApi.listByFamily(familyId),
    relationsApi.getGraph(familyId),
  ]);
  return { family, persons, graph };
}

export async function createPersonAsChild(
  personData,
  parentId,
  relationType = "BIOLOGICAL"
) {
  const person = await personsApi.create(personData);
  await relationsApi.addParentChild({
    parent_id: parentId,
    child_id: person.id,
    relation_type: relationType,
  });
  return person;
}

export async function createPersonAsSpouse(personData, partnerId, marriageData = {}) {
  const person = await personsApi.create(personData);
  await relationsApi.addSpouse({
    person_a_id: person.id,
    person_b_id: partnerId,
    marriage_status: "MARRIED",
    ...marriageData,
  });
  return person;
}
