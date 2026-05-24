/**
 * lib/genealogyLayout.js  v4+spacing
 *
 * v4 (из обновления):
 *  - orderPairByGender: женщина слева, мужчина справа
 *  - buildMarriageBlocks: поддержка нескольких браков
 *  - inferMissingSpouseEdges: экспортируемая утилита для TreeCanvas
 *
 * spacing fix (из исправления расстояний):
 *  - H_GAP  40 → 24
 *  - PAIR_GAP 20 → 16
 *  - V_GAP  100 → 80
 *  - ROOT_GAP = 40 (отдельный зазор между независимыми корневыми поддеревьями)
 */

const NODE_W    = 140;
const NODE_H    = 100;
const H_GAP     = 24;   // зазор между соседними поддеревьями
const PAIR_GAP  = 16;   // зазор внутри супружеской пары
const V_GAP     = 80;   // вертикальный зазор между поколениями
const ROOT_GAP  = 40;   // зазор между независимыми корневыми поддеревьями

// ─────────────────────────────────────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Возвращает {leftId, rightId} для пары с учётом пола:
 *   FEMALE слева, MALE справа.
 *   Если оба одного пола / неизвестно — ведущий слева.
 */
function orderPairByGender(leadId, spouseId, nodeById) {
  const lGender = nodeById.get(leadId)?.gender  ?? null;
  const sGender = nodeById.get(spouseId)?.gender ?? null;

  if (lGender === 'MALE'   && sGender !== 'MALE')   return { leftId: spouseId, rightId: leadId };
  if (lGender === 'FEMALE' && sGender !== 'FEMALE') return { leftId: leadId,   rightId: spouseId };
  if (sGender === 'MALE'   && lGender !== 'MALE')   return { leftId: leadId,   rightId: spouseId };
  if (sGender === 'FEMALE' && lGender !== 'FEMALE') return { leftId: spouseId, rightId: leadId };

  return { leftId: leadId, rightId: spouseId };
}

// ─────────────────────────────────────────────────────────────────────────────
//  Main layout
// ─────────────────────────────────────────────────────────────────────────────

export function computeGenealogyLayout(nodes, edges) {
  if (!nodes?.length) return new Map();

  // ── Индексы ───────────────────────────────────────────────────────────────
  const spousesOf  = new Map(); // id → Set<spouseId>  (все браки)
  const parentsOf  = new Map(); // child_id → Set<parent_id>
  const childrenOf = new Map(); // parent_id → Set<child_id>
  const genMap     = new Map(); // id → generation
  const nodeById   = new Map(); // id → node

  for (const n of nodes) {
    spousesOf .set(n.id, new Set());
    parentsOf .set(n.id, new Set());
    childrenOf.set(n.id, new Set());
    genMap    .set(n.id, n.generation ?? 0);
    nodeById  .set(n.id, n);
  }

  for (const e of edges) {
    if (e.type === 'spouse') {
      spousesOf.get(e.source_id)?.add(e.target_id);
      spousesOf.get(e.target_id)?.add(e.source_id);
    }
    if (e.type === 'parent_child') {
      parentsOf .get(e.target_id)?.add(e.source_id);
      childrenOf.get(e.source_id)?.add(e.target_id);
    }
  }

  // ── Строим супружеские блоки ──────────────────────────────────────────────
  // Блок = { leadId, spouseId|null, children: Set<id> }
  // Один человек может быть lead в нескольких блоках (несколько браков).
  // primaryBlockOf: Map<personId, blockKey> — блок, в котором персона нарисована.

  const blocks         = new Map();
  const processedPairs = new Set();

  for (const n of nodes) {
    const gen = genMap.get(n.id);
    for (const spId of spousesOf.get(n.id) ?? []) {
      if (genMap.get(spId) !== gen) continue;
      const pairKey = [n.id, spId].sort().join('+');
      if (processedPairs.has(pairKey)) continue;
      processedPairs.add(pairKey);

      // Ведущий — у кого больше детей
      const nChildren  = childrenOf.get(n.id)?.size  ?? 0;
      const spChildren = childrenOf.get(spId)?.size   ?? 0;
      const leadId   = (spChildren > nChildren) ? spId : n.id;
      const spouseId = leadId === n.id ? spId : n.id;

      const childSet = new Set([
        ...(childrenOf.get(leadId)   ?? []),
        ...(childrenOf.get(spouseId) ?? []),
      ]);

      blocks.set(pairKey, { leadId, spouseId, children: childSet });
    }

    // Одиночные блоки (без супруга того же поколения)
    const sameGenSpouses = [...(spousesOf.get(n.id) ?? [])].filter(
      s => genMap.get(s) === genMap.get(n.id)
    );
    if (sameGenSpouses.length === 0) {
      blocks.set(n.id, {
        leadId:   n.id,
        spouseId: null,
        children: childrenOf.get(n.id) ?? new Set(),
      });
    }
  }

  // primaryBlockOf: для каждого человека — ключ блока, в котором он нарисован
  const primaryBlockOf = new Map();

  for (const [key, blk] of blocks) {
    const { leadId, spouseId } = blk;

    const existing = primaryBlockOf.get(leadId);
    if (!existing) {
      primaryBlockOf.set(leadId, key);
    } else {
      const existingBlk = blocks.get(existing);
      if (blk.children.size > (existingBlk?.children.size ?? 0)) {
        primaryBlockOf.set(leadId, key);
      }
    }

    if (spouseId && !primaryBlockOf.has(spouseId)) {
      primaryBlockOf.set(spouseId, key);
    }
  }

  // ── Вычисление ширины поддерева ───────────────────────────────────────────
  const widthCache = new Map();

  function blockSelfWidth(key) {
    const blk = blocks.get(key);
    if (!blk) return NODE_W;
    return blk.spouseId ? NODE_W * 2 + PAIR_GAP : NODE_W;
  }

  function hasFamily(personId) {
    const key = primaryBlockOf.get(personId);
    if (!key) return false;
    const blk = blocks.get(key);
    return !!blk?.spouseId || (blk?.children.size ?? 0) > 0;
  }

  function sortChildren(children) {
    const arr           = [...children];
    const withFamily    = arr.filter(id => hasFamily(id));
    const withoutFamily = arr.filter(id => !hasFamily(id));
    const half = Math.floor(withoutFamily.length / 2);
    return [
      ...withoutFamily.slice(0, half),
      ...withFamily,
      ...withoutFamily.slice(half),
    ];
  }

  function subtreeWidth(blockKey, visited = new Set()) {
    if (widthCache.has(blockKey)) return widthCache.get(blockKey);
    if (visited.has(blockKey))    return blockSelfWidth(blockKey);
    visited.add(blockKey);

    const blk = blocks.get(blockKey);
    if (!blk) return NODE_W;

    const selfW    = blockSelfWidth(blockKey);
    const children = [...blk.children];

    if (children.length === 0) {
      widthCache.set(blockKey, selfW);
      return selfW;
    }

    const sorted    = sortChildren(children);
    const childrenW = sorted.reduce((acc, cid, i) => {
      const cKey = primaryBlockOf.get(cid);
      if (!cKey) return acc + NODE_W + (i > 0 ? H_GAP : 0);
      return acc + subtreeWidth(cKey, new Set(visited)) + (i > 0 ? H_GAP : 0);
    }, 0);

    const w = Math.max(selfW, childrenW);
    widthCache.set(blockKey, w);
    return w;
  }

  // ── Рекурсивное размещение ────────────────────────────────────────────────
  const positions  = new Map();
  const placedKeys = new Set();

  function placeBlock(blockKey, centerX, visited = new Set()) {
    if (placedKeys.has(blockKey)) return;
    if (visited.has(blockKey))    return;
    visited.add(blockKey);
    placedKeys.add(blockKey);

    const blk = blocks.get(blockKey);
    if (!blk) return;

    const { leadId, spouseId, children } = blk;
    const gen = genMap.get(leadId);
    const y   = gen * (NODE_H + V_GAP);

    if (spouseId) {
      const { leftId, rightId } = orderPairByGender(leadId, spouseId, nodeById);
      const totalW = NODE_W * 2 + PAIR_GAP;
      const left   = centerX - totalW / 2;
      if (!positions.has(leftId))  positions.set(leftId,  { x: left,                     y });
      if (!positions.has(rightId)) positions.set(rightId, { x: left + NODE_W + PAIR_GAP, y });
    } else {
      if (!positions.has(leadId)) positions.set(leadId, { x: centerX - NODE_W / 2, y });
    }

    if (children.size === 0) return;

    const sorted      = sortChildren([...children]);
    const childWidths = sorted.map(cid => {
      const cKey = primaryBlockOf.get(cid);
      return cKey ? subtreeWidth(cKey) : NODE_W;
    });
    const totalChildW = childWidths.reduce((a, b) => a + b, 0)
      + (sorted.length - 1) * H_GAP;

    let cx = centerX - totalChildW / 2;
    for (let i = 0; i < sorted.length; i++) {
      const cid  = sorted[i];
      const cKey = primaryBlockOf.get(cid);
      if (cKey && !placedKeys.has(cKey)) {
        placeBlock(cKey, cx + childWidths[i] / 2, new Set(visited));
      }
      cx += childWidths[i] + H_GAP;
    }
  }

  // ── Корневые блоки ────────────────────────────────────────────────────────
  const rootKeys = [];
  const rootSeen = new Set();

  for (const n of nodes) {
    if ((parentsOf.get(n.id)?.size ?? 0) > 0) continue;
    const key = primaryBlockOf.get(n.id);
    if (!key || rootSeen.has(key)) continue;
    rootSeen.add(key);
    rootKeys.push(key);
  }

  rootKeys.sort((a, b) => {
    const ga = genMap.get(blocks.get(a)?.leadId) ?? 0;
    const gb = genMap.get(blocks.get(b)?.leadId) ?? 0;
    return ga - gb;
  });

  const rootWidths = rootKeys.map(k => subtreeWidth(k));
  const totalRootW = rootWidths.reduce((a, b) => a + b, 0)
    + (rootKeys.length - 1) * ROOT_GAP;

  let rx = -totalRootW / 2;
  for (let i = 0; i < rootKeys.length; i++) {
    placeBlock(rootKeys[i], rx + rootWidths[i] / 2);
    rx += rootWidths[i] + ROOT_GAP;
  }

  // ── Fallback для изолированных нод ───────────────────────────────────────
  let fallbackX = 0;
  for (const n of nodes) {
    if (!positions.has(n.id)) {
      const y = (genMap.get(n.id) ?? 0) * (NODE_H + V_GAP);
      positions.set(n.id, { x: fallbackX, y });
      fallbackX += NODE_W + H_GAP;
    }
  }

  // ── Устранение перекрытий внутри поколения ────────────────────────────────
  const byGen = new Map();
  for (const [id, pos] of positions) {
    const gen = genMap.get(id) ?? 0;
    if (!byGen.has(gen)) byGen.set(gen, []);
    byGen.get(gen).push({ id, pos });
  }

  for (const [, items] of byGen) {
    items.sort((a, b) => a.pos.x - b.pos.x);
    for (let i = 1; i < items.length; i++) {
      const prev = items[i - 1];
      const curr = items[i];
      const minX = prev.pos.x + NODE_W + H_GAP;
      if (curr.pos.x < minX) {
        const shift = minX - curr.pos.x;
        for (let j = i; j < items.length; j++) {
          items[j].pos.x += shift;
          positions.set(items[j].id, { ...items[j].pos });
        }
      }
    }
  }

  return positions;
}

// ─────────────────────────────────────────────────────────────────────────────
//  inferMissingSpouseEdges
// ─────────────────────────────────────────────────────────────────────────────

export function inferMissingSpouseEdges(nodes, rawEdges, positions) {
  const existing = new Set(
    rawEdges
      .filter(e => e.type === 'spouse')
      .map(e => [e.source_id, e.target_id].sort().join('|'))
  );

  const genMap   = new Map(nodes.map(n => [n.id, n.generation ?? 0]));
  const extra    = [];
  const nodeList = nodes.filter(n => positions.has(n.id));

  for (let i = 0; i < nodeList.length; i++) {
    for (let j = i + 1; j < nodeList.length; j++) {
      const a = nodeList[i];
      const b = nodeList[j];
      if (genMap.get(a.id) !== genMap.get(b.id)) continue;

      const posA = positions.get(a.id);
      const posB = positions.get(b.id);
      if (!posA || !posB) continue;

      const dx = Math.abs(posA.x - posB.x);
      const dy = Math.abs(posA.y - posB.y);

      const expectedGap = NODE_W + PAIR_GAP;
      if (dy < 5 && Math.abs(dx - expectedGap) < 3) {
        const key = [a.id, b.id].sort().join('|');
        if (!existing.has(key)) {
          existing.add(key);
          extra.push({
            type:       'spouse',
            source_id:  posA.x < posB.x ? a.id : b.id,
            target_id:  posA.x < posB.x ? b.id : a.id,
            _synthetic: true,
          });
        }
      }
    }
  }

  return extra;
}
