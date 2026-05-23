/**
 * lib/genealogyLayout.js
 *
 * Кастомный алгоритм layout для генеалогического дерева.
 *
 * Логика:
 *  1. Определяем поколение каждой ноды (BFS от корней)
 *  2. Супружеские пары всегда стоят рядом на одной строке
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

  // ── 1. Определить поколения (BFS) ────────────────────────────────────────
  const generation = new Map();   // id → number

  // Корни — ноды без родителей
  const roots = nodes.filter(n => parentsOf.get(n.id).size === 0);
  if (!roots.length) roots.push(nodes[0]);   // защита

  const queue = [...roots.map(r => ({ id: r.id, gen: 0 }))];
  while (queue.length) {
    const { id, gen } = queue.shift();
    if (generation.has(id)) continue;
    generation.set(id, gen);

    // Супруги — то же поколение
    for (const sid of spouseOf.get(id) ?? []) {
      if (!generation.has(sid)) queue.push({ id: sid, gen });
    }
    // Дети — следующее поколение
    for (const cid of childrenOf.get(id) ?? []) {
      if (!generation.has(cid)) queue.push({ id: cid, gen: gen + 1 });
    }
  }

  // Ноды без поколения (изолированные) — ставим в конец
  for (const n of nodes) {
    if (!generation.has(n.id)) generation.set(n.id, 0);
  }

  // ── 2. Сгруппировать в супружеские пары ──────────────────────────────────
  // Пара = { primary, spouse|null }
  const paired    = new Set();
  const pairsPerGen = new Map();  // gen → Pair[]

  for (const n of nodes) {
    if (paired.has(n.id)) continue;
    const gen      = generation.get(n.id);
    const spouses  = [...(spouseOf.get(n.id) ?? [])].filter(
      sid => generation.get(sid) === gen
    );

    const pair = { primary: n.id, spouse: spouses[0] ?? null };
    paired.add(n.id);
    if (pair.spouse) paired.add(pair.spouse);

    if (!pairsPerGen.has(gen)) pairsPerGen.set(gen, []);
    pairsPerGen.get(gen).push(pair);
  }

  // ── 3. Рекурсивный layout ─────────────────────────────────────────────────
  // positions: id → {x, y}  (x — левый край ноды)
  const positions = new Map();

  // Сортируем поколения
  const gens = [...pairsPerGen.keys()].sort((a, b) => a - b);

  // Для каждого поколения — вычисляем y
  const genY = gen => gen * (NODE_H + V_GAP);

  // Стартуем с нулевого поколения, размещаем пары последовательно
  // Потом корректируем x так, чтобы каждая пара центрировалась над детьми,
  // а дети — между родителями.

  // Сначала — bottom-up: вычислить "минимальную ширину" поддерева
  function subtreeWidth(id, visitedInCall = new Set()) {
    if (visitedInCall.has(id)) return NODE_W;
    visitedInCall.add(id);

    const children = [...(childrenOf.get(id) ?? [])];
    const spouse   = [...(spouseOf.get(id) ?? [])][0] ?? null;

    if (!children.length) {
      // Листовая нода: ширина = 1 нода (+ супруг если есть)
      return spouse ? NODE_W * 2 + PAIR_GAP : NODE_W;
    }

    // Ширина = сумма ширин детей + зазоры
    const childWidths = children.map(c => subtreeWidth(c, new Set(visitedInCall)));
    const totalChildren = childWidths.reduce((a, b) => a + b, 0)
      + (children.length - 1) * H_GAP;

    const selfWidth = spouse ? NODE_W * 2 + PAIR_GAP : NODE_W;

    return Math.max(selfWidth, totalChildren);
  }

  // Top-down размещение
  function placeNode(id, centerX, gen, visited = new Set()) {
    if (visited.has(id)) return;
    visited.add(id);

    const y      = genY(gen);
    const spouse = [...(spouseOf.get(id) ?? [])].find(
      sid => generation.get(sid) === gen && !visited.has(sid)
    ) ?? null;

    if (spouse) {
      // Пара: primary слева, spouse справа, центр = centerX
      const pairW = NODE_W * 2 + PAIR_GAP;
      const pairLeft = centerX - pairW / 2;
      positions.set(id,     { x: pairLeft,              y });
      positions.set(spouse, { x: pairLeft + NODE_W + PAIR_GAP, y });
      visited.add(spouse);
    } else {
      positions.set(id, { x: centerX - NODE_W / 2, y });
    }

    // Дети этой ноды + детей супруга (объединяем)
    const myChildren     = [...(childrenOf.get(id) ?? [])];
    const spouseChildren = spouse ? [...(childrenOf.get(spouse) ?? [])] : [];
    const allChildren    = [...new Set([...myChildren, ...spouseChildren])];

    if (!allChildren.length) return;

    // Вычислить суммарную ширину детей
    const childWidths = allChildren.map(c => subtreeWidth(c));
    const totalW = childWidths.reduce((a, b) => a + b, 0)
      + (allChildren.length - 1) * H_GAP;

    let childX = centerX - totalW / 2;
    const childGen = gen + 1;

    for (let i = 0; i < allChildren.length; i++) {
      const cid   = allChildren[i];
      const cw    = childWidths[i];
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

  let rootX = -totalRootW / 2;
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
      positions.set(n.id, { x: fallbackX, y: 0 });
      fallbackX += NODE_W + H_GAP;
    }
  }

  return positions;
}
