"""
identity/infrastructure/oauth/telegram_verifier.py

Верификация данных от Telegram Login Widget.

Алгоритм (официальная документация Telegram):
  1. Убрать поле hash из полученных данных
  2. Отсортировать оставшиеся поля как key=value, соединить \n
  3. data_check_string = "auth_date=...\nfirst_name=...\nid=..."
  4. secret_key = SHA-256(bot_token)  ← не HMAC, а чистый SHA-256
  5. hash = HMAC-SHA256(data_check_string, secret_key)
  6. Сравнить с присланным hash (константное время)
  7. Проверить auth_date — не старше MAX_AGE_SECONDS
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import logging
import time

from shared.infrastructure.db.settings import settings


logger = logging.getLogger(__name__)

# Максимальный возраст данных от Telegram (секунды).
# После этого считаем данные устаревшими (replay attack защита).
_MAX_AGE_SECONDS = 86400  # 24 часа — стандартное значение


@dataclass(frozen=True)
class TelegramUserInfo:
    """Верифицированные данные пользователя из Telegram Login Widget."""

    telegram_id: str
    first_name: str
    last_name: str | None
    username: str | None
    photo_url: str | None


def verify_telegram_auth(
    *,
    telegram_id: str,
    first_name: str,
    last_name: str | None,
    username: str | None,
    photo_url: str | None,
    auth_date: int,
    received_hash: str,
) -> TelegramUserInfo:
    """
    Верифицировать данные от Telegram Login Widget.

    Args:
        telegram_id: ID пользователя в Telegram
        first_name: Имя
        last_name: Фамилия (опционально)
        username: Username (опционально)
        photo_url: Фото (опционально)
        auth_date: Unix timestamp авторизации
        received_hash: HMAC подпись от Telegram

    Returns:
        TelegramUserInfo — верифицированные данные

    Raises:
        ValueError: если подпись невалидна или данные устарели
    """
    # 1. Проверить возраст данных
    age = int(time.time()) - auth_date
    if age > _MAX_AGE_SECONDS:
        raise ValueError(f"Данные Telegram устарели: {age} секунд назад")

    # 2. Собрать data_check_string — только непустые поля, отсортированные
    fields: dict[str, str] = {"id": telegram_id, "first_name": first_name, "auth_date": str(auth_date)}
    if last_name:
        fields["last_name"] = last_name
    if username:
        fields["username"] = username
    if photo_url:
        fields["photo_url"] = photo_url

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))

    # 3. secret_key = SHA-256(bot_token)
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()

    # 4. Вычислить HMAC-SHA256
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    # 5. Сравнить в константное время (защита от timing attack)
    if not hmac.compare_digest(expected_hash, received_hash):
        logger.warning("Telegram auth hash mismatch for telegram_id=%s", telegram_id)
        raise ValueError("Невалидная подпись Telegram")

    return TelegramUserInfo(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        photo_url=photo_url,
    )
