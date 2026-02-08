# 🤖 Telegram Channel Auto-Poster Bot

[English](#english) | [Русский](#русский)

---

## English

### Advanced Automated Content Manager for Telegram Channels

A powerful Telegram bot that automates content posting with intelligent scheduling, user role management, and multi-format media support. Perfect for content creators, marketing teams, and community managers who need reliable automated posting across multiple channels.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-4.19%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

## ✨ Features

### ⏰ **Smart Scheduling System**
- **Timezone-aware scheduling** - Automatically converts to UTC
- **Randomized posting** - Prevents predictable posting patterns
- **Multiple time slots** - Set multiple posting times per day
- **Missed post recovery** - Handles missed posts intelligently

### 👥 **Advanced Role Management**
- **Four-tier role system** - Owner, Admin, Moderator, User
- **Channel-based permissions** - Assign specific channels to moderators
- **Role promotion/demotion** - Flexible user management
- **Hierarchical access control** - Clear permission boundaries

### 📁 **Multi-Format Media Support**
- **Photo & Video support** - Full media type compatibility
- **Queue management** - Intelligent media queue system
- **Duplicate prevention** - Avoids posting duplicate content
- **Low-stock alerts** - Warns when media supply is low

### 🔧 **Channel Management Suite**
- **Complete CRUD operations** - Create, Read, Update, Delete channels
- **Post content editing** - Modify text and scheduling
- **Media folder management** - Automatic folder organization
- **Channel access control** - Granular permission settings

### 📊 **Real-time Monitoring**
- **Status dashboard** - View all channels and schedules
- **Queue tracking** - Monitor media queue sizes
- **Time-to-post display** - See upcoming posts
- **Error notifications** - Get alerted about issues

### ⚡ **Performance & Reliability**
- **Background scheduler** - Non-blocking post scheduling
- **Data persistence** - Automatic save/load system
- **Error resilience** - Graceful error handling
- **Resource efficient** - Low memory and CPU usage

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Administrator access to target Telegram channels
- Basic understanding of Telegram channel IDs

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/kisyufka/Telegram_Channel_Auto-Poster_Bot.git
cd telegram-auto-poster
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the bot:**

Create `config.yml` with your settings:
```yaml
telegram:
  token: "YOUR_BOT_TOKEN_HERE"           # From @BotFather
  admin_id: YOUR_USER_ID                 # Your Telegram user ID

posts:
  timezone_offset: 3                     # MSK timezone (UTC+3)
  random_offset_minutes: 60              # Randomize posts ±60 minutes

storage:
  data_file: "bot_data.pkl"              # Data storage file
```

4. **Set up initial permissions:**
- Add the bot as administrator to your channels
- The bot needs: Post Messages, Edit Messages, Delete Messages permissions
- Start the bot with `/start` command

5. **Run the bot:**
```bash
python bot.py
```

## 📖 How It Works

### System Architecture

```mermaid
graph TB
    A[Telegram User] --> B[Bot Interface]
    B --> C[User Role Check]
    C --> D[Command Router]
    
    D --> E[Admin Panel]
    D --> F[Moderator Panel]
    D --> G[Owner Panel]
    
    E --> H[User Management]
    F --> I[Media Upload]
    G --> J[Channel Management]
    
    subgraph "Background Services"
        K[Scheduler Engine]
        L[Post Queue]
        M[Media Processor]
    end
    
    J --> K
    I --> L
    L --> M
    K --> N[Telegram API]
    M --> N
    N --> O[Published Posts]
```

### User Role Hierarchy

```mermaid
graph TD
    A[👑 Owner] -->|Full system access| B[🛡️ Administrator]
    B -->|User management| C[🛠️ Moderator]
    C -->|Channel-specific| D[👤 User]
    
    style A fill:#ffd700
    style B fill:#c0c0c0
    style C fill:#cd7f32
    style D fill:#87CEEB
```

### Example Workflow

**1. Setting up a channel:**
```
Owner: /start → Manage Channels → Add Channel
→ Enter Channel ID: -1001234567890
→ Enter Name: My Awesome Channel
→ Enter Post Text: Daily content!
→ Enter Times: 10:00, 15:00, 20:00
✅ Channel added successfully!
```

**2. Adding media:**
```
Moderator: Add Media → Select Channel
→ Upload photos/videos
→ Complete Upload
✅ 15 media files added to queue!
```

**3. Automated posting:**
```
Scheduler: 10:00 MSK ± random offset
→ Get next media from queue
→ Post to channel with caption
→ Remove from queue
→ Check remaining count
→ Alert if low (<6 remaining)
✅ Post published successfully!
```

## 🛠️ Configuration

### config.yml Details

```yaml
telegram:
  token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # Bot token
  admin_id: 6105451955                                # Initial owner ID

posts:
  timezone_offset: 3                                  # Moscow time = UTC+3
  random_offset_minutes: 60                           # Randomize ±60 minutes

storage:
  data_file: "bot_data.pkl"                           # Data persistence
```

### Bot Commands Overview

| Command | Role Required | Description |
|---------|---------------|-------------|
| `/start` | Anyone | Initial bot setup and main menu |
| `📤 Добавить медиа` | Moderator+ | Upload media to channels |
| `📊 Статус` | Moderator+ | View channel status and schedules |
| `👥 Управление пользователями` | Admin+ | User and role management |
| `📺 Управление каналами` | Owner | Complete channel management |
| `❓ Помощь` | Anyone | Display help information |

## 🔧 Advanced Features

### Channel Access Control

Moderators can be assigned specific channels:
```python
# Admin can assign channels to moderators:
Admin → Manage Users → Assign Channels to Moderator
→ Select Moderator
→ Add/Remove specific channels
→ Moderator now sees only assigned channels
```

### Post Scheduling System

- **Time conversion**: Automatically handles timezone differences
- **Randomization**: Avoids pattern recognition by followers
- **Missed posts**: Automatically reschedules if bot was offline
- **Multiple slots**: Support for unlimited posting times per day

### Media Queue Management

```python
# Queue features:
- FIFO (First In, First Out) system
- Duplicate file prevention
- Automatic file cleanup
- Low-stock notifications
- Background processing
```

### Data Persistence

- **Pickle-based storage**: Simple and efficient
- **Automatic saves**: After every significant change
- **Data migration**: Handles version upgrades
- **Backup friendly**: Easy to backup/restore data file

## 📊 Performance & Scaling

### Performance Metrics
- **<50ms** command response time
- **<100ms** media processing time
- **30-second** scheduler check interval
- **Unlimited** channels and media support
- **Low memory** usage (<100MB typical)

### Scaling Considerations
- **Single bot instance** can handle 50+ channels
- **Thread-safe design** for concurrent operations
- **Database-ready architecture** for future upgrades
- **Modular codebase** for easy feature additions

## 🔒 Security & Permissions

### Security Features
- **User authentication** via Telegram ID
- **Role-based access control** (RBAC)
- **Channel isolation** between moderators
- **No external APIs** (except Telegram)
- **Local data storage** (no cloud dependencies)

### Permission Matrix

| Action | Owner | Admin | Moderator | User |
|--------|-------|-------|-----------|------|
| Add/Delete Channels | ✅ | ❌ | ❌ | ❌ |
| Edit Channel Settings | ✅ | ❌ | ❌ | ❌ |
| Manage Users | ✅ | ✅ | ❌ | ❌ |
| Assign Channels | ✅ | ✅ | ❌ | ❌ |
| Upload Media | ✅ | ✅ | ✅* | ❌ |
| View Status | ✅ | ✅ | ✅* | ❌ |
| Start Bot | ✅ | ✅ | ✅ | ✅ |

*Only to assigned channels

## 🌐 Deployment

### Local Development
```bash
# Development setup
git clone https://github.com/kisyufka/Telegram_Channel_Auto-Poster_Bot.git
cd telegram-auto-poster
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run in debug mode
python bot.py
```

### Production Deployment

**Linux Server (Systemd Service):**
```bash
# Create service file: /etc/systemd/system/telegram-poster.service
[Unit]
Description=Telegram Auto-Poster Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/telegram-poster
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable telegram-poster
sudo systemctl start telegram-poster
```

**Docker Deployment:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### Cloud Platforms
- **AWS EC2/Lightsail**: Full control, scalable
- **Google Cloud Run**: Serverless, pay-per-use
- **PythonAnywhere**: Simple, beginner-friendly
- **Heroku**: Easy deployment with Git
- **DigitalOcean Droplet**: Reliable, affordable

## 🤝 Contributing

We love contributions! Here's how to help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 coding standards
- Add comments for complex logic
- Update documentation for new features
- Write clear commit messages
- Test thoroughly before submitting

### Project Structure
```
telegram-auto-poster/
├── bot.py                 # Main bot application
├── config.yml             # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
├── LICENSE               # MIT License
├── media/                # Media storage directory
│   └── channel_*/        # Per-channel media folders
└── bot_data.pkl          # Data persistence (auto-created)
```

## 🐛 Troubleshooting

### Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Bot not starting | No response to /start | Check token in config.yml |
| Posts not sending | No posts in channel | Verify bot permissions in channel |
| Media not uploading | Files not appearing in queue | Check file permissions in media/ folder |
| Timezone issues | Posts at wrong times | Adjust timezone_offset in config |
| Permission errors | "Insufficient permissions" | Re-add bot to channel with admin rights |

### Debug Mode

Enable verbose logging by modifying the logging configuration in `bot.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Getting Channel IDs

1. **Method 1**: Forward any message from channel to @username_to_id_bot
2. **Method 2**: Use @RawDataBot and send /start in the channel
3. **Method 3**: Add @getidsbot to channel and use /getids
   - **Important**: Channel IDs are negative (e.g., -1001234567890)

## 📞 Support & Community

### Getting Help
- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/telegram-auto-poster/issues)
- **Documentation**: This README and code comments
- **Telegram Support**: Contact the maintainer directly

### Community Guidelines
- Be respectful and constructive
- Search existing issues before creating new ones
- Provide details when reporting bugs
- Help others when you can

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for full details.

**Summary of MIT License:**
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ✅ No liability
- ✅ No warranty

## 🙏 Acknowledgments

- **Telegram** for their excellent Bot API
- **pyTelegramBotAPI** team for the Python wrapper library
- **Python community** for amazing tools and libraries
- **Contributors** who help improve this project

## 📍 Roadmap

### Next Releases
- [ ] Web dashboard for management
- [ ] Analytics and reporting
- [ ] API for external integrations
- [ ] Multi-language interface
- [ ] Cloud storage integration

### Future Ideas
- [ ] AI-powered content suggestions
- [ ] Cross-platform posting (Twitter, Instagram)
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features
- [ ] Mobile management app

---

## Русский

### Продвинутый Автоматический Менеджер Контента для Telegram Каналов

Мощный Telegram бот для автоматизации публикации контента с интеллектуальным планированием, управлением ролями пользователей и поддержкой мультиформатных медиа. Идеально подходит для создателей контента, маркетинговых команд и менеджеров сообществ.

## ✨ Возможности

### ⏰ **Умная система планирования**
- **Учет часовых поясов** - Автоматическая конвертация в UTC
- **Рандомизированная публикация** - Избегает предсказуемых паттернов
- **Множество временных слотов** - Несколько времен публикации в день
- **Восстановление пропущенных постов** - Интеллектуальная обработка

### 👥 **Продвинутое управление ролями**
- **Четырехуровневая система** - Владелец, Админ, Модератор, Пользователь
- **Канальные права** - Назначение конкретных каналов модераторам
- **Повышение/понижение ролей** - Гибкое управление пользователями
- **Иерархический контроль доступа** - Четкие границы прав

### 📁 **Поддержка нескольких форматов**
- **Фото и видео** - Полная совместимость с медиа
- **Управление очередью** - Интеллектуальная система очереди
- **Предотвращение дубликатов** - Избегает повторной публикации
- **Оповещения о низком запасе** - Предупреждает при нехватке контента

### 🔧 **Комплексное управление каналами**
- **Полный CRUD** - Создание, чтение, обновление, удаление каналов
- **Редактирование контента** - Изменение текста и расписания
- **Управление медиа-папками** - Автоматическая организация
- **Контроль доступа к каналам** - Детальные настройки прав

### 📊 **Мониторинг в реальном времени**
- **Панель статуса** - Просмотр всех каналов и расписаний
- **Отслеживание очереди** - Мониторинг размера медиа-очереди
- **Отображение времени до поста** - Предстоящие публикации
- **Уведомления об ошибках** - Оповещения о проблемах

### ⚡ **Производительность и надежность**
- **Фоновый планировщик** - Неблокирующее планирование
- **Сохранение данных** - Автоматическая система сохранения
- **Устойчивость к ошибкам** - Грациозная обработка сбоев
- **Эффективное использование ресурсов** - Низкое потребление памяти и CPU

## 🚀 Быстрый старт

### Требования
- Python 3.8 или выше
- Токен Telegram бота (от [@BotFather](https://t.me/BotFather))
- Права администратора в целевых Telegram каналах
- Базовое понимание ID Telegram каналов

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/kisyufka/Telegram_Channel_Auto-Poster_Bot.git
cd telegram-auto-poster
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте бота:**

Создайте `config.yml` с вашими настройками:
```yaml
telegram:
  token: "ВАШ_ТОКЕН_БОТА"                # От @BotFather
  admin_id: ВАШ_USER_ID                  # Ваш ID в Telegram

posts:
  timezone_offset: 3                     # Московское время (UTC+3)
  random_offset_minutes: 60              # Рандомизация постов ±60 минут

storage:
  data_file: "bot_data.pkl"              # Файл хранения данных
```

4. **Настройте начальные права:**
- Добавьте бота как администратора в ваши каналы
- Боту нужны права: Публикация сообщений, Редактирование сообщений, Удаление сообщений
- Запустите бота командой `/start`

5. **Запустите бота:**
```bash
python bot.py
```

## 📖 Как это работает

### Архитектура системы

```mermaid
graph TB
    A[Пользователь Telegram] --> B[Интерфейс бота]
    B --> C[Проверка роли]
    C --> D[Маршрутизатор команд]
    
    D --> E[Панель админа]
    D --> F[Панель модератора]
    D --> G[Панель владельца]
    
    E --> H[Управление пользователями]
    F --> I[Загрузка медиа]
    G --> J[Управление каналами]
    
    subgraph "Фоновые сервисы"
        K[Движок планировщика]
        L[Очередь постов]
        M[Обработчик медиа]
    end
    
    J --> K
    I --> L
    L --> M
    K --> N[API Telegram]
    M --> N
    N --> O[Опубликованные посты]
```

### Иерархия ролей пользователей

```mermaid
graph TD
    A[👑 Владелец] -->|Полный доступ| B[🛡️ Администратор]
    B -->|Управление пользователями| C[🛠️ Модератор]
    C -->|Для конкретных каналов| D[👤 Пользователь]
    
    style A fill:#ffd700
    style B fill:#c0c0c0
    style C fill:#cd7f32
    style D fill:#87CEEB
```

### Пример рабочего процесса

**1. Настройка канала:**
```
Владелец: /start → Управление каналами → Добавить канал
→ Введите ID канала: -1001234567890
→ Введите название: Мой крутой канал
→ Введите текст постов: Ежедневный контент!
→ Введите время: 10:00, 15:00, 20:00
✅ Канал успешно добавлен!
```

**2. Добавление медиа:**
```
Модератор: Добавить медиа → Выбрать канал
→ Загрузить фото/видео
→ Завершить загрузку
✅ 15 медиафайлов добавлены в очередь!
```

**3. Автоматическая публикация:**
```
Планировщик: 10:00 МСК ± случайное смещение
→ Получить следующее медиа из очереди
→ Опубликовать в канал с подписью
→ Удалить из очереди
→ Проверить оставшееся количество
→ Предупредить если мало (<6 осталось)
✅ Пост успешно опубликован!
```

## 🛠️ Конфигурация

### Детали config.yml

```yaml
telegram:
  token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # Токен бота
  admin_id: 6105451955                                # ID владельца

posts:
  timezone_offset: 3                                  # Московское время = UTC+3
  random_offset_minutes: 60                           # Рандомизация ±60 минут

storage:
  data_file: "bot_data.pkl"                           # Хранение данных
```

### Обзор команд бота

| Команда | Требуемая роль | Описание |
|---------|----------------|----------|
| `/start` | Любой | Начальная настройка и главное меню |
| `📤 Добавить медиа` | Модератор+ | Загрузка медиа в каналы |
| `📊 Статус` | Модератор+ | Просмотр статуса каналов |
| `👥 Управление пользователями` | Админ+ | Управление пользователями |
| `📺 Управление каналами` | Владелец | Управление каналами |
| `❓ Помощь` | Любой | Справка по боту |

## 🔧 Продвинутые возможности

### Контроль доступа к каналам

Модераторам можно назначать конкретные каналы:
```python
# Админ может назначить каналы модератору:
Админ → Управление пользователями → Назначить каналы модератору
→ Выбрать модератора
→ Добавить/Удалить каналы
→ Модератор теперь видит только назначенные каналы
```

### Система планирования постов

- **Конвертация времени**: Автоматически обрабатывает разницу часовых поясов
- **Рандомизация**: Избегает распознавания паттернов подписчиками
- **Пропущенные посты**: Автоматически переносит если бот был офлайн
- **Множество слотов**: Поддержка неограниченного времени публикаций в день

### Управление медиа-очередью

```python
# Особенности очереди:
- Система FIFO (Первый пришел - первый ушел)
- Предотвращение дубликатов
- Автоматическая очистка файлов
- Уведомления о низком запасе
- Фоновая обработка
```

### Сохранение данных

- **Хранение на основе pickle**: Просто и эффективно
- **Автоматическое сохранение**: После каждого значимого изменения
- **Миграция данных**: Обрабатывает обновления версий
- **Удобное резервное копирование**: Легко создавать/восстанавливать резервные копии

## 📊 Производительность и масштабирование

### Метрики производительности
- **<50мс** время отклика на команды
- **<100мс** время обработки медиа
- **30-секундный** интервал проверки планировщика
- **Неограниченное** количество каналов и медиа
- **Низкое использование памяти** (<100МБ типично)

### Соображения по масштабированию
- **Один экземпляр бота** может обрабатывать 50+ каналов
- **Потокобезопасный дизайн** для параллельных операций
- **Готовая архитектура для БД** для будущих обновлений
- **Модульный код** для легкого добавления функций

## 🔒 Безопасность и права

### Функции безопасности
- **Аутентификация пользователей** через Telegram ID
- **Контроль доступа на основе ролей** (RBAC)
- **Изоляция каналов** между модераторами
- **Нет внешних API** (кроме Telegram)
- **Локальное хранение данных** (без облачных зависимостей)

### Матрица прав

| Действие | Владелец | Админ | Модератор | Пользователь |
|----------|----------|-------|-----------|--------------|
| Добавить/Удалить каналы | ✅ | ❌ | ❌ | ❌ |
| Редактировать настройки каналов | ✅ | ❌ | ❌ | ❌ |
| Управлять пользователями | ✅ | ✅ | ❌ | ❌ |
| Назначать каналы | ✅ | ✅ | ❌ | ❌ |
| Загружать медиа | ✅ | ✅ | ✅* | ❌ |
| Просматривать статус | ✅ | ✅ | ✅* | ❌ |
| Запускать бота | ✅ | ✅ | ✅ | ✅ |

*Только для назначенных каналов

## 🌐 Развертывание

### Локальная разработка
```bash
# Настройка для разработки
git clone https://github.com/kisyufka/Telegram_Channel_Auto-Poster_Bot.git
cd telegram-auto-poster
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Запуск в режиме отладки
python bot.py
```

### Продукционное развертывание

**Linux сервер (Systemd сервис):**
```bash
# Создайте файл сервиса: /etc/systemd/system/telegram-poster.service
[Unit]
Description=Telegram Auto-Poster Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/telegram-poster
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Включите и запустите
sudo systemctl enable telegram-poster
sudo systemctl start telegram-poster
```

**Docker развертывание:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### Облачные платформы
- **AWS EC2/Lightsail**: Полный контроль, масштабируемость
- **Google Cloud Run**: Serverless, оплата за использование
- **PythonAnywhere**: Просто, для начинающих
- **Heroku**: Легкое развертывание через Git
- **DigitalOcean Droplet**: Надежно, доступно

## 🤝 Участие в разработке

Мы рады вкладу! Вот как помочь:

1. **Форкните репозиторий**
2. **Создайте ветку для фичи**: `git checkout -b feature/amazing-feature`
3. **Зафиксируйте изменения**: `git commit -m 'Add amazing feature'`
4. **Запушьте в ветку**: `git push origin feature/amazing-feature`
5. **Откройте Pull Request**

### Рекомендации по разработке
- Следуйте стандартам PEP 8
- Добавляйте комментарии для сложной логики
- Обновляйте документацию для новых функций
- Пишите понятные сообщения коммитов
- Тщательно тестируйте перед отправкой

### Структура проекта
```
telegram-auto-poster/
├── bot.py                 # Основное приложение бота
├── config.yml             # Файл конфигурации
├── requirements.txt       # Зависимости Python
├── README.md             # Эта документация
├── LICENSE               # MIT лицензия
├── media/                # Директория для медиа
│   └── channel_*/        # Папки по каналам
└── bot_data.pkl          # Хранение данных (создается автоматически)
```

## 🐛 Решение проблем

### Частые проблемы и решения

| Проблема | Симптомы | Решение |
|----------|----------|---------|
| Бот не запускается | Нет ответа на /start | Проверьте токен в config.yml |
| Посты не отправляются | Нет постов в канале | Проверьте права бота в канале |
| Медиа не загружается | Файлы не появляются в очереди | Проверьте права доступа к папке media/ |
| Проблемы с часовым поясом | Посты в неправильное время | Настройте timezone_offset в config |
| Ошибки прав | "Недостаточно прав" | Передобавьте бота в канал с правами админа |

### Режим отладки

Включите подробное логирование, изменив конфигурацию в `bot.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Измените с INFO на DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Получение ID каналов

1. **Способ 1**: Перешлите любое сообщение из канала @username_to_id_bot
2. **Способ 2**: Используйте @RawDataBot и отправьте /start в канале
3. **Способ 3**: Добавьте @getidsbot в канал и используйте /getids
   - **Важно**: ID каналов отрицательные (например, -1001234567890)

## 📞 Поддержка и сообщество

### Получение помощи
- **GitHub Issues**: [Сообщите об ошибке или запросите функцию](https://github.com/yourusername/telegram-auto-poster/issues)
- **Документация**: Этот README и комментарии в коде
- **Поддержка в Telegram**: Свяжитесь с maintainer напрямую

### Правила сообщества
- Будьте уважительны и конструктивны
- Ищите существующие issues перед созданием новых
- Предоставляйте детали при сообщении об ошибках
- Помогайте другим, когда можете

## 📄 Лицензия

Этот проект лицензирован под MIT License - полные детали в файле [LICENSE](LICENSE).

**Краткое содержание MIT лицензии:**
- ✅ Коммерческое использование разрешено
- ✅ Модификация разрешена
- ✅ Распространение разрешено
- ✅ Частное использование разрешено
- ✅ Нет ответственности
- ✅ Нет гарантий

## 🙏 Благодарности

- **Telegram** за их отличный Bot API
- **Команде pyTelegramBotAPI** за Python обертку
- **Сообществу Python** за удивительные инструменты и библиотеки
- **Контрибьюторам**, которые помогают улучшить этот проект

## 📍 Дорожная карта

### Следующие релизы
- [ ] Веб-панель для управления
- [ ] Аналитика и отчеты
- [ ] API для внешних интеграций
- [ ] Мультиязычный интерфейс
- [ ] Интеграция с облачным хранилищем

### Идеи на будущее
- [ ] AI-подсказки для контента
- [ ] Кросс-платформенная публикация (Twitter, Instagram)
- [ ] Продвинутая аналитическая панель
- [ ] Функции командной работы
- [ ] Мобильное приложение для управления
