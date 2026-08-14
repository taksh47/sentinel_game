const API = "http://localhost:5001/api";
const TILE = 32;
const GRID_W = 21, GRID_H = 15;

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

const overlay = document.getElementById("overlay");
const startBtn = document.getElementById("startBtn");
const bossLayer = document.getElementById("bossLayer");
const endLayer = document.getElementById("endLayer");
const retryBtn = document.getElementById("retryBtn");
const connDot = document.getElementById("connDot");
const connLabel = document.getElementById("connLabel");
const logFeed = document.getElementById("logFeed");
const guardStateEl = document.getElementById("guardState");
const droneStateEl = document.getElementById("droneState");

let latest = null;
let moving = false;

const COLORS = {
  wall: "#152019",
  floor: "#0d1613",
  floorAlt: "#0f1a15",
  player: "#5fe89a",
  key: "#ffd76a",
  exit: "#7fd8ff",
  guard: "#ff5f5f",
  guardSearch: "#ffb454",
  drone: "#d29bff",
  grid: "#182620",
};

function addLog(text, cls) {
  const div = document.createElement("div");
  div.className = "entry " + (cls || "system");
  div.textContent = "> " + text;
  logFeed.prepend(div);
  while (logFeed.children.length > 60) logFeed.removeChild(logFeed.lastChild);
}

function classifyLog(line) {
  if (line.startsWith("GUARD")) return "guard";
  if (line.startsWith("DRONE")) return "drone";
  if (line.startsWith("CORE")) return "core";
  return "system";
}

function pushLogs(lines) {
  (lines || []).forEach((l) => addLog(l, classifyLog(l)));
}

function draw(state) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const grid = state.grid;

  for (let y = 0; y < GRID_H; y++) {
    for (let x = 0; x < GRID_W; x++) {
      const isWall = grid[y][x] === 1;
      ctx.fillStyle = isWall ? COLORS.wall : ((x + y) % 2 === 0 ? COLORS.floor : COLORS.floorAlt);
      ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
    }
  }

  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 1;
  for (let x = 0; x <= GRID_W; x++) {
    ctx.beginPath(); ctx.moveTo(x * TILE, 0); ctx.lineTo(x * TILE, canvas.height); ctx.stroke();
  }
  for (let y = 0; y <= GRID_H; y++) {
    ctx.beginPath(); ctx.moveTo(0, y * TILE); ctx.lineTo(canvas.width, y * TILE); ctx.stroke();
  }

  // exit
  drawTile(state.exit, state.has_key ? COLORS.exit : "#2a4048", "▣");
  // key
  if (!state.has_key) drawTile(state.key, COLORS.key, "◆");
  // guard
  const guardColor = state.guard.state === "PATROL" ? COLORS.guard : (state.guard.state === "SEARCH" ? COLORS.guardSearch : COLORS.guard);
  drawTile(state.guard.pos, guardColor, "▲");
  // drone
  drawTile(state.drone.pos, COLORS.drone, "✦");
  // player
  drawTile(state.player, COLORS.player, "●");
}

function drawTile(pos, color, glyph) {
  const [x, y] = pos;
  ctx.fillStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 10;
  ctx.font = "20px monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(glyph, x * TILE + TILE / 2, y * TILE + TILE / 2 + 1);
  ctx.shadowBlur = 0;
}

function updateHud(state) {
  document.getElementById("objKey").className = state.has_key ? "done" : "pending";
  document.getElementById("objExit").className = (state.status !== "playing" && state.status !== "lost") ? "done" : "pending";
  document.getElementById("objBoss").className = state.status === "won" ? "done" : "pending";

  guardStateEl.textContent = state.guard.state;
  guardStateEl.className = "threat-state " + (state.guard.state === "CHASE" ? "chase" : state.guard.state === "SEARCH" ? "search" : "");
  droneStateEl.textContent = "learning (" + (state.drone_episodes || "") + ")";
}

async function newGame() {
  connLabel.textContent = "connecting to backend…";
  try {
    const res = await fetch(`${API}/new_game`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: "{}",
    });
    const data = await res.json();
    connDot.classList.add("online");
    connLabel.textContent = "backend online // port 5001";
    latest = data;
    logFeed.innerHTML = "";
    pushLogs(data.log);
    draw(data);
    updateHud(data);
    overlay.classList.add("hidden");
    bossLayer.classList.remove("visible");
    endLayer.classList.remove("visible");
  } catch (e) {
    connLabel.textContent = "backend unreachable — start the Flask server (see README)";
  }
}

async function move(direction) {
  if (!latest || latest.status !== "playing" || moving) return;
  moving = true;
  try {
    const res = await fetch(`${API}/move`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ direction }),
    });
    const data = await res.json();
    latest = data;
    pushLogs(data.log);
    draw(data);
    updateHud(data);
    if (data.status === "boss") openBoss();
    if (data.status === "lost") openEnd(false);
  } finally {
    moving = false;
  }
}

function openBoss() {
  bossLayer.classList.add("visible");
  document.getElementById("bossResult").textContent = "Core Sentinel initialized. Choose your move.";
  updateBossHp();
}

function updateBossHp() {
  const p = Math.max(0, latest.player_hp), b = Math.max(0, latest.boss_hp);
  document.getElementById("playerHpFill").style.width = (p / 60 * 100) + "%";
  document.getElementById("bossHpFill").style.width = (b / 60 * 100) + "%";
  document.getElementById("playerHpText").textContent = p;
  document.getElementById("bossHpText").textContent = b;
}

async function bossMove(playerMove) {
  const res = await fetch(`${API}/boss_move`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move: playerMove }),
  });
  const data = await res.json();
  latest = data;
  pushLogs(data.log);
  updateBossHp();
  document.getElementById("bossResult").textContent =
    `You: ${playerMove.toUpperCase()}  //  Core: ${data.boss_move.toUpperCase()}  →  ${data.outcome.replace(/_/g, " ")}`;

  if (data.status === "won") {
    setTimeout(() => { bossLayer.classList.remove("visible"); openEnd(true); }, 900);
  } else if (data.status === "lost") {
    setTimeout(() => { bossLayer.classList.remove("visible"); openEnd(false); }, 900);
  }
}

function openEnd(won) {
  endLayer.classList.add("visible");
  document.getElementById("endTitle").textContent = won ? "ESCAPE SUCCESSFUL" : "MISSION FAILED";
  document.getElementById("endTitle").style.color = won ? "#5fe89a" : "#ff5f5f";
  document.getElementById("endBody").textContent = won
    ? "The Core Sentinel is disabled. You slip out through the service exit before backup arrives."
    : "You were detected and the facility went into lockdown. Better luck next run.";
}

startBtn.addEventListener("click", newGame);
retryBtn.addEventListener("click", newGame);

document.querySelectorAll(".btn-move").forEach((btn) => {
  btn.addEventListener("click", () => bossMove(btn.dataset.move));
});

window.addEventListener("keydown", (e) => {
  const map = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
                w: "up", s: "down", a: "left", d: "right" };
  const dir = map[e.key];
  if (dir) { e.preventDefault(); move(dir); }
});

draw({ grid: Array.from({ length: GRID_H }, () => Array(GRID_W).fill(1)),
       player: [0,0], exit: [0,0], key: [0,0], has_key: false,
       guard: { pos: [0,0], state: "PATROL" }, drone: { pos: [0,0] } });
