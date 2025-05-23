from enum import Enum

BOARD_SIZE = 3

class ENDPOINTS(Enum):
    GAME_START = '/games/start'
    GAME_PLAY = '/games/play'


PLAYER_1 = 'X'
PLAYER_2 = 'O'

PROTOCOL = 'http://'
HOSTNAME = '127.0.0.1'
PORT = 8081
