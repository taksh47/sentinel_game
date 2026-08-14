# SENTINEL — AI Facility Escape

A small stealth-escape game built to showcase 5 distinct AI/ML algorithms
actually used in real games, each doing real work rather than just being
name-dropped:

| # | Algorithm | Where it's used |
|---|-----------|------------------|
| 1 | **Cellular Automata** | Generates the facility layout every run (procedural content generation) |
| 2 | **A\* Pathfinding** | The Guard navigates the shortest route to you |
| 3 | **Finite State Machine** | The Guard's behavior: PATROL → CHASE → SEARCH → RETURN |
| 4 | **Q-Learning (Reinforcement Learning)** | The Tracker Drone learns to intercept you over the course of a run |
| 5 | **Minimax + Alpha-Beta Pruning** | The Core Sentinel boss fight, a turn-based RPS-style duel |

**How the game plays:** you spawn in a randomly generated facility. Find the
keycard, avoid the Guard's line-of-sight and the learning Drone, reach the
exit, then beat the Core Sentinel in a turn-based duel to escape.

## Project structure

```
sentinel_game/
├── backend/
│   ├── app.py                  Flask server + API endpoints
│   ├── requirements.txt
│   └── algorithms/
│       ├── cellular_automata.py
│       ├── astar.py
│       ├── fsm.py
│       ├── qlearning.py
│       └── minimax.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── game.js
└── README.md
```

## Running it in VS Code

**1. Start the backend**

Open a terminal in the project folder:

```bash
cd sentinel_game/backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

You should see Flask start on `http://localhost:5000`. Leave this terminal running.

**2. Open the frontend**

In VS Code, right-click `frontend/index.html` → **Open with Live Server**
(install the free "Live Server" extension if you don't have it), or just
double-click `index.html` to open it directly in your browser.

> The frontend talks to `http://localhost:5000`, so the backend terminal
> from step 1 needs to stay running while you play.

**3. Play**

Click **Initialize Run**, move with `WASD` or arrow keys. Watch the "AI
State Log" panel on the right — it prints out what each algorithm is doing
in real time (guard state transitions, drone Q-table updates, boss minimax
picks).

## Notes on the algorithms (for your portfolio / explaining this later)

- **Cellular automata**: seeds random noise, then applies smoothing rules
  (a cell becomes wall/floor based on how many of its 8 neighbors are
  walls) for a few passes until it looks cave-like instead of static. A
  flood-fill afterward guarantees the whole map is one connected region —
  no unreachable pockets, no unsolvable maps.
- **A\***: standard `f = g + h` search with a Manhattan-distance heuristic
  and a min-heap open set. This is what the guard uses to actually walk to
  wherever the FSM tells it to go.
- **FSM**: the guard is always in exactly one of 4 states, and transitions
  are driven by a Bresenham line-of-sight check against the maze walls —
  it can't see through walls, so you can break its lock by ducking around
  a corner.
- **Q-learning**: the drone has no map knowledge. It only knows a coarse
  bucketed state (which rough direction you're in, how far) and updates a
  Q-table with the Bellman equation after every move based on whether it
  got closer to you. Early in a run it's aimless; by the end it's
  noticeably better at cutting you off — that's the learning visibly
  happening.
- **Minimax + alpha-beta**: the boss searches 4 turns ahead through every
  combination of attack/defend/special, assuming you'll play the counter
  that's worst for it at each step (the standard adversarial-search
  assumption), and prunes branches that can't change the outcome. It's the
  same algorithm chess engines use, just on a tiny 3-move game tree.

## Extending it

- Swap the drone's discretized state for a small neural net (a natural
  next step toward Deep Q-Networks).
- Add a second guard and have them share a blackboard so they coordinate
  search patterns.
- Make maze difficulty scale with a seed parameter exposed in the UI.
