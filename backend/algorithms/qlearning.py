"""
ALGORITHM 4: Q-Learning (model-free reinforcement learning)

The Tracker Drone doesn't know the map or chase directly like the Guard does.
Instead it learns, over the course of the run, which action (up/down/left/
right/stay) tends to close distance to the player from a given discretized
state. Every tick it: picks an action (epsilon-greedy), observes the reward
(did it get closer or farther?), and updates its Q-table with the standard
Bellman update. Early game it wanders; by the end of a run it's noticeably
better at cutting you off.
"""
import random

ACTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)]  # up, down, left, right, stay


def _discretize(drone_pos, player_pos):
    """State = coarse relative direction bucket from drone to player (dx sign, dy sign, near/far)."""
    dx = player_pos[0] - drone_pos[0]
    dy = player_pos[1] - drone_pos[1]
    dx_bucket = (dx > 0) - (dx < 0)   # -1, 0, 1
    dy_bucket = (dy > 0) - (dy < 0)
    dist = abs(dx) + abs(dy)
    dist_bucket = "near" if dist <= 3 else ("mid" if dist <= 7 else "far")
    return (dx_bucket, dy_bucket, dist_bucket)


class TrackerDrone:
    def __init__(self, start_pos, alpha=0.3, gamma=0.8, epsilon=0.25):
        self.pos = start_pos
        self.q_table = {}
        self.alpha = alpha      # learning rate
        self.gamma = gamma      # discount factor
        self.epsilon = epsilon  # exploration rate
        self.episodes = 0

    def _q(self, state, action_idx):
        return self.q_table.get((state, action_idx), 0.0)

    def _best_action_idx(self, state):
        qs = [self._q(state, i) for i in range(len(ACTIONS))]
        max_q = max(qs)
        best = [i for i, q in enumerate(qs) if q == max_q]
        return random.choice(best)

    def step(self, player_pos, grid):
        height, width = len(grid), len(grid[0])
        state = _discretize(self.pos, player_pos)
        prev_dist = abs(self.pos[0] - player_pos[0]) + abs(self.pos[1] - player_pos[1])

        # epsilon-greedy action selection
        if random.random() < self.epsilon:
            action_idx = random.randrange(len(ACTIONS))
        else:
            action_idx = self._best_action_idx(state)

        dx, dy = ACTIONS[action_idx]
        nx, ny = self.pos[0] + dx, self.pos[1] + dy
        moved = False
        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == 0:
            self.pos = (nx, ny)
            moved = True

        new_dist = abs(self.pos[0] - player_pos[0]) + abs(self.pos[1] - player_pos[1])

        # reward shaping: closing distance is good, hitting a wall is bad, catching player is great
        if new_dist == 0:
            reward = 20
        elif not moved:
            reward = -2
        elif new_dist < prev_dist:
            reward = 1
        else:
            reward = -0.5

        next_state = _discretize(self.pos, player_pos)
        best_next_q = max(self._q(next_state, i) for i in range(len(ACTIONS)))
        old_q = self._q(state, action_idx)
        new_q = old_q + self.alpha * (reward + self.gamma * best_next_q - old_q)
        self.q_table[(state, action_idx)] = new_q
        self.episodes += 1

        log = None
        if self.episodes % 15 == 0:
            log = f"DRONE: Q-table updated ({len(self.q_table)} states learned so far)"
        return log
