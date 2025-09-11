# 🎮 ПОЛНАЯ ИНСТРУКЦИЯ ПО НАСТРОЙКЕ MCP TWITCH SERVER

## 📋 СОДЕРЖАНИЕ
1. [Получение Twitch API ключей](#-1-получение-twitch-api-ключей)
2. [Установка и настройка](#-2-установка-и-настройка)
3. [Тестирование сервера](#-3-тестирование-сервера)
4. [Интеграция с клиентами](#-4-интеграция-с-клиентами)
5. [Использование инструментов](#-5-использование-инструментов)

---

## 🔑 1. ПОЛУЧЕНИЕ TWITCH API КЛЮЧЕЙ

### Шаг 1: Регистрация приложения в Twitch Developer Console

1. **Перейдите на https://dev.twitch.tv/console/apps**
2. **Нажмите "Register Your Application"**
3. **Заполните форму:**
   
   ```
   Название: MCP Twitch Server (или любое другое)
   OAuth Redirect URLs: http://localhost:3000
   Категория: Application Integration
   Тип клиента: Конфиденциально (для серверных приложений)
   ```

4. **Нажмите "Create"**

### Шаг 2: Получение Client ID и Client Secret

После создания приложения вы получите:
- **Client ID** - публичный идентификатор (можно показывать в коде)
- **Client Secret** - секретный ключ (НЕ показывать в коде!)

### Шаг 3: Генерация Access Token (опционально)

Для некоторых эндпоинтов нужен Access Token:

1. **Перейдите на https://twitchtokengenerator.com/**
2. **Выберите нужные scopes:**
   - `user:read:email` - чтение email пользователя
   - `channel:read:subscriptions` - чтение подписок канала
   - `moderation:read` - чтение данных модерации
   - `channel:manage:broadcast` - управление трансляцией

3. **Получите токен и сохраните его**

---

## ⚙️ 2. УСТАНОВКА И НАСТРОЙКА

### Шаг 1: Клонирование и установка зависимостей

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd mcp-twitch

# Установите Python 3.10+ если не установлен
# https://www.python.org/downloads/

# Установите зависимости
pip install -r requirements.txt

# Или с uv (рекомендуется)
pip install uv
uv sync
```

### Шаг 2: Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp example.env .env

# Отредактируйте .env файл
notepad .env  # Windows
nano .env     # Linux/Mac
```

Заполните `.env` файл:

```env
# Обязательно - Client ID из Twitch Developer Console
TWITCH_CLIENT_ID=your_client_id_here

# Опционально - Access Token для защищенных эндпоинтов
TWITCH_ACCESS_TOKEN=your_access_token_here
```

### Шаг 3: Проверка установки

```bash
# Запустите тесты
python test_server.py

# Запустите демо
python demo_server.py

# Проверьте CLI
python mcp_twitch_server.py --help
```

---

## 🧪 3. ТЕСТИРОВАНИЕ СЕРВЕРА

### Базовое тестирование

```bash
# Автоматические тесты
python test_server.py

# Демонстрация всех возможностей
python demo_server.py

# Список доступных тегов
python mcp_twitch_server.py --list-tags
```

### Тестирование с реальными данными

```bash
# Запуск с тестовыми кредами (без реальных API вызовов)
python mcp_twitch_server.py --client-id test_client

# Запуск с реальными кредами
python mcp_twitch_server.py --client-id YOUR_CLIENT_ID --access-token YOUR_TOKEN
```

### Тестирование фильтрации

```bash
# Только инструменты для каналов
python mcp_twitch_server.py --include-tags channels

# Без модерации
python mcp_twitch_server.py --exclude-tags moderation

# HTTP сервер для веб-интеграции
python mcp_twitch_server.py --transport http --port 8080
```

---

## 🔗 4. ИНТЕГРАЦИЯ С КЛИЕНТАМИ

### Claude Desktop

Добавьте в `%APPDATA%/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "twitch": {
      "command": "python",
      "args": [
        "C:/path/to/mcp-twitch/mcp_twitch_server.py",
        "--client-id", "YOUR_CLIENT_ID",
        "--include-tags", "channels", "users", "streams"
      ],
      "env": {
        "TWITCH_CLIENT_ID": "your_client_id",
        "TWITCH_ACCESS_TOKEN": "your_token"
      }
    }
  }
}
```

### Cursor

Добавьте в настройки MCP:

```json
{
  "mcpServers": {
    "twitch-api": {
      "command": "uv",
      "args": [
        "run", "--with", "fastmcp",
        "python", "C:/path/to/mcp-twitch/mcp_twitch_server.py",
        "--transport", "stdio"
      ],
      "env": {
        "TWITCH_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

### HTTP интеграция

```bash
# Запустите HTTP сервер
python mcp_twitch_server.py --transport http --host 0.0.0.0 --port 8080

# Сервер будет доступен на http://localhost:8080
# Эндпоинты:
# GET  /mcp - получение схемы
# POST /mcp - вызов инструментов
```

---

## 🛠️ 5. ИСПОЛЬЗОВАНИЕ ИНСТРУМЕНТОВ

### Категории инструментов

| Тег | Описание | Примеры инструментов |
|-----|----------|---------------------|
| `channels` | Управление каналами | `get_twitch_channel`, `modify_channel_info` |
| `users` | Пользователи | `find_twitch_users`, `twitch_quick_stats` |
| `streams` | Стримы | `get_live_streams`, `get_streams` |
| `games` | Игры | `get_games`, `get_top_games` |
| `search` | Поиск | `search_channels`, `search_categories` |
| `clips` | Клипы | `get_clips`, `create_clip` |
| `moderation` | Модерация | `moderate_ban_user`, `get_banned_users` |
| `analytics` | Аналитика | `get_extension_analytics`, `get_game_analytics` |

### Примеры вызовов через Claude

```
Пользователь: "Найди информацию о стримере ninja"
Claude: Использует find_twitch_users("ninja") → получает ID → twitch_quick_stats(ninja_id)

Пользователь: "Какие игры сейчас популярны?"
Claude: Использует get_top_games() → показывает топ игр

Пользователь: "Найди стримеров играющих в Fortnite"
Claude: search_categories("Fortnite") → get_live_streams(game_id=fortnite_id)
```

### Трансформированные инструменты

Сервер автоматически улучшает некоторые инструменты:

| Оригинальный | Трансформированный | Улучшения |
|--------------|-------------------|-----------|
| `get_channel_info` | `get_twitch_channel` | Лучшее описание, переименованные параметры |
| `get_users` | `find_twitch_users` | Поддержка поиска нескольких пользователей |
| `get_streams` | `get_live_streams` | Акцент на "живые" стримы |
| `ban_user` | `moderate_ban_user` | Скрытые модераторские параметры |

---

## 🚨 ВАЖНЫЕ ЗАМЕЧАНИЯ

### Лимиты API
- **Без токена**: 30 запросов/минуту
- **С App Token**: 800 запросов/минуту  
- **С User Token**: 120 запросов/минуту на пользователя

### Безопасность
- **НЕ** добавляйте Client Secret в код или git
- **НЕ** делитесь Access Token публично
- Используйте переменные окружения для кредов

### Отладка
```bash
# Включите подробное логирование
export FASTMCP_LOG_LEVEL=DEBUG
python mcp_twitch_server.py

# Или с переменной в команде
FASTMCP_LOG_LEVEL=DEBUG python mcp_twitch_server.py
```

---

## 🆘 РЕШЕНИЕ ПРОБЛЕМ

### Ошибка "Client ID is required"
```bash
# Убедитесь что .env файл в той же папке
ls -la .env

# Или передайте явно
python mcp_twitch_server.py --client-id YOUR_CLIENT_ID
```

### Ошибка "401 Unauthorized"
- Проверьте правильность Client ID
- Для защищенных эндпоинтов нужен Access Token
- Убедитесь что токен не истек

### Ошибка "Tool not found"
```bash
# Проверьте доступные инструменты
python demo_server.py

# Убедитесь что нужный тег включен
python mcp_twitch_server.py --include-tags channels users streams
```

---

## 📞 ПОДДЕРЖКА

Если возникают проблемы:

1. **Проверьте логи**: `FASTMCP_LOG_LEVEL=DEBUG`
2. **Запустите тесты**: `python test_server.py`
3. **Проверьте креды**: https://dev.twitch.tv/console/apps
4. **Обновите зависимости**: `pip install -r requirements.txt --upgrade`

Сервер готов к использованию! 🚀
