import chess

class YACB:
    def __init__(self, color = chess.WHITE, board = chess.Board()):
        self.board = board
        self.values = {
            chess.PAWN: 2,
            chess.KNIGHT: 3.2,
            chess.BISHOP: 3.3,
            chess.ROOK: 4.5,
            chess.QUEEN: 9,
            chess.KING: 1
        }
        self.positionalValue = {
            chess.PAWN:  [
                [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # rank 1
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],  # rank 2
                [1.03, 1.04, 1.08, 1.10, 1.10, 1.08, 1.04, 1.03],  # rank 3
                [1.10, 1.12, 1.15, 1.18, 1.18, 1.15, 1.12, 1.10],  # rank 4
                [1.18, 1.20, 1.25, 1.28, 1.28, 1.25, 1.20, 1.18],  # rank 5
                [1.35, 1.40, 1.45, 1.50, 1.50, 1.45, 1.40, 1.35],  # rank 6
                [1.80, 1.90, 2.00, 2.10, 2.10, 2.00, 1.90, 1.80],  # rank 7
                [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # rank 8
            ],
            chess.KNIGHT: [
                [0.75, 0.80, 0.85, 0.85, 0.85, 0.85, 0.80, 0.75],
                [0.80, 0.90, 0.95, 1.00, 1.00, 0.95, 0.90, 0.80],
                [0.85, 0.95, 1.05, 1.10, 1.10, 1.05, 0.95, 0.85],
                [0.85, 1.00, 1.10, 1.15, 1.15, 1.10, 1.00, 0.85],
                [0.85, 1.00, 1.10, 1.15, 1.15, 1.10, 1.00, 0.85],
                [0.85, 0.95, 1.05, 1.10, 1.10, 1.05, 0.95, 0.85],
                [0.80, 0.90, 0.95, 1.00, 1.00, 0.95, 0.90, 0.80],
                [0.75, 0.80, 0.85, 0.85, 0.85, 0.85, 0.80, 0.75],
            ],
            chess.BISHOP: [
                [0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.90],
                [0.95, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.95],
                [0.95, 1.00, 1.05, 1.05, 1.05, 1.05, 1.00, 0.95],
                [0.95, 1.02, 1.05, 1.08, 1.08, 1.05, 1.02, 0.95],
                [0.95, 1.02, 1.05, 1.08, 1.08, 1.05, 1.02, 0.95],
                [0.95, 1.00, 1.05, 1.05, 1.05, 1.05, 1.00, 0.95],
                [0.95, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.95],
                [0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.90],
            ],

            chess.ROOK: [
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
                [1.05, 1.05, 1.05, 1.05, 1.05, 1.05, 1.05, 1.05],  # 7th rank
                [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
            ],

            chess.QUEEN: [
                [0.98, 0.98, 0.98, 1.00, 1.00, 0.98, 0.98, 0.98],
                [0.98, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.98],
                [0.98, 1.00, 1.02, 1.02, 1.02, 1.02, 1.00, 0.98],
                [1.00, 1.00, 1.02, 1.04, 1.04, 1.02, 1.00, 1.00],
                [1.00, 1.00, 1.02, 1.04, 1.04, 1.02, 1.00, 1.00],
                [0.98, 1.00, 1.02, 1.02, 1.02, 1.02, 1.00, 0.98],
                [0.98, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.98],
                [0.98, 0.98, 0.98, 1.00, 1.00, 0.98, 0.98, 0.98],
            ],

            chess.KING: [
                [1.08, 1.10, 1.05, 0.90, 0.90, 1.05, 1.10, 1.08],
                [1.05, 1.05, 1.00, 0.90, 0.90, 1.00, 1.05, 1.05],
                [0.95, 0.95, 0.92, 0.88, 0.88, 0.92, 0.95, 0.95],
                [0.90, 0.90, 0.88, 0.85, 0.85, 0.88, 0.90, 0.90],
                [0.88, 0.88, 0.85, 0.82, 0.82, 0.85, 0.88, 0.88],
                [0.85, 0.85, 0.82, 0.80, 0.80, 0.82, 0.85, 0.85],
                [0.82, 0.82, 0.80, 0.78, 0.78, 0.80, 0.82, 0.82],
                [0.80, 0.80, 0.78, 0.75, 0.75, 0.78, 0.80, 0.80],
            ]
        }
        self.color = color
        if self.color == chess.BLACK:
            self.positionalValue[chess.PAWN].reverse()
            self.positionalValue[chess.ROOK].reverse()
            self.positionalValue[chess.KING].reverse()
        self.opponentPositionalValue = {
            typ: table[::-1]
            for typ, table in self.positionalValue.items()
        }
    def evaluate(self, board: chess.Board):
        if board.is_checkmate():
            if board.turn == self.color:
                # My turn, but I have no legal move => I got mated
                return -10000
            else:
                return 10000
        evaluation = 0
        for typ, val in self.values.items():
            for i in board.pieces(typ, self.color):
                rk, fl = chess.square_rank(i), chess.square_file(i)
                evaluation += self.positionalValue[typ][rk][fl] * val
            # evaluation += len(board.pieces(typ, self.color)) * val
            for i in board.pieces(typ, not self.color):
                rk, fl = chess.square_rank(i), chess.square_file(i)
                evaluation -= self.opponentPositionalValue[typ][rk][fl] * val
            # evaluation -= len(board.pieces(typ, not self.color)) * val
        return evaluation
    def minimax(self, board: chess.Board, depth):
        if depth == 0 or board.is_game_over():
            return [self.evaluate(board), None]
        if board.turn == self.color:
            best = -float("inf")
            bestMove = None
            for move in board.legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1)[0]
                board.pop()
                if score > best:
                    best = score
                    bestMove = move
            return [best, bestMove]
        else:
            best = float("inf")
            bestMove = None
            for move in board.legal_moves:
                board.push(move)
                score = self.minimax(board, depth - 1)[0]
                board.pop()
                if score < best:
                    best = score
                    bestMove = move
            return [best, bestMove]
    def getNextMove(self):
        return self.minimax(self.board, 3)[1]
    def move(self, move):
        self.board.push(move)