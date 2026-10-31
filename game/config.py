"""Настройки и справочники игры.

Чтобы менять баланс или игровой контент, начните с этого файла:
ресурсы и локации описаны в начале, затем идут параметры корабля и уровней,
кейсы, вероятности редкости, косметика ника, крафт и настройки гильдий.
"""

from dataclasses import dataclass


DATABASE_TIMEOUT_SECONDS = 30


# Каталог ресурсов: имя, описание, редкость, значок и назначение.
@dataclass(frozen=True)
class Resource:
    name: str
    description: str
    rarity: str
    icon: str
    uses: str


RESOURCES: dict[str, Resource] = {
    "fuel": Resource("Топливо", "Запас для межпланетных перелётов.", "обычный", "⛽", "перелёты"),
    "scrap": Resource("Металлолом", "Обломки для ремонта и базовых модулей.", "обычный", "🔩", "ремонт корпуса, улучшения"),
    "ice": Resource("Лёд", "Лёд из теневых кратеров.", "обычный", "🧊", "задания и будущая переработка"),
    "electronics": Resource("Электронные компоненты", "Исправные детали старых зондов.", "необычный", "🔌", "двигатель и сканер"),
    "data": Resource("Научные данные", "Записи сканирования и исследований.", "необычный", "🔬", "сюжет и задания"),
    "asterium": Resource("Астерий", "Редкий сплав из метеоритных обломков.", "редкий", "🪨", "усиление корпуса"),
    "nebulite": Resource("Небулит", "Кристалл из облаков и аномальных зон.", "редкий", "💎", "улучшение сканера"),
    "ion_gel": Resource("Ионный гель", "Энергоёмкое вещество ледяных миров.", "необычный", "🧪", "энергомодуль"),
    "xenoquartz": Resource("Ксенокварц", "Неизвестный кристалл рядом с артефактами.", "редкий", "🔷", "анализ артефактов"),
    "phase_dust": Resource("Фазовая пыль", "Микрочастицы нестабильных аномалий.", "редкий", "✨", "защитный модуль"),
    "plasma_threads": Resource("Плазменные нити", "Следы высокоэнергетических выбросов.", "редкий", "🧵", "улучшение двигателя"),
    "biosilicate": Resource("Биосиликат", "Органоминеральный внеземной образец.", "необычный", "🧬", "исследовательские задания"),
    "graviton_cores": Resource("Гравитонные ядра", "Плотные объекты из опасных зон.", "эпический", "⚛️", "дальние маршруты"),
    "echo_shards": Resource("Эхо-осколки", "Фрагменты передатчика с остаточными сигналами.", "редкий", "📡", "сюжетные записи"),
    "quantum_matrices": Resource("Квантовые матрицы", "Технологические блоки поздних экспедиций.", "эпический", "🧩", "продвинутые модули и проекты"),
}


# Локации, доступные на карте; требования используются для проверки перелёта.
@dataclass(frozen=True)
class Location:
    name: str
    description: str
    required_ship_level: int
    required_hero_level: int
    required_engine: int
    required_scanner: int
    fuel_cost: int
    energy_cost: int
    resources: tuple[str, ...]
    story_flag: str | None = None
    hazard_chance: float = 0.0


LOCATIONS: dict[str, Location] = {
    "earth_orbit": Location("Орбита Земли", "Безопасная станция для подготовки, ремонта и новых заданий.", 1, 1, 0, 0, 0, 5, ("scrap", "electronics", "data")),
    "moon": Location("Луна", "Тихие кратеры, следы автоматических зондов и неизвестный передатчик.", 1, 1, 1, 0, 30, 10, ("scrap", "ice", "electronics", "data", "ion_gel", "echo_shards"), "signal_coordinates", 0.05),
    "mercury": Location("Меркурий", "Обожжённая Солнцем планета с кратерами и залежами металлов.", 2, 2, 1, 0, 35, 12, ("scrap", "asterium", "electronics", "data"), None, 0.12),
    "venus": Location("Венера", "Плотная атмосфера и раскалённые вулканические равнины.", 2, 2, 1, 1, 40, 14, ("scrap", "asterium", "data", "biosilicate"), None, 0.18),
    "mars": Location("Марс", "Пыльные каньоны и залежи древних минералов.", 2, 2, 1, 0, 45, 12, ("scrap", "ice", "data", "asterium", "biosilicate"), None, 0.08),
    "asteroid_belt": Location("Пояс астероидов", "Обломки древних экспедиций вращаются среди астероидов.", 3, 3, 2, 2, 55, 15, ("scrap", "electronics", "asterium", "nebulite", "plasma_threads"), None, 0.12),
    "pioneer9": Location("Станция «Пионер-9»", "Заброшенная станция. В журнале значится предупреждение: «Не открывайте шлюз».", 2, 2, 1, 1, 40, 20, ("electronics", "data", "echo_shards", "xenoquartz"), "pioneer_coordinates", 0.10),
    "phobos": Location("Фобос", "Спутник Марса с заброшенным ретранслятором.", 4, 4, 2, 2, 65, 16, ("scrap", "asterium", "echo_shards", "graviton_cores"), "mars_archive"),
    "deimos": Location("Деймос", "Далёкий спутник с необычными геологическими структурами.", 4, 4, 2, 2, 70, 16, ("ice", "nebulite", "biosilicate", "phase_dust"), "mars_archive"),
    "europa": Location("Европа", "Ледяная кора скрывает подлёдный океан.", 5, 5, 3, 2, 80, 20, ("ice", "ion_gel", "biosilicate", "xenoquartz"), "pioneer_choice"),
    "titan": Location("Титан", "Плотная атмосфера и метановые моря.", 6, 6, 3, 3, 90, 22, ("ice", "ion_gel", "nebulite", "phase_dust"), "europa_archive"),
    "jupiter": Location("Юпитер", "Опасная зона у газового гиганта.", 7, 7, 4, 3, 100, 25, ("nebulite", "plasma_threads", "graviton_cores"), "titan_archive"),
    "saturn": Location("Сатурн", "Кольца Сатурна полны древнего космического льда.", 8, 8, 4, 4, 110, 25, ("ice", "asterium", "xenoquartz", "quantum_matrices"), "jupiter_archive"),
    "sun_observatory": Location("Солнце (наблюдательная орбита)", "Защищённая научная станция для наблюдения за короной Солнца.", 9, 9, 5, 4, 120, 25, ("plasma_threads", "graviton_cores", "phase_dust"), "saturn_archive", 0.25),
    "uranus": Location("Уран", "Ледяной гигант на краю исследованной системы.", 9, 9, 5, 4, 120, 28, ("ion_gel", "nebulite", "phase_dust"), "saturn_archive"),
    "neptune": Location("Нептун", "Дальний мир с сильными ветрами и аномальными сигналами.", 10, 10, 5, 5, 130, 30, ("plasma_threads", "graviton_cores", "echo_shards"), "uranus_archive"),
    "pluto": Location("Плутон", "Карликовая планета в поясе Койпера.", 11, 11, 6, 5, 140, 30, ("asterium", "xenoquartz", "quantum_matrices"), "neptune_archive"),
}

SCAN_STORY_UNLOCKS: dict[str, str] = {
    "mars": "mars_archive",
    "europa": "europa_archive",
    "titan": "titan_archive",
    "jupiter": "jupiter_archive",
    "saturn": "saturn_archive",
    "uranus": "uranus_archive",
    "neptune": "neptune_archive",
}

# Артефакты, которые могут находить исследователи в каждой локации.
ARTIFACT_NAMES: dict[str, tuple[str, ...]] = {
    "earth_orbit": (
        "Фрагмент звёздной карты",
        "Старый маяк станции",
        "Запечатанный контейнер",
        "Памятная пластина экипажа",
        "Сломанный навигационный диск",
    ),
    "moon": (
        "Лунный навигационный диск",
        "Сломанный ретранслятор Эхо",
        "Кристалл неизвестного происхождения",
        "След ботинка экспедиции",
        "Фрагмент звёздной карты",
    ),
    "pioneer9": (
        "Пластина «Пионера»",
        "Бортовой журнал инженера",
        "Оплавленный ключ шлюза",
        "Голосовой кристалл экипажа",
        "Последний сигнал станции",
    ),
}


# Стартовые характеристики корабля, цены модулей и стоимость обслуживания.
SHIP = {
    "name": "Искра",
    "fuel_max": 100,
    "hull_max": 100,
    "energy_max": 100,
    "starting_energy": 80,
    "starting_credits": 500,
    "starting_resources": {"scrap": 5, "electronics": 2},
    "upgrade_costs": {
        "ship": {"credits": 250, "scrap": 2, "electronics": 1},
        "engine": {"credits": 150, "electronics": 1, "plasma_threads": 0},
        "scanner": {"credits": 200, "electronics": 2, "nebulite": 0},
        "cargo": {"credits": 150, "scrap": 2},
        "protection": {"credits": 250, "scrap": 3, "phase_dust": 0},
        "energy": {"credits": 200, "electronics": 1, "ion_gel": 0},
    },
    "advanced_upgrade_costs": {
        "ship": {2: {"asterium": 1}},
        "engine": {2: {"plasma_threads": 1}, 3: {"graviton_cores": 1}, 4: {"quantum_matrices": 1}},
        "scanner": {2: {"nebulite": 1, "xenoquartz": 1}, 4: {"quantum_matrices": 1}},
        "cargo": {2: {"ion_gel": 1}, 3: {"quantum_matrices": 1}},
        "protection": {1: {"phase_dust": 1}, 2: {"asterium": 1}, 3: {"quantum_matrices": 1}},
        "energy": {1: {"ion_gel": 1, "biosilicate": 1}, 2: {"quantum_matrices": 1}},
    },
    "repair": {"credits": 50, "scrap": 2, "hull": 25},
    "refuel": {"credits": 40, "fuel": 30},
    "scan_energy": 10,
    "cargo_capacity": 20,
}

# Пакеты пополнения ОРБИТАЛОВ через Telegram Stars (цены подтверждены пользователем).
DONATION_PACKAGES: dict[str, dict[str, int | str]] = {
    "starter": {"name": "Стартовый", "orbitals": 50, "stars": 25},
    "pilot": {"name": "Пилотский", "orbitals": 120, "stars": 50},
    "captain": {"name": "Капитанский", "orbitals": 300, "stars": 100},
}

REFERRAL_MAX_FRIENDS = 20
REFERRAL_FIRST_REWARD = 20
REFERRAL_NEXT_REWARD = 5
REFERRAL_TOPUP_BONUS_PERCENT = 5

SCAN_CREDIT_REWARD = 5
FIRST_SCAN_CREDIT_REWARD = 100


# Опыт, максимальный уровень и награды за достижение отдельных уровней.
LEVEL_XP_BASE = 100
LEVEL_XP_EXPONENT = 1.35
LEVEL_CAP = 100
LEVEL_REWARDS: dict[int, dict[str, int]] = {
    2: {"fuel": 20}, 3: {"orbitals": 5}, 5: {"scrap": 3},
    7: {"orbitals": 10}, 10: {"electronics": 2, "orbitals": 15},
    15: {"orbitals": 20}, 20: {"asterium": 1, "orbitals": 25},
}


# Контейнеры и награды. Вес вероятности задаётся целыми числами из 10 000.
@dataclass(frozen=True)
class Case:
    name: str
    description: str
    cost: int
    rewards: tuple[tuple[str, str, int, int], ...]


# Редкости экипировки и косметики независимы друг от друга.
EQUIPMENT_RARITY_CHANCES: tuple[tuple[str, int], ...] = (
    ("Обычный", 5500),
    ("Редкий", 2500),
    ("Эпический", 1200),
    ("Уникальный", 600),
    ("Легендарный", 170),
    ("Квантовый", 30),
)

NICKNAME_COSMETIC_RARITY_CHANCES: tuple[tuple[str, int], ...] = (
    ("Обычный", 6000),
    ("Редкий", 2500),
    ("Эпический", 1000),
    ("Легендарный", 400),
    ("Мифический", 100),
)

# Внешний вид ника хранится отдельно от игровых характеристик.
NICKNAME_COSMETICS: dict[
    str, tuple[tuple[str, str, str, str], ...]
] = {
    "Обычный": (
        ("dust_signal", "Пыльный сигнал", "⌁ ", " ⌁"),
        ("crew_member", "Член экипажа", "· ", " ·"),
    ),
    "Редкий": (
        ("lunar_spectrum", "Лунный спектр", "☾ ", " ☽"),
        ("asteroid_trail", "След астероида", "✧ ", " ✧"),
    ),
    "Эпический": (
        ("pioneer_echo", "Эхо Пионера", "◈ ", " ◈"),
        ("nebula_wave", "Волна туманности", "∿ ", " ∿"),
    ),
    "Легендарный": (
        ("solar_crown", "Солнечная корона", "☼ ", " ☼"),
        ("pulsar_ring", "Кольцо пульсара", "⟲ ", " ⟲"),
    ),
    "Мифический": (
        ("neon_singularity", "Неон-сингулярность", "⟦", "⟧"),
    ),
}


# Каталог кейсов. Для обычных кейсов вес награды указан из 10 000;
# «Неон-сингулярность» выдаёт косметику ника вместо ресурсов.
CASES: dict[str, Case] = {
    "salvage_container": Case(
        "Утильконтейнер",
        "Базовый набор материалов из переработанных обломков.",
        20,
        (
            ("scrap", "Металлолом", 5, 4500),
            ("ice", "Лёд", 4, 2500),
            ("electronics", "Электронные компоненты", 2, 2000),
            ("fuel", "Топливо", 15, 1000),
        ),
    ),
    "lunar_cache": Case(
        "Лунный тайник",
        "Запечатанный контейнер из теневого кратера с редкими лунными образцами.",
        35,
        (
            ("ice", "Лёд", 5, 3000),
            ("ion_gel", "Ионный гель", 2, 2500),
            ("echo_shards", "Эхо-осколки", 2, 1800),
            ("nebulite", "Небулит", 1, 1500),
            ("xenoquartz", "Ксенокварц", 1, 1200),
        ),
    ),
    "pioneer_archive": Case(
        "Архив Пионера-9",
        "Восстановленные журналы, компоненты и фрагменты сигнала станции.",
        50,
        (
            ("data", "Научные данные", 5, 3000),
            ("echo_shards", "Эхо-осколки", 3, 2500),
            ("electronics", "Электронные компоненты", 3, 2000),
            ("xenoquartz", "Ксенокварц", 1, 1500),
            ("quantum_matrices", "Квантовые матрицы", 1, 1000),
        ),
    ),
    "zero_sector_arsenal": Case(
        "Арсенал нулевого сектора",
        "Военный контейнер с деталями для двигателей и усиления корпуса.",
        80,
        (
            ("electronics", "Электронные компоненты", 4, 2500),
            ("plasma_threads", "Плазменные нити", 2, 2500),
            ("asterium", "Астерий", 2, 2000),
            ("scrap", "Металлолом", 8, 2000),
            ("graviton_cores", "Гравитонные ядра", 1, 1000),
        ),
    ),
    "prospector_protocol": Case(
        "Протокол добытчика",
        "Экспедиционный резерв минералов и материалов дальних маршрутов.",
        65,
        (
            ("scrap", "Металлолом", 7, 3000),
            ("asterium", "Астерий", 2, 2200),
            ("ice", "Лёд", 5, 2000),
            ("nebulite", "Небулит", 2, 1500),
            ("plasma_threads", "Плазменные нити", 1, 900),
            ("graviton_cores", "Гравитонные ядра", 1, 400),
        ),
    ),
    "quantum_sarcophagus": Case(
        "Квантовый саркофаг",
        "Изолированный блок с высокотехнологичными и фазовыми материалами.",
        120,
        (
            ("quantum_matrices", "Квантовые матрицы", 2, 2200),
            ("xenoquartz", "Ксенокварц", 3, 2200),
            ("phase_dust", "Фазовая пыль", 3, 2000),
            ("graviton_cores", "Гравитонные ядра", 2, 1600),
            ("nebulite", "Небулит", 3, 1200),
            ("echo_shards", "Эхо-осколки", 3, 800),
        ),
    ),
    "neon_singularity": Case(
        "Неон-сингулярность",
        "Кейс с косметическими оболочками ника. Косметика не влияет на характеристики, сюжет или доступ к планетам.",
        150,
        (),
    ),
}

CASE_COST = CASES["salvage_container"].cost
CASE_REWARDS = CASES["salvage_container"].rewards

# Исследование чертежа и стоимость создания одной квантовой матрицы.
# Для исследования сначала нужно собрать этот же набор ресурсов и кредитов;
# после исследования материалы остаются у игрока для последующей сборки.
QUANTUM_MATRIX_RECIPE = {
    "credits": 600,
    "plasma_threads": 5,
    "xenoquartz": 2,
    "data": 6,
}


# Ограничения прокачки и вклада в гильдии.
GUILD_MAX_LEVEL = 100
GUILD_LEVEL_XP_BASE = 100
GUILD_LEVEL_XP_STEP = 65
GUILD_STARTING_MEMBERS = 10
GUILD_MEMBER_BONUS_LEVELS = {5: 5, 10: 5, 25: 10, 50: 10}
GUILD_CONTRIBUTION_XP_PER_UNIT = 1
GUILD_DAILY_XP_CAP = 100
GUILD_ALLOWED_CONTRIBUTIONS = {"scrap", "electronics", "ice", "data", "asterium", "nebulite", "ion_gel"}
