from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import cycle, islice, product
from rich import print
from typing import Iterable, Iterator, Protocol, TypeVar


class Dice(Protocol):
    def roll(self) -> Iterator[int]:
        """Yield one value for each universe that the dice roll creates."""


@dataclass
class SequentialDice:
    """Deterministic dice. Each roll return the next value in this universe."""

    sides: int = 6
    num: int = 1
    rolls: int = 0

    def __post_init__(self):
        self.it: Iterator[int] = cycle(range(1, self.sides + 1))

    def roll(self) -> Iterator[int]:
        self.rolls += self.num
        yield sum(islice(self.it, self.num))


@dataclass
class DiracDice:
    """Quantum dice. Each roll returns all values in separate universes."""

    sides: int = 3
    num: int = 1

    def roll(self) -> Iterator[int]:
        rolls = product(range(1, self.sides + 1), repeat=self.num)
        for r in rolls:
            yield sum(r)


Board = tuple(range(1, 11))  # Board positions


@dataclass(frozen=True)
class Player:
    num: int
    pos: int  # index into Board
    score: int = 0

    @classmethod
    def parse(cls, line: str, num: int) -> Player:
        start = int(line.removeprefix(f"Player {num} starting position: "))
        return cls(num, Board.index(start))

    def turn(self, die: Dice) -> Iterator[tuple[Player, int]]:
        results = Counter(die.roll())
        for result, count in results.most_common():
            new_pos = (self.pos + result) % len(Board)
            new_score = self.score + Board[new_pos]
            yield self.__class__(self.num, new_pos, new_score), count


@dataclass
class Game:
    players: tuple[Player, Player]  # (current player, other player)
    dice: Dice  # The dice being used (alternately by both players)
    target: int  # End game when either player achieves this score
    count: int = 1  # How many parallel universes this is the game state

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Game):
            return NotImplemented
        return self.players == other.players

    def turn(self) -> Iterator[Game]:
        player, other = self.players
        for new_player, count in player.turn(self.dice):  # player => new_player
            yield self.__class__(
                (other, new_player),  # switch player order for next turn
                self.dice,
                self.target,
                self.count * count,
            )

    def done(self) -> tuple[Player, Player] | None:
        a, b = self.players
        if a.score >= self.target:
            assert b.score < self.target
            return a, b
        elif b.score >= self.target:
            return b, a
        else:
            return None


T = TypeVar("T")


def only(gen: Iterable[T]) -> T:
    one_item_list = list(gen)
    assert len(one_item_list) == 1
    return one_item_list[0]


class Stats(dict[int, int]):
    """Statistics on the games won by each player across the multiverse."""

    def __iadd__(self, other: Stats) -> Stats:
        for pnum, wins in other.items():
            self[pnum] = self.get(pnum, 0) + wins
        return self

    def __mul__(self, num: int) -> Stats:
        return Stats({p: w * num for p, w in self.items()})

    def __floordiv__(self, num: int) -> Stats:
        assert all(w % num == 0 for w in self.values())
        return Stats({p: w // num for p, w in self.items()})


def play_in_multiverse(game: Game) -> Stats:
    games = [game]  # Start with single universe
    totals = Stats()
    shortcuts: dict[tuple[Player, Player], Stats] = {}  # map game state to wins

    def follow_shortcut(game: Game) -> Stats | None:
        if game.players in shortcuts:
            # We have previously played to completion from this state
            return shortcuts[game.players] * game.count
        return None

    def add_shortcut(game: Game, stats: Stats) -> None:
        assert game.players not in shortcuts
        shortcuts[game.players] = stats // game.count

    while games:  # There are still unresolved games/universes
        game = games.pop()  # Play one of the remaining games
        unresolved = []  # Keep track of games that we cannot directly resolve
        subtotal = Stats()  # Count stats for the games that we _can_ resolve
        for next_game in game.turn():
            if (shortcut := follow_shortcut(next_game)) is not None:
                # We know how _all_ games starting from this position will end
                subtotal += shortcut
            elif (result := next_game.done()) is not None:  # Game completed
                winner, _ = result
                subtotal += Stats({winner.num: next_game.count})
            else:  # Cannot resolve this game yet
                unresolved.append(next_game)

        totals += subtotal

        if not unresolved:  # All subsequent games are resolved!
            add_shortcut(game, subtotal)
        games += unresolved  # Must keep playing the unresolved games

    return totals


with open("21.input") as f:
    player1, player2 = [Player.parse(line, i + 1) for i, line in enumerate(f)]
    players = (player1, player2)

# Part 1: Score of losing player multiplied by deterministic die rolls
dice = SequentialDice(100, 3)
game = Game(players, dice, 1000)
while (result := game.done()) is None:
    game = only(game.turn())  # No multiverse here!
winner, loser = result
print(loser.score * dice.rolls)

# Part 2: In how many universes does the most-winning player win?
wins = play_in_multiverse(Game(players, DiracDice(3, 3), 21))
print(max(wins.values()))
