from typing import Union, List, Tuple, Optional

from engines.base_engine import BaseEngine
from facades import MarkMove, Board, CollapseMove, Mark, Engine, Cell
from settings import PLAYER_1, PLAYER_2

STOP_AFTER_N_MARKS = 7


class DummyEngine(BaseEngine):
    """
        The engine does not implements the rules of the Quantic TicTacToe
        It's only here to provide an example of BaseEngine abstract methods implementation and
        allow a "kind of" play using play.py
    """
    _ENGINE = Engine.DUMMY

    def _check_move_validity(self, move: Union[MarkMove, CollapseMove], previous_board: Board):
        # Always valid for this engine
        return

    def _update_board(self, move: Union[MarkMove, CollapseMove], board: Board):
        # CollapseMove is not supported

        next_index = max([a.round_index for c in board.cells for a in c.quantic_marks] + [0]) + 1
        player_id = PLAYER_1 if next_index % 2 == 0 else PLAYER_2

        if isinstance(move, MarkMove):
            board.cells[move.first_cell].quantic_marks.append(Mark(player_id, next_index))
            board.cells[move.second_cell].quantic_marks.append(Mark(player_id, next_index))

    def _get_winner(self, board: Board) -> Optional[str]:
        # Return PLAYER_1 as winner when STOP_AFTER_N_MARKS cells has been marked at least once

        marked: List[Tuple[Cell, int]] = list(filter(
            lambda c: len(c.quantic_marks) > 0,
            board.cells,
        ))

        if len(marked) >= STOP_AFTER_N_MARKS:
            return PLAYER_1

        return None
