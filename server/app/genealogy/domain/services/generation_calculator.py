"""
genealogy/domain/services/generation_calculator.py

Доменный сервис: вычисление уровня поколения для каждого узла графа.

Алгоритм:
  Шаг 1: Топологическая сортировка по parent_child рёбрам.
          generation[child] = max(generation[parents]) + 1
          Корни (без родителей в этой семье) = generation 0.

  Шаг 2: Выравнивание супругов.
          Если A и B — супруги, оба получают max(gen[A], gen[B]).
          Это корректно обрабатывает «вошедших» супругов (in-laws):
          Света входит без родителей (generation=0 после шага 1),
          но через брак с Петром (generation=1) получает generation=1.
          Повторяется до стабилизации (обычно 1–2 итерации).

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

    # ── Шаг 1: топологическая сортировка ─────────────────────────────────────
    parents_of: dict[str, set[str]] = defaultdict(set)
    children_of: dict[str, set[str]] = defaultdict(set)

    for parent, child in internal_parent:
        parents_of[child].add(parent)
        children_of[parent].add(child)

    in_degree = {pid: len(parents_of[pid]) for pid in person_ids}
    queue: deque[str] = deque(pid for pid in person_ids if in_degree[pid] == 0)
    generation: dict[str, int] = {}
    processed = 0

    while queue:
        node = queue.popleft()
        processed += 1

        parent_gens = [generation[p] for p in parents_of[node] if p in generation]
        generation[node] = (max(parent_gens) + 1) if parent_gens else 0

        for child in children_of[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # ── Защита от циклов ──────────────────────────────────────────────────────
    # Если processed < len(person_ids) — есть цикл (некорректные данные в БД).
    # Таким узлам присваиваем None.
    result: dict[str, int | None] = {pid: generation.get(pid) for pid in person_ids}

    if processed < len(person_ids):
        for pid in person_ids:
            if pid not in generation:
                result[pid] = None

    # ── Шаг 2: выравнивание супругов ─────────────────────────────────────────
    # Итерируем до стабилизации. Максимум len(spouse_edges) итераций.
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
                # Ставим обоих на БОЛЕЕ ВЫСОКИЙ уровень (max = дальше от корней)
                target = max(ga, gb)
                if result[a] != target:
                    result[a] = target
                    changed = True
                if result[b] != target:
                    result[b] = target
                    changed = True

        if not changed:
            break

    return result
