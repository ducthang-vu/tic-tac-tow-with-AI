from itertools import product
from random import choice
from collections import Counter
from enum import Enum


class OccupiedCell(Exception):
    pass


class GameState(Enum):
    NOT_FINISHED = 'Game not finished'
    X_WINS = 'X wins'
    O_WINS = 'O wins'
    DRAW = 'Draw'

    @classmethod
    def win_for(cls, symbol):
        return cls.X_WINS if symbol == 'X' else cls.O_WINS


class Field:
    coords = sorted(product(range(1, 4), repeat=2), key=lambda a: (- a[1], a[0]))

    def __init__(self, start=None):
        if start is None:
            self.cells = dict(zip(Field.coords, [' ' for _ in range(9)]))
        else:
            self.cells = dict(zip(Field.coords, start))
        self.state = GameState.NOT_FINISHED

    def __str__(self):
        return ('---------\n'
                '| {} {} {} |\n'
                '| {} {} {} |\n'
                '| {} {} {} |\n'
                '---------\n').format(*self.cells.values())

    @property
    def free_cells(self):
        return [key for key in self.cells if self.cells[key] == ' ']

    @property
    def symbol(self):
        return 'X' if bool(Counter(self.cells.values())[' '] % 2) else 'O'

    def evaluate(self, coord):
        return any(map(lambda a: len(set(a)) == 1 and ' ' not in set(a),
                       [[self.cells[(coord[0]), n] for n in range(1, 4)],
                        [self.cells[n, (coord[1])] for n in range(1, 4)],
                        [self.cells[n, n] for n in range(1, 4)],
                        [self.cells[n, 4 - n] for n in range(1, 4)]
                        ]))

    def update(self, coord, raise_if_occupied=True):
        if any(n < 1 or n > 3 for n in [*coord]):
            raise IndexError
        if raise_if_occupied and not self.cells[coord] == ' ':
            raise OccupiedCell

        symbol = self.symbol
        self.cells[coord] = symbol
        if self.evaluate(coord):
            self.state = GameState.win_for(symbol)
            return True
        elif not Counter(self.cells.values())[' ']:
            self.state = GameState.DRAW
        return False


class Game:
    def __init__(self):
        self.players = []
        self.field = None
        self.moves = {
            'user': self.user_moves,
            'easy': self.bot_easy,
            'medium': self.bot_medium,
            'hard': self.bot_hard,
        }

    def user_moves(self):
        while True:
            try:
                x, y = [int(n) for n in input('Enter the coordinates: (x y) > ').split()]
            except ValueError:
                print('You should enter numbers!')
                continue
            try:
                self.field.update((x, y))
            except IndexError:
                print('Coordinates should be from 1 to 3!')
                continue
            except OccupiedCell:
                print('This cell is occupied! Choose another one!')
                continue
            return True

    def make_random_move(self, coords=None):
        coord = choice(self.field.free_cells) if coords is None else choice(coords)
        self.field.update(coord)

    def bot_easy(self):
        print('Making move level "easy"')
        self.make_random_move()

    def get_candidate_moves(self, field=None):
        if field is None:
            field = self.field
        scenarios = {cell: Field(field.cells.values()) for cell in field.free_cells}
        return [cell for cell, field_obj in scenarios.items() if field_obj.update(cell)] or \
               [cell for cell, field_obj in scenarios.items() if field_obj.update(cell, False)]

    def bot_medium(self):
        print('Making move level "medium"')
        candidate_moves = self.get_candidate_moves()
        if candidate_moves:
            self.make_random_move(candidate_moves)
        else:
            self.make_random_move()

    def minimax(self, field=None, depth=0):
        if field is None:
            field = self.field
        branches = {}
        for cell in field.free_cells:
            scenario = Field(field.cells.values())
            if scenario.update(cell):
                branches[cell] = -1 if depth % 2 else 1
            elif scenario.state == GameState.DRAW:
                branches[cell] = 0
            else:
                branches[cell] = self.minimax(scenario, depth + 1)
        if depth:
            return min(branches.values()) if depth % 2 else max(branches.values())
        else:
            return {
                1: [cell for cell in branches if branches[cell] == 1],
                0: [cell for cell in branches if branches[cell] == 0],
                -1: [cell for cell in branches if branches[cell] == -1]
            }

    def bot_hard(self):
        print('Making move level "hard"')
        all_moves = self.minimax()
        for score in (1, 0, -1):
            if all_moves[score]:
                self.make_random_move(all_moves[score])
                break

    def play(self):
        print(self.field)
        for turn in range(9):
            self.moves[self.players[turn % 2]]()
            print(self.field)
            if self.field.state != GameState.NOT_FINISHED:
                print(self.field.state.value)
                break

    def set_players(self, command):
        try:
            start_command, first_player, second_player = command.split()
            if all(player in self.moves for player in [first_player, second_player]):
                self.players = [first_player, second_player]
                return True
            else:
                return False
        except ValueError:
            return False

    def main(self):
        while True:
            command = input('Input command: > ')
            if command == 'exit':
                break
            elif self.set_players(command):
                self.field = Field()
                self.play()
            else:
                print('Bad parameters!')


if __name__ == '__main__':
    try:
        Game().main()
    except (KeyboardInterrupt, EOFError):
        print()
