from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_response_buttons() -> InlineKeyboardMarkup:
    """Кнопки для ответа на напоминание"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Точно приду", callback_data="response:will_come"))
    builder.add(InlineKeyboardButton(text="🤔 Пока думаю", callback_data="response:thinking"))
    builder.add(InlineKeyboardButton(text="❌ Не смогу", callback_data="response:wont_come"))
    builder.adjust(1)
    return builder.as_markup()


def get_admin_menu() -> InlineKeyboardMarkup:
    """Меню администратора"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📊 Статистика ответов", callback_data="admin:stats"))
    builder.add(InlineKeyboardButton(text="👥 Статистика подписчиков", callback_data="admin:subscribers"))
    builder.add(InlineKeyboardButton(text="📤 Создать рассылку", callback_data="admin:create_broadcast"))
    builder.add(InlineKeyboardButton(text="👤 Назначить администратора", callback_data="admin:make_admin"))
    builder.adjust(1)
    return builder.as_markup()


def get_user_menu(is_subscribed: bool = True) -> ReplyKeyboardMarkup:
    """Меню пользователя"""
    if is_subscribed:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Поделиться контактом", request_contact=True)],
                [KeyboardButton(text="❌ Отписаться от рассылки")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Поделиться контактом", request_contact=True)],
                [KeyboardButton(text="🔔 Подписаться на рассылку")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    return keyboard


def get_stats_menu() -> InlineKeyboardMarkup:
    """Меню статистики"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📈 Последние 10 событий", callback_data="stats:last_events"))
    builder.add(InlineKeyboardButton(text="👤 Все подписчики", callback_data="stats:all_subscribers"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back"))
    builder.adjust(1)
    return builder.as_markup()


def get_broadcast_options() -> InlineKeyboardMarkup:
    """Опции рассылки"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⏰ Отложенная отправка", callback_data="broadcast:schedule"))
    builder.add(InlineKeyboardButton(text="📤 Отправить сейчас", callback_data="broadcast:send_now"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="admin:back"))
    builder.adjust(1)
    return builder.as_markup()


def get_confirmation_buttons() -> InlineKeyboardMarkup:
    """Кнопки подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Да", callback_data="confirm:yes"))
    builder.add(InlineKeyboardButton(text="❌ Нет", callback_data="confirm:no"))
    builder.adjust(2)
    return builder.as_markup()


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка возврата"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back"))
    return builder.as_markup()
