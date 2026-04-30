/**
 * api/index.js
 *
 * Использует authApi из AuthContext — единый axios-инстанс
 * с withCredentials:true и auto-refresh интерцептором.
 * Токены в localStorage/sessionStorage не хранятся.
 */

import { authApi as http } from "@/lib/AuthContext";

// ─── Families ─────────────────────────────────────────────────────────────────

export const familiesApi = {
  list: (params = {}) =>
    http.get("/families/", { params }).then((r) => r.data),

  get: (familyId) =>
    http.get(`/families/${familyId}`).then((r) => r.data),

  create: (data) =>
    http.post("/families/", data).then((r) => r.data),

  update: (familyId, data) =>
    http.put(`/families/${familyId}`, data).then((r) => r.data),

  patch: (familyId, data) =>
    http.patch(`/families/${familyId}`, data).then((r) => r.data),

  delete: (familyId) =>
    http.delete(`/families/${familyId}`).then(() => undefined),
};

// ─── Persons ──────────────────────────────────────────────────────────────────

export const personsApi = {
  list: (params = {}) =>
    http.get("/persons/", { params }).then((r) => r.data),

  async listByFamily(familyId, extra = {}) {
    const page = await this.list({ family_id: familyId, limit: 500, ...extra });
    return page.result ?? [];
  },

  get: (personId) =>
    http.get(`/persons/${personId}`).then((r) => r.data),

  create: (data) =>
    http.post("/persons/", data).then((r) => r.data),

  update: (personId, data) =>
    http.put(`/persons/${personId}`, data).then((r) => r.data),

  patch: (personId, data) =>
    http.patch(`/persons/${personId}`, data).then((r) => r.data),

  delete: (personId) =>
    http.delete(`/persons/${personId}`).then(() => undefined),
};

// ─── Relations ────────────────────────────────────────────────────────────────

export const relationsApi = {
  addParentChild: (data) =>
    http.post("/relations/parent-child", data).then((r) => r.data),

  removeParentChild: (parentId, childId) =>
    http.delete(`/relations/parent-child/${parentId}/${childId}`).then(() => undefined),

  addSpouse: (data) =>
    http.post("/relations/spouses", data).then((r) => r.data),

  divorce: (data) =>
    http.post("/relations/spouses/divorce", data).then((r) => r.data),

  removeSpouse: (personAId, personBId) =>
    http.delete(`/relations/spouses/${personAId}/${personBId}`).then(() => undefined),

  getGraph: (familyId) =>
    http.get(`/relations/graph/${familyId}`).then((r) => r.data),
};

// ─── High-level helpers ───────────────────────────────────────────────────────

export async function loadFamilyTree(familyId) {
  const [family, persons, graph] = await Promise.all([
    familiesApi.get(familyId),
    personsApi.listByFamily(familyId),
    relationsApi.getGraph(familyId),
  ]);
  return { family, persons, graph };
}

export async function createPersonAsChild(personData, parentId, relationType = "BIOLOGICAL") {
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
