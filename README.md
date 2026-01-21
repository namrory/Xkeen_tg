# 🤖 XKeen Telegram Bot v2.0 ADVANCED

Полнофункциональный Telegram-бот для управления **XKeen** (Xray прокси-клиент) на роутерах **Keenetic** с поддержкой **VLESS конфигураций**.

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

---

## 🆕 Что нового в v2.0 ADVANCED

✅ **Полное управление VLESS конфигами:**
- Загрузка новых конфигов через Telegram (прямо ссылки вида `vless://...`)
- Автоматический парсинг параметров (UUID, host, port, fingerprint, SNI, publicKey, shortId)
- Переключение между сохранёнными конфигами с автоматическим перезапуском XKeen
- Проверка доступности конфигов (пинг до хоста, замер latency)
- Тестирование всех конфигов одновременно
- Сохранение резервных копий конфигов в `/opt/vless-configs/`

✅ **Управление XKeen:**
- Проверка статуса
- Перезапуск
- Просмотр портов и версий

✅ **Безопасность:**
- Доступ ограничен одним Telegram user ID
- Чувствительные данные защищены
- Логирование команд

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Политика XKeen

**XKeen работает через политики доступа!**

XKeen применяется **НЕ ко всему роутеру**, а только к устройствам в политике **"XKeen"**.

### Быстрая настройка политики:

1. Откройте веб-интерфейс: **http://192.168.1.1**
2. Перейдите: **Приоритеты подключений** → **Политики доступа в интернет**
3. Создайте политику **"XKeen"** и выберите провайдера
4. В разделе **Применение политик** добавьте нужные устройства/сети в "XKeen"

---

## ⚡ Быстрый старт (15 минут)

### 0️⃣ Убедитесь, что создали политику XKeen!

Без этого бот не сможет управлять трафиком.

### 1️⃣ Создать Telegram-бота

```bash
Telegram → @BotFather → /newbot
↓ Копируете TOKEN
```

### 2️⃣ Получить свой User ID

```bash
Telegram → @userinfobot → любое сообщение
↓ Копируете User ID
```

### 3️⃣ Подключиться к роутеру по SSH

```bash
ssh -p 222 root@192.168.1.1
# Пароль: keenetic
```

### 4️⃣ Установить зависимости

```bash
opkg update
opkg remove python3 python3-pip --force-removal-of-dependent-packages
opkg install python3 python3-pip
pip3 install python-telegram-bot==13.15 paramiko
```

### 5️⃣ Скачать и отредактировать бота

```bash
# На роутере
nano /opt/xkeen_tg_bot.py
# Вставьте код из xkeen_tg_bot.py
# Замените:
# - BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" на твой токен
# - ALLOWED_CHAT_ID = YOUR_TELEGRAM_USER_ID на твой user ID
# Сохраните: Ctrl+O, Enter, Ctrl+X
```

### 6️⃣ Запустить бота

```bash
chmod +x /opt/xkeen_tg_bot.py
nohup python3 /opt/xkeen_tg_bot.py > /opt/xkeen_bot.log 2>&1 &
```

### 7️⃣ Тестировать в Telegram

```
Напиши боту: /start
```

---

## 🎯 Основные команды v2.0

### Управление VLESS конфигами

```
/add_vless vless://...     - Добавить новый VLESS конфиг из ссылки
/list_vless                - Список всех сохранённых конфигов
/show_current              - Показать текущий VLESS конфиг
/switch_vless [name]       - Переключиться на другой конфиг
/test_vless                - Проверить доступность текущего
/test_all                  - Проверить все конфиги
```

### Управление XKeen

```
/status                    - Статус XKeen
/restart                   - Перезапуск XKeen
/ports                     - Просмотр портов
/version                   - Версии XKeen и Xray
/policy                    - Справка по политике
/vless_menu                - Меню VLESS
/help                      - Все команды
```

---

## 📱 Примеры использования

### Пример 1: Загрузить новый VLESS конфиг

**Способ 1: Через команду**

```bash
/add_vless vless://12345678-1234-5678-1234-567812345678@example.com:443?fp=chrome&sni=example.com&pbk=KEY&sid=12345678
```

**Способ 2: Просто отправить VLESS ссылку**

```
vless://12345678-1234-5678-1234-567812345678@example.com:443?fp=chrome&sni=example.com&pbk=KEY&sid=12345678
```

**Результат:**

```
✅ VLESS конфиг загружен и активирован!

🌐 Host: example.com
🔌 Port: 443
🔒 Fingerprint: chrome
📝 SNI: example.com

💾 Сохранено в: /opt/vless-configs/vless_20250121_103000.json
```

### Пример 2: Проверить доступность всех конфигов

**Команда:**

```
/test_all
```

**Результат:**

```
📡 Результаты тестирования:

✅ OK | vless_20250121_103000
   example.com:443 (45ms)
✅ OK | vless_20250121_110500
   another.example.com:443 (52ms)
❌ DOWN | vless_20250121_114000
   dead-server.example.com:443 (Timeout)
```

---

## ✨ Особенности v2.0

✅ **Работает с серым IP** – не требует webhook  
✅ **VLESS конфигурации** – загрузка, парсинг, переключение, тесты  
✅ **Выборочное проксирование** – через политики Keenetic  
✅ **Проверка доступности** – пинг и измерение latency  
✅ **Простая установка** – всё на роутере в `/opt/`  
✅ **Полное управление XKeen** – все команды доступны  
✅ **Защита доступа** – только авторизованный пользователь  
✅ **Резервные копии** – сохранение всех конфигов в `/opt/vless-configs/`  

---

## 📊 Требования

| Компонент | Требование |
|-----------|-----------|
| **Роутер** | Keenetic  |
| **Entware** | Установлен |
| **XKeen** | Версия 1.1.3.8+ |
| **Политика** | Создана политика "XKeen" ⚠️ |
| **Python** | 3.8+ |
| **Библиотеки** | python-telegram-bot 13.15+, paramiko |
| **Интернет** | На роутере и на устройстве |

---

## 🔒 Безопасность

- ✅ Доступ к боту ограничен вашим User ID
- ✅ XKeen работает только для выбранных устройств (политика)
- ✅ VLESS конфиги сохраняются локально в `/opt/vless-configs/`
- ✅ Токен бота НЕ должен быть в репозитории
- ✅ Все команды логируются

---

## 🐛 Решение проблем

### Проблема: "ModuleNotFoundError: No module named 'logging'"

```bash
opkg remove python3 python3-pip --force-removal-of-dependent-packages
opkg install python3 python3-pip
python3 -c "import logging"  # Проверка
pip3 install python-telegram-bot==13.15
```

### Проблема: Бот не запускается

```bash
tail -50 /opt/xkeen_bot.log
python3 /opt/xkeen_tg_bot.py  # Запустить в переднем плане
```

### Проблема: "Ошибка парсинга VLESS"

Проверьте формат VLESS ссылки:

```
vless://UUID@host:port?fp=chrome&sni=host&pbk=KEY&sid=SHORT_ID
```

---

## 🔗 Полезные ссылки

- 🔗 [XKeen GitHub](https://github.com/Corvus-Malus/XKeen)
- 🔗 [Keenetic Форум](https://forum.keenetic.ru/topic/16899-xkeen/)
- 🔗 [VLESS Protocol](https://xtls.github.io/)
- 🔗 [python-telegram-bot](https://docs.python-telegram-bot.org/)

---

**✨ v2.0 ADVANCED – Полное управление VLESS конфигурациями на Keenetic! ✨**

**Версия:** 2.0 ADVANCED  
**Дата:** 2025-01-22  
**Совместимость:** Keenetic Netis N6 + XKeen 1.1.3.8+  
