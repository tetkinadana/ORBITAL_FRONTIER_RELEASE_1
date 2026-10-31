"""Telegram-интерфейс игры.

Это главный файл запуска бота; токен Telegram читается из BOT_TOKEN в файле .env.
Здесь находятся тексты экранов, кнопки и обработчики команд/нажатий.
Правила игры реализованы в game/engine.py, настройки — в game/config.py,
а сохранение прогресса — в game/database.py.
"""

import asyncio
import logging
import os
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import urlencode

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    User,
)

from game import database as db
from game import engine
from game.ui import format_screen, plain_screen, progress_bar, rarity_label
from game.config import (
    CASES,
    DONATION_PACKAGES,
    EQUIPMENT_RARITY_CHANCES,
    LOCATIONS,
    NICKNAME_COSMETICS,
    NICKNAME_COSMETIC_RARITY_CHANCES,
    REFERRAL_MAX_FRIENDS,
    RESOURCES,
    SHIP,
)

load_dotenv(Path(__file__).with_name(".env"))
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не найден токен в файле .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()
logger = logging.getLogger(__name__)
T = TypeVar("T")

MISSION_NAMES = {
    "pioneer_signal": "Изучить аварийный сигнал",
    "scan_moon": "Просканировать Луну",
    "moon_transmitter": "Исследовать лунный передатчик",
    "pioneer9_chapter": "Раскрыть тайну «Пионера-9»",
}

# Названия модулей корабля для экранов улучшения.
MODULE_NAMES = {
    "ship": "корабль",
    "engine": "двигатель",
    "scanner": "сканер",
    "cargo": "грузовой отсек",
    "protection": "защита",
    "energy": "энергомодуль",
}


# Сборка экранов и клавиатур Telegram.
async def run_sync(function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    return await asyncio.to_thread(function, *args, **kwargs)


def offload(function: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    async def wrapped(*args: Any, **kwargs: Any) -> T:
        return await run_sync(function, *args, **kwargs)

    return wrapped


@offload
def register_user(user: User) -> bool:
    return db.ensure_player(user.id, username=user.username)


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🚀 Корабль", callback_data="ship"),
            InlineKeyboardButton(text="🪐 Карта", callback_data="map"),
        ],
        [
            InlineKeyboardButton(text="🔎 Исследовать", callback_data="explore"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"),
        ],
        [
            InlineKeyboardButton(text="📜 Миссии", callback_data="missions"),
            InlineKeyboardButton(text="🧬 Коллекции", callback_data="collections"),
        ],
        [
            InlineKeyboardButton(text="📖 Сюжет", callback_data="story"),
            InlineKeyboardButton(text="🛰 Журнал", callback_data="journal"),
        ],
        [
            InlineKeyboardButton(text="🛡 Гильдия", callback_data="guild"),
            InlineKeyboardButton(text="📦 Кейсы", callback_data="cases"),
        ],
        [InlineKeyboardButton(text="🧪 Лаборатория", callback_data="laboratory")],
        [InlineKeyboardButton(text="💫 Донат · ОРБИТАЛЫ", callback_data="donate")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_button(target: str = "home", text: str = "↩️ Назад") -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=text, callback_data=target)]


def add_back(
    rows: list[list[InlineKeyboardButton]],
    target: str = "home",
) -> InlineKeyboardMarkup:
    rows.append(back_button(target))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def module_menu() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🚀 Корабль", callback_data="upgrade:ship"),
            InlineKeyboardButton(text="🔥 Двигатель", callback_data="upgrade:engine"),
        ],
        [
            InlineKeyboardButton(text="🔎 Сканер", callback_data="upgrade:scanner"),
            InlineKeyboardButton(text="📦 Трюм", callback_data="upgrade:cargo"),
        ],
        [
            InlineKeyboardButton(text="🛡 Защита", callback_data="upgrade:protection"),
            InlineKeyboardButton(text="⚡ Энергия", callback_data="upgrade:energy"),
        ],
    ]
    return add_back(rows, "ship")


def ship_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Модули и улучшения", callback_data="upgrades")],
            [
                InlineKeyboardButton(text="⛽ Заправить", callback_data="refuel"),
                InlineKeyboardButton(text="🛠 Ремонт", callback_data="repair"),
            ],
            [InlineKeyboardButton(text="⚡ Зарядить", callback_data="recharge")],
            back_button(),
        ]
    )


@offload
def map_menu(telegram_id: int) -> InlineKeyboardMarkup:
    current = db.get_player(telegram_id)["location"]
    rows: list[list[InlineKeyboardButton]] = []
    buttons: list[InlineKeyboardButton] = []
    for location_id, location in LOCATIONS.items():
        if location_id == "earth_orbit":
            label = "🛰 Орбита Земли"
        else:
            locked = bool(engine.route_requirements(telegram_id, location_id))
            label = ("🔒 " if locked else "✅ ") + location.name
        buttons.append(
            InlineKeyboardButton(
                text=("📍 " if location_id == current else "") + label,
                callback_data=f"dest:{location_id}",
            )
        )
        if len(buttons) == 2:
            rows.append(buttons)
            buttons = []
    if buttons:
        rows.append(buttons)
    if current != "earth_orbit":
        rows.append(
            [
                InlineKeyboardButton(
                    text="↩️ Вернуться на орбитальную базу (бесплатно)",
                    callback_data="travel:earth_orbit",
                )
            ]
        )
    return add_back(rows)


def location_keyboard(location_id: str, locked: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if not locked:
        rows.append(
            [InlineKeyboardButton(text="🚀 Перелететь", callback_data=f"travel:{location_id}")]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="🛠 Проверить улучшения", callback_data="upgrades")]
        )
    rows.append(back_button("map", "🪐 Назад к карте"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Подготовка карточек профиля и корабля для Telegram-панели.
@offload
def profile_text(player: db.Player) -> str:
    collections = engine.collection_progress(player["telegram_id"])
    completed = sum(1 for item in collections if item["completed"])
    achievements = engine.achievement_list(player["telegram_id"])
    if player["hero_level"] >= engine.LEVEL_CAP:
        level_progress = "▰" * 10 + " 100%\nМаксимальный уровень достигнут."
    else:
        next_xp = engine.xp_for_next_level(player["hero_level"])
        progress = min(player["hero_xp"], next_xp)
        level_progress = (
            f"{progress_bar(progress, next_xp)}\n"
            f"Опыт: {progress}/{next_xp} · до уровня: {next_xp - progress}"
        )
    return (
        "👤 ПРОФИЛЬ ИССЛЕДОВАТЕЛЯ\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Уровень: {player['hero_level']}\n"
        f"{level_progress}\n\n"
        f"🚀 Корабль T1 LVL ({player['ship_level']}) — «{SHIP['name']}»\n"
        f"◈ ОРБИТАЛЫ: {player['orbitals']}\n"
        f"🪪 Ник: {public_nickname(player)}\n"
        f"📍 Локация: {LOCATIONS[player['location']].name}\n"
        f"🧬 Коллекции: {completed}/{len(collections)}\n"
        f"🏅 Достижения: {len(achievements)}"
    )


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Скины ника", callback_data="nickname_skins")],
            [InlineKeyboardButton(text="👥 Пригласить друга", callback_data="invite")],
            [InlineKeyboardButton(text="💫 Донат · ОРБИТАЛЫ", callback_data="donate")],
            back_button(),
        ]
    )


def donation_text() -> str:
    packages = [
        f"• {int(package['orbitals'])} ОРБИТАЛОВ — {int(package['stars'])} ⭐"
        for package in DONATION_PACKAGES.values()
    ]
    return (
        "💫 ПОПОЛНЕНИЕ ОРБИТАЛОВ\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Выбери пакет. Оплата проходит через Telegram Stars.\n\n"
        + "\n".join(packages)
        + "\n\nПри покупке приглашённым другом тебе начислится 5% "
        "от суммы ОРБИТАЛОВ в его пакете."
    )


def donation_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{int(package['orbitals'])} ◈ · {int(package['stars'])} ⭐",
                callback_data=f"donate:pack:{package_id}",
            )
        ]
        for package_id, package in DONATION_PACKAGES.items()
    ]
    rows.append(back_button())
    return InlineKeyboardMarkup(inline_keyboard=rows)


@offload
def invite_text(telegram_id: int) -> str:
    stats = db.get_referral_stats(telegram_id)
    return (
        "👥 ПРИГЛАСИТЬ ДРУГА\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Приглашено: {stats['friends']}/{REFERRAL_MAX_FRIENDS}\n"
        f"Награды за приглашения: {stats['invite_rewards']} ◈\n"
        f"Бонусы с пополнений друзей: {stats['topup_bonus']} ◈\n\n"
        "За первого друга начисляется 20 ОРБИТАЛОВ, за каждого следующего — 5 "
        "(максимум 20 друзей). Дополнительно получай 5% ОРБИТАЛОВ "
        "с каждого пополнения приглашённого друга."
    )


async def user_profile_photo_id(telegram_id: int) -> str | None:
    photos = await bot.get_user_profile_photos(telegram_id, limit=1)
    if not photos.photos:
        return None
    return photos.photos[0][-1].file_id


def ship_text(player: db.Player) -> str:
    capacity = SHIP["cargo_capacity"] + player["cargo_level"] * 10
    return (
        "🚀 ИССЛЕДОВАТЕЛЬСКИЙ КОРАБЛЬ\n\n"
        f"Корабль T1 LVL ({player['ship_level']}) — «{SHIP['name']}»\n"
        f"Локация: {LOCATIONS[player['location']].name}\n"
        f"⛽ Топливо: {player['fuel']}/{SHIP['fuel_max']} · "
        f"{progress_bar(player['fuel'], SHIP['fuel_max'])}\n"
        f"🛡 Корпус: {player['hull']}/{SHIP['hull_max']} · "
        f"{progress_bar(player['hull'], SHIP['hull_max'])}\n"
        f"⚡ Энергия: {player['energy']}/{SHIP['energy_max']} · "
        f"{progress_bar(player['energy'], SHIP['energy_max'])}\n"
        f"🔥 Двигатель: {player['engine_level']}\n"
        f"🔎 Сканер: {player['scanner_level']}\n"
        f"📦 Грузовой отсек: уровень {player['cargo_level']} ({capacity} единиц)\n"
        f"🛡 Защита: уровень {player['protection_level']}\n"
        "Улучшения, ремонт и заправка доступны на орбитальной станции."
    )


@offload
def inventory_text(telegram_id: int) -> str:
    player = db.get_player(telegram_id)
    inventory = db.get_inventory(telegram_id)
    capacity = SHIP["cargo_capacity"] + player["cargo_level"] * 10
    used = sum(inventory.values())
    lines = ["🎒 ИНВЕНТАРЬ", f"Трюм: {used}/{capacity} · {progress_bar(used, capacity, 8)}", ""]
    for resource_id, resource in RESOURCES.items():
        amount = player["fuel"] if resource_id == "fuel" else inventory.get(resource_id, 0)
        if amount:
            lines.append(
                f"{resource.icon} {resource.name}: {amount} · {rarity_label(resource.rarity)}"
            )
    if not any(
        player["fuel"] if resource_id == "fuel" else inventory.get(resource_id, 0)
        for resource_id in RESOURCES
    ):
        lines.append("▫️ Инвентарь пока пуст.")
    return "\n".join(lines)


def level_up_text(level_ups: list[dict[str, Any]]) -> str:
    if not level_ups:
        return ""
    lines = ["", "🎉 Повышение уровня!"]
    for level_up in level_ups:
        level = level_up["level"]
        reward = level_up["reward"]
        reward_text = ", ".join(
            f"{quantity} {RESOURCES[item].name if item in RESOURCES else item}"
            for item, quantity in reward.items()
        ) or "доступ к новым возможностям"
        lines.append(f"Уровень {level}: награда — {reward_text}.")
    return "\n".join(lines)


async def answer_screen(
    message: Message,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
) -> Message:
    """Отправляет сообщения одним стилем и экранирует пользовательский текст."""
    return await message.answer(
        format_screen(text),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def answer_error(message: Message, text: str) -> Message:
    return await answer_screen(message, f"🔴 {text}")


async def set_panel(message: Message, user_id: int, text: str, keyboard: InlineKeyboardMarkup) -> None:
    if message.photo:
        await message.delete()
        panel = await answer_screen(message, text, keyboard)
        await run_sync(db.save_panel, user_id, panel.chat.id, panel.message_id)
        return
    if message.text != plain_screen(text) or message.reply_markup != keyboard:
        await message.edit_text(
            format_screen(text),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    await run_sync(db.save_panel, user_id, message.chat.id, message.message_id)


async def edit_panel(callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await set_panel(callback.message, callback.from_user.id, text, keyboard)


async def alert_error(callback: CallbackQuery, text: str) -> None:
    await callback.answer(f"🔴 {text}", show_alert=True)


async def show_profile_panel(callback: CallbackQuery) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    user_id = callback.from_user.id
    text = await profile_text(await run_sync(db.get_player, user_id))
    keyboard = profile_keyboard()
    photo_id = await user_profile_photo_id(user_id)
    if photo_id is None:
        await set_panel(callback.message, user_id, text, keyboard)
        return
    if callback.message.photo:
        if callback.message.caption != plain_screen(text) or callback.message.reply_markup != keyboard:
            await callback.message.edit_caption(
                caption=format_screen(text),
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        await run_sync(
            db.save_panel,
            user_id,
            callback.message.chat.id,
            callback.message.message_id,
        )
        return
    await callback.message.delete()
    panel = await callback.message.answer_photo(
        photo_id,
        caption=format_screen(text),
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await run_sync(db.save_panel, user_id, panel.chat.id, panel.message_id)


@offload
def missions_text(telegram_id: int) -> str:
    missions = db.get_missions(telegram_id)
    if not missions:
        return "📜 Пока нет заданий. Проверь журнал сигналов на орбите Земли."
    lines = ["📜 ЖУРНАЛ ЗАДАНИЙ", ""]
    for mission in missions:
        mission_id = str(mission["mission_id"])
        status = str(mission["status"])
        icon = {"active": "🔄", "completed": "✅", "available": "🔓"}.get(status, "•")
        title = MISSION_NAMES.get(mission_id, mission_id.replace("_", " ").capitalize())
        lines.append(f"{icon} {title}")
    return "\n".join(lines)


@offload
def collections_text(telegram_id: int) -> tuple[str, InlineKeyboardMarkup]:
    progress = engine.collection_progress(telegram_id)
    discoveries = {
        row["discovery_id"]
        for row in db.get_discoveries(telegram_id)
    }
    open_locations = {
        location_id
        for location_id in LOCATIONS
        if f"location:{location_id}" in discoveries or location_id == "earth_orbit"
    }
    lines = ["🏺 КОЛЛЕКЦИИ АРТЕФАКТОВ", ""]
    buttons: list[list[InlineKeyboardButton]] = []
    for item in progress:
        if item["location_id"] not in open_locations:
            continue
        status = "✅ завершена" if item["completed"] else "в процессе"
        lines.append(
            f"{item['name']}: {item['found']}/{item['total']} · "
            f"{progress_bar(item['found'], item['total'], 8)} · {status}"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🔎 {item['name']}",
                    callback_data=f"collection:{item['location_id']}",
                )
            ]
        )
    if not buttons:
        lines.append("Пока не найдено ни одной коллекции.")
    return "\n".join(lines), add_back(buttons)


@offload
def guild_text(telegram_id: int) -> tuple[str, InlineKeyboardMarkup]:
    guild = db.get_guild(telegram_id)
    if guild is None:
        return (
            "🛡 ГИЛЬДИЯ\n\n"
            "Создай гильдию командой:\n/guild_create Название\n\n"
            "Или посмотри открытые гильдии и вступи в одну.",
            InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔎 Найти гильдию", callback_data="guild:list")],
                    back_button(),
                ]
            ),
        )
    guild_id = int(guild["guild_id"])
    members = db.get_guild_members(guild_id)
    missions = engine.get_guild_missions(guild_id)
    mission_lines = [
        f"{'✅' if mission['status'] == 'completed' else '🔄'} {mission['title']}: "
        f"{mission['progress']}/{mission['target_amount']} {RESOURCES[str(mission['resource_id'])].name}"
        for mission in missions
    ] or ["Пока нет гильдейских заданий."]
    member_lines = [
        f"• {public_member_nickname(member)} — {member['role']}"
        for member in members[:15]
    ]
    next_xp = engine.xp_for_guild_level(int(guild["level"]))
    text = (
        f"🛡 ГИЛЬДИЯ «{guild['name']}»\n\n"
        f"Уровень: {guild['level']} · опыт {guild['xp']}/{next_xp} · "
        f"{progress_bar(int(guild['xp']), next_xp)}\n"
        f"Участники: {len(members)}/{engine.guild_member_limit(int(guild['level']))}\n"
        f"Твой вклад: {guild['contribution_total']}\n"
        f"Описание: {guild['description'] or 'не задано'}\n\n"
        "👥 Состав:\n" + ("\n".join(member_lines) or "—")
        + "\n\n📋 Задания:\n" + "\n".join(mission_lines)
        + "\n\nВклад: /guild_contribute scrap 2\nУправление: /guild_promote ID, /guild_kick ID"
    )
    return text, InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Обновить гильдию", callback_data="guild")],
            back_button(),
        ]
    )


def case_catalog_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    buttons: list[InlineKeyboardButton] = []
    for case_id, case in CASES.items():
        buttons.append(
            InlineKeyboardButton(
                text=f"📦 {case.name} · {case.cost}◈",
                callback_data=f"case:view:{case_id}",
            )
        )
        if len(buttons) == 2:
            rows.append(buttons)
            buttons = []
    if buttons:
        rows.append(buttons)
    return add_back(rows)


def create_case_keyboard(case_id: str) -> InlineKeyboardMarkup:
    case = CASES[case_id]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⚡ ОТКРЫТЬ · {case.cost} ◈",
                    callback_data=f"case:open:{case_id}",
                )
            ],
            back_button("cases", "↩️ К КЕЙСАМ"),
        ]
    )


def cases_text(balance: int) -> str:
    lines = [
        "🎁 ЧЁРНЫЙ РЫНОК · КОНТЕЙНЕРЫ\n"
        "━━━━━━━━━━━━━━━━━━━━",
        "Выбери контейнер, чтобы изучить содержимое.",
        "Вероятности наград указаны до открытия.",
        "",
    ]
    lines.extend(f"◈ {case.name} · {case.cost} ОРБИТАЛОВ" for case in CASES.values())
    lines.extend(
        [
            "",
            f"БАЛАНС: {balance} ◈",
            "Пополнить баланс можно в разделе «Донат · ОРБИТАЛЫ».",
        ]
    )
    return "\n".join(lines)


def case_detail_text(case_id: str, balance: int) -> str:
    case = CASES[case_id]
    lines = [
        f"🎁 {case.name.upper()}\n━━━━━━━━━━━━━━━━━━━━",
        case.description,
        "",
        f"СТОИМОСТЬ: {case.cost} ◈",
    ]
    if case_id == "neon_singularity":
        lines.append("РЕДКОСТЬ СКИНОВ НИКА:")
        for rarity, weight in NICKNAME_COSMETIC_RARITY_CHANCES:
            names = ", ".join(item[1] for item in NICKNAME_COSMETICS[rarity])
            lines.append(f"{rarity_label(rarity)} · {weight / 100:.1f}% · {names}")
    else:
        lines.append("ВОЗМОЖНЫЙ ДРОП:")
        lines.extend(
            f"{RESOURCES[resource_id].icon} {name} ×{quantity} · "
            f"{rarity_label(RESOURCES[resource_id].rarity)} · {weight / 100:.0f}%"
            for resource_id, name, quantity, weight in case.rewards
        )
    lines.extend(["", f"ТВОЙ БАЛАНС: {balance} ◈"])
    return "\n".join(lines)


def equipment_rarity_text() -> str:
    lines = ["🧰 РЕДКОСТЬ СНАРЯЖЕНИЯ"]
    lines.extend(
        f"{rarity_label(rarity)} · {weight / 100:.1f}%"
        for rarity, weight in EQUIPMENT_RARITY_CHANCES
    )
    return "\n".join(lines)


def public_nickname(player: db.Player) -> str:
    nickname = player["nickname"] or f"Исследователь-{player['telegram_id'] % 10000:04d}"
    return f"{player['nickname_prefix']}{nickname}{player['nickname_suffix']}"


@offload
def nickname_cosmetics_text(telegram_id: int) -> tuple[str, InlineKeyboardMarkup]:
    cosmetics = db.get_nickname_cosmetics(telegram_id)
    lines = [
        "🎭 ОФОРМЛЕНИЕ НИКА\n━━━━━━━━━━━━━━━━━━━━",
        f"Текущий ник: {public_nickname(db.get_player(telegram_id))}",
        "",
    ]
    rows: list[list[InlineKeyboardButton]] = []
    if not cosmetics:
        lines.append("Скинов пока нет. Открой кейс «Неон-сингулярность».")
    else:
        for cosmetic in cosmetics:
            is_equipped = bool(cosmetic["equipped"])
            lines.append(
                f"{'✅' if is_equipped else '▫️'} {cosmetic['name']} · "
                f"{rarity_label(str(cosmetic['rarity']))}"
            )
            if not is_equipped:
                rows.append(
                    [
                        InlineKeyboardButton(
                            text=f"Надеть · {cosmetic['name']}",
                            callback_data=f"nickname_skin:{cosmetic['cosmetic_id']}",
                        )
                    ]
                )
    rows.append(
        [InlineKeyboardButton(text="Снять оформление", callback_data="nickname_skin:none")]
    )
    rows.append(back_button("profile"))
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


def public_member_nickname(member: dict[str, int | str | None]) -> str:
    member_id = member["telegram_id"]
    if not isinstance(member_id, int):
        raise ValueError("ID участника гильдии отсутствует")
    telegram_id = member_id
    nickname = member.get("nickname") or f"Исследователь-{telegram_id % 10000:04d}"
    return (
        f"{member.get('nickname_prefix') or ''}{nickname}"
        f"{member.get('nickname_suffix') or ''}"
    )


@offload
def laboratory_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    status = engine.quantum_matrix_lab_status(telegram_id)
    rows: list[list[InlineKeyboardButton]] = []
    if not status["researched"] and status["materials_ready"] and status["at_station"]:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔬 ИССЛЕДОВАТЬ ЧЕРТЁЖ",
                    callback_data="laboratory:research:quantum_matrix",
                )
            ]
        )
    elif status["researched"] and status["materials_ready"] and status["at_station"]:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚛️ СКРАФТИТЬ КВАНТОВУЮ МАТРИЦУ",
                    callback_data="laboratory:craft:quantum_matrix",
                )
            ]
        )
    rows.append(back_button())
    return InlineKeyboardMarkup(inline_keyboard=rows)


@offload
def laboratory_text(telegram_id: int) -> str:
    status = engine.quantum_matrix_lab_status(telegram_id)
    if status["researched"]:
        research_status = "✅ Чертёж исследован."
    elif status["materials_ready"]:
        research_status = "🔬 Все компоненты собраны. Можно исследовать чертёж."
    else:
        research_status = "🔒 Собери все компоненты, чтобы исследовать чертёж."
    materials = "\n".join(
        f"{'✅' if item['owned'] >= item['required'] else '▫️'} "
        f"{item['name']}: {item['owned']}/{item['required']}"
        for item in status["materials"]
    )
    station_note = (
        ""
        if status["at_station"]
        else "\n\nВернись на орбитальную станцию Земли для исследования и сборки."
    )
    return (
        "🧪 ЛАБОРАТОРИЯ · ИССЛЕДОВАНИЯ И СБОРКА\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 Чертёж: квантовая матрица\n"
        "Сначала собери компоненты и исследуй чертёж. После этого появится кнопка сборки.\n\n"
        f"{materials}\n\n"
        f"{research_status}{station_note}\n\n"
        "Исследование не расходует материалы. Сборка расходует указанные компоненты "
        "и не открывает планеты или сюжет."
    )


@dp.message(CommandStart())
async def start(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    is_new_player = await register_user(message.from_user)
    if is_new_player and command.args and command.args.startswith("ref_"):
        referrer_value = command.args.removeprefix("ref_")
        if referrer_value.isdecimal():
            await run_sync(engine.register_referral, message.from_user.id, int(referrer_value))
    panel = await answer_screen(
        message,
        "🚀 ORBITAL FRONTIER // UPLINK\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "СИСТЕМА: ОНЛАЙН · БАЗА: ОРБИТА ЗЕМЛИ\n"
        "Аварийный сигнал станции «Пионер-9» ожидает анализа.\n\n"
        "Выбери модуль управления:",
        main_menu(),
    )
    await run_sync(db.save_panel, message.from_user.id, panel.chat.id, panel.message_id)


@dp.message(Command("menu"))
async def menu_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    panel = await answer_screen(
        message,
        "🚀 ORBITAL FRONTIER // CONTROL\n━━━━━━━━━━━━━━━━━━━━\nВыбери модуль управления:",
        main_menu(),
    )
    await run_sync(db.save_panel, message.from_user.id, panel.chat.id, panel.message_id)


@dp.message(Command("help"))
async def help_command(message: Message) -> None:
    await answer_screen(
        message,
        "Команды игры:\n"
        "/menu — главное меню\n/status — профиль и корабль\n"
        "/inventory — ресурсы\n/map — маршруты\n/missions — задания\n"
        "/collections — артефакты\n/guild — гильдия\n"
        "/nickname ИМЯ — задать публичный игровой ник\n"
        "/guild_create НАЗВАНИЕ — создать гильдию\n"
        "/guild_join ID — вступить\n"
        "/guild_contribute РЕСУРС КОЛИЧЕСТВО — внести ресурс\n"
        "/guild_leave — покинуть гильдию\n\n"
        "Начни с изучения сигнала на орбите Земли, затем установи двигатель и лети на Луну."
    )


@dp.message(Command("nickname"))
async def nickname_command(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    if not command.args:
        await answer_screen(
            message,
            "Укажи игровой ник: /nickname НовоеИмя\n"
            "Ник длиной 3–20 символов. Настоящее имя и Telegram username другим игрокам не показываются."
        )
        return
    try:
        nickname = await run_sync(engine.set_nickname, message.from_user.id, command.args)
    except engine.GameError as error:
        await answer_error(message, str(error))
        return
    await answer_screen(
        message,
        f"✅ Игровой ник установлен: {nickname}\n"
        "В гильдиях будет отображаться только игровой ник или анонимный идентификатор."
    )


@dp.message(Command("status"))
async def status_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    player = await run_sync(db.get_player, message.from_user.id)
    photo_id = await user_profile_photo_id(message.from_user.id)
    if photo_id is None:
        panel = await answer_screen(message, await profile_text(player), profile_keyboard())
    else:
        panel = await message.answer_photo(
            photo_id,
            caption=format_screen(await profile_text(player)),
            reply_markup=profile_keyboard(),
            parse_mode="HTML",
        )
    await run_sync(db.save_panel, message.from_user.id, panel.chat.id, panel.message_id)
    await answer_screen(message, ship_text(player))


@dp.message(Command("inventory"))
async def inventory_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    await answer_screen(message, await inventory_text(message.from_user.id))


@dp.message(Command("map"))
async def map_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    await answer_screen(
        message,
        "🪐 КАРТА\nВыбирай маршрут. Закрытые маршруты показывают точные требования.",
        await map_menu(message.from_user.id),
    )


@dp.message(Command("missions"))
async def missions_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    await answer_screen(message, await missions_text(message.from_user.id))


@dp.message(Command("collections"))
async def collections_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    text, keyboard = await collections_text(message.from_user.id)
    await answer_screen(message, text, keyboard)


@dp.message(Command("guild"))
async def guild_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    text, keyboard = await guild_text(message.from_user.id)
    await answer_screen(message, text, keyboard)


@dp.message(Command("guild_create"))
async def guild_create_command(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    name = command.args or ""
    try:
        guild_id = await run_sync(engine.create_guild, message.from_user.id, name)
    except engine.GameError as error:
        await answer_error(message, str(error))
        return
    await answer_screen(message, f"Гильдия создана. Её ID: {guild_id}. Используй /guild для управления.")


@dp.message(Command("guild_join"))
async def guild_join_command(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    try:
        guild_id = int((command.args or "").strip())
        await run_sync(engine.join_guild, message.from_user.id, guild_id)
    except (ValueError, engine.GameError) as error:
        await answer_error(message, str(error) or "Использование: /guild_join ID")
        return
    await answer_screen(message, "Ты вступил в гильдию. Используй /guild, чтобы посмотреть состав и задания.")


@dp.message(Command("guild_contribute"))
async def guild_contribute_command(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    parts = (command.args or "").split()
    if len(parts) != 2:
        await answer_screen(message, "Использование: /guild_contribute scrap 2")
        return
    try:
        result = await run_sync(
            engine.contribute_to_guild,
            message.from_user.id,
            parts[0],
            int(parts[1]),
        )
    except (ValueError, engine.GameError) as error:
        await answer_error(message, str(error))
        return
    await answer_screen(
        message,
        f"Вклад принят. Гильдия получила {result['xp_gained']} опыта "
        f"(уровень {result['level']})."
    )


@dp.message(Command("guild_leave"))
async def guild_leave_command(message: Message) -> None:
    if message.from_user is None:
        return
    try:
        await run_sync(engine.leave_guild, message.from_user.id)
    except engine.GameError as error:
        await answer_error(message, str(error))
        return
    await answer_screen(message, "Ты покинул гильдию. Личный прогресс сохранён.")


@dp.message(Command("guild_promote"))
async def guild_promote_command(message: Message, command: CommandObject) -> None:
    await guild_management_command(message, command, "promote")


@dp.message(Command("guild_demote"))
async def guild_demote_command(message: Message, command: CommandObject) -> None:
    await guild_management_command(message, command, "demote")


@dp.message(Command("guild_kick"))
async def guild_kick_command(message: Message, command: CommandObject) -> None:
    await guild_management_command(message, command, "kick")


async def guild_management_command(
    message: Message,
    command: CommandObject,
    action: str,
) -> None:
    if message.from_user is None:
        return
    try:
        target_id = int((command.args or "").strip())
        await run_sync(engine.guild_manage, message.from_user.id, target_id, action)
    except (ValueError, engine.GameError) as error:
        await answer_error(message, str(error) or f"Использование: /guild_{action} TELEGRAM_ID")
        return
    await answer_screen(message, "Изменения состава сохранены.")


@dp.message(Command("guild_description"))
async def guild_description_command(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    try:
        await run_sync(engine.update_guild_description, message.from_user.id, command.args or "")
    except engine.GameError as error:
        await answer_error(message, str(error))
        return
    await answer_screen(message, "Описание гильдии обновлено.")


@dp.message(Command("shop"))
async def shop_command(message: Message) -> None:
    if message.from_user is None:
        return
    await register_user(message.from_user)
    player = await run_sync(db.get_player, message.from_user.id)
    await answer_screen(
        message,
        cases_text(player["orbitals"]) + "\n\n" + equipment_rarity_text(),
        case_catalog_keyboard(),
    )


@dp.callback_query(F.data == "home")
async def home_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await edit_panel(
        callback,
        "🚀 ORBITAL FRONTIER // CONTROL\n━━━━━━━━━━━━━━━━━━━━\nВыбери модуль управления:",
        main_menu(),
    )


@dp.callback_query(F.data == "ship")
async def ship_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    player = await run_sync(db.get_player, callback.from_user.id)
    await edit_panel(callback, ship_text(player), ship_menu())


@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await show_profile_panel(callback)


@dp.callback_query(F.data == "invite")
async def invite_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    bot_user = await bot.get_me()
    if not bot_user.username:
        raise RuntimeError("У бота не задан username — невозможно создать ссылку приглашения.")
    invite_link = f"https://t.me/{bot_user.username}?start=ref_{callback.from_user.id}"
    share_link = "https://t.me/share/url?" + urlencode(
        {"url": invite_link, "text": "Присоединяйся к ORBITAL FRONTIER!"}
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 ОТПРАВИТЬ ПРИГЛАШЕНИЕ", url=share_link)],
            back_button("profile", "↩️ В профиль"),
        ]
    )
    await edit_panel(callback, await invite_text(callback.from_user.id), keyboard)


@dp.callback_query(F.data == "donate")
async def donate_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await edit_panel(callback, donation_text(), donation_keyboard())


@dp.callback_query(F.data.startswith("donate:pack:"))
async def donate_package_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    package_id = (callback.data or "").rsplit(":", maxsplit=1)[-1]
    package = DONATION_PACKAGES.get(package_id)
    if package is None:
        await alert_error(callback, "Пакет ОРБИТАЛОВ не найден.")
        return
    if not isinstance(callback.message, Message):
        await alert_error(callback, "Не удалось открыть оплату.")
        return
    orbitals = int(package["orbitals"])
    stars = int(package["stars"])
    await callback.answer()
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=f"{orbitals} ОРБИТАЛОВ",
        description=f"Пакет «{package['name']}»: {orbitals} ОРБИТАЛОВ.",
        payload=f"orbitals:{package_id}:{callback.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{orbitals} ОРБИТАЛОВ", amount=stars)],
    )


def parse_orbital_invoice_payload(payload: str) -> tuple[str, int] | None:
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "orbitals" or not parts[2].isdecimal():
        return None
    return parts[1], int(parts[2])


@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    parsed = parse_orbital_invoice_payload(query.invoice_payload)
    if parsed is None:
        await query.answer(ok=False, error_message="🔴 Не удалось проверить пакет ОРБИТАЛОВ.")
        return
    package_id, intended_user_id = parsed
    package = DONATION_PACKAGES.get(package_id)
    if (
        intended_user_id != query.from_user.id
        or package is None
        or query.currency != "XTR"
        or query.total_amount != int(package["stars"])
    ):
        await query.answer(ok=False, error_message="🔴 Данные оплаты не совпадают с пакетом.")
        return
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if message.from_user is None or payment is None:
        return
    parsed = parse_orbital_invoice_payload(payment.invoice_payload)
    if parsed is None:
        logger.error("Successful Telegram payment has invalid payload: %s", payment.invoice_payload)
        await answer_screen(message, "Оплата получена, но пакет не удалось определить. Обратись в поддержку.")
        return
    package_id, intended_user_id = parsed
    if intended_user_id != message.from_user.id or payment.currency != "XTR":
        logger.error("Successful Telegram payment has inconsistent payer or currency.")
        await answer_screen(message, "Оплата получена, но данные платежа не совпали. Обратись в поддержку.")
        return
    await register_user(message.from_user)
    try:
        result = await run_sync(
            engine.record_orbital_purchase,
            message.from_user.id,
            package_id,
            payment.total_amount,
            payment.telegram_payment_charge_id,
        )
    except engine.GameError:
        logger.exception("Could not register successful Stars payment.")
        await answer_screen(message, "Оплата получена, но ОРБИТАЛЫ не начислены автоматически. Обратись в поддержку.")
        return
    player = await run_sync(db.get_player, message.from_user.id)
    if result["duplicate"]:
        await answer_screen(
            message,
            "Этот платёж уже был обработан.\n"
            f"Текущий баланс: {player['orbitals']} ◈"
        )
        return
    bonus_text = (
        f"\nБонус пригласившему: {result['referral_bonus']} ОРБИТАЛОВ."
        if result["referral_bonus"]
        else ""
    )
    await answer_screen(
        message,
        f"✅ Начислено: {result['orbitals']} ОРБИТАЛОВ.\n"
        f"Баланс: {player['orbitals']} ◈{bonus_text}"
    )


@dp.callback_query(F.data == "nickname_skins")
async def nickname_skins_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    text, keyboard = await nickname_cosmetics_text(callback.from_user.id)
    await edit_panel(callback, text, keyboard)


@dp.callback_query(F.data.startswith("nickname_skin:"))
async def equip_nickname_skin_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Оформление ника не найдено.")
        return
    cosmetic_id = callback.data.split(":", maxsplit=1)[1]
    try:
        await run_sync(
            engine.equip_nickname_cosmetic,
            callback.from_user.id,
            None if cosmetic_id == "none" else cosmetic_id,
        )
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    text, keyboard = await nickname_cosmetics_text(callback.from_user.id)
    await edit_panel(callback, "✅ Оформление ника обновлено.\n\n" + text, keyboard)


@dp.callback_query(F.data == "map")
async def map_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await edit_panel(
        callback,
        "🪐 КАРТА\n\n"
        "🔒 — маршрут пока закрыт; нажми на него, чтобы узнать требования.\n"
        "Маршруты открываются постепенно по мере улучшения корабля и сюжета.",
        await map_menu(callback.from_user.id),
    )


@dp.callback_query(F.data.startswith("dest:"))
async def destination_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Маршрут не найден.")
        return
    location_id = callback.data.split(":", maxsplit=1)[1]
    location = LOCATIONS.get(location_id)
    if location is None:
        await alert_error(callback, "Маршрут не найден.")
        return
    requirements = await run_sync(engine.route_requirements, callback.from_user.id, location_id)
    current = (await run_sync(db.get_player, callback.from_user.id))["location"] == location_id
    message = f"🪐 {location.name}\n\n{location.description}\n\n"
    if current:
        message += "📍 Ты уже находишься здесь."
    elif requirements:
        message += "🔒 Требования:\n• " + "\n• ".join(requirements)
    else:
        message += f"⛽ Расход топлива: {location.fuel_cost}.\nМаршрут открыт."
    await edit_panel(
        callback,
        message,
        location_keyboard(location_id, bool(requirements) and not current),
    )


@dp.callback_query(F.data.startswith("travel:"))
async def travel_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Маршрут не найден.")
        return
    location_id = callback.data.split(":", maxsplit=1)[1]
    try:
        result, level_ups = await run_sync(engine.travel, callback.from_user.id, location_id)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    await edit_panel(
        callback,
        f"🚀 Перелёт завершён.\n\n📍 {result['name']}\n"
        f"⛽ Потрачено топлива: {result['fuel_spent']}."
        + ("\n✨ Новая локация открыта!" if result["first_visit"] else "")
        + level_up_text(level_ups),
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔎 Исследовать", callback_data="explore")],
                [InlineKeyboardButton(text="🪐 Карта", callback_data="map")],
                back_button(),
            ]
        ),
    )


@dp.callback_query(F.data == "explore")
async def explore_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    try:
        outcome = await run_sync(engine.explore, callback.from_user.id)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    lines = [f"🔎 Исследование: {outcome['location']}", ""]
    if outcome["resources"]:
        lines.append("Найдено:")
        for resource_id, amount in outcome["resources"].items():
            lines.append(f"{RESOURCES[resource_id].icon} {RESOURCES[resource_id].name}: +{amount}")
    if outcome["artifact"]:
        lines.extend(
            [
                "",
                f"{rarity_label(str(outcome['artifact']['rarity']))} · "
                f"{outcome['artifact']['name']}",
                outcome["artifact"]["description"],
            ]
        )
    if outcome.get("collection_completed"):
        lines.append(
            f"\n🏆 Коллекция завершена! Награда: {outcome['collection_orbitals']} ОРБИТАЛОВ "
            f"и {outcome['collection_data']} ед. данных."
        )
    if outcome.get("story_unlock"):
        lines.append("\n📡 Новые сюжетные координаты записаны в журнал.")
    if not outcome["resources"] and not outcome["artifact"]:
        lines.append("Новых находок не обнаружено. Энергия потрачена.")
    energy = (await run_sync(db.get_player, callback.from_user.id))["energy"]
    lines.extend(
        [
            "",
            f"⚡ Энергия: {energy}/{SHIP['energy_max']} · "
            f"{progress_bar(energy, SHIP['energy_max'])}",
        ]
    )
    text = "\n".join(lines) + level_up_text(outcome["level_ups"])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Исследовать ещё раз", callback_data="explore")],
            [InlineKeyboardButton(text="📖 Сюжет", callback_data="story")],
            back_button(),
        ]
    )
    await edit_panel(callback, text, keyboard)


@dp.callback_query(F.data == "inventory")
async def inventory_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await edit_panel(callback, await inventory_text(callback.from_user.id), add_back([]))


@dp.callback_query(F.data == "upgrades")
async def upgrades_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    player = await run_sync(db.get_player, callback.from_user.id)
    costs = SHIP["upgrade_costs"]
    lines = ["🛠 УЛУЧШЕНИЯ КОРАБЛЯ", ""]
    for module, name in MODULE_NAMES.items():
        current = player["ship_level"] if module == "ship" else player[f"{module}_level"]
        requirements = costs[module]
        price = [f"{value} кредитов" for key, value in requirements.items() if key == "credits"]
        price.extend(
            f"{value} {RESOURCES[key].name}"
            for key, value in requirements.items()
            if key != "credits" and value
        )
        advanced = SHIP["advanced_upgrade_costs"].get(module, {}).get(current, {})
        price.extend(
            f"{quantity} {RESOURCES[resource_id].name}"
            for resource_id, quantity in advanced.items()
        )
        lines.append(f"{name.capitalize()} — уровень {current}. Цена следующего: {', '.join(price)}.")
    lines.append("\nУлучшения выполняются только на орбитальной станции Земли.")
    await edit_panel(callback, "\n".join(lines), module_menu())


@dp.callback_query(F.data.startswith("upgrade:"))
async def upgrade_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Улучшение не найдено.")
        return
    module = callback.data.split(":", maxsplit=1)[1]
    try:
        result = await run_sync(engine.upgrade_module, callback.from_user.id, module)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    player = await run_sync(db.get_player, callback.from_user.id)
    advanced_text = ""
    if result["advanced_costs"]:
        advanced_text = "\nДополнительные ресурсы: " + ", ".join(
            f"{quantity} {RESOURCES[resource_id].name}"
            for resource_id, quantity in result["advanced_costs"].items()
        ) + "."
    await edit_panel(
        callback,
        f"✅ Улучшен модуль «{MODULE_NAMES[module]}» до уровня {result['level']}.\n"
        f"Потрачено: {result['credits']} кредитов.{advanced_text}\n\n{ship_text(player)}",
        ship_menu(),
    )


async def perform_station_action(callback: CallbackQuery, action: str) -> None:
    await register_user(callback.from_user)
    try:
        if action == "repair":
            amount = await run_sync(engine.repair, callback.from_user.id)
            result = f"Корпус восстановлен на {amount}."
        elif action == "refuel":
            amount = await run_sync(engine.refuel, callback.from_user.id)
            result = f"Заправлено {amount} единиц топлива."
        else:
            amount = await run_sync(engine.recharge, callback.from_user.id)
            result = f"Восстановлено {amount} единиц энергии."
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    await edit_panel(
        callback,
        f"✅ {result}\n\n{ship_text(await run_sync(db.get_player, callback.from_user.id))}",
        ship_menu(),
    )


@dp.callback_query(F.data == "repair")
async def repair_callback(callback: CallbackQuery) -> None:
    await perform_station_action(callback, "repair")


@dp.callback_query(F.data == "refuel")
async def refuel_callback(callback: CallbackQuery) -> None:
    await perform_station_action(callback, "refuel")


@dp.callback_query(F.data == "recharge")
async def recharge_callback(callback: CallbackQuery) -> None:
    await perform_station_action(callback, "recharge")


@dp.callback_query(F.data == "missions")
async def missions_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await edit_panel(callback, await missions_text(callback.from_user.id), add_back([]))


@dp.callback_query(F.data == "collections")
async def collections_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    text, keyboard = await collections_text(callback.from_user.id)
    await edit_panel(callback, text, keyboard)


@dp.callback_query(F.data.startswith("collection:"))
async def collection_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Коллекция не найдена.")
        return
    location_id = callback.data.split(":", maxsplit=1)[1]
    if location_id not in LOCATIONS:
        await alert_error(callback, "Коллекция не найдена.")
        return
    discoveries = {
        row["discovery_id"]
        for row in await run_sync(db.get_discoveries, callback.from_user.id)
    }
    if location_id != "earth_orbit" and f"location:{location_id}" not in discoveries:
        await alert_error(callback, "Сначала открой эту локацию.")
        return
    artifacts = await run_sync(engine.collection_artifacts, callback.from_user.id, location_id)
    progress = next(
        item
        for item in await run_sync(engine.collection_progress, callback.from_user.id)
        if item["location_id"] == location_id
    )
    lines = [f"🏺 КОЛЛЕКЦИЯ: {LOCATIONS[location_id].name}", ""]
    for artifact in artifacts:
        if artifact["found"]:
            lines.append(
                f"{rarity_label(str(artifact['rarity']))} · {artifact['name']}\n"
                f"{artifact['description']}"
            )
        else:
            lines.append("❔ Неизвестный артефакт")
    lines.extend(
        [
            "",
            f"Прогресс: {progress['found']}/{progress['total']} · "
            f"{progress_bar(progress['found'], progress['total'])}",
        ]
    )
    lines.append("Статус: завершена." if progress["completed"] else "Статус: не завершена. Награда выдаётся один раз.")
    await edit_panel(callback, "\n\n".join(lines), add_back([], "collections"))


@dp.callback_query(F.data == "story")
async def story_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    player = await run_sync(db.get_player, callback.from_user.id)
    flags = await run_sync(db.get_story_flags, callback.from_user.id)
    rows: list[list[InlineKeyboardButton]] = []
    if player["story_stage"] == "intro" and player["location"] == "earth_orbit":
        text = (
            "📡 АВАРИЙНЫЙ СИГНАЛ\n\n"
            "Станция «Пионер-9» исчезла 17 лет назад. В последнем сообщении повторяется: "
            "«Не открывайте шлюз». Изучить сигнал?"
        )
        rows.append([InlineKeyboardButton(text="📡 Изучить сигнал", callback_data="story_action:signal")])
    elif player["story_stage"] == "moon_decision" and "moon_choice" not in flags:
        text = (
            "📡 ЛУННЫЙ ПЕРЕДАТЧИК\n\n"
            "Сканер обнаружил устойчивый сигнал. Можно изучить архив, включить передатчик "
            "или безопасно отключить его."
        )
        rows.extend(
            [
                [InlineKeyboardButton(text="🔬 Изучить архив", callback_data="story_action:analyze")],
                [InlineKeyboardButton(text="⚡ Активировать (−20 энергии)", callback_data="story_action:activate")],
                [InlineKeyboardButton(text="⛔ Отключить", callback_data="story_action:shutdown")],
            ]
        )
    elif player["story_stage"] == "pioneer_choice" and "pioneer_choice" not in flags:
        text = (
            "📖 ПОСЛЕДНИЙ ЖУРНАЛ «ПИОНЕРА-9»\n\n"
            "В журнале экипаж спорит о судьбе передатчика. Как поступить с данными?"
        )
        rows.extend(
            [
                [InlineKeyboardButton(text="📚 Скопировать журнал", callback_data="story_action:copy")],
                [InlineKeyboardButton(text="📡 Передать сигнал", callback_data="story_action:transmit")],
                [InlineKeyboardButton(text="🛑 Уничтожить передатчик", callback_data="story_action:destroy")],
            ]
        )
    else:
        text = (
            f"📖 ЖУРНАЛ ИСТОРИИ\n\n"
            f"Этап: {player['story_stage']}\n"
            f"Локация: {LOCATIONS[player['location']].name}\n\n"
            "Чтобы продвинуться, исследуй объект или выполни доступное задание."
        )
    rows.append(back_button())
    await edit_panel(callback, text, InlineKeyboardMarkup(inline_keyboard=rows))


@dp.callback_query(F.data.startswith("story_action:"))
async def story_action_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Сюжетное действие не найдено.")
        return
    action = callback.data.split(":", maxsplit=1)[1]
    try:
        result = await run_sync(engine.story_action, callback.from_user.id, action)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    await edit_panel(
        callback,
        result["text"] + level_up_text(result["level_ups"]),
        InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📖 Продолжить", callback_data="story")],
                [InlineKeyboardButton(text="🪐 Карта", callback_data="map")],
                back_button(),
            ]
        ),
    )


@dp.callback_query(F.data == "cases")
async def cases_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    player = await run_sync(db.get_player, callback.from_user.id)
    await edit_panel(
        callback,
        cases_text(player["orbitals"]) + "\n\n" + equipment_rarity_text(),
        case_catalog_keyboard(),
    )


@dp.callback_query(F.data.startswith("case:view:"))
async def case_view_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Кейс не найден.")
        return
    case_id = callback.data.split(":", maxsplit=2)[2]
    if case_id not in CASES:
        await alert_error(callback, "Кейс не найден.")
        return
    player = await run_sync(db.get_player, callback.from_user.id)
    await edit_panel(
        callback,
        case_detail_text(case_id, player["orbitals"]),
        create_case_keyboard(case_id),
    )


@dp.callback_query(F.data.startswith("case:open"))
async def open_case_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    case_id = "salvage_container"
    if callback.data and callback.data.startswith("case:open:"):
        case_id = callback.data.split(":", maxsplit=2)[2]
    try:
        reward = await run_sync(engine.open_case, callback.from_user.id, case_id=case_id)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    player = await run_sync(db.get_player, callback.from_user.id)
    rarity_line = f"\nРедкость: {reward['rarity']}." if reward["rarity"] else ""
    cosmetic_line = (
        "\nСкин можно надеть в разделе «Профиль → Скины ника»."
        if reward["cosmetic"] and not reward["duplicate"]
        else ""
    )
    await edit_panel(
        callback,
        f"🎁 КОНТЕЙНЕР ВСКРЫТ\n━━━━━━━━━━━━━━━━━━━━\n"
        f"{reward['case_name']}\nПолучено: {reward['name']} ×{reward['quantity']}."
        f"{rarity_line}{cosmetic_line}\n\nБаланс: {player['orbitals']} ◈",
        create_case_keyboard(case_id),
    )


@dp.callback_query(F.data == "laboratory")
@dp.callback_query(F.data == "craft")
async def laboratory_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    await edit_panel(
        callback,
        await laboratory_text(callback.from_user.id),
        await laboratory_keyboard(callback.from_user.id),
    )


@dp.callback_query(F.data == "laboratory:research:quantum_matrix")
async def research_quantum_matrix_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    try:
        await run_sync(engine.research_quantum_matrix, callback.from_user.id)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    await edit_panel(
        callback,
        "✅ ЧЕРТЁЖ ИССЛЕДОВАН\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Компоненты сохранены. Теперь можно собрать квантовую матрицу.",
        await laboratory_keyboard(callback.from_user.id),
    )


@dp.callback_query(F.data.in_({"laboratory:craft:quantum_matrix", "craft:quantum_matrix"}))
async def craft_quantum_matrix_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    try:
        await run_sync(engine.craft_quantum_matrix, callback.from_user.id)
    except engine.GameError as error:
        await alert_error(callback, str(error))
        return
    player = await run_sync(db.get_player, callback.from_user.id)
    inventory = await run_sync(db.get_inventory, callback.from_user.id)
    await edit_panel(
        callback,
        "✅ КВАНТОВАЯ МАТРИЦА СОБРАНА\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"На складе: {inventory['quantum_matrices']} шт.\n"
        f"Кредиты: {player['credits']}\n\n"
        "Рецепт не открывает маршруты и не меняет сюжетную прогрессию.",
        await laboratory_keyboard(callback.from_user.id),
    )


@dp.callback_query(F.data == "guild")
async def guild_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    text, keyboard = await guild_text(callback.from_user.id)
    await edit_panel(callback, text, keyboard)


@dp.callback_query(F.data == "guild:list")
async def guild_list_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    guilds = await run_sync(engine.list_guilds)
    if not guilds:
        await edit_panel(
            callback,
            "Открытых гильдий пока нет. Создай свою командой /guild_create Название.",
            add_back([], "guild"),
        )
        return
    rows = [
        [
            InlineKeyboardButton(
                text=f"🛡 {guild['name']} · ур. {guild['level']} · {guild['members']} участников",
                callback_data=f"guild:join:{guild['guild_id']}",
            )
        ]
        for guild in guilds
    ]
    await edit_panel(
        callback,
        "🔎 ОТКРЫТЫЕ ГИЛЬДИИ\n\nНажми на гильдию, чтобы вступить.",
        add_back(rows, "guild"),
    )


@dp.callback_query(F.data.startswith("guild:join:"))
async def guild_join_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    if callback.data is None:
        await alert_error(callback, "Гильдия не найдена.")
        return
    try:
        guild_id = int(callback.data.rsplit(":", maxsplit=1)[1])
        await run_sync(engine.join_guild, callback.from_user.id, guild_id)
    except (ValueError, engine.GameError) as error:
        await alert_error(callback, str(error) or "Гильдия не найдена.")
        return
    text, keyboard = await guild_text(callback.from_user.id)
    await edit_panel(callback, "✅ Ты вступил в гильдию.\n\n" + text, keyboard)


@dp.callback_query(F.data == "journal")
async def journal_callback(callback: CallbackQuery) -> None:
    await register_user(callback.from_user)
    discoveries = await run_sync(db.get_discoveries, callback.from_user.id)
    flags = await run_sync(db.get_story_flags, callback.from_user.id)
    lines = ["📖 ЖУРНАЛ ЭКСПЕДИЦИИ", ""]
    for discovery in discoveries[:30]:
        discovery_id = str(discovery["discovery_id"])
        if discovery_id.startswith("location:"):
            location_id = discovery_id.split(":", 1)[1]
            title = LOCATIONS.get(location_id)
            lines.append(f"🪐 Открыта локация: {title.name if title else location_id}")
        elif discovery_id.startswith("scan:"):
            location_id = discovery_id.split(":", 1)[1]
            title = LOCATIONS.get(location_id)
            lines.append(f"🔎 Проведено сканирование: {title.name if title else location_id}")
    if not discoveries:
        lines.append("Пока нет записей. Изучи аварийный сигнал на орбите Земли.")
    if flags.get("moon_choice"):
        lines.append(f"\nРешение на Луне: {flags['moon_choice']}.")
    if flags.get("pioneer_choice"):
        lines.append(f"Решение на «Пионере-9»: {flags['pioneer_choice']}.")
    await edit_panel(callback, "\n".join(lines), add_back([]))


async def main() -> None:
    await run_sync(db.initialize_database)
    logging.basicConfig(level=logging.INFO)
    logger.info("ORBITAL FRONTIER запущена")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
