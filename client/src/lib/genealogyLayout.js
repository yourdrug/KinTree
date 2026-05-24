/**
 * lib/genealogyLayout.js
 *
 * Алгоритм layout для генеалогического дерева.
 *
 * Поколения берутся напрямую из API (node.generation) — бэкенд
 * уже вычислил их через bottom-up alignment (generation_calculator.py).
 * Фронт не пересчитывает поколения самостоятельно.
 *
 * Логика позиционирования:
 *  1. Группируем ноды по generation (строки)
 *  2. Супружеские пары всегда рядом на одной строке
 *  3. Дети центрируются под своими родителями
 *  4. Рекурсивно разрешаем перекрытия через сдвиги
 *
 * Входные данные: nodes[], edges[] — те же, что приходят из API.
 * Выходные данные: Map<id, {x, y}>
 */

const NODE_W   = 140;   // ширина карточки
const NODE_H   = 100;   // высота карточки
const H_GAP    = 32;    // горизонтальный зазор между нодами
const PAIR_GAP = 16;    // зазор внутри супружеской пары (теснее)
const V_GAP    = 100;   // вертикальный зазор между поколениями

// ─────────────────────────────────────────────────────────────────────────────

export function computeGenealogyLayout(nodes, edges) {
  if (!nodes?.length) return new Map();

  // Индексы
  const spouseOf    = new Map();   // id → Set<id>
  const parentsOf   = new Map();   // child_id → Set<parent_id>
  const childrenOf  = new Map();   // parent_id → Set<child_id>

  for (const n of nodes) {
    spouseOf  .set(n.id, new Set());
    parentsOf .set(n.id, new Set());
    childrenOf.set(n.id, new Set());
  }

  for (const e of edges) {
    if (e.type === "spouse") {
      spouseOf.get(e.source_id)?.add(e.target_id);
      spouseOf.get(e.target_id)?.add(e.source_id);
    }
    if (e.type === "parent_child") {
      parentsOf .get(e.target_id)?.add(e.source_id);
      childrenOf.get(e.source_id)?.add(e.target_id);
    }
  }

  // ── 1. Используем generation из API ──────────────────────────────────────
  // Бэкенд уже вычислил корректные поколения через bottom-up alignment.
  // Нода без generation (null) получает fallback = 0.
  const generation = new Map();
  for (const n of nodes) {
    generation.set(n.id, n.generation ?? 0);
  }

  // ── 2. Сгруппировать в супружеские пары ──────────────────────────────────
  const paired      = new Set();
  const pairsPerGen = new Map();  // gen → Pair[]

  for (const n of nodes) {
    if (paired.has(n.id)) continue;
    const gen     = generation.get(n.id);
    const spouses = [...(spouseOf.get(n.id) ?? [])].filter(
      sid => generation.get(sid) === gen
    );

    const pair = { primary: n.id, spouse: spouses[0] ?? null };
    paired.add(n.id);
    if (pair.spouse) paired.add(pair.spouse);

    if (!pairsPerGen.has(gen)) pairsPerGen.set(gen, []);
    pairsPerGen.get(gen).push(pair);
  }

  // ── 3. Рекурсивный layout ─────────────────────────────────────────────────
  const positions = new Map();
  const gens      = [...pairsPerGen.keys()].sort((a, b) => a - b);

  const genY = gen => gen * (NODE_H + V_GAP);

  function subtreeWidth(id, visitedInCall = new Set()) {
    if (visitedInCall.has(id)) return NODE_W;
    visitedInCall.add(id);

    const children = [...(childrenOf.get(id) ?? [])];
    const spouse   = [...(spouseOf.get(id) ?? [])][0] ?? null;

    if (!children.length) {
      return spouse ? NODE_W * 2 + PAIR_GAP : NODE_W;
    }

    const childWidths  = children.map(c => subtreeWidth(c, new Set(visitedInCall)));
    const totalChildren = childWidths.reduce((a, b) => a + b, 0)
      + (children.length - 1) * H_GAP;

    const selfWidth = spouse ? NODE_W * 2 + PAIR_GAP : NODE_W;

    return Math.max(selfWidth, totalChildren);
  }

  function placeNode(id, centerX, gen, visited = new Set()) {
    if (visited.has(id)) return;
    visited.add(id);

    const y      = genY(gen);
    const spouse = [...(spouseOf.get(id) ?? [])].find(
      sid => generation.get(sid) === gen && !visited.has(sid)
    ) ?? null;

    if (spouse) {
      const pairW    = NODE_W * 2 + PAIR_GAP;
      const pairLeft = centerX - pairW / 2;
      positions.set(id,     { x: pairLeft,                       y });
      positions.set(spouse, { x: pairLeft + NODE_W + PAIR_GAP,   y });
      visited.add(spouse);
    } else {
      positions.set(id, { x: centerX - NODE_W / 2, y });
    }

    const myChildren     = [...(childrenOf.get(id) ?? [])];
    const spouseChildren = spouse ? [...(childrenOf.get(spouse) ?? [])] : [];
    const allChildren    = [...new Set([...myChildren, ...spouseChildren])];

    if (!allChildren.length) return;

    const childWidths = allChildren.map(c => subtreeWidth(c));
    const totalW = childWidths.reduce((a, b) => a + b, 0)
      + (allChildren.length - 1) * H_GAP;

    let childX    = centerX - totalW / 2;
    const childGen = gen + 1;

    for (let i = 0; i < allChildren.length; i++) {
      const cid     = allChildren[i];
      const cw      = childWidths[i];
      const cCenter = childX + cw / 2;
      placeNode(cid, cCenter, childGen, visited);
      childX += cw + H_GAP;
    }
  }

  // Размещаем корни
  // Вычисляем общую ширину всех корневых поддеревьев
  const rootPairs = pairsPerGen.get(Math.min(...gens)) ?? [];
  const rootIds   = rootPairs.map(p => p.primary);

  const rootWidths = rootIds.map(id => subtreeWidth(id));
  const totalRootW = rootWidths.reduce((a, b) => a + b, 0)
    + (rootIds.length - 1) * H_GAP;

  let rootX   = -totalRootW / 2;
  const visited = new Set();

  for (let i = 0; i < rootIds.length; i++) {
    const rid = rootIds[i];
    const rw  = rootWidths[i];
    placeNode(rid, rootX + rw / 2, generation.get(rid) ?? 0, visited);
    rootX += rw + H_GAP;
  }

  // Ноды без позиции (изолированные или циклы)
  let fallbackX = 0;
  for (const n of nodes) {
    if (!positions.has(n.id)) {
      positions.set(n.id, { x: fallbackX, y: genY(generation.get(n.id) ?? 0) });
      fallbackX += NODE_W + H_GAP;
    }
  }

  return positions;
}
