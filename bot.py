import os
import logging
import random
import yaml
import threading
import pickle
from datetime import datetime, time, timedelta
import telebot
from telebot import types
import mimetypes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
try:
    with open("config.yml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    TOKEN = config["telegram"]["token"]
    ADMIN_ID = config["telegram"]["admin_id"]
    TIMEZONE_OFFSET = config["posts"]["timezone_offset"]
    RANDOM_OFFSET = config["posts"]["random_offset_minutes"]
    DATA_FILE = config["storage"]["data_file"]
    
except Exception as e:
    logger.error(f"Ошибка загрузки конфига: {e}")
    exit()

# Роли пользователей
ROLES = {
    "owner": 3,
    "admin": 2,
    "moderator": 1,
    "user": 0
}

class BotData:
    def __init__(self):
        self.users = {}  # {user_id: {"role": "owner/admin/moderator/user", "channels": [channel_ids]}}
        self.channels = {}  # {channel_id: {"name": "Название", "media_folder": "path", "post_text": "текст", "post_times": ["10:00", "15:00"]}}
        self.user_sessions = {}  # {user_id: {"state": "adding_media", "current_channel": channel_id, "temp_files": []}}
        self.load_data()
        
        # Инициализация владельца
        if ADMIN_ID not in self.users:
            self.users[ADMIN_ID] = {"role": "owner", "channels": list(self.channels.keys())}  # Владелец имеет доступ ко всем каналам
            self.save_data()
    
    def load_data(self):
        try:
            with open(DATA_FILE, "rb") as f:
                data = pickle.load(f)
                self.users = data.get("users", {})
                self.channels = data.get("channels", {})
                self.user_sessions = data.get("user_sessions", {})
                
                # Миграция для старых данных: добавляем поле channels если его нет
                for user_id, user_data in self.users.items():
                    if "channels" not in user_data:
                        if user_data["role"] == "owner" or user_data["role"] == "admin":
                            user_data["channels"] = list(self.channels.keys())  # Админы и владелец имеют доступ ко всем каналам
                        else:
                            user_data["channels"] = []  # Новые модераторы без доступа
                
                # Создаем папки для каналов
                for channel_id, channel_data in self.channels.items():
                    os.makedirs(channel_data["media_folder"], exist_ok=True)
                    
        except (FileNotFoundError, EOFError):
            pass
    
    def save_data(self):
        data = {
            "users": self.users,
            "channels": self.channels,
            "user_sessions": self.user_sessions
        }
        with open(DATA_FILE, "wb") as f:
            pickle.dump(data, f)
    
    def get_user_role(self, user_id):
        return self.users.get(user_id, {}).get("role", "user")
    
    def has_permission(self, user_id, required_role):
        user_role = self.get_user_role(user_id)
        return ROLES[user_role] >= ROLES[required_role]
    
    def has_channel_access(self, user_id, channel_id):
        """Проверяет, есть ли у пользователя доступ к конкретному каналу"""
        user_data = self.users.get(user_id, {})
        
        # Владелец и админы имеют доступ ко всем каналам
        if user_data.get("role") in ["owner", "admin"]:
            return True
        
        # Модераторы имеют доступ только к назначенным каналам
        if user_data.get("role") == "moderator":
            return channel_id in user_data.get("channels", [])
        
        return False
    
    def get_accessible_channels(self, user_id):
        """Возвращает список каналов, к которым есть доступ у пользователя"""
        user_data = self.users.get(user_id, {})
        
        # Владелец и админы видят все каналы
        if user_data.get("role") in ["owner", "admin"]:
            return list(self.channels.keys())
        
        # Модераторы видят только назначенные каналы
        if user_data.get("role") == "moderator":
            return user_data.get("channels", [])
        
        return []
    
    def add_channel_access(self, user_id, channel_id):
        """Добавляет доступ к каналу для модератора"""
        if user_id not in self.users or self.users[user_id]["role"] != "moderator":
            return False
        
        if channel_id not in self.channels:
            return False
        
        if "channels" not in self.users[user_id]:
            self.users[user_id]["channels"] = []
        
        if channel_id not in self.users[user_id]["channels"]:
            self.users[user_id]["channels"].append(channel_id)
            self.save_data()
            return True
        
        return False
    
    def remove_channel_access(self, user_id, channel_id):
        """Удаляет доступ к каналу у модератора"""
        if user_id not in self.users or self.users[user_id]["role"] != "moderator":
            return False
        
        if "channels" in self.users[user_id] and channel_id in self.users[user_id]["channels"]:
            self.users[user_id]["channels"].remove(channel_id)
            self.save_data()
            return True
        
        return False
    
    def add_channel(self, channel_id, name, post_text, post_times):
        media_folder = f"media/channel_{abs(channel_id)}"
        os.makedirs(media_folder, exist_ok=True)
        
        self.channels[channel_id] = {
            "name": name,
            "media_folder": media_folder,
            "post_text": post_text,
            "post_times": post_times,
            "media_queue": [],
            "used_files": set()
        }
        
        # Автоматически даем доступ к новому каналу владельцу и админам
        for uid, user_data in self.users.items():
            if user_data["role"] in ["owner", "admin"]:
                if "channels" not in user_data:
                    user_data["channels"] = []
                if channel_id not in user_data["channels"]:
                    user_data["channels"].append(channel_id)
        
        self.save_data()
    
    def add_file_to_channel(self, channel_id, file_path, file_type):
        if channel_id not in self.channels:
            return False
        
        channel = self.channels[channel_id]
        if file_path not in channel["used_files"]:
            channel["media_queue"].append({"path": file_path, "type": file_type})
            channel["used_files"].add(file_path)
            self.save_data()
            return True
        return False
    
    def get_next_file_from_channel(self, channel_id, remove=True):
        if channel_id not in self.channels:
            return None
        
        channel = self.channels[channel_id]
        if channel["media_queue"]:
            return channel["media_queue"].pop(0) if remove else channel["media_queue"][0]
        return None
    
    def start_adding_session(self, user_id, channel_id):
        self.user_sessions[user_id] = {
            "state": "adding_media",
            "current_channel": channel_id,
            "temp_files": []
        }
        self.save_data()
    
    def add_temp_file(self, user_id, file_path, file_type):
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["temp_files"].append({"path": file_path, "type": file_type})
            self.save_data()
            return True
        return False
    
    def finish_adding_session(self, user_id):
        if user_id not in self.user_sessions:
            return 0
        
        session = self.user_sessions[user_id]
        channel_id = session["current_channel"]
        added_count = 0
        
        for file_info in session["temp_files"]:
            if self.add_file_to_channel(channel_id, file_info["path"], file_info["type"]):
                added_count += 1
            else:
                if os.path.exists(file_info["path"]):
                    os.remove(file_info["path"])
        
        del self.user_sessions[user_id]
        self.save_data()
        
        return added_count
    
    def remove_user_role(self, user_id):
        if user_id in self.users and user_id != ADMIN_ID:
            role = self.users[user_id]["role"]
            del self.users[user_id]
            self.save_data()
            return role
        return None
    
    def update_channel(self, channel_id, **kwargs):
        if channel_id not in self.channels:
            return False
        
        for key, value in kwargs.items():
            if key in self.channels[channel_id] and key != "media_folder":
                self.channels[channel_id][key] = value
        
        self.save_data()
        return True
    
    def delete_channel(self, channel_id):
        if channel_id not in self.channels:
            return False
        
        # Удаляем доступ к каналу у всех пользователей
        for user_id, user_data in self.users.items():
            if "channels" in user_data and channel_id in user_data["channels"]:
                user_data["channels"].remove(channel_id)
        
        # Удаляем папку с медиа
        media_folder = self.channels[channel_id]["media_folder"]
        if os.path.exists(media_folder):
            for root, dirs, files in os.walk(media_folder, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(media_folder)
        
        del self.channels[channel_id]
        self.save_data()
        return True

class PostScheduler:
    def __init__(self, bot, bot_data):
        self.bot = bot
        self.bot_data = bot_data
        self.last_sent = {}
    
    def convert_to_utc(self, msk_time_str):
        hour, minute = map(int, msk_time_str.split(":"))
        hour_utc = (hour - TIMEZONE_OFFSET) % 24
        return time(hour_utc, minute)
    
    def calculate_post_times(self, channel_id):
        if channel_id not in self.bot_data.channels:
            return []
            
        now = datetime.now()
        post_times = []
        
        for msk_time in self.bot_data.channels[channel_id]["post_times"]:
            utc_time = self.convert_to_utc(msk_time)
            post_time = datetime.combine(now.date(), utc_time)
            
            post_time += timedelta(minutes=random.randint(-RANDOM_OFFSET, RANDOM_OFFSET))
            
            if post_time < now - timedelta(minutes=1):
                post_time += timedelta(days=1)
            
            post_times.append((msk_time, post_time))
        
        return sorted(post_times, key=lambda x: x[1])
    
    def should_send_post(self, channel_id, msk_time, post_time):
        now = datetime.now()
        date_key = post_time.date()
        
        time_diff = (now - post_time).total_seconds()
        if abs(time_diff) > 60:
            return False
        
        if channel_id not in self.last_sent:
            self.last_sent[channel_id] = {}
            
        if self.last_sent[channel_id].get(date_key, {}).get(msk_time, False):
            return False
            
        return True
    
    def check_posts(self):
        try:
            for channel_id in self.bot_data.channels.keys():
                for msk_time, post_time in self.calculate_post_times(channel_id):
                    if self.should_send_post(channel_id, msk_time, post_time):
                        if self.send_scheduled_post(channel_id):
                            date_key = post_time.date()
                            if channel_id not in self.last_sent:
                                self.last_sent[channel_id] = {}
                            if date_key not in self.last_sent[channel_id]:
                                self.last_sent[channel_id][date_key] = {}
                            self.last_sent[channel_id][date_key][msk_time] = True
                            logger.info(f"Отправлен пост в канал {channel_id} по расписанию {msk_time} МСК")
        except Exception as e:
            logger.error(f"Ошибка проверки постов: {e}")
    
    def send_scheduled_post(self, channel_id):
        file_info = self.bot_data.get_next_file_from_channel(channel_id)
        if not file_info:
            for user_id, user_data in self.bot_data.users.items():
                if self.bot_data.has_permission(user_id, "admin"):
                    try:
                        channel_name = self.bot_data.channels[channel_id]["name"]
                        self.bot.send_message(user_id, f"❌ В канале '{channel_name}' нет медиа для поста!")
                    except:
                        pass
            return False
        
        try:
            channel_data = self.bot_data.channels[channel_id]
            file_path = file_info["path"]
            file_type = file_info["type"]
            
            with open(file_path, "rb") as media_file:
                if file_type == "photo":
                    self.bot.send_photo(
                        chat_id=channel_id,
                        photo=media_file,
                        caption=channel_data["post_text"]
                    )
                elif file_type == "video":
                    self.bot.send_video(
                        chat_id=channel_id,
                        video=media_file,
                        caption=channel_data["post_text"]
                    )
            
            os.remove(file_path)
            
            remaining = len(self.bot_data.channels[channel_id]["media_queue"])
            if remaining <= 6:
                channel_name = self.bot_data.channels[channel_id]["name"]
                # Уведомляем только тех, у кого есть доступ к каналу
                for user_id, user_data in self.bot_data.users.items():
                    if self.bot_data.has_channel_access(user_id, channel_id):
                        try:
                            self.bot.send_message(
                                user_id,
                                f"⚠️ В канале '{channel_name}' осталось {remaining} медиа. Пополните запас!"
                            )
                        except:
                            pass
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки поста в канал {channel_id}: {e}")
            return False
    
    def get_schedule_info(self, user_id=None):
        """Возвращает информацию о расписании с учетом доступных каналов"""
        info = []
        now = datetime.now()
        
        # Определяем, какие каналы показывать
        if user_id is None or self.bot_data.has_permission(user_id, "admin"):
            channels_to_show = self.bot_data.channels
        else:
            accessible_channels = self.bot_data.get_accessible_channels(user_id)
            channels_to_show = {cid: data for cid, data in self.bot_data.channels.items() 
                              if cid in accessible_channels}
        
        if not channels_to_show:
            return "❌ Нет доступных каналов" if user_id else "❌ Нет добавленных каналов"
        
        for channel_id, channel_data in channels_to_show.items():
            info.append(f"📺 Канал: {channel_data['name']}")
            info.append(f"📊 Осталось медиа: {len(channel_data['media_queue'])}")
            
            channel_times = self.calculate_post_times(channel_id)
            if not channel_times:
                info.append("   ⚠️ Нет расписания")
            else:
                for i, (msk_time, post_time) in enumerate(channel_times, 1):
                    time_left = post_time - now
                    if time_left.total_seconds() < 0:
                        time_left = timedelta(0)
                    
                    hours, rem = divmod(time_left.seconds, 3600)
                    minutes, seconds = divmod(rem, 60)
                    
                    info.append(
                        f"   {i}. Через {hours:02d}:{minutes:02d}:{seconds:02d} "
                        f"(~{msk_time} МСК)"
                    )
            info.append("")
        
        return "\n".join(info)

def run_scheduler(bot, bot_data):
    scheduler = PostScheduler(bot, bot_data)
    while True:
        try:
            scheduler.check_posts()
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
        threading.Event().wait(30)

# Инициализация
bot_data = BotData()
bot = telebot.TeleBot(TOKEN)

# Запуск планировщика
threading.Thread(
    target=run_scheduler,
    args=(bot, bot_data),
    daemon=True
).start()

def create_main_keyboard(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if bot_data.has_permission(user_id, "moderator"):
        keyboard.add("📤 Добавить медиа")
    
    if bot_data.has_permission(user_id, "admin"):
        keyboard.add("👥 Управление пользователями")
    
    if bot_data.has_permission(user_id, "owner"):
        keyboard.add("📺 Управление каналами")
    
    keyboard.add("📊 Статус", "❓ Помощь")
    return keyboard

def create_channels_keyboard(user_id, action="select"):
    """Создает клавиатуру с каналами, доступными пользователю"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    accessible_channels = bot_data.get_accessible_channels(user_id)
    
    for channel_id in accessible_channels:
        if channel_id in bot_data.channels:
            keyboard.add(f"📺 {bot_data.channels[channel_id]['name']}")
    
    if not accessible_channels:
        keyboard.add("❌ Нет доступных каналов")
    
    keyboard.add("🔙 Назад")
    return keyboard

def create_all_channels_keyboard():
    """Создает клавиатуру со всеми каналами (для админов)"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for channel_id, channel_data in bot_data.channels.items():
        keyboard.add(f"📺 {channel_data['name']}")
    keyboard.add("🔙 Назад")
    return keyboard

def create_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("➕ Добавить модератора", "➕ Добавить администратора")
    keyboard.add("🔧 Назначить каналы модератору", "🗑️ Удалить пользователя")
    keyboard.add("📊 Список пользователей", "🔙 Назад")
    return keyboard

def create_owner_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("➕ Добавить канал", "📋 Список каналов")
    keyboard.add("✏️ Редактировать канал", "🗑️ Удалить канал")
    keyboard.add("🔙 Назад")
    return keyboard

def create_edit_channel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📝 Изменить название", "📝 Изменить текст")
    keyboard.add("⏰ Изменить время", "🔙 Назад")
    return keyboard

def create_moderator_management_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("➕ Добавить канал модератору", "➖ Удалить канал у модератора")
    keyboard.add("📋 Показать каналы модератора", "🔙 Назад")
    return keyboard

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    role = bot_data.get_user_role(user_id)
    
    welcome_text = f"🤖 Бот работает!\nВаша роль: {role}"
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_keyboard(user_id)
    )

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def help_command(message):
    user_id = message.from_user.id
    role = bot_data.get_user_role(user_id)
    
    help_text = f"""
📖 Справка по боту
Ваша роль: {role}

Доступные функции:
📤 Добавить медиа - загрузка фото и видео в доступные каналы
📊 Статус - информация о доступных каналах и расписании

{f"👥 Управление пользователями - добавление/удаление модераторов и администраторов, назначение каналов" if bot_data.has_permission(user_id, "admin") else ""}
{f"📺 Управление каналами - добавление/редактирование/удаление каналов" if bot_data.has_permission(user_id, "owner") else ""}

Система доступа:
• Владелец и Администраторы: доступ ко всем каналам
• Модераторы: доступ только к назначенным каналам
    """.strip()
    
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: message.text == "📊 Статус")
def status(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "moderator"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    scheduler = PostScheduler(bot, bot_data)
    status_text = scheduler.get_schedule_info(user_id)
    
    if status_text:
        bot.reply_to(message, status_text)
    else:
        bot.reply_to(message, "❌ Нет доступных каналов для просмотра")

@bot.message_handler(func=lambda message: message.text == "📤 Добавить медиа")
def add_media_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "moderator"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    accessible_channels = bot_data.get_accessible_channels(user_id)
    if not accessible_channels:
        bot.reply_to(message, "❌ У вас нет доступа ни к одному каналу. Обратитесь к администратору.")
        return
    
    bot.send_message(
        message.chat.id,
        "Выберите канал для загрузки медиа:",
        reply_markup=create_channels_keyboard(user_id)
    )

@bot.message_handler(func=lambda message: message.text.startswith("📺") and message.text != "📺 Управление каналами")
def select_channel(message):
    user_id = message.from_user.id
    channel_name = message.text[2:].strip()
    
    # Находим канал по имени среди доступных
    channel_id = None
    accessible_channels = bot_data.get_accessible_channels(user_id)
    
    for cid, data in bot_data.channels.items():
        if data["name"] == channel_name and cid in accessible_channels:
            channel_id = cid
            break
    
    if not channel_id:
        bot.reply_to(message, "❌ Канал не найден или нет доступа")
        return
    
    # Проверяем контекст выбора
    if user_id in bot_data.user_sessions:
        session_state = bot_data.user_sessions[user_id]["state"]
        
        if session_state == "edit_channel":
            msg = bot.send_message(
                message.chat.id,
                f"Выбран канал: {channel_name}\nВыберите действие:",
                reply_markup=create_edit_channel_keyboard()
            )
            bot_data.user_sessions[user_id]["current_channel"] = channel_id
        
        elif session_state == "add_channel_to_moderator":
            target_user_id = bot_data.user_sessions[user_id].get("target_user_id")
            if target_user_id and bot_data.add_channel_access(target_user_id, channel_id):
                bot.reply_to(message, f"✅ Канал '{channel_name}' добавлен модератору {target_user_id}")
            else:
                bot.reply_to(message, "❌ Ошибка при добавлении канала")
            del bot_data.user_sessions[user_id]
        
        elif session_state == "remove_channel_from_moderator":
            target_user_id = bot_data.user_sessions[user_id].get("target_user_id")
            if target_user_id and bot_data.remove_channel_access(target_user_id, channel_id):
                bot.reply_to(message, f"✅ Канал '{channel_name}' удален у модератора {target_user_id}")
            else:
                bot.reply_to(message, "❌ Ошибка при удалении канала")
            del bot_data.user_sessions[user_id]
    
    else:
        # Обычное добавление медиа
        bot_data.start_adding_session(user_id, channel_id)
        bot.send_message(
            message.chat.id,
            f"✅ Выбран канал: {channel_name}\nТеперь присылайте фото или видео. Когда закончите, нажмите '✅ Завершить загрузку'",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Завершить загрузку")
        )

@bot.message_handler(func=lambda message: message.text == "✅ Завершить загрузку")
def finish_upload(message):
    user_id = message.from_user.id
    
    if user_id not in bot_data.user_sessions:
        bot.reply_to(message, "❌ Нет активной сессии загрузки")
        return
    
    added_count = bot_data.finish_adding_session(user_id)
    
    bot.send_message(
        message.chat.id,
        f"✅ Загрузка завершена! Добавлено {added_count} медиафайлов",
        reply_markup=create_main_keyboard(user_id)
    )

@bot.message_handler(content_types=["photo", "video"])
def handle_media(message):
    user_id = message.from_user.id
    
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "adding_media":
        if bot_data.has_permission(user_id, "moderator"):
            bot.reply_to(message, "❌ Сначала выберите канал через меню '📤 Добавить медиа'")
        else:
            bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    try:
        session = bot_data.user_sessions[user_id]
        channel_id = session["current_channel"]
        
        # Проверяем доступ к каналу
        if not bot_data.has_channel_access(user_id, channel_id):
            bot.reply_to(message, "❌ Доступ к этому каналу запрещен")
            return
        
        if message.content_type == "photo":
            file_info = bot.get_file(message.photo[-1].file_id)
            file_type = "photo"
            ext = "jpg"
        else:  # video
            file_info = bot.get_file(message.video.file_id)
            file_type = "video"
            ext = "mp4"
        
        downloaded = bot.download_file(file_info.file_path)
        
        media_folder = bot_data.channels[channel_id]["media_folder"]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(media_folder, f"{file_type}_{timestamp}_{file_info.file_id}.{ext}")
        
        with open(file_path, "wb") as f:
            f.write(downloaded)
        
        bot_data.add_temp_file(user_id, file_path, file_type)
        
        temp_count = len(session["temp_files"])
        bot.reply_to(message, f"✅ {file_type.capitalize()} добавлено (временное). Всего в сессии: {temp_count}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при добавлении: {e}")

@bot.message_handler(func=lambda message: message.text == "👥 Управление пользователями")
def manage_users(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    bot.send_message(
        message.chat.id,
        "Управление пользователями:",
        reply_markup=create_admin_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "➕ Добавить модератора")
def add_moderator_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    msg = bot.reply_to(message, "Пришлите user_id пользователя для добавления модератором:")
    bot.register_next_step_handler(msg, add_moderator_finish)

def add_moderator_finish(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        return
    
    try:
        new_moderator_id = int(message.text)
        bot_data.users[new_moderator_id] = {"role": "moderator", "channels": []}
        bot_data.save_data()
        bot.reply_to(message, f"✅ Пользователь {new_moderator_id} добавлен как модератор. Теперь назначьте ему каналы через меню '🔧 Назначить каналы модератору'")
    except ValueError:
        bot.reply_to(message, "❌ Неверный user_id")

@bot.message_handler(func=lambda message: message.text == "➕ Добавить администратора")
def add_admin_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    msg = bot.reply_to(message, "Пришлите user_id пользователя для добавления администратором:")
    bot.register_next_step_handler(msg, add_admin_finish)

def add_admin_finish(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        return
    
    try:
        new_admin_id = int(message.text)
        bot_data.users[new_admin_id] = {"role": "admin", "channels": list(bot_data.channels.keys())}
        bot_data.save_data()
        bot.reply_to(message, f"✅ Пользователь {new_admin_id} добавлен как администратор (имеет доступ ко всем каналам)")
    except ValueError:
        bot.reply_to(message, "❌ Неверный user_id")

@bot.message_handler(func=lambda message: message.text == "🔧 Назначить каналы модератору")
def manage_moderator_channels_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    msg = bot.reply_to(message, "Пришлите user_id модератора для управления каналами:")
    bot.register_next_step_handler(msg, select_moderator_for_channels)

def select_moderator_for_channels(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        return
    
    try:
        moderator_id = int(message.text)
        
        # Проверяем, что это модератор
        if moderator_id not in bot_data.users or bot_data.users[moderator_id]["role"] != "moderator":
            bot.reply_to(message, "❌ Этот пользователь не является модератором")
            return
        
        # Сохраняем ID модератора в сессии
        bot_data.user_sessions[user_id] = {
            "state": "manage_moderator_channels",
            "target_user_id": moderator_id
        }
        
        bot.send_message(
            message.chat.id,
            f"Управление каналами модератора {moderator_id}:",
            reply_markup=create_moderator_management_keyboard()
        )
    except ValueError:
        bot.reply_to(message, "❌ Неверный user_id")

@bot.message_handler(func=lambda message: message.text == "➕ Добавить канал модератору")
def add_channel_to_moderator(message):
    user_id = message.from_user.id
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "manage_moderator_channels":
        return
    
    bot_data.user_sessions[user_id]["state"] = "add_channel_to_moderator"
    
    bot.send_message(
        message.chat.id,
        "Выберите канал для добавления модератору:",
        reply_markup=create_all_channels_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "➖ Удалить канал у модератора")
def remove_channel_from_moderator(message):
    user_id = message.from_user.id
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "manage_moderator_channels":
        return
    
    target_user_id = bot_data.user_sessions[user_id].get("target_user_id")
    if not target_user_id:
        return
    
    # Получаем каналы модератора
    moderator_channels = bot_data.users[target_user_id].get("channels", [])
    
    if not moderator_channels:
        bot.reply_to(message, "❌ У этого модератора нет назначенных каналов")
        return
    
    # Создаем клавиатуру только с каналами модератора
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for channel_id in moderator_channels:
        if channel_id in bot_data.channels:
            keyboard.add(f"📺 {bot_data.channels[channel_id]['name']}")
    keyboard.add("🔙 Назад")
    
    bot_data.user_sessions[user_id]["state"] = "remove_channel_from_moderator"
    
    bot.send_message(
        message.chat.id,
        "Выберите канал для удаления у модератора:",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == "📋 Показать каналы модератора")
def show_moderator_channels(message):
    user_id = message.from_user.id
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "manage_moderator_channels":
        return
    
    target_user_id = bot_data.user_sessions[user_id].get("target_user_id")
    if not target_user_id:
        return
    
    moderator_data = bot_data.users.get(target_user_id, {})
    if moderator_data.get("role") != "moderator":
        bot.reply_to(message, "❌ Этот пользователь не является модератором")
        return
    
    channels_list = bot_data.users[target_user_id].get("channels", [])
    
    if not channels_list:
        bot.reply_to(message, f"📋 У модератора {target_user_id} нет назначенных каналов")
        return
    
    text = f"📋 Каналы модератора {target_user_id}:\n\n"
    for channel_id in channels_list:
        if channel_id in bot_data.channels:
            text += f"📺 {bot_data.channels[channel_id]['name']} (ID: {channel_id})\n"
    
    bot.reply_to(message, text)

@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить пользователя")
def remove_user_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    msg = bot.reply_to(message, "Пришлите user_id пользователя для удаления из роли (нельзя удалить владельца):")
    bot.register_next_step_handler(msg, remove_user_finish)

def remove_user_finish(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "admin"):
        return
    
    try:
        remove_id = int(message.text)
        if remove_id == ADMIN_ID:
            bot.reply_to(message, "❌ Нельзя удалить владельца бота")
            return
        
        removed_role = bot_data.remove_user_role(remove_id)
        if removed_role:
            bot.reply_to(message, f"✅ Пользователь {remove_id} (роль: {removed_role}) удален")
        else:
            bot.reply_to(message, f"❌ Пользователь {remove_id} не найден или является владельцем")
    except ValueError:
        bot.reply_to(message, "❌ Неверный user_id")

@bot.message_handler(func=lambda message: message.text == "📺 Управление каналами")
def manage_channels(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    bot.send_message(
        message.chat.id,
        "Управление каналами:",
        reply_markup=create_owner_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "➕ Добавить канал")
def add_channel_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    msg = bot.reply_to(message, "Пришлите ID канала (например: -1001234567890):")
    bot.register_next_step_handler(msg, add_channel_step2)

def add_channel_step2(message):
    try:
        channel_id = int(message.text)
        msg = bot.reply_to(message, "Пришлите название канала:")
        bot.register_next_step_handler(msg, add_channel_step3, channel_id)
    except ValueError:
        bot.reply_to(message, "❌ Неверный ID канала. Должен быть числом (например: -1001234567890)")

def add_channel_step3(message, channel_id):
    channel_name = message.text
    msg = bot.reply_to(message, "Пришлите текст для постов:")
    bot.register_next_step_handler(msg, add_channel_step4, channel_id, channel_name)

def add_channel_step4(message, channel_id, channel_name):
    post_text = message.text
    msg = bot.reply_to(message, "Пришлите время постов через запятую (например: 10:00, 15:00, 20:00):")
    bot.register_next_step_handler(msg, add_channel_finish, channel_id, channel_name, post_text)

def add_channel_finish(message, channel_id, channel_name, post_text):
    try:
        times = [time.strip() for time in message.text.split(",")]
        for t in times:
            if not t.replace(':', '').isdigit() or len(t.split(':')) != 2:
                raise ValueError(f"Неверный формат времени: {t}")
        
        bot_data.add_channel(channel_id, channel_name, post_text, times)
        bot.reply_to(message, f"✅ Канал '{channel_name}' успешно добавлен!\nID: {channel_id}\nТекст: {post_text}\nВремя: {', '.join(times)}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при добавлении канала: {e}")

@bot.message_handler(func=lambda message: message.text == "✏️ Редактировать канал")
def edit_channel_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    if not bot_data.channels:
        bot.reply_to(message, "❌ Нет добавленных каналов")
        return
    
    # Создаем сессию для редактирования
    bot_data.user_sessions[user_id] = {
        "state": "edit_channel",
        "current_channel": None
    }
    
    bot.send_message(
        message.chat.id,
        "Выберите канал для редактирования:",
        reply_markup=create_all_channels_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "📝 Изменить название")
def edit_channel_name(message):
    user_id = message.from_user.id
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "edit_channel":
        return
    
    channel_id = bot_data.user_sessions[user_id]["current_channel"]
    if not channel_id:
        return
    
    msg = bot.reply_to(message, "Пришлите новое название канала:")
    bot.register_next_step_handler(msg, edit_channel_name_finish, channel_id)

def edit_channel_name_finish(message, channel_id):
    new_name = message.text
    if bot_data.update_channel(channel_id, name=new_name):
        bot.reply_to(message, f"✅ Название канала изменено на: {new_name}")
    else:
        bot.reply_to(message, "❌ Ошибка при изменении названия")

@bot.message_handler(func=lambda message: message.text == "📝 Изменить текст")
def edit_channel_text(message):
    user_id = message.from_user.id
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "edit_channel":
        return
    
    channel_id = bot_data.user_sessions[user_id]["current_channel"]
    if not channel_id:
        return
    
    msg = bot.reply_to(message, "Пришлите новый текст для постов:")
    bot.register_next_step_handler(msg, edit_channel_text_finish, channel_id)

def edit_channel_text_finish(message, channel_id):
    new_text = message.text
    if bot_data.update_channel(channel_id, post_text=new_text):
        bot.reply_to(message, f"✅ Текст постов изменен")
    else:
        bot.reply_to(message, "❌ Ошибка при изменении текста")

@bot.message_handler(func=lambda message: message.text == "⏰ Изменить время")
def edit_channel_time(message):
    user_id = message.from_user.id
    if user_id not in bot_data.user_sessions or bot_data.user_sessions[user_id]["state"] != "edit_channel":
        return
    
    channel_id = bot_data.user_sessions[user_id]["current_channel"]
    if not channel_id:
        return
    
    msg = bot.reply_to(message, "Пришлите новое время постов через запятую (например: 10:00, 15:00, 20:00):")
    bot.register_next_step_handler(msg, edit_channel_time_finish, channel_id)

def edit_channel_time_finish(message, channel_id):
    try:
        times = [time.strip() for time in message.text.split(",")]
        for t in times:
            if not t.replace(':', '').isdigit() or len(t.split(':')) != 2:
                raise ValueError(f"Неверный формат времени: {t}")
        
        if bot_data.update_channel(channel_id, post_times=times):
            bot.reply_to(message, f"✅ Время постов изменено на: {', '.join(times)}")
        else:
            bot.reply_to(message, "❌ Ошибка при изменении времени")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить канал")
def delete_channel_start(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        bot.reply_to(message, "⛔ Недостаточно прав")
        return
    
    if not bot_data.channels:
        bot.reply_to(message, "❌ Нет добавленных каналов")
        return
    
    # Показываем список каналов для удаления
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for channel_id, channel_data in bot_data.channels.items():
        keyboard.add(f"🗑️ {channel_data['name']}")
    keyboard.add("🔙 Назад")
    
    bot.send_message(
        message.chat.id,
        "Выберите канал для удаления (все медиафайлы будут удалены):",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text.startswith("🗑️") and not message.text.startswith("🗑️ Удалить"))
def delete_channel_execute(message):
    user_id = message.from_user.id
    if not bot_data.has_permission(user_id, "owner"):
        return
    
    channel_name = message.text[2:].strip()
    
    # Находим канал по имени
    channel_id = None
    for cid, data in bot_data.channels.items():
        if data["name"] == channel_name:
            channel_id = cid
            break
    
    if not channel_id:
        bot.reply_to(message, "❌ Канал не найден")
        return
    
    # Удаляем канал
    if bot_data.delete_channel(channel_id):
        bot.reply_to(message, f"✅ Канал '{channel_name}' успешно удален")
    else:
        bot.reply_to(message, "❌ Ошибка при удалении канала")

@bot.message_handler(func=lambda message: message.text in ["🔙 Назад", "📋 Список каналов", "📊 Список пользователей"])
def handle_back_and_lists(message):
    user_id = message.from_user.id
    
    if message.text == "🔙 Назад":
        # Очищаем сессии при возврате
        if user_id in bot_data.user_sessions:
            # Если мы в меню управления каналами модератора, возвращаемся к списку действий
            if bot_data.user_sessions[user_id]["state"] == "manage_moderator_channels":
                bot.send_message(
                    message.chat.id,
                    f"Управление каналами модератора {bot_data.user_sessions[user_id].get('target_user_id', '')}:",
                    reply_markup=create_moderator_management_keyboard()
                )
                return
            
            # Если в режиме редактирования канала, возвращаемся к выбору действия
            if bot_data.user_sessions[user_id]["state"] == "edit_channel":
                bot.send_message(
                    message.chat.id,
                    "Выберите канал для редактирования:",
                    reply_markup=create_all_channels_keyboard()
                )
                return
            
            # Очищаем другие сессии
            del bot_data.user_sessions[user_id]
        
        # Возврат в главное меню
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=create_main_keyboard(user_id)
        )
    
    elif message.text == "📋 Список каналов":
        if not bot_data.has_permission(user_id, "owner"):
            return
        
        if not bot_data.channels:
            bot.reply_to(message, "❌ Нет добавленных каналов")
            return
        
        channels_list = "📋 Список всех каналов:\n\n"
        for channel_id, channel_data in bot_data.channels.items():
            channels_list += f"📺 {channel_data['name']}\n"
            channels_list += f"   ID: {channel_id}\n"
            channels_list += f"   Очередь: {len(channel_data['media_queue'])} медиа\n"
            channels_list += f"   Время постов: {', '.join(channel_data['post_times'])}\n\n"
        
        bot.reply_to(message, channels_list)
    
    elif message.text == "📊 Список пользователей":
        if not bot_data.has_permission(user_id, "admin"):
            return
        
        users_list = "👥 Список пользователей:\n\n"
        for uid, user_data in bot_data.users.items():
            role_icon = "👑" if user_data['role'] == "owner" else "🛡️" if user_data['role'] == "admin" else "🛠️"
            role_text = user_data['role']
            
            # Добавляем информацию о каналах для модераторов
            if user_data['role'] == "moderator":
                channel_count = len(user_data.get("channels", []))
                role_text += f" ({channel_count} каналов)"
            
            users_list += f"{role_icon} {uid}: {role_text}\n"
        
        bot.reply_to(message, users_list)

if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()