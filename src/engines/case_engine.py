from typing import Union, Optional

from engines.base_engine import BaseEngine
from facades import MarkMove, Board, CollapseMove, Engine


class CaseEngine(BaseEngine):
    _ENGINE = Engine.CASE

    def _check_move_validity(self, move: Union[MarkMove, CollapseMove], previous_board: Board):
        raise NotImplementedError()

    def _update_board(self, move: Union[MarkMove, CollapseMove], board: Board):
        raise NotImplementedError()

    def _get_winner(self, board: Board) -> Optional[str]:
        raise NotImplementedError()
