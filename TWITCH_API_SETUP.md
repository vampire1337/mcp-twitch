# 🔑 ПОЛНАЯ ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ TWITCH API КЛЮЧЕЙ

## 📋 СОДЕРЖАНИЕ
1. [Быстрый старт](#-1-быстрый-старт)
2. [Пошаговая регистрация приложения](#-2-пошаговая-регистрация-приложения)
3. [Получение Access Token](#-3-получение-access-token)
4. [Настройка OAuth Redirect URL](#-4-настройка-oauth-redirect-url)
5. [Тестирование подключения](#-5-тестирование-подключения)

---

## ⚡ 1. БЫСТРЫЙ СТАРТ

### Для нетерпеливых:

1. **Перейдите на https://dev.twitch.tv/console/apps**
2. **Нажмите "Register Your Application"**
3. **Заполните:**
   - Название: `MCP Twitch Server`
   - OAuth Redirect: `http://localhost:3000` 
   - Категория: `Application Integration`
   - Тип клиента: **Конфиденциально**
4. **Скопируйте Client ID в `.env` файл**
5. **Для токена: https://twitchtokengenerator.com**

---

## 🔧 2. ПОШАГОВАЯ РЕГИСТРАЦИЯ ПРИЛОЖЕНИЯ

### Шаг 2.1: Переход в Developer Console

![Twitch Console](https://dev.twitch.tv/console/apps)

1. Перейдите на **https://dev.twitch.tv/console/apps**
2. Войдите в свою учетную запись Twitch (если не авторизованы)
3. Нажмите кнопку **"Register Your Application"** (Зарегистрировать приложение)

### Шаг 2.2: Заполнение формы регистрации

Заполните форму следующим образом:

| Поле | Значение | Пояснение |
|------|----------|-----------|
| **Name** | `MCP Twitch Server` | Любое описательное название |
| **OAuth Redirect URLs** | `http://localhost:3000` | URL для OAuth авторизации |
| **Category** | `Application Integration` | Категория приложения |
| **Client Type** | **Конфиденциально** | ⚠️ ВАЖНО: Выберите именно этот тип! |

### ⚠️ КРИТИЧЕСКИ ВАЖНО:
- **Тип клиента должен быть "Конфиденциально"** (не "Публичный")
- Это позволит получать Client Secret для серверных приложений

### Шаг 2.3: Создание приложения

1. Нажмите кнопку **"Create"** (Создать)
2. Вы будете перенаправлены на страницу с деталями приложения
3. **Сохраните Client ID** - он понадобится для настройки

---

## 🎫 3. ПОЛУЧЕНИЕ ACCESS TOKEN

### Опция 1: Через Twitch Token Generator (Рекомендуется)

1. **Перейдите на https://twitchtokengenerator.com**
2. **Найдите "Custom Scope Token"**
3. **Выберите нужные права (scopes):**

   | Scope | Описание | Нужен для |
   |-------|----------|-----------|
   | `user:read:email` | Чтение email пользователя | Информация профиля |
   | `channel:read:subscriptions` | Подписки канала | Статистика канала |
   | `moderation:read` | Данные модерации | Модераторские функции |
   | `channel:manage:broadcast` | Управление трансляцией | Изменение настроек |
   | `clips:edit` | Создание клипов | Создание клипов |
   | `user:read:follows` | Подписки пользователя | Кого пользователь читает |

4. **Нажмите "Generate Token"**
5. **Авторизуйтесь на Twitch**
6. **Скопируйте полученный токен**

### Опция 2: Через собственное OAuth приложение

```bash
# 1. Получите код авторизации (откройте в браузере):
https://id.twitch.tv/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000&response_type=code&scope=user:read:email+channel:read:subscriptions

# 2. После авторизации получите код из URL:
# http://localhost:3000/?code=AUTHORIZATION_CODE

# 3. Обменяйте код на токен:
curl -X POST 'https://id.twitch.tv/oauth2/token' \
-H 'Content-Type: application/x-www-form-urlencoded' \
-d 'client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&code=AUTHORIZATION_CODE&grant_type=authorization_code&redirect_uri=http://localhost:3000'
```

---

## 🔗 4. НАСТРОЙКА OAUTH REDIRECT URL

### Что такое OAuth Redirect URL?

OAuth Redirect URL - это адрес, куда Twitch перенаправит пользователя после авторизации. Для нашего MCP сервера это технический параметр.

### Рекомендуемые настройки:

| Окружение | Redirect URL | Пояснение |
|-----------|--------------|-----------|
| **Разработка** | `http://localhost:3000` | Локальная разработка |
| **Продакшн** | `https://yourdomain.com/auth/callback` | Ваш сайт |
| **Тестирование** | `http://localhost:8080/callback` | Тестовый сервер |

### Добавление дополнительных URL:

1. В Developer Console откройте ваше приложение
2. Нажмите **"Edit"** (Редактировать) 
3. В поле **"OAuth Redirect URLs"** нажмите **"Add"**
4. Добавьте дополнительные URL при необходимости

---

## 🧪 5. ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ

### Шаг 5.1: Настройка .env файла

Создайте файл `.env` в корне проекта:

```env
# Обязательный параметр
TWITCH_CLIENT_ID=your_client_id_here

# Опциональный параметр для расширенного доступа
TWITCH_ACCESS_TOKEN=your_access_token_here
```

### Шаг 5.2: Запуск тестов

```bash
# Полное тестирование с реальными API вызовами
python test_real_api.py

# Демонстрация возможностей
python demo_server.py

# Быстрый тест без реальных API
python test_server.py
```

### Шаг 5.3: Проверка токена

```bash
# Запуск сервера для проверки токена
python mcp_twitch_server.py --client-id YOUR_CLIENT_ID --access-token YOUR_TOKEN

# Или через переменные окружения
export TWITCH_CLIENT_ID=your_client_id
export TWITCH_ACCESS_TOKEN=your_token
python mcp_twitch_server.py
```

---

## 🚨 РЕШЕНИЕ ЧАСТЫХ ПРОБЛЕМ

### Проблема: "401 Unauthorized"

**Причины:**
- Неверный Client ID
- Отсутствует Access Token для защищенного эндпоинта
- Токен истек

**Решения:**
1. Проверьте Client ID в Developer Console
2. Перегенерируйте Access Token
3. Убедитесь что токен имеет нужные scopes

### Проблема: "OAuth token is missing"

**Причина:** Эндпоинт требует авторизации пользователя

**Решение:** Получите Access Token через twitchtokengenerator.com

### Проблема: "Invalid redirect URI"

**Причина:** URL в OAuth запросе не совпадает с зарегистрированным

**Решение:** Добавьте нужный URL в настройки приложения

### Проблема: "Client ID mismatch"

**Причина:** Использование чужого токена с вашим Client ID

**Решение:** Генерируйте токен для вашего приложения

---

## 📊 ПРАВА ДОСТУПА (SCOPES) - СПРАВОЧНИК

| Scope | Доступ | Примеры использования |
|-------|--------|--------------------|
| **Публичные данные** (без токена) |
| - | Топ игры, поиск каналов | `get_top_games`, `search_channels` |
| **user:read:email** |
| ✅ | Email пользователя | Профиль пользователя |
| **channel:read:subscriptions** |
| ✅ | Подписки канала | Количество подписчиков |
| **moderation:read** |
| ✅ | Списки банов, модераторы | `get_banned_users`, `get_moderators` |
| **moderation:write** |
| ✅ | Бан/разбан пользователей | `ban_user`, `unban_user` |
| **channel:manage:broadcast** |
| ✅ | Изменение настроек канала | `modify_channel_info` |
| **clips:edit** |
| ✅ | Создание клипов | `create_clip` |
| **user:read:follows** |
| ✅ | Кого читает пользователь | `get_followed_channels` |

---

## ⚡ БЫСТРЫЙ CHECKLIST

- [ ] ✅ Зарегистрировано приложение на dev.twitch.tv
- [ ] ✅ Тип клиента: **Конфиденциально**
- [ ] ✅ Client ID скопирован в `.env`
- [ ] ✅ Access Token получен (если нужен)
- [ ] ✅ Токен имеет нужные scopes
- [ ] ✅ `python test_real_api.py` проходит без ошибок
- [ ] ✅ Сервер запускается: `python mcp_twitch_server.py`

---

## 🆘 ПОЛУЧЕНИЕ ПОМОЩИ

Если что-то не работает:

1. **Проверьте статус Twitch API**: https://twitchstatus.com/
2. **Документация Twitch**: https://dev.twitch.tv/docs/api/
3. **Тестирование API**: https://twitchtoken.adamrayner.io/
4. **Наши тесты**: `python test_real_api.py`

### Полезные ссылки:

- 🔗 **Developer Console**: https://dev.twitch.tv/console/apps
- 🎫 **Token Generator**: https://twitchtokengenerator.com
- 📚 **API Documentation**: https://dev.twitch.tv/docs/api/reference
- 🧪 **Token Tester**: https://id.twitch.tv/oauth2/validate

---

**🎉 После настройки у вас будет полнофункциональный MCP сервер для Twitch API!**
