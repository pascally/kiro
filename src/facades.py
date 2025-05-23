from enum import Enum
from typing import List, Optional, Tuple

from marshmallow_dataclass import dataclass, class_schema


class Engine(Enum):
    DUMMY = 'DUMMY'
    CASE = 'CASE'


@dataclass
class Mark:
    player_id: str
    round_index: int


@dataclass
class Cell:
    quantic_marks: List[Mark]
    collapsed_mark: Optional[Mark] = None


@dataclass
class Board:
    """
        for a list of cells [A, B, C, D, E, F, G, H, I] and a square_size of 3
        we'll have this Board
        A, B, C
        D, E, F
        G, H, I
    """
    cells: List[Cell]
    board_size: int
    cells_indexes_to_be_collapsed: Optional[Tuple[int, int]]
    engine: Engine


@dataclass
class StartGameRequest:
    engine: Engine


StartGameRequestSchema = class_schema(StartGameRequest)()


@dataclass
class StartGameResponse:
    board: Board


StartGameResponseSchema = class_schema(StartGameResponse)()


@dataclass
class MarkMove:
    first_cell: int
    second_cell: int


@dataclass
class CollapseMove:
    selected_cell: int


@dataclass
class PlayMoveRequest:
    mark_move: Optional[MarkMove]
    collapse_move: Optional[CollapseMove]
    previous_board: Board


PlayMoveRequestSchema = class_schema(PlayMoveRequest)()


@dataclass
class PlayMoveResponse:
    board: Board
    winner: Optional[str]


PlayMoveResponseSchema = class_schema(PlayMoveResponse)()
