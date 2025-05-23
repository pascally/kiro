from facades import Board


class InvalidMoveException(Exception):
    pass


class GameIsOverException(Exception):
    def __init__(self, board: Board, winner_id: str):
        self.board = board
        self.winner_id = winner_id


class InvalidEngineException(Exception):
    pass


class InvalidBoardException(Exception):
    pass
