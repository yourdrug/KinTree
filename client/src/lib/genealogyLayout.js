/**
 * lib/genealogyLayout.js
 *
 * Алгоритм layout для генеалогического дерева.
 *
 * Исправления v2:
 *  - subtreeWidth корректно считает ширину пары (оба супруга вместе)
 *  - супруги всегда объединяются в пару независимо от порядка обхода корней
 *  - фиксированный размер нод (NODE_W × NODE_H) во всех местах
 *  - resolveOverlaps — финальный проход, раздвигает пересекающиеся ноды одного поколения
 */

const NODE_W   = 140;
const NODE_H   = 100;
const H_GAP    = 40;   // горизонтальный зазор между независимыми поддеревьями
const PAIR_GAP = 20;   // зазор внутри супружеской пары
const V_GAP    = 100;  // вертикальный зазор между поколениями

// ─────────────────────────────────────────────────────────────────────────────

export function computeGenealogyLayout(nodes, edges) {
  if (!nodes?.length) return new Map();

  // ── Индексы ───────────────────────────────────────────────────────────────
  const spouseOf   = new Map(); // id → Set<id>
  const parentsOf  = new Map(); // child_id → Set<parent_id>
  const childrenOf = new Map(); // parent_id → Set<child_id>
  const genMap     = new Map(); // id → generation (из API)

  for (const n of nodes) {
    spouseOf  .set(n.id, new Set());
    parentsOf .set(n.id, new Set());
    childrenOf.set(n.id, new Set());
    genMap    .set(n.id, n.generation ?? 0);
  }

  for (const e of edges) {
    if (e.type === 'spouse') {
      spouseOf.get(e.source_id)?.add(e.target_id);
      spouseOf.get(e.target_id)?.add(e.source_id);
    }
    if (e.type === 'parent_child') {
      parentsOf .get(e.target_id)?.add(e.source_id);
      childrenOf.get(e.source_id)?.add(e.target_id);
    }
  }

  // ── Супружеские пары ──────────────────────────────────────────────────────
  // Каждая пара: { primary, spouse|null }
  // Один человек входит ровно в одну пару.
  const paired = new Set();
  const pairs  = []; // все пары, упорядочены по generation затем по первому появлению

  for (const n of nodes) {
    if (paired.has(n.id)) continue;
    const gen = genMap.get(n.id);
    const spouseId = [...(spouseOf.get(n.id) ?? [])]
      .find(sid => genMap.get(sid) === gen && !paired.has(sid)) ?? null;

    pairs.push({ primary: n.id, spouse: spouseId, gen });
    paired.add(n.id);
    if (spouseId) paired.add(spouseId);
  }

  // ── Вычисление ширины поддерева ───────────────────────────────────────────
  // Ширина поддерева с корнем в `id` — максимум из:
  //   (a) ширина самой пары (id + супруг если есть)
  //   (b) суммарная ширина всех детей пары
  //
  // visited предотвращает зацикливание при ромбовидных графах
  const widthCache = new Map();

  function pairWidth(id) {
    const gen = genMap.get(id);
    const spouse = [...(spouseOf.get(id) ?? [])]
      .find(sid => genMap.get(sid) === gen) ?? null;
    return spouse ? NODE_W * 2 + PAIR_GAP : NODE_W;
  }

  function subtreeWidth(id, visited = new Set()) {
    if (widthCache.has(id)) return widthCache.get(id);
    if (visited.has(id)) return pairWidth(id);
    visited.add(id);

    const gen    = genMap.get(id);
    const spouse = [...(spouseOf.get(id) ?? [])]
      .find(sid => genMap.get(sid) === gen) ?? null;

    // Дети обоих супругов (уникальные)
    const myChildren     = [...(childrenOf.get(id)     ?? [])];
    const spouseChildren = spouse ? [...(childrenOf.get(spouse) ?? [])] : [];
    const allChildren    = [...new Set([...myChildren, ...spouseChildren])];

    const selfW = pairWidth(id);

    if (allChildren.length === 0) {
      widthCache.set(id, selfW);
      return selfW;
    }

    // Ширина блока детей — сумма их поддеревьев + зазоры
    const childrenW = allChildren.reduce((acc, cid, i) => {
      return acc + subtreeWidth(cid, new Set(visited)) + (i > 0 ? H_GAP : 0);
    }, 0);

    const w = Math.max(selfW, childrenW);
    widthCache.set(id, w);
    return w;
  }

  // ── Рекурсивное размещение ────────────────────────────────────────────────
  const positions = new Map();

  function placeSubtree(id, centerX, visited = new Set()) {
    if (visited.has(id)) return;
    visited.add(id);

    const gen    = genMap.get(id);
    const y      = gen * (NODE_H + V_GAP);
    const spouse = [...(spouseOf.get(id) ?? [])]
      .find(sid => genMap.get(sid) === gen && !visited.has(sid)) ?? null;

    // Размещаем пару
    if (spouse) {
      const totalPairW = NODE_W * 2 + PAIR_GAP;
      const left = centerX - totalPairW / 2;
      positions.set(id,     { x: left,                    y });
      positions.set(spouse, { x: left + NODE_W + PAIR_GAP, y });
      visited.add(spouse);
    } else {
      positions.set(id, { x: centerX - NODE_W / 2, y });
    }

    // Дети
    const myChildren     = [...(childrenOf.get(id)     ?? [])];
    const spouseChildren = spouse ? [...(childrenOf.get(spouse) ?? [])] : [];
    const allChildren    = [...new Set([...myChildren, ...spouseChildren])];

    if (allChildren.length === 0) return;

    const childWidths = allChildren.map(cid => subtreeWidth(cid));
    const totalChildW = childWidths.reduce((a, b) => a + b, 0)
      + (allChildren.length - 1) * H_GAP;

    let x = centerX - totalChildW / 2;
    for (let i = 0; i < allChildren.length; i++) {
      const cid = allChildren[i];
      if (!visited.has(cid)) {
        placeSubtree(cid, x + childWidths[i] / 2, visited);
      }
      x += childWidths[i] + H_GAP;
    }
  }

  // ── Корневые ноды: те, у кого нет родителей ───────────────────────────────
  // Важно: если оба супруга — корни, берём только одного из пары (primary)
  const rootIds = [];
  const rootSeen = new Set();

  for (const n of nodes) {
    if ((parentsOf.get(n.id)?.size ?? 0) > 0) continue; // есть родители — не корень
    // Найти primary этой пары
    const gen = genMap.get(n.id);
    const spouse = [...(spouseOf.get(n.id) ?? [])].find(sid => genMap.get(sid) === gen);
    const primary = spouse && !rootSeen.has(spouse) ? n.id : n.id;
    if (!rootSeen.has(n.id)) {
      rootIds.push(primary);
      rootSeen.add(n.id);
      if (spouse) rootSeen.add(spouse);
    }
  }

  // Сортируем корни по generation (возрастание), затем стабильно
  rootIds.sort((a, b) => (genMap.get(a) ?? 0) - (genMap.get(b) ?? 0));

  // Вычисляем общую ширину корневых поддеревьев
  const rootWidths = rootIds.map(id => subtreeWidth(id));
  const totalRootW = rootWidths.reduce((a, b) => a + b, 0)
    + (rootIds.length - 1) * H_GAP;

  const visited = new Set();
  let x = -totalRootW / 2;

  for (let i = 0; i < rootIds.length; i++) {
    placeSubtree(rootIds[i], x + rootWidths[i] / 2, visited);
    x += rootWidths[i] + H_GAP;
  }

  // ── Fallback для изолированных нод ────────────────────────────────────────
  let fallbackX = 0;
  for (const n of nodes) {
    if (!positions.has(n.id)) {
      const y = (genMap.get(n.id) ?? 0) * (NODE_H + V_GAP);
      positions.set(n.id, { x: fallbackX, y });
      fallbackX += NODE_W + H_GAP;
    }
  }

  // ── Финальный проход: устранение перекрытий внутри поколения ─────────────
  // Группируем по generation и раздвигаем пересекающиеся карточки
  const byGen = new Map();
  for (const [id, pos] of positions) {
    const gen = genMap.get(id) ?? 0;
    if (!byGen.has(gen)) byGen.set(gen, []);
    byGen.get(gen).push({ id, pos });
  }

  for (const [, items] of byGen) {
    // Сортируем по x
    items.sort((a, b) => a.pos.x - b.pos.x);
    for (let i = 1; i < items.length; i++) {
      const prev = items[i - 1];
      const curr = items[i];
      const minX = prev.pos.x + NODE_W + H_GAP;
      if (curr.pos.x < minX) {
        const shift = minX - curr.pos.x;
        // Сдвигаем все ноды начиная с curr вправо
        for (let j = i; j < items.length; j++) {
          items[j].pos.x += shift;
          positions.set(items[j].id, { ...items[j].pos });
        }
      }
    }
  }

  return positions;
}
