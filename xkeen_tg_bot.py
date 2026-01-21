#!/opt/bin/python3
# -*- coding: utf-8 -*-

"""
XKeen Telegram Bot v2.0 ADVANCED - GITHUB VERSION
Управление XKeen (Xray) на Keenetic с поддержкой VLESS конфигов

GitHub: https://github.com/YOUR_USERNAME/Xkeen_tg
"""

import subprocess
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup

# === НАСТРОЙКИ ===
# ⚠️  ПЕРЕД ИСПОЛЬЗОВАНИЕМ ЗАМЕНИ НА СВОИ ЗНАЧЕНИЯ!
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # Получи у @BotFather
ALLOWED_CHAT_ID = YOUR_TELEGRAM_USER_ID     # Твой Telegram user ID (число)

# Пути на роутере
XRAY_CONFIG_DIR = "/opt/etc/xray/configs"
OUTBOUNDS_FILE = f"{XRAY_CONFIG_DIR}/04_outbounds.json"
VLESS_BACKUP_DIR = "/opt/vless-configs"


# === ИНИЦИАЛИЗАЦИЯ ПАПОК ===
def init_dirs():
    """Создание необходимых директорий."""
    for d in [VLESS_BACKUP_DIR]:
        if not os.path.exists(d):
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                print(f"⚠️  Не могу создать {d}: {e}")


# === VLESS ПАРСИНГ ===
def parse_vless_url(vless_url: str) -> dict:
    """
    Парсинг VLESS ссылки вида:
    vless://UUID@host:port?fp=chrome&sni=host&pbk=KEY&sid=SHORT_ID
    
    Возвращает словарь с параметрами или None если ошибка.
    """
    try:
        vless_url = vless_url.strip()
        
        if not vless_url.startswith("vless://"):
            return None
        
        url_part = vless_url[8:]
        
        if "@" not in url_part:
            return None
        
        uuid_part, server_part = url_part.split("@", 1)
        
        if "?" in server_part:
            server_str, query_str = server_part.split("?", 1)
        else:
            server_str = server_part
            query_str = ""
        
        if ":" not in server_str:
            return None
        
        host, port_str = server_str.rsplit(":", 1)
        
        try:
            port = int(port_str)
        except:
            return None
        
        params = {}
        if query_str:
            for param in query_str.split("&"):
                if "=" in param:
                    k, v = param.split("=", 1)
                    params[k] = v
        
        return {
            "uuid": uuid_part,
            "host": host,
            "port": port,
            "flow": params.get("flow", "xtls-rprx-vision"),
            "fingerprint": params.get("fp", "chrome"),
            "server_name": params.get("sni", host),
            "public_key": params.get("pbk", ""),
            "short_id": params.get("sid", ""),
            "spider_x": params.get("spider", "/"),
        }
    except Exception as e:
        return None


def vless_to_outbounds(vless_data: dict, tag: str = "vless-reality") -> dict:
    """
    Преобразуем распарсенные VLESS параметры в структуру Xray outbound.
    """
    outbound = {
        "tag": tag,
        "protocol": "vless",
        "settings": {
            "vnext": [
                {
                    "address": vless_data["host"],
                    "port": vless_data["port"],
                    "users": [
                        {
                            "id": vless_data["uuid"],
                            "flow": vless_data["flow"],
                            "encryption": "none",
                            "level": 0
                        }
                    ]
                }
            ]
        },
        "streamSettings": {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "publicKey": vless_data["public_key"],
                "fingerprint": vless_data["fingerprint"],
                "serverName": vless_data["server_name"],
                "shortId": vless_data["short_id"],
                "spiderX": vless_data["spider_x"]
            }
        }
    }
    return outbound


def save_vless_backup(vless_data: dict, name: str = None) -> str:
    """Сохраняем VLESS конфиг в файл в /opt/vless-configs/"""
    if name is None:
        name = f"vless_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = os.path.join(VLESS_BACKUP_DIR, f"{name}.json")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(vless_data, f, indent=2, ensure_ascii=False)
        return filepath
    except Exception as e:
        return None


def list_vless_backups() -> list:
    """Возвращает список всех сохранённых VLESS конфигов."""
    try:
        if not os.path.exists(VLESS_BACKUP_DIR):
            return []
        files = [f[:-5] for f in os.listdir(VLESS_BACKUP_DIR) if f.endswith(".json")]
        return sorted(files)
    except:
        return []


def load_vless_backup(name: str) -> dict:
    """Загружаем VLESS конфиг из файла."""
    filepath = os.path.join(VLESS_BACKUP_DIR, f"{name}.json")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def switch_outbounds(vless_data: dict) -> bool:
    """Заменяем первый outbound в 04_outbounds.json на новый VLESS конфиг."""
    try:
        with open(OUTBOUNDS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        new_outbound = vless_to_outbounds(vless_data)
        
        if config.get("outbounds") and len(config["outbounds"]) > 0:
            config["outbounds"][0] = new_outbound
        else:
            config["outbounds"] = [new_outbound]
        
        with open(OUTBOUNDS_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        return True
    except Exception as e:
        return False


def get_current_vless() -> dict:
    """Получаем текущий VLESS конфиг из 04_outbounds.json."""
    try:
        with open(OUTBOUNDS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        if config.get("outbounds") and len(config["outbounds"]) > 0:
            outbound = config["outbounds"][0]
            
            if outbound.get("protocol") == "vless" and outbound.get("settings"):
                vnext = outbound["settings"].get("vnext", [{}])[0]
                users = vnext.get("users", [{}])[0]
                stream = outbound.get("streamSettings", {}).get("realitySettings", {})
                
                return {
                    "host": vnext.get("address", "N/A"),
                    "port": vnext.get("port", "N/A"),
                    "uuid": users.get("id", "N/A"),
                    "fingerprint": stream.get("fingerprint", "N/A"),
                    "server_name": stream.get("serverName", "N/A"),
                    "public_key": stream.get("publicKey", "N/A"),
                    "short_id": stream.get("shortId", "N/A"),
                }
        return None
    except:
        return None


def test_vless_connectivity(host: str, port: int, timeout: int = 5) -> dict:
    """Проверка доступности VLESS хоста (пинг + проверка порта)."""
    result = {"ok": False, "latency": None, "error": None}
    
    try:
        res = subprocess.run(
            f"ping -c 1 -W {timeout} {host}",
            shell=True,
            capture_output=True,
            timeout=timeout + 2
        )
        
        if res.returncode == 0:
            output = res.stdout.decode("utf-8", errors="ignore")
            match = re.search(r"time=([0-9.]+)\s*ms", output)
            if match:
                result["latency"] = int(float(match.group(1)))
            result["ok"] = True
        else:
            result["error"] = "Host unreachable"
    except Exception as e:
        result["error"] = str(e)
    
    return result


# === ОСНОВНЫЕ ФУНКЦИИ ===
def check_auth(update):
    """Проверка авторизации."""
    if update.effective_user is None:
        return False
    return update.effective_user.id == ALLOWED_CHAT_ID


def run_cmd(cmd: str) -> str:
    """Запуск команды на роутере."""
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=30,
        )
        out = (res.stdout or "") + (("\n" + res.stderr) if res.stderr else "")
        return out.strip() if out.strip() else "нет вывода"
    except Exception as e:
        return f"❌ Ошибка: {e}"


# === КЛАВИАТУРЫ ===
def main_keyboard():
    keyboard = [
        ["📊 Статус", "🔄 Перезапуск"],
        ["🎯 Порты", "📦 Версии"],
        ["📌 Политика", "🧩 VLESS"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def vless_keyboard():
    keyboard = [
        ["🆕 Добавить VLESS", "📜 Список VLESS"],
        ["🔀 Переключить", "ℹ️ Текущий"],
        ["📡 Тест один", "📡 Тест все"],
        ["↩️ Назад"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# === КОМАНДЫ ОСНОВНЫЕ ===
def start(update, context):
    if not check_auth(update):
        return
    update.message.reply_text(
        "👋 XKeen Telegram Bot v2.0 ADVANCED\n\n"
        "📋 Команды:\n"
        "/status – статус XKeen\n"
        "/restart – перезапуск XKeen\n"
        "/ports – порты прокси\n"
        "/version – версии\n"
        "/policy – про политику\n"
        "/vless_menu – работа с VLESS\n"
        "/help – все команды\n",
        reply_markup=main_keyboard(),
    )


def status_cmd(update, context):
    if not check_auth(update):
        return
    text = run_cmd("xkeen -status 2>&1")
    update.message.reply_text(f"📊 Статус XKeen:\n\n{text[:3500]}")


def restart_cmd(update, context):
    if not check_auth(update):
        return
    update.message.reply_text("🔄 Перезапускаю XKeen...")
    text = run_cmd("xkeen -restart 2>&1")
    update.message.reply_text(f"✅ Результат:\n\n{text[:3500]}")


def ports_cmd(update, context):
    if not check_auth(update):
        return
    ports = run_cmd("xkeen -cp 2>&1")
    excl = run_cmd("xkeen -cpe 2>&1")
    msg = "🎯 Порты XKeen:\n\n"
    msg += f"🔹 Прокси (xkeen -cp):\n{ports[:1500]}\n\n"
    msg += f"🔸 Исключённые (xkeen -cpe):\n{excl[:1500]}"
    update.message.reply_text(msg)


def version_cmd(update, context):
    if not check_auth(update):
        return
    xk = run_cmd("xkeen -v 2>&1")
    xr = run_cmd("xray -version 2>&1")
    msg = "📦 Версии:\n\n"
    msg += f"XKeen:\n{xk[:1500]}\n\n"
    msg += f"Xray:\n{xr[:1500]}"
    update.message.reply_text(msg)


def policy_cmd(update, context):
    if not check_auth(update):
        return
    msg = (
        "📌 Политика XKeen:\n\n"
        "XKeen работает ТОЛЬКО для устройств в политике \"XKeen\".\n\n"
        "⚙️  Настройка:\n"
        "1. Веб-интерфейс: http://192.168.1.1\n"
        "2. Приоритеты подключений → Политики доступа в интернет\n"
        "3. Создать политику \"XKeen\" → выбрать провайдера\n"
        "4. Применение политик → добавить устройства в \"XKeen\"\n"
    )
    update.message.reply_text(msg)


def help_cmd(update, context):
    if not check_auth(update):
        return
    msg = (
        "📚 Все команды XKeen Bot v2.0:\n\n"
        "🔹 Основные:\n"
        "/status – статус\n"
        "/restart – перезапуск\n"
        "/ports – порты\n"
        "/version – версии\n"
        "/policy – политика\n\n"
        "🔹 VLESS:\n"
        "/vless_menu – меню\n"
        "/add_vless – добавить ссылку\n"
        "/list_vless – список конфигов\n"
        "/show_current – текущий конфиг\n"
        "/switch_vless – переключить\n"
        "/test_vless – тест одного\n"
        "/test_all – тест всех\n"
    )
    update.message.reply_text(msg)


# === VLESS КОМАНДЫ ===
def vless_menu(update, context):
    if not check_auth(update):
        return
    update.message.reply_text(
        "🧩 Меню управления VLESS конфигами:\n\n"
        "🆕 Добавить VLESS – отправить ссылку вида vless://...\n"
        "📜 Список VLESS – все сохранённые конфиги\n"
        "🔀 Переключить – выбрать активный конфиг\n"
        "ℹ️  Текущий – показать активный\n"
        "📡 Тест один – проверить доступность\n"
        "📡 Тест все – проверить все конфиги\n",
        reply_markup=vless_keyboard(),
    )


def add_vless_cmd(update, context):
    if not check_auth(update):
        return
    update.message.reply_text(
        "🆕 Отправь VLESS ссылку или используй /add_vless vless://...\n\n"
        "Формат:\n"
        "vless://UUID@host:port?fp=chrome&sni=host&pbk=KEY&sid=SHORT_ID\n\n"
        "Пример:\n"
        "vless://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@example.com:443"
        "?fp=chrome&sni=example.com&pbk=XXXXXXXX...&sid=xxxxxxxx"
    )


def list_vless_cmd(update, context):
    if not check_auth(update):
        return
    
    backups = list_vless_backups()
    
    if not backups:
        update.message.reply_text("📜 Нет сохранённых VLESS конфигов.")
        return
    
    msg = "📜 Сохранённые VLESS конфиги:\n\n"
    for i, name in enumerate(backups, 1):
        msg += f"{i}. {name}\n"
    
    msg += "\n💡 Используй /switch_vless [имя] чтобы переключиться"
    update.message.reply_text(msg)


def show_current_cmd(update, context):
    if not check_auth(update):
        return
    
    vless = get_current_vless()
    
    if not vless:
        update.message.reply_text("ℹ️  Не удалось прочитать текущий конфиг.")
        return
    
    msg = "ℹ️  Текущий VLESS конфиг:\n\n"
    msg += f"🌐 Host: {vless['host']}\n"
    msg += f"🔌 Port: {vless['port']}\n"
    msg += f"🆔 UUID: {vless['uuid'][:20]}...\n"
    msg += f"🔒 Fingerprint: {vless['fingerprint']}\n"
    msg += f"📝 SNI: {vless['server_name']}\n"
    msg += f"🔑 PublicKey: {vless['public_key'][:20]}...\n"
    msg += f"📌 ShortId: {vless['short_id']}\n"
    
    update.message.reply_text(msg)


def switch_vless_cmd(update, context):
    if not check_auth(update):
        return
    
    if not context.args:
        update.message.reply_text(
            "🔀 Используй: /switch_vless [имя]\n\n"
            "Доступные конфиги:\n"
        )
        backups = list_vless_backups()
        for name in backups:
            update.message.reply_text(f"  • {name}")
        return
    
    config_name = " ".join(context.args)
    vless_data = load_vless_backup(config_name)
    
    if not vless_data:
        update.message.reply_text(f"❌ Конфиг '{config_name}' не найден.")
        return
    
    if switch_outbounds(vless_data):
        run_cmd("xkeen -restart 2>&1")
        update.message.reply_text(
            f"✅ Переключился на '{config_name}'\n"
            "XKeen перезапущен."
        )
    else:
        update.message.reply_text(
            f"❌ Ошибка при переключении на '{config_name}'"
        )


def test_vless_cmd(update, context):
    if not check_auth(update):
        return
    
    vless = get_current_vless()
    
    if not vless:
        update.message.reply_text("❌ Не удалось прочитать текущий конфиг.")
        return
    
    update.message.reply_text(
        f"📡 Проверяю доступность: {vless['host']}:{vless['port']}..."
    )
    
    result = test_vless_connectivity(vless['host'], vless['port'])
    
    if result['ok']:
        msg = f"✅ OK | {vless['host']}:{vless['port']}\n"
        msg += f"⏱️  Latency: {result['latency']}ms"
    else:
        msg = f"❌ DOWN | {vless['host']}:{vless['port']}\n"
        msg += f"Error: {result['error']}"
    
    update.message.reply_text(msg)


def test_all_cmd(update, context):
    if not check_auth(update):
        return
    
    backups = list_vless_backups()
    
    if not backups:
        update.message.reply_text("📜 Нет сохранённых конфигов для тестирования.")
        return
    
    update.message.reply_text(
        f"📡 Тестирую {len(backups)} конфигов, подожди..."
    )
    
    results = []
    for name in backups:
        vless = load_vless_backup(name)
        if vless:
            test_result = test_vless_connectivity(vless['host'], vless['port'])
            status = "✅ OK" if test_result['ok'] else "❌ DOWN"
            latency_str = f"{test_result['latency']}ms" if test_result['latency'] else "N/A"
            results.append(f"{status} | {name}\n   {vless['host']}:{vless['port']} ({latency_str})")
    
    msg = "📡 Результаты тестирования:\n\n"
    msg += "\n".join(results)
    
    update.message.reply_text(msg)


def back_cmd(update, context):
    if not check_auth(update):
        return
    update.message.reply_text(
        "↩️ Возврат в основное меню.",
        reply_markup=main_keyboard(),
    )


# === ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ===
def handle_message(update, context):
    if not check_auth(update):
        return
    
    text = (update.message.text or "").strip()
    
    # Кнопки главного меню
    if text == "📊 Статус":
        return status_cmd(update, context)
    if text == "🔄 Перезапуск":
        return restart_cmd(update, context)
    if text == "🎯 Порты":
        return ports_cmd(update, context)
    if text == "📦 Версии":
        return version_cmd(update, context)
    if text == "📌 Политика":
        return policy_cmd(update, context)
    if text == "🧩 VLESS":
        return vless_menu(update, context)
    
    # Кнопки VLESS
    if text == "↩️ Назад":
        return back_cmd(update, context)
    if text == "🆕 Добавить VLESS":
        return add_vless_cmd(update, context)
    if text == "📜 Список VLESS":
        return list_vless_cmd(update, context)
    if text == "🔀 Переключить":
        return switch_vless_cmd(update, context)
    if text == "ℹ️ Текущий":
        return show_current_cmd(update, context)
    if text == "📡 Тест один":
        return test_vless_cmd(update, context)
    if text == "📡 Тест все":
        return test_all_cmd(update, context)
    
    # VLESS ссылка
    if text.startswith("vless://"):
        update.message.reply_text("⏳ Парсню VLESS ссылку...")
        
        vless_data = parse_vless_url(text)
        
        if not vless_data:
            update.message.reply_text("❌ Ошибка парсинга VLESS ссылки.")
            return
        
        backup_path = save_vless_backup(vless_data)
        
        if not backup_path:
            update.message.reply_text("❌ Ошибка сохранения конфига.")
            return
        
        if switch_outbounds(vless_data):
            run_cmd("xkeen -restart 2>&1")
            
            msg = "✅ VLESS конфиг загружен и активирован!\n\n"
            msg += f"🌐 Host: {vless_data['host']}\n"
            msg += f"🔌 Port: {vless_data['port']}\n"
            msg += f"🔒 Fingerprint: {vless_data['fingerprint']}\n"
            msg += f"📝 SNI: {vless_data['server_name']}\n"
            msg += f"\n💾 Сохранено в: {backup_path}"
            
            update.message.reply_text(msg)
        else:
            update.message.reply_text("⚠️  Конфиг сохранён, но ошибка при активации.")
        
        return
    
    update.message.reply_text(
        "Неизвестная команда.\n"
        "Используй /start или кнопки снизу."
    )


def main():
    init_dirs()
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Основные команды
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status_cmd))
    dp.add_handler(CommandHandler("restart", restart_cmd))
    dp.add_handler(CommandHandler("ports", ports_cmd))
    dp.add_handler(CommandHandler("version", version_cmd))
    dp.add_handler(CommandHandler("policy", policy_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))
    
    # VLESS команды
    dp.add_handler(CommandHandler("vless_menu", vless_menu))
    dp.add_handler(CommandHandler("add_vless", add_vless_cmd))
    dp.add_handler(CommandHandler("list_vless", list_vless_cmd))
    dp.add_handler(CommandHandler("show_current", show_current_cmd))
    dp.add_handler(CommandHandler("switch_vless", switch_vless_cmd))
    dp.add_handler(CommandHandler("test_vless", test_vless_cmd))
    dp.add_handler(CommandHandler("test_all", test_all_cmd))
    dp.add_handler(CommandHandler("back", back_cmd))
    
    # Текстовые сообщения
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    print("🚀 Бот запущен...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
