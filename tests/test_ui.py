import unittest

from game.ui import format_screen, plain_screen, progress_bar, rarity_label


class UiTests(unittest.TestCase):
    def test_progress_bar_uses_clamped_real_values(self) -> None:
        self.assertEqual(progress_bar(72, 100, 10), "▰▰▰▰▰▰▰▱▱▱ 72%")
        self.assertEqual(progress_bar(120, 100, 10), "▰▰▰▰▰▰▰▰▰▰ 100%")
        self.assertEqual(progress_bar(-5, 100, 10), "▱▱▱▱▱▱▱▱▱▱ 0%")
        with self.assertRaises(ValueError):
            progress_bar(1, 0)

    def test_rarity_labels_have_consistent_semantic_markers(self) -> None:
        self.assertEqual(rarity_label("Редкий"), "🔹 Редкий")
        self.assertEqual(rarity_label("Легендарный"), "🟨 Легендарный")
        self.assertEqual(rarity_label("Unknown"), "▫️ Unknown")

    def test_screen_formatter_compacts_and_escapes_user_text(self) -> None:
        raw = "ЭКРАН\n━━━━━━━━━━━━\n\nПилот <командир> & команда"

        self.assertEqual(plain_screen(raw), "ЭКРАН\n\nПилот <командир> & команда")
        self.assertEqual(
            format_screen(raw),
            "<b>ЭКРАН</b>\n\nПилот &lt;командир&gt; &amp; команда",
        )


if __name__ == "__main__":
    unittest.main()
