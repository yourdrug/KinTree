/**
 * lib/genealogyLayout.js  v3
 *
 * Правила:
 *  1. Мужчина ВСЕГДА справа в паре, женщина слева.
 *     Если оба одного пола / неизвестен — сохраняем порядок (ведущий слева).
 *  2. Дети размещаются строго под центром родительской пары.
 *  3. Дети с собственными семьями группируются в центре, одиночки — по краям,
 *     чтобы их партнёры и потомки не улетали далеко.
 *  4. Spouse-рёбра синтетически добавляются в TreeCanvas если их нет в rawEdges
 *     (см. buildRFEdges — теперь он принимает extraSpouseEdges).
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
  const genMap     = new Map(); // id → generation
  const nodeById   = new Map(); // id → node object

  for (const n of nodes) {
    spouseOf  .set(n.id, new Set());
    parentsOf .set(n.id, new Set());
    childrenOf.set(n.id, new Set());
    genMap    .set(n.id, n.generation ?? 0);
    nodeById  .set(n.id, n);
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

  // ── Определяем пары (ведущий + супруг) ────────────────────────────────────
  // Каждый человек входит ровно в одну пару.
  // Ведущий — тот, у кого есть дети (или первый встреченный если оба/ни один).
  const primarySpouse = new Map(); // id → spouseId | null
  const pairedSet     = new Set();

  for (const n of nodes) {
    if (pairedSet.has(n.id)) continue;
    const gen = genMap.get(n.id);
    const spouse = [...(spouseOf.get(n.id) ?? [])]
      .find(sid => genMap.get(sid) === gen && !pairedSet.has(sid)) ?? null;

    primarySpouse.set(n.id, spouse);
    pairedSet.add(n.id);
    if (spouse) {
      primarySpouse.set(spouse, n.id);
      pairedSet.add(spouse);
    }
  }

  // ── Ведущий пары (lead) ────────────────────────────────────────────────────
  // lead — тот, вокруг кого строится поддерево; spouse привязан к нему.
  // Из двух партнёров ведущим делаем того, у кого больше детей (или первый).
  const leadOf = new Map(); // id → leadId

  for (const [id, spId] of primarySpouse) {
    if (leadOf.has(id)) continue;
    if (!spId) { leadOf.set(id, id); continue; }

    const idChildren = [...(childrenOf.get(id)   ?? [])];
    const spChildren = [...(childrenOf.get(spId) ?? [])];
    const idHas = idChildren.length > 0;
    const spHas = spChildren.length > 0;

    const lead = (spHas && !idHas) ? spId : id;
    leadOf.set(id,   lead);
    leadOf.set(spId, lead);
  }

  // ── Правило: мужчина ВСЕГДА справа ────────────────────────────────────────
  function getPairOrder(leadId) {
    const spId = primarySpouse.get(leadId);
    if (!spId) return { leftId: leadId, rightId: null };

    const leadGender   = nodeById.get(leadId)?.gender ?? null;
    const spouseGender = nodeById.get(spId)?.gender   ?? null;

    if (leadGender === 'MALE' && spouseGender !== 'MALE') {
      // Ведущий — мужчина → он справа, супруг(а) слева
      return { leftId: spId, rightId: leadId };
    }
    if (spouseGender === 'MALE' && leadGender !== 'MALE') {
      // Супруг — мужчина → он справа
      return { leftId: leadId, rightId: spId };
    }
    // Оба мужчины / обе женщины / неизвестно → ведущий слева
    return { leftId: leadId, rightId: spId };
  }

  // ── Общие дети пары ────────────────────────────────────────────────────────
  function pairChildren(leadId) {
    const spId = primarySpouse.get(leadId);
    const my = [...(childrenOf.get(leadId) ?? [])];
    const sp = spId ? [...(childrenOf.get(spId) ?? [])] : [];
    return [...new Set([...my, ...sp])];
  }

  // ── Ширина поддерева ───────────────────────────────────────────────────────
  const widthCache = new Map();

  function pairSelfWidth(leadId) {
    return primarySpouse.get(leadId) ? NODE_W * 2 + PAIR_GAP : NODE_W;
  }

  function subtreeWidth(leadId, visited = new Set()) {
    if (widthCache.has(leadId)) return widthCache.get(leadId);
    if (visited.has(leadId))    return pairSelfWidth(leadId);
    visited.add(leadId);

    const children = pairChildren(leadId);
    const selfW    = pairSelfWidth(leadId);

    if (children.length === 0) {
      widthCache.set(leadId, selfW);
      return selfW;
    }

    const sortedChildren = sortChildren(children);
    const childrenW = sortedChildren.reduce((acc, cid, i) => {
      const cLead = leadOf.get(cid) ?? cid;
      return acc + subtreeWidth(cLead, new Set(visited)) + (i > 0 ? H_GAP : 0);
    }, 0);

    const w = Math.max(selfW, childrenW);
    widthCache.set(leadId, w);
    return w;
  }

  // ── Сортировка детей: с семьёй в центр, одиночки по краям ─────────────────
  // Это решает кейс 3: Евгений (с женой/детьми) должен быть ближе к своей семье.
  function hasFamily(id) {
    const lead = leadOf.get(id) ?? id;
    return pairChildren(lead).length > 0 || !!primarySpouse.get(lead);
  }

  function sortChildren(children) {
    const withFamily    = children.filter(id => hasFamily(id));
    const withoutFamily = children.filter(id => !hasFamily(id));
    // Одиночки по краям, семейные в центре
    const half = Math.floor(withoutFamily.length / 2);
    return [
      ...withoutFamily.slice(0, half),
      ...withFamily,
      ...withoutFamily.slice(half),
    ];
  }

  // ── Рекурсивное размещение ────────────────────────────────────────────────
  const positions = new Map();

  function placeSubtree(id, centerX, visited = new Set()) {
    const lead = leadOf.get(id) ?? id;
    if (visited.has(lead)) return;
    visited.add(lead);

    const gen  = genMap.get(lead);
    const y    = gen * (NODE_H + V_GAP);
    const spId = primarySpouse.get(lead);

    const { leftId, rightId } = getPairOrder(lead);

    if (rightId) {
      const totalW = NODE_W * 2 + PAIR_GAP;
      const left   = centerX - totalW / 2;
      positions.set(leftId,  { x: left,                     y });
      positions.set(rightId, { x: left + NODE_W + PAIR_GAP, y });
      visited.add(spId);
    } else {
      positions.set(lead, { x: centerX - NODE_W / 2, y });
    }

    // Дети
    const children = pairChildren(lead);
    if (children.length === 0) return;

    const sortedChildren = sortChildren(children);
    const childWidths    = sortedChildren.map(cid => {
      const cLead = leadOf.get(cid) ?? cid;
      return subtreeWidth(cLead);
    });
    const totalChildW = childWidths.reduce((a, b) => a + b, 0)
      + (sortedChildren.length - 1) * H_GAP;

    let x = centerX - totalChildW / 2;
    for (let i = 0; i < sortedChildren.length; i++) {
      const cid   = sortedChildren[i];
      const cLead = leadOf.get(cid) ?? cid;
      if (!visited.has(cLead)) {
        placeSubtree(cLead, x + childWidths[i] / 2, visited);
      }
      x += childWidths[i] + H_GAP;
    }
  }

  // ── Корневые ноды: нет родителей ──────────────────────────────────────────
  const rootLeads = [];
  const rootSeen  = new Set();

  for (const n of nodes) {
    if ((parentsOf.get(n.id)?.size ?? 0) > 0) continue;
    const lead = leadOf.get(n.id) ?? n.id;
    if (!rootSeen.has(lead)) {
      rootLeads.push(lead);
      rootSeen.add(lead);
      const sp = primarySpouse.get(lead);
      if (sp) rootSeen.add(sp);
    }
  }

  rootLeads.sort((a, b) => (genMap.get(a) ?? 0) - (genMap.get(b) ?? 0));

  const rootWidths = rootLeads.map(id => subtreeWidth(id));
  const totalRootW = rootWidths.reduce((a, b) => a + b, 0)
    + (rootLeads.length - 1) * H_GAP;

  const visited = new Set();
  let x = -totalRootW / 2;

  for (let i = 0; i < rootLeads.length; i++) {
    placeSubtree(rootLeads[i], x + rootWidths[i] / 2, visited);
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

/**
 * Возвращает массив синтетических spouse-рёбер для пар,
 * у которых позиции смежны (разница по x ≈ NODE_W + PAIR_GAP)
 * но нет явного edge в rawEdges.
 *
 * Используется в TreeCanvas.buildRFEdges чтобы гарантировать,
 * что у КАЖДОЙ пары есть пунктирная линия.
 *
 * @param {Array}  nodes      — rawNodes
 * @param {Array}  rawEdges   — rawEdges из API
 * @param {Map}    positions  — результат computeGenealogyLayout
 */
export function inferMissingSpouseEdges(nodes, rawEdges, positions) {
  // Существующие spouse пары
  const existing = new Set(
    rawEdges
      .filter(e => e.type === 'spouse')
      .map(e => [e.source_id, e.target_id].sort().join('|'))
  );

  const genMap = new Map(nodes.map(n => [n.id, n.generation ?? 0]));
  const extra  = [];

  // Для каждой пары узлов одного поколения с позициями вплотную — добавляем ребро
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

      // Смежные по x (расстояние = NODE_W + PAIR_GAP ± 2px) и на одной строке
      const expectedGap = NODE_W + PAIR_GAP;
      if (dy < 5 && Math.abs(dx - expectedGap) < 3) {
        const key = [a.id, b.id].sort().join('|');
        if (!existing.has(key)) {
          existing.add(key);
          extra.push({
            type:      'spouse',
            source_id: posA.x < posB.x ? a.id : b.id,
            target_id: posA.x < posB.x ? b.id : a.id,
            _synthetic: true,
          });
        }
      }
    }
  }

  return extra;
}
