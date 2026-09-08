import chess
from flask import Flask, jsonify, render_template, request

from yacb import YACB

app = Flask(__name__)

board = chess.Board()
human_color = chess.WHITE
bot = None


def make_bot():
    global bot
    bot = YACB(not human_color, board)


def game_state():
    outcome = board.outcome()

    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "gameOver": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None,
        "reason": outcome.termination.name if outcome else None,
        "legalMoves": [move.uci() for move in board.legal_moves],
        "lastMove": (
            board.peek().uci()
            if board.move_stack
            else None
        ),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/new")
def new_game():
    global board, human_color

    data = request.get_json()
    human_color = (
        chess.WHITE
        if data.get("color", "white") == "white"
        else chess.BLACK
    )

    board = chess.Board()
    make_bot()

    response = game_state()

    # If human chose black, bot makes the first move.
    if board.turn != human_color:
        move = bot.getNextMove()

        if move not in board.legal_moves:
            return jsonify({
                "error": f"Bot returned illegal move: {move}"
            }), 500

        bot.move(move)
        response = game_state()
        response["botMove"] = move.uci()

    return jsonify(response)


@app.get("/state")
def state():
    return jsonify(game_state())


@app.post("/move")
def move():
    data = request.get_json()
    uci = data.get("move")

    if board.is_game_over():
        return jsonify({"error": "Game is already over."}), 400

    if board.turn != human_color:
        return jsonify({"error": "It is not your turn."}), 400

    try:
        player_move = chess.Move.from_uci(uci)
    except ValueError:
        return jsonify({"error": "Invalid move format."}), 400

    if player_move not in board.legal_moves:
        return jsonify({"error": "Illegal move."}), 400

    bot.move(player_move)

    if board.is_game_over():
        return jsonify(game_state())

    bot_move = bot.getNextMove()

    if bot_move not in board.legal_moves:
        return jsonify({
            "error": f"Bot returned illegal move: {bot_move}"
        }), 500

    bot.move(bot_move)

    response = game_state()
    response["botMove"] = bot_move.uci()

    return jsonify(response)


if __name__ == "__main__":
    make_bot()
    app.run(debug=True, port=5000)