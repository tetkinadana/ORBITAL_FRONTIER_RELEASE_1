"""Игровые правила и действия, не зависящие от Telegram.

Здесь рассчитываются перелёты, исследования, опыт, улучшения корабля,
сюжет, коллекции, кейсы, крафт и гильдии. Функции обращаются к SQLite
через game/database.py; пользовательские сообщения и кнопки находятся
в main.py.
"""

import random
import re
import sqlite3
from typing import Any

from game import database as db
from game.config import (
    CASES,
    DONATION_PACKAGES,
    EQUIPMENT_RARITY_CHANCES,
    FIRST_SCAN_CREDIT_REWARD,
    GUILD_ALLOWED_CONTRIBUTIONS,
    GUILD_CONTRIBUTION_XP_PER_UNIT,
    GUILD_DAILY_XP_CAP,
    GUILD_LEVEL_XP_BASE,
    GUILD_LEVEL_XP_STEP,
    GUILD_MAX_LEVEL,
    GUILD_MEMBER_BONUS_LEVELS,
    GUILD_STARTING_MEMBERS,
    LEVEL_CAP,
    LEVEL_REWARDS,
    LEVEL_XP_BASE,
    LEVEL_XP_EXPONENT,
    LOCATIONS,
    NICKNAME_COSMETICS,
    NICKNAME_COSMETIC_RARITY_CHANCES,
    QUANTUM_MATRIX_RECIPE,
    REFERRAL_FIRST_REWARD,
    REFERRAL_MAX_FRIENDS,
    REFERRAL_NEXT_REWARD,
    REFERRAL_TOPUP_BONUS_PERCENT,
    RESOURCES,
    SCAN_CREDIT_REWARD,
    SCAN_STORY_UNLOCKS,
    SHIP,
)


class GameError(ValueError):
    """Понятная игровая ошибка, которую интерфейс может показать игроку."""

    pass


# Опыт и награды игрока и гильдии.
def xp_for_next_level(level: int) -> int:
    if level < 1:
        raise ValueError("Уровень должен быть не меньше 1")
    return round(LEVEL_XP_BASE * level**LEVEL_XP_EXPONENT)


def xp_for_guild_level(level: int) -> int:
    if level < 1:
        raise ValueError("Уровень гильдии должен быть не меньше 1")
    return GUILD_LEVEL_XP_BASE + (level - 1) * GUILD_LEVEL_XP_STEP


def _award_xp(connection: sqlite3.Connection, telegram_id: int, amount: int) -> list[dict[str, Any]]:
    if amount <= 0:
        return []
    connection.execute(
        "UPDATE players SET hero_xp = hero_xp + ? WHERE telegram_id = ?",
        (amount, telegram_id),
    )
    player = connection.execute(
        "SELECT hero_level, hero_xp FROM players WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    if player is None:
        raise LookupError(f"Игрок {telegram_id} не найден")
    level = int(player["hero_level"])
    xp = int(player["hero_xp"])
    level_ups: list[dict[str, Any]] = []
    while level < LEVEL_CAP and xp >= xp_for_next_level(level):
        xp -= xp_for_next_level(level)
        level += 1
        reward = LEVEL_REWARDS.get(level, {})
        claimed = connection.execute(
            """
            INSERT OR IGNORE INTO level_rewards (telegram_id, level)
            VALUES (?, ?)
            """,
            (telegram_id, level),
        )
        if claimed.rowcount:
            awarded_reward: dict[str, int] = {}
            for resource_id, quantity in reward.items():
                if resource_id == "orbitals":
                    connection.execute(
                        "UPDATE players SET orbitals = orbitals + ? WHERE telegram_id = ?",
                        (quantity, telegram_id),
                    )
                    awarded_reward[resource_id] = quantity
                elif resource_id == "fuel":
                    ship = connection.execute(
                        "SELECT fuel FROM ships WHERE telegram_id = ?",
                        (telegram_id,),
                    ).fetchone()
                    fuel_awarded = min(quantity, SHIP["fuel_max"] - int(ship["fuel"]))
                    updated = connection.execute(
                        """
                        UPDATE ships SET fuel = fuel + ?
                        WHERE telegram_id = ?
                        """,
                        (fuel_awarded, telegram_id),
                    )
                    if updated.rowcount and fuel_awarded:
                        awarded_reward[resource_id] = fuel_awarded
                else:
                    awarded = _add_resource(
                        connection,
                        telegram_id,
                        resource_id,
                        quantity,
                        allow_partial=True,
                    )
                    if awarded:
                        awarded_reward[resource_id] = awarded
            level_ups.append({"level": level, "reward": awarded_reward})
    connection.execute(
        "UPDATE players SET hero_level = ?, hero_xp = ? WHERE telegram_id = ?",
        (level, xp, telegram_id),
    )
    return level_ups


def award_xp(telegram_id: int, amount: int, event_id: str) -> list[dict[str, Any]]:
    with db.database() as connection:
        inserted = connection.execute(
            """
            INSERT OR IGNORE INTO discoveries (telegram_id, discovery_id)
            VALUES (?, ?)
            """,
            (telegram_id, f"xp:{event_id}"),
        )
        if inserted.rowcount == 0:
            return []
        return _award_xp(connection, telegram_id, amount)


# Проверка требований маршрута и выполнение перелёта.
def route_requirements(telegram_id: int, location_id: str) -> list[str]:
    location = LOCATIONS.get(location_id)
    if location is None:
        return ["Эта локация не найдена."]
    player = db.get_player(telegram_id)
    requirements: list[str] = []
    if player["ship_level"] < location.required_ship_level:
        requirements.append(f"корабль уровня {location.required_ship_level}")
    if player["hero_level"] < location.required_hero_level:
        requirements.append(f"уровень героя {location.required_hero_level}")
    if player["engine_level"] < location.required_engine:
        requirements.append(f"двигатель уровня {location.required_engine}")
    if player["scanner_level"] < location.required_scanner:
        requirements.append(f"сканер уровня {location.required_scanner}")
    if player["fuel"] < location.fuel_cost:
        requirements.append(f"{location.fuel_cost} единиц топлива")
    if location.story_flag and db.get_story_flags(telegram_id).get(location.story_flag) != "1":
        requirements.append("завершить необходимый сюжетный этап")
    return requirements


def travel(telegram_id: int, location_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    location = LOCATIONS.get(location_id)
    if location is None:
        raise GameError("Эта локация не найдена.")
    if location_id == "earth_orbit":
        with db.database() as connection:
            player = connection.execute(
                "SELECT 1 FROM players WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
            if player is None:
                raise GameError("Сначала начни игру командой /start.")
            connection.execute(
                "UPDATE players SET location = 'earth_orbit' WHERE telegram_id = ?",
                (telegram_id,),
            )
        return {
            "location_id": location_id,
            "name": location.name,
            "fuel_spent": 0,
            "first_visit": False,
        }, []
    requirements = route_requirements(telegram_id, location_id)
    if requirements:
        raise GameError("Для перелёта нужно: " + ", ".join(requirements) + ".")

    level_ups: list[dict[str, Any]] = []
    with db.database() as connection:
        player = connection.execute(
            """
            SELECT p.location, s.fuel, s.ship_level, p.hero_level
            FROM players p JOIN ships s USING (telegram_id)
            WHERE p.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if int(player["ship_level"]) < location.required_ship_level:
            raise GameError(f"Нужен корабль уровня {location.required_ship_level}.")
        if int(player["hero_level"]) < location.required_hero_level:
            raise GameError(f"Нужен уровень героя {location.required_hero_level}.")
        modules = connection.execute(
            "SELECT engine_level, scanner_level FROM ships WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if int(modules["engine_level"]) < location.required_engine:
            raise GameError(f"Нужен двигатель уровня {location.required_engine}.")
        if int(modules["scanner_level"]) < location.required_scanner:
            raise GameError(f"Нужен сканер уровня {location.required_scanner}.")
        fuel_cost = location.fuel_cost
        if player["fuel"] < fuel_cost:
            raise GameError(f"Недостаточно топлива: нужно {fuel_cost}.")
        if location.story_flag:
            flag = connection.execute(
                "SELECT value FROM story_flags WHERE telegram_id = ? AND flag_id = ?",
                (telegram_id, location.story_flag),
            ).fetchone()
            if flag is None or flag["value"] != "1":
                raise GameError("Сюжетные координаты этого маршрута ещё не открыты.")
        connection.execute(
            "UPDATE ships SET fuel = fuel - ? WHERE telegram_id = ?",
            (fuel_cost, telegram_id),
        )
        connection.execute(
            "UPDATE players SET location = ? WHERE telegram_id = ?",
            (location_id, telegram_id),
        )
        first_visit = connection.execute(
            """
            INSERT OR IGNORE INTO discoveries (telegram_id, discovery_id)
            VALUES (?, ?)
            """,
            (telegram_id, f"location:{location_id}"),
        ).rowcount == 1
        if first_visit:
            connection.execute(
                "UPDATE ships SET ship_xp = ship_xp + 25 WHERE telegram_id = ?",
                (telegram_id,),
            )
            level_ups = _award_xp(connection, telegram_id, 50)
            connection.execute(
                """
                INSERT OR IGNORE INTO missions (telegram_id, mission_id, status)
                VALUES (?, ?, 'active')
                """,
                (telegram_id, f"visit_{location_id}"),
            )
            connection.execute(
                """
                UPDATE missions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ? AND mission_id = ?
                """,
                (telegram_id, f"visit_{location_id}"),
            )
        result = {
            "location_id": location_id,
            "name": location.name,
            "fuel_spent": fuel_cost,
            "first_visit": first_visit,
        }
    return result, level_ups


# Исследование локаций и расчёт занятого места в трюме.
def _cargo_used(connection: sqlite3.Connection, telegram_id: int) -> int:
    row = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM inventory WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    return int(row["total"])


def _cargo_capacity(connection: sqlite3.Connection, telegram_id: int) -> int:
    row = connection.execute(
        "SELECT cargo_level FROM ships WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    return SHIP["cargo_capacity"] + int(row["cargo_level"]) * 10


def _add_resource(
    connection: sqlite3.Connection,
    telegram_id: int,
    resource_id: str,
    amount: int,
    *,
    allow_partial: bool = False,
) -> int:
    if resource_id not in RESOURCES or amount <= 0:
        raise GameError("Некорректная награда.")
    free_capacity = _cargo_capacity(connection, telegram_id) - _cargo_used(connection, telegram_id)
    if free_capacity < amount and not allow_partial:
        raise GameError("В трюме нет места. Освободи место или улучши грузовой отсек.")
    amount = min(amount, max(0, free_capacity))
    if amount == 0:
        return 0
    connection.execute(
        """
        INSERT INTO inventory (telegram_id, resource_id, amount)
        VALUES (?, ?, ?)
        ON CONFLICT (telegram_id, resource_id)
        DO UPDATE SET amount = amount + excluded.amount
        """,
        (telegram_id, resource_id, amount),
    )
    return amount


def explore(telegram_id: int, rng: random.Random | None = None) -> dict[str, Any]:
    rng = rng or random.SystemRandom()
    player = db.get_player(telegram_id)
    location = LOCATIONS[player["location"]]
    outcome: dict[str, Any] = {"location": location.name, "resources": {}, "artifact": None, "level_ups": []}
    with db.database() as connection:
        ship = connection.execute(
            "SELECT energy, hull, scanner_level, protection_level FROM ships WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if ship is None:
            raise GameError("Сначала начни игру командой /start.")
        if ship["hull"] <= 0:
            raise GameError("Корпус повреждён. Сначала отремонтируй корабль на орбите Земли.")
        energy_cost = location.energy_cost
        if ship["energy"] < energy_cost:
            raise GameError(f"Недостаточно энергии: нужно {energy_cost}. Вернись на орбиту Земли для подзарядки.")
        used = _cargo_used(connection, telegram_id)
        capacity = _cargo_capacity(connection, telegram_id)
        if used >= capacity:
            raise GameError(f"Трюм заполнен: {used}/{capacity}. Улучши грузовой отсек или потрать ресурсы.")

        connection.execute(
            "UPDATE ships SET energy = energy - ? WHERE telegram_id = ?",
            (energy_cost, telegram_id),
        )
        hazard_chance = max(
            0.0,
            location.hazard_chance - int(ship["protection_level"]) * 0.03,
        )
        if rng.random() < hazard_chance:
            damage = max(1, 10 - int(ship["protection_level"]) * 3)
            connection.execute(
                "UPDATE ships SET hull = MAX(0, hull - ?) WHERE telegram_id = ?",
                (damage, telegram_id),
            )
            outcome["hazard_damage"] = damage
        scan = connection.execute(
            """
            INSERT OR IGNORE INTO discoveries (telegram_id, discovery_id)
            VALUES (?, ?)
            """,
            (telegram_id, f"scan:{player['location']}"),
        )
        connection.execute(
            "UPDATE players SET credits = credits + ? WHERE telegram_id = ?",
            (SCAN_CREDIT_REWARD, telegram_id),
        )
        if scan.rowcount:
            connection.execute(
                "UPDATE players SET credits = credits + ? WHERE telegram_id = ?",
                (FIRST_SCAN_CREDIT_REWARD, telegram_id),
            )
            connection.execute(
                "UPDATE ships SET ship_xp = ship_xp + 5 WHERE telegram_id = ?",
                (telegram_id,),
            )
            outcome["level_ups"] = _award_xp(connection, telegram_id, 35)
            connection.execute(
                """
                INSERT OR IGNORE INTO player_achievements (telegram_id, achievement_id)
                VALUES (?, 'first_scan')
                """,
                (telegram_id,),
            )
            if player["location"] == "moon":
                connection.execute(
                    """
                    INSERT OR IGNORE INTO story_flags (telegram_id, flag_id, value)
                    VALUES (?, 'moon_transmitter', '1')
                    """,
                    (telegram_id,),
                )
                connection.execute(
                    """
                    UPDATE missions
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ? AND mission_id = 'scan_moon'
                    """,
                    (telegram_id,),
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO missions (telegram_id, mission_id, status)
                    VALUES (?, 'moon_transmitter', 'active')
                    """,
                    (telegram_id,),
                )
                connection.execute(
                    "UPDATE players SET story_stage = 'moon_decision' WHERE telegram_id = ? AND story_stage = 'moon_signal'",
                    (telegram_id,),
                )
            if player["location"] in SCAN_STORY_UNLOCKS:
                flag_id = SCAN_STORY_UNLOCKS[player["location"]]
                unlocked = connection.execute(
                    """
                    INSERT OR IGNORE INTO story_flags (telegram_id, flag_id, value)
                    VALUES (?, ?, '1')
                    """,
                    (telegram_id, flag_id),
                )
                outcome["story_unlock"] = unlocked.rowcount == 1

        available = list(location.resources)
        resource_id = rng.choice(available)
        amount = rng.randint(1, 3)
        current_used = _cargo_used(connection, telegram_id)
        amount = min(amount, capacity - current_used)
        if amount > 0:
            _add_resource(connection, telegram_id, resource_id, amount)
            outcome["resources"][resource_id] = amount

        chance = min(0.75, 0.20 + int(ship["scanner_level"]) * 0.08)
        if rng.random() < chance:
            artifacts = connection.execute(
                """
                SELECT a.artifact_id, a.name, a.description, a.rarity
                FROM artifacts a
                LEFT JOIN player_artifacts pa
                    ON pa.artifact_id = a.artifact_id AND pa.telegram_id = ?
                WHERE a.location_id = ? AND pa.artifact_id IS NULL
                """,
                (telegram_id, player["location"]),
            ).fetchall()
            if artifacts:
                artifact = rng.choice(artifacts)
                artifact_rarity, _ = rng.choices(
                    EQUIPMENT_RARITY_CHANCES,
                    weights=[weight for _, weight in EQUIPMENT_RARITY_CHANCES],
                    k=1,
                )[0]
                connection.execute(
                    """
                    INSERT OR IGNORE INTO player_artifacts
                        (telegram_id, artifact_id, rarity)
                    VALUES (?, ?, ?)
                    """,
                    (telegram_id, artifact["artifact_id"], artifact_rarity),
                )
                outcome["artifact"] = {**dict(artifact), "rarity": artifact_rarity}
                xenoquartz_added = _add_resource(
                    connection,
                    telegram_id,
                    "xenoquartz",
                    1,
                    allow_partial=True,
                )
                if xenoquartz_added:
                    outcome["resources"]["xenoquartz"] = outcome["resources"].get("xenoquartz", 0) + xenoquartz_added
                outcome["level_ups"].extend(
                    _award_xp(connection, telegram_id, 60)
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO player_achievements (telegram_id, achievement_id)
                    VALUES (?, 'first_artifact')
                    """,
                    (telegram_id,),
                )

                collection_id = f"collection_{player['location']}"
                totals = connection.execute(
                    "SELECT COUNT(*) AS total FROM artifacts WHERE location_id = ?",
                    (player["location"],),
                ).fetchone()
                found = connection.execute(
                    """
                    SELECT COUNT(*) AS total FROM player_artifacts pa
                    JOIN artifacts a USING (artifact_id)
                    WHERE pa.telegram_id = ? AND a.location_id = ?
                    """,
                    (telegram_id, player["location"]),
                ).fetchone()
                if totals["total"] and found["total"] == totals["total"]:
                    completed = connection.execute(
                        """
                        INSERT OR IGNORE INTO player_collections
                            (telegram_id, collection_id, reward_claimed)
                        VALUES (?, ?, 1)
                        """,
                        (telegram_id, collection_id),
                    )
                    if completed.rowcount:
                        collection = connection.execute(
                            "SELECT reward_orbitals FROM collections WHERE collection_id = ?",
                            (collection_id,),
                        ).fetchone()
                        connection.execute(
                            "UPDATE players SET orbitals = orbitals + ? WHERE telegram_id = ?",
                            (collection["reward_orbitals"], telegram_id),
                        )
                        data_added = _add_resource(
                            connection,
                            telegram_id,
                            "data",
                            10,
                            allow_partial=True,
                        )
                        if data_added:
                            outcome["resources"]["data"] = outcome["resources"].get("data", 0) + data_added
                        outcome["level_ups"].extend(
                            _award_xp(connection, telegram_id, 100)
                        )
                        outcome["collection_completed"] = True
                        outcome["collection_orbitals"] = int(collection["reward_orbitals"])
                        outcome["collection_data"] = data_added

        if player["location"] == "pioneer9":
            connection.execute(
                """
                INSERT OR IGNORE INTO story_flags (telegram_id, flag_id, value)
                VALUES (?, 'pioneer_log_found', '1')
                """,
                (telegram_id,),
            )
            connection.execute(
                "UPDATE players SET story_stage = 'pioneer_choice' WHERE telegram_id = ?",
                (telegram_id,),
            )
            connection.execute(
                """
                UPDATE missions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ? AND mission_id = 'pioneer_signal'
                """,
                (telegram_id,),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO missions (telegram_id, mission_id, status)
                VALUES (?, 'pioneer_choice', 'active')
                """,
                (telegram_id,),
            )
    return outcome


# Обслуживание и улучшение корабля.
def upgrade_module(telegram_id: int, module: str) -> dict[str, Any]:
    allowed = {"ship", "engine", "scanner", "cargo", "protection", "energy"}
    if module not in allowed:
        raise GameError("Неизвестный модуль.")
    player = db.get_player(telegram_id)
    costs = SHIP["upgrade_costs"][module]
    with db.database() as connection:
        if player["location"] != "earth_orbit":
            raise GameError("Улучшать корабль можно только на орбитальной станции Земли.")
        ship = connection.execute(
            "SELECT * FROM ships WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        field = "ship_level" if module == "ship" else f"{module}_level"
        current_level = int(ship[field])
        max_level = 100 if module == "ship" else 5
        if current_level >= max_level:
            raise GameError("Этот модуль уже улучшен до максимального уровня.")
        advanced_costs = SHIP["advanced_upgrade_costs"].get(module, {}).get(current_level, {})
        multiplier = current_level + 1
        credit_cost = int(costs["credits"]) * multiplier
        if player["credits"] < credit_cost:
            raise GameError(f"Нужно кредитов: {credit_cost}.")
        for resource_id, quantity in costs.items():
            if resource_id == "credits":
                continue
            needed = int(quantity) * multiplier
            if needed == 0:
                continue
            row = connection.execute(
                """
                SELECT amount FROM inventory
                WHERE telegram_id = ? AND resource_id = ?
                """,
                (telegram_id, resource_id),
            ).fetchone()
            available = int(row["amount"]) if row else 0
            if available < needed:
                raise GameError(f"Для улучшения не хватает ресурса «{RESOURCES[resource_id].name}»: нужно {needed}.")
        for resource_id, needed in advanced_costs.items():
            row = connection.execute(
                """
                SELECT amount FROM inventory
                WHERE telegram_id = ? AND resource_id = ?
                """,
                (telegram_id, resource_id),
            ).fetchone()
            available = int(row["amount"]) if row else 0
            if available < needed:
                raise GameError(
                    f"Для следующего уровня не хватает ресурса "
                    f"«{RESOURCES[resource_id].name}»: нужно {needed}."
                )
        connection.execute(
            "UPDATE players SET credits = credits - ? WHERE telegram_id = ?",
            (credit_cost, telegram_id),
        )
        for resource_id, quantity in costs.items():
            if resource_id != "credits" and quantity:
                connection.execute(
                    """
                    UPDATE inventory SET amount = amount - ?
                    WHERE telegram_id = ? AND resource_id = ?
                    """,
                    (int(quantity) * multiplier, telegram_id, resource_id),
                )
        for resource_id, quantity in advanced_costs.items():
            connection.execute(
                """
                UPDATE inventory SET amount = amount - ?
                WHERE telegram_id = ? AND resource_id = ?
                """,
                (quantity, telegram_id, resource_id),
            )
        connection.execute(
            f"UPDATE ships SET {field} = {field} + 1 WHERE telegram_id = ?",
            (telegram_id,),
        )
        if module == "energy":
            connection.execute(
                "UPDATE ships SET energy = MIN(100, energy + 10) WHERE telegram_id = ?",
                (telegram_id,),
            )
    return {
        "module": module,
        "level": current_level + 1,
        "credits": credit_cost,
        "advanced_costs": advanced_costs,
    }


def refuel(telegram_id: int) -> int:
    with db.database() as connection:
        player = connection.execute(
            """
            SELECT p.location, p.credits, s.fuel
            FROM players p JOIN ships s USING (telegram_id)
            WHERE p.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if player["location"] != "earth_orbit":
            raise GameError("Заправиться можно только на орбитальной станции Земли.")
        amount = min(int(SHIP["refuel"]["fuel"]), SHIP["fuel_max"] - int(player["fuel"]))
        if amount <= 0:
            raise GameError("Бак уже полон.")
        if player["credits"] < SHIP["refuel"]["credits"]:
            raise GameError(f"Для заправки нужно {SHIP['refuel']['credits']} кредитов.")
        connection.execute(
            "UPDATE players SET credits = credits - ? WHERE telegram_id = ?",
            (SHIP["refuel"]["credits"], telegram_id),
        )
        connection.execute(
            "UPDATE ships SET fuel = fuel + ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
    return amount


def repair(telegram_id: int) -> int:
    with db.database() as connection:
        player = connection.execute(
            """
            SELECT p.location, s.hull FROM players p
            JOIN ships s USING (telegram_id) WHERE p.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if player["location"] != "earth_orbit":
            raise GameError("Ремонт доступен только на орбитальной станции Земли.")
        amount = min(int(SHIP["repair"]["hull"]), SHIP["hull_max"] - int(player["hull"]))
        if amount <= 0:
            raise GameError("Корпус уже полностью исправен.")
        scrap_cost = int(SHIP["repair"]["scrap"])
        credits_cost = int(SHIP["repair"]["credits"])
        row = connection.execute(
            "SELECT amount FROM inventory WHERE telegram_id = ? AND resource_id = 'scrap'",
            (telegram_id,),
        ).fetchone()
        if int(row["amount"]) < scrap_cost:
            raise GameError(f"Для ремонта нужно {scrap_cost} металлолома.")
        if connection.execute(
            "SELECT credits FROM players WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()["credits"] < credits_cost:
            raise GameError(f"Для ремонта нужно {credits_cost} кредитов.")
        connection.execute(
            "UPDATE inventory SET amount = amount - ? WHERE telegram_id = ? AND resource_id = 'scrap'",
            (scrap_cost, telegram_id),
        )
        connection.execute(
            "UPDATE players SET credits = credits - ? WHERE telegram_id = ?",
            (credits_cost, telegram_id),
        )
        connection.execute(
            "UPDATE ships SET hull = hull + ? WHERE telegram_id = ?",
            (amount, telegram_id),
        )
    return amount


def recharge(telegram_id: int) -> int:
    with db.database() as connection:
        player = connection.execute(
            """
            SELECT p.location, s.energy FROM players p
            JOIN ships s USING (telegram_id) WHERE p.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if player["location"] != "earth_orbit":
            raise GameError("Зарядить корабль можно только на орбитальной станции.")
        amount = SHIP["energy_max"] - int(player["energy"])
        if amount <= 0:
            raise GameError("Энергоблок уже заряжен.")
        connection.execute(
            "UPDATE ships SET energy = ? WHERE telegram_id = ?",
            (SHIP["energy_max"], telegram_id),
        )
    return amount


# Сюжетные решения, коллекции и найденные артефакты.
def story_action(telegram_id: int, action: str) -> dict[str, Any]:
    player = db.get_player(telegram_id)
    if action == "signal":
        if player["location"] != "earth_orbit":
            raise GameError("Сигнал можно изучить на орбитальной станции Земли.")
        with db.database() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO story_flags (telegram_id, flag_id, value)
                VALUES (?, 'signal_coordinates', '1')
                """,
                (telegram_id,),
            )
            connection.execute(
                "UPDATE players SET story_stage = 'moon_signal' WHERE telegram_id = ?",
                (telegram_id,),
            )
            connection.execute(
                """
                UPDATE missions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ? AND mission_id = 'pioneer_signal'
                """,
                (telegram_id,),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO missions (telegram_id, mission_id, status)
                VALUES (?, 'scan_moon', 'active')
                """,
                (telegram_id,),
            )
        levels = award_xp(telegram_id, 35, "story:signal")
        return {"text": "Сигнал ведёт к Луне. Координаты сохранены; установи улучшенный двигатель, чтобы открыть маршрут.", "level_ups": levels}

    if action in {"analyze", "activate", "shutdown"}:
        if player["location"] != "moon":
            raise GameError("Это решение доступно только после прибытия на Луну.")
        if db.get_story_flags(telegram_id).get("moon_transmitter") != "1":
            raise GameError("Сначала просканируй лунный передатчик.")
        if db.get_story_flags(telegram_id).get("moon_choice"):
            raise GameError("Решение по лунному передатчику уже сохранено.")
        costs = {"analyze": 0, "activate": 20, "shutdown": 0}
        labels = {
            "analyze": "изучен",
            "activate": "активирован",
            "shutdown": "отключён",
        }
        with db.database() as connection:
            ship = connection.execute(
                "SELECT energy FROM ships WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
            if int(ship["energy"]) < costs[action]:
                raise GameError("Для активации не хватает энергии.")
            if costs[action]:
                connection.execute(
                    "UPDATE ships SET energy = energy - ? WHERE telegram_id = ?",
                    (costs[action], telegram_id),
                )
            connection.execute(
                """
                INSERT INTO story_flags (telegram_id, flag_id, value)
                VALUES (?, 'moon_choice', ?)
                ON CONFLICT (telegram_id, flag_id) DO UPDATE SET value = excluded.value
                """,
                (telegram_id, action),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO story_flags (telegram_id, flag_id, value)
                VALUES (?, 'pioneer_coordinates', '1')
                """,
                (telegram_id,),
            )
            connection.execute(
                """
                UPDATE players SET story_stage = 'pioneer_signal'
                WHERE telegram_id = ?
                """,
                (telegram_id,),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO missions
                    (telegram_id, mission_id, status, completed_at)
                VALUES (?, 'moon_transmitter', 'completed', CURRENT_TIMESTAMP)
                """,
                (telegram_id,),
            )
            connection.execute(
                """
                UPDATE missions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ? AND mission_id = 'pioneer_choice'
                """,
                (telegram_id,),
            )
            if action == "activate":
                _add_resource(connection, telegram_id, "echo_shards", 2)
            elif action == "analyze":
                _add_resource(connection, telegram_id, "data", 5)
        levels = award_xp(telegram_id, 75, "story:moon_decision")
        return {"text": f"Передатчик {labels[action]}. Координаты станции «Пионер-9» сохранены.", "level_ups": levels}

    if action in {"copy", "transmit", "destroy"}:
        if player["location"] != "pioneer9":
            raise GameError("Финальное решение доступно только на станции «Пионер-9».")
        if db.get_story_flags(telegram_id).get("pioneer_log_found") != "1":
            raise GameError("Сначала просканируй станцию и найди журнал экипажа.")
        with db.database() as connection:
            already = connection.execute(
                "SELECT value FROM story_flags WHERE telegram_id = ? AND flag_id = 'pioneer_choice'",
                (telegram_id,),
            ).fetchone()
            if already:
                raise GameError("Решение уже сохранено. Основная история завершена.")
            connection.execute(
                "INSERT INTO story_flags (telegram_id, flag_id, value) VALUES (?, 'pioneer_choice', ?)",
                (telegram_id, action),
            )
            connection.execute(
                "UPDATE players SET story_stage = 'chapter_complete' WHERE telegram_id = ?",
                (telegram_id,),
            )
            if action == "copy":
                _add_resource(connection, telegram_id, "data", 15)
            elif action == "transmit":
                _add_resource(connection, telegram_id, "echo_shards", 3)
            else:
                connection.execute(
                    "UPDATE ships SET hull = MAX(0, hull - 10) WHERE telegram_id = ?",
                    (telegram_id,),
                )
                _add_resource(connection, telegram_id, "scrap", 3)
            connection.execute(
                """
                INSERT OR IGNORE INTO missions
                    (telegram_id, mission_id, status, completed_at)
                VALUES (?, 'pioneer9_chapter', 'completed', CURRENT_TIMESTAMP)
                """,
                (telegram_id,),
            )
            connection.execute(
                "UPDATE players SET orbitals = orbitals + 10 WHERE telegram_id = ?",
                (telegram_id,),
            )
        levels = award_xp(telegram_id, 150, "story:pioneer9")
        return {"text": "Решение записано в журнал. Глава «Пионер-9» завершена; получено 10 ОРБИТАЛОВ.", "level_ups": levels}

    raise GameError("Это действие сейчас недоступно.")


def collection_progress(telegram_id: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with db.database() as connection:
        for location_id, location in LOCATIONS.items():
            total = int(connection.execute(
                "SELECT COUNT(*) FROM artifacts WHERE location_id = ?",
                (location_id,),
            ).fetchone()[0])
            found = int(connection.execute(
                """
                SELECT COUNT(*) FROM player_artifacts pa
                JOIN artifacts a USING (artifact_id)
                WHERE pa.telegram_id = ? AND a.location_id = ?
                """,
                (telegram_id, location_id),
            ).fetchone()[0])
            completed = connection.execute(
                """
                SELECT 1 FROM player_collections pc
                JOIN collections c USING (collection_id)
                WHERE pc.telegram_id = ? AND c.location_id = ?
                """,
                (telegram_id, location_id),
            ).fetchone() is not None
            result.append({
                "location_id": location_id,
                "name": location.name,
                "found": found,
                "total": total,
                "completed": completed,
            })
    return result


def collection_artifacts(telegram_id: int, location_id: str) -> list[dict[str, Any]]:
    with db.database() as connection:
        rows = connection.execute(
            """
            SELECT a.artifact_id, a.name, a.description,
                   COALESCE(pa.rarity, a.rarity) AS rarity,
                   CASE WHEN pa.telegram_id IS NULL THEN 0 ELSE 1 END AS found
            FROM artifacts a
            LEFT JOIN player_artifacts pa
                ON pa.artifact_id = a.artifact_id AND pa.telegram_id = ?
            WHERE a.location_id = ?
            ORDER BY a.artifact_id
            """,
            (telegram_id, location_id),
        ).fetchall()
    return [dict(row) for row in rows]


# Игровой ник, косметика и создание квантовых матриц.
def set_nickname(telegram_id: int, nickname: str) -> str:
    cleaned = " ".join(nickname.split())
    if not 3 <= len(cleaned) <= 20 or not re.fullmatch(r"[\w -]+", cleaned):
        raise GameError(
            "Ник должен содержать 3–20 символов: буквы, цифры, пробелы, дефис или подчёркивание."
        )
    db.set_nickname(telegram_id, cleaned)
    return cleaned


def equip_nickname_cosmetic(telegram_id: int, cosmetic_id: str | None) -> None:
    if cosmetic_id is not None and cosmetic_id not in {
        str(item["cosmetic_id"]) for item in db.get_nickname_cosmetics(telegram_id)
    }:
        raise GameError("У тебя нет этого оформления ника.")
    db.equip_nickname_cosmetic(telegram_id, cosmetic_id)


def craft_quantum_matrix(telegram_id: int) -> dict[str, int]:
    with db.database() as connection:
        player = connection.execute(
            "SELECT location, credits FROM players WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if player["location"] != "earth_orbit":
            raise GameError("Сборка доступна только на орбитальной станции Земли.")
        researched = connection.execute(
            """
            SELECT 1 FROM discoveries
            WHERE telegram_id = ? AND discovery_id = 'lab:quantum_matrix'
            """,
            (telegram_id,),
        ).fetchone()
        if researched is None:
            raise GameError("Сначала собери материалы и исследуй чертёж в лаборатории.")

        for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items():
            if resource_id == "credits":
                if int(player["credits"]) < quantity:
                    raise GameError(f"Для крафта нужно {quantity} кредитов.")
                continue
            row = connection.execute(
                """
                SELECT amount FROM inventory
                WHERE telegram_id = ? AND resource_id = ?
                """,
                (telegram_id, resource_id),
            ).fetchone()
            if row is None or int(row["amount"]) < quantity:
                raise GameError(
                    f"Для крафта не хватает ресурса «{RESOURCES[resource_id].name}»: "
                    f"нужно {quantity}."
                )
        connection.execute(
            "UPDATE players SET credits = credits - ? WHERE telegram_id = ?",
            (QUANTUM_MATRIX_RECIPE["credits"], telegram_id),
        )
        for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items():
            if resource_id == "credits":
                continue
            connection.execute(
                """
                UPDATE inventory SET amount = amount - ?
                WHERE telegram_id = ? AND resource_id = ?
                """,
                (quantity, telegram_id, resource_id),
            )
        _add_resource(connection, telegram_id, "quantum_matrices", 1)
    return dict(QUANTUM_MATRIX_RECIPE)


def register_referral(invitee_id: int, inviter_id: int) -> int:
    """Привязывает нового игрока к пригласившему и начисляет разовую награду."""
    if invitee_id == inviter_id:
        return 0
    with db.database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM players WHERE telegram_id = ?",
            (inviter_id,),
        ).fetchone() is None:
            return 0
        existing = connection.execute(
            "SELECT 1 FROM referrals WHERE invitee_id = ?",
            (invitee_id,),
        ).fetchone()
        if existing:
            return 0
        invited_count = int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM referrals WHERE inviter_id = ?",
                (inviter_id,),
            ).fetchone()["count"]
        )
        if invited_count >= REFERRAL_MAX_FRIENDS:
            return 0
        reward = REFERRAL_FIRST_REWARD if invited_count == 0 else REFERRAL_NEXT_REWARD
        connection.execute(
            """
            INSERT INTO referrals (invitee_id, inviter_id, reward_orbitals)
            VALUES (?, ?, ?)
            """,
            (invitee_id, inviter_id, reward),
        )
        connection.execute(
            "UPDATE players SET orbitals = orbitals + ? WHERE telegram_id = ?",
            (reward, inviter_id),
        )
    return reward


def record_orbital_purchase(
    telegram_id: int,
    package_id: str,
    stars: int,
    charge_id: str,
) -> dict[str, int | bool]:
    """Начисляет оплату один раз и отправляет 5% ОРБИТАЛОВ пригласившему."""
    package = DONATION_PACKAGES.get(package_id)
    if package is None:
        raise GameError("Пакет ОРБИТАЛОВ не найден.")
    package_stars = int(package["stars"])
    orbitals = int(package["orbitals"])
    if stars != package_stars:
        raise GameError("Сумма оплаты не совпадает с выбранным пакетом.")
    if not charge_id:
        raise GameError("Telegram не передал идентификатор платежа.")

    with db.database() as connection:
        existing = connection.execute(
            """
            SELECT telegram_id, package_id, stars, orbitals, referral_bonus
            FROM orbital_payments WHERE charge_id = ?
            """,
            (charge_id,),
        ).fetchone()
        if existing:
            if (
                int(existing["telegram_id"]) != telegram_id
                or str(existing["package_id"]) != package_id
                or int(existing["stars"]) != stars
            ):
                raise GameError("Этот платёж уже зарегистрирован с другими данными.")
            return {
                "orbitals": int(existing["orbitals"]),
                "referral_bonus": int(existing["referral_bonus"]),
                "duplicate": True,
            }

        inviter = connection.execute(
            "SELECT inviter_id FROM referrals WHERE invitee_id = ?",
            (telegram_id,),
        ).fetchone()
        referral_bonus = orbitals * REFERRAL_TOPUP_BONUS_PERCENT // 100 if inviter else 0
        connection.execute(
            """
            INSERT INTO orbital_payments
                (charge_id, telegram_id, package_id, stars, orbitals, referral_bonus)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (charge_id, telegram_id, package_id, stars, orbitals, referral_bonus),
        )
        connection.execute(
            "UPDATE players SET orbitals = orbitals + ? WHERE telegram_id = ?",
            (orbitals, telegram_id),
        )
        if inviter and referral_bonus:
            connection.execute(
                "UPDATE players SET orbitals = orbitals + ? WHERE telegram_id = ?",
                (referral_bonus, int(inviter["inviter_id"])),
            )
    return {"orbitals": orbitals, "referral_bonus": referral_bonus, "duplicate": False}


def quantum_matrix_lab_status(telegram_id: int) -> dict[str, Any]:
    """Возвращает готовность чертежа и список необходимых для него ресурсов."""
    player = db.get_player(telegram_id)
    inventory = db.get_inventory(telegram_id)
    discoveries = db.get_discoveries(telegram_id)
    materials = [
        {
            "resource_id": resource_id,
            "name": "Кредиты" if resource_id == "credits" else RESOURCES[resource_id].name,
            "required": quantity,
            "owned": player["credits"] if resource_id == "credits" else inventory[resource_id],
        }
        for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items()
    ]
    return {
        "researched": any(
            discovery["discovery_id"] == "lab:quantum_matrix"
            for discovery in discoveries
        ),
        "materials_ready": all(item["owned"] >= item["required"] for item in materials),
        "materials": materials,
        "at_station": player["location"] == "earth_orbit",
    }


def research_quantum_matrix(telegram_id: int) -> None:
    """Исследует чертёж матрицы, если игрок собрал полный набор компонентов."""
    with db.database() as connection:
        player = connection.execute(
            "SELECT location, credits FROM players WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if player["location"] != "earth_orbit":
            raise GameError("Исследовать чертёж можно только на орбитальной станции Земли.")
        if connection.execute(
            """
            SELECT 1 FROM discoveries
            WHERE telegram_id = ? AND discovery_id = 'lab:quantum_matrix'
            """,
            (telegram_id,),
        ).fetchone():
            raise GameError("Чертёж квантовой матрицы уже исследован.")

        for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items():
            if resource_id == "credits":
                if int(player["credits"]) < quantity:
                    raise GameError(f"Для исследования нужно {quantity} кредитов.")
                continue
            row = connection.execute(
                """
                SELECT amount FROM inventory
                WHERE telegram_id = ? AND resource_id = ?
                """,
                (telegram_id, resource_id),
            ).fetchone()
            if row is None or int(row["amount"]) < quantity:
                raise GameError(
                    f"Для исследования не хватает ресурса «{RESOURCES[resource_id].name}»: "
                    f"нужно {quantity}."
                )

        connection.execute(
            """
            INSERT INTO discoveries (telegram_id, discovery_id)
            VALUES (?, 'lab:quantum_matrix')
            """,
            (telegram_id,),
        )


# Открытие кейсов и независимые таблицы игровых наград.
def open_case(
    telegram_id: int,
    rng: random.Random | None = None,
    case_id: str = "salvage_container",
) -> dict[str, Any]:
    case = CASES.get(case_id)
    if case is None:
        raise GameError("Такого кейса не существует.")
    rng = rng or random.SystemRandom()
    cosmetic_reward: dict[str, Any] | None = None
    duplicate = False
    if case_id == "neon_singularity":
        rarity, _ = rng.choices(
            NICKNAME_COSMETIC_RARITY_CHANCES,
            weights=[weight for _, weight in NICKNAME_COSMETIC_RARITY_CHANCES],
            k=1,
        )[0]
        cosmetic_id, reward_name, prefix, suffix = rng.choice(NICKNAME_COSMETICS[rarity])
        reward_id = cosmetic_id
        quantity = 1
        cosmetic_reward = {
            "rarity": rarity,
            "prefix": prefix,
            "suffix": suffix,
        }
    else:
        reward_id, reward_name, quantity, _ = rng.choices(
            case.rewards,
            weights=[item[3] for item in case.rewards],
            k=1,
        )[0]
    with db.database() as connection:
        player = connection.execute(
            "SELECT orbitals FROM players WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if player is None:
            raise GameError("Сначала начни игру командой /start.")
        if int(player["orbitals"]) < case.cost:
            raise GameError(f"Для кейса нужно {case.cost} ОРБИТАЛОВ.")
        if cosmetic_reward is not None:
            duplicate = connection.execute(
                """
                SELECT 1 FROM player_nickname_cosmetics
                WHERE telegram_id = ? AND cosmetic_id = ?
                """,
                (telegram_id, reward_id),
            ).fetchone() is not None
            if duplicate:
                connection.execute(
                    "UPDATE players SET orbitals = orbitals + 5 WHERE telegram_id = ?",
                    (telegram_id,),
                )
                reward_name = f"{reward_name} · дубликат, компенсация 5 ◈"
            else:
                connection.execute(
                    """
                    INSERT INTO player_nickname_cosmetics (telegram_id, cosmetic_id)
                    VALUES (?, ?)
                    """,
                    (telegram_id, reward_id),
                )
        elif reward_id == "fuel":
            ship = connection.execute(
                "SELECT fuel FROM ships WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
            if ship is None:
                raise GameError("Корабль игрока не найден.")
            if int(ship["fuel"]) + quantity > SHIP["fuel_max"]:
                raise GameError("В баке недостаточно места для топливной награды кейса.")
        elif cosmetic_reward is None and _cargo_used(connection, telegram_id) + quantity > _cargo_capacity(connection, telegram_id):
            raise GameError("В трюме нет места для награды из кейса.")
        connection.execute(
            "UPDATE players SET orbitals = orbitals - ? WHERE telegram_id = ?",
            (case.cost, telegram_id),
        )
        if cosmetic_reward is None:
            if reward_id == "fuel":
                connection.execute(
                    "UPDATE ships SET fuel = fuel + ? WHERE telegram_id = ?",
                    (quantity, telegram_id),
                )
            else:
                _add_resource(connection, telegram_id, reward_id, quantity)
        connection.execute(
            """
            INSERT INTO case_openings
                (telegram_id, case_id, reward_id, cost_paid)
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, case_id, reward_id, case.cost),
        )
    return {
        "case_id": case_id,
        "case_name": case.name,
        "reward_id": reward_id,
        "name": reward_name,
        "quantity": quantity,
        "cost": case.cost,
        "rarity": cosmetic_reward["rarity"] if cosmetic_reward is not None else None,
        "cosmetic": cosmetic_reward is not None,
        "duplicate": duplicate,
    }


# Создание и управление гильдиями, их заданиями и достижениями.
def create_guild(telegram_id: int, name: str, description: str = "") -> int:
    cleaned = " ".join(name.split())
    if not 3 <= len(cleaned) <= 30 or not re.fullmatch(r"[\wА-Яа-яЁё -]+", cleaned):
        raise GameError("Название гильдии должно быть длиной 3–30 символов (буквы, цифры, пробел и дефис).")
    if len(description) > 160:
        raise GameError("Описание гильдии не должно превышать 160 символов.")
    with db.database() as connection:
        if connection.execute(
            "SELECT 1 FROM guild_members WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone():
            raise GameError("Ты уже состоишь в гильдии.")
        try:
            cursor = connection.execute(
                """
                INSERT INTO guilds (name, description, leader_id)
                VALUES (?, ?, ?)
                """,
                (cleaned, description, telegram_id),
            )
        except sqlite3.IntegrityError as error:
            raise GameError("Гильдия с таким названием уже существует.") from error
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite не вернула ID созданной гильдии")
        guild_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO guild_members (guild_id, telegram_id, role)
            VALUES (?, ?, 'leader')
            """,
            (guild_id, telegram_id),
        )
        connection.execute(
            "INSERT INTO guild_events (guild_id, telegram_id, event_type, details) VALUES (?, ?, 'created', ?)",
            (guild_id, telegram_id, cleaned),
        )
        connection.execute(
            """
            INSERT INTO guild_missions
                (guild_id, title, resource_id, target_amount, reward_xp)
            VALUES (?, 'Общий запас металлолома', 'scrap', 10, 50)
            """,
            (guild_id,),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO player_achievements (telegram_id, achievement_id)
            VALUES (?, 'first_guild')
            """,
            (telegram_id,),
        )
    return guild_id


def list_guilds(limit: int = 20) -> list[dict[str, Any]]:
    with db.database() as connection:
        rows = connection.execute(
            """
            SELECT g.guild_id, g.name, g.description, g.level, g.xp,
                   COUNT(m.telegram_id) AS members
            FROM guilds g
            LEFT JOIN guild_members m USING (guild_id)
            WHERE g.join_mode = 'open'
            GROUP BY g.guild_id
            ORDER BY g.level DESC, g.created_at
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def join_guild(telegram_id: int, guild_id: int) -> None:
    with db.database() as connection:
        if connection.execute(
            "SELECT 1 FROM guild_members WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone():
            raise GameError("Ты уже состоишь в гильдии.")
        guild = connection.execute(
            """
            SELECT g.level, g.join_mode, COUNT(m.telegram_id) AS members
            FROM guilds g LEFT JOIN guild_members m USING (guild_id)
            WHERE g.guild_id = ? GROUP BY g.guild_id
            """,
            (guild_id,),
        ).fetchone()
        if guild is None:
            raise GameError("Гильдия не найдена.")
        if guild["join_mode"] != "open":
            raise GameError("В эту гильдию можно вступить только по приглашению.")
        if int(guild["members"]) >= guild_member_limit(int(guild["level"])):
            raise GameError("В гильдии нет свободных мест.")
        connection.execute(
            "INSERT INTO guild_members (guild_id, telegram_id) VALUES (?, ?)",
            (guild_id, telegram_id),
        )
        connection.execute(
            "INSERT INTO guild_events (guild_id, telegram_id, event_type) VALUES (?, ?, 'joined')",
            (guild_id, telegram_id),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO guild_missions
                (guild_id, title, resource_id, target_amount, reward_xp)
            VALUES (?, 'Общий запас металлолома', 'scrap', 10, 50)
            """,
            (guild_id,),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO player_achievements (telegram_id, achievement_id)
            VALUES (?, 'first_guild')
            """,
            (telegram_id,),
        )


def guild_member_limit(level: int) -> int:
    return GUILD_STARTING_MEMBERS + sum(
        bonus for required_level, bonus in GUILD_MEMBER_BONUS_LEVELS.items()
        if level >= required_level
    )


def contribute_to_guild(telegram_id: int, resource_id: str, amount: int) -> dict[str, Any]:
    if resource_id not in GUILD_ALLOWED_CONTRIBUTIONS or resource_id not in RESOURCES:
        raise GameError("Этот ресурс нельзя вносить в гильдию.")
    if amount < 1 or amount > 1000:
        raise GameError("Количество должно быть от 1 до 1000.")
    with db.database() as connection:
        member = connection.execute(
            """
            SELECT g.guild_id, g.level, m.role FROM guild_members m
            JOIN guilds g USING (guild_id) WHERE m.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
        if member is None:
            raise GameError("Сначала вступи в гильдию.")
        inventory = connection.execute(
            """
            SELECT amount FROM inventory
            WHERE telegram_id = ? AND resource_id = ?
            """,
            (telegram_id, resource_id),
        ).fetchone()
        if inventory is None or int(inventory["amount"]) < amount:
            raise GameError(f"Недостаточно ресурса «{RESOURCES[resource_id].name}».")
        connection.execute(
            "UPDATE inventory SET amount = amount - ? WHERE telegram_id = ? AND resource_id = ?",
            (amount, telegram_id, resource_id),
        )
        connection.execute(
            """
            INSERT INTO guild_inventory (guild_id, resource_id, amount)
            VALUES (?, ?, ?)
            ON CONFLICT (guild_id, resource_id)
            DO UPDATE SET amount = amount + excluded.amount
            """,
            (member["guild_id"], resource_id, amount),
        )
        xp = amount * GUILD_CONTRIBUTION_XP_PER_UNIT
        activity_date = connection.execute("SELECT date('now')").fetchone()[0]
        connection.execute(
            """
            INSERT OR IGNORE INTO guild_daily_xp
                (guild_id, telegram_id, activity_date, xp_awarded)
            VALUES (?, ?, ?, 0)
            """,
            (member["guild_id"], telegram_id, activity_date),
        )
        daily = connection.execute(
            """
            SELECT xp_awarded FROM guild_daily_xp
            WHERE guild_id = ? AND telegram_id = ? AND activity_date = ?
            """,
            (member["guild_id"], telegram_id, activity_date),
        ).fetchone()
        xp_awarded = min(xp, max(0, GUILD_DAILY_XP_CAP - int(daily["xp_awarded"])))
        connection.execute(
            """
            UPDATE guild_daily_xp SET xp_awarded = xp_awarded + ?
            WHERE guild_id = ? AND telegram_id = ? AND activity_date = ?
            """,
            (xp_awarded, member["guild_id"], telegram_id, activity_date),
        )
        connection.execute(
            """
            UPDATE guilds
            SET total_contribution = total_contribution + ?, xp = xp + ?
            WHERE guild_id = ?
            """,
            (amount, xp_awarded, member["guild_id"]),
        )
        connection.execute(
            """
            UPDATE guild_members SET contribution_total = contribution_total + ?
            WHERE guild_id = ? AND telegram_id = ?
            """,
            (amount, member["guild_id"], telegram_id),
        )
        connection.execute(
            """
            INSERT INTO guild_contributions
                (guild_id, telegram_id, resource_id, amount)
            VALUES (?, ?, ?, ?)
            """,
            (member["guild_id"], telegram_id, resource_id, amount),
        )
        connection.execute(
            """
            INSERT INTO guild_events (guild_id, telegram_id, event_type, details)
            VALUES (?, ?, 'contributed', ?)
            """,
            (member["guild_id"], telegram_id, f"{resource_id}:{amount}"),
        )
        missions = connection.execute(
            """
            SELECT mission_id, title, progress, target_amount, reward_xp
            FROM guild_missions
            WHERE guild_id = ? AND resource_id = ? AND status = 'active'
            """,
            (member["guild_id"], resource_id),
        ).fetchall()
        mission_xp = 0
        for mission in missions:
            progress = int(mission["progress"]) + amount
            if progress >= int(mission["target_amount"]):
                completed = connection.execute(
                    """
                    UPDATE guild_missions
                    SET progress = target_amount, status = 'completed',
                        completed_at = CURRENT_TIMESTAMP
                    WHERE mission_id = ? AND status = 'active'
                    """,
                    (mission["mission_id"],),
                )
                if completed.rowcount:
                    mission_xp += int(mission["reward_xp"])
                    connection.execute(
                        """
                        INSERT INTO guild_events
                            (guild_id, telegram_id, event_type, details)
                        VALUES (?, ?, 'mission_completed', ?)
                        """,
                        (member["guild_id"], telegram_id, str(mission["title"]) if "title" in mission.keys() else str(mission["mission_id"])),
                    )
            else:
                connection.execute(
                    "UPDATE guild_missions SET progress = ? WHERE mission_id = ?",
                    (progress, mission["mission_id"]),
                )
        if mission_xp:
            connection.execute(
                "UPDATE guilds SET xp = xp + ? WHERE guild_id = ?",
                (mission_xp, member["guild_id"]),
            )
        guild = connection.execute(
            "SELECT level, xp FROM guilds WHERE guild_id = ?",
            (member["guild_id"],),
        ).fetchone()
        level = int(guild["level"])
        current_xp = int(guild["xp"])
        levels_gained = 0
        while level < GUILD_MAX_LEVEL and current_xp >= xp_for_guild_level(level):
            current_xp -= xp_for_guild_level(level)
            level += 1
            levels_gained += 1
            bonus = GUILD_MEMBER_BONUS_LEVELS.get(level, 0)
            if bonus:
                connection.execute(
                    "INSERT INTO guild_events (guild_id, telegram_id, event_type, details) VALUES (?, ?, 'level_up', ?)",
                    (member["guild_id"], telegram_id, str(level)),
                )
        connection.execute(
            "UPDATE guilds SET level = ?, xp = ? WHERE guild_id = ?",
            (level, current_xp, member["guild_id"]),
        )
    return {"guild_id": int(member["guild_id"]), "xp_gained": xp_awarded, "level": level, "levels_gained": levels_gained}


def leave_guild(telegram_id: int) -> None:
    with db.database() as connection:
        member = connection.execute(
            "SELECT guild_id, role FROM guild_members WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if member is None:
            raise GameError("Ты не состоишь в гильдии.")
        if member["role"] == "leader":
            raise GameError("Лидер не может покинуть гильдию, пока не передаст лидерство.")
        connection.execute(
            "DELETE FROM guild_members WHERE guild_id = ? AND telegram_id = ?",
            (member["guild_id"], telegram_id),
        )
        connection.execute(
            "INSERT INTO guild_events (guild_id, telegram_id, event_type) VALUES (?, ?, 'left')",
            (member["guild_id"], telegram_id),
        )


def guild_manage(telegram_id: int, target_id: int, action: str) -> None:
    if action not in {"promote", "demote", "kick"}:
        raise GameError("Неизвестное действие.")
    with db.database() as connection:
        actor = connection.execute(
            "SELECT guild_id, role FROM guild_members WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        target = connection.execute(
            "SELECT guild_id, role FROM guild_members WHERE telegram_id = ?",
            (target_id,),
        ).fetchone()
        if actor is None or target is None or actor["guild_id"] != target["guild_id"]:
            raise GameError("Игрок не состоит в твоей гильдии.")
        if actor["role"] != "leader":
            raise GameError("Управлять составом может только лидер.")
        if target["role"] == "leader":
            raise GameError("Нельзя изменить роль лидера.")
        if action == "promote":
            connection.execute(
                "UPDATE guild_members SET role = 'officer' WHERE telegram_id = ?",
                (target_id,),
            )
            event = "promoted"
        elif action == "demote":
            connection.execute(
                "UPDATE guild_members SET role = 'member' WHERE telegram_id = ?",
                (target_id,),
            )
            event = "demoted"
        else:
            connection.execute(
                "DELETE FROM guild_members WHERE telegram_id = ?",
                (target_id,),
            )
            event = "kicked"
        connection.execute(
            "INSERT INTO guild_events (guild_id, telegram_id, event_type, details) VALUES (?, ?, ?, ?)",
            (actor["guild_id"], telegram_id, event, str(target_id)),
        )


def update_guild_description(telegram_id: int, description: str) -> None:
    if len(description) > 160:
        raise GameError("Описание гильдии не должно превышать 160 символов.")
    with db.database() as connection:
        member = connection.execute(
            "SELECT guild_id, role FROM guild_members WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if member is None or member["role"] != "leader":
            raise GameError("Изменить описание может только лидер гильдии.")
        connection.execute(
            "UPDATE guilds SET description = ? WHERE guild_id = ?",
            (description, member["guild_id"]),
        )


def guild_inventory(guild_id: int) -> dict[str, int]:
    with db.database() as connection:
        rows = connection.execute(
            "SELECT resource_id, amount FROM guild_inventory WHERE guild_id = ?",
            (guild_id,),
        ).fetchall()
    return {str(row["resource_id"]): int(row["amount"]) for row in rows}


def get_guild_missions(guild_id: int) -> list[dict[str, Any]]:
    with db.database() as connection:
        rows = connection.execute(
            """
            SELECT mission_id, title, resource_id, target_amount, progress,
                   status, reward_xp
            FROM guild_missions
            WHERE guild_id = ?
            ORDER BY status, mission_id
            """,
            (guild_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def achievement_list(telegram_id: int) -> list[dict[str, Any]]:
    with db.database() as connection:
        rows = connection.execute(
            """
            SELECT a.achievement_id, a.description, pa.unlocked_at
            FROM player_achievements pa
            JOIN achievements a USING (achievement_id)
            WHERE pa.telegram_id = ?
            ORDER BY pa.unlocked_at
            """,
            (telegram_id,),
        ).fetchall()
    return [dict(row) for row in rows]
