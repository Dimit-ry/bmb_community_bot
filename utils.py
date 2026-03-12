import re
from datetime import datetime
from typing import Optional


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Парсинг строки с датой и временем"""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def extract_phone_number(text: str) -> Optional[str]:
    """Извлечение номера телефона из текста"""
    # Ищем номера в форматах: +7 XXX XXX-XX-XX, 8 XXX XXX-XX-XX
    phone_patterns = [
        r'\+7\s*(\d{3})\s*(\d{3})[-\s]?(\d{2})[-\s]?(\d{2})',
        r'8\s*(\d{3})\s*(\d{3})[-\s]?(\d{2})[-\s]?(\d{2})',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                return f"+7{groups[0]}{groups[1]}{groups[2]}{groups[3]}"
            elif len(groups) == 4 and text.startswith('8'):
                return f"+7{groups[0]}{groups[1]}{groups[2]}{groups[3]}"
    
    return None


def validate_username(username: str) -> bool:
    """Валидация username"""
    if not username:
        return False
    
    # Username должен начинаться с @ и содержать только буквы, цифры и подчеркивания
    if username.startswith('@'):
        username = username[1:]
    
    return bool(re.match(r'^[a-zA-Z0-9_]{3,32}$', username))


def format_user_info(user_data: dict) -> str:
    """Форматирование информации о пользователе"""
    username = user_data.get('username') or 'No username'
    phone = user_data.get('phone') or 'No phone'
    first_name = user_data.get('first_name') or ''
    last_name = user_data.get('last_name') or ''
    
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = username
    
    status = "✅ Подписан" if user_data.get('is_subscribed') else "❌ Отписан"
    admin_status = "👑 Админ" if user_data.get('is_admin') else ""
    
    return (
        f"👤 {full_name} (@{username})\n"
        f"📱 {phone}\n"
        f"{status} {admin_status}\n"
        f"📅 {user_data.get('created_at', 'N/A')}"
    )


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста с добавлением многоточия"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def escape_markdown(text: str) -> str:
    """Экранирование Markdown символов"""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text
