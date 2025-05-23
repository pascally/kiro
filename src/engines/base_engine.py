from copy import deepcopy
from random import randint, sample, choice
from typing import Tuple, List, Union, Optional

from exceptions import GameIsOverException
from facades import MarkMove, Board, Cell, CollapseMove


class BaseEngine:

    _ENGINE = None

    def __init__(self, board_size: int):
        self.board_size = board_size

    def start_game(self) -> Board:

        if self._ENGINE is None:
            raise ValueError('self._ENGINE is not defined')

        board = Board(
            [Cell([]) for i in range(0, self.board_size * self.board_size)],
            self.board_size,
            None,
            self._ENGINE
        )

        # we randomly decide to make the AI play the first move
        if choice([True, False]):
            ai_move = self._get_ai_move(board)
            self._update_board(ai_move, board)

        return board

    def play_move(self, move: Union[MarkMove, CollapseMove], previous_board: Board) -> Board:
        self._check_move_validity(move, previous_board)

        new_board = deepcopy(previous_board)

        # We first play player's move (self._update_board), check if there is a winner then
        # play AI move (built by self._get_ai_move) then check there's a winner again.
        # If not returned updated Board
        for m in [lambda: move, lambda: self._get_ai_move(new_board)]:
            self._update_board(m(), new_board)
            winner = self._get_winner(new_board)
            if winner is not None:
                raise GameIsOverException(
                    new_board,
                    winner
                )

        return new_board

    def _check_move_validity(self, move: Union[MarkMove, CollapseMove], previous_board: Board):
        """
        Check whether a move is legal, raising InvalidMoveException if not

        :param move: MarkMove
        :param previous_board: Board

        :raise InvalidMoveException
        """
        raise NotImplementedError()

    def _update_board(self, move: Union[MarkMove, CollapseMove], board: Board):
        """
        Update board object by applying move
        if relevant, set board.cells_indexes_to_be_collapsed to the indexes of the two cells that needs to be collapsed

        :param move: MarkMove
        :param previous_board: Board
        """
        raise NotImplementedError()

    def _get_winner(self, board: Board) -> Optional[str]:
        """
        check if  boardstate is final and a player won and return player id

        :param board: Board

        :return: str
        """
        raise NotImplementedError()

    def _get_ai_move(self, board: Board) -> Union[MarkMove, CollapseMove]:

        if board.cells_indexes_to_be_collapsed:
            i = randint(0, 1)
            return CollapseMove(
                board.cells_indexes_to_be_collapsed[i]
            )

        available_cells: List[Tuple[Cell, int]] = list(filter(
            lambda tu: tu[0].collapsed_mark is None,
            [(c, i) for i, c in enumerate(board.cells)],
        ))

        selected_cells = sample(available_cells, 2)

        return MarkMove(
            selected_cells[0][1],
            selected_cells[1][1],
        )


