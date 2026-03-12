import aiosqlite
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import settings


class Database:
    def __init__(self):
        self.db_path = settings.database_path
    
    async def init(self):
        """Инициализация базы данных"""
        # Создаем директорию для базы данных, если ее нет
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"DEBUG: Создана директория {db_dir}")
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    is_subscribed BOOLEAN DEFAULT 1,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    media_path TEXT,
                    media_type TEXT,
                    scheduled_at TIMESTAMP,
                    sent_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message_id INTEGER,
                    response_type TEXT,
                    responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    user_id INTEGER,
                    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            await db.commit()
    
    async def add_user(self, telegram_id: int, username: str, first_name: str, 
                      last_name: str = None, phone: str = None) -> int:
        """Добавление нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR IGNORE INTO users 
                (telegram_id, username, first_name, last_name, phone)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, username, first_name, last_name, phone))
            await db.commit()
            return cursor.lastrowid or await self.get_user_by_telegram_id(telegram_id)
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[int]:
        """Получение ID пользователя по telegram_id"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_phone_number(self, telegram_id: int, phone_number: str) -> bool:
        """Обновление номера телефона пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE users SET phone = ? WHERE telegram_id = ?", 
                    (phone_number, telegram_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"ERROR updating phone: {e}")
                return False
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_admin FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else False
    
    async def make_admin(self, telegram_id: int) -> bool:
        """Назначение пользователя администратором"""
        async with aiosqlite.connect(self.db_path) as db:
            # Сначала проверяем, есть ли пользователь
            cursor = await db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            )
            user_exists = await cursor.fetchone()
            
            if not user_exists:
                # Если пользователя нет, создаем его
                await db.execute(
                    "INSERT INTO users (telegram_id, username, first_name, last_name, is_admin) VALUES (?, ?, ?, ?, 1)",
                    (telegram_id, "admin", "Admin", "")
                )
                print(f"DEBUG: Создан администратор telegram_id={telegram_id}")
            else:
                # Если пользователь есть, обновляем статус
                cursor = await db.execute(
                    "UPDATE users SET is_admin = 1 WHERE telegram_id = ?", 
                    (telegram_id,)
                )
                print(f"DEBUG: Обновлен статус администратора для telegram_id={telegram_id}, rowcount={cursor.rowcount}")
            
            await db.commit()
            return True
    
    async def get_subscribers(self) -> List[Dict[str, Any]]:
        """Получение всех подписчиков"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE is_subscribed = 1"
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
    
    async def save_message(self, text: str, media_path: str = None, 
                          media_type: str = None, scheduled_at: datetime = None) -> int:
        """Сохранение сообщения для рассылки"""
        async with aiosqlite.connect(self.db_path) as db:
            # Если указано время планирования, статус pending, иначе sent
            status = 'pending' if scheduled_at else 'sent'
            cursor = await db.execute("""
                INSERT INTO messages (text, media_path, media_type, status, scheduled_at)
                VALUES (?, ?, ?, ?, ?)
            """, (text, media_path, media_type, status, scheduled_at))
            await db.commit()
            return cursor.lastrowid
    
    async def save_response(self, user_id: int, message_id: int, response_type: str):
        """Сохранение ответа пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO responses (user_id, message_id, response_type)
                VALUES (?, ?, ?)
            """, (user_id, message_id, response_type))
            await db.commit()
    
    async def update_message_status(self, message_id: int, status: str) -> bool:
        """Обновление статуса сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "UPDATE messages SET status = ?, sent_at = ? WHERE id = ?",
                    (status, datetime.now(), message_id)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error updating message status: {e}")
                return False

    async def get_last_events_stats(self) -> List[Dict[str, Any]]:
        """Статистика по последним 10 отправленным сообщениям с ответами"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    m.id as message_id,
                    m.text,
                    m.sent_at,
                    u.username,
                    u.phone,
                    r.response_type,
                    r.responded_at
                FROM messages m
                LEFT JOIN responses r ON m.id = r.message_id
                LEFT JOIN users u ON r.user_id = u.id
                WHERE m.status = 'sent' AND m.sent_at IS NOT NULL
                ORDER BY m.sent_at DESC, r.responded_at DESC
                LIMIT 10
            """) as cursor:
                results = []
                current_message_id = None
                message_data = {}
                
                for row in await cursor.fetchall():
                    row_dict = dict(row)
                    
                    # Если это новое сообщение
                    if current_message_id != row_dict['message_id']:
                        if current_message_id is not None:
                            results.append(message_data)
                        
                        current_message_id = row_dict['message_id']
                        message_data = {
                            'message_id': row_dict['message_id'],
                            'text': row_dict['text'] or '',
                            'sent_at': row_dict['sent_at'],
                            'responses': []
                        }
                    
                    # Добавляем ответ, если он есть
                    if row_dict['response_type']:
                        message_data['responses'].append({
                            'username': row_dict['username'],
                            'phone': row_dict['phone'],
                            'response_type': row_dict['response_type'],
                            'responded_at': row_dict['responded_at']
                        })
                
                # Добавляем последнее сообщение
                if current_message_id is not None:
                    results.append(message_data)
                
                return results
    
    async def get_subscribers_stats(self) -> List[Dict[str, Any]]:
        """Статистика по подписчикам"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT username, phone, created_at, is_subscribed
                FROM users
                ORDER BY created_at DESC
            """) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
    
    async def toggle_subscription(self, telegram_id: int) -> bool:
        """Переключение статуса подписки"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_subscribed FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if not result:
                    return False
                
                new_status = not result[0]
                await db.execute(
                    "UPDATE users SET is_subscribed = ? WHERE telegram_id = ?", 
                    (new_status, telegram_id)
                )
                await db.commit()
                return new_status
    
    async def record_delivery(self, message_id: int, user_id: int):
        """Запись доставки сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO message_deliveries (message_id, user_id)
                VALUES (?, ?)
            """, (message_id, user_id))
            await db.commit()
    
    async def get_pending_messages(self) -> List[Dict[str, Any]]:
        """Получение отложенных сообщений"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            current_time = datetime.now()
            async with db.execute("""
                SELECT * FROM messages 
                WHERE status = 'pending' AND scheduled_at <= ?
                ORDER BY scheduled_at
            """, (current_time,)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
    
    async def mark_message_sent(self, message_id: int):
        """Пометить сообщение как отправленное"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE messages 
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (message_id,))
            await db.commit()


db = Database()
