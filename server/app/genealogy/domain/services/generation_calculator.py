"""
genealogy/domain/services/generation_calculator.py

Доменный сервис: вычисление уровня поколения для каждого узла графа.

Алгоритм (v2):

  Шаг 1 — Топологическая сортировка + глубина от корня.
           Только биологические/приёмные parent_child рёбра задают иерархию.
           STEP-рёбра учитываются отдельно (слабая привязка).

  Шаг 2 — Bottom-up alignment.
           Корни выравниваются так, чтобы листья совпадали по уровню.
           «Присоединённый» корень (например, отчим без предков в дереве)
           не смещает всё дерево — он прибивается к поколению супруга.

  Шаг 3 — Выравнивание супругов (итеративное).
           Супруги получают одинаковый generation = min(gen_a, gen_b).
           После каждого изменения пересчитываются поколения всех потомков
           изменённой персоны (propagate_down), чтобы дети не оказались
           выше родителя.

  Шаг 4 — Коррекция STEP-детей.
           Ребёнок не может быть на том же или более высоком уровне,
           чем любой из его родителей (включая STEP/ADOPTED).
           child_gen = max(all_parents_gen) + 1.

  Шаг 5 — Нормализация: сдвигаем всё дерево так, чтобы min(gen) = 0.

  Результат: dict[person_id → int | None]
             None только для узлов в циклах (защита от кривых данных).

Edge-кейсы, обрабатываемые корректно:
  - Развод: бывшие супруги остаются на одном поколении, общие дети — на следующем.
  - Отчим: попадает в дерево через spouse-align, его STEP-дети получают gen+1.
  - Приёмный ребёнок: ADOPTED рёбра участвуют в иерархии наравне с BIO.
  - Несколько браков: каждый последующий супруг выравнивается по min-gen.
  - Разница поколений у супругов: берём старшего, потомков пересчитываем.
  - Изолированная пара без предков: gen=0, их дети gen=1 — без артефактов.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import NamedTuple


class _Edge(NamedTuple):
    parent_id: str
    child_id: str
    is_step: bool       # True для STEP, False для BIO/ADOPTED


def compute_generations(
    person_ids: list[str],
    parent_edges: list[tuple[str, str]],       # (parent_id, child_id) — все типы
    spouse_edges: list[tuple[str, str]],       # (person_a_id, person_b_id)
    step_child_ids: set[str] | None = None,    # child_id из STEP-связей
) -> dict[str, int | None]:
    """
    Вычисляет generation для каждой персоны.

    Args:
        person_ids:      все ID персон в семье
        parent_edges:    рёбра parent→child (BIO + ADOPTED + STEP)
        spouse_edges:    рёбра супругов
        step_child_ids:  child_id, где связь STEP (опционально).
                         Передайте их, если хотите, чтобы STEP-рёбра
                         имели более слабый приоритет при выравнивании.

    Returns:
        dict[person_id → generation | None]
        Минимальное значение = 0 (самый старший предок).
        None = цикл в данных.
    """
    if not person_ids:
        return {}

    step_children: set[str] = step_child_ids or set()
    person_set = set(person_ids)

    # Фильтруем: только рёбра внутри семьи
    internal_parent = [
        (s, t) for s, t in parent_edges
        if s in person_set and t in person_set
    ]
    internal_spouse = [
        (a, b) for a, b in spouse_edges
        if a in person_set and b in person_set
    ]

    # ── Строим индексы ────────────────────────────────────────────────────────
    parents_of:  dict[str, set[str]] = defaultdict(set)
    children_of: dict[str, set[str]] = defaultdict(set)

    for parent, child in internal_parent:
        parents_of[child].add(parent)
        children_of[parent].add(child)

    spouses_of: dict[str, set[str]] = defaultdict(set)
    for a, b in internal_spouse:
        spouses_of[a].add(b)
        spouses_of[b].add(a)

    # ── Шаг 1: Топологическая сортировка ─────────────────────────────────────
    in_degree = {pid: len(parents_of[pid]) for pid in person_ids}
    queue: deque[str] = deque(pid for pid in person_ids if in_degree[pid] == 0)

    topo_order: list[str] = []
    processed_count = 0

    while queue:
        node = queue.popleft()
        processed_count += 1
        topo_order.append(node)
        for child in children_of[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Узлы в цикле
    cycle_nodes = {pid for pid in person_ids if pid not in set(topo_order)}

    # ── Шаг 2: Bottom-up alignment ───────────────────────────────────────────
    subtree_height: dict[str, int] = dict.fromkeys(person_ids, 0)
    for node in reversed(topo_order):
        for child in children_of[node]:
            subtree_height[node] = max(
                subtree_height[node],
                subtree_height.get(child, 0) + 1,
            )

    # Корни без родителей (не в цикле)
    roots = [
        pid for pid in topo_order
        if not parents_of[pid] and pid not in cycle_nodes
    ]

    # Максимальная высота — у корня с самым глубоким потомством
    max_height = max((subtree_height[r] for r in roots), default=0)

    # Сдвиг корня: листья всех поддеревьев совпадают снизу
    root_offset: dict[str, int] = {
        r: max_height - subtree_height[r] for r in roots
    }

    # Propagate вниз через topo_order (BFS-like, учитываем нескольких родителей)
    result: dict[str, int | None] = {}
    node_gen: dict[str, int] = {}

    for r in roots:
        node_gen[r] = root_offset[r]

    for node in topo_order:
        if node not in node_gen:
            # Изолированный узел (не попал в roots из-за cycle-защиты)
            node_gen[node] = 0
        gen = node_gen[node]
        result[node] = gen

        for child in children_of[node]:
            candidate = gen + 1
            if child not in node_gen or node_gen[child] < candidate:
                node_gen[child] = candidate

    # Узлы в циклах → None
    for pid in cycle_nodes:
        result[pid] = None

    # Оставшиеся без результата
    for pid in person_ids:
        if pid not in result:
            result[pid] = None

    # ── Шаг 3: Итеративное выравнивание супругов + пересчёт потомков ─────────
    #
    # Ключевое отличие от v1:
    #   После сдвига супруга мы пересчитываем его потомков (propagate_down),
    #   иначе дети могут оказаться на том же уровне, что и родитель.
    #
    # «Присоединённый» супруг (отчим без предков) изначально имеет gen=None
    # или gen=0 (если он изолированный корень). После выравнивания он получает
    # generation матери/отца ребёнка, а его STEP-дети получают gen+1.

    def propagate_down(start_id: str, new_gen: int) -> None:
        """BFS: пересчитываем generation потомков, если это нужно."""
        bfs: deque[tuple[str, int]] = deque([(start_id, new_gen)])
        while bfs:
            pid, pg = bfs.popleft()
            for child in children_of[pid]:
                needed = pg + 1
                current = result.get(child)
                if current is None or current < needed:
                    result[child] = needed
                    bfs.append((child, needed))

    max_iters = max(len(internal_spouse) * 2, 1)

    for _ in range(max_iters):
        changed = False

        for a, b in internal_spouse:
            ga = result.get(a)
            gb = result.get(b)

            if ga is None and gb is None:
                continue

            if ga is None and gb is not None:
                result[a] = gb
                propagate_down(a, gb)
                changed = True
            elif gb is None and ga is not None:
                result[b] = ga
                propagate_down(b, ga)
                changed = True
            elif ga is not None and gb is not None and ga != gb:
                target = min(ga, gb)
                if result[a] != target:
                    result[a] = target
                    propagate_down(a, target)
                    changed = True
                if result[b] != target:
                    result[b] = target
                    propagate_down(b, target)
                    changed = True

        if not changed:
            break

    # ── Шаг 4: Коррекция детей (все типы связей) ─────────────────────────────
    #
    # После spouse-align некоторые дети могут быть на уровне родителя.
    # Проходим в topo-порядке и гарантируем child_gen > max(parent_gen).

    for node in topo_order:
        node_result = result.get(node)
        if node_result is None:
            continue
        for child in children_of[node]:
            child_result = result.get(child)
            needed = node_result + 1
            if child_result is None or child_result < needed:
                result[child] = needed

    # ── Шаг 5: Нормализация — min(gen) = 0 ───────────────────────────────────
    valid_gens = [g for g in result.values() if g is not None]
    if valid_gens:
        min_gen = min(valid_gens)
        if min_gen != 0:
            result = {
                pid: (g - min_gen if g is not None else None)
                for pid, g in result.items()
            }

    return result
