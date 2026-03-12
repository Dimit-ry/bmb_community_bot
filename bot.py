import asyncio
import logging
import aiosqlite
import fcntl  # для файловой блокировки
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardRemove, Contact
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from config import settings
from database import db
from keyboards import (
    get_response_buttons, get_admin_menu, get_user_menu, 
    get_stats_menu, get_broadcast_options, get_confirmation_buttons, get_back_button
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BroadcastState:
    """Состояния для создания рассылки"""
    def __init__(self):
        self.pending_messages = {}
        self.user_states = {}


bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
broadcast_state = BroadcastState()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    try:
        print(f"DEBUG: Получен /start от {message.from_user.id} (@{message.from_user.username})")
        
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        
        # Отладка
        print(f"DEBUG: /start от user_id={user_id}, admin_id={settings.admin_id}")
        print(f"DEBUG: Сравнение: {user_id} == {settings.admin_id} = {user_id == settings.admin_id}")
        
        # Добавляем пользователя в базу
        await db.add_user(user_id, username, first_name, last_name)
        print("DEBUG: Пользователь добавлен в базу")
        
        # Назначаем администратором, если это ID из конфига
        if user_id == settings.admin_id:
            print(f"DEBUG: Назначаем администратором user_id={user_id}")
            await db.make_admin(user_id)
        
        # Проверяем, является ли пользователь администратором
        is_admin = await db.is_admin(user_id)
        print(f"DEBUG: is_admin={is_admin}")
        
        # Получаем статус подписки
        user_info = await db.get_user_by_telegram_id(user_id)
        print(f"DEBUG: user_info={user_info}, type={type(user_info)}")
        
        if user_info and isinstance(user_info, dict):
            is_subscribed = user_info.get('is_subscribed', False)
        else:
            is_subscribed = False
        print(f"DEBUG: is_subscribed={is_subscribed}")
        
        if is_admin:
            welcome_text = (
                f"👋 Добро пожаловать, {first_name}!\n\n"
                f"🔐 Вы вошли как администратор\n"
                f"Используйте команду /admin для доступа к панели управления."
            )
            print("DEBUG: Отправляем приветствие админу")
            await message.answer(welcome_text)
        else:
            welcome_text = (
                f"👋 Добро пожаловать, {first_name}!\n\n"
                f"Я бот для напоминаний о событиях.\n"
                f"Вы будете получать уведомления и сможете отметить свое присутствие.\n\n"
                f"Используйте меню ниже для управления подпиской."
            )
            print("DEBUG: Отправляем приветствие пользователю")
            await message.answer(welcome_text, reply_markup=get_user_menu(is_subscribed))
            
        print("DEBUG: /start обработан успешно")
        
    except Exception as e:
        import traceback
        print(f"ERROR в /start: {e}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        try:
            await message.answer(f"❌ Произошла ошибка: {str(e)}")
        except:
            print("ERROR: Не удалось даже отправить сообщение об ошибке")


@dp.message(F.contact)
async def handle_contact(message: Message):
    """Обработка поделенного контакта"""
    try:
        contact = message.contact
        user_id = message.from_user.id
        
        print(f"DEBUG: Получен контакт от user_id={user_id}")
        print(f"DEBUG: contact.user_id={contact.user_id}, phone={contact.phone_number}")
        
        # Проверяем, что контакт принадлежит пользователю
        if contact.user_id == user_id:
            # Сохраняем номер телефона
            success = await db.update_phone_number(user_id, contact.phone_number)
            
            if success:
                # Получаем актуальный статус подписки
                user_info = await db.get_user_by_telegram_id(user_id)
                if user_info and isinstance(user_info, dict):
                    is_subscribed = user_info.get('is_subscribed', False)
                else:
                    is_subscribed = False
                    
                await message.answer(
                    f"✅ Спасибо! Ваш номер телефона {contact.phone_number} сохранен.",
                    reply_markup=get_user_menu(is_subscribed)
                )
            else:
                await message.answer("❌ Ошибка сохранения номера телефона")
        else:
            await message.answer("❌ Пожалуйста, поделитесь СВОИМ контактом")
            
    except Exception as e:
        print(f"ERROR в обработке контакта: {e}")
        await message.answer("❌ Ошибка обработки контакта")


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Открытие админ панели"""
    if await db.is_admin(message.from_user.id):
        await message.answer("🔐 Панель администратора:", reply_markup=get_admin_menu())
    else:
        await message.answer("❌ У вас нет прав администратора")


@dp.message(F.text == "📊 Моя статистика")
async def show_user_stats(message: Message):
    """Показать статистику пользователя"""
    user_id = await db.get_user_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("❌ Пользователь не найден")
        return
    
    # Здесь можно добавить логику получения статистики пользователя
    stats_text = (
        "📊 Ваша статистика:\n\n"
        f"🔔 Вы подписаны на рассылку\n"
        f"📝 Ваши ответы на напоминания:\n"
        f"   ✅ Точно приду: 0\n"
        f"   🤔 Пока думаю: 0\n"
        f"   ❌ Не смогу: 0"
    )
    
    await message.answer(stats_text)


@dp.message(F.text == "🔔 Настройки уведомлений")
async def notification_settings(message: Message):
    """Настройки уведомлений"""
    user_id = message.from_user.id
    is_subscribed = await db.get_user_by_telegram_id(user_id)
    
    if is_subscribed:
        await message.answer("✅ Вы подписаны на рассылку", reply_markup=get_user_menu())
    else:
        await message.answer("❌ Вы отписаны от рассылки", reply_markup=get_user_menu())


@dp.message(F.text == "❌ Отписаться от рассылки")
async def unsubscribe(message: Message):
    """Отписка от рассылки"""
    user_id = message.from_user.id
    new_status = await db.toggle_subscription(user_id)
    
    if new_status:
        await message.answer("✅ Вы подписались на рассылку", reply_markup=get_user_menu())
    else:
        await message.answer("❌ Вы отписались от рассылки", reply_markup=get_user_menu())


@dp.callback_query(F.data.startswith("response:"))
async def handle_response(callback: CallbackQuery):
    """Обработка ответов на напоминание"""
    response_type = callback.data.split(":")[1]
    user_id = await db.get_user_by_telegram_id(callback.from_user.id)
    
    print(f"DEBUG: Ответ от user_id={user_id}, response_type={response_type}")
    
    if not user_id:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Получаем message_id из данных callback (нужно передавать при отправке)
    # Временно используем последнее сообщение для теста
    async with aiosqlite.connect("bot.db") as conn:
        cursor = await conn.execute(
            "SELECT id FROM messages WHERE status = 'sent' ORDER BY sent_at DESC LIMIT 1"
        )
        result = await cursor.fetchone()
        if result:
            message_id = result[0]
            print(f"DEBUG: Сохраняем ответ для message_id={message_id}")
            await db.save_response(user_id, message_id, response_type)
    
    response_texts = {
        "will_come": "✅ Вы выбрали: Точно приду",
        "thinking": "🤔 Вы выбрали: Пока думаю", 
        "wont_come": "❌ Вы выбрали: Не смогу"
    }
    
    await callback.answer(f"Ваш ответ: {response_texts.get(response_type, 'Неизвестный ответ')}")
    
    # Обновляем сообщение, чтобы убрать кнопки
    response_text = response_texts.get(response_type, "Неизвестный ответ")
    await callback.message.edit_text(
        f"Спасибо за ответ!\n{response_text}"
    )


@dp.callback_query(F.data.startswith("admin:"))
async def handle_admin_callbacks(callback: CallbackQuery):
    """Обработка админ callbacks"""
    action = callback.data.split(":")[1]
    
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    if action == "stats":
        await callback.message.edit_text("📊 Выберите статистику:", reply_markup=get_stats_menu())
    
    elif action == "subscribers":
        stats = await db.get_subscribers_stats()
        text = "👥 Статистика подписчиков:\n\n"
        
        for user in stats[:20]:  # Показываем первые 20
            username = user['username'] or "No username"
            phone = user['phone'] or "No phone"
            status = "✅ Подписан" if user['is_subscribed'] else "❌ Отписан"
            text += f"@{username} | {phone} | {status}\n"
        
        await callback.message.edit_text(text, reply_markup=get_back_button())
    
    elif action == "create_broadcast":
        broadcast_state.user_states[callback.from_user.id] = {"step": "text"}
        await callback.message.edit_text(
            "📤 Создание рассылки\n\n"
            "Отправьте текст для рассылки (можно использовать HTML форматирование и гиперссылки):",
            reply_markup=get_back_button()
        )
    
    elif action == "make_admin":
        broadcast_state.user_states[callback.from_user.id] = {"step": "make_admin"}
        await callback.message.edit_text(
            "👤 Назначение администратора\n\n"
            "Отправьте username пользователя (с @) или его Telegram ID:",
            reply_markup=get_back_button()
        )
    
    elif action == "back":
        await callback.message.edit_text("🔐 Панель администратора:", reply_markup=get_admin_menu())


@dp.callback_query(F.data.startswith("stats:"))
async def handle_stats_callbacks(callback: CallbackQuery):
    """Обработка статистики"""
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    action = callback.data.split(":")[1]
    
    if action == "last_events":
        from utils import truncate_text, escape_markdown
        
        print("DEBUG: Запрашиваем статистику последних событий...")
        stats = await db.get_last_events_stats()
        print(f"DEBUG: Получено {len(stats)} сообщений")
        
        if not stats:
            text = "📈 Статистика по последним событиям:\n\n"
            text += "❌ Пока нет отправленных сообщений\n"
            text += "Создайте рассылку для получения статистики"
        else:
            text = "📈 Статистика по последним событиям:\n\n"
            
            for i, message in enumerate(stats[:10], 1):
                print(f"DEBUG: Обработка сообщения {i}: {message}")
                
                # Форматируем дату отправки
                sent_date = message['sent_at']
                if sent_date:
                    try:
                        from datetime import datetime
                        if isinstance(sent_date, str):
                            dt = datetime.fromisoformat(sent_date.replace('Z', '+00:00'))
                        else:
                            dt = sent_date
                        date_str = dt.strftime("%d.%m.%Y %H:%M")
                    except:
                        date_str = str(sent_date)
                else:
                    date_str = "N/A"
                
                # Получаем первую строку текста и очищаем от HTML
                import re
                first_line = message['text'].split('\n')[0] if message['text'] else 'Без текста'
                # Удаляем HTML теги
                first_line = re.sub(r'<[^>]+>', '', first_line)
                first_line = truncate_text(first_line.strip(), 50)
                
                text += f"{first_line}\n"
                text += f"📅 {date_str}\n"
                
                # Добавляем ответы
                if message['responses']:
                    response_count = len(message['responses'])
                    if response_count == 1:
                        text += f"✅ {response_count} ответ\n"
                    else:
                        text += f"✅ {response_count} ответа\n"
                    
                    # Показываем первые 3 ответа
                    for response in message['responses'][:3]:
                        username = response['username'] or "No username"
                        resp_type = response['response_type']
                        
                        response_emoji = {
                            "will_come": "Приду",
                            "thinking": "Думаю", 
                            "wont_come": "Не смогу"
                        }.get(resp_type, resp_type)
                        
                        text += f"   • @{username}: {response_emoji}\n"
                else:
                    text += "📭 Нет ответов\n"
                
                text += "\n"
        
        print(f"DEBUG: Текст статистики готов, длина: {len(text)}")
        await callback.message.edit_text(text, parse_mode=None, reply_markup=get_back_button())
    
    elif action == "all_subscribers":
        stats = await db.get_subscribers_stats()
        text = "👤 Все подписчики:\n\n"
        
        for user in stats[:30]:
            username = user['username'] or "No username"
            phone = user['phone'] or "No phone"
            status = "✅" if user['is_subscribed'] else "❌"
            text += f"{status} @{username} | {phone}\n"
        
        await callback.message.edit_text(text, reply_markup=get_back_button())


@dp.message()
async def handle_text_messages(message: Message):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    
    print(f"DEBUG: Текстовое сообщение от user_id={user_id}: {message.text[:50]}...")
    
    # Если администратор - обрабатываем команды админа
    if await db.is_admin(user_id):
        print(f"DEBUG: Пользователь админ, проверяем состояния...")
        # Проверяем, находится ли пользователь в процессе создания рассылки
        if user_id in broadcast_state.user_states:
            state = broadcast_state.user_states[user_id]
            print(f"DEBUG: Состояние пользователя: {state}")
            
            if state["step"] == "text":
                # Сохраняем текст рассылки
                state["text"] = message.html_text
                state["step"] = "confirm"
                
                await message.answer(
                    f"📤 Текст рассылки сохранен:\n\n{message.html_text}\n\n"
                    "Выберите действие:",
                    reply_markup=get_broadcast_options()
                )
            
            elif state["step"] == "make_admin":
                # Обработка назначения администратора
                admin_input = message.text.strip()
                print(f"DEBUG: Попытка назначить администратором: {admin_input}")
                
                if admin_input.startswith("@"):
                    # Ищем пользователя по username
                    username = admin_input[1:]  # Убираем @
                    print(f"DEBUG: Ищем пользователя по username: {username}")
                    
                    async with aiosqlite.connect("bot.db") as conn:
                        cursor = await conn.execute(
                            "SELECT telegram_id, username FROM users WHERE username = ?",
                            (username,)
                        )
                        result = await cursor.fetchone()
                        
                        if result:
                            telegram_id = result[0]
                            found_username = result[1]
                            print(f"DEBUG: Найден пользователь: telegram_id={telegram_id}, username={found_username}")
                            
                            success = await db.make_admin(telegram_id)
                            if success:
                                await message.answer(f"✅ Пользователь @{found_username} назначен администратором")
                            else:
                                await message.answer("❌ Ошибка при назначении администратора")
                        else:
                            await message.answer(f"❌ Пользователь @{username} не найден в базе")
                            
                else:
                    try:
                        telegram_id = int(admin_input)
                        print(f"DEBUG: Ищем пользователя по telegram_id: {telegram_id}")
                        
                        success = await db.make_admin(telegram_id)
                        if success:
                            await message.answer(f"✅ Пользователь {telegram_id} назначен администратором")
                        else:
                            await message.answer("❌ Пользователь с таким ID не найден")
                    except ValueError:
                        await message.answer("❌ Неверный формат. Введите username (@username) или Telegram ID")
                
                del broadcast_state.user_states[user_id]
                await message.answer("🔐 Панель администратора:", reply_markup=get_admin_menu())
            
            elif state["step"] == "schedule_time":
                # Обработка отложенной отправки
                from utils import parse_datetime
                
                print(f"DEBUG: Получено время: {message.text.strip()}")
                
                scheduled_time = parse_datetime(message.text.strip())
                print(f"DEBUG: Распарсенное время: {scheduled_time}")
                
                if scheduled_time:
                    if scheduled_time <= datetime.now():
                        await message.answer("❌ Указанное время уже прошло. Выберите будущее время.")
                    else:
                        # Сохраняем отложенное сообщение
                        message_id = await db.save_message(
                            state["text"], 
                            scheduled_at=scheduled_time
                        )
                        
                        await message.answer(
                            f"✅ Рассылка запланирована на\n"
                            f"📅 {scheduled_time.strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"ID сообщения: {message_id}"
                        )
                        
                        del broadcast_state.user_states[user_id]
                        await message.answer("🔐 Панель администратора:", reply_markup=get_admin_menu())
                else:
                    await message.answer(
                        "❌ Неверный формат времени. Попробуйте еще раз:\n\n"
                        "Формат: ГГГГ-ММ-ДД ЧЧ:ММ\n"
                        "Пример: 2024-12-31 18:30"
                    )
    
    # Обработка сообщений от обычных пользователей (не админов)
    else:
        # Проверяем, является ли пользователь администратором
        is_admin_user = await db.is_admin(user_id)
        
        if is_admin_user:
            # Если администратор пишет не в режиме админки
            await message.answer("🔐 Используйте команду /admin для доступа к панели управления.", reply_markup=get_admin_menu())
        else:
            # Обработка кнопок меню пользователя
            if message.text == "🔔 Подписаться на рассылку":
                new_status = await db.toggle_subscription(user_id)
                if new_status:
                    await message.answer("✅ Вы подписались на рассылку", reply_markup=get_user_menu(True))
                else:
                    await message.answer("❌ Ошибка подписки", reply_markup=get_user_menu(False))
                    
            elif message.text == "❌ Отписаться от рассылки":
                new_status = await db.toggle_subscription(user_id)
                if not new_status:
                    await message.answer("❌ Вы отписались от рассылки", reply_markup=get_user_menu(False))
                else:
                    await message.answer("✅ Вы остались подписаны", reply_markup=get_user_menu(True))
                
            else:
                # Другие сообщения от пользователей
                user_info = await db.get_user_by_telegram_id(user_id)
                if user_info and isinstance(user_info, dict):
                    is_subscribed = user_info.get('is_subscribed', False)
                else:
                    is_subscribed = False
                await message.answer("💬 Используйте меню для управления подпиской.", reply_markup=get_user_menu(is_subscribed))


@dp.callback_query(F.data.startswith("broadcast:"))
async def handle_broadcast_callbacks(callback: CallbackQuery):
    """Обработка callbacks для рассылки"""
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    if user_id not in broadcast_state.user_states:
        await callback.answer("❌ Рассылка не найдена", show_alert=True)
        return
    
    state = broadcast_state.user_states[user_id]
    
    if action == "send_now":
        # Немедленная отправка
        await send_broadcast(state["text"], callback.from_user.id)
        del broadcast_state.user_states[user_id]
    
    elif action == "schedule":
        # Отложенная отправка
        state["step"] = "schedule_time"
        await callback.message.edit_text(
            "⏰ Отложенная отправка\n\n"
            "Введите время отправки в формате: ГГГГ-ММ-ДД ЧЧ:ММ\n"
            "Например: 2024-12-31 18:30",
            reply_markup=get_back_button()
        )
    
    elif action == "cancel":
        del broadcast_state.user_states[user_id]
        await callback.message.edit_text("🔐 Панель администратора:", reply_markup=get_admin_menu())


async def send_broadcast(text: str, admin_id: int, media_path: str = None, media_type: str = None):
    """Отправка рассылки"""
    subscribers = await db.get_subscribers()
    message_id = await db.save_message(text, media_path, media_type)
    
    sent_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        try:
            if media_path and media_type == "photo":
                await bot.send_photo(
                    chat_id=subscriber["telegram_id"],
                    photo=media_path,
                    caption=text
                )
            else:
                await bot.send_message(
                    chat_id=subscriber["telegram_id"],
                    text=text,
                    reply_markup=get_response_buttons()
                )
            
            await db.record_delivery(message_id, subscriber["id"])
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send message to {subscriber['telegram_id']}: {e}")
            failed_count += 1
    
    await db.mark_message_sent(message_id)
    
    # Отправляем отчет администратору
    report_text = (
        f"📊 Рассылка завершена\n\n"
        f"✅ Отправлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}\n"
        f"📝 Текст: {text[:100]}..."
    )
    
    await bot.send_message(admin_id, report_text, reply_markup=get_admin_menu())


async def check_scheduled_messages():
    """Проверка отложенных сообщений"""
    messages = await db.get_pending_messages()
    
    for message in messages:
        try:
            print(f"DEBUG: Отправка отложенного сообщения ID={message['id']}")
            
            # Отправляем сообщение
            await send_broadcast(
                message["text"], 
                settings.admin_id,
                message.get("media_path"),
                message.get("media_type")
            )
            
            # Обновляем статус на sent
            await db.update_message_status(message['id'], 'sent')
            print(f"DEBUG: Сообщение ID={message['id']} отправлено, статус обновлен на 'sent'")
            
        except Exception as e:
            logger.error(f"Failed to send scheduled message {message['id']}: {e}")


async def main():
    """Главная функция"""
    # Блокировка файла для предотвращения множественных экземпляров
    lock_file = "/tmp/bot.lock"
    try:
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("DEBUG: Получена блокировка, запускаем бота")
    except (IOError, OSError):
        print("ERROR: Бот уже запущен! Выход.")
        return
    
    try:
        await db.init()
        
        # Настройка планировщика для проверки отложенных сообщений
        scheduler.add_job(
            check_scheduled_messages,
            "interval",
            minutes=1,
            id="check_scheduled"
        )
        scheduler.start()
        
        # Назначаем первого администратора
        await db.make_admin(settings.admin_id)
        
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        # Освобождаем блокировку
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
            os.unlink(lock_file)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
