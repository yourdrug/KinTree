"""
genealogy/domain/services/generation_calculator.py

Доменный сервис: вычисление уровня поколения для каждого узла графа.

Алгоритм:
  Шаг 1: Топологическая сортировка по parent_child рёбрам.
          Вычисляем глубину каждого узла от его ближайшего корня.

  Шаг 2: Выравнивание по листьям (bottom-up alignment).
          Для каждого узла без родителей (корень) вычисляем высоту
          его поддерева (max расстояние до листа).
          Корень с максимальной высотой получает generation=0.
          Остальные корни сдвигаются вниз так, чтобы их листья
          находились на том же уровне, что и листья самого глубокого дерева.
          Это гарантирует, что "самый старший предок" всегда generation=0.

  Шаг 3: Выравнивание супругов.
          Если A и B — супруги, оба получают min(gen[A], gen[B])
          (берём более высокий уровень = меньшее число).
          Повторяется до стабилизации.

  Результат: dict[person_id → generation]
             None для узлов в цикле (защита от некорректных данных).

Чистая функция — нет IO, легко тестируется.
"""

from __future__ import annotations

from collections import defaultdict, deque


def compute_generations(
    person_ids: list[str],
    parent_edges: list[tuple[str, str]],  # (parent_id, child_id)
    spouse_edges: list[tuple[str, str]],  # (person_a_id, person_b_id)
) -> dict[str, int | None]:
    """
    Вычисляет generation для каждой персоны.

    generation=0 — самый старший предок (корень с максимальной глубиной потомков).
    Остальные корни выравниваются так, чтобы их листья совпадали с листьями
    самого глубокого дерева (bottom-up alignment).

    Args:
        person_ids:    все ID персон в семье
        parent_edges:  рёбра parent→child (только parent_child связи)
        spouse_edges:  рёбра супругов (нормализованные пары)

    Returns:
        dict[person_id → generation | None]
        None = не удалось определить (циклические данные в БД)
    """
    if not person_ids:
        return {}

    person_set = set(person_ids)

    # Фильтруем рёбра — только те, у которых оба участника в этой семье
    internal_parent = [(s, t) for s, t in parent_edges if s in person_set and t in person_set]
    internal_spouse = [(a, b) for a, b in spouse_edges if a in person_set and b in person_set]

    # ── Построить граф ────────────────────────────────────────────────────────
    parents_of: dict[str, set[str]] = defaultdict(set)
    children_of: dict[str, set[str]] = defaultdict(set)

    for parent, child in internal_parent:
        parents_of[child].add(parent)
        children_of[parent].add(child)

    # ── Шаг 1: Топологическая сортировка, глубина от корня ───────────────────
    in_degree = {pid: len(parents_of[pid]) for pid in person_ids}
    queue: deque[str] = deque(pid for pid in person_ids if in_degree[pid] == 0)

    # depth_from_root: расстояние от ближайшего корня вниз
    depth_from_root: dict[str, int] = {}
    for pid in person_ids:
        if in_degree[pid] == 0:
            depth_from_root[pid] = 0

    processed = 0
    topo_order: list[str] = []

    while queue:
        node = queue.popleft()
        processed += 1
        topo_order.append(node)

        for child in children_of[node]:
            # глубина ребёнка = max(глубин родителей) + 1
            candidate = depth_from_root.get(node, 0) + 1
            depth_from_root[child] = max(depth_from_root.get(child, 0), candidate)

            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # ── Защита от циклов ──────────────────────────────────────────────────────
    cycle_nodes = {pid for pid in person_ids if pid not in depth_from_root}

    # ── Шаг 2: Bottom-up alignment ───────────────────────────────────────────
    # Для каждого узла вычисляем высоту поддерева (max глубина потомков).
    # Проходим в обратном топологическом порядке.
    subtree_height: dict[str, int] = dict.fromkeys(person_ids, 0)

    for node in reversed(topo_order):
        for child in children_of[node]:
            subtree_height[node] = max(subtree_height[node], subtree_height[child] + 1)

    # Корни (узлы без родителей в этой семье, не в цикле)
    roots = [pid for pid in person_ids if not parents_of[pid] and pid not in cycle_nodes]

    # Максимальная высота среди всех корней = "самый старший предок"
    max_height = max((subtree_height[r] for r in roots), default=0)

    # Сдвиг для каждого корня: корень с max_height получает offset=0,
    # остальные сдвигаются вниз так, чтобы их листья были на одном уровне
    # с листьями самого глубокого дерева.
    root_offset: dict[str, int] = {}
    for r in roots:
        root_offset[r] = max_height - subtree_height[r]

    # Propagate offsets вниз по дереву
    result: dict[str, int | None] = {}

    # BFS от каждого корня с его offset
    visited: set[str] = set()
    bfs: deque[tuple[str, int]] = deque()

    for r in roots:
        if r not in visited:
            visited.add(r)
            bfs.append((r, root_offset[r]))

    while bfs:
        node, gen = bfs.popleft()
        result[node] = gen

        for child in children_of[node]:
            if child not in visited:
                visited.add(child)
                # Ребёнок на 1 поколение ниже родителя.
                # Если у ребёнка несколько родителей — берём max generation
                # (чтобы ребёнок не оказался выше одного из родителей)
                bfs.append((child, gen + 1))

    # Если узел посещён несколько раз (несколько родителей) — берём максимум.
    # Перезапускаем через тополог. порядок для корректного многократного прохода.
    result = {}
    node_gen: dict[str, int] = {}

    for r in roots:
        node_gen[r] = root_offset[r]

    for node in topo_order:
        if node not in node_gen:
            # Изолированный узел без родителей (не попал в roots из-за cycles)
            node_gen[node] = 0
        gen = node_gen[node]
        result[node] = gen

        for child in children_of[node]:
            candidate = gen + 1
            if child not in node_gen or node_gen[child] < candidate:
                node_gen[child] = candidate

    # Узлы в цикле → None
    for pid in cycle_nodes:
        result[pid] = None

    # Оставшиеся без результата
    for pid in person_ids:
        if pid not in result:
            result[pid] = None

    # ── Шаг 3: Выравнивание супругов ─────────────────────────────────────────
    # Супруги получают MIN generation (выше = старше = меньшее число).
    # Это важно для "вошедших" супругов без предков в дереве.
    max_iterations = max(len(internal_spouse), 1)

    for _ in range(max_iterations):
        changed = False

        for a, b in internal_spouse:
            ga = result.get(a)
            gb = result.get(b)

            if ga is None and gb is None:
                continue

            if ga is None and gb is not None:
                result[a] = gb
                changed = True
            elif gb is None and ga is not None:
                result[b] = ga
                changed = True
            elif ga is not None and gb is not None and ga != gb:
                # Оба на уровень старшего из пары
                target = min(ga, gb)
                if result[a] != target:
                    result[a] = target
                    changed = True
                if result[b] != target:
                    result[b] = target
                    changed = True

        if not changed:
            break

    return result
