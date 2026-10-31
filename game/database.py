"""Хранение игрового прогресса в SQLite.

Этот модуль создаёт таблицы и миграции, а также предоставляет функции
для чтения и изменения данных игроков, кораблей, ресурсов и гильдий.
Игровые правила находятся в game/engine.py; файл базы создаётся рядом
с main.py и называется orbital.db.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, TypedDict

from game.config import (
    ARTIFACT_NAMES,
    DATABASE_TIMEOUT_SECONDS,
    LOCATIONS,
    NICKNAME_COSMETICS,
    RESOURCES,
    SHIP,
)

DATABASE_PATH = Path(__file__).resolve().parent.parent / "orbital.db"


# Описание полей игрока и гильдии помогает проверять структуру данных в коде.
class Player(TypedDict):
    telegram_id: int
    username: str | None
    display_name: str | None
    nickname: str | None
    nickname_prefix: str
    nickname_suffix: str
    registered_at: str
    story_stage: str
    hero_level: int
    hero_xp: int
    credits: int
    orbitals: int
    fuel: int
    location: str
    ship_level: int
    ship_xp: int
    hull: int
    energy: int
    engine_level: int
    scanner_level: int
    cargo_level: int
    protection_level: int
    energy_level: int
    iron_ore: int
    crystals: int
    science_data: int
    panel_chat_id: int | None
    panel_message_id: int | None


class Guild(TypedDict):
    guild_id: int
    name: str
    description: str
    leader_id: int
    level: int
    xp: int
    total_contribution: int
    created_at: str
    join_mode: str
    role: str
    contribution_total: int


@contextmanager
def database() -> Generator[sqlite3.Connection, None, None]:
    """Открывает соединение с транзакцией и закрывает его после работы."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=DATABASE_TIMEOUT_SECONDS)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Создаёт игровые таблицы и применяет недостающие миграции."""
    with database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                nickname TEXT,
                registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                story_stage TEXT NOT NULL DEFAULT 'intro',
                hero_level INTEGER NOT NULL DEFAULT 1 CHECK (hero_level BETWEEN 1 AND 100),
                hero_xp INTEGER NOT NULL DEFAULT 0 CHECK (hero_xp >= 0),
                credits INTEGER NOT NULL DEFAULT 500 CHECK (credits >= 0),
                orbitals INTEGER NOT NULL DEFAULT 0 CHECK (orbitals >= 0),
                fuel INTEGER NOT NULL DEFAULT 100 CHECK (fuel >= 0),
                location TEXT NOT NULL DEFAULT 'earth_orbit',
                ship_level INTEGER NOT NULL DEFAULT 0 CHECK (ship_level >= 0),
                iron_ore INTEGER NOT NULL DEFAULT 0 CHECK (iron_ore >= 0),
                crystals INTEGER NOT NULL DEFAULT 0 CHECK (crystals >= 0),
                science_data INTEGER NOT NULL DEFAULT 0 CHECK (science_data >= 0),
                panel_chat_id INTEGER,
                panel_message_id INTEGER
            )
            """
        )
        player_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(players)").fetchall()
        }
        for column, definition in (
            ("username", "TEXT"),
            ("display_name", "TEXT"),
            ("nickname", "TEXT"),
            ("registered_at", "TEXT"),
            ("story_stage", "TEXT NOT NULL DEFAULT 'intro'"),
            ("hero_level", "INTEGER NOT NULL DEFAULT 1"),
            ("hero_xp", "INTEGER NOT NULL DEFAULT 0"),
        ):
            if column not in player_columns:
                connection.execute(f"ALTER TABLE players ADD COLUMN {column} {definition}")
        connection.execute(
            "UPDATE players SET registered_at = CURRENT_TIMESTAMP WHERE registered_at IS NULL"
        )
        orbit_start_migration = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE migration_id = 'earth_orbit_start_v1'"
        ).fetchone() is None
        if orbit_start_migration:
            connection.execute("UPDATE players SET location = 'earth_orbit'")
            connection.execute(
                "INSERT INTO schema_migrations (migration_id) VALUES ('earth_orbit_start_v1')"
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ships (
                telegram_id INTEGER PRIMARY KEY,
                ship_level INTEGER NOT NULL DEFAULT 1 CHECK (ship_level BETWEEN 1 AND 100),
                ship_xp INTEGER NOT NULL DEFAULT 0 CHECK (ship_xp >= 0),
                fuel INTEGER NOT NULL DEFAULT 100 CHECK (fuel BETWEEN 0 AND 100),
                hull INTEGER NOT NULL DEFAULT 100 CHECK (hull BETWEEN 0 AND 100),
                energy INTEGER NOT NULL DEFAULT 80 CHECK (energy BETWEEN 0 AND 100),
                engine_level INTEGER NOT NULL DEFAULT 0 CHECK (engine_level >= 0),
                scanner_level INTEGER NOT NULL DEFAULT 0 CHECK (scanner_level >= 0),
                cargo_level INTEGER NOT NULL DEFAULT 0 CHECK (cargo_level >= 0),
                protection_level INTEGER NOT NULL DEFAULT 0 CHECK (protection_level >= 0),
                energy_level INTEGER NOT NULL DEFAULT 0 CHECK (energy_level >= 0),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO ships
                (telegram_id, ship_level, fuel, hull, energy)
            SELECT telegram_id, MAX(1, ship_level + 1), MIN(fuel, 100), 100, 80
            FROM players
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                telegram_id INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0 CHECK (amount >= 0),
                PRIMARY KEY (telegram_id, resource_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        for resource_id in RESOURCES:
            connection.execute(
                """
                INSERT OR IGNORE INTO inventory (telegram_id, resource_id, amount)
                SELECT telegram_id, ?, 0 FROM players
                """,
                (resource_id,),
            )
        legacy_inventory_migration = connection.execute(
            "SELECT 1 FROM schema_migrations WHERE migration_id = 'legacy_inventory_v1'"
        ).fetchone() is None
        if legacy_inventory_migration:
            for resource_id, column in (
                ("scrap", "iron_ore"),
                ("data", "science_data"),
                ("nebulite", "crystals"),
            ):
                connection.execute(
                    f"""
                    UPDATE inventory
                    SET amount = (SELECT {column} FROM players WHERE players.telegram_id = inventory.telegram_id)
                    WHERE resource_id = ?
                    """,
                    (resource_id,),
                )
            connection.execute(
                "INSERT INTO schema_migrations (migration_id) VALUES ('legacy_inventory_v1')"
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS discoveries (
                telegram_id INTEGER NOT NULL,
                discovery_id TEXT NOT NULL,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, discovery_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS story_flags (
                telegram_id INTEGER NOT NULL,
                flag_id TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (telegram_id, flag_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                location_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                required_ship_level INTEGER NOT NULL DEFAULT 1 CHECK (required_ship_level >= 1),
                required_hero_level INTEGER NOT NULL DEFAULT 1 CHECK (required_hero_level >= 1),
                fuel_cost INTEGER NOT NULL DEFAULT 0 CHECK (fuel_cost >= 0),
                energy_cost INTEGER NOT NULL DEFAULT 0 CHECK (energy_cost >= 0),
                required_engine INTEGER NOT NULL DEFAULT 0 CHECK (required_engine >= 0),
                required_scanner INTEGER NOT NULL DEFAULT 0 CHECK (required_scanner >= 0),
                required_story_flag TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS missions (
                telegram_id INTEGER NOT NULL,
                mission_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('available', 'active', 'completed')),
                started_at TEXT,
                completed_at TEXT,
                PRIMARY KEY (telegram_id, mission_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                rarity TEXT NOT NULL,
                discovery_method TEXT NOT NULL,
                FOREIGN KEY (location_id) REFERENCES locations (location_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_artifacts (
                telegram_id INTEGER NOT NULL,
                artifact_id TEXT NOT NULL,
                rarity TEXT,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, artifact_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (artifact_id) REFERENCES artifacts (artifact_id)
            )
            """
        )
        artifact_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(player_artifacts)").fetchall()
        }
        if "rarity" not in artifact_columns:
            connection.execute("ALTER TABLE player_artifacts ADD COLUMN rarity TEXT")
        connection.execute(
            """
            UPDATE player_artifacts
            SET rarity = (
                SELECT rarity FROM artifacts
                WHERE artifacts.artifact_id = player_artifacts.artifact_id
            )
            WHERE rarity IS NULL
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS nickname_cosmetics (
                cosmetic_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                prefix TEXT NOT NULL,
                suffix TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_nickname_cosmetics (
                telegram_id INTEGER NOT NULL,
                cosmetic_id TEXT NOT NULL,
                obtained_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, cosmetic_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (cosmetic_id) REFERENCES nickname_cosmetics (cosmetic_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS equipped_nickname_cosmetics (
                telegram_id INTEGER PRIMARY KEY,
                cosmetic_id TEXT NOT NULL,
                FOREIGN KEY (telegram_id, cosmetic_id)
                    REFERENCES player_nickname_cosmetics (telegram_id, cosmetic_id)
                    ON DELETE CASCADE
            )
            """
        )
        for rarity, cosmetics in NICKNAME_COSMETICS.items():
            for cosmetic_id, name, prefix, suffix in cosmetics:
                connection.execute(
                    """
                    INSERT INTO nickname_cosmetics
                        (cosmetic_id, name, rarity, prefix, suffix)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (cosmetic_id) DO UPDATE SET
                        name = excluded.name,
                        rarity = excluded.rarity,
                        prefix = excluded.prefix,
                        suffix = excluded.suffix
                    """,
                    (cosmetic_id, name, rarity, prefix, suffix),
                )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                collection_id TEXT PRIMARY KEY,
                location_id TEXT NOT NULL UNIQUE,
                reward_orbitals INTEGER NOT NULL DEFAULT 5,
                FOREIGN KEY (location_id) REFERENCES locations (location_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_collections (
                telegram_id INTEGER NOT NULL,
                collection_id TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reward_claimed INTEGER NOT NULL DEFAULT 1 CHECK (reward_claimed IN (0, 1)),
                PRIMARY KEY (telegram_id, collection_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (collection_id) REFERENCES collections (collection_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS level_rewards (
                telegram_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, level),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                reward_configuration TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_achievements (
                telegram_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, achievement_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (achievement_id) REFERENCES achievements (achievement_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS case_openings (
                opening_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                case_id TEXT NOT NULL,
                reward_id TEXT NOT NULL,
                opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                cost_paid INTEGER NOT NULL CHECK (cost_paid >= 0),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                leader_id INTEGER NOT NULL,
                level INTEGER NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 100),
                xp INTEGER NOT NULL DEFAULT 0 CHECK (xp >= 0),
                total_contribution INTEGER NOT NULL DEFAULT 0 CHECK (total_contribution >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                join_mode TEXT NOT NULL DEFAULT 'open' CHECK (join_mode IN ('open', 'invite')),
                FOREIGN KEY (leader_id) REFERENCES players (telegram_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_members (
                guild_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('leader', 'officer', 'member')),
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                contribution_total INTEGER NOT NULL DEFAULT 0 CHECK (contribution_total >= 0),
                PRIMARY KEY (guild_id, telegram_id),
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_contributions (
                contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK (amount > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reason TEXT NOT NULL DEFAULT 'contribution',
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_inventory (
                guild_id INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0 CHECK (amount >= 0),
                PRIMARY KEY (guild_id, resource_id),
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                telegram_id INTEGER,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_daily_xp (
                guild_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                activity_date TEXT NOT NULL,
                xp_awarded INTEGER NOT NULL DEFAULT 0 CHECK (xp_awarded >= 0),
                PRIMARY KEY (guild_id, telegram_id, activity_date),
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_missions (
                mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                target_amount INTEGER NOT NULL CHECK (target_amount > 0),
                progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed')),
                reward_xp INTEGER NOT NULL DEFAULT 50 CHECK (reward_xp >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_guild_members_guild ON guild_members (guild_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_location ON artifacts (location_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_case_openings_player ON case_openings (telegram_id, opened_at)")
        for location_id, location in LOCATIONS.items():
            connection.execute(
                """
                INSERT OR IGNORE INTO locations
                    (location_id, name, description, required_ship_level,
                     required_hero_level, fuel_cost, energy_cost, required_engine,
                     required_scanner, required_story_flag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (location_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    required_ship_level = excluded.required_ship_level,
                    required_hero_level = excluded.required_hero_level,
                    fuel_cost = excluded.fuel_cost,
                    energy_cost = excluded.energy_cost,
                    required_engine = excluded.required_engine,
                    required_scanner = excluded.required_scanner,
                    required_story_flag = excluded.required_story_flag
                """,
                (
                    location_id,
                    location.name,
                    location.description,
                    location.required_ship_level,
                    location.required_hero_level,
                    location.fuel_cost,
                    location.energy_cost,
                    location.required_engine,
                    location.required_scanner,
                    location.story_flag,
                ),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO collections
                    (collection_id, location_id, reward_orbitals)
                VALUES (?, ?, ?)
                ON CONFLICT (collection_id) DO UPDATE SET
                    reward_orbitals = excluded.reward_orbitals
                """,
                (
                    f"collection_{location_id}",
                    location_id,
                    min(25, 5 + location.required_ship_level * 2),
                ),
            )
            for index in range(1, 6):
                artifact_id = f"{location_id}_artifact_{index}"
                artifact_names = ARTIFACT_NAMES.get(location_id, ())
                artifact_name = (
                    artifact_names[index - 1]
                    if len(artifact_names) >= index
                    else f"Фрагмент {index}: {location.name}"
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO artifacts
                        (artifact_id, location_id, name, description, rarity, discovery_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (artifact_id) DO UPDATE SET
                        location_id = excluded.location_id,
                        name = excluded.name,
                        description = excluded.description,
                        rarity = excluded.rarity,
                        discovery_method = excluded.discovery_method
                    """,
                    (
                        artifact_id,
                        location_id,
                        artifact_name,
                        f"Запись экспедиции: {artifact_name} обнаружен в локации «{location.name}».",
                        "обычный" if index <= 3 else "редкий",
                        "сканирование",
                    ),
                )
        for achievement_id, description in (
            ("first_scan", "Впервые просканировать небесное тело."),
            ("first_artifact", "Найти первый артефакт."),
            ("first_guild", "Создать или найти гильдию."),
        ):
            connection.execute(
                """
                INSERT INTO achievements (achievement_id, description) VALUES (?, ?)
                ON CONFLICT (achievement_id) DO UPDATE SET description = excluded.description
                """,
                (achievement_id, description),
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orbital_payments (
                charge_id TEXT PRIMARY KEY,
                telegram_id INTEGER NOT NULL,
                package_id TEXT NOT NULL,
                stars INTEGER NOT NULL CHECK (stars > 0),
                orbitals INTEGER NOT NULL CHECK (orbitals > 0),
                referral_bonus INTEGER NOT NULL DEFAULT 0 CHECK (referral_bonus >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
            )
            """
        )
        payment_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(orbital_payments)").fetchall()
        }
        if "referral_bonus" not in payment_columns:
            connection.execute(
                """
                ALTER TABLE orbital_payments
                ADD COLUMN referral_bonus INTEGER NOT NULL DEFAULT 0
                """
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                invitee_id INTEGER PRIMARY KEY,
                inviter_id INTEGER NOT NULL,
                reward_orbitals INTEGER NOT NULL CHECK (reward_orbitals > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (invitee_id != inviter_id),
                FOREIGN KEY (invitee_id) REFERENCES players (telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (inviter_id) REFERENCES players (telegram_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals (inviter_id)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS planet_visits (
                telegram_id INTEGER NOT NULL,
                planet_id TEXT NOT NULL,
                PRIMARY KEY (telegram_id, planet_id),
                FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO planet_visits (telegram_id, planet_id)
            SELECT telegram_id, location FROM players
            """
        )


# Регистрация и чтение сохранённого состояния игрока.
def ensure_player(
    telegram_id: int,
    username: str | None = None,
    display_name: str | None = None,
) -> bool:
    with database() as connection:
        player = connection.execute(
            """
            INSERT OR IGNORE INTO players
                (telegram_id, username, display_name, registered_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (telegram_id, username, display_name),
        )
        is_new_player = player.rowcount == 1
        if is_new_player:
            connection.execute(
                """
                INSERT OR IGNORE INTO planet_visits (telegram_id, planet_id)
                VALUES (?, 'earth_orbit')
                """,
                (telegram_id,),
            )
        connection.execute(
            "INSERT OR IGNORE INTO ships (telegram_id) VALUES (?)",
            (telegram_id,),
        )
        for resource_id in RESOURCES:
            connection.execute(
                """
                INSERT OR IGNORE INTO inventory (telegram_id, resource_id)
                VALUES (?, ?)
                """,
                (telegram_id, resource_id),
            )
        if is_new_player:
            for resource_id, amount in SHIP["starting_resources"].items():
                connection.execute(
                    """
                    UPDATE inventory SET amount = ?
                    WHERE telegram_id = ? AND resource_id = ?
                    """,
                    (amount, telegram_id, resource_id),
                )
            connection.execute(
                """
                INSERT OR IGNORE INTO missions (telegram_id, mission_id, status)
                VALUES (?, 'pioneer_signal', 'active')
                """,
                (telegram_id,),
            )
        elif username is not None or display_name is not None:
            connection.execute(
                """
                UPDATE players
                SET username = COALESCE(?, username),
                    display_name = COALESCE(?, display_name)
                WHERE telegram_id = ?
                """,
                (username, display_name, telegram_id),
            )
    return is_new_player


def get_player(telegram_id: int) -> Player:
    with database() as connection:
        player = connection.execute(
            """
            SELECT p.telegram_id, p.username, p.display_name, p.nickname, p.registered_at,
                   p.story_stage, p.hero_level, p.hero_xp, p.credits, p.orbitals,
                   p.location, p.panel_chat_id, p.panel_message_id,
                   COALESCE((
                       SELECT c.prefix
                       FROM equipped_nickname_cosmetics e
                       JOIN player_nickname_cosmetics pc
                           ON pc.telegram_id = e.telegram_id AND pc.cosmetic_id = e.cosmetic_id
                       JOIN nickname_cosmetics c ON c.cosmetic_id = e.cosmetic_id
                       WHERE e.telegram_id = p.telegram_id
                   ), '') AS nickname_prefix,
                   COALESCE((
                       SELECT c.suffix
                       FROM equipped_nickname_cosmetics e
                       JOIN player_nickname_cosmetics pc
                           ON pc.telegram_id = e.telegram_id AND pc.cosmetic_id = e.cosmetic_id
                       JOIN nickname_cosmetics c ON c.cosmetic_id = e.cosmetic_id
                       WHERE e.telegram_id = p.telegram_id
                   ), '') AS nickname_suffix,
                   s.ship_level, s.ship_xp, s.fuel, s.hull, s.energy,
                   s.engine_level, s.scanner_level, s.cargo_level, s.protection_level,
                   s.energy_level,
                   COALESCE((SELECT amount FROM inventory i WHERE i.telegram_id = p.telegram_id AND i.resource_id = 'scrap'), p.iron_ore) AS iron_ore,
                   COALESCE((SELECT amount FROM inventory i WHERE i.telegram_id = p.telegram_id AND i.resource_id = 'nebulite'), p.crystals) AS crystals,
                   COALESCE((SELECT amount FROM inventory i WHERE i.telegram_id = p.telegram_id AND i.resource_id = 'data'), p.science_data) AS science_data
            FROM players p
            JOIN ships s ON s.telegram_id = p.telegram_id
            WHERE p.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
    if player is None:
        raise LookupError(f"Игрок {telegram_id} не найден")
    return {
        "telegram_id": int(player["telegram_id"]),
        "username": player["username"],
        "display_name": player["display_name"],
        "nickname": player["nickname"],
        "nickname_prefix": str(player["nickname_prefix"]),
        "nickname_suffix": str(player["nickname_suffix"]),
        "registered_at": str(player["registered_at"]),
        "story_stage": str(player["story_stage"]),
        "hero_level": int(player["hero_level"]),
        "hero_xp": int(player["hero_xp"]),
        "credits": int(player["credits"]),
        "orbitals": int(player["orbitals"]),
        "fuel": int(player["fuel"]),
        "location": str(player["location"]),
        "ship_level": int(player["ship_level"]),
        "ship_xp": int(player["ship_xp"]),
        "hull": int(player["hull"]),
        "energy": int(player["energy"]),
        "engine_level": int(player["engine_level"]),
        "scanner_level": int(player["scanner_level"]),
        "cargo_level": int(player["cargo_level"]),
        "protection_level": int(player["protection_level"]),
        "energy_level": int(player["energy_level"]),
        "iron_ore": int(player["iron_ore"]),
        "crystals": int(player["crystals"]),
        "science_data": int(player["science_data"]),
        "panel_chat_id": (
            int(player["panel_chat_id"])
            if player["panel_chat_id"] is not None
            else None
        ),
        "panel_message_id": (
            int(player["panel_message_id"])
            if player["panel_message_id"] is not None
            else None
        ),
    }


def list_players(limit: int = 100, offset: int = 0) -> list[Player]:
    if limit < 1 or offset < 0:
        raise ValueError("limit должен быть положительным, offset — неотрицательным")
    with database() as connection:
        player_ids = connection.execute(
            """
            SELECT telegram_id
            FROM players
            ORDER BY registered_at, telegram_id
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return [get_player(int(row["telegram_id"])) for row in player_ids]


def get_inventory(telegram_id: int) -> dict[str, int]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT resource_id, amount FROM inventory
            WHERE telegram_id = ?
            ORDER BY resource_id
            """,
            (telegram_id,),
        ).fetchall()
    return {str(row["resource_id"]): int(row["amount"]) for row in rows}


def get_story_flags(telegram_id: int) -> dict[str, str]:
    with database() as connection:
        rows = connection.execute(
            "SELECT flag_id, value FROM story_flags WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchall()
    return {str(row["flag_id"]): str(row["value"]) for row in rows}


def get_discoveries(telegram_id: int) -> list[dict[str, str]]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT discovery_id, discovered_at
            FROM discoveries
            WHERE telegram_id = ?
            ORDER BY discovered_at DESC
            """,
            (telegram_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_missions(telegram_id: int) -> list[dict[str, str | None]]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT mission_id, status, started_at, completed_at
            FROM missions WHERE telegram_id = ?
            ORDER BY started_at, mission_id
            """,
            (telegram_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_guild(telegram_id: int) -> Guild | None:
    with database() as connection:
        row = connection.execute(
            """
            SELECT g.guild_id, g.name, g.description, g.leader_id, g.level,
                   g.xp, g.total_contribution, g.created_at, g.join_mode,
                   m.role, m.contribution_total
            FROM guild_members m
            JOIN guilds g ON g.guild_id = m.guild_id
            WHERE m.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "guild_id": int(row["guild_id"]),
        "name": str(row["name"]),
        "description": str(row["description"]),
        "leader_id": int(row["leader_id"]),
        "level": int(row["level"]),
        "xp": int(row["xp"]),
        "total_contribution": int(row["total_contribution"]),
        "created_at": str(row["created_at"]),
        "join_mode": str(row["join_mode"]),
        "role": str(row["role"]),
        "contribution_total": int(row["contribution_total"]),
    }


def get_guild_members(guild_id: int) -> list[dict[str, int | str | None]]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT m.telegram_id, p.nickname, m.role, m.joined_at,
                   m.contribution_total, c.prefix AS nickname_prefix,
                   c.suffix AS nickname_suffix
            FROM guild_members m
            JOIN players p ON p.telegram_id = m.telegram_id
            LEFT JOIN equipped_nickname_cosmetics e
                ON e.telegram_id = m.telegram_id
            LEFT JOIN nickname_cosmetics c ON c.cosmetic_id = e.cosmetic_id
            WHERE m.guild_id = ?
            ORDER BY CASE m.role WHEN 'leader' THEN 0 WHEN 'officer' THEN 1 ELSE 2 END,
                     m.joined_at
            """,
            (guild_id,),
        ).fetchall()
    return [dict(row) for row in rows]


# Данные интерфейса и косметические настройки игрового профиля.
def save_panel(telegram_id: int, chat_id: int, message_id: int) -> None:
    ensure_player(telegram_id)
    with database() as connection:
        connection.execute(
            """
            UPDATE players
            SET panel_chat_id = ?, panel_message_id = ?
            WHERE telegram_id = ?
            """,
            (chat_id, message_id, telegram_id),
        )


def set_nickname(telegram_id: int, nickname: str) -> None:
    with database() as connection:
        updated = connection.execute(
            "UPDATE players SET nickname = ? WHERE telegram_id = ?",
            (nickname, telegram_id),
        )
        if updated.rowcount == 0:
            raise LookupError(f"Игрок {telegram_id} не найден")


def get_nickname_cosmetics(telegram_id: int) -> list[dict[str, int | str]]:
    with database() as connection:
        rows = connection.execute(
            """
            SELECT c.cosmetic_id, c.name, c.rarity, c.prefix, c.suffix,
                   CASE WHEN e.cosmetic_id IS NULL THEN 0 ELSE 1 END AS equipped
            FROM player_nickname_cosmetics pc
            JOIN nickname_cosmetics c ON c.cosmetic_id = pc.cosmetic_id
            LEFT JOIN equipped_nickname_cosmetics e
                ON e.telegram_id = pc.telegram_id AND e.cosmetic_id = pc.cosmetic_id
            WHERE pc.telegram_id = ?
            ORDER BY c.rarity, c.name
            """,
            (telegram_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def equip_nickname_cosmetic(telegram_id: int, cosmetic_id: str | None) -> None:
    with database() as connection:
        if cosmetic_id is None:
            connection.execute(
                "DELETE FROM equipped_nickname_cosmetics WHERE telegram_id = ?",
                (telegram_id,),
            )
            return
        owned = connection.execute(
            """
            SELECT 1 FROM player_nickname_cosmetics
            WHERE telegram_id = ? AND cosmetic_id = ?
            """,
            (telegram_id, cosmetic_id),
        ).fetchone()
        if owned is None:
            raise LookupError("У игрока нет такого оформления ника")
        connection.execute(
            """
            INSERT INTO equipped_nickname_cosmetics (telegram_id, cosmetic_id)
            VALUES (?, ?)
            ON CONFLICT (telegram_id) DO UPDATE SET cosmetic_id = excluded.cosmetic_id
            """,
            (telegram_id, cosmetic_id),
        )


def get_referral_stats(telegram_id: int) -> dict[str, int]:
    """Возвращает число приглашённых друзей и бонусы с приглашений/покупок."""
    with database() as connection:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM referrals WHERE inviter_id = ?) AS friends,
                (SELECT COALESCE(SUM(reward_orbitals), 0)
                 FROM referrals WHERE inviter_id = ?) AS invite_rewards,
                (SELECT COALESCE(SUM(p.referral_bonus), 0)
                 FROM orbital_payments p
                 JOIN referrals r ON r.invitee_id = p.telegram_id
                 WHERE r.inviter_id = ?) AS topup_bonus
            """,
            (telegram_id, telegram_id, telegram_id),
        ).fetchone()
    return {
        "friends": int(row["friends"]),
        "invite_rewards": int(row["invite_rewards"]),
        "topup_bonus": int(row["topup_bonus"]),
    }
