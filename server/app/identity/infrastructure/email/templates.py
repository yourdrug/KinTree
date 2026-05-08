"""
identity/infrastructure/email/templates.py

HTML-шаблоны писем для KinTree.

Принципы:
  - Минималистичный, читаемый HTML без внешних зависимостей.
  - Inline CSS — максимальная совместимость с email-клиентами.
  - Все ссылки передаются как параметры — шаблон не знает о настройках.
"""

from __future__ import annotations


_BASE = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="540" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;padding:40px;max-width:540px;">
          <tr>
            <td>
              <p style="margin:0 0 8px;font-size:22px;font-weight:700;color:#111827;">KinTree</p>
              <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0 24px;">
              {body}
              <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0 16px;">
              <p style="margin:0;font-size:12px;color:#9ca3af;">
                Если вы не запрашивали это письмо — просто проигнорируйте его.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

_BUTTON = """
<a href="{url}"
   style="display:inline-block;padding:12px 28px;background:#111827;color:#ffffff;
          text-decoration:none;border-radius:6px;font-size:15px;font-weight:600;
          margin:24px 0;">
  {label}
</a>
"""

_EXPIRE_NOTE = '<p style="margin:16px 0 0;font-size:13px;color:#6b7280;">Ссылка действительна {minutes} минут.</p>'


def verify_email_html(verify_url: str, expires_minutes: int = 60) -> str:
    """Письмо с подтверждением адреса электронной почты."""
    body = (
        '<h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#111827;">'
        "Подтвердите ваш email</h1>"
        '<p style="margin:0 0 4px;font-size:15px;color:#374151;">'
        "Нажмите кнопку ниже, чтобы подтвердить адрес электронной почты и активировать аккаунт."
        "</p>"
        + _BUTTON.format(url=verify_url, label="Подтвердить email")
        + _EXPIRE_NOTE.format(minutes=expires_minutes)
    )
    return _BASE.format(title="Подтверждение email — KinTree", body=body)


def reset_password_html(reset_url: str, expires_minutes: int = 15) -> str:
    """Письмо со ссылкой для сброса пароля."""
    body = (
        '<h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#111827;">'
        "Сброс пароля</h1>"
        '<p style="margin:0 0 4px;font-size:15px;color:#374151;">'
        "Мы получили запрос на сброс пароля для вашего аккаунта. "
        "Нажмите кнопку ниже чтобы задать новый пароль."
        "</p>"
        + _BUTTON.format(url=reset_url, label="Задать новый пароль")
        + _EXPIRE_NOTE.format(minutes=expires_minutes)
    )
    return _BASE.format(title="Сброс пароля — KinTree", body=body)
