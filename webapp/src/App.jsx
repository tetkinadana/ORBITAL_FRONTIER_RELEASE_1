import { useEffect, useMemo, useState } from "react";
import PlanetRun from "./PlanetRun.jsx";
import "./App.css";
import "./PixelTheme.css";

const STORAGE_KEY = "orbital-frontier-save-v1";

const initialGame = {
  xp: 0,
  credits: 120,
  orbitals: 0,
  accelerators: 0,
  dailyOrbitalClaim: "",
  weeklyOrbitalClaims: [],
  orbitalHistory: [],
  crystals: 30,
  dna: 0,
  fuel: 30,
  iron: 8,
  copper: 6,
  silicon: 2,
  coal: 0,
  aluminum: 0,
  polymers: 0,
  plates: 0,
  copperWire: 0,
  aluminumPanel: 0,
  circuitBoard: 0,
  insulation: 0,
  reinforcedBeam: 0,
  // Extended planetary and rare-resource catalog. Existing save values are retained by loadGame.
  titanium: 0,
  uranium: 0,
  ice: 0,
  helium3: 0,
  scrap: 0,
  electronics: 0,
  data: 0,
  asterium: 0,
  nebulite: 0,
  ion_gel: 0,
  xenoquartz: 0,
  phase_dust: 0,
  plasma_threads: 0,
  biosilicate: 0,
  graviton_cores: 0,
  echo_shards: 0,
  quantum_matrices: 0,
  scanners: 0,
  weaponBonus: 0,
  armorBonus: 0,
  expeditions: 0,
  creditsSpent: 0,
  dailyTaskStats: { date: "", clears: 0, crafted: 0, sold: 0 },
  weeklyTaskStats: { week: "", expeditions: 0, bosses: 0, creditsSpent: 0, chests: 0 },
  sectors: ["earth"],
  weapons: ["pulse"],
  skins: ["default"],
  artifacts: [],
  shipStorage: [],
  stationStorage: [],
  shipResources: {},
  shipUpgrades: { storage: 0, engine: 0, hull: 0, reactor: 0 },
  planetBuildings: [],
  blueprints: [],
  craftedBlueprints: [],
  equippedWeapon: "pulse",
  equippedSkin: "default",
  bossesDefeated: 0,
  gachaPity: 0,
  dailyDraw: "",
  referralCode: "",
  referralClaimed: false,
  guild: null,
  pilotName: "",
  labTask: null,
  claimedCollections: [],
  claimedTasks: [],
  planetResearch: null,
  upgrades: { health: 0, damage: 0, speed: 0, luck: 0, research: 0 },
};

const tabs = [
  { id: "home", icon: "⌂", label: "БАЗА" },
  { id: "station", icon: "▤", label: "СТАНЦИЯ" },
  { id: "battle", icon: "✦", label: "ЭКСПЕДИЦИИ" },
  { id: "more", icon: "☷", label: "ЕЩЁ" },
];
const extraTabs = [
  { id: "gacha", icon: "✦", label: "КОСМИЧЕСКИЙ ПРИЗЫВ" },
  { id: "collection", icon: "✧", label: "КОЛЛЕКЦИИ" },
  { id: "craft", icon: "⌬", label: "МАСТЕРСКАЯ" },
  { id: "lab", icon: "▦", label: "ЛАБОРАТОРИЯ" },
  { id: "guild", icon: "♟", label: "ГИЛЬДИЯ" },
  { id: "profile", icon: "◉", label: "ПИЛОТ" },
  { id: "donate", icon: "◎", label: "ДОНАТ" },
  { id: "ship", icon: "🚀", label: "КОРАБЛЬ" },
  { id: "tasks", icon: "☑", label: "ЗАДАНИЯ" },
];

const sectors = [
  { id: "earth", icon: "◉", name: "Земля", description: "Стартовая орбита и первая зона зачистки", threatLevel: 1, unlockXp: 0, cost: 0 },
  { id: "mercury", icon: "☿", name: "Меркурий", description: "Обожжённые кратеры и металлические залежи", threatLevel: 1, unlockXp: 80, cost: 40 },
  { id: "venus", icon: "♀", name: "Венера", description: "Плотная атмосфера и вулканические равнины", threatLevel: 2, unlockXp: 180, cost: 80 },
  { id: "mars", icon: "♂", name: "Марс", description: "Красные каньоны и древние минералы", threatLevel: 3, unlockXp: 320, cost: 120 },
  { id: "jupiter", icon: "♃", name: "Юпитер", description: "Штормовая зона газового гиганта", threatLevel: 4, unlockXp: 550, cost: 180 },
  { id: "saturn", icon: "♄", name: "Сатурн", description: "Кольца из льда и обломков", threatLevel: 5, unlockXp: 850, cost: 240 },
  { id: "uranus", icon: "⛢", name: "Уран", description: "Холодный ледяной гигант", threatLevel: 6, unlockXp: 1250, cost: 320 },
  { id: "neptune", icon: "♆", name: "Нептун", description: "Дальний мир с экстремальными ветрами", threatLevel: 6, unlockXp: 1800, cost: 420 },
];

const solarPositions = {
  mars: { x: 50, y: 13, size: 52 },
  neptune: { x: 24, y: 25, size: 60 },
  uranus: { x: 76, y: 25, size: 58 },
  saturn: { x: 15, y: 51, size: 88 },
  jupiter: { x: 85, y: 51, size: 84 },
  venus: { x: 25, y: 79, size: 64 },
  earth: { x: 75, y: 79, size: 68 },
  mercury: { x: 50, y: 91, size: 43 },
};

function PlanetArtwork({ planetId }) {
  const clipId = `planet-clip-${planetId}`;
  const gradientId = `planet-shade-${planetId}`;
  const palettes = {
    mercury: { light: "#d2d0c5", mid: "#858a8d", dark: "#454b55", accent: "#b3b1a6" },
    venus: { light: "#ffe0a0", mid: "#d58b49", dark: "#874a32", accent: "#f2bd70" },
    earth: { light: "#83d9ed", mid: "#2878b7", dark: "#173b75", accent: "#70bf75" },
    mars: { light: "#f5b081", mid: "#bd604b", dark: "#713747", accent: "#db8060" },
    jupiter: { light: "#f6d4a3", mid: "#c38b65", dark: "#754e4b", accent: "#e8b77d" },
    saturn: { light: "#fff0bd", mid: "#c9a66d", dark: "#786044", accent: "#e5ce96" },
    uranus: { light: "#d0fff0", mid: "#78bdc5", dark: "#34718c", accent: "#9ce0da" },
    neptune: { light: "#9cc7ff", mid: "#426fbd", dark: "#1d326f", accent: "#7195df" },
  };
  const colors = palettes[planetId] || palettes.earth;
  const isSaturn = planetId === "saturn";
  return (
    <svg className={`planet-art planet-art-${planetId}`} viewBox="0 0 96 96" role="img" aria-label={sectors.find((item) => item.id === planetId)?.name || "Планета"} shapeRendering="crispEdges">
      <defs>
        <clipPath id={clipId}><circle cx="48" cy="48" r="29" /></clipPath>
        <linearGradient id={gradientId} x1="18%" y1="12%" x2="84%" y2="88%">
          <stop offset="0%" stopColor={colors.light} />
          <stop offset="48%" stopColor={colors.mid} />
          <stop offset="100%" stopColor={colors.dark} />
        </linearGradient>
      </defs>
      {isSaturn && <>
        <ellipse cx="48" cy="50" rx="43" ry="13" transform="rotate(-22 48 50)" fill="none" stroke="#8b704d" strokeWidth="10" opacity=".9" />
        <ellipse cx="48" cy="50" rx="43" ry="13" transform="rotate(-22 48 50)" fill="none" stroke="#f4d79a" strokeWidth="3" opacity=".9" />
      </>}
      <circle cx="48" cy="48" r="30" fill={`url(#${gradientId})`} stroke={colors.light} strokeWidth="1.5" />
      <g clipPath={`url(#${clipId})`} shapeRendering="crispEdges">
        {planetId === "earth" && <>
          <path d="M24 35h10v-5h9v7h-5v8h-8v8h-8v-9h-5v-5h7z M54 54h8v-7h10v7h8v11H71v8h-9v-7h-8z" fill="#77c56f" />
          <path d="M27 29h8v4h-8z M60 34h7v4h-7z M19 55h7v4h-7z" fill="#b6e69a" />
          <path d="M54 27h12v4H54z M68 61h9v4h-9z" fill="#e9f5e8" opacity=".8" />
        </>}
        {planetId === "mercury" && <>
          <circle cx="34" cy="34" r="7" fill="#626a70" stroke="#d0cbbc" strokeWidth="2" />
          <circle cx="59" cy="55" r="9" fill="#555e68" stroke="#b9b6a9" strokeWidth="2" />
          <rect x="26" y="58" width="8" height="5" fill="#d4cbb8" /><rect x="54" y="26" width="9" height="4" fill="#e1d9c8" />
          <rect x="69" y="39" width="7" height="5" fill="#616872" />
        </>}
        {planetId === "venus" && <>
          <path d="M15 31h20v6h-8v5H17z M42 22h30v7H60v5H43z M33 49h38v7H56v5H33z M18 64h24v6H18z" fill="#ffd58b" />
          <rect x="51" y="39" width="25" height="5" fill="#f1b96b" /><rect x="23" y="44" width="12" height="4" fill="#9d5538" opacity=".7" />
        </>}
        {planetId === "mars" && <>
          <path d="M18 32h17v6H18z M49 26h18v5H49z M32 55h24v6H32z M61 66h17v5H61z" fill="#f1ad7b" />
          <circle cx="36" cy="43" r="6" fill="#8d4a48" stroke="#e99a71" strokeWidth="2" />
          <circle cx="65" cy="50" r="4" fill="#733b43" stroke="#d98167" strokeWidth="1.5" />
          <rect x="22" y="68" width="8" height="4" fill="#743e45" />
        </>}
        {planetId === "jupiter" && <>
          <rect x="15" y="27" width="66" height="7" fill="#f2d6a2" /><rect x="15" y="39" width="66" height="5" fill="#9b6756" />
          <rect x="15" y="49" width="66" height="8" fill="#f0c18a" /><rect x="15" y="63" width="66" height="6" fill="#89584f" />
          <rect x="53" y="51" width="14" height="8" fill="#bd6651" /><rect x="57" y="48" width="7" height="3" fill="#e9a071" />
        </>}
        {planetId === "saturn" && <>
          <rect x="15" y="28" width="66" height="6" fill="#fff0c1" /><rect x="15" y="39" width="66" height="5" fill="#9c8059" />
          <rect x="15" y="50" width="66" height="8" fill="#f3d89d" /><rect x="15" y="65" width="66" height="5" fill="#a78357" />
        </>}
        {planetId === "uranus" && <>
          <rect x="16" y="29" width="64" height="5" fill="#c4f5e7" /><rect x="16" y="42" width="64" height="5" fill="#4c9eae" />
          <rect x="16" y="56" width="64" height="7" fill="#b8f0df" /><rect x="27" y="68" width="43" height="4" fill="#4f9aa9" />
        </>}
        {planetId === "neptune" && <>
          <path d="M16 30h64v6H16z M16 44h64v5H16z M16 59h64v7H16z" fill="#789ee9" />
          <rect x="55" y="39" width="15" height="7" fill="#304b98" /><rect x="25" y="65" width="16" height="5" fill="#263e82" />
          <path d="M32 25h9v4h-9z M65 69h8v4h-8z" fill="#b4d5ff" />
        </>}
        <rect x="17" y="19" width="24" height="5" fill="#ffffff" opacity=".16" />
      </g>
      <path d="M29 21A30 30 0 0 0 20 61" fill="none" stroke="#ffffff" strokeWidth="3" opacity=".28" />
      <path d="M65 72h13v5H65z" fill="#101a31" opacity=".25" />
      {isSaturn && <path d="M9 55C26 75 69 77 88 51" fill="none" stroke="#f4d79a" strokeWidth="5" opacity=".95" />}
    </svg>
  );
}

// Распределение простых ресурсов по планетам первого этапа.
const planetDeposits = {
  earth: ["Железо", "Медь", "Уголь", "Полимеры"],
  mercury: ["Железо", "Медь", "Алюминий"],
  venus: ["Кремний", "Алюминий", "Полимеры"],
  mars: ["Железо", "Кремний", "Алюминий", "Уголь"],
  jupiter: ["Медь", "Кремний", "Полимеры"],
  saturn: ["Алюминий", "Кремний", "Полимеры"],
  uranus: ["Железо", "Алюминий", "Уголь"],
  neptune: ["Медь", "Кремний", "Полимеры"],
};

const weapons = [
  { id: "pulse", name: "Импульсный бластер", rarity: "Обычное", damage: 18, color: "#b9dc7b" },
  { id: "frost", name: "Крио-излучатель", rarity: "Необычное", damage: 22, color: "#80d9ee" },
  { id: "rail", name: "Рельсовая пушка", rarity: "Редкое", damage: 30, color: "#ffbc6e" },
  { id: "nova", name: "Копьё сверхновой", rarity: "Уникальное", damage: 40, color: "#b5baff" },
  { id: "comet", name: "Кометный разряд", rarity: "Легендарное", damage: 52, color: "#ff7d83" },
  { id: "phase", name: "Фазовый разрушитель", rarity: "Квантовое", damage: 64, color: "#e18cff" },
];

const skins = [
  { id: "default", name: "Кадет", rarity: "Обычное", color: "#b9dc7b" },
  { id: "amber", name: "Пустынный рейнджер", rarity: "Необычное", color: "#eda96e" },
  { id: "lunar", name: "Лунный призрак", rarity: "Редкое", color: "#b5baff" },
  { id: "exo", name: "Экзокостюм «Фантом»", rarity: "Уникальное", color: "#8df0d2" },
  { id: "nebula", name: "Страж туманности", rarity: "Легендарное", color: "#ef8ed3" },
  { id: "chrono", name: "Хроноскафандр", rarity: "Квантовое", color: "#e18cff" },
];

const baseArtifacts = [
  { id: "heart", name: "Сердце титана", rarity: "Обычное", bonus: "Здоровье +12", stat: "health", value: 1 },
  { id: "magnet", name: "Магнитный модуль", rarity: "Необычное", bonus: "Дальность сбора +", stat: "magnet", value: 1 },
  { id: "lens", name: "Линза охотника", rarity: "Редкое", bonus: "Урон +8", stat: "damage", value: 2 },
  { id: "aegis", name: "Эгида древних", rarity: "Уникальное", bonus: "Здоровье +36", stat: "health", value: 3 },
  { id: "star", name: "Осколок сверхновой", rarity: "Легендарное", bonus: "Урон +16", stat: "damage", value: 4 },
  { id: "core", name: "Ядро сингулярности", rarity: "Квантовое", bonus: "Урон +24", stat: "damage", value: 6 },
 ];

const relicNames = [
  ["Спутниковый осколок", "Ядро старой Земли", "Лунный компас", "Память биосферы", "Сфера первой колонии"],
  ["Солнечный шлак", "Ртутная печать", "Кратерный глаз", "Жар-память", "Осколок Меркурия"],
  ["Венерианская жемчужина", "Облачный фильтр", "Сердце вулкана", "Туманная линза", "Сфера Венеры"],
  ["Марсианский тотем", "Песчаный архив", "Красный кристалл", "Ключ каньона", "Осколок Фобоса"],
  ["Штормовой узел", "Ионная спираль", "Глаз Юпитера", "Грозовой куб", "Ядро гиганта"],
  ["Кольцо времени", "Ледяная руна", "Сатурнианский ключ", "Пыль древних колец", "Сфера титана"],
  ["Крио-сигил", "Ледяное сердце", "Полярный архив", "Синий резонатор", "Осколок Урана"],
  ["Нептунова корона", "Глубинный маяк", "Вихревой кристалл", "Синий реликварий", "Печать бездны"],
];
const artifacts = [...baseArtifacts, ...sectors.flatMap((sector, planetIndex) => relicNames[planetIndex].map((name, index) => ({
  id: `${sector.id}_relic_${index + 1}`, name, planetId: sector.id,
  rarity: ["Обычное", "Необычное", "Редкое", "Уникальное", "Легендарное"][index],
  bonus: "Реликвия коллекции", stat: "collection", value: 0,
})))];

const rarityTiers = [
  { name: "Обычное", color: "#b8c5a5" },
  { name: "Необычное", color: "#76d5a5" },
  { name: "Редкое", color: "#70c9f2" },
  { name: "Уникальное", color: "#b5a0ff" },
  { name: "Легендарное", color: "#ffb65c" },
  { name: "Квантовое", color: "#ef82ff" },
];

const gachaItems = [...weapons, ...skins, ...artifacts];
const gachaChests = [
  {
    id: "frontier",
    name: "Сундук первопроходца",
    icon: "▣",
    cost: 10,
    description: "Базовое снаряжение и артефакты для первых экспедиций.",
    itemIds: ["pulse", "frost", "rail", "heart", "magnet", "lens", "default", "amber", "lunar"],
    weights: [58, 27, 15, 0, 0, 0],
  },
  {
    id: "armory",
    name: "Арсенальный контейнер",
    icon: "▤",
    cost: 20,
    description: "Оружие, костюмы и артефакты вплоть до легендарных.",
    itemIds: ["pulse", "frost", "rail", "nova", "comet", "heart", "magnet", "lens", "aegis", "star", "default", "amber", "lunar", "exo", "nebula"],
    weights: [35, 25, 19, 11, 10, 0],
  },
  {
    id: "quantum",
    name: "Квантовый реликварий",
    icon: "▧",
    cost: 30,
    description: "Редкие находки, включая уникальные и квантовые реликвии.",
    itemIds: ["rail", "nova", "comet", "phase", "lens", "aegis", "star", "core", "lunar", "exo", "nebula", "chrono"],
    weights: [0, 0, 20, 28, 27, 25],
  },
];

gachaChests.forEach((chest) => {
  chest.itemIds = [...new Set([...chest.itemIds, ...artifacts.filter((item) => item.planetId && (chest.id !== "frontier" || item.rarity === "Обычное" || item.rarity === "Необычное")).map((item) => item.id)])];
});

const blueprintRecipes = [
  { id: "overclock", name: "Катушка перегрузки", description: "+6 к урону оружия", iron: 5, copper: 3, silicon: 2, weaponBonus: 6 },
  { id: "armor", name: "Усиленная броня", description: "+18 к здоровью", iron: 6, copper: 3, plates: 2, armorBonus: 18 },
];

const researchModules = [
  { id: "armor", name: "Броня", icon: "▣", description: "Крепость корпуса и защита от ударов", resource: "iron", baseCost: 18, scale: 1.4, durationMs: 1000 * 60 * 60 * 12, effect: "+12 к здоровью" },
  { id: "damage", name: "Урон", icon: "⚔", description: "Критический урон оружия для зачистки", resource: "copper", baseCost: 22, scale: 1.6, durationMs: 1000 * 60 * 60 * 12, effect: "+4 к урону" },
  { id: "speed", name: "Скорость", icon: "⇄", description: "Быстрее маневрировать на планетах", resource: "silicon", baseCost: 16, scale: 1.5, durationMs: 1000 * 60 * 60 * 12, effect: "+12% к скорости" },
  { id: "luck", name: "Удача", icon: "✦", description: "Лучшая вероятность находок и выпадений", resource: "crystals", baseCost: 12, scale: 1.8, durationMs: 1000 * 60 * 60 * 12, effect: "+1 удача" },
  { id: "research", name: "Исследование", icon: "⌬", description: "Повышение эффективности лаборатории", resource: "dna", baseCost: 20, scale: 1.8, durationMs: 1000 * 60 * 60 * 12, effect: "+1 научный модуль" },
];

const resourceLabels = {
  iron: "железа", copper: "меди", silicon: "кремния", coal: "угля", aluminum: "алюминия", polymers: "полимеров",
  plates: "железных пластин", copperWire: "медных проводов", aluminumPanel: "алюминиевых панелей", circuitBoard: "электронных плат",
  insulation: "изоляции", reinforcedBeam: "усиленных балок", titanium: "титана", uranium: "урана", ice: "водяного льда",
  helium3: "гелия-3", scrap: "металлолома", electronics: "электронных компонентов", data: "научных данных", asterium: "астерии",
  nebulite: "небулита", scanners: "сканеров", ion_gel: "ионного геля", xenoquartz: "ксенокварца", phase_dust: "фазовой пыли",
  plasma_threads: "плазменных нитей", biosilicate: "биосиликата", graviton_cores: "гравитонных ядер",
  echo_shards: "эхо-осколков", quantum_matrices: "квантовых матриц"
};

const recipes = [
  { id: "plates", icon: "▰", name: "Железная пластина", description: "3 железа", iron: 3, output: { plates: 1 } },
  { id: "scanner", icon: "⌕", name: "Сканер разведчика", description: "2 пластины + 2 меди + 2 кремния", plates: 2, copper: 2, silicon: 2, output: { scanners: 1 } },
  { id: "fuel", icon: "◌", name: "Запас топлива", description: "2 железа + 1 кремний", iron: 2, silicon: 1, output: { fuel: 10 } },
  { id: "copperWire", icon: "〰", name: "Медный провод ×2", description: "1 медь", copper: 1, output: { copperWire: 2 } },
  { id: "aluminumPanel", icon: "▱", name: "Алюминиевая панель", description: "3 алюминия", aluminum: 3, output: { aluminumPanel: 1 } },
  { id: "circuitBoard", icon: "▦", name: "Электронная плата", description: "2 меди + 2 кремния", copper: 2, silicon: 2, output: { circuitBoard: 1 } },
  { id: "insulation", icon: "▤", name: "Изоляция ×2", description: "2 полимера", polymers: 2, output: { insulation: 2 } },
  { id: "reinforcedBeam", icon: "╋", name: "Усиленная балка", description: "2 железа + 1 алюминий", iron: 2, aluminum: 1, output: { reinforcedBeam: 1 } },
];

const recipeResources = [
  { key: "iron", label: "Железо", icon: "Fe" },
  { key: "copper", label: "Медь", icon: "Cu" },
  { key: "silicon", label: "Кремний", icon: "Si" },
  { key: "coal", label: "Уголь", icon: "C" },
  { key: "aluminum", label: "Алюминий", icon: "Al" },
  { key: "polymers", label: "Полимеры", icon: "P" },
  { key: "plates", label: "Пластины", icon: "▰" },
];

const guildDirectory = [];

const donationPackages = [
  { id: "starter", name: "Стартер", orbitals: 120, rubles: 199 },
  { id: "expedition", name: "Экспедиция", orbitals: 360, rubles: 499 },
  { id: "vanguard", name: "Авангард", orbitals: 900, rubles: 999 },
  { id: "carrier", name: "Перевозчик", orbitals: 2100, rubles: 1999 },
];

function drawGachaItem(chest, pity) {
  const chestItems = gachaItems.filter((item) => chest.itemIds.includes(item.id));
  const highRarities = rarityTiers.slice(3).map((tier) => tier.name);
  const availableWeights = rarityTiers.map((tier, index) => ({
    rarity: tier.name,
    weight: chest.weights[index],
  })).filter(({ rarity, weight }) => weight > 0 && chestItems.some((item) => item.rarity === rarity));
  const guaranteedWeights = availableWeights.filter(({ rarity }) => highRarities.includes(rarity));
  const rarityWeights = pity >= 9 && guaranteedWeights.length > 0 ? guaranteedWeights : availableWeights;
  const weightTotal = rarityWeights.reduce((total, entry) => total + entry.weight, 0);
  let roll = Math.random() * weightTotal;
  const selectedRarity = rarityWeights.find(({ weight }) => {
    roll -= weight;
    return roll < 0;
  }) ?? rarityWeights[rarityWeights.length - 1];
  const pool = chestItems.filter((item) => item.rarity === selectedRarity.rarity);
  return { item: pool[Math.floor(Math.random() * pool.length)], highRarities };
}

function makeReferralCode() {
  return `OF-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

function loadGame() {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (!saved) return { game: { ...initialGame, referralCode: makeReferralCode() }, warning: "" };

    const parsed = JSON.parse(saved);
    if (parsed?.version !== 1 || typeof parsed.game !== "object" || parsed.game === null) {
      return { game: { ...initialGame, referralCode: makeReferralCode() }, warning: "Сохранение не распознано — начата новая экспедиция." };
    }

    const source = parsed.game;
    const game = { ...initialGame, ...source };
    for (const key of ["xp", "credits", "orbitals", "accelerators", "crystals", "dna", "fuel", "iron", "copper", "silicon", "coal", "aluminum", "polymers", "plates", "copperWire", "aluminumPanel", "circuitBoard", "insulation", "reinforcedBeam", "titanium", "uranium", "ice", "helium3", "scrap", "electronics", "data", "asterium", "nebulite", "ion_gel", "xenoquartz", "phase_dust", "plasma_threads", "biosilicate", "graviton_cores", "echo_shards", "quantum_matrices", "scanners", "weaponBonus", "armorBonus", "expeditions", "bossesDefeated", "gachaPity", "creditsSpent"]) {
      game[key] = Number.isFinite(source[key]) && source[key] >= 0 ? Math.floor(source[key]) : initialGame[key];
    }
    for (const key of ["sectors", "weapons", "skins", "artifacts", "blueprints", "craftedBlueprints"]) {
      game[key] = Array.isArray(source[key]) ? source[key].filter((id) => typeof id === "string") : [...initialGame[key]];
    }
    game.sectors = [...new Set(game.sectors.filter((id) => sectors.some((sector) => sector.id === id)))];
    if (!game.sectors.includes("earth")) game.sectors.unshift("earth");
    game.weapons = [...new Set(["pulse", ...game.weapons.filter((id) => weapons.some((weapon) => weapon.id === id))])];
    game.skins = [...new Set(["default", ...game.skins.filter((id) => skins.some((skin) => skin.id === id))])];
    game.artifacts = [...new Set(game.artifacts.filter((id) => artifacts.some((artifact) => artifact.id === id)))];
    const ownedStorageIds = [...new Set([...game.weapons, ...game.skins, ...game.artifacts.filter((id) => baseArtifacts.some((item) => item.id === id))])];
    game.shipStorage = Array.isArray(source.shipStorage) ? source.shipStorage.filter((id) => ownedStorageIds.includes(id)) : [];
    game.stationStorage = Array.isArray(source.stationStorage) ? source.stationStorage.filter((id) => ownedStorageIds.includes(id)) : ownedStorageIds.filter((id) => !game.shipStorage.includes(id));
    // Preserve every cargo key from older/newer saves. A fixed whitelist silently discarded
    // resources introduced by later game updates (including rare planetary materials).
    const knownCargoKeys = ["iron","copper","silicon","coal","aluminum","polymers","plates","copperWire","aluminumPanel","circuitBoard","insulation","reinforcedBeam","fuel","titanium","uranium","ice","helium3","scrap","electronics","data","asterium","nebulite","ion_gel","xenoquartz","phase_dust","plasma_threads","biosilicate","graviton_cores","echo_shards","quantum_matrices","scanners"];
    const savedCargo = source.shipResources && typeof source.shipResources === "object" ? source.shipResources : {};
    game.shipResources = Object.fromEntries([...new Set([...knownCargoKeys, ...Object.keys(savedCargo)])].map((key) => [
      key,
      Number.isFinite(savedCargo[key]) && savedCargo[key] >= 0 ? Math.floor(savedCargo[key]) : 0,
    ]));
    game.shipUpgrades = Object.fromEntries(["storage", "engine", "hull", "reactor"].map((key) => [key, Number.isFinite(source.shipUpgrades?.[key]) ? Math.max(0, Math.min(10, Math.floor(source.shipUpgrades[key]))) : 0]));
    game.planetBuildings = Array.isArray(source.planetBuildings) ? source.planetBuildings.filter((id) => typeof id === "string") : [];
    game.claimedCollections = Array.isArray(source.claimedCollections) ? source.claimedCollections.filter((id) => typeof id === "string") : [];
    game.claimedTasks = Array.isArray(source.claimedTasks) ? source.claimedTasks.filter((id) => typeof id === "string") : [];
    game.dailyTaskStats = source.dailyTaskStats && typeof source.dailyTaskStats === "object" ? {
      date: typeof source.dailyTaskStats.date === "string" ? source.dailyTaskStats.date : "",
      clears: Math.max(0, Math.floor(Number(source.dailyTaskStats.clears) || 0)),
      crafted: Math.max(0, Math.floor(Number(source.dailyTaskStats.crafted) || 0)),
      sold: Math.max(0, Math.floor(Number(source.dailyTaskStats.sold) || 0)),
    } : { ...initialGame.dailyTaskStats };
    game.weeklyTaskStats = source.weeklyTaskStats && typeof source.weeklyTaskStats === "object" ? {
      week: typeof source.weeklyTaskStats.week === "string" ? source.weeklyTaskStats.week : "",
      expeditions: Math.max(0, Math.floor(Number(source.weeklyTaskStats.expeditions) || 0)),
      bosses: Math.max(0, Math.floor(Number(source.weeklyTaskStats.bosses) || 0)),
      creditsSpent: Math.max(0, Math.floor(Number(source.weeklyTaskStats.creditsSpent) || 0)),
      chests: Math.max(0, Math.floor(Number(source.weeklyTaskStats.chests) || 0)),
    } : { ...initialGame.weeklyTaskStats };
    game.planetResearch = source.planetResearch && typeof source.planetResearch.sectorId === "string" && Number.isFinite(source.planetResearch.endsAt) ? source.planetResearch : null;
    game.blueprints = [...new Set(game.blueprints.filter((id) => blueprintRecipes.some((recipe) => recipe.id === id)))];
    game.craftedBlueprints = [...new Set(game.craftedBlueprints.filter((id) => blueprintRecipes.some((recipe) => recipe.id === id)))];
    game.upgrades = Object.fromEntries(["health", "damage", "speed", "luck", "research"].map((key) => [
      key,
      Number.isFinite(source.upgrades?.[key]) ? Math.max(0, Math.min(key === "research" ? 10 : 50, Math.floor(source.upgrades[key]))) : 0,
    ]));
    game.equippedWeapon = game.weapons.includes(source.equippedWeapon) ? source.equippedWeapon : "pulse";
    game.equippedSkin = game.skins.includes(source.equippedSkin) ? source.equippedSkin : "default";
    game.referralCode = typeof source.referralCode === "string" && source.referralCode ? source.referralCode : makeReferralCode();
    game.referralClaimed = source.referralClaimed === true;
    game.guild = source.guild && typeof source.guild.name === "string" ? source.guild : null;
    game.dailyDraw = typeof source.dailyDraw === "string" ? source.dailyDraw : "";
    game.dailyOrbitalClaim = typeof source.dailyOrbitalClaim === "string" ? source.dailyOrbitalClaim : "";
    game.weeklyOrbitalClaims = Array.isArray(source.weeklyOrbitalClaims) ? source.weeklyOrbitalClaims.filter((id) => typeof id === "string") : [];
    game.orbitalHistory = Array.isArray(source.orbitalHistory) ? source.orbitalHistory.slice(0, 30) : [];
    game.pilotName = typeof source.pilotName === "string" && source.pilotName.trim() ? source.pilotName.trim().slice(0, 16) : "";
    game.labTask = source.labTask && typeof source.labTask.id === "string" ? {
      id: source.labTask.id,
      startedAt: Number.isFinite(source.labTask.startedAt) ? Number(source.labTask.startedAt) : Date.now(),
      endsAt: Number.isFinite(source.labTask.endsAt) ? Number(source.labTask.endsAt) : Date.now() + 60_000,
    } : null;
    return { game, warning: "" };
  } catch {
    return { game: { ...initialGame, referralCode: makeReferralCode() }, warning: "Не удалось прочитать сохранение. Игра продолжится без старых данных." };
  }
}

function pilotProgress(totalXp) {
  let level = 1;
  let remaining = totalXp;
  let requirement = 500;
  while (remaining >= requirement) {
    remaining -= requirement;
    level += 1;
    requirement = 500 + (level - 1) * 250;
  }
  return { level, current: remaining, requirement };
}

function App() {
  const [active, setActive] = useState("home");
  const [loaded] = useState(loadGame);
  const [game, setGame] = useState(loaded.game);
  const [message, setMessage] = useState(loaded.warning);
  const [saveError, setSaveError] = useState("");
  const [selectedPlanet, setSelectedPlanet] = useState("earth");
  const [researchHours, setResearchHours] = useState(4);
  const [clockNow, setClockNow] = useState(Date.now());
  useEffect(() => { const timer = window.setInterval(() => setClockNow(Date.now()), 1000); return () => window.clearInterval(timer); }, []);
  const [runResult, setRunResult] = useState(null);
  const [runKey, setRunKey] = useState(0);
  const [inviteInput, setInviteInput] = useState("");
  const [guildInput, setGuildInput] = useState("");
  const [guildAvatar, setGuildAvatar] = useState("🛡️");
  const [guildCategory, setGuildCategory] = useState("Зачистки");
  const [nicknameDraft, setNicknameDraft] = useState("");
  const [nicknameEditorOpen, setNicknameEditorOpen] = useState(false);
  const [lastDrop, setLastDrop] = useState(null);
  const [chestHistory, setChestHistory] = useState([]);
  const [expandedRecipe, setExpandedRecipe] = useState("");
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [selectedChestId, setSelectedChestId] = useState("frontier");
  const [lootChestId, setLootChestId] = useState("");
  const [selectedStationResource, setSelectedStationResource] = useState("");
  const [equipmentModalOpen, setEquipmentModalOpen] = useState(false);
  const [gearModalCategory, setGearModalCategory] = useState("");
  const [stationInventoryExpanded, setStationInventoryExpanded] = useState(false);
  const [today] = useState(() => new Date().toISOString().slice(0, 10));
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { level, current: levelXp, requirement: levelRequirement } = pilotProgress(game.xp);
  const isPlaying = active === "battle" && runKey > 0 && !runResult;
  const taskWeekKey = (() => { const d = new Date(); const utc = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())); const day = utc.getUTCDay() || 7; utc.setUTCDate(utc.getUTCDate() + 4 - day); const yearStart = new Date(Date.UTC(utc.getUTCFullYear(), 0, 1)); const week = Math.ceil((((utc - yearStart) / 86400000) + 1) / 7); return `${utc.getUTCFullYear()}-W${String(week).padStart(2, "0")}`; })();
  const dailyStats = game.dailyTaskStats?.date === today ? game.dailyTaskStats : { date: today, clears: 0, crafted: 0, sold: 0 };
  const weeklyStats = game.weeklyTaskStats?.week === taskWeekKey ? game.weeklyTaskStats : { week: taskWeekKey, expeditions: 0, bosses: 0, creditsSpent: 0, chests: 0 };
  const baseStats = { health: 20, damage: 1, speed: 1, luck: 0.01 };
  const characterStats = useMemo(() => Object.fromEntries(Object.entries(baseStats).map(([key, base]) => [key, base * Math.pow(1.1, game.upgrades[key] ?? 0)])), [game.upgrades]);
  const dailyTaskDefinitions = [
    { id: "clear2", period: "daily", title: "Зачистка планеты", description: "Зачисти любую планету два раза.", progress: dailyStats.clears, target: 2, credits: 20, label: "20 кредитов" },
    { id: "craft5", period: "daily", title: "Мастер производства", description: "Изготовь пять предметов в мастерской.", progress: dailyStats.crafted, target: 5, credits: 50, label: "50 кредитов" },
    { id: "sell1", period: "daily", title: "Торговый обмен", description: "Продай один предмет из инвентаря станции.", progress: dailyStats.sold, target: 1, credits: 10, label: "10 кредитов" },
  ];
  const weeklyTaskDefinitions = [
    { id: "exp7", period: "weekly", title: "Дальний маршрут", description: "Заверши семь экспедиций.", progress: weeklyStats.expeditions, target: 7, orbitals: 15, label: "15 орбиталов" },
    { id: "boss10", period: "weekly", title: "Охотник на боссов", description: "Победи десять боссов.", progress: weeklyStats.bosses, target: 10, orbitals: 5, label: "5 орбиталов" },
    { id: "spend1000", period: "weekly", title: "Инвестиции в развитие", description: "Потрать 1000 кредитов на развитие и покупки.", progress: weeklyStats.creditsSpent, target: 1000, orbitals: 2, label: "2 орбитала" },
    { id: "chest7", period: "weekly", title: "Космический призыв", description: "Открой семь сундуков в Космическом призыве.", progress: weeklyStats.chests, target: 7, orbitals: 5, label: "5 орбиталов" },
  ];
  const achievementGroups = [
    { id: "exploration", title: "ИССЛЕДОВАНИЕ ПЛАНЕТ", items: sectors.filter((sector) => sector.id !== "earth").map((sector) => ({ id: `sector-${sector.id}`, title: `Открой сектор ${sector.name}`, progress: Number(game.sectors.includes(sector.id)), target: 1, reward: sector.id === "mars" ? 3 : 2, label: `${sector.id === "mars" ? 3 : 2} орбитала` })) },
    { id: "wealth", title: "БОГАЧ", items: [{ id: "spent500", title: "Потрать 500 кредитов", progress: game.creditsSpent || 0, target: 500, reward: 2, label: "2 орбитала" }, { id: "spent5000", title: "Потрать 5000 кредитов", progress: game.creditsSpent || 0, target: 5000, reward: 8, label: "8 орбиталов" }] },
    { id: "pilot", title: "ВЕЛИКИЙ ИССЛЕДОВАТЕЛЬ", items: [{ id: "pilot3", title: "Достигни 3 уровня пилота", progress: level, target: 3, reward: 2, label: "2 орбитала" }, { id: "pilot5", title: "Достигни 5 уровня пилота", progress: level, target: 5, reward: 5, label: "5 орбиталов" }, { id: "pilot10", title: "Достигни 10 уровня пилота", progress: level, target: 10, reward: 10, label: "10 орбиталов" }] },
    { id: "mutant", title: "МАСТЕР МУТАЦИИ", items: [{ id: "upgrade10", title: "Улучши характеристику до 10 уровня", progress: Math.max(0, ...["health", "damage", "speed", "luck"].map((key) => game.upgrades[key] ?? 0)), target: 10, reward: 3, label: "3 орбитала" }, { id: "upgrade50", title: "Доведи характеристику до 50 уровня", progress: Math.max(0, ...["health", "damage", "speed", "luck"].map((key) => game.upgrades[key] ?? 0)), target: 50, reward: 10, label: "10 орбиталов" }] },
  ];

  const telegramUser = typeof window !== "undefined" ? window.Telegram?.WebApp?.initDataUnsafe?.user ?? null : null;
  const visualPilotName = game.pilotName || telegramUser?.username || telegramUser?.first_name || "Космический пилот";
  const pilotAvatar = telegramUser?.photo_url || "";
  const pilotInitials = visualPilotName.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase() ?? "").join("") || "П";
  const currentSector = [...sectors].reverse().find((sector) => game.sectors.includes(sector.id)) ?? sectors[0];
  const equippedWeapon = weapons.find((weapon) => weapon.id === game.equippedWeapon) ?? weapons[0];
  const equippedSkin = skins.find((skin) => skin.id === game.equippedSkin) ?? skins[0];
  const selectedChest = gachaChests.find((chest) => chest.id === selectedChestId) ?? gachaChests[0];
  const battleWeapon = useMemo(() => ({ ...equippedWeapon, damage: equippedWeapon.damage + game.weaponBonus }), [equippedWeapon, game.weaponBonus]);
  const battleArmorBonus = Number(game.armorBonus) || 0;
  const battleMagnetBonus = game.artifacts.includes("magnet") ? 1 : 0;
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    tg?.ready();
    tg?.expand();
  }, []);

  useEffect(() => {
    const telegram = window.Telegram?.WebApp;
    const syncFullscreen = () => setIsFullscreen(Boolean(document.fullscreenElement || window.Telegram?.WebApp?.isFullscreen));
    document.addEventListener("fullscreenchange", syncFullscreen);
    telegram?.onEvent?.("fullscreenChanged", syncFullscreen);
    return () => {
      document.removeEventListener("fullscreenchange", syncFullscreen);
      telegram?.offEvent?.("fullscreenChanged", syncFullscreen);
    };
  }, []);

  function openNicknameEditor() {
    setNicknameDraft(game.pilotName || visualPilotName);
    setNicknameEditorOpen(true);
  }

  function commitGame(nextGame) {
    setGame(nextGame);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, game: nextGame }));
      setSaveError("");
    } catch {
      setSaveError("Не удалось сохранить прогресс. Проверьте свободное место и настройки приватности браузера.");
    }
  }

  const ownedStorageItems = useMemo(() => [
    ...game.weapons.map((id) => ({ id, category: "weapon", item: weapons.find((entry) => entry.id === id) })).filter((entry) => entry.item),
    ...game.skins.map((id) => ({ id, category: "armor", item: skins.find((entry) => entry.id === id) })).filter((entry) => entry.item),
    ...game.artifacts.filter((id) => baseArtifacts.some((entry) => entry.id === id)).map((id) => ({ id, category: "artifact", item: baseArtifacts.find((entry) => entry.id === id) })).filter((entry) => entry.item),
  ], [game.weapons, game.skins, game.artifacts]);
  const shipStorageCapacity = 20 + game.shipUpgrades.storage * 10;
  const stationStorageCapacity = 50;
  const shipStorageItems = ownedStorageItems.filter((entry) => game.shipStorage.includes(entry.id));
  const stationStorageItems = ownedStorageItems.filter((entry) => !game.shipStorage.includes(entry.id));
  const stationResourceDefs = [
    ["iron","Железо","⛓"],["copper","Медь","◈"],["titanium","Титан","⬡"],["aluminum","Алюминий","▰"],["uranium","Уран","☢"],
    ["ice","Водяной лёд","❄"],["helium3","Гелий-3","◉"],["silicon","Кремний","◇"],["scrap","Металлолом","⚙"],["electronics","Электронные компоненты","▦"],
    ["asterium","Астерий","✧"],["nebulite","Небулит","✦"],["coal","Уголь","▪"],["polymers","Полимеры","⬢"],
    ["plates","Железные пластины","▤"],["copperWire","Медные провода","⌁"],["aluminumPanel","Алюминиевые панели","▥"],["circuitBoard","Электронные платы","▦"],
    ["insulation","Изоляция","▧"],["reinforcedBeam","Усиленные балки","╋"],["data","Научные данные","⌕"],["ion_gel","Ионный гель","🧪"],
    ["xenoquartz","Ксенокварц","◇"],["phase_dust","Фазовая пыль","✴"],["plasma_threads","Плазменные нити","〰"],["biosilicate","Биосиликат","⌬"],
    ["graviton_cores","Гравитонные ядра","⚛"],["echo_shards","Эхо-осколки","◌"],["quantum_matrices","Квантовые матрицы","▦"],
    ["scanners","Сканеры","⌕"],["fuel","Топливо","⛽"],["dna","ДНК","✧"],["credits","Кредиты","◉"],["crystals","Кристаллы","✦"],["orbitals","Орбиталы","◎"]
  ];
  // Keep resource types from saves that may be newer than this client. Only known game
  // counters are excluded; unknown positive numeric inventory fields remain visible.
  const stationResourceKeySet = new Set(stationResourceDefs.map(([key]) => key));
  const nonResourceCounters = new Set(["xp","weaponBonus","armorBonus","expeditions","bossesDefeated","gachaPity","creditsSpent","accelerators"]);
  const extraSavedResourceDefs = Object.entries(game)
    .filter(([key, value]) => !stationResourceKeySet.has(key) && !nonResourceCounters.has(key) && Number.isFinite(value) && value > 0)
    .map(([key]) => [key, key.replace(/([a-z0-9])([A-Z])/g, "$1 $2").replace(/[_-]+/g, " ").replace(/^./, (letter) => letter.toUpperCase()), "◇"]);
  const completeStationResourceDefs = [...stationResourceDefs, ...extraSavedResourceDefs];
  const stationResourceSlots = completeStationResourceDefs.filter(([key]) => (Number(game[key]) || 0) > 0).length;
  const stationInventoryEntries = [
    { kind: "accelerator", key: "accelerators" },
    ...completeStationResourceDefs.filter(([key]) => (Number(game[key]) || 0) > 0).map(([key, label, icon]) => ({ kind: "resource", key, label, icon, count: Number(game[key]) || 0 }))
  ];
  const stationInventoryCells = Array.from({ length: 50 }, (_, index) => stationInventoryEntries[index] || null);
  // Render all 50 slots in both states; CSS clips the collapsed grid to exactly three rows.
  const visibleStationInventoryCells = stationInventoryCells;
  const sellableStationResources = completeStationResourceDefs.filter(([key]) => (Number(game[key]) || 0) > 0 && !["dna", "credits", "crystals", "orbitals"].includes(key));
  const shipResourceTotal = Object.values(game.shipResources || {}).reduce((sum, value) => sum + value, 0);
  const selectedResourceDef = stationResourceDefs.find(([key]) => key === selectedStationResource);
  function transferShipResources() {
    const cargo = game.shipResources || {};
    const incoming = Object.entries(cargo).filter(([, amount]) => amount > 0);
    const newKinds = incoming.filter(([key]) => !(game[key] > 0)).length;
    if (stationResourceSlots + newKinds > 50) { setMessage("На станции недостаточно свободных ячеек. Продай или используй часть ресурсов."); return; }
    const next = { ...game };
    incoming.forEach(([key, amount]) => { next[key] = (next[key] || 0) + amount; });
    next.shipResources = Object.fromEntries(Object.keys(cargo).map((key) => [key, 0]));
    commitGame(next);
    setMessage(incoming.length ? "Все ресурсы выгружены на станцию." : "Грузовой отсек пуст.");
  }
  function sellStationResource(key) {
    const amount = Math.max(0, Number(game[key]) || 0);
    if (!amount) return;
    const unitPrice = ({ iron:2,copper:3,silicon:4,coal:1,aluminum:4,polymers:3,plates:5,copperWire:4,aluminumPanel:7,circuitBoard:10,insulation:5,reinforcedBeam:8,fuel:2,titanium:8,uranium:12,ice:2,helium3:10,scrap:1,electronics:9,asterium:20,nebulite:18,ion_gel:12,xenoquartz:16,phase_dust:14,plasma_threads:14,biosilicate:8,graviton_cores:25,echo_shards:22,quantum_matrices:30 })[key] ?? 1;
    if (unitPrice <= 0) { setMessage("Этот ресурс нельзя продать."); return; }
    commitGame({ ...game, [key]: 0, credits: game.credits + amount * unitPrice });
    setSelectedStationResource("");
    setMessage(`Продано ${amount} ед. ресурса. Получено ${amount * unitPrice} кредитов.`);
  }

  function recordCreditSpend(nextGame, amount) {
    if (!amount || amount <= 0) return nextGame;
    return {
      ...nextGame,
      creditsSpent: (game.creditsSpent || 0) + amount,
      weeklyTaskStats: { ...weeklyStats, creditsSpent: weeklyStats.creditsSpent + amount },
    };
  }

  function upgradeShip(module) {
    const levelNow = game.shipUpgrades[module.id] ?? 0;
    const multiplier = levelNow + 1;
    const creditCost = module.baseCost * multiplier;
    const missing = Object.entries(module.materials).filter(([key, amount]) => (game[key] ?? 0) < amount * multiplier);
    if (levelNow >= 10) { setMessage("Улучшение достигло максимального уровня."); return; }
    if (game.credits < creditCost || missing.length) {
      const need = missing.map(([key, amount]) => `${amount * multiplier} ${resourceLabels[key]}`).join(", ");
      setMessage([game.credits < creditCost ? `Нужно ${creditCost} кредитов` : "", need ? `Не хватает: ${need}` : ""].filter(Boolean).join(". ") + ".");
      return;
    }
    const spent = Object.fromEntries(Object.entries(module.materials).map(([key, amount]) => [key, game[key] - amount * multiplier]));
    commitGame(recordCreditSpend({ ...game, ...spent, credits: game.credits - creditCost, shipUpgrades: { ...game.shipUpgrades, [module.id]: levelNow + 1 } }, creditCost));
    setMessage(`${module.name}: уровень ${levelNow + 1}. Списано ${creditCost} кредитов и материалы.`);
  }

  function moveStorageItem(id, toShip) {
    const nextShip = toShip ? [...game.shipStorage.filter((itemId) => itemId !== id), id] : game.shipStorage.filter((itemId) => itemId !== id);
    if (toShip && nextShip.length > shipStorageCapacity) { setMessage("Хранилище корабля заполнено. Улучши грузовой отсек."); return; }
    commitGame({ ...game, shipStorage: nextShip, stationStorage: toShip ? game.stationStorage.filter((itemId) => itemId !== id) : [...new Set([...game.stationStorage, id])] });
  }

  function sellStationItem(entry) {
    if (entry.category === "weapon" && entry.id === game.equippedWeapon) { setMessage("Нельзя продать установленное оружие. Сначала выбери другое."); return; }
    if (entry.category === "armor" && entry.id === game.equippedSkin) { setMessage("Нельзя продать надетую броню. Сначала выбери другой комплект."); return; }
    const price = entry.category === "weapon" ? Math.max(8, entry.item.damage) : entry.category === "armor" ? 12 : 15;
    const key = entry.category === "weapon" ? "weapons" : entry.category === "armor" ? "skins" : "artifacts";
    commitGame({ ...game, credits: game.credits + price, dailyTaskStats: { ...dailyStats, sold: dailyStats.sold + 1 }, [key]: game[key].filter((id) => id !== entry.id), shipStorage: game.shipStorage.filter((id) => id !== entry.id), stationStorage: game.stationStorage.filter((id) => id !== entry.id) });
    setMessage(`Продано: ${entry.item.name} · +${price} кредитов.`);
  }



  function buildPlanetDrill(sector) {
    const buildingId = `${sector.id}:drill`;
    if (game.planetBuildings.includes(buildingId)) { setMessage("На этой планете бур уже построен."); return; }
    if (game.credits < 1200 || game.iron < 100 || game.copper < 60) { setMessage("Для промышленного бура нужны 1200 кредитов, 100 железа и 60 меди."); return; }
    commitGame(recordCreditSpend({ ...game, credits: game.credits - 1200, iron: game.iron - 100, copper: game.copper - 60, planetBuildings: [...game.planetBuildings, buildingId] }, 1200));
    setMessage(`Промышленный бур построен на планете ${sector.name}.`);
  }

  function unlockSector(sector) {
    if (game.sectors.includes(sector.id)) return;
    if (game.xp < sector.unlockXp || game.credits < sector.cost) {
      setMessage(`Для открытия нужны ${sector.unlockXp} опыта и ${sector.cost} кредитов.`);
      return;
    }
    commitGame(recordCreditSpend({ ...game, credits: game.credits - sector.cost, sectors: [...game.sectors, sector.id] }, sector.cost));
    setMessage(`Сектор «${sector.name}» открыт!`);
  }

  function craft(recipe, requestedAmount = 1) {
    const isBlueprint = Boolean(recipe.blueprint);
    if (isBlueprint && (!game.blueprints.includes(recipe.blueprint) || game.craftedBlueprints.includes(recipe.blueprint))) return;

    const ingredients = recipeResources
      .map(({ key }) => [key, Math.max(0, Number(recipe[key]) || 0)])
      .filter(([, amount]) => amount > 0);
    const maxByResources = ingredients.length
      ? Math.min(...ingredients.map(([key, amount]) => Math.floor((Number(game[key]) || 0) / amount)))
      : 0;
    const amount = isBlueprint ? 1 : (requestedAmount === Infinity ? maxByResources : Math.min(maxByResources, Math.max(1, requestedAmount)));
    if (amount < 1) {
      setMessage(`Не хватает материалов для рецепта «${recipe.name}».`);
      return;
    }

    const nextGame = { ...game };
    for (const [key, perCraft] of ingredients) {
      nextGame[key] = Math.max(0, (Number(game[key]) || 0) - perCraft * amount);
    }
    for (const [key, perCraft] of Object.entries(recipe.output ?? {})) {
      nextGame[key] = Math.max(0, Number(nextGame[key]) || 0) + Math.max(0, Number(perCraft) || 0) * amount;
    }
    nextGame.weaponBonus = (Number(game.weaponBonus) || 0) + (recipe.weaponBonus ?? 0) * amount;
    nextGame.armorBonus = (Number(game.armorBonus) || 0) + (recipe.armorBonus ?? 0) * amount;
    nextGame.craftedBlueprints = isBlueprint ? [...game.craftedBlueprints, recipe.blueprint] : game.craftedBlueprints;
    nextGame.dailyTaskStats = { ...dailyStats, crafted: dailyStats.crafted + amount };

    commitGame(nextGame);
    setMessage(recipe.id === "fuel" ? `Запас топлива готов: +${10 * amount} топлива.` : `Готово: ${recipe.name} ×${amount}.`);
  }

  function startRun() {
    const planetIndex = Math.max(0, sectors.findIndex((sector) => sector.id === selectedPlanet));
    const difficultyLevel = sectors[planetIndex]?.threatLevel ?? 1;
    const fuelCost = 5 + planetIndex * 2;
    if (game.fuel < fuelCost) {
      setMessage(`Для зачистки ${sectors[planetIndex].name} нужно ${fuelCost} единиц топлива. Создай топливо в мастерской.`);
      return;
    }
    commitGame({ ...game, fuel: game.fuel - fuelCost });
    setRunResult(null);
    setRunKey((key) => key + 1);
    setActive("battle");
    setMessage("");
  }

  function finishRun(result) {
    const bossDNA = result.bossDefeated ? 1 : 0;
    const crystals = result.bossDefeated ? 5 : 0;
    const iron = result.bossDefeated ? 12 : Math.floor(result.kills / 5);
    const copper = result.bossDefeated ? 8 : Math.floor(result.kills / 7);
    const silicon = result.bossDefeated ? 5 : 0;
    const planetResourceKey = ({ earth: "coal", mercury: "aluminum", venus: "polymers", mars: "aluminum", jupiter: "polymers", saturn: "aluminum", uranus: "coal", neptune: "polymers" })[selectedPlanet] ?? "coal";
    const planetResourceAmount = result.bossDefeated ? 4 : Math.floor(result.kills / 4);
    const chestRewards = result.chestRewards && typeof result.chestRewards === "object" ? result.chestRewards : {};
    const chestCredits = Math.max(0, Math.floor(Number(result.chestCredits) || 0));
    const luckBonusChance = Math.min(0.10, Math.max(0, (characterStats.luck - 0.01) * 0.10));
    const creditDrops = Array.from({ length: Math.max(0, result.kills) }).filter(() => Math.random() < 0.10 + luckBonusChance).length;
    const credits = chestCredits + creditDrops * 5 + (result.bossDefeated ? 35 : 0);
    const rawXp = Number(result.xp);
    const xp = Math.max(0, Math.floor((Number.isFinite(rawXp) ? rawXp : (result.kills * 2 + (result.bossDefeated ? 40 : 0))) * 0.4));
    const acceleratorDrop = Math.random() < 0.05 + luckBonusChance;
    const artifactPool = artifacts.filter((item) => !game.artifacts.includes(item.id));
    const artifactDrop = result.bossDefeated && artifactPool.length && Math.random() < 0.05 + luckBonusChance
      ? artifactPool[Math.floor(Math.random() * artifactPool.length)]
      : null;
    const nextArtifacts = artifactDrop ? [...game.artifacts, artifactDrop.id] : game.artifacts;
    const nextShipResources = {
      ...game.shipResources,
      iron: (game.shipResources?.iron || 0) + iron,
      copper: (game.shipResources?.copper || 0) + copper,
      silicon: (game.shipResources?.silicon || 0) + silicon,
      [planetResourceKey]: (game.shipResources?.[planetResourceKey] || 0) + planetResourceAmount,
    };
    Object.entries(chestRewards).forEach(([key, amount]) => {
      const count = Math.max(0, Math.floor(Number(amount) || 0));
      if (count > 0) nextShipResources[key] = (Number(nextShipResources[key]) || 0) + count;
    });

    commitGame({
      ...game,
      artifacts: nextArtifacts,
      accelerators: (game.accelerators || 0) + Number(acceleratorDrop),
      dna: game.dna + bossDNA,
      crystals: game.crystals + crystals,
      shipResources: nextShipResources,
      credits: game.credits + credits,
      xp: game.xp + xp,
      expeditions: game.expeditions + 1,
      bossesDefeated: game.bossesDefeated + Number(result.bossDefeated),
      dailyTaskStats: { ...dailyStats, clears: dailyStats.clears + Number(result.won) },
      weeklyTaskStats: { ...weeklyStats, expeditions: weeklyStats.expeditions + Number(result.won), bosses: weeklyStats.bosses + Number(result.bossDefeated) },
    });
    setRunResult({
      ...result,
      dna: bossDNA,
      crystals,
      iron,
      copper,
      silicon,
      planetResourceKey,
      planetResourceAmount,
      chestRewards,
      chestCredits,
      credits,
      xp,
      artifactDrop: artifactDrop?.name ?? null,
      acceleratorDrop,
      creditDrops,
    });
    if (acceleratorDrop) setMessage("Редкая находка: ускоритель экспедиции! Шанс выпадения — 5%.");
    else if (artifactDrop) setMessage(`Редкая находка босса: ${artifactDrop.name}!`);
  }


  function buyAccelerators() {
    const cost = 100;
    if (game.orbitals < cost) {
      setMessage("Для покупки 10 ускорителей нужно 100 ОРБИТАЛОВ.");
      return;
    }
    commitGame({ ...game, orbitals: game.orbitals - cost, accelerators: (game.accelerators || 0) + 10 });
    setMessage("Куплено 10 ускорителей экспедиции.");
  }

  function useAccelerator() {
    const task = game.planetResearch;
    if (!task) { setMessage("Сейчас нет активного исследования, которое можно ускорить."); return; }
    if ((game.accelerators || 0) < 1) { setMessage("В инвентаре нет ускорителей."); return; }
    const now = Date.now();
    const reducedEndsAt = Math.max(now, Number(task.endsAt) - 30 * 60 * 1000);
    commitGame({ ...game, accelerators: game.accelerators - 1, planetResearch: { ...task, endsAt: reducedEndsAt } });
    setClockNow(now);
    setMessage(reducedEndsAt <= now ? "Ускоритель завершил оставшееся ожидание. Забери результат исследования!" : "Ускоритель применён: осталось на 30 минут меньше.");
  }

  function startPlanetResearch(sector, selectedHours = researchHours) {
    if (!game.sectors.includes(sector.id)) { setMessage("Сначала открой эту планету."); return; }
    if (game.planetResearch) { setMessage("Сначала забери результат текущего планетарного исследования."); return; }
    const index = sectors.indexOf(sector);
    const durationHours = selectedHours + Math.floor(index / 2) * 2;
    const fuelCost = 5 + index * 2;
    if (game.fuel < fuelCost) { setMessage(`Для экспедиции нужно ${fuelCost} топлива.`); return; }
    const startedAt = Date.now();
    commitGame({ ...game, fuel: game.fuel - fuelCost, planetResearch: { sectorId: sector.id, startedAt, endsAt: startedAt + durationHours * 60 * 60 * 1000, durationHours, fuelCost } });
    setMessage(`Исследование ${sector.name} началось на ${durationHours} ч. Прогресс сохранится после закрытия игры.`);
  }

  function collectPlanetResearch() {
    const task = game.planetResearch;
    if (!task) return;
    if (Date.now() < Number(task.endsAt)) { setMessage("Исследование ещё не завершено."); return; }
    const sector = sectors.find((entry) => entry.id === task.sectorId);
    if (!sector) { commitGame({ ...game, planetResearch: null }); return; }
    const index = sectors.indexOf(sector);
    const rewards = { iron: 2 + index, copper: 1 + Math.floor(index / 2), silicon: 1 + Math.floor(index / 3), coal: 0, aluminum: 0, polymers: 0, credits: 20 + index * 10, xp: 15 + index * 10 };
    const bonusKey = ({ earth: "coal", mercury: "aluminum", venus: "polymers", mars: "aluminum", jupiter: "polymers", saturn: "aluminum", uranus: "coal", neptune: "polymers" })[sector.id];
    rewards[bonusKey] = 2 + Math.floor(index / 2);
    const resourceRewards = Object.fromEntries(Object.entries(rewards).filter(([key]) => key !== "xp").map(([key, value]) => [key, game[key] + value]));
    commitGame({ ...game, ...resourceRewards, xp: game.xp + rewards.xp, planetResearch: null });
    setMessage(`Исследование ${sector.name} завершено: получены базовые руды, ${rewards[bonusKey]} ${resourceLabels[bonusKey]}, ${rewards.credits} кредитов и ${rewards.xp} XP.`);
  }

  function getResearchCost(moduleId) {
    const module = researchModules.find((entry) => entry.id === moduleId);
    if (!module) return 0;
    const level = game.upgrades[moduleId] ?? 0;
    return Math.max(6, Math.round(module.baseCost + level * module.scale * (level + 1)));
  }

  function getCharacterUpgradeCost(stat) {
    const currentLevel = game.upgrades[stat] ?? 0;
    return { credits: Math.ceil(100 * Math.pow(1.1, currentLevel)), dna: currentLevel + 1 };
  }

  function upgradeCharacter(stat) {
    const currentLevel = game.upgrades[stat] ?? 0;
    const cost = getCharacterUpgradeCost(stat);
    if (currentLevel >= 50) { setMessage("Характеристика достигла максимального уровня."); return; }
    if (game.credits < cost.credits || game.dna < cost.dna) {
      setMessage(`Для улучшения нужно ${cost.credits} кредитов и ${cost.dna} ДНК.`);
      return;
    }
    commitGame(recordCreditSpend({
      ...game,
      credits: game.credits - cost.credits,
      dna: game.dna - cost.dna,
      upgrades: { ...game.upgrades, [stat]: currentLevel + 1 },
    }, cost.credits));
    setMessage(`${stat === "health" ? "Живучесть" : stat === "damage" ? "Урон" : stat === "speed" ? "Скорость" : "Удача"} улучшена до ${currentLevel + 1} уровня.`);
  }

  function startAutonomousResearch(moduleId) {
    const module = researchModules.find((entry) => entry.id === moduleId);
    if (!module) return;
    if (game.labTask && Date.now() < Number(game.labTask.endsAt)) {
      setMessage("Автономное исследование уже запущено.");
      return;
    }
    if ((game.upgrades[moduleId] ?? 0) >= 10) {
      setMessage(`${module.name} уже доведён до максимального уровня.`);
      return;
    }
    const cost = getResearchCost(moduleId);
    const resourceValue = game[module.resource] ?? 0;
    if (resourceValue < module.baseCost || game.dna < cost) {
      setMessage(`Нужно ${module.baseCost} ${module.resource} и ${cost} ДНК для запуска ${module.name.toLowerCase()}.`);
      return;
    }
    const startedAt = Date.now();
    const endsAt = startedAt + module.durationMs;
    commitGame({
      ...game,
      [module.resource]: game[module.resource] - module.baseCost,
      dna: game.dna - cost,
      labTask: { id: moduleId, startedAt, endsAt },
    });
    setMessage(`Запущено автономное исследование: ${module.name}.`);
  }

  function collectAutonomousResearch() {
    if (!game.labTask) {
      setMessage("Нет активного исследования для сбора награды.");
      return;
    }
    if (Date.now() < Number(game.labTask.endsAt)) {
      setMessage("Исследование ещё не завершено.");
      return;
    }
    const module = researchModules.find((entry) => entry.id === game.labTask.id);
    if (!module) {
      commitGame({ ...game, labTask: null });
      return;
    }
    const level = game.upgrades[module.id] ?? 0;
    const rewardResources = {
      credits: 25 + level * 8,
      dna: 8 + level * 2,
      [module.resource]: Math.max(6, Math.round(module.baseCost * 0.8)),
    };
    commitGame({
      ...game,
      ...rewardResources,
      labTask: null,
      upgrades: { ...game.upgrades, [module.id]: Math.min(10, level + 1) },
    });
    setMessage(`Научный модуль обновлён: ${module.name}. Награда получена.`);
  }

  function summon(chest = selectedChest, free = false) {
    if (free ? game.dailyDraw === today : game.crystals < chest.cost) {
      setMessage(free ? "Бесплатная попытка уже использована сегодня." : `Для этого сундука нужно ${chest.cost} кристаллов.`);
      return;
    }
    const { item, highRarities } = drawGachaItem(chest, game.gachaPity);
    const category = weapons.some((entry) => entry.id === item.id) ? "weapon"
      : skins.some((entry) => entry.id === item.id) ? "skin" : "artifact";
    const ownedKey = category === "weapon" ? "weapons" : category === "skin" ? "skins" : "artifacts";
    const duplicate = game[ownedKey].includes(item.id);
    const nextGame = {
      ...game,
      crystals: game.crystals - (free ? 0 : chest.cost) + (duplicate ? 4 : 0),
      gachaPity: highRarities.includes(item.rarity) ? 0 : game.gachaPity + 1,
      dailyDraw: free ? today : game.dailyDraw,
      weeklyTaskStats: { ...weeklyStats, chests: weeklyStats.chests + 1 },
      [ownedKey]: duplicate ? game[ownedKey] : [...game[ownedKey], item.id],
    };
    commitGame(nextGame);
    setLastDrop({ ...item, category, duplicate });
    setChestHistory((history) => [{ id: `${Date.now()}-${Math.random()}`, chest: chest.name, name: item.name, rarity: item.rarity, category, duplicate, at: new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }) }, ...history].slice(0, 20));
    setMessage(duplicate ? `Повтор предмета «${item.name}»: возвращено 4 кристалла.` : `Выпало: ${item.name} · ${item.rarity}!`);
  }

  function summonWithOrbitals(chest, count) {
    const cost = count * 10;
    if (game.orbitals < cost) { setMessage(`Нужно ${cost} ОРБИТАЛОВ.`); return; }
    let next = { ...game, orbitals: game.orbitals - cost, weeklyTaskStats: { ...weeklyStats, chests: weeklyStats.chests + count } };
    const entries = [];
    for (let i=0;i<count;i++) {
      const { item, highRarities } = drawGachaItem(chest, next.gachaPity);
      const category = weapons.some((entry)=>entry.id===item.id)?"weapon":skins.some((entry)=>entry.id===item.id)?"skin":"artifact";
      const key = category === "weapon" ? "weapons" : category === "skin" ? "skins" : "artifacts";
      const duplicate = next[key].includes(item.id);
      next = { ...next, [key]: duplicate ? next[key] : [...next[key], item.id], crystals: next.crystals + (duplicate ? 4 : 0), gachaPity: highRarities.includes(item.rarity) ? 0 : next.gachaPity + 1 };
      entries.push({ id: `${Date.now()}-${i}-${Math.random()}`, chest: chest.name, name: item.name, rarity: item.rarity, category, duplicate, at: new Date().toLocaleTimeString("ru-RU", {hour:"2-digit",minute:"2-digit"}) });
    }
    commitGame(next); setChestHistory((history)=>[...entries.reverse(),...history].slice(0,20));
    setLastDrop({ ...gachaItems.find((item)=>item.name===entries[0]?.name), category: entries[0]?.category, duplicate: entries[0]?.duplicate });
    setMessage(`Открыто сундуков: ${count}. Результаты добавлены в историю.`);
  }

  function equip(category, id) {
    const key = category === "weapon" ? "equippedWeapon" : "equippedSkin";
    commitGame({ ...game, [key]: id });
    setMessage("Снаряжение установлено.");
  }

  function useReferral() {
    const code = inviteInput.trim().toUpperCase();
    if (game.referralClaimed) {
      setMessage("Бонус за приглашение уже получен.");
      return;
    }
    if (!code || code === game.referralCode) {
      setMessage("Введи код приглашения другого пилота.");
      return;
    }
    commitGame({ ...game, referralClaimed: true, crystals: game.crystals + 5, credits: game.credits + 100 });
    setInviteInput("");
    setMessage("Бонус прототипа получен: +5 кристаллов и +100 кредитов!");
  }

  async function copyReferral() {
    try {
      await navigator.clipboard.writeText(game.referralCode);
      setMessage("Код приглашения скопирован.");
    } catch {
      setMessage(`Твой код приглашения: ${game.referralCode}`);
    }
  }

  async function toggleFullscreen() {
    const telegram = window.Telegram?.WebApp;
    try {
      if (document.fullscreenElement || telegram?.isFullscreen) {
        if (telegram?.exitFullscreen) await telegram.exitFullscreen();
        else if (document.exitFullscreen) await document.exitFullscreen();
        return;
      }
      if (telegram?.requestFullscreen) {
        await telegram.requestFullscreen();
        return;
      }
      if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
      else setMessage("Полноэкранный режим недоступен. Добавь игру на главный экран браузера.");
    } catch {
      setMessage("Браузер не разрешил полный экран. Попробуй добавить игру на главный экран.");
    }
  }

  function createGuild() {
    const name = guildInput.trim();
    if (name.length < 3 || name.length > 24) {
      setMessage("Название гильдии должно содержать от 3 до 24 символов.");
      return;
    }
    if (game.guild) {
      setMessage("Ты уже состоишь в гильдии.");
      return;
    }
    if (game.orbitals < 100) {
      setMessage("Для создания гильдии нужно 100 ОРБИТАЛОВ.");
      return;
    }
    const tag = name.replace(/[^A-ZА-Я0-9]/gi, "").slice(0, 5).toUpperCase() || "PILOT";
    commitGame({ ...game, orbitals: game.orbitals - 100, guild: { name, tag, avatar: guildAvatar, category: guildCategory, members: 1, role: "Глава", level: 1, medals: 0 } });
    setGuildInput("");
    setMessage(`Гильдия «${name}» создана. Списано 100 ОРБИТАЛОВ (локальный прототип).`);
  }

  function joinGuild(guild) {
    commitGame({ ...game, guild: { ...guild, members: 1 } });
    setMessage(`Ты вступил в «${guild.name}» (локальный прототип).`);
  }

  function leaveGuild() {
    commitGame({ ...game, guild: null });
    setMessage("Ты покинул гильдию.");
  }

  function savePilotName() {
    const nextName = nicknameDraft.trim();
    const cleaned = nextName.replace(/[^\p{L}\p{N}\s_.-]/gu, "").slice(0, 16);
    if (!cleaned || cleaned.length < 2) {
      setMessage("Никнейм должен содержать от 2 до 16 символов.");
      return;
    }
    commitGame({ ...game, pilotName: cleaned });
    setNicknameEditorOpen(false);
    setMessage(`Никнейм обновлён: ${cleaned}`);
  }

  function addOrbitalReward(amount, reason) {
    const entry = { id: `${Date.now()}-${Math.random()}`, amount, reason, at: new Date().toISOString() };
    commitGame({ ...game, orbitals: game.orbitals + amount, orbitalHistory: [entry, ...(game.orbitalHistory || [])].slice(0, 30) });
    setMessage(`${reason}: +${amount} ОРБИТАЛОВ.`);
  }

  function claimDailyOrbitals() {
    if (game.dailyOrbitalClaim === today) return;
    const entry = { id: `${Date.now()}-daily`, amount: 2, reason: "Ежедневная награда", at: new Date().toISOString() };
    commitGame({ ...game, orbitals: game.orbitals + 2, dailyOrbitalClaim: today, orbitalHistory: [entry, ...(game.orbitalHistory || [])].slice(0, 30) });
    setMessage("Ежедневная награда получена: +2 ОРБИТАЛА.");
  }

  function claimExpeditionMilestone(milestone) {
    const id = `expeditions-${milestone}`;
    if (game.expeditions < milestone || (game.weeklyOrbitalClaims || []).includes(id)) return;
    const reward = milestone === 5 ? 5 : 10;
    const entry = { id: `${Date.now()}-${id}`, amount: reward, reason: `Достижение: ${milestone} экспедиций`, at: new Date().toISOString() };
    commitGame({ ...game, orbitals: game.orbitals + reward, weeklyOrbitalClaims: [...(game.weeklyOrbitalClaims || []), id], orbitalHistory: [entry, ...(game.orbitalHistory || [])].slice(0, 30) });
    setMessage(`Награда за ${milestone} экспедиций: +${reward} ОРБИТАЛОВ.`);
  }

  function buyOrbitalCosmetic(skin) {
    if (game.skins.includes(skin.id)) { setMessage("Этот внешний вид уже открыт."); return; }
    if (game.orbitals < skin.cost) { setMessage(`Не хватает ${skin.cost - game.orbitals} ОРБИТАЛОВ.`); return; }
    const entry = { id: `${Date.now()}-buy-${skin.id}`, amount: -skin.cost, reason: `Покупка косметики: ${skin.name}`, at: new Date().toISOString() };
    commitGame({ ...game, orbitals: game.orbitals - skin.cost, skins: [...game.skins, skin.id], orbitalHistory: [entry, ...(game.orbitalHistory || [])].slice(0, 30) });
    setMessage(`Открыт внешний вид «${skin.name}». Характеристики не изменены.`);
  }

  function purchaseOrbitalPack(pack) {
    setMessage(`Покупка ${pack.name} пока не подключена. Для цифровой валюты в Telegram Mini App потребуется оплата Telegram Stars и серверное подтверждение платежа. Орбиталы не начислены.`);
  }

  function resetGame() {
    if (!window.confirm("Сбросить весь прогресс этой экспедиции? Это действие нельзя отменить.")) return;
    const freshGame = { ...initialGame, referralCode: makeReferralCode() };
    commitGame(freshGame);
    setMessage("Начата новая экспедиция.");
  }

  return (
    <main className={`app-shell${isPlaying ? " battle-active" : ""}`}>
      {!isPlaying && <header className="topbar">
        <div className="brand-mark">OF</div>
        <div className="brand"><b>ORBITAL FRONTIER</b><span>Пиксельная экспедиция</span></div>
        <div className="topbar-currencies" aria-label="Текущий баланс" aria-live="polite">
          <span className="currency-pill currency-credits"><i aria-hidden="true">◈</i><small>КРЕДИТЫ</small><b>{Number(game.credits || 0).toLocaleString("ru-RU")}</b></span>
          <span className="currency-pill currency-crystals"><i aria-hidden="true">✦</i><small>КРИСТАЛЛЫ</small><b>{Number(game.crystals || 0).toLocaleString("ru-RU")}</b></span>
          <span className="currency-pill currency-orbitals"><i aria-hidden="true">◎</i><small>ОРБИТАЛЫ</small><b>{Number(game.orbitals || 0).toLocaleString("ru-RU")}</b></span>
        </div>
        <div className="topbar-actions">
          <button className="profile-button" onClick={() => setActive("profile")}>ПРОФИЛЬ</button>
          <button className="fullscreen-button" onClick={toggleFullscreen}>{isFullscreen ? "⛶ ВЫЙТИ" : "⛶ ПОЛНЫЙ ЭКРАН"}</button>
        </div>
      </header>}

      {!isPlaying && (message || saveError) && (
        <div className={saveError ? "notice error" : "notice"} role="status" aria-live="polite">
          <span>{saveError || message}</span>
          <button aria-label="Закрыть уведомление" onClick={() => { setMessage(""); setSaveError(""); }}>×</button>
        </div>
      )}

      {!isPlaying && nicknameEditorOpen && (
        <div className="panel nickname-modal" role="dialog" aria-modal="true">
          <div className="eyebrow">ИЗМЕНЕНИЕ НИКНЕЙМА</div>
          <h2>Сохрани новый позывной</h2>
          <input
            className="pixel-input"
            maxLength={16}
            value={nicknameDraft}
            onChange={(event) => setNicknameDraft(event.target.value)}
            placeholder="Личный позывной"
          />
          <div className="modal-actions">
            <button className="secondary-button" onClick={() => setNicknameEditorOpen(false)}>ОТМЕНА</button>
            <button className="primary-button" onClick={savePilotName}>СОХРАНИТЬ</button>
          </div>
        </div>
      )}

      {active === "home" && (
        <>
          <section className="home-console">
            <div className="home-welcome">
              <div className="pilot-avatar-wrap home-avatar">
                {pilotAvatar ? <img className="pilot-avatar" src={pilotAvatar} alt={visualPilotName} /> : <div className="pilot-avatar fallback">{pilotInitials}</div>}
              </div>
              <div className="pilot-meta">
                <div className="eyebrow">ПРОГРЕСС ПИЛОТА</div>
                <div className="pilot-name-row"><span className="pilot-name">{visualPilotName}</span><button className="text-button" onClick={openNicknameEditor}>ИЗМЕНИТЬ</button></div>
                <div className="pilot-level-row"><span>УРОВЕНЬ {level}</span><span className="muted">ПРОГРЕСС</span></div>
                <div className="progress-track compact"><div className="progress-fill" style={{ width: `${Math.min(100, (levelXp / levelRequirement) * 100)}%` }} /></div>
                <div className="muted">{levelXp} / {levelRequirement} XP</div>
              </div>
            </div>
          </section>

          <section className="pixel-base panel">
            <div className="section-heading"><div><div className="eyebrow">ЛИЧНЫЙ АНГАР</div><h2>Снаряжение пилота</h2></div></div>
            <div className="loadout-stage">
              <div className="gear-slot slot-suit" onClick={() => setGearModalCategory("armor")}><span>▣</span><b>БРОНЯ</b><small>{equippedSkin.name}</small></div>
              <div className="gear-slot slot-weapon" onClick={() => setGearModalCategory("weapon")}><span>⚔</span><b>ОРУЖИЕ</b><small>{equippedWeapon.name}</small></div>
              <div className="pixel-pilot-art" aria-label="Пиксельный персонаж пилота"><div className="pilot-helmet"></div><div className="pilot-arm left"></div><div className="pilot-arm right"></div><div className="pilot-body"></div><div className="pilot-leg left"></div><div className="pilot-leg right"></div><div className="pilot-pack"></div></div>
              <div className="gear-slot slot-artifact" onClick={() => setGearModalCategory("artifact")}><span>✧</span><b>АРТЕФАКТЫ</b><small>{game.artifacts.length} найдено</small></div>

            </div>
              <div className="pilot-quick-stats" aria-label="Текущие характеристики пилота">
                {[
                  { id: "health", label: "ЖИВУЧЕСТЬ", icon: "♥", value: characterStats.health.toFixed(1) },
                  { id: "damage", label: "УРОН", icon: "⚔", value: characterStats.damage.toFixed(2) },
                  { id: "speed", label: "СКОРОСТЬ", icon: "➤", value: characterStats.speed.toFixed(2) },
                  { id: "luck", label: "УДАЧА", icon: "✦", value: characterStats.luck.toFixed(4) },
                ].map((stat) => {
                  const statLevel = game.upgrades[stat.id] ?? 0;
                  return <div className="pilot-stat-row" key={stat.id}>
                    <div className="pilot-stat-level-line"><span>УР. {statLevel}/50</span><div className="pilot-stat-progress"><i style={{ width: `${Math.min(100, statLevel / 50 * 100)}%` }} /></div></div>
                    <div className="pilot-stat-value-line"><b>{stat.icon} {stat.label}</b><strong>{stat.value}</strong></div>
                  </div>;
                })}
              </div>
            <div className="home-shortcuts">
              <button onClick={() => setActive("lab")}><span>▦</span><b>ЛАБОРАТОРИЯ</b><small>Характеристики пилота</small></button>
              <button onClick={() => setActive("craft")}><span>⌬</span><b>МАСТЕРСКАЯ</b><small>Ресурсы и производство</small></button>
              <button onClick={() => setActive("station")}><span>▤</span><b>СТАНЦИЯ</b><small>Ресурсы и хранилище</small></button>
              <button onClick={() => setActive("ship")}><span>🚀</span><b>КОРАБЛЬ</b><small>Прокачка и трюм</small></button>
              <button onClick={() => setActive("tasks")}><span>☑</span><b>ЗАДАНИЯ</b><small>Цели и награды</small></button>
            </div>
          </section>
          <footer>ПИКСЕЛЬНАЯ ЭКСПЕДИЦИЯ · ПРОГРЕСС СОХРАНЯЕТСЯ ЛОКАЛЬНО</footer>
        </>
      )}

      {active === "battle" && !runResult && !runKey && (
        <section className="page-content expedition-page">
          <div className="eyebrow">НАВИГАЦИЯ · ИССЛЕДОВАТЕЛЬСКИЙ ФЛОТ</div>
          <h1>Экспедиции</h1>
          <p className="muted">Выбирай планету, отправляй исследовательскую группу и получай ресурсы. Исследование продолжается, даже если закрыть игру.</p>
          <div className="solar-map map-page expedition-map solar-system-art" aria-label="Карта Солнечной системы">
            <svg className="solar-orbits" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              {[14, 23, 32, 41, 49].map((radius) => <ellipse key={radius} cx="50" cy="50" rx={radius} ry={radius * 0.86} />)}
              <path d="M3 50H97 M50 3V97" className="orbit-axis" />
            </svg>
            <div className="solar-sun-art" aria-hidden="true"><span>✦</span><i /></div>
            {sectors.map((sector) => {
              const unlocked = game.sectors.includes(sector.id);
              const position = solarPositions[sector.id];
              const selected = selectedPlanet === sector.id;
              return <button
                type="button"
                key={sector.id}
                aria-label={`${sector.name}${unlocked ? ", доступна" : ", закрыта"}`}
                aria-pressed={selected}
                title={sector.name}
                className={`solar-world planet-${sector.id} ${selected ? "selected" : ""} ${!unlocked ? "locked" : ""}`}
                style={{ "--planet-left": `${position.x}%`, "--planet-top": `${position.y}%`, "--planet-size": `${position.size}px` }}
                onClick={() => setSelectedPlanet(sector.id)}
              >
                <span className="planet-art-wrap"><PlanetArtwork planetId={sector.id} /></span>
                <b>{sector.name}</b>
                <small>{unlocked ? "ДОСТУПНА" : "ЗАКРЫТА · 🔒"}</small>
              </button>;
            })}
          </div>
          {sectors.filter((sector)=>sector.id===selectedPlanet).map((sector)=>{
            const index=sectors.indexOf(sector); const unlocked=game.sectors.includes(sector.id);
            const danger=index<2?"Низкая":index<5?"Средняя":"Высокая";
            const baseHours=[4,6,8].includes(researchHours)?researchHours:4;
            const duration=baseHours+Math.floor(index/2)*2; const fuelCost=5+index*2;
            const task=game.planetResearch; const isTask=task?.sectorId===sector.id;
            const remaining=isTask?Math.max(0,task.endsAt-clockNow):0;
            const progress=isTask?Math.min(100,Math.max(0,((clockNow-task.startedAt)/(task.endsAt-task.startedAt))*100)):0;
            const hoursLeft=Math.floor(remaining/3600000); const minutesLeft=Math.floor((remaining%3600000)/60000);
            return <div className="panel planet-mission-card expedition-detail" key={sector.id}>
              <div className="eyebrow">{unlocked?"ЦЕЛЬ ЭКСПЕДИЦИИ":"НЕИССЛЕДОВАННЫЙ СЕКТОР"}</div>
              <h2 className="expedition-target-name">{sector.name}</h2>
              <p className="expedition-target-description">{sector.description}</p>
              <div className="expedition-combined-panel">
                <div className="expedition-threat-row">
                  <div className="expedition-threat-copy"><span className="eyebrow">УРОВЕНЬ УГРОЗЫ</span><b>СЛОЖНОСТЬ {sector.threatLevel}/6</b></div>
                  <span className="difficulty-segments expedition-threat-segments" aria-label={`Уровень угрозы ${sector.threatLevel} из 6`}>{[1,2,3,4,5,6].map(level => <i key={level} className={level<=sector.threatLevel?"active":""} />)}</span>
                </div>
                <div className="difficulty-description expedition-threat-description">{({1:"Обычные враги · пониженный урон",2:"Обычные враги · спавн +30%",3:"Обычные + элитные противники",4:"Обычные 20% · элитные 40%",5:"Элитные 60% · элитные II редко",6:"Элитные 40% · элитные II 30%"})[sector.threatLevel]}</div>
                <div className="expedition-resource-block"><b>РЕСУРСЫ</b><span>{planetDeposits[sector.id].join(" · ")}</span><div><span className="expedition-fuel-label">ТОПЛИВА ТРЕБУЕТСЯ</span><strong>⛽ {fuelCost}</strong></div></div>
              </div>
              <button className="primary-button planet-clear-button" disabled={!unlocked||game.fuel<fuelCost} onClick={startRun}>{!unlocked?"СНАЧАЛА ОТКРОЙ ПЛАНЕТУ":game.fuel>=fuelCost?`⚔ НАЧАТЬ ЗАЧИСТКУ · ${fuelCost} ТОПЛИВА`:`НУЖНО ${fuelCost} ТОПЛИВА`}</button>
              {!unlocked&&<button className="secondary-button" disabled={game.xp<sector.unlockXp||game.credits<sector.cost} onClick={()=>unlockSector(sector)}>ОТКРЫТЬ ПЛАНЕТУ · {sector.cost} ◈</button>}
              {unlocked&&!task&&<><div className="research-duration-picker"><div className="eyebrow">ДЛИТЕЛЬНОСТЬ ИССЛЕДОВАНИЯ</div><div className="duration-options">{[4,6,8].map(hours=><button type="button" key={hours} className={researchHours===hours?"selected":""} onClick={()=>setResearchHours(hours)}><b>{hours+Math.floor(index/2)*2} ч</b><small>{hours} ч база</small></button>)}</div><p className="muted">На этой планете: {duration} ч. На дальних и опасных планетах исследование дольше.</p></div><button className="primary-button" disabled={game.fuel<fuelCost} onClick={()=>startPlanetResearch(sector,researchHours)}>{game.fuel>=fuelCost?`НАЧАТЬ ИССЛЕДОВАНИЕ · ${fuelCost} ТОПЛИВА`: `НУЖНО ${fuelCost} ТОПЛИВА`}</button></>}
              {task&&<div className="research-active"><div className="research-active-heading"><b>⌬ ИССЛЕДУЕТСЯ: {sectors.find(x=>x.id===task.sectorId)?.name||"ПЛАНЕТА"}</b><strong>{Math.round(progress)}%</strong></div><div className="progress-track"><div className="progress-fill" style={{width:`${progress}%`}}/></div><p className="muted">{remaining>0?`Осталось: ${hoursLeft} ч ${minutesLeft} мин`:"Исследование завершено. Можно забрать результаты."}</p><div className="research-accelerator-row"><span>⏩ Ускорители в инвентаре: <b>{game.accelerators || 0}</b></span><button className="secondary-button" disabled={remaining<=0 || (game.accelerators || 0)<1} onClick={useAccelerator}>УСКОРИТЬ · −30 МИН</button></div>{remaining<=0&&<button className="primary-button" onClick={collectPlanetResearch}>ЗАБРАТЬ РЕЗУЛЬТАТЫ</button>}</div>}
              <div className="planet-building"><div className="eyebrow">ПЛАНЕТАРНАЯ ПРОМЫШЛЕННОСТЬ</div><p>Устанавливай стационарные модули для работы на выбранной планете.</p><button className="secondary-button" disabled={!game.sectors.includes(sector.id)} onClick={()=>setEquipmentModalOpen(true)}>УСТАНОВИТЬ ОБОРУДОВАНИЕ</button></div>
            </div>;
          })}
        </section>
      )}

      {active === "battle" && runResult && (
        <section className="page-content">
          <div className="eyebrow">{runResult.bossDefeated ? "БОСС ПОВЕРЖЕН" : runResult.won ? "ЗАЧИСТКА ЗАВЕРШЕНА" : "ПИЛОТ ВЫБЫЛ"}</div>
          <h1>{runResult.bossDefeated ? "Победа!" : "Экспедиция окончена"}</h1>
          <div className="panel run-summary">
            <p className="run-difficulty-result">УРОВЕНЬ СЛОЖНОСТИ: <b>{runResult.difficultyLevel || sectors.find((sector) => sector.id === selectedPlanet)?.threatLevel || 1}/6</b></p>
            <div className="run-summary-grid">
              <div><small>УРОН НАНЕСЁН</small><b>{Math.floor(runResult.damageDealt || 0)}</b></div>
              <div><small>УБИТО ВРАГОВ</small><b>{runResult.kills || 0}</b></div>
              <div><small>СУНДУКОВ СОБРАНО</small><b>{runResult.chestsCollected || 0}</b></div>
              <div><small>ПОЛУЧЕНО EXP</small><b>+{runResult.xp || 0}</b></div>
            </div>
            <div className="run-summary-section">
              <h3>НАГРАДЫ ЗА БОЙ</h3>
              <p>ДНК: <b>+{runResult.dna || 0}</b></p>
              <p>Кредиты: <b>+{runResult.credits || 0}</b> <span className="muted">(включая кредиты из сундуков)</span></p>
              {runResult.bossDefeated && <p className="boss-reward">Кристаллы босса: <b>+{runResult.crystals || 0}</b></p>}
              {runResult.artifactDrop && <p className="boss-reward">Артефакт босса: <b>{runResult.artifactDrop}</b> · шанс 5%</p>}
              {runResult.acceleratorDrop && <p className="boss-reward">⏩ Редкий ускоритель экспедиции: <b>+1</b> · шанс 5%</p>}
            </div>
            <div className="run-summary-section">
              <h3>РЕСУРСЫ ИЗ СУНДУКОВ</h3>
              {Object.entries(runResult.chestRewards || {}).length ? Object.entries(runResult.chestRewards).map(([key, amount]) => <p className="run-loot-line" key={key}><span>{resourceLabels[key] || key}</span><b>+{amount}</b></p>) : <p className="muted">Ресурсы из сундуков не получены.</p>}
              <p className="run-loot-line"><span>Кредиты из сундуков</span><b>+{runResult.chestCredits || 0}</b></p>
            </div>
            <div className="run-summary-section">
              <h3>ДОПОЛНИТЕЛЬНАЯ ДОБЫЧА БОССА</h3>
              <p>Железо <b>+{runResult.iron || 0}</b> · Медь <b>+{runResult.copper || 0}</b> · Кремний <b>+{runResult.silicon || 0}</b></p>
              <p>Местный ресурс: <b>+{runResult.planetResourceAmount || 0} {resourceLabels[runResult.planetResourceKey] || ""}</b></p>
            </div>
          </div>
          <button className="primary-button" onClick={() => { setRunResult(null); setRunKey((key) => key + 1); setActive("battle"); }}>ЕЩЁ ОДИН ВЫЛЕТ</button>
          <button className="secondary-button" onClick={() => { setRunResult(null); setRunKey(0); setActive("home"); }}>ВЕРНУТЬСЯ НА БАЗУ</button>
        </section>
      )}

      {active === "battle" && runKey > 0 && !runResult && (
        <PlanetRun
          key={runKey}
          planetId={selectedPlanet}
          difficultyLevel={sectors.find((sector) => sector.id === selectedPlanet)?.threatLevel ?? 1}
          stats={characterStats}
          armorBonus={battleArmorBonus}
          magnetBonus={battleMagnetBonus}
          weapon={battleWeapon}
          skin={equippedSkin}
          onFinish={finishRun}
          onExit={() => {
            if (!window.confirm("Вылет будет прерван без наград. Выйти с планеты?")) return;
            setRunResult(null);
            setRunKey(0);
            setActive("battle");
            setMessage("");
          }}
        />
      )}

      {active === "map" && (
        <section className="page-content">
          <div className="eyebrow">НАВИГАЦИЯ</div><h1>Солнечная система</h1>
          <p className="muted">Выбери планету на карте, чтобы изучить угрозы и доступные ресурсы.</p>
          <div className="solar-map map-page"><div className="solar-sun">☀</div>{sectors.map((sector,index) => {
            const unlocked = game.sectors.includes(sector.id); const canUnlock = game.xp >= sector.unlockXp && game.credits >= sector.cost;
            return <button key={sector.id} className={`solar-planet planet-${sector.id} ${selectedPlanet===sector.id?"selected":""} ${!unlocked?"locked":""}`} style={{"--planet-index":index}} onClick={() => { setSelectedPlanet(sector.id); if (!unlocked) setMessage(`Для открытия ${sector.name} нужны ${sector.unlockXp} XP и ${sector.cost} кредитов.`); }}><span className={`planet-ball ${sector.id}`}>●</span><b>{sector.name}</b>{!unlocked && <small>🔒</small>}</button>;
          })}</div>
          {sectors.filter((sector)=>sector.id===selectedPlanet).map((sector)=> <div className="panel planet-mission-card" key={sector.id}><div className="eyebrow">ПЛАНЕТА · {game.sectors.includes(sector.id)?"ДОСТУПНА":"ЗАКРЫТА"}</div><h2>{sector.name}</h2><p>{sector.description}</p><div className="mission-facts"><span>⚠ Опасность: {sectors.indexOf(sector)<2?"низкая":sectors.indexOf(sector)<5?"средняя":"высокая"}</span><span>📦 Месторождения: {planetDeposits[sector.id].join(" · ")}</span><span>⌛ Исследование: от 4 часов</span></div>{!game.sectors.includes(sector.id)&&<button className="secondary-button" disabled={game.xp<sector.unlockXp||game.credits<sector.cost} onClick={()=>unlockSector(sector)}>ОТКРЫТЬ · {sector.cost} ◈</button>}<button className="primary-button" disabled={!game.sectors.includes(sector.id)} onClick={()=>setActive("battle")}>ОТКРЫТЬ ЭКСПЕДИЦИИ</button><div className="planet-building"><div className="eyebrow">ПЛАНЕТАРНАЯ ПРОМЫШЛЕННОСТЬ</div><p>Устанавливай стационарные модули для работы на выбранной планете.</p><button className="secondary-button" disabled={!game.sectors.includes(sector.id)} onClick={()=>setEquipmentModalOpen(true)}>УСТАНОВИТЬ ОБОРУДОВАНИЕ</button></div></div>)}
        </section>
      )}

      {active === "ship" && (
        <section className="page-content ship-page">
          <div className="eyebrow">ЛИЧНЫЙ ТРАНСПОРТ · ТИР 1</div><h1>Корабль «Следопыт»</h1>
          <div className="panel ship-hero-panel">
            <div className="ship-art-wrap" role="img" aria-label="Пиксельный корабль первого тира"><div className="ship-art"><i className="ship-wing ship-wing-left"/><i className="ship-wing ship-wing-right"/><i className="ship-engine ship-engine-left"/><i className="ship-engine ship-engine-right"/><i className="ship-cockpit"/><i className="ship-core"/></div></div>
            <div className="ship-stats"><span>КОРПУС <b>ТИР 1 · {1 + game.shipUpgrades.hull * 20}%</b></span><span>ДВИГАТЕЛЬ <b>УРОВЕНЬ {game.shipUpgrades.engine}/10</b></span><span>РЕАКТОР <b>УРОВЕНЬ {game.shipUpgrades.reactor}/10</b></span><span>ТРЮМ <b>{shipStorageItems.length}/{shipStorageCapacity}</b></span></div>
          </div>
          <h2 className="subheading">МОДЕРНИЗАЦИЯ КОРАБЛЯ</h2>
          {[{id:"engine",name:"Ионный двигатель",icon:"➤",description:"Улучшает скорость перелёта между планетами.",baseCost:80,materials:{aluminumPanel:1,copperWire:1,iron:2}},{id:"hull",name:"Усиленный корпус",icon:"⬡",description:"Повышает прочность корабля.",baseCost:70,materials:{plates:2,reinforcedBeam:1}},{id:"reactor",name:"Реактор питания",icon:"ϟ",description:"Увеличивает энергетический резерв корабля.",baseCost:100,materials:{circuitBoard:1,copperWire:2,iron:2}},{id:"storage",name:"Грузовой отсек",icon:"▤",description:"Добавляет 10 ячеек хранилища за каждый уровень.",baseCost:90,materials:{aluminumPanel:1,plates:1,insulation:1}}].map((module)=>{const level=game.shipUpgrades[module.id];const multiplier=level+1;const materials=Object.entries(module.materials).map(([key,amount])=>`${amount*multiplier} ${resourceLabels[key]}`).join(" · ");const canUpgrade=level<10&&game.credits>=module.baseCost*multiplier&&!Object.entries(module.materials).some(([key,amount])=>(game[key]||0)<amount*multiplier);return <article className="panel ship-upgrade-card compact-ship-upgrade" key={module.id}><span className="item-icon">{module.icon}</span><div className="ship-upgrade-copy"><b>{module.name} · {level}/10</b><p className="upgrade-materials">МАТЕРИАЛЫ · {materials}</p><p className="ship-upgrade-description">{module.description}</p><small>◈ {module.baseCost*multiplier} КРЕДИТОВ</small></div><button className="secondary-button ship-upgrade-action" disabled={!canUpgrade} onClick={()=>upgradeShip(module)}>{level>=10?"МАКСИМУМ":"УЛУЧШИТЬ"}</button></article>})}
          <div className="panel storage-panel"><div className="section-heading"><div><div className="eyebrow">ЛИЧНЫЙ ТРЮМ</div><h2>Хранилище корабля</h2></div><span className="status-chip">{shipStorageItems.length}/{shipStorageCapacity}</span></div><p className="muted">Обычные артефакты, броня и оружие. Коллекционные реликвии хранятся отдельно.</p>{shipStorageItems.length===0&&<p className="muted">Трюм пока пуст. Перемести предметы со станции.</p>}{shipStorageItems.map((entry)=><div className="collection-row" key={entry.id}><div><b>{entry.item.name}</b><p>{entry.category==="weapon"?`Оружие · урон ${entry.item.damage}`:entry.category==="armor"?`Броня · ${entry.item.rarity}`:`Артефакт · ${entry.item.bonus}`}</p></div><button className="small-button" onClick={()=>moveStorageItem(entry.id,false)}>НА СТАНЦИЮ</button></div>)}</div>
        </section>
      )}

      {active === "station" && (
        <section className="page-content">
          <div className="eyebrow">ОРБИТАЛЬНЫЙ ДОК</div><h1>Станция «Атлас»</h1>
          <div className="panel station-overview"><div className="station-icon-art">▥</div><div><h2>Центральное хранилище</h2><p className="muted">Ресурсные ячейки · {stationResourceSlots}/50 занято</p><div className="progress-track"><div className="progress-fill" style={{width:`${Math.min(100,stationResourceSlots/50*100)}%`}}/></div></div></div>
          <div className="panel ship-cargo-panel"><div><h3>ГРУЗОВОЙ ОТСЕК КОРАБЛЯ</h3><p className="muted">Добытые во время зачисток ресурсы хранятся здесь до выгрузки.</p></div><b>{shipResourceTotal} ед.</b>{Object.entries(game.shipResources||{}).filter(([,amount])=>amount>0).map(([key,amount])=><span className="cargo-line" key={key}>{resourceLabels[key]||key} <b>{amount}</b></span>)}</div>
          <div className="station-resource-toolbar">
            <div className="station-resource-heading">
              <h2 className="subheading">ИНВЕНТАРЬ СТАНЦИИ</h2>
              <p className="muted">Ресурсы и расходные предметы. Ресурсная ёмкость — 50 ячеек.</p>
            </div>
            <button className="primary-button" disabled={shipResourceTotal===0} onClick={transferShipResources}>ПЕРЕНЕСТИ ВСЁ · {shipResourceTotal}</button>
          </div>
          <div className={`resource-grid station-resource-grid ${stationInventoryExpanded ? "expanded" : "collapsed"}`} aria-label="Инвентарь станции: 50 ячеек">
            {visibleStationInventoryCells.map((entry, index) => {
              if (!entry) return <div className="station-resource-cell station-empty-cell" key={`empty-${index}`} aria-hidden="true" />;
              if (entry.kind === "accelerator") return (
                <div className="resource-chip station-resource-cell station-accelerator-tile" key="accelerators" aria-label={`Ускоритель исследования: ${game.accelerators || 0}`}>
                  <span className="station-resource-icon accelerator-stock-image" role="img" aria-label="Ускоритель исследования">⏩</span>
                  <span>Ускоритель исследования</span>
                  <b>× {game.accelerators || 0}</b>
                </div>
              );
              return <button type="button" className="resource-chip station-resource-cell" key={entry.key} onClick={() => setSelectedStationResource(entry.key)}>
                <span className="station-resource-icon">{entry.icon}</span>
                <span>{entry.label}</span>
                <b>{entry.count}</b>
              </button>;
            })}
          </div>
          <button type="button" className="secondary-button station-inventory-toggle" onClick={() => setStationInventoryExpanded((value) => !value)}>{stationInventoryExpanded ? "▲ СВЕРНУТЬ ИНВЕНТАРЬ" : "▼ ПОКАЗАТЬ ВЕСЬ ИНВЕНТАРЬ"}</button>
          <div className="panel station-sell-panel"><div className="eyebrow">ТОРГОВЫЙ ТЕРМИНАЛ</div><h2>Продажа ресурсов</h2><p>Выбирай любой накопленный ресурс. Цена указана за всю стопку.</p><b>Баланс: {game.credits} кредитов</b><div className="station-resource-sales">{sellableStationResources.length ? sellableStationResources.map(([key,label,icon]) => { const amount = Number(game[key]) || 0; const unitPrice = ({iron:2,copper:3,silicon:4,coal:1,aluminum:4,polymers:3,plates:5,copperWire:4,aluminumPanel:7,circuitBoard:10,insulation:5,reinforcedBeam:8,fuel:2,titanium:8,uranium:12,ice:2,helium3:10,scrap:1,electronics:9,asterium:20,nebulite:18,ion_gel:12,xenoquartz:16,phase_dust:14,plasma_threads:14,biosilicate:8,graviton_cores:25,echo_shards:22,quantum_matrices:30})[key] ?? 1; return <div className="station-sale-row" key={key}><span>{icon} {label} · ×{amount}</span><b>◈ {amount*unitPrice}</b><button className="small-button sell-button" onClick={() => sellStationResource(key)}>ПРОДАТЬ</button></div>; }) : <p className="muted">Нет ресурсов для продажи.</p>}</div></div>
        </section>
      )}


      {active === "gacha" && (
        <section className="page-content gacha-page gacha-clean-page">
          <div className="gacha-heading">
            <div className="eyebrow">ФЛОТ · ТЕРМИНАЛ ПРИЗЫВА</div>
            <h1>Зал реликвий</h1>
            <div className="gacha-balance">◎ {game.orbitals} ОРБИТАЛОВ</div>
          </div>

          <div className="gacha-chest-list" aria-label="Выбор сундука">
            {gachaChests.map((chest) => (
              <div className={`gacha-chest-row ${selectedChest.id === chest.id ? "selected" : ""}`} key={chest.id}>
                <button
                  className={`gacha-chest ${selectedChest.id === chest.id ? "selected" : ""}`}
                  aria-pressed={selectedChest.id === chest.id}
                  onClick={() => setSelectedChestId(chest.id)}
                >
                  <span className="gacha-chest-icon" aria-hidden="true">{chest.icon}</span>
                  <span className="gacha-chest-copy"><b>{chest.name}</b><small>{chest.cost ?? 10} ◎ · {chest.id === "frontier" ? "Стартовый набор" : "Особые находки"}</small></span>
                  <span className="gacha-select-mark">{selectedChest.id === chest.id ? "▶" : "›"}</span>
                </button>
                <button
                  className="gacha-loot-button"
                  aria-label={`Список предметов: ${chest.name}`}
                  title="Список предметов"
                  onClick={() => { setSelectedChestId(chest.id); setLootChestId(chest.id); }}
                >
                  <span aria-hidden="true">▦</span><small>ЛУТ</small>
                </button>
              </div>
            ))}
          </div>

          <section className="gacha-selected-panel" aria-live="polite">
            <div className="gacha-selected-title">
              <span className="gacha-selected-icon">{selectedChest.icon}</span>
              <div><small>ВЫБРАН КОНТЕЙНЕР</small><h2>{selectedChest.name}</h2></div>
            </div>
            <p>{selectedChest.description}</p>
            <div className="gacha-open-grid">
              <button className="primary-button gacha-open-button" disabled={game.orbitals < 10} onClick={() => summonWithOrbitals(selectedChest, 1)}>
                ОТКРЫТЬ ×1 <b>10 ◎</b>
              </button>
              <button className="secondary-button gacha-open-button" disabled={game.orbitals < 100} onClick={() => summonWithOrbitals(selectedChest, 10)}>
                ОТКРЫТЬ ×10 <b>100 ◎</b>
              </button>
            </div>
            <button className="gacha-free-button" disabled={game.dailyDraw === today} onClick={() => summon(selectedChest, true)}>
              {game.dailyDraw === today ? "✓ БЕСПЛАТНАЯ ПОПЫТКА ИСПОЛЬЗОВАНА" : "БЕСПЛАТНО · 1 РАЗ В ДЕНЬ"}
            </button>
            <div className="gacha-pity">ГАРАНТИЯ: {Math.max(0, 10 - game.gachaPity)} ПРИЗЫВ(А)</div>
          </section>

          {lastDrop && <div className="panel drop-card" style={{ "--rarity-color": rarityTiers.find((tier) => tier.name === lastDrop.rarity)?.color }}>
            <span className="eyebrow">ПОСЛЕДНЯЯ НАХОДКА · {lastDrop.rarity}</span>
            <h2>{lastDrop.name}</h2>
            <p>{lastDrop.bonus ?? (lastDrop.damage ? `Урон ${lastDrop.damage}` : "Косметический костюм")}</p>
            <p className="muted">{lastDrop.duplicate ? "Повтор превращён в 4 кристалла." : "Предмет добавлен в коллекцию."}</p>
          </div>}

          <details className="panel chest-history gacha-history">
            <summary><span>ЖУРНАЛ ПРИЗЫВОВ</span><b>{chestHistory.length}</b></summary>
            {chestHistory.length ? chestHistory.map((entry) => <div className="collection-row" key={entry.id}><div><b>{entry.name}</b><p>{entry.chest} · {entry.at}</p></div><span className="rarity-label">{entry.rarity}{entry.duplicate ? " · повтор" : ""}</span></div>) : <p className="muted">История появится после открытия первого сундука.</p>}
          </details>
          <div className="prototype-note">Покупки в текущем прототипе обрабатываются локально.</div>

          {selectedResourceDef && (() => { const [key,label,icon] = selectedResourceDef; const amount = game[key] || 0; const price = ({iron:2,copper:3,silicon:4,coal:1,aluminum:4,polymers:3,plates:5,copperWire:4,aluminumPanel:7,circuitBoard:10,insulation:5,reinforcedBeam:8,fuel:2})[key] || 0; return <div className="gacha-modal-backdrop" role="presentation" onClick={(event)=>{if(event.target===event.currentTarget)setSelectedStationResource("");}}><div className="panel station-resource-modal" role="dialog" aria-modal="true"><button className="gacha-modal-close" onClick={()=>setSelectedStationResource("")}>×</button><div className="station-resource-icon modal-resource-icon">{icon}</div><div className="eyebrow">РЕСУРС СТАНЦИИ</div><h2>{label}</h2><p>Доступно на станции: <b>{amount}</b></p><p className="muted">Ресурс используется для изготовления предметов и модернизации корабля.</p><p className="muted">Цена продажи: {price ? `${price} кредитов за единицу` : "не продаётся"}</p><button className="primary-button" disabled={!price||amount===0} onClick={()=>sellStationResource(key)}>ПРОДАТЬ · {amount*price} ◈</button></div></div>; })()}
      {lootChestId && (() => {
            const lootChest = gachaChests.find((chest) => chest.id === lootChestId) ?? selectedChest;
            return <div className="gacha-modal-backdrop" role="presentation" onClick={(event) => { if (event.target === event.currentTarget) setLootChestId(""); }}>
              <section className="gacha-loot-modal" role="dialog" aria-modal="true" aria-label={`Предметы сундука ${lootChest.name}`}>
                <div className="gacha-modal-heading"><div><small>ТАБЛИЦА ДОБЫЧИ</small><h2>{lootChest.name}</h2></div><button className="gacha-modal-close" onClick={() => setLootChestId("")} aria-label="Закрыть список">×</button></div>
                <div className="gacha-modal-chances">{rarityTiers.map((tier, index) => lootChest.weights[index] > 0 && <span key={tier.name} style={{ "--rarity-color": tier.color }}><b>{tier.name}</b><small>{lootChest.weights[index]}%</small></span>)}</div>
                <div className="gacha-loot-list">
                  {lootChest.itemIds.map((id) => {
                    const item = gachaItems.find((entry) => entry.id === id);
                    if (!item) return null;
                    const category = weapons.some((entry) => entry.id === id) ? "ОРУЖИЕ" : skins.some((entry) => entry.id === id) ? "КОСТЮМ" : "АРТЕФАКТ";
                    const rarityColor = rarityTiers.find((tier) => tier.name === item.rarity)?.color;
                    return <div className="gacha-loot-row" key={id}><span className="gacha-loot-pixel" style={{ "--rarity-color": rarityColor }}>✦</span><span className="gacha-loot-name"><small>{category}</small><b>{item.name}</b></span><span className="rarity-label" style={{ "--rarity-color": rarityColor }}>{item.rarity}</span></div>;
                  })}
                </div>
                <button className="primary-button" onClick={() => setLootChestId("")}>НАЗАД К СУНДУКУ</button>
              </section>
            </div>;
          })()}
        </section>
      )}

      {active === "guild" && (
        <section className="page-content">
          <div className="eyebrow">ОТРЯД ПИЛОТА</div><h1>Гильдии и друзья</h1>
          <div className="prototype-note">Локальный прототип: гильдия видна только в этом сохранении. Для настоящего общего чата и участников нужен сервер.</div>
          {game.guild ? (
            <div className="panel guild-card"><span className="guild-emblem">{game.guild.avatar || "🛡️"}</span><div className="eyebrow">[{game.guild.tag}] · ЛОКАЛЬНАЯ</div><h2>{game.guild.name}</h2><p>{game.guild.category || "Универсальная"} · {game.guild.role || "Глава"}</p><p>Ты — первый пилот этой локальной гильдии.</p><div className="guild-stats"><span>Участники <b>1</b></span><span>Победы над боссами <b>{game.bossesDefeated}</b></span></div><button className="danger-button" onClick={leaveGuild}>ПОКИНУТЬ ГИЛЬДИЮ</button></div>
          ) : (
            <>
              <div className="panel guild-create-panel">
                <div className="eyebrow">ОСНОВАНИЕ ОТРЯДА</div><h2>Создать гильдию</h2>
                <p className="muted">Выбери название, эмблему и направление. Создание стоит 100 ОРБИТАЛОВ.</p>
                <label className="guild-field-label" htmlFor="guild-name">Название гильдии</label>
                <input id="guild-name" className="pixel-input" minLength={3} maxLength={24} placeholder="Например, Звёздный легион" value={guildInput} onChange={(event) => setGuildInput(event.target.value)} />
                <div className="guild-field-label">Аватарка гильдии</div>
                <div className="guild-avatar-picker">{["🛡️", "🚀", "☄️", "🌌", "⚔️", "👾", "🔱", "💠"].map((avatar) => <button type="button" key={avatar} aria-label={`Эмблема ${avatar}`} aria-pressed={guildAvatar === avatar} className={`guild-avatar-option ${guildAvatar === avatar ? "selected" : ""}`} onClick={() => setGuildAvatar(avatar)}>{avatar}</button>)}</div>
                <div className="guild-field-label">Категория</div>
                <div className="guild-category-picker">{["Общение", "Зачистки", "Прокачка", "Исследования", "Соревнования", "Универсальная"].map((category) => <button type="button" key={category} aria-pressed={guildCategory === category} className={`guild-category-option ${guildCategory === category ? "selected" : ""}`} onClick={() => setGuildCategory(category)}>{category}</button>)}</div>
                <div className="guild-create-cost"><span>Стоимость создания</span><strong>100 ◎ ОРБИТАЛОВ</strong><small>Твой баланс: {game.orbitals} ◎</small></div>
                <button className="primary-button" disabled={game.orbitals < 100 || guildInput.trim().length < 3} onClick={createGuild}>СОЗДАТЬ ГИЛЬДИЮ · 100 ◎</button>
              </div>
              <div className="panel"><h2>Каталог гильдий</h2><p className="muted">Публичный каталог появится после подключения Mini App к серверному API. Демонстрационные гильдии удалены, чтобы не вводить игроков в заблуждение.</p></div>
            </>
          )}
          <div className="panel invite-panel">
            <h2>Пригласи друга</h2>
            <p className="muted">Твой код: бонус за ввод чужого кода доступен один раз.</p>
            <div className="invite-code"><b>{game.referralCode}</b><button className="small-button" onClick={copyReferral}>КОПИРОВАТЬ</button></div>
            <p className="muted">У тебя есть чужой код?</p>
            <input className="pixel-input" maxLength={24} placeholder="Например, OF-ABC123" value={inviteInput} onChange={(event) => setInviteInput(event.target.value)} />
            <button className="primary-button" disabled={game.referralClaimed} onClick={useReferral}>{game.referralClaimed ? "БОНУС УЖЕ ПОЛУЧЕН" : "ПОЛУЧИТЬ БОНУС · +5 ✦ · +100 ◈"}</button>
            <p className="prototype-note">В демо код не проверяет другого реального игрока. Для реферальной системы нужна серверная проверка.</p>
          </div>
        </section>
      )}

      {active === "collection" && (
        <section className="page-content collection-page"><div className="eyebrow">АРХИВ КСЕНОАРТЕФАКТОВ</div><h1>Коллекции планет</h1><p className="muted">На каждой планете спрятано 5 уникальных реликвий. Собери полный набор и один раз получи 25 ОРБИТАЛОВ.</p>
          {sectors.map((sector) => {
            const planetArtifacts = artifacts.filter((item) => item.planetId === sector.id);
            const found = planetArtifacts.filter((item) => game.artifacts.includes(item.id)).length;
            const claimed = game.claimedCollections.includes(sector.id);
            return <details className="panel collection-planet" key={sector.id} open={sector.id === "earth"}>
              <summary><span className={`planet-ball ${sector.id}`}>●</span><span><b>{sector.name}</b><small>{found}/{planetArtifacts.length} реликвий</small></span><strong>{claimed ? "НАГРАДА ПОЛУЧЕНА" : found === planetArtifacts.length ? "КОМПЛЕКТ" : ""}</strong></summary>
              <div className="artifact-grid">{planetArtifacts.map((item, index) => { const owned = game.artifacts.includes(item.id); return <div className={`artifact-tile ${owned ? "found" : "undiscovered"}`} key={item.id}><span>{owned ? ["✦", "⌬", "◈", "✧", "❖"][index] : "?"}</span><b>{owned ? item.name : `Неизвестная реликвия #${index + 1}`}</b><small>{owned ? item.rarity : "Не обнаружена"}</small></div>})}</div>
              {found === planetArtifacts.length && <div className="set-reward">✦ Полный комплект · награда 25 ОРБИТАЛОВ {claimed ? "· уже получена" : <button className="small-button" onClick={() => { if (game.claimedCollections.includes(sector.id)) return; commitGame({ ...game, orbitals: game.orbitals + 25, claimedCollections: [...game.claimedCollections, sector.id] }); setMessage(`Комплект ${sector.name} собран: +25 ОРБИТАЛОВ.`); }}>ЗАБРАТЬ</button>}</div>}
            </details>;
          })}
        </section>
      )}

      {active === "donate" && (
        <section className="page-content donation-page">
          <div className="eyebrow">ЭКОНОМИКА ПИЛОТА</div><h1>ОРБИТАЛЫ</h1>
          <div className="panel orbital-wallet"><div><small>ТЕКУЩИЙ БАЛАНС</small><strong>◎ {game.orbitals}</strong></div><p>Орбиталы открывают косметику и дополнительные удобства. Основные планеты, сюжет и развитие корабля доступны бесплатно.</p></div>
          <div className="panel accelerator-donate-card"><div className="accelerator-donate-art">⏩</div><div className="accelerator-donate-copy"><div className="eyebrow">РАСХОДНИК · УСКОРЕНИЕ ИССЛЕДОВАНИЙ</div><h2>Ускоритель исследования</h2><p>Сокращает активное исследование планеты на 30 минут. Может выпасть после зачистки с шансом 5%.</p><b>В инвентаре: {game.accelerators || 0} шт.</b></div><div className="accelerator-donate-buy"><strong>10 шт. · 100 ◎</strong><button className="primary-button" disabled={game.orbitals < 100} onClick={buyAccelerators}>КУПИТЬ 10</button></div></div>
          <div className="panel orbital-free-panel"><div className="eyebrow">БЕСПЛАТНЫЕ НАГРАДЫ</div><h2>Получай орбиталы за игру</h2>
            <div className="orbital-reward-row"><div><b>Ежедневный бонус</b><small>Можно получить один раз в день</small></div><strong>+2 ◎</strong><button className="small-button" disabled={game.dailyOrbitalClaim === today} onClick={claimDailyOrbitals}>{game.dailyOrbitalClaim === today ? "ПОЛУЧЕНО" : "ЗАБРАТЬ"}</button></div>
            {[{n:5,r:5},{n:15,r:10}].map(({n,r})=><div className="orbital-reward-row" key={n}><div><b>{n} завершённых экспедиций</b><small>Твой прогресс: {Math.min(game.expeditions,n)}/{n}</small></div><strong>+{r} ◎</strong><button className="small-button" disabled={game.expeditions<n||(game.weeklyOrbitalClaims||[]).includes(`expeditions-${n}`)} onClick={()=>claimExpeditionMilestone(n)}>{(game.weeklyOrbitalClaims||[]).includes(`expeditions-${n}`)?"ПОЛУЧЕНО":game.expeditions>=n?"ЗАБРАТЬ":"В ПРОЦЕССЕ"}</button></div>)}
            <p className="muted">Орбиталы также выдаются за сюжетные главы, коллекции и специальные события.</p>
          </div>
          <div className="eyebrow section-eyebrow">МАГАЗИН КОСМЕТИКИ</div><h2>Внешний вид без преимущества в бою</h2>
          <div className="orbital-cosmetic-grid">{[{id:"amber",name:"Пустынный рейнджер",cost:30},{id:"lunar",name:"Лунный призрак",cost:60},{id:"exo",name:"Экзокостюм «Фантом»",cost:100},{id:"nebula",name:"Страж туманности",cost:160},{id:"chrono",name:"Хроноскафандр",cost:240}].map((skin)=><article className="panel orbital-cosmetic-card" key={skin.id}><b>{skin.name}</b><small>Косметический предмет · без бонусов характеристик</small><strong>{skin.cost} ◎</strong><button className="secondary-button" disabled={game.skins.includes(skin.id)||game.orbitals<skin.cost} onClick={()=>buyOrbitalCosmetic(skin)}>{game.skins.includes(skin.id)?"ОТКРЫТО":`КУПИТЬ · ${skin.cost} ◎`}</button></article>)}</div>
          <div className="eyebrow section-eyebrow">ПОКУПКА ОРБИТАЛОВ</div><p className="muted">Пакеты показаны как концепт. Реальная оплата пока не подключена; цифровые товары в Telegram Mini App будут продаваться через Telegram Stars после настройки бота и сервера.</p>
          <div className="donation-grid">{donationPackages.map((pack)=><button key={pack.id} className="donation-card" onClick={()=>purchaseOrbitalPack(pack)}><span className="donation-name">{pack.name}</span><strong>{pack.orbitals} ◎ ОРБИТАЛОВ</strong><small>Пакет оплаты · {pack.rubles} ₽ — концепт</small><em>ОПЛАТА СКОРО</em></button>)}</div>
          <div className="panel orbital-history"><div className="eyebrow">ИСТОРИЯ ОРБИТАЛОВ</div>{(game.orbitalHistory||[]).length===0?<p className="muted">Начисления и покупки появятся здесь.</p>:(game.orbitalHistory||[]).slice(0,8).map((entry)=><div className="orbital-history-row" key={entry.id}><span>{entry.reason}</span><b className={entry.amount<0?"negative":"positive"}>{entry.amount>0?"+":""}{entry.amount} ◎</b></div>)}</div>
        </section>
      )}

      {active === "profile" && (
        <section className="page-content">
          <div className="eyebrow">ЛИЧНОЕ ДЕЛО</div><h1>Профиль пилота</h1>
          <div className="panel profile-card">
            {pilotAvatar ? (
              <img className="avatar avatar-image" src={pilotAvatar} alt={visualPilotName} />
            ) : (
              <div className="avatar">{pilotInitials}</div>
            )}
            <h2>{visualPilotName}</h2>
            <p className="muted">ORBITAL FRONTIER · {equippedSkin.name}</p>
            <div className="profile-stats">
              <div><strong>{level}</strong><span>Уровень</span></div>
              <div><strong>{game.bossesDefeated}</strong><span>Боссы</span></div>
              <div><strong>{game.expeditions}</strong><span>Вылеты</span></div>
            </div>
            <button className="secondary-button profile-edit" onClick={openNicknameEditor}>ИЗМЕНИТЬ НИКНЕЙМ</button>
          </div>
          <div className="panel profile-summary">
            <div className="item-row"><span className="item-icon">⚔</span><div><b>Оружие</b><p>{equippedWeapon.name} · урон {equippedWeapon.damage + game.weaponBonus}</p></div></div>
            <div className="item-row"><span className="item-icon">♟</span><div><b>Гильдия</b><p>{game.guild?.name ?? "Не состоит"}</p></div></div>
            <div className="item-row"><span className="item-icon">✦</span><div><b>Коллекция</b><p>{game.weapons.length} оружия · {game.skins.length} костюма · {game.artifacts.length} артефакта</p></div></div>
            <div className="item-row"><span className="item-icon">⌁</span><div><b>Опыт</b><p>{game.xp} XP · {levelXp} / {levelRequirement} до следующего уровня</p></div></div>
          </div>
          <button className="danger-button" onClick={resetGame}>СБРОСИТЬ ПРОГРЕСС</button>
        </section>
      )}

      {active === "tasks" && (
        <section className="page-content tasks-page">
          <div className="eyebrow">ПРОТОКОЛЫ ПИЛОТА</div><h1>Задания</h1>
          <p className="muted">Выполняй ежедневные и еженедельные цели. Достижения остаются с пилотом навсегда.</p>
          {[{ id: "daily", title: "ЕЖЕДНЕВНЫЕ ЗАДАНИЯ", tasks: dailyTaskDefinitions, cycle: today }, { id: "weekly", title: "ЕЖЕНЕДЕЛЬНЫЕ ЗАДАНИЯ", tasks: weeklyTaskDefinitions, cycle: taskWeekKey }].map((group) => (
            <section className="task-group" key={group.id}><h2 className="subheading">{group.title}</h2><div className="task-grid">
              {group.tasks.map((task) => { const claimKey = `${group.id}:${group.cycle}:${task.id}`; const complete = task.progress >= task.target; const claimed = game.claimedTasks.includes(claimKey); return (
                <article className="panel task-card" key={task.id}>
                  <div className="task-card-heading"><b>{task.title}</b><span className={task.orbitals ? "currency-orbitals" : "currency-credits"}>{task.label}</span></div><p>{task.description}</p>
                  <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(100, task.progress / task.target * 100)}%` }} /></div>
                  <small className="muted">ПРОГРЕСС · {Math.min(task.progress, task.target)}/{task.target}</small>
                  <button className="secondary-button" disabled={!complete || claimed} onClick={() => { const next = { ...game, credits: game.credits + (task.credits || 0), orbitals: game.orbitals + (task.orbitals || 0), claimedTasks: [...game.claimedTasks, claimKey] }; commitGame(next); setMessage(`Награда получена: ${task.label}.`); }}>{claimed ? "ПОЛУЧЕНО" : complete ? "ЗАБРАТЬ НАГРАДУ" : "В ПРОЦЕССЕ"}</button>
                </article>);
              })}
            </div>
            {group.id === "daily" && <button className="primary-button daily-bonus-button" disabled={!dailyTaskDefinitions.every((task) => game.claimedTasks.includes(`daily:${today}:${task.id}`)) || game.claimedTasks.includes(`daily:${today}:all`)} onClick={() => { commitGame({ ...game, orbitals: game.orbitals + 5, claimedTasks: [...game.claimedTasks, `daily:${today}:all`] }); setMessage("Все ежедневные задания выполнены: +5 ОРБИТАЛОВ."); }}>{game.claimedTasks.includes(`daily:${today}:all`) ? "ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН" : "БОНУС ЗА ВСЕ ЗАДАНИЯ · 5 ◎"}</button>}
            </section>
          ))}
          <div className="eyebrow section-eyebrow">ПОСТОЯННЫЙ ПРОГРЕСС</div><h2>ДОСТИЖЕНИЯ</h2>
          {achievementGroups.map((group) => <section className="task-group" key={group.id}><h3 className="subheading">{group.title}</h3><div className="task-grid achievement-grid">{group.items.map((task) => { const claimKey = `achievement:${task.id}`; const complete = task.progress >= task.target; const claimed = game.claimedTasks.includes(claimKey); return (
            <article className="panel task-card achievement-card" key={task.id}><div className="task-card-heading"><b>{task.title}</b><span className="currency-orbitals">{task.label}</span></div><div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(100, task.progress / task.target * 100)}%` }} /></div><small className="muted">ПРОГРЕСС · {Math.min(task.progress, task.target)}/{task.target}</small><button className="secondary-button" disabled={!complete || claimed} onClick={() => { commitGame({ ...game, orbitals: game.orbitals + task.reward, claimedTasks: [...game.claimedTasks, claimKey] }); setMessage(`Достижение получено: +${task.reward} ОРБИТАЛОВ.`); }}>{claimed ? "ПОЛУЧЕНО" : complete ? "ЗАБРАТЬ" : "В ПРОЦЕССЕ"}</button></article>
          ); })}</div></section>)}
          <p className="muted">Ежедневные задания обновляются каждый день, еженедельные — каждую неделю. Достижения не сбрасываются.</p>
        </section>
      )}

      {active === "lab" && (
        <section className="page-content lab-page">
          <div className="eyebrow">ЦЕНТР РАЗВИТИЯ ПИЛОТА</div>
          <h1>Лаборатория</h1>
          <p className="muted lab-intro">Каждый уровень повышает базовую характеристику на 10%. Максимум — 50 уровней на каждую характеристику.</p>
          <div className="lab-balance panel"><span>ДОСТУПНО ДНК</span><b>🧬 {game.dna}</b><span className="lab-credit-balance">КРЕДИТЫ</span><b>◈ {game.credits}</b></div>
          {[{id:"health",name:"Живучесть",icon:"♥",desc:"Увеличивает запас здоровья пилота."},{id:"damage",name:"Урон",icon:"⚔",desc:"Усиливает автоматическую атаку."},{id:"speed",name:"Скорость",icon:"➤",desc:"Ускоряет передвижение по полю боя."},{id:"luck",name:"Удача",icon:"✦",desc:"Повышает шанс ценных находок."}].map((stat) => {
            const statLevel = game.upgrades[stat.id] ?? 0;
            const cost = getCharacterUpgradeCost(stat.id);
            const canUpgrade = statLevel < 50 && game.credits >= cost.credits && game.dna >= cost.dna;
            return <article className="panel lab-upgrade-card" key={stat.id}>
              <div className="lab-stat-top"><span className="lab-stat-icon">{stat.icon}</span><div><b>{stat.name}</b><small>{stat.desc}</small></div><strong>УР. {statLevel}/50</strong></div>
              <div className="lab-current-value">ТЕКУЩЕЕ ЗНАЧЕНИЕ: <b>{characterStats[stat.id].toFixed(stat.id === "luck" ? 4 : 2)}</b> · +10% за уровень</div>
              <div className="progress-track"><div className="progress-fill" style={{width:`${statLevel*2}%`}} /></div>
              <div className="lab-upgrade-cost"><span>◈ {cost.credits} кредитов</span><span>🧬 {cost.dna} ДНК</span></div>
              <button className={`primary-button large-touch-button ${canUpgrade ? "" : "is-unavailable"}`} disabled={!canUpgrade} onClick={() => upgradeCharacter(stat.id)}>{statLevel >= 50 ? "МАКСИМАЛЬНЫЙ УРОВЕНЬ" : canUpgrade ? "УЛУЧШИТЬ" : `НЕ ХВАТАЕТ РЕСУРСОВ · ◈ ${cost.credits} · 🧬 ${cost.dna}`}</button>
            </article>;
          })}
          <section className="panel lab-character-summary"><div className="eyebrow">ПИЛОТ · ТЕКУЩИЕ ХАРАКТЕРИСТИКИ</div><h2>Статистики персонажа</h2><div className="lab-character-stat-grid">
            {[{id:"health",name:"Живучесть",icon:"♥",digits:2},{id:"damage",name:"Урон",icon:"⚔",digits:2},{id:"speed",name:"Скорость",icon:"➤",digits:2},{id:"luck",name:"Удача",icon:"✦",digits:4}].map((stat)=><div className="lab-character-stat" key={stat.id}><span>{stat.icon}</span><small>{stat.name}</small><b>{characterStats[stat.id].toFixed(stat.digits)}</b><em>УР. {game.upgrades[stat.id]}/50</em></div>)}
          </div></section>
          <button className="secondary-button large-touch-button" onClick={() => setActive("craft")}>ПЕРЕЙТИ В МАСТЕРСКУЮ</button>
        </section>
      )}

      {active === "craft" && (
        <section className="page-content"><div className="eyebrow">ПРОИЗВОДСТВО</div><h1>Мастерская</h1>
          <div className="recipe-grid">
            {[...recipes, ...blueprintRecipes.map((recipe) => ({ ...recipe, blueprint: recipe.id }))].map((recipe) => {
              if (recipe.blueprint && !game.blueprints.includes(recipe.blueprint)) return null;
              const crafted = recipe.blueprint && game.craftedBlueprints.includes(recipe.blueprint);
              const ingredients = recipeResources.filter(({ key }) => (recipe[key] ?? 0) > 0);
              const maxCraft = ingredients.length ? Math.min(...ingredients.map(({ key }) => Math.floor((Number(game[key]) || 0) / (recipe[key] || 1)))) : 0;
              const available = maxCraft >= 1 && !crafted;
              return <article className="panel recipe-card" key={recipe.id}>
                <div className="recipe-card-heading">
                  <span className="recipe-item-icon" aria-hidden="true">{recipe.icon ?? "▧"}</span>
                  <div className="recipe-item-copy"><b>{recipe.name}</b></div>
                </div>
                <div className="recipe-requirements">
                  <span className="recipe-section-label">ТРЕБОВАНИЯ ДЛЯ КРАФТА</span>
                  {recipe.description && <small className="recipe-description">{recipe.description}</small>}
                </div>
                <div className="recipe-composition">
                  <span className="recipe-section-label">СОСТАВ · РЕСУРСЫ</span>
                  <div className="recipe-ingredients" aria-label="Необходимые ресурсы">
                  {ingredients.map(({ key, label, icon }) => {
                    const amount = recipe[key] ?? 0;
                    const enough = game[key] >= amount;
                    return <span className={`ingredient-chip ${enough ? "is-enough" : "is-short"}`} key={key} title={`${label}: нужно ${amount}, есть ${game[key]}`}>
                      <span className="ingredient-icon">{icon}</span><span className="ingredient-count">×{amount}</span>
                    </span>;
                  })}
                  </div>
                </div>
                <div className="recipe-actions">
                  {crafted ? <button className="primary-button recipe-action" disabled>ИЗГОТОВЛЕНО</button> : <>
                    <button className="primary-button recipe-action" disabled={!available} onClick={() => craft(recipe, 1)}>СОЗДАНИЕ</button>
                    {!recipe.blueprint && <>
                      <button className="primary-button recipe-action" disabled={maxCraft < 5} onClick={() => craft(recipe, 5)}>×5</button>
                      <button className="primary-button recipe-action" disabled={maxCraft < 10} onClick={() => craft(recipe, 10)}>×10</button>
                      <button className="primary-button recipe-action recipe-all-action" disabled={!available} onClick={() => craft(recipe, Infinity)}>ВСЁ · {maxCraft}</button>
                    </>}
                  </>}
                </div>
              </article>;
            })}
          </div>
        </section>
      )}

      {equipmentModalOpen && <div className="modal-backdrop" role="presentation" onClick={()=>setEquipmentModalOpen(false)}><section className="panel equipment-modal" role="dialog" aria-modal="true" aria-label="Планетарное оборудование" onClick={event=>event.stopPropagation()}><div className="section-heading"><div><div className="eyebrow">ПЛАНЕТАРНАЯ ПРОМЫШЛЕННОСТЬ</div><h2>Оборудование · {sectors.find(item=>item.id===selectedPlanet)?.name||"Планета"}</h2></div><button className="small-button" onClick={()=>setEquipmentModalOpen(false)}>ЗАКРЫТЬ</button></div><article className="equipment-option"><div><b>⛏ Промышленный бур</b><p>Стационарная установка для добычи ресурсов на выбранной планете.</p><small>Требуется: 1200 кредитов · 100 железа · 60 меди</small></div><button className="secondary-button" disabled={!game.sectors.includes(selectedPlanet)||game.planetBuildings.includes(`${selectedPlanet}:drill`)||game.credits<1200||game.iron<100||game.copper<60} onClick={()=>{const sector=sectors.find(item=>item.id===selectedPlanet);if(sector)buildPlanetDrill(sector);}}>{game.planetBuildings.includes(`${selectedPlanet}:drill`)?"УСТАНОВЛЕНО":"УСТАНОВИТЬ"}</button></article></section></div>}
      {gearModalCategory && <div className="modal-backdrop" role="presentation" onClick={() => setGearModalCategory("")}><section className="panel equipment-modal gear-category-modal" role="dialog" aria-modal="true" aria-label="Инвентарь снаряжения" onClick={event => event.stopPropagation()}><div className="section-heading"><div><div className="eyebrow">ИНВЕНТАРЬ ПИЛОТА</div><h2>{gearModalCategory==="weapon"?"Доступное оружие":gearModalCategory==="armor"?"Доступная броня":"Найденные артефакты"}</h2></div><button className="small-button" onClick={() => setGearModalCategory("")}>ЗАКРЫТЬ</button></div>{ownedStorageItems.filter(entry => entry.category===gearModalCategory).length ? ownedStorageItems.filter(entry => entry.category===gearModalCategory).map(entry => <article className="equipment-option gear-option" key={entry.id}><div><b>{entry.item.name}</b><p>{gearModalCategory==="weapon"?`Урон: ${entry.item.damage}`:gearModalCategory==="armor"?`Редкость: ${entry.item.rarity}`:`${entry.item.rarity} · ${entry.item.bonus}`}</p><small>{game.shipStorage.includes(entry.id)?"В трюме корабля":"На станции"}</small></div>{gearModalCategory==="weapon"||gearModalCategory==="armor"?<button className="secondary-button" disabled={(gearModalCategory==="weapon"&&game.equippedWeapon===entry.id)||(gearModalCategory==="armor"&&game.equippedSkin===entry.id)} onClick={() => { equip(gearModalCategory,entry.id); setGearModalCategory(""); }}>{(gearModalCategory==="weapon"&&game.equippedWeapon===entry.id)||(gearModalCategory==="armor"&&game.equippedSkin===entry.id)?"УСТАНОВЛЕНО":"ЭКИПИРОВАТЬ"}</button>:<span className="status-chip">НАЙДЕН</span>}</article>) : <p className="muted">Предметов этой категории пока нет.</p>}</section></div>}

      {!isPlaying && <>
        {moreMenuOpen && <div className="more-menu" role="dialog" aria-label="Дополнительные разделы">
          {extraTabs.map((tab) => <button key={tab.id} className={active === tab.id ? "more-menu-item active" : "more-menu-item"} onClick={() => { setActive(tab.id); setMoreMenuOpen(false); setRunResult(null); setRunKey(0); setMessage(""); }}><span>{tab.icon}</span><b>{tab.label}</b></button>)}
        </div>}
        <nav className="bottom-nav" aria-label="Разделы игры">
          {tabs.map((tab) => <button key={tab.id} className={(active === tab.id || (tab.id === "more" && extraTabs.some((extra) => extra.id === active))) ? "nav-item active" : "nav-item"} aria-current={active === tab.id ? "page" : undefined} onClick={() => {
            if (tab.id === "more") { setMoreMenuOpen((open) => !open); return; }
            if (active === "battle" && runKey > 0 && !runResult && !window.confirm("Вылет будет прерван без наград. Выйти с планеты?")) return;
            setMoreMenuOpen(false); setActive(tab.id); setRunResult(null); setRunKey(0); setMessage("");
          }}><span>{tab.icon}</span><small>{tab.label}</small></button>)}
        </nav>
      </>}
    </main>
  );
}

export default App;
