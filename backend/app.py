"""
SENTINEL — Flask backend

Ties together 5 AI/ML algorithms into one small stealth-escape game:
  1. Cellular Automata  -> procedural facility layout generation
  2. A* Pathfinding      -> Guard navigates to the player
  3. Finite State Machine -> Guard's patrol/chase/search behavior
  4. Q-Learning           -> Tracker Drone learns to intercept the player
  5. Minimax + Alpha-Beta -> Core Sentinel boss duel

Game state is kept in a single in-memory dict since this is a local,
single-player demo (run with `python app.py`).
"""
import random
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from algorithms import cellular_automata, fsm, qlearning, minimax

#app = Flask(__name__)
app = Flask(__name__, static_folder="../frontend", static_url_path="")

@app.route("/")
def serve_index():
    return app.send_static_file("index.html")
CORS(app)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

GRID_W, GRID_H = 21, 15
STATE = {}


def _random_floor(region, exclude=(), min_dist_from=None, min_dist=0):
    choices = [c for c in region if c not in exclude]
    if min_dist_from and min_dist > 0:
        far_choices = [c for c in choices if abs(c[0] - min_dist_from[0]) + abs(c[1] - min_dist_from[1]) >= min_dist]
        if far_choices:
            choices = far_choices
    return random.choice(choices)


def _build_patrol_route(region, start, hops=4, radius=5):
    """Pick a short loop of nearby floor tiles for the guard to patrol between."""
    route = [start]
    for _ in range(hops):
        candidates = [c for c in region if abs(c[0] - route[-1][0]) + abs(c[1] - route[-1][1]) <= radius]
        if candidates:
            route.append(random.choice(candidates))
    return route


@app.route("/api/new_game", methods=["POST"])
def new_game():
    seed = request.json.get("seed") if request.is_json else None
    grid, region = cellular_automata.generate_cave(GRID_W, GRID_H, seed=seed)
    region_set = set(region)

    player_pos = min(region, key=lambda c: c[0] + c[1])          # near top-left
    exit_pos = max(region, key=lambda c: c[0] + c[1])             # near bottom-right
    key_pos = _random_floor(region, exclude={player_pos, exit_pos})

    guard_start = _random_floor(region, exclude={player_pos, exit_pos, key_pos},
                                 min_dist_from=player_pos, min_dist=8)
    patrol_route = _build_patrol_route(region, guard_start)
    guard = fsm.Guard(guard_start, patrol_route, vision_range=6)

    drone_start = _random_floor(region, exclude={player_pos, exit_pos, key_pos, guard_start},
                                 min_dist_from=player_pos, min_dist=6)
    drone = qlearning.TrackerDrone(drone_start)

    STATE.clear()
    STATE.update({
        "grid": grid,
        "region": region_set,
        "player": player_pos,
        "exit": exit_pos,
        "key": key_pos,
        "has_key": False,
        "guard": guard,
        "drone": drone,
        "status": "playing",  # playing | caught | boss | won | lost
        "boss_hp": 60,
        "player_hp": 60,
    })

    return jsonify(_public_state(log=["SYSTEM: facility generated (cellular automata)",
                                       "SYSTEM: guard AI online (FSM + A*)",
                                       "SYSTEM: tracker drone online (Q-learning, epsilon=0.25)"]))


def _public_state(log=None):
    return {
        "grid": STATE["grid"],
        "player": STATE["player"],
        "exit": STATE["exit"],
        "key": STATE["key"],
        "has_key": STATE["has_key"],
        "guard": {"pos": STATE["guard"].pos, "state": STATE["guard"].state},
        "drone": {"pos": STATE["drone"].pos},
        "status": STATE["status"],
        "boss_hp": STATE["boss_hp"],
        "player_hp": STATE["player_hp"],
        "log": log or [],
    }


@app.route("/api/move", methods=["POST"])
def move():
    if STATE.get("status") != "playing":
        return jsonify(_public_state())

    direction = request.json.get("direction")
    dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(direction, (0, 0))
    px, py = STATE["player"]
    nx, ny = px + dx, py + dy
    grid = STATE["grid"]
    log = []

    if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] == 0:
        STATE["player"] = (nx, ny)

    if STATE["player"] == STATE["key"] and not STATE["has_key"]:
        STATE["has_key"] = True
        log.append("SYSTEM: keycard acquired -> exit unlocked")

    if STATE["player"] == STATE["exit"] and STATE["has_key"]:
        STATE["status"] = "boss"
        log.append("SYSTEM: exit reached -> CORE SENTINEL activated")
        return jsonify(_public_state(log=log))

    guard_state, guard_log = STATE["guard"].step(STATE["player"], grid)
    if guard_log:
        log.append(guard_log)

    drone_log = STATE["drone"].step(STATE["player"], grid)
    if drone_log:
        log.append(drone_log)

    if STATE["guard"].pos == STATE["player"] or STATE["drone"].pos == STATE["player"]:
        STATE["status"] = "lost"
        log.append("SYSTEM: player detected and caught -> mission failed")

    return jsonify(_public_state(log=log))


@app.route("/api/boss_move", methods=["POST"])
def boss_move():
    if STATE.get("status") != "boss":
        return jsonify(_public_state())

    player_move = request.json.get("move")
    if player_move not in minimax.MOVES:
        return jsonify({"error": "invalid move"}), 400

    boss_choice = minimax.choose_boss_move(STATE["player_hp"], STATE["boss_hp"])
    dmg_to_player, dmg_to_boss, outcome = minimax.resolve_turn(player_move, boss_choice)

    STATE["player_hp"] = max(0, STATE["player_hp"] - dmg_to_player)
    STATE["boss_hp"] = max(0, STATE["boss_hp"] - dmg_to_boss)

    log = [f"CORE: minimax (depth=4, alpha-beta) selected '{boss_choice}'",
           f"CORE: exchange result -> {outcome.replace('_', ' ')}"]

    if STATE["boss_hp"] <= 0:
        STATE["status"] = "won"
        log.append("SYSTEM: Core Sentinel disabled -> ESCAPE SUCCESSFUL")
    elif STATE["player_hp"] <= 0:
        STATE["status"] = "lost"
        log.append("SYSTEM: player HP depleted -> mission failed")

    resp = _public_state(log=log)
    resp["boss_move"] = boss_choice
    resp["outcome"] = outcome
    return jsonify(resp)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, port=port)
