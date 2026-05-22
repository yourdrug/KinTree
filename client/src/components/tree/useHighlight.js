/**
 * components/tree/useHighlight.js
 *
 * Хук: вычисляет подсветку узлов и рёбер при наведении.
 *
 * Возвращает:
 *   hoveredId          — ID узла под курсором (null если нет)
 *   getNodeRole(id)    — "hovered"|"parent"|"child"|"spouse"|"sibling"|"dimmed"|null
 *   getEdgeHighlight(edge) — "active"|"dimmed"|null
 *   onNodeMouseEnter(id)
 *   onNodeMouseLeave()
 *
 * Логика dimmed:
 *   Если hoveredId != null и узел не является родственником — он dimmed.
 *   Рёбра между нерелевантными узлами — dimmed.
 *   Рёбра между hoveredId и его родственниками — active.
 */

import { useState, useCallback, useMemo } from "react";

/**
 * Вычисляет карту ролей для всех узлов при hover на hoveredId.
 *
 * @param {string|null}  hoveredId
 * @param {EdgeDTO[]}    edges
 * @returns {Map<string, "hovered"|"parent"|"child"|"spouse"|"sibling">}
 *          Только узлы с ролью (не-dimmed). Остальные — dimmed.
 */
function computeRoleMap(hoveredId, edges) {
  const roles = new Map();
  if (!hoveredId || !edges?.length) return roles;

  roles.set(hoveredId, "hovered");

  for (const edge of edges) {
    switch (edge.type) {
      case "parent_child":
        // source = родитель, target = ребёнок
        if (edge.target_id === hoveredId) {
          // hoveredId — ребёнок → source — родитель
          if (!roles.has(edge.source_id)) roles.set(edge.source_id, "parent");
        }
        if (edge.source_id === hoveredId) {
          // hoveredId — родитель → target — ребёнок
          if (!roles.has(edge.target_id)) roles.set(edge.target_id, "child");
        }
        break;

      case "spouse":
        if (edge.source_id === hoveredId) {
          if (!roles.has(edge.target_id)) roles.set(edge.target_id, "spouse");
        }
        if (edge.target_id === hoveredId) {
          if (!roles.has(edge.source_id)) roles.set(edge.source_id, "spouse");
        }
        break;

      case "sibling":
        if (edge.source_id === hoveredId) {
          if (!roles.has(edge.target_id)) roles.set(edge.target_id, "sibling");
        }
        if (edge.target_id === hoveredId) {
          if (!roles.has(edge.source_id)) roles.set(edge.source_id, "sibling");
        }
        break;

      default:
        break;
    }
  }

  return roles;
}

/**
 * Определяет, является ли ребро "активным" при данном hover:
 * ребро активно если оба его участника имеют роль (не dimmed).
 */
function isEdgeActive(edge, roleMap) {
  if (!roleMap.size) return false;
  return roleMap.has(edge.source_id) && roleMap.has(edge.target_id);
}

export function useHighlight(edges) {
  const [hoveredId, setHoveredId] = useState(null);

  const roleMap = useMemo(
    () => computeRoleMap(hoveredId, edges),
    [hoveredId, edges]
  );

  const onNodeMouseEnter = useCallback((id) => {
    setHoveredId(id);
  }, []);

  const onNodeMouseLeave = useCallback(() => {
    setHoveredId(null);
  }, []);

  /**
   * Возвращает роль узла при текущем hover:
   *   "hovered"  — сам узел
   *   "parent"   — родитель hoveredId
   *   "child"    — ребёнок hoveredId
   *   "spouse"   — супруг hoveredId
   *   "sibling"  — брат/сестра hoveredId
   *   "dimmed"   — нет связи с hoveredId
   *   null       — hover не активен
   */
  const getNodeRole = useCallback(
    (id) => {
      if (!hoveredId) return null;
      return roleMap.get(id) ?? "dimmed";
    },
    [hoveredId, roleMap]
  );

  /**
   * Возвращает статус ребра:
   *   "active"  — соединяет hoveredId с родственником
   *   "dimmed"  — не связан с hoveredId
   *   null      — hover не активен
   */
  const getEdgeHighlight = useCallback(
    (edge) => {
      if (!hoveredId) return null;
      return isEdgeActive(edge, roleMap) ? "active" : "dimmed";
    },
    [hoveredId, roleMap]
  );

  return {
    hoveredId,
    getNodeRole,
    getEdgeHighlight,
    onNodeMouseEnter,
    onNodeMouseLeave,
  };
}
