import { useEffect, useRef, useState } from "react";

const WIDTH = 420;
const HEIGHT = 760;
const BOSS_AT = 60;
const RUN_DURATION = 120;

const planetChestResources = {
  earth: ["iron", "copper", "silicon", "coal", "biosilicate"],
  mercury: ["iron", "aluminum", "titanium", "silicon"],
  venus: ["aluminum", "polymers", "uranium", "ion_gel"],
  mars: ["iron", "aluminum", "titanium", "scrap"],
  jupiter: ["helium3", "polymers", "electronics", "plasma_threads"],
  saturn: ["ice", "helium3", "scrap", "nebulite"],
  uranus: ["ice", "uranium", "nebulite", "phase_dust"],
  neptune: ["ice", "nebulite", "phase_dust", "xenoquartz"],
};

const planets = {
  earth: { name: "Земля", ground: "#182b35", grid: "#233b41", enemy: "#8bb869", boss: "#d5a25e" },
  mercury: { name: "Меркурий", ground: "#332a25", grid: "#514136", enemy: "#d5a16e", boss: "#f1cf85" },
  venus: { name: "Венера", ground: "#38251f", grid: "#59392a", enemy: "#d77b54", boss: "#f0b36b" },
  mars: { name: "Марс", ground: "#35232b", grid: "#56323a", enemy: "#c66d63", boss: "#f1a16e" },
  jupiter: { name: "Юпитер", ground: "#302a35", grid: "#4d3d49", enemy: "#c79c82", boss: "#f1c37b" },
  saturn: { name: "Сатурн", ground: "#292c3b", grid: "#41475a", enemy: "#d1b978", boss: "#f0d89b" },
  uranus: { name: "Уран", ground: "#1e3039", grid: "#2c4b54", enemy: "#82c9c8", boss: "#b5e8e1" },
  neptune: { name: "Нептун", ground: "#1c263f", grid: "#2b3b60", enemy: "#7598ee", boss: "#b0c9ff" },
};

function pixelRect(context, x, y, width, height, color) {
  context.fillStyle = color;
  context.fillRect(Math.round(x / 4) * 4, Math.round(y / 4) * 4, width, height);
}

function createPlanetTerrain(planetId) {
  const terrain = document.createElement("canvas");
  terrain.width = WIDTH;
  terrain.height = HEIGHT;
  const ctx = terrain.getContext("2d");
  if (!ctx) return terrain;
  const palette = planets[planetId] || planets.earth;
  let seed = [...String(planetId)].reduce((value, char) => ((value * 31) + char.charCodeAt(0)) >>> 0, 2166136261);
  const random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const patch = (color, count, minSize = 8, maxSize = 32) => {
    ctx.fillStyle = color;
    for (let i = 0; i < count; i += 1) {
      const size = minSize + Math.floor(random() * (maxSize - minSize + 1));
      const x = Math.floor(random() * (WIDTH - size));
      const y = Math.floor(random() * (HEIGHT - size));
      ctx.fillRect(x, y, size, Math.max(4, Math.floor(size * (0.35 + random() * 0.65))));
    }
  };
  const steppedLine = (points, color, width) => {
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    points.slice(1).forEach(([x, y]) => ctx.lineTo(x, y));
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = "square";
    ctx.lineJoin = "miter";
    ctx.stroke();
  };

  ctx.fillStyle = palette.ground;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  if (planetId === "earth") {
    // Lush landing zone: grass fields, forest clusters, a winding river and shallows.
    patch("#285f3d", 110, 10, 34);
    patch("#3f7845", 74, 8, 26);
    patch("#6d9950", 26, 8, 18);
    const river = [[-18, 178], [52, 204], [92, 248], [142, 260], [174, 310], [230, 326], [268, 380], [318, 398], [370, 458], [448, 484]];
    steppedLine(river, "#173e50", 60);
    steppedLine(river, "#287f94", 42);
    steppedLine(river, "#5ab4b2", 8);
    patch("#173d31", 50, 12, 28);
    for (let i = 0; i < 34; i += 1) {
      const x = Math.floor(random() * WIDTH), y = Math.floor(random() * HEIGHT);
      ctx.fillStyle = random() > 0.5 ? "#193d2b" : "#8ab766";
      ctx.fillRect(x, y, 8, 8); ctx.fillRect(x + 8, y + 4, 8, 8); ctx.fillRect(x + 4, y - 4, 8, 8);
    }
    patch("#c5b878", 8, 14, 28);
  } else if (planetId === "mercury") {
    // Baked rocky regolith and impact craters.
    patch("#77736a", 60, 12, 36); patch("#3f4348", 45, 8, 28); patch("#a49c88", 25, 6, 16);
    for (let i = 0; i < 20; i += 1) {
      const x = 18 + random() * (WIDTH - 36), y = 20 + random() * (HEIGHT - 40), r = 8 + random() * 25;
      ctx.fillStyle = "#292f36"; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "#9a9586"; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(x - 2, y - 2, r * .78, Math.PI * 1.05, Math.PI * 1.9); ctx.stroke();
      ctx.fillStyle = "#68655f"; ctx.beginPath(); ctx.arc(x + 3, y + 4, r * .52, 0, Math.PI * 2); ctx.fill();
    }
  } else if (planetId === "venus") {
    // Sulphur desert, heated dunes, volcanic crust and bright acid-yellow fissures.
    patch("#9a5c35", 80, 12, 44); patch("#d38b48", 54, 10, 32); patch("#6f3d2c", 28, 8, 22);
    for (let y = 35; y < HEIGHT; y += 94) {
      steppedLine([[-20, y + 14], [76, y - 9], [162, y + 17], [250, y - 8], [340, y + 14], [450, y - 4]], "#e6ad61", 11);
    }
    steppedLine([[54, 85], [86, 132], [72, 180], [112, 222], [100, 274]], "#f3c86e", 5);
    steppedLine([[304, 392], [274, 438], [295, 492], [252, 550], [272, 620]], "#f0bd61", 6);
    patch("#422b27", 24, 7, 18);
  } else if (planetId === "mars") {
    // Red regolith, canyon cuts and scattered iron-rich rock fields.
    patch("#a65343", 70, 12, 36); patch("#6e3940", 50, 8, 30); patch("#d27c59", 38, 8, 25);
    steppedLine([[-20, 210], [68, 224], [118, 265], [210, 278], [278, 330], [350, 346], [450, 388]], "#4f303c", 48);
    steppedLine([[-20, 210], [68, 224], [118, 265], [210, 278], [278, 330], [350, 346], [450, 388]], "#8e4a45", 24);
    for (let i = 0; i < 32; i += 1) {
      const x = random() * WIDTH, y = random() * HEIGHT, size = 5 + random() * 18;
      ctx.fillStyle = random() > .5 ? "#593641" : "#d48660";
      ctx.fillRect(x, y, size, size * .6);
    }
  } else if (planetId === "jupiter") {
    // Turbulent gas giant bands and a large rust-red storm system.
    ctx.fillStyle = "#b98c70"; ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const bands = ["#70505a", "#e1b18a", "#d7a17c", "#8b6261", "#e5c39c", "#a8796e"];
    for (let y = -30; y < HEIGHT + 40; y += 76) {
      ctx.fillStyle = bands[Math.floor(random() * bands.length)];
      ctx.fillRect(0, y + random() * 18, WIDTH, 24 + random() * 22);
      ctx.fillStyle = "#f0d5ad"; ctx.fillRect(0, y + 42, WIDTH, 4);
    }
    ctx.fillStyle = "#9c4f47"; ctx.beginPath(); ctx.ellipse(286, 435, 84, 49, -.18, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#e0a07c"; ctx.lineWidth = 8; ctx.beginPath(); ctx.ellipse(286, 435, 62, 33, -.18, .2, 5.8); ctx.stroke();
    patch("#f0d4ae", 42, 8, 22);
  } else if (planetId === "saturn") {
    // Pale ochre cloud belts, long shadows from the rings and ice fragments.
    ctx.fillStyle = "#bba176"; ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const bands = ["#ddc69a", "#8d765d", "#c5ae83", "#e8d8ae", "#9a8568"];
    for (let y = -20; y < HEIGHT + 40; y += 68) {
      ctx.fillStyle = bands[Math.floor(random() * bands.length)];
      ctx.fillRect(0, y + random() * 14, WIDTH, 20 + random() * 24);
    }
    steppedLine([[-20, 560], [90, 490], [190, 410], [300, 334], [445, 245]], "#6e634e", 18);
    patch("#efe0b7", 48, 4, 12); patch("#75634e", 18, 8, 20);
  } else if (planetId === "uranus") {
    // Frozen turquoise crust with deep crevasses and pale ice plates.
    patch("#7bbcc0", 72, 14, 42); patch("#b7e1d9", 40, 9, 29); patch("#356f83", 42, 8, 24);
    const cracks = [ [[24, 8], [62, 70], [38, 130], [94, 198], [73, 262]], [[310, 34], [274, 112], [330, 176], [286, 252], [324, 320]], [[126, 350], [168, 408], [142, 472], [206, 536], [178, 650], [224, 760]] ];
    cracks.forEach((line) => steppedLine(line, "#244f68", 10));
    cracks.forEach((line) => steppedLine(line, "#9cd9d5", 3));
    patch("#e2f3e8", 18, 8, 18);
  } else {
    // Neptune: deep frozen ocean, blue ice ridges and a rotating dark storm.
    patch("#2d4a86", 74, 12, 36); patch("#496eaf", 46, 8, 28); patch("#142b5d", 52, 10, 30);
    for (let i = 0; i < 18; i += 1) {
      const y = random() * HEIGHT, x = random() * WIDTH;
      steppedLine([[x - 55, y], [x - 18, y - 10], [x + 20, y + 7], [x + 62, y - 3]], "#7ba8e5", 5);
    }
    ctx.fillStyle = "#243b77"; ctx.beginPath(); ctx.ellipse(280, 292, 94, 58, -.35, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#7da4e9"; ctx.lineWidth = 7; ctx.beginPath(); ctx.ellipse(280, 292, 68, 36, -.35, .2, 5.9); ctx.stroke();
    patch("#b3d8ed", 18, 5, 13);
  }

  // Fine pixel noise makes every biome feel textured without painting each frame.
  patch("rgba(235,245,255,.10)", 44, 2, 5);
  return terrain;
}

export default function PlanetRun({ planetId, stats, armorBonus = 0, magnetBonus = 0, weapon, skin, onFinish, onExit }) {
  const canvasRef = useRef(null);
  const keysRef = useRef(new Set());
  const onFinishRef = useRef(onFinish);
  const pausedRef = useRef(false);
  const joystickRef = useRef({ x: 0, y: 0 });
  const joystickBaseRef = useRef(null);
  const joystickPointerRef = useRef(null);
  const maxHp = Math.max(1, Number((Number(stats?.health) || 20).toFixed(1)));
  const [hud, setHud] = useState(() => ({ hp: maxHp, xp: 0, kills: 0, time: 0, boss: 0, bossSpawned: false, level: 1, chests: 0 }));
  const [paused, setPaused] = useState(false);
  const [joystickPosition, setJoystickPosition] = useState({ x: 0, y: 0 });
  const [victoryReady, setVictoryReady] = useState(false);
  const [completionResult, setCompletionResult] = useState(null);

  useEffect(() => {
    onFinishRef.current = onFinish;
  }, [onFinish]);

  // The joystick owns vertical drags while the battle is active. Telegram's
  // swipe-to-minimize gesture is disabled only for this screen and restored on exit.
  useEffect(() => {
    const telegram = window.Telegram?.WebApp;
    try {
      telegram?.ready?.();
      telegram?.expand?.();
      telegram?.disableVerticalSwipes?.();
    } catch { /* Older Telegram clients may not expose this API. */ }
    const pad = joystickBaseRef.current;
    const stopTelegramTouchGesture = (event) => {
      if (event.cancelable) event.preventDefault();
      event.stopPropagation();
    };
    const reassertBattleTouchLock = (event) => {
      stopTelegramTouchGesture(event);
      try { telegram?.disableVerticalSwipes?.(); } catch { /* Older Telegram clients may not expose this API. */ }
    };
    // iOS Telegram WebView may still forward native touch gestures to its swipe
    // recognizer even when pointer events are captured. Suppress native touch
    // events on the dedicated pad as an additional mobile fallback.
    pad?.addEventListener("touchstart", reassertBattleTouchLock, { passive: false });
    pad?.addEventListener("touchmove", stopTelegramTouchGesture, { passive: false });
    pad?.addEventListener("touchend", stopTelegramTouchGesture, { passive: false });
    pad?.addEventListener("touchcancel", stopTelegramTouchGesture, { passive: false });
    return () => {
      pad?.removeEventListener("touchstart", reassertBattleTouchLock);
      pad?.removeEventListener("touchmove", stopTelegramTouchGesture);
      pad?.removeEventListener("touchend", stopTelegramTouchGesture);
      pad?.removeEventListener("touchcancel", stopTelegramTouchGesture);
      try { telegram?.enableVerticalSwipes?.(); } catch { /* Best-effort restore. */ }
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const keys = keysRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      onFinishRef.current({ won: false, kills: 0, bossDefeated: false, xp: 0 });
      return undefined;
    }

    const terrainCanvas = createPlanetTerrain(planetId);
    const world = {
      player: { x: WIDTH / 2, y: HEIGHT / 2 },
      enemies: [],
      shots: [],
      gems: [],
      chests: [],
      chestTimer: 4,
      chestsCollected: 0,
      hp: maxHp,
      maxHp,
      xp: 0,
      kills: 0,
      bossHp: 0,
      bossMaxHp: 0,
      bossSpawned: false,
      bossDefeated: false,
      elapsed: 0,
      damageDealt: 0,
      chestRewards: {},
      chestCredits: 0,
      finishing: false,
      finishTimer: 0,
      spawnTimer: 0,
      shotTimer: 0,
      damageTimer: 0,
      lastHud: 0,
      lastFrame: performance.now(),
      frame: 0,
      finished: false,
      level: 1,
    };

    const makeResult = (won) => ({
      won,
      kills: world.kills,
      bossDefeated: world.bossDefeated,
      xp: Math.floor(world.xp),
      chestsCollected: world.chestsCollected,
      damageDealt: Math.floor(world.damageDealt),
      chestRewards: { ...world.chestRewards },
      chestCredits: world.chestCredits,
      battleTime: Math.floor(world.elapsed),
      remainingHp: Math.max(0, Number(world.hp.toFixed(1))),
    });

    const draw = (timestamp) => {
      if (world.finished) return;
      const delta = Math.min((timestamp - world.lastFrame) / 1000, 0.05);
      world.lastFrame = timestamp;

      if (world.finishing) {
        world.finishTimer += delta;
        if (world.finishTimer >= 2) {
          world.finished = true;
          setCompletionResult(makeResult(true));
          setVictoryReady(true);
        }
      }

      context.drawImage(terrainCanvas, 0, 0, WIDTH, HEIGHT);
      context.save();
      context.globalAlpha = 0.23;
      context.fillStyle = planets[planetId].grid;
      for (let x = 0; x < WIDTH; x += 32) context.fillRect(x, 0, 1, HEIGHT);
      for (let y = 0; y < HEIGHT; y += 32) context.fillRect(0, y, WIDTH, 1);
      context.restore();

      if (!pausedRef.current && !world.finishing) {
        const bossAlreadyActive = world.enemies.some((enemy) => enemy.boss);
        // Battle clock freezes while the boss is alive, but player movement and combat continue.
        if (!bossAlreadyActive) world.elapsed += delta;
        if (world.elapsed >= RUN_DURATION && !world.bossDefeated) {
          world.finished = true;
          onFinishRef.current(makeResult(false));
        }
        let dx = Number(keys.has("ArrowRight") || keys.has("KeyD")) - Number(keys.has("ArrowLeft") || keys.has("KeyA")) + joystickRef.current.x;
        let dy = Number(keys.has("ArrowDown") || keys.has("KeyS")) - Number(keys.has("ArrowUp") || keys.has("KeyW")) + joystickRef.current.y;
        const directionLength = Math.hypot(dx, dy) || 1;
        const speedValue = Math.max(1, Number(stats?.speed) || 1);
        const movementSpeed = 145 * (1 + Math.log2(speedValue) * 0.12);
        world.player.x = Math.max(12, Math.min(WIDTH - 20, world.player.x + (dx / directionLength) * movementSpeed * delta));
        world.player.y = Math.max(12, Math.min(HEIGHT - 20, world.player.y + (dy / directionLength) * movementSpeed * delta));

        const bossActive = world.enemies.some((enemy) => enemy.boss);
        if (!bossActive && !world.bossDefeated) {
          world.spawnTimer += delta;
          const spawnInterval = Math.max(0.48, 1.25 - Math.floor(world.elapsed / 60) * 0.08);
          const enemyLimit = Math.min(30, 20 + Math.floor(world.elapsed / 60) * 2);
          if (world.spawnTimer >= spawnInterval && world.enemies.length < enemyLimit) {
            world.spawnTimer = 0;
            const angle = Math.random() * Math.PI * 2;
            const radius = Math.max(WIDTH, HEIGHT) / 2 + 20;
            world.enemies.push({
              x: Math.max(8, Math.min(WIDTH - 24, world.player.x + Math.cos(angle) * radius)),
              y: Math.max(8, Math.min(HEIGHT - 24, world.player.y + Math.sin(angle) * radius)),
              hp: 28 + Math.min(world.elapsed, 35) * 0.7,
              speed: 24 + Math.min(world.elapsed, 40) * 0.35,
              boss: false,
            });
          }
        }

        world.chestTimer += delta;
        if (world.chestTimer >= 13 && world.chests.length < 2) {
          world.chestTimer = 0;
          world.chests.push({ x: 20 + Math.random() * (WIDTH - 60), y: 30 + Math.random() * (HEIGHT - 60) });
        }

        if (world.elapsed >= BOSS_AT && !world.bossSpawned) {
          world.bossSpawned = true;
          const damageValue = Math.max(1, Number(stats?.damage) || 1);
          world.bossHp = 280 * (1 + Math.log2(damageValue) * 0.30);
          world.bossMaxHp = world.bossHp;
          world.enemies.push({
            x: 40 + Math.random() * (WIDTH - 80),
            y: 30,
            hp: world.bossHp,
            speed: 19,
            boss: true,
          });
        }

        world.shotTimer += delta;
        const damageValue = Math.max(1, Number(stats?.damage) || 1);
        const damageScale = 1 + Math.log2(damageValue) * 0.18;
        const shotInterval = Math.max(0.27, 0.62 / damageScale);
        const bossTarget = world.enemies.find((enemy) => enemy.boss);
        const target = bossTarget ?? world.enemies.reduce((nearest, enemy) => {
          if (!nearest) return enemy;
          return Math.hypot(enemy.x - world.player.x, enemy.y - world.player.y) <
            Math.hypot(nearest.x - world.player.x, nearest.y - world.player.y) ? enemy : nearest;
        }, null);
        if (target && world.shotTimer >= shotInterval) {
          world.shotTimer = 0;
          world.shots.push({ x: world.player.x, y: world.player.y, target, damage: weapon.damage * damageScale });
        }

        let playerTouching = false;
        for (const enemy of world.enemies) {
          const distance = Math.hypot(world.player.x - enemy.x, world.player.y - enemy.y) || 1;
          enemy.x += ((world.player.x - enemy.x) / distance) * enemy.speed * delta;
          enemy.y += ((world.player.y - enemy.y) / distance) * enemy.speed * delta;
          if (distance < (enemy.boss ? 30 : 20)) playerTouching = true;
        }
        world.damageTimer = playerTouching ? world.damageTimer + delta : Math.max(0, world.damageTimer - delta);

        for (const shot of world.shots) {
          if (!world.enemies.includes(shot.target)) continue;
          const distance = Math.hypot(shot.target.x - shot.x, shot.target.y - shot.y) || 1;
          const speed = 440;
          shot.x += ((shot.target.x - shot.x) / distance) * speed * delta;
          shot.y += ((shot.target.y - shot.y) / distance) * speed * delta;
          if (distance < 12) {
            const appliedDamage = Math.max(0, Math.min(shot.damage, Math.max(0, shot.target.hp)));
            world.damageDealt += appliedDamage;
            shot.target.hp -= shot.damage;
            shot.x = WIDTH + 100;
            if (shot.target.hp <= 0) {
              const killedBoss = shot.target.boss;
              world.enemies = world.enemies.filter((enemy) => enemy !== shot.target);
              world.kills += 1;
              if (killedBoss) {
                world.bossDefeated = true;
                world.xp += 60;
                // The final boss ends the run: clear every mob and collectible,
                // hold the clean field for two seconds, then show the statistics button.
                world.finishing = true;
                world.finishTimer = 0;
                world.enemies = [];
                world.shots = [];
                world.gems = [];
                world.chests = [];
                break;
              }
              world.gems.push({ x: shot.target.x, y: shot.target.y, value: 8 });
            }
          }
        }
        world.shots = world.shots.filter((shot) => shot.x <= WIDTH + 50 && shot.y >= -50 && shot.y <= HEIGHT + 50);

        for (const gem of world.gems) {
          const distance = Math.hypot(world.player.x - gem.x, world.player.y - gem.y) || 1;
          if (distance < 78 + (Number(magnetBonus) || 0) * 55) {
            gem.x += ((world.player.x - gem.x) / distance) * 170 * delta;
            gem.y += ((world.player.y - gem.y) / distance) * 170 * delta;
          }
          if (distance < 18) gem.collected = true;
        }
        for (const gem of world.gems) if (gem.collected) world.xp += gem.value;
        world.gems = world.gems.filter((gem) => !gem.collected);

        for (const chest of world.chests) {
          if (Math.hypot(world.player.x - chest.x, world.player.y - chest.y) < 27 && !chest.collected) {
            chest.collected = true;
            world.chestsCollected += 1;
            const resources = planetChestResources[planetId] || planetChestResources.earth;
            const resource = resources[Math.floor(Math.random() * resources.length)];
            const amount = 1 + Math.floor(Math.random() * 5);
            const credits = 5 + Math.floor(Math.random() * 16);
            world.chestRewards[resource] = (world.chestRewards[resource] || 0) + amount;
            world.chestCredits += credits;
          }
        }
        world.chests = world.chests.filter((chest) => !chest.collected);

        const newLevel = Math.floor(world.xp / 50) + 1;
        if (newLevel > world.level) {
          world.level = newLevel;
          world.hp = Math.min(world.maxHp, world.hp + 2);
        }

        if (!world.finishing && world.damageTimer >= 1) {
          world.hp -= 1;
          world.damageTimer = 0;
        }
        if (!world.finishing && world.hp <= 0) {
          world.finished = true;
          onFinishRef.current(makeResult(false));
        }
      }

      for (const gem of world.gems) pixelRect(context, gem.x, gem.y, 8, 8, "#d5ef91");
      for (const chest of world.chests) {
        pixelRect(context, chest.x, chest.y + 6, 24, 15, "#a85c43");
        pixelRect(context, chest.x, chest.y, 24, 8, "#efbf66");
        pixelRect(context, chest.x + 8, chest.y + 8, 8, 8, "#f5e29b");
      }
      for (const shot of world.shots) pixelRect(context, shot.x, shot.y, 7, 7, weapon.color);
      for (const enemy of world.enemies) {
        const size = enemy.boss ? 32 : 16;
        pixelRect(context, enemy.x, enemy.y, size, size, enemy.boss ? planets[planetId].boss : planets[planetId].enemy);
        pixelRect(context, enemy.x + size * .2, enemy.y + size * .3, 4, 4, "#17202a");
        pixelRect(context, enemy.x + size * .65, enemy.y + size * .3, 4, 4, "#17202a");
        if (enemy.boss) {
          world.bossHp = enemy.hp;
          context.fillStyle = "#101725";
          context.fillRect(8, 8, WIDTH - 16, 8);
          context.fillStyle = "#e87d72";
          context.fillRect(8, 8, (WIDTH - 16) * Math.max(0, enemy.hp / world.bossMaxHp), 8);
        }
      }

      const px = world.player.x;
      const py = world.player.y;
      pixelRect(context, px + 4, py, 12, 8, skin.color);
      pixelRect(context, px, py + 8, 20, 12, "#d9e8dc");
      pixelRect(context, px + 4, py + 20, 5, 6, "#91bd6c");
      pixelRect(context, px + 12, py + 20, 5, 6, "#91bd6c");
      pixelRect(context, px + 6, py + 2, 2, 2, "#17202a");
      pixelRect(context, px + 12, py + 2, 2, 2, "#17202a");

      if (timestamp - world.lastHud > 120) {
        world.lastHud = timestamp;
        setHud({
          hp: Math.max(0, Number(world.hp.toFixed(1))),
          xp: Math.floor(world.xp),
          kills: world.kills,
          time: Math.floor(world.elapsed),
          boss: world.enemies.some((enemy) => enemy.boss) ? Math.max(0, Math.ceil((world.bossHp / (world.bossMaxHp || 1)) * 100)) : 0,
          bossSpawned: world.bossSpawned,
          level: world.level,
          chests: world.chestsCollected,
        });
      }

      if (!world.finished) world.frame = requestAnimationFrame(draw);
    };

    const handleKeyDown = (event) => {
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"].includes(event.code)) event.preventDefault();
      keysRef.current.add(event.code);
    };
    const handleKeyUp = (event) => keysRef.current.delete(event.code);
    const clearKeys = () => keysRef.current.clear();
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    window.addEventListener("blur", clearKeys);
    world.frame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(world.frame);
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      window.removeEventListener("blur", clearKeys);
      keys.clear();
    };
  }, [planetId, stats, armorBonus, magnetBonus, weapon, skin, maxHp]);

  function togglePaused() {
    pausedRef.current = !pausedRef.current;
    setPaused(pausedRef.current);
  }

  function updateJoystickFromPointer(event) {
    const rect = joystickBaseRef.current?.getBoundingClientRect();
    if (!rect) return;
    const origin = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    const radius = rect.width * 0.34;
    let x = event.clientX - origin.x;
    let y = event.clientY - origin.y;
    const length = Math.hypot(x, y);
    if (length > radius) { x = (x / length) * radius; y = (y / length) * radius; }
    joystickRef.current = { x: x / radius, y: y / radius };
    setJoystickPosition({ x, y });
  }

  function handleJoystickDown(event) {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    event.preventDefault();
    event.stopPropagation();
    try { window.Telegram?.WebApp?.disableVerticalSwipes?.(); } catch { /* Best effort for older Telegram clients. */ }
    joystickPointerRef.current = event.pointerId;
    try { event.currentTarget.setPointerCapture(event.pointerId); } catch { /* Pointer capture may be unavailable in older webviews. */ }
    updateJoystickFromPointer(event);
  }

  function handleJoystickMove(event) {
    if (joystickPointerRef.current !== event.pointerId) return;
    event.preventDefault();
    event.stopPropagation();
    updateJoystickFromPointer(event);
  }

  function releaseJoystick(event) {
    if (event && joystickPointerRef.current !== null && event.pointerId !== joystickPointerRef.current) return;
    event?.preventDefault?.();
    event?.stopPropagation?.();
    const pointerId = joystickPointerRef.current;
    joystickPointerRef.current = null;
    joystickRef.current = { x: 0, y: 0 };
    setJoystickPosition({ x: 0, y: 0 });
    if (event?.currentTarget?.hasPointerCapture?.(pointerId)) {
      try { event.currentTarget.releasePointerCapture(pointerId); } catch { /* Ignore a stale pointer capture. */ }
    }
  }

  return (
    <section className="battle-page">
      <canvas ref={canvasRef} className="battle-canvas" width={WIDTH} height={HEIGHT} aria-label="Поле зачистки планеты. Двигай пилота виртуальным джойстиком." />
      <div className="battle-overlay">
        <div className="battle-title">
          <div><div className="eyebrow">ЗАЧИСТКА ПЛАНЕТЫ</div><h1>{planets[planetId].name}</h1></div>
          <div className="battle-actions">
            <button className="battle-pause" aria-label="Выйти с планеты" onClick={onExit}>×</button>
            <button className="battle-pause" aria-label={paused ? "Продолжить игру" : "Пауза"} onClick={togglePaused}>{paused ? "▶" : "Ⅱ"}</button>
          </div>
        </div>
        <div className="battle-hud">
          <span>♥ {hud.hp}/{maxHp} HP</span><span>LVL {hud.level}</span><span>УБИЙСТВ {hud.kills}</span><span>📦 {hud.chests}</span><span>{hud.time} СЕК.</span>
        </div>
        <div className="battle-stat-strip" aria-label="Характеристики пилота, совпадают с главной базой">
          <span>ЖИВ. {Number(stats?.health || 20).toFixed(1)}</span>
          <span>УРОН {Number(stats?.damage || 1).toFixed(2)}</span>
          <span>СКОР. {Number(stats?.speed || 1).toFixed(2)}</span>
          <span>УДАЧА {Number(stats?.luck || 0.01).toFixed(4)}</span>
        </div>
        <div className="battle-meter"><div className="battle-meter-fill health" style={{ width: `${Math.min(100, (hud.hp / maxHp) * 100)}%` }} /></div>
        <div className="battle-meter"><div className="battle-meter-fill battle-xp" style={{ width: `${(hud.xp % 50) * 2}%` }} /></div>
        {!hud.bossSpawned && hud.time >= BOSS_AT - 5 && <div className="boss-warning">ВНИМАНИЕ: ПРИБЛИЖАЕТСЯ БОСС!</div>}
        {hud.boss > 0 && <div className="boss-label">БОСС · {hud.boss}% HP</div>}
      </div>
      {victoryReady && (
        <div className="battle-victory-backdrop" role="dialog" aria-modal="true" aria-label="Зачистка завершена">
          <div className="battle-victory-panel">
            <div className="eyebrow">ПОСЛЕДНИЙ БОСС ПОВЕРЖЕН</div>
            <h2>ЗАЧИСТКА ЗАВЕРШЕНА</h2>
            <p>Поле очищено. Данные экспедиции готовы.</p>
            <button className="primary-button" onClick={() => {
              if (completionResult) onFinishRef.current(completionResult);
            }}>ПЕРЕЙТИ К СТАТИСТИКЕ БОЯ</button>
          </div>
        </div>
      )}
      <div
        ref={joystickBaseRef}
        className="virtual-joystick joystick-pad"
        role="application"
        aria-label="Виртуальный джойстик. Удерживай и перемещай палец для движения."
        onPointerDown={handleJoystickDown}
        onPointerMove={handleJoystickMove}
        onPointerUp={releaseJoystick}
        onPointerCancel={releaseJoystick}
        onLostPointerCapture={releaseJoystick}
      >
        <span className="joystick-knob" style={{ "--stick-x": `${joystickPosition.x}px`, "--stick-y": `${joystickPosition.y}px` }} />
      </div>
    </section>
  );
}
