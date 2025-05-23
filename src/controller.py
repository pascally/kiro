import json

from flask import request, Blueprint, Flask, jsonify

from configuration import CASE_ENGINE, DUMMY_ENGINE
from engines.base_engine import BaseEngine
from exceptions import InvalidEngineException, InvalidMoveException, GameIsOverException, InvalidBoardException
from facades import PlayMoveRequestSchema, PlayMoveRequest, StartGameResponseSchema, StartGameResponse, \
    PlayMoveResponseSchema, PlayMoveResponse, StartGameRequest, StartGameRequestSchema, Engine
from settings import ENDPOINTS

main_controller = Blueprint('main_controller', __name__)


def get_engine(_type: Engine) -> BaseEngine:
    if _type == Engine.DUMMY:
        return DUMMY_ENGINE
    elif _type == Engine.CASE:
        return CASE_ENGINE

    raise InvalidEngineException()


@main_controller.route(ENDPOINTS.GAME_START.value, methods=['POST'])
def start():
    req: StartGameRequest = StartGameRequestSchema.load(json.loads(request.data))

    return jsonify(
        StartGameResponseSchema.dump(
            StartGameResponse(
                get_engine(req.engine).start_game()
            )
        )
    )


@main_controller.route(ENDPOINTS.GAME_PLAY.value, methods=['POST'])
def play():
    req: PlayMoveRequest = PlayMoveRequestSchema.load(json.loads(request.data))

    if req.collapse_move is None and req.mark_move is None:
        return jsonify(
            error=str('collapse_move and mark_move cannot both be null')
        ), 400

    return jsonify(
        PlayMoveResponseSchema.dump(
            PlayMoveResponse(
                get_engine(req.previous_board.engine).play_move(
                    req.mark_move or req.collapse_move, req.previous_board
                ),
                None
            )
        )
    )


APP = Flask(__name__)

APP.register_blueprint(main_controller)


@APP.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, InvalidMoveException):
        return jsonify(
            error=str(e)
        ), 400

    if isinstance(e, InvalidEngineException):
        return jsonify(
            error=str(e)
        ), 404

    if isinstance(e, InvalidBoardException):
        return jsonify(
            error=str(e)
        ), 404

    if isinstance(e, GameIsOverException):
        return jsonify(
            PlayMoveResponseSchema.dump(
                PlayMoveResponse(
                    e.board,
                    e.winner_id
                )
            )
        ), 200

    return jsonify(
        error=f"Server Error: {str(e)}"
    ), 500
