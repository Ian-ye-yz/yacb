const boardElement = document.getElementById("board");

const statusElement =
    document.getElementById("status");

const lastMoveElement =
    document.getElementById("last-move");

const botMoveElement =
    document.getElementById("bot-move");

const errorElement =
    document.getElementById("error");

const colorSelect =
    document.getElementById("color");

const newGameButton =
    document.getElementById("new-game");


const pieces = {
    "K": "♚",
    "Q": "♛",
    "R": "♜",
    "B": "♝",
    "N": "♞",
    "P": "♟",

    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
};


let state = null;
let selected = null;


function fenToBoard(fen) {
    const placement = fen.split(" ")[0];
    const rows = placement.split("/");

    const board = {};

    for (let row = 0; row < 8; row++) {
        let file = 0;

        for (const symbol of rows[row]) {
            if (/\d/.test(symbol)) {
                file += Number(symbol);
                continue;
            }

            const square =
                "abcdefgh"[file] +
                (8 - row);

            board[square] = symbol;

            file++;
        }
    }

    return board;
}


function squareColor(file, rank) {
    return (file + rank) % 2 === 0
        ? "dark"
        : "light";
}


function legalTargets(square) {
    if (!state) {
        return [];
    }

    return state.legalMoves
        .filter(move => move.slice(0, 2) === square)
        .map(move => move.slice(2, 4));
}


function isCapture(target, board) {
    return board[target] !== undefined;
}


function renderBoard() {
    const board = fenToBoard(state.fen);

    boardElement.innerHTML = "";

    const humanColor = colorSelect.value;

    const files =
        humanColor === "white"
            ? "abcdefgh"
            : "hgfedcba";

    const ranks =
        humanColor === "white"
            ? [8, 7, 6, 5, 4, 3, 2, 1]
            : [1, 2, 3, 4, 5, 6, 7, 8];

    const targets =
        selected
            ? legalTargets(selected)
            : [];

    const lastMove = state.lastMove;

    for (const rank of ranks) {
        for (const fileName of files) {
            const square = `${fileName}${rank}`;

            const file =
                "abcdefgh".indexOf(fileName);

            const squareElement =
                document.createElement("div");

            squareElement.classList.add(
                "square",
                squareColor(file, rank)
            );

            squareElement.dataset.square = square;

            if (square === selected) {
                squareElement.classList.add("selected");
            }

            if (targets.includes(square)) {
                squareElement.classList.add(
                    isCapture(square, board)
                        ? "capture"
                        : "legal"
                );
            }

            if (
                lastMove &&
                (
                    lastMove.slice(0, 2) === square ||
                    lastMove.slice(2, 4) === square
                )
            ) {
                squareElement.classList.add("last");
            }

            if (board[square]) {
                const piece =
                    document.createElement("span");

                const symbol = board[square];

                piece.className = "piece";

                piece.classList.add(
                    symbol === symbol.toUpperCase()
                        ? "white-piece"
                        : "black-piece"
                );

                piece.textContent =
                    pieces[symbol];

                squareElement.appendChild(piece);
            }

            squareElement.addEventListener(
                "click",
                () => onSquareClick(square)
            );

            boardElement.appendChild(squareElement);
        }
    }
}


async function onSquareClick(square) {
    if (!state || state.gameOver) {
        return;
    }

    const board = fenToBoard(state.fen);

    if (!selected) {
        const targets = legalTargets(square);

        if (targets.length === 0) {
            return;
        }

        selected = square;
        renderBoard();

        return;
    }

    if (square === selected) {
        selected = null;
        renderBoard();

        return;
    }

    const candidate =
        selected + square;

    const legalMoves =
        state.legalMoves.filter(
            move =>
                move.startsWith(candidate)
        );

    if (legalMoves.length > 0) {
        let move = legalMoves[0];

        if (legalMoves.length > 1) {
            const promotion =
                prompt(
                    "Promote to q, r, b or n:",
                    "q"
                ) || "q";

            const requested =
                candidate +
                promotion.toLowerCase();

            if (legalMoves.includes(requested)) {
                move = requested;
            }
        }

        selected = null;

        await playMove(move);

        return;
    }

    if (legalTargets(square).length > 0) {
        selected = square;
    } else {
        selected = null;
    }

    renderBoard();
}


async function playMove(move) {
    errorElement.textContent = "";
    botMoveElement.textContent = "Thinking...";

    try {
        const response = await fetch("/move", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                move,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Move failed."
            );
        }

        state = data;

        botMoveElement.textContent =
            data.botMove || "—";

        render();
    } catch (error) {
        errorElement.textContent =
            error.message;

        botMoveElement.textContent = "—";
    }
}


function render() {
    renderBoard();

    lastMoveElement.textContent =
        state.lastMove || "—";

    if (state.gameOver) {
        statusElement.textContent =
            `${state.result} — ${state.reason}`;

        return;
    }

    statusElement.textContent =
        `${state.turn} to move`;
}


async function newGame() {
    selected = null;

    errorElement.textContent = "";
    botMoveElement.textContent = "—";

    const response = await fetch("/new", {
        method: "POST",

        headers: {
            "Content-Type": "application/json",
        },

        body: JSON.stringify({
            color: colorSelect.value,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        errorElement.textContent =
            data.error || "Could not create game.";

        return;
    }

    state = data;

    if (data.botMove) {
        botMoveElement.textContent =
            data.botMove;
    }

    render();
}


newGameButton.addEventListener(
    "click",
    newGame
);

newGame();