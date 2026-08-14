"""
ALGORITHM 5: Minimax with Alpha-Beta Pruning

The final Core Sentinel fight is a turn-based duel: each side picks
ATTACK, DEFEND, or SPECIAL, rock-paper-scissors style:
  ATTACK  beats SPECIAL (interrupts the wind-up)
  SPECIAL beats DEFEND  (breaks guard)
  DEFEND  beats ATTACK  (blocks the hit)
A win nets bonus damage; a loss/draw does reduced/no damage.
Minimax searches a few turns ahead assuming the player plays optimally
against the boss (worst case for the boss), and alpha-beta pruning cuts
branches that can't possibly change the result -- same algorithm chess
engines use, just on a tiny 3-move game tree.
"""
import math
import random

MOVES = ["attack", "defend", "special"]
BEATS = {"attack": "special", "special": "defend", "defend": "attack"}

BASE_DAMAGE = 12
WIN_BONUS = 8
MAX_DEPTH = 4


def _resolve(player_move, boss_move):
    """Returns (damage_to_player, damage_to_boss) for one exchange."""
    if player_move == boss_move:
        return 4, 4  # clash, both take a little chip damage
    if BEATS[player_move] == boss_move:
        return 0, BASE_DAMAGE + WIN_BONUS  # player's move beats boss's move
    return BASE_DAMAGE + WIN_BONUS, 0      # boss's move beats player's move


def _evaluate(player_hp, boss_hp):
    return boss_hp - player_hp  # boss wants this high, player wants it low


def _minimax(player_hp, boss_hp, depth, alpha, beta, maximizing):
    if depth == 0 or player_hp <= 0 or boss_hp <= 0:
        return _evaluate(player_hp, boss_hp)

    if maximizing:  # boss's turn to choose, trying to maximize boss advantage
        best = -math.inf
        for boss_move in MOVES:
            # assume player responds optimally (minimizing) to this boss move
            worst_for_boss = math.inf
            for player_move in MOVES:
                dmg_p, dmg_b = _resolve(player_move, boss_move)
                score = _minimax(player_hp - dmg_p, boss_hp - dmg_b, depth - 1, alpha, beta, False)
                worst_for_boss = min(worst_for_boss, score)
            best = max(best, worst_for_boss)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for player_move in MOVES:
            best_for_player = -math.inf
            for boss_move in MOVES:
                dmg_p, dmg_b = _resolve(player_move, boss_move)
                score = _minimax(player_hp - dmg_p, boss_hp - dmg_b, depth - 1, alpha, beta, True)
                best_for_player = max(best_for_player, score)
            best = min(best, best_for_player)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def choose_boss_move(player_hp, boss_hp):
    """
    Runs alpha-beta minimax and returns the boss's chosen move for this turn.

    Note: attack/defend/special forms a symmetric rock-paper-scissors matrix,
    so under optimal play the minimax value is identical for all three boss
    moves almost every turn (there's no dominant move in a symmetric game --
    that's expected, not a bug). Always breaking ties the same way would
    make the boss 100% predictable and trivially exploitable, so we collect
    every move tied for best and sample among them. This mirrors the real
    solution to a symmetric zero-sum game: a mixed (randomized) strategy
    over the moves the search found equally optimal, rather than a single
    deterministic pick.
    """
    scored = []
    for boss_move in MOVES:
        worst_for_boss = math.inf
        for player_move in MOVES:
            dmg_p, dmg_b = _resolve(player_move, boss_move)
            score = _minimax(player_hp - dmg_p, boss_hp - dmg_b, MAX_DEPTH - 1, -math.inf, math.inf, False)
            worst_for_boss = min(worst_for_boss, score)
        scored.append((boss_move, worst_for_boss))

    best_score = max(s for _, s in scored)
    best_moves = [m for m, s in scored if s == best_score]
    return random.choice(best_moves)


def resolve_turn(player_move, boss_move):
    dmg_to_player, dmg_to_boss = _resolve(player_move, boss_move)
    if player_move == boss_move:
        outcome = "clash"
    elif BEATS[player_move] == boss_move:
        outcome = "player_wins_exchange"
    else:
        outcome = "boss_wins_exchange"
    return dmg_to_player, dmg_to_boss, outcome
