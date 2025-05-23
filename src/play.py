import sys
from typing import Union

import requests

from facades import StartGameResponseSchema, StartGameResponse, Engine, PlayMoveRequestSchema, PlayMoveRequest, \
    MarkMove, Board, CollapseMove, PlayMoveResponseSchema, PlayMoveResponse
from settings import PORT, HOSTNAME, PROTOCOL

SIZE_CELL = 18

URL = f'{PROTOCOL}{HOSTNAME}:{PORT}'

USE_DUMMY = False


def play_move(previous_board: Board, move: Union[MarkMove, CollapseMove]) -> PlayMoveResponse:
    r = requests.post(
        f'{URL}/games/play', json=PlayMoveRequestSchema.dump(
            PlayMoveRequest(
                move,
                None,
                previous_board

            ) if isinstance(move, MarkMove) else PlayMoveRequest(
                None,
                move,
                previous_board

            )
        )
    )

    return PlayMoveResponseSchema.load(r.json())


def print_board(board: Board):
    for index, cell in enumerate(board.cells):
        if index % board.board_size == 0:
            print('\n' + '-' * (SIZE_CELL + 1) * board.board_size)

        cell_name = f' ({index}) '
        if cell.collapsed_mark:
            cell_name = f' {cell.collapsed_mark.player_id}{cell.collapsed_mark.round_index} '
        else:
            cell_name += f" {' '.join([f'{m.player_id}{m.round_index}' for m in cell.quantic_marks])} "

        print(cell_name + (SIZE_CELL - len(cell_name)) * ' ' + '|', end='')

    print('\n' + '-' * (SIZE_CELL + 1) * board.board_size)


if __name__ == '__main__':

    r = requests.post(f'{URL}/games/start', json={'engine': (Engine.DUMMY if USE_DUMMY else Engine.CASE).value})

    if r.status_code != 200:
        print(f'\033[91mERR : {r.json()["error"]}\033[0m')

        sys.exit(0)

    start_response: StartGameResponse = StartGameResponseSchema.load(
        r.json()
    )

    board = start_response.board

    while True:
        print_board(board)
        if board.cells_indexes_to_be_collapsed:
            print(
                f'Which cell to collapse '
                f'between {board.cells_indexes_to_be_collapsed[0]} '
                f'and {board.cells_indexes_to_be_collapsed[1]}'
            )
            r = input('Type cell index :')

            response = play_move(board, CollapseMove(int(r)))

        else:
            print('Which cells to mark ?')
            first = input(
                f'first cell index :'
            )
            second = input(
                f'second cell index :'
            )

            response = play_move(board, MarkMove(int(first), int(second)))

        if response.winner:

            print(f'{response.winner} WON !')
            print_board(board)
            sys.exit(0)
        else:
            board = response.board
