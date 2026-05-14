"""
identity/infrastructure/permissions/role_cache.py

In-process кэш маппинга role_name → frozenset[permission_codenames].

Зачем:
  При каждом аутентифицированном запросе AccountRepository делает 2 SELECT:
    1. SELECT role_id, role_name FROM roles JOIN account_roles WHERE account_id = ?
    2. SELECT codename FROM permissions JOIN role_permissions WHERE role_id = ?

  Роли и их пермишены — глобальные данные, меняются только при деплое
  (через sync_permissions). Кэшировать их in-process безопасно.

  После прогрева (первый запрос каждой роли) — 0 запросов к permissions.
  Экономия: 1 SELECT на каждый аутентифицированный HTTP-запрос.

Инвалидация:
  invalidate() вызывается из PermissionService.sync_permissions() после
  синхронизации, чтобы следующие запросы подтянули актуальные данные.

Thread-safety:
  asyncio — однопоточный в рамках event loop, dict-операции атомарны.
  GIL защищает от гонок при чтении/записи словаря.

Ограничения:
  - Не синхронизируется между воркерами uvicorn (каждый воркер — свой кэш).
    Это нормально: при деплое все воркеры перезапускаются.
  - Не подходит если роли меняются в рантайме через UI без рестарта.
    В текущей архитектуре это невозможно (роли только через миграции).
"""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

# role_name → frozenset[codename]
_cache: dict[str, frozenset[str]] = {}


def get_cached_permissions(role_name: str) -> frozenset[str] | None:
    """
    Вернуть пермишены роли из кэша.
    None если роль ещё не закэширована.
    """
    return _cache.get(role_name)


def set_cached_permissions(role_name: str, permissions: frozenset[str]) -> None:
    """Записать пермишены роли в кэш."""
    _cache[role_name] = permissions


def invalidate() -> None:
    """
    Инвалидировать весь кэш.

    Вызывается после sync_permissions() чтобы следующие запросы
    подтянули актуальные данные из БД.
    """
    _cache.clear()
    logger.info("Role permissions cache invalidated (%d entries cleared)", len(_cache))


def stats() -> dict[str, int]:
    """Статистика для отладки и мониторинга."""
    return {
        "cached_roles": len(_cache),
        "total_permissions": sum(len(v) for v in _cache.values()),
    }
