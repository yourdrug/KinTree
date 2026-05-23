/**
 * api/relations.js
 *
 * API отношений между персонами + утилиты для работы с графом.
 */

import { http } from "./http";
import { ENDPOINTS as EP } from "./endpoints";
import { personsApi } from "./persons";

// ── Relations API ─────────────────────────────────────────────────────────────

export const relationsApi = {
  /** GET /relations/family-graph/{familyId} */
  getFamilyGraph: (familyId) =>
    http.get(EP.relations.graph(familyId)).then((r) => r.data),

  addParentChild: (data) =>
    http.post(EP.relations.addParentChild(), data).then((r) => r.data),

  removeParentChild: (parentId, childId) =>
    http.delete(EP.relations.removeParentChild(parentId, childId)).then((r) => r.data),

  addSpouse: (data) =>
    http.post(EP.relations.addSpouse(), data).then((r) => r.data),

  removeSpouse: (idA, idB) =>
    http.delete(EP.relations.removeSpouse(idA, idB)).then((r) => r.data),
};

// ── Composite operations ──────────────────────────────────────────────────────

/** Создать персону и сразу связать как ребёнка parentId */
export async function createPersonAsChild(personPayload, parentId) {
  const person = await personsApi.create(personPayload);
  await relationsApi.addParentChild({
    parent_id: parentId,
    child_id: person.id,
    relation_type: "BIOLOGICAL",
  });
  return person;
}

/** Создать персону и сразу связать как супруга personId */
export async function createPersonAsSpouse(personPayload, personId) {
  const person = await personsApi.create(personPayload);
  await relationsApi.addSpouse({
    person_a_id: personId,
    person_b_id: person.id,
    marriage_status: "MARRIED",
  });
  return person;
}

/**
 * Создать персону-сиблинга через общих родителей.
 * parentIds берётся из relationMaps (не из person.parent_ids — его нет в NodeResponse).
 */
export async function createPersonAsSibling(personPayload, parentIds, relationType = "BIOLOGICAL") {
  const person = await personsApi.create(personPayload);
  if (parentIds.length > 0) {
    await Promise.all(
      parentIds.map((pid) =>
        relationsApi.addParentChild({
          parent_id: pid,
          child_id: person.id,
          relation_type: relationType,
        })
      )
    );
  }
  return person;
}

// ── Graph utilities ───────────────────────────────────────────────────────────

/**
 * Строит per-person карту связей из graph.edges.
 *
 * Это ЕДИНСТВЕННЫЙ способ получить parent_ids/spouse_ids/sibling_ids на клиенте —
 * NodeResponse эти поля не содержит.
 *
 * @returns {Map<string, RelationMap>}
 */
export function buildRelationMaps(graph) {
  const maps = new Map();

  const ensure = (id) => {
    if (!maps.has(id)) {
      maps.set(id, {
        parentIds:         [],
        childIds:          [],
        spouseIds:         [],
        siblingIds:        [],
        siblingTypeMap:    new Map(),
        siblingParentsMap: new Map(),
      });
    }
    return maps.get(id);
  };

  if (!graph?.edges) return maps;

  for (const edge of graph.edges) {
    switch (edge.type) {
      case "parent_child": {
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
 * Получить связи персоны из карты. Возвращает пустую структуру если не найдена.
 */
export function getPersonRelations(relationMaps, personId) {
  return (
    relationMaps?.get(personId) ?? {
      parentIds:         [],
      childIds:          [],
      spouseIds:         [],
      siblingIds:        [],
      siblingTypeMap:    new Map(),
      siblingParentsMap: new Map(),
    }
  );
}

// ── Date utilities ────────────────────────────────────────────────────────────

/**
 * "1990-06-15" → { year: 1990, month: 6, day: 15 }
 * "1990"       → { year: 1990, month: null, day: null }
 * ""           → null
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
 * { year: 1990, month: 6, day: 15 } → "15.06.1990"
 * { year: 1990, month: 6 }          → "06.1990"
 * { year: 1990 }                    → "1990"
 */
export function formatPartialDate(pd) {
  if (!pd || typeof pd !== "object") return "";
  const { year, month, day } = pd;
  if (!year && !month && !day) return "";
  if (day && month && year) {
    return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.${year}`;
  }
  if (month && year) return `${String(month).padStart(2, "0")}.${year}`;
  if (year) return String(year);
  return "";
}

/**
 * Загрузить полное дерево семьи за 2 параллельных запроса.
 */
export async function loadFamilyTree(familyId) {
  const [family, graph] = await Promise.all([
    import("./families").then((m) => m.familiesApi.get(familyId)),
    relationsApi.getFamilyGraph(familyId),
  ]);

  return {
    family,
    graph,
    nodes: graph.nodes ?? [],
    edges: graph.edges ?? [],
    relationMaps: buildRelationMaps(graph),
  };
}
