import json
import os
import sys
import threading
import time

import chess
import requests

from yacb import YACB


BASE_URL = "https://lichess.org"

TOKEN = ""

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
}


# ------------------------------------------------------------
# Basic API
# ------------------------------------------------------------

def get_account():
    response = requests.get(
        BASE_URL + "/api/account",
        headers=HEADERS,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


ACCOUNT = get_account()
BOT_ID = ACCOUNT["id"]


def api_post(path, data=None):
    response = requests.post(
        BASE_URL + path,
        headers=HEADERS,
        data=data,
        timeout=20,
    )

    if response.status_code == 429:
        print("Lichess rate limit reached. Waiting 60 seconds...")
        time.sleep(60)

        return api_post(path, data)

    if not response.ok:
        raise RuntimeError(
            f"Lichess API error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    return response


# ------------------------------------------------------------
# Challenges
# ------------------------------------------------------------

def accept_challenge(challenge_id):
    print(f"Accepting challenge {challenge_id}")

    api_post(
        f"/api/challenge/{challenge_id}/accept"
    )


def decline_challenge(
    challenge_id,
    reason="generic",
):
    print(
        f"Declining challenge {challenge_id}: "
        f"{reason}"
    )

    api_post(
        f"/api/challenge/{challenge_id}/decline",
        {
            "reason": reason,
        },
    )


def create_challenge(
    username,
    *,
    rated=False,
    color="random",
    clock_limit=300,
    clock_increment=3,
):
    """
    Challenge another Lichess account.

    clock_limit:
        initial clock in seconds

    clock_increment:
        increment per move in seconds
    """

    print()
    print(f"Challenging @{username}...")
    print(
        f"Time control: "
        f"{clock_limit // 60}+{clock_increment}"
    )
    print(
        "Rated:"
        if rated
        else "Casual:",
        rated,
    )
    print()

    response = api_post(
        f"/api/challenge/{username}",
        {
            "rated": str(rated).lower(),
            "color": color,

            "variant": "standard",

            "clock.limit": clock_limit,
            "clock.increment": clock_increment,
        },
    )

    data = response.json()

    challenge = data.get("challenge", data)

    challenge_id = challenge.get("id")

    print(
        "Challenge created:",
        challenge_id,
    )

    if challenge.get("url"):
        print(
            "Game/challenge:",
            challenge["url"],
        )

    return challenge_id


# ------------------------------------------------------------
# Board synchronization
# ------------------------------------------------------------

def make_board(initial_fen):
    if initial_fen in (
        None,
        "",
        "startpos",
    ):
        return chess.Board()

    return chess.Board(initial_fen)


def sync_board(
    board,
    initial_fen,
    moves_string,
):
    """
    Lichess sends the complete move history each time.

    Reconstructing the board from that history is simple and
    removes a whole class of synchronization bugs.
    """

    if initial_fen in (
        None,
        "",
        "startpos",
    ):
        board.reset()

    else:
        board.set_fen(initial_fen)

    for move_uci in moves_string.split():
        board.push_uci(move_uci)


# ------------------------------------------------------------
# Moves
# ------------------------------------------------------------

def send_move(game_id, move):
    print(
        f"[{game_id}] "
        f"YACB -> {move.uci()}"
    )

    api_post(
        f"/api/bot/game/{game_id}/move/{move.uci()}"
    )


def resign(game_id):
    print(
        f"[{game_id}] Resigning"
    )

    api_post(
        f"/api/bot/game/{game_id}/resign"
    )


# ------------------------------------------------------------
# Playing a position
# ------------------------------------------------------------

def handle_position(
    game_id,
    board,
    bot,
    bot_color,
    state,
):
    status = state.get(
        "status",
        "started",
    )

    if status != "started":
        print()
        print(
            f"[{game_id}] Game over"
        )

        print(
            "Status:",
            status,
        )

        winner = state.get("winner")

        if winner:
            print(
                "Winner:",
                winner,
            )

        print()

        return

    # Opponent's turn.
    if board.turn != bot_color:
        return

    print()
    print(
        f"[{game_id}] "
        f"{'White' if bot_color else 'Black'} "
        "to move"
    )

    print(board)
    print()

    move = bot.getNextMove()

    if move is None:
        print(
            f"[{game_id}] "
            "YACB returned no move."
        )

        return

    if move not in board.legal_moves:
        print(
            f"[{game_id}] "
            f"ERROR: YACB returned illegal move "
            f"{move}"
        )

        print(board)

        return

    send_move(
        game_id,
        move,
    )


# ------------------------------------------------------------
# Game stream
# ------------------------------------------------------------

def play_game(game_id):
    print()
    print(
        f"[{game_id}] Game started"
    )

    url = (
        BASE_URL
        + f"/api/bot/game/stream/{game_id}"
    )

    with requests.get(
        url,
        headers=HEADERS,
        stream=True,
        timeout=None,
    ) as response:

        response.raise_for_status()

        board = None
        bot = None

        bot_color = None
        initial_fen = "startpos"

        last_processed_moves = None

        for raw_line in response.iter_lines():
            if not raw_line:
                continue

            event = json.loads(raw_line)

            event_type = event.get(
                "type"
            )

            # ------------------------------------------------
            # Initial state
            # ------------------------------------------------

            if event_type == "gameFull":

                initial_fen = event.get(
                    "initialFen",
                    "startpos",
                )

                board = make_board(
                    initial_fen
                )

                white = event["white"]
                black = event["black"]

                white_id = (
                    white
                    .get("id", "")
                    .lower()
                )

                black_id = (
                    black
                    .get("id", "")
                    .lower()
                )

                if (
                    white_id
                    == BOT_ID.lower()
                ):
                    bot_color = chess.WHITE

                elif (
                    black_id
                    == BOT_ID.lower()
                ):
                    bot_color = chess.BLACK

                else:
                    raise RuntimeError(
                        "Could not determine "
                        "which side YACB is playing."
                    )

                state = event["state"]

                moves = state.get(
                    "moves",
                    "",
                )

                sync_board(
                    board,
                    initial_fen,
                    moves,
                )

                last_processed_moves = moves

                bot = YACB(
                    bot_color,
                    board,
                )

                opponent = (
                    black
                    if bot_color == chess.WHITE
                    else white
                )

                print(
                    f"[{game_id}] "
                    f"Playing against "
                    f"@{opponent.get('name', '?')}"
                )

                print(
                    f"[{game_id}] "
                    f"YACB is "
                    f"{'White' if bot_color else 'Black'}"
                )

                handle_position(
                    game_id,
                    board,
                    bot,
                    bot_color,
                    state,
                )

            # ------------------------------------------------
            # Updated state
            # ------------------------------------------------

            elif event_type == "gameState":

                if board is None:
                    continue

                moves = event.get(
                    "moves",
                    "",
                )

                # Streams can occasionally give us redundant
                # state messages. Don't think twice.
                if (
                    moves
                    == last_processed_moves
                ):
                    continue

                sync_board(
                    board,
                    initial_fen,
                    moves,
                )

                last_processed_moves = moves

                handle_position(
                    game_id,
                    board,
                    bot,
                    bot_color,
                    event,
                )

            elif event_type == "chatLine":
                pass

            else:
                print(
                    f"[{game_id}] "
                    f"Event: {event_type}"
                )


# ------------------------------------------------------------
# Challenge filtering
# ------------------------------------------------------------

def handle_incoming_challenge(event):
    challenge = event[
        "challenge"
    ]

    challenge_id = challenge[
        "id"
    ]

    challenger = (
        challenge
        .get("challenger", {})
        .get("name", "?")
    )

    variant = (
        challenge
        .get("variant", {})
        .get("key")
    )

    print()
    print(
        f"Incoming challenge "
        f"from @{challenger}"
    )

    print(
        "Variant:",
        variant,
    )

    if variant != "standard":
        decline_challenge(
            challenge_id,
            "variant",
        )

        return

    accept_challenge(
        challenge_id
    )


# ------------------------------------------------------------
# Main event stream
# ------------------------------------------------------------

def event_loop(
    accept_incoming=True,
):
    print()
    print(
        f"YACB logged in as @{ACCOUNT['username']}"
    )

    if accept_incoming:
        print(
            "Incoming challenges: ACCEPT"
        )

    else:
        print(
            "Incoming challenges: IGNORE"
        )

    print()

    url = (
        BASE_URL
        + "/api/stream/event"
    )

    with requests.get(
        url,
        headers=HEADERS,
        stream=True,
        timeout=None,
    ) as response:

        response.raise_for_status()

        for raw_line in response.iter_lines():

            if not raw_line:
                continue

            event = json.loads(
                raw_line
            )

            event_type = event.get(
                "type"
            )

            if event_type == "challenge":

                if accept_incoming:
                    handle_incoming_challenge(
                        event
                    )

            elif event_type == "gameStart":

                game_id = (
                    event["game"]["id"]
                )

                print()
                print(f"Game started!")
                print(f"Watch: https://lichess.org/{game_id}")
                print()

                thread = threading.Thread(
                    target=play_game,
                    args=(game_id,),
                    daemon=True,
                )

                thread.start()

            elif event_type == "gameFinish":

                game_id = (
                    event["game"]["id"]
                )

                print(
                    f"[{game_id}] Finished"
                )


# ------------------------------------------------------------
# Interactive frontend
# ------------------------------------------------------------

def print_menu():
    print()
    print("======================")
    print("       YACB BOT")
    print("======================")
    print()
    print("1. Wait for challenges")
    print("2. Challenge a player/bot")
    print()
    print("q. Quit")
    print()


def challenge_mode():
    username = input(
        "Opponent username: "
    ).strip()

    if not username:
        print(
            "No username provided."
        )

        return

    print()
    print("Choose time control:")
    print("1. 1+0")
    print("2. 3+0")
    print("3. 3+2")
    print("4. 5+3")
    print("5. 10+0")
    print()

    choice = input(
        "Time control [4]: "
    ).strip()

    controls = {
        "1": (60, 0),
        "2": (180, 0),
        "3": (180, 2),
        "4": (300, 3),
        "5": (600, 0),
        "": (300, 3),
    }

    clock_limit, clock_increment = (
        controls.get(
            choice,
            (300, 3),
        )
    )

    color = input(
        "Color "
        "[white/black/random] "
        "(default random): "
    ).strip().lower()

    if color not in (
        "white",
        "black",
        "random",
    ):
        color = "random"

    create_challenge(
        username,
        rated=False,
        color=color,
        clock_limit=clock_limit,
        clock_increment=clock_increment,
    )

    print()
    print(
        "Challenge sent."
    )

    print(
        "Waiting for opponent "
        "to accept..."
    )

    # We still need the event stream:
    # challenge accepted -> gameStart -> play_game()
    event_loop(
        accept_incoming=False
    )


def main():
    print(
        f"Authenticated as "
        f"@{ACCOUNT['username']}"
    )

    while True:
        print_menu()

        choice = input(
            "> "
        ).strip().lower()

        if choice == "1":
            event_loop(
                accept_incoming=True
            )

            return

        elif choice == "2":
            challenge_mode()

            return

        elif choice in (
            "q",
            "quit",
            "exit",
        ):
            return

        else:
            print(
                "Unknown option."
            )


if __name__ == "__main__":
    main()