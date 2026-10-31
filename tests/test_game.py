import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game import database as db
from game import engine
from game.config import (
    CASES,
    EQUIPMENT_RARITY_CHANCES,
    NICKNAME_COSMETIC_RARITY_CHANCES,
    QUANTUM_MATRIX_RECIPE,
)


class FixedRandom(random.Random):
    def __init__(self) -> None:
        self.random_values = iter((0.99, 0.0, 0.0))

    def random(self) -> float:
        return next(self.random_values)

    def choice(self, values: list[str]) -> str:
        return values[0]

    def randint(self, lower: int, upper: int) -> int:
        return min(lower, upper)


class NoArtifactRandom(random.Random):
    def random(self) -> float:
        return 0.99

    def choice(self, values: list[str]) -> str:
        return values[0]

    def randint(self, lower: int, upper: int) -> int:
        return min(lower, upper)


class FixedCaseRandom(random.Random):
    def choices(self, population, **kwargs):
        weights = kwargs.get("weights")
        cum_weights = kwargs.get("cum_weights")
        if weights is not None:
            self.assert_weights_match(population, weights)
        if cum_weights is not None:
            self.assert_weights_match(population, cum_weights)
        k = kwargs.get("k", 1)
        return [population[0] for _ in range(k)]

    @staticmethod
    def assert_weights_match(population, weights) -> None:
        if len(population) != len(weights):
            raise ValueError("weights must match population length")


class FirstCosmeticRandom(random.Random):
    def choices(self, population, **kwargs):
        k = kwargs.get("k", 1)
        return [population[0] for _ in range(k)]

    def choice(self, sequence):
        return sequence[0]


class QuantumArtifactRandom(FixedRandom):
    def choices(self, population, **kwargs):
        k = kwargs.get("k", 1)
        return [population[-1] for _ in range(k)]


class GameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.database_patcher = patch.object(db, "DATABASE_PATH", self.database_path)
        self.database_patcher.start()
        db.initialize_database()
        db.ensure_player(101, "pilot", "Test Pilot")

    def tearDown(self) -> None:
        self.database_patcher.stop()
        self.temp_dir.cleanup()

    def test_registration_is_idempotent_and_initializes_private_game_data(self) -> None:
        db.ensure_player(101, "pilot", "Test Pilot")

        player = db.get_player(101)
        self.assertEqual(player["location"], "earth_orbit")
        self.assertEqual(player["credits"], 500)
        self.assertEqual(db.get_inventory(101)["scrap"], 5)
        self.assertEqual(db.get_inventory(101)["electronics"], 2)
        self.assertEqual(len(db.list_players()), 1)

    def test_initialization_refreshes_static_planet_and_artifact_catalog(self) -> None:
        with db.database() as connection:
            connection.execute(
                """
                UPDATE artifacts SET name = 'Старое название'
                WHERE artifact_id = 'moon_artifact_1'
                """
            )

        db.initialize_database()

        artifact = engine.collection_artifacts(101, "moon")[0]
        self.assertEqual(artifact["name"], "Лунный навигационный диск")
        self.assertIn("mercury", engine.LOCATIONS)
        with db.database() as connection:
            reward = connection.execute(
                "SELECT reward_orbitals FROM collections WHERE collection_id = 'collection_mars'"
            ).fetchone()["reward_orbitals"]
        self.assertEqual(reward, 9)

    def test_legacy_player_progress_and_resources_survive_migration(self) -> None:
        legacy_path = Path(self.temp_dir.name) / "legacy.db"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.execute(
                """
                CREATE TABLE players (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    credits INTEGER NOT NULL,
                    orbitals INTEGER NOT NULL,
                    fuel INTEGER NOT NULL,
                    location TEXT NOT NULL,
                    ship_level INTEGER NOT NULL,
                    iron_ore INTEGER NOT NULL,
                    crystals INTEGER NOT NULL,
                    science_data INTEGER NOT NULL,
                    panel_chat_id INTEGER,
                    panel_message_id INTEGER
                )
                """
            )
            connection.execute(
                """
                INSERT INTO players VALUES
                    (303, 'legacy', 1250, 7, 45, 'mars', 2, 8, 3, 11, NULL, NULL)
                """
            )
            connection.commit()
        finally:
            connection.close()

        with patch.object(db, "DATABASE_PATH", legacy_path):
            db.initialize_database()
            player = db.get_player(303)
            inventory = db.get_inventory(303)

        self.assertEqual(player["location"], "earth_orbit")
        self.assertEqual(player["credits"], 1250)
        self.assertEqual(player["orbitals"], 7)
        self.assertEqual(player["ship_level"], 3)
        self.assertEqual(player["fuel"], 45)
        self.assertEqual(inventory["scrap"], 8)
        self.assertEqual(inventory["nebulite"], 3)
        self.assertEqual(inventory["data"], 11)

    def test_travel_home_requires_an_existing_player(self) -> None:
        with self.assertRaises(engine.GameError):
            engine.travel(999, "earth_orbit")

    def test_signal_unlocks_moon_and_travel_spends_fuel(self) -> None:
        with self.assertRaises(engine.GameError):
            engine.travel(101, "moon")

        engine.upgrade_module(101, "engine")
        engine.story_action(101, "signal")
        self.assertEqual(engine.route_requirements(101, "moon"), [])

        trip, _ = engine.travel(101, "moon")
        self.assertEqual(trip["fuel_spent"], 30)
        self.assertEqual(db.get_player(101)["fuel"], 70)

    def test_advanced_upgrade_requirements_are_checked_before_spending(self) -> None:
        with db.database() as connection:
            connection.execute(
                "UPDATE players SET credits = 2000 WHERE telegram_id = 101"
            )
            connection.execute(
                "UPDATE inventory SET amount = 10 WHERE telegram_id = 101 AND resource_id = 'electronics'"
            )
            connection.execute(
                "UPDATE inventory SET amount = 10 WHERE telegram_id = 101 AND resource_id = 'plasma_threads'"
            )
        engine.upgrade_module(101, "engine")
        engine.upgrade_module(101, "engine")

        with db.database() as connection:
            connection.execute(
                "UPDATE inventory SET amount = 0 WHERE telegram_id = 101 AND resource_id = 'plasma_threads'"
            )
        credits_before = db.get_player(101)["credits"]
        with self.assertRaises(engine.GameError):
            engine.upgrade_module(101, "engine")
        self.assertEqual(db.get_player(101)["credits"], credits_before)

        with db.database() as connection:
            connection.execute(
                "UPDATE inventory SET amount = 1 WHERE telegram_id = 101 AND resource_id = 'plasma_threads'"
            )
        result = engine.upgrade_module(101, "engine")
        self.assertEqual(result["level"], 3)
        self.assertEqual(db.get_inventory(101)["plasma_threads"], 0)

    def test_exploration_handles_full_cargo_and_unlocks_next_story_route(self) -> None:
        with db.database() as connection:
            connection.execute(
                "UPDATE players SET location = 'mars' WHERE telegram_id = 101"
            )
            connection.execute(
                "UPDATE inventory SET amount = 19 WHERE telegram_id = 101 AND resource_id = 'scrap'"
            )
            connection.execute(
                "UPDATE inventory SET amount = 0 WHERE telegram_id = 101 AND resource_id != 'scrap'"
            )

        outcome = engine.explore(101, FixedRandom())

        self.assertTrue(outcome["artifact"])
        self.assertTrue(outcome["story_unlock"])
        self.assertEqual(db.get_story_flags(101)["mars_archive"], "1")
        self.assertEqual(sum(db.get_inventory(101).values()), 20)
        requirements = engine.route_requirements(101, "phobos")
        self.assertIn("корабль уровня 4", requirements)
        self.assertNotIn("завершить необходимый сюжетный этап", requirements)

    def test_moon_decision_does_not_block_future_exploration(self) -> None:
        with db.database() as connection:
            connection.execute(
                """
                INSERT INTO story_flags (telegram_id, flag_id, value)
                VALUES (101, 'moon_choice', 'analyze')
                """
            )

        outcome = engine.explore(101, NoArtifactRandom())

        self.assertEqual(outcome["location"], "Орбита Земли")

    def test_case_purchase_is_atomic_when_cargo_is_full(self) -> None:
        with db.database() as connection:
            connection.execute(
                "UPDATE players SET orbitals = 20 WHERE telegram_id = 101"
            )
            connection.execute(
                "UPDATE inventory SET amount = 18 WHERE telegram_id = 101 AND resource_id = 'scrap'"
            )
            connection.execute(
                "UPDATE inventory SET amount = 0 WHERE telegram_id = 101 AND resource_id != 'scrap'"
            )

        with self.assertRaises(engine.GameError):
            engine.open_case(101, FixedCaseRandom())
        self.assertEqual(db.get_player(101)["orbitals"], 20)

    def test_equipment_and_nickname_cosmetic_rarity_tables_are_separate_and_total_100(self) -> None:
        self.assertEqual(sum(weight for _, weight in EQUIPMENT_RARITY_CHANCES), 10000)
        self.assertEqual(sum(weight for _, weight in NICKNAME_COSMETIC_RARITY_CHANCES), 10000)
        self.assertEqual(len(CASES), 7)
        for case_id, case in CASES.items():
            if case_id != "neon_singularity":
                self.assertEqual(sum(weight for _, _, _, weight in case.rewards), 10000)
        self.assertEqual(
            CASES["neon_singularity"].name,
            "Неон-сингулярность",
        )
        self.assertEqual(
            dict(EQUIPMENT_RARITY_CHANCES)["Квантовый"],
            30,
        )
        self.assertEqual(
            dict(NICKNAME_COSMETIC_RARITY_CHANCES)["Мифический"],
            100,
        )

    def test_neon_case_awards_and_equips_private_nickname_cosmetic(self) -> None:
        with db.database() as connection:
            connection.execute(
                "UPDATE players SET orbitals = 500 WHERE telegram_id = 101"
            )
            connection.execute(
                "UPDATE players SET display_name = 'Real Name' WHERE telegram_id = 101"
            )

        reward = engine.open_case(
            101,
            FirstCosmeticRandom(),
            case_id="neon_singularity",
        )
        self.assertTrue(reward["cosmetic"])
        self.assertEqual(reward["rarity"], "Обычный")
        self.assertEqual(len(db.get_nickname_cosmetics(101)), 1)

        engine.set_nickname(101, "Космический пилот")
        engine.equip_nickname_cosmetic(101, reward["reward_id"])
        player = db.get_player(101)
        self.assertEqual(player["nickname"], "Космический пилот")
        self.assertTrue(player["nickname_prefix"])
        self.assertNotEqual(player["nickname"], player["display_name"])

        duplicate = engine.open_case(
            101,
            FirstCosmeticRandom(),
            case_id="neon_singularity",
        )
        self.assertTrue(duplicate["duplicate"])
        self.assertIn("дубликат", duplicate["name"])

    def test_nickname_validation_rejects_empty_or_oversized_names(self) -> None:
        self.assertEqual(engine.set_nickname(101, "  Star   Pilot "), "Star Pilot")
        with self.assertRaises(engine.GameError):
            engine.set_nickname(101, "ab")
        with self.assertRaises(engine.GameError):
            engine.set_nickname(101, "x" * 21)

    def test_quantum_matrix_can_be_crafted_without_unlocking_planets_or_story(self) -> None:
        with db.database() as connection:
            connection.execute(
                "UPDATE players SET credits = 1000 WHERE telegram_id = 101"
            )
            for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items():
                if resource_id != "credits":
                    connection.execute(
                        """
                        UPDATE inventory SET amount = amount + ?
                        WHERE telegram_id = 101 AND resource_id = ?
                        """,
                        (quantity, resource_id),
                    )

        with self.assertRaisesRegex(engine.GameError, "исследуй чертёж"):
            engine.craft_quantum_matrix(101)

        status = engine.quantum_matrix_lab_status(101)
        self.assertTrue(status["materials_ready"])
        self.assertFalse(status["researched"])

        engine.research_quantum_matrix(101)
        status = engine.quantum_matrix_lab_status(101)
        self.assertTrue(status["researched"])
        self.assertTrue(status["materials_ready"])
        engine.craft_quantum_matrix(101)

        self.assertEqual(db.get_inventory(101)["quantum_matrices"], 1)
        requirements = engine.route_requirements(101, "pluto")
        self.assertIn("завершить необходимый сюжетный этап", requirements)
        self.assertEqual(db.get_story_flags(101), {})

    def test_lab_research_requires_all_recipe_materials_and_keeps_them(self) -> None:
        with db.database() as connection:
            connection.execute(
                "UPDATE players SET credits = ? WHERE telegram_id = 101",
                (QUANTUM_MATRIX_RECIPE["credits"],),
            )

        with self.assertRaisesRegex(engine.GameError, "не хватает ресурса"):
            engine.research_quantum_matrix(101)

        self.assertFalse(engine.quantum_matrix_lab_status(101)["researched"])

        with db.database() as connection:
            connection.execute(
                "UPDATE players SET credits = ? WHERE telegram_id = 101",
                (QUANTUM_MATRIX_RECIPE["credits"],),
            )
            for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items():
                if resource_id != "credits":
                    connection.execute(
                        """
                        UPDATE inventory SET amount = ?
                        WHERE telegram_id = 101 AND resource_id = ?
                        """,
                        (quantity, resource_id),
                    )

        engine.research_quantum_matrix(101)

        self.assertTrue(engine.quantum_matrix_lab_status(101)["researched"])
        self.assertEqual(db.get_player(101)["credits"], QUANTUM_MATRIX_RECIPE["credits"])
        for resource_id, quantity in QUANTUM_MATRIX_RECIPE.items():
            if resource_id != "credits":
                self.assertEqual(db.get_inventory(101)[resource_id], quantity)

    def test_referrals_reward_inviter_and_limit_referrals_to_twenty(self) -> None:
        db.ensure_player(202)
        db.ensure_player(203)

        self.assertEqual(engine.register_referral(202, 9999), 0)
        self.assertEqual(engine.register_referral(202, 101), 20)
        self.assertEqual(engine.register_referral(202, 203), 0)
        self.assertEqual(db.get_player(101)["orbitals"], 20)

        self.assertEqual(engine.register_referral(203, 101), 5)
        self.assertEqual(db.get_player(101)["orbitals"], 25)
        self.assertEqual(db.get_referral_stats(101)["friends"], 2)

        for invitee_id in range(300, 318):
            db.ensure_player(invitee_id)
            self.assertEqual(engine.register_referral(invitee_id, 101), 5)
        db.ensure_player(318)
        self.assertEqual(engine.register_referral(318, 101), 0)
        self.assertEqual(db.get_referral_stats(101)["friends"], 20)

    def test_orbital_purchase_credits_referral_bonus_only_once(self) -> None:
        db.ensure_player(202)
        self.assertEqual(engine.register_referral(202, 101), 20)

        first = engine.record_orbital_purchase(202, "starter", 25, "charge-1")
        repeated = engine.record_orbital_purchase(202, "starter", 25, "charge-1")

        self.assertEqual(first, {"orbitals": 50, "referral_bonus": 2, "duplicate": False})
        self.assertEqual(repeated, {"orbitals": 50, "referral_bonus": 2, "duplicate": True})
        self.assertEqual(db.get_player(202)["orbitals"], 50)
        self.assertEqual(db.get_player(101)["orbitals"], 22)
        self.assertEqual(db.get_referral_stats(101)["topup_bonus"], 2)

    def test_orbital_purchase_rejects_mismatched_stars_amount(self) -> None:
        with self.assertRaisesRegex(engine.GameError, "не совпадает"):
            engine.record_orbital_purchase(101, "starter", 1, "invalid-charge")

    def test_quantum_artifact_rarity_does_not_bypass_story_route_requirements(self) -> None:
        outcome = engine.explore(101, QuantumArtifactRandom())

        self.assertEqual(outcome["artifact"]["rarity"], "Квантовый")
        self.assertEqual(db.get_story_flags(101), {})
        self.assertIn("завершить необходимый сюжетный этап", engine.route_requirements(101, "moon"))

    def test_guild_join_and_contribution_update_shared_progress(self) -> None:
        db.ensure_player(202, "member", "Second Pilot")
        guild_id = engine.create_guild(101, "Звёздный путь")
        engine.join_guild(202, guild_id)

        result = engine.contribute_to_guild(202, "scrap", 2)

        self.assertEqual(result["guild_id"], guild_id)
        self.assertEqual(result["xp_gained"], 2)
        self.assertEqual(db.get_inventory(202)["scrap"], 3)
        self.assertEqual(engine.guild_inventory(guild_id)["scrap"], 2)
        member = db.get_guild_members(guild_id)[1]
        self.assertNotIn("username", member)
        self.assertNotIn("display_name", member)


if __name__ == "__main__":
    unittest.main()
