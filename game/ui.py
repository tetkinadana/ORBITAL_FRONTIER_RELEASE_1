"""Переиспользуемые элементы текстового интерфейса Telegram."""

from html import escape


RARITY_MARKERS = {
    "Обычный": "▫️",
    "Редкий": "🔹",
    "Эпический": "🟣",
    "Уникальный": "🟣",
    "Легендарный": "🟨",
    "Квантовый": "🟨",
    "Мифический": "🟨",
    "обычный": "▫️",
    "необычный": "🔹",
    "редкий": "🔹",
    "эпический": "🟣",
}


def progress_bar(current: int, maximum: int, width: int = 10) -> str:
    """Рисует компактный индикатор только для реальных числовых значений."""
    if maximum <= 0 or width <= 0:
        raise ValueError("maximum и width должны быть положительными")
    bounded = min(max(current, 0), maximum)
    filled = bounded * width // maximum
    percent = bounded * 100 // maximum
    return f"{'▰' * filled}{'▱' * (width - filled)} {percent}%"


def rarity_label(rarity: str) -> str:
    """Возвращает единообразный маркер редкости и её название."""
    marker = RARITY_MARKERS.get(rarity, "▫️")
    return f"{marker} {rarity}"


def plain_screen(text: str) -> str:
    """Очищает лишние разделители и пустые строки для компактного экрана."""
    lines: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned and set(cleaned) <= {"━", "─", "—"}:
            continue
        if not cleaned and (not lines or not lines[-1]):
            continue
        lines.append(cleaned)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def format_screen(text: str) -> str:
    """Выделяет заголовок и безопасно экранирует весь текст для Telegram HTML."""
    plain = plain_screen(text)
    lines = plain.splitlines()
    if not lines:
        return ""
    lines[0] = f"<b>{escape(lines[0], quote=False)}</b>"
    return "\n".join([lines[0], *(escape(line, quote=False) for line in lines[1:])])
