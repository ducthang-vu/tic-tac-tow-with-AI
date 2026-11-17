"""Tests for tic_tac_toe.py, using only the standard library.

Run from the repository root with:
    python3 -m unittest discover -s tests -v
"""
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import tic_tac_toe as ttt  # noqa: E402


def make_field(rows):
    """Build a Field from three 3-character strings, top row first (y=3 down to y=1)."""
    assert all(len(r) == 3 for r in rows)
    return ttt.Field(''.join(rows))


def run_game(commands):
    """Run Game.main() with scripted input and return everything it printed."""
    with mock.patch('builtins.input', side_effect=commands), \
            contextlib.redirect_stdout(io.StringIO()) as out:
        ttt.Game().main()
    return out.getvalue()


class FieldTests(unittest.TestCase):
    def test_empty_field_has_nine_free_cells(self):
        self.assertEqual(len(ttt.Field().free_cells), 9)

    def test_first_symbol_is_x(self):
        self.assertEqual(ttt.Field().symbol, 'X')

    def test_symbol_alternates(self):
        field = ttt.Field()
        field.update((1, 1))
        self.assertEqual(field.symbol, 'O')

    def test_every_winning_line_is_detected(self):
        lines = {
            'bottom row': [(1, 1), (2, 1), (3, 1)],
            'middle row': [(1, 2), (2, 2), (3, 2)],
            'top row': [(1, 3), (2, 3), (3, 3)],
            'left column': [(1, 1), (1, 2), (1, 3)],
            'middle column': [(2, 1), (2, 2), (2, 3)],
            'right column': [(3, 1), (3, 2), (3, 3)],
            'main diagonal': [(1, 1), (2, 2), (3, 3)],
            'anti diagonal': [(3, 1), (2, 2), (1, 3)],
        }
        for name, line in lines.items():
            with self.subTest(name):
                field = ttt.Field()
                for cell in line:
                    field.cells[cell] = 'X'
                self.assertTrue(field.evaluate(line[-1]))

    def test_update_reports_win_and_sets_state(self):
        field = ttt.Field()
        for cell in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            field.update(cell)
        self.assertTrue(field.update((3, 1)))  # X completes the bottom row
        self.assertEqual(field.state, ttt.GameState.X_WINS)

    def test_no_false_win_from_a_diagonal_the_move_is_not_on(self):
        field = make_field(['X  ', ' X ', '  X'])  # full main diagonal of X
        self.assertFalse(field.evaluate((1, 2)))  # cell (1,2) is not on it

    def test_draw_is_detected_when_board_fills_without_a_winner(self):
        # Board with no winning line, one cell left: bottom-right (3,1).
        field = make_field(['XOX', 'XOO', 'OX '])
        self.assertFalse(field.update((3, 1)))
        self.assertEqual(field.state, ttt.GameState.DRAW)

    def test_update_rejects_out_of_range_coordinates(self):
        with self.assertRaises(IndexError):
            ttt.Field().update((0, 1))
        with self.assertRaises(IndexError):
            ttt.Field().update((1, 4))

    def test_update_rejects_occupied_cell(self):
        field = ttt.Field()
        field.update((2, 2))
        with self.assertRaises(ttt.OccupiedCell):
            field.update((2, 2))


class GameTests(unittest.TestCase):
    def test_constructor_does_not_read_input(self):
        with mock.patch('builtins.input', side_effect=AssertionError('read input')):
            game = ttt.Game()
        self.assertIsNone(game.field)

    def test_set_players_accepts_valid_names(self):
        game = ttt.Game()
        self.assertTrue(game.set_players('start user hard'))
        self.assertEqual(game.players, ['user', 'hard'])

    def test_set_players_rejects_unknown_player_or_wrong_count(self):
        game = ttt.Game()
        self.assertFalse(game.set_players('start user nobody'))
        self.assertFalse(game.set_players('start user'))

    def test_medium_bot_takes_a_winning_move(self):
        game = ttt.Game()
        game.field = make_field(['  X', 'OO ', 'XX '])  # O to move; (3,2) wins for O
        with contextlib.redirect_stdout(io.StringIO()):
            game.bot_medium()
        self.assertEqual(game.field.cells[(3, 2)], 'O')
        self.assertEqual(game.field.state, ttt.GameState.O_WINS)

    def test_medium_bot_blocks_opponent_win(self):
        game = ttt.Game()
        game.field = make_field(['   ', 'O  ', 'XX '])  # O to move; X threatens (3,1)
        with contextlib.redirect_stdout(io.StringIO()):
            game.bot_medium()
        self.assertEqual(game.field.cells[(3, 1)], 'O')

    def test_hard_bot_takes_an_immediate_win(self):
        game = ttt.Game()
        game.field = make_field(['  X', 'OO ', 'XX '])  # O to move; (3,2) wins now
        with contextlib.redirect_stdout(io.StringIO()):
            game.bot_hard()
        self.assertEqual(game.field.state, ttt.GameState.O_WINS)

    def test_hard_vs_hard_is_a_draw(self):
        output = run_game(['start hard hard', 'exit'])
        self.assertTrue(output.rstrip().endswith('Draw'), output)

    def test_bot_combinations_all_finish(self):
        for first in ('easy', 'medium', 'hard'):
            for second in ('easy', 'medium', 'hard'):
                with self.subTest(first=first, second=second):
                    output = run_game([f'start {first} {second}', 'exit'])
                    self.assertTrue(
                        any(output.rstrip().endswith(r) for r in ('X wins', 'O wins', 'Draw')),
                        output)

    def test_user_game_with_input_errors(self):
        commands = ['start user user',
                    'a b',    # not numbers
                    '4 1',    # out of range
                    '1 1',    # X
                    '1 1',    # occupied
                    '2 1',    # O
                    '1 2',    # X
                    '2 2',    # O
                    '1 3',    # X completes the left column
                    'exit']
        output = run_game(commands)
        self.assertIn('You should enter numbers!', output)
        self.assertIn('Coordinates should be from 1 to 3!', output)
        self.assertIn('This cell is occupied! Choose another one!', output)
        self.assertTrue(output.rstrip().endswith('X wins'), output)

    def test_wrong_number_of_coordinates_has_its_own_message(self):
        for entry in ['1', '1 2 3']:
            with self.subTest(entry=entry):
                output = run_game(['start user user', entry, '1 1', '2 1', '1 2', '2 2', '1 3', 'exit'])
                self.assertIn('Enter exactly two coordinates!', output)
                self.assertNotIn('You should enter numbers!', output)

    def test_bad_command_prints_error(self):
        self.assertIn('Bad parameters!', run_game(['start user nobody', 'exit']))


if __name__ == '__main__':
    unittest.main()
