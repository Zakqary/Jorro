import tkinter as tk
import random
import json

CELL_SIZE = 60
BOARD_SIZE = 9

class Piece:
    def __init__(self, player, kind):
        self.player = player
        self.kind = kind

    def __str__(self):
        return f"{self.kind}{self.player}"

class Game:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=BOARD_SIZE * CELL_SIZE, height=BOARD_SIZE * CELL_SIZE)
        self.canvas.grid(row=0, column=0, rowspan=20)
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = 1
        self.selected = None
        self.valid_moves = []
        self.history = []
        self.captured_p1 = []
        self.captured_p2 = [] 

        self.status = tk.Label(root, text="Player 1's turn", font=("Arial", 14))
        self.status.grid(row=0, column=1, sticky="nw", padx=10)

        guide_text = (
            "Piece Movement Guide:\n"
            "D: Diagonal 1 square any direction\n"
            "F: 1 square forward/back/left/right (no diagonal)\n"
            "H: Left/Right any squares, or 1 square forward/back\n"
            "J: Jump 2 squares in any direction\n"
            "W: Like F but is special (forced capture rule)\n"
            "S: Exactly 2 or 3 squares any direction (no jumping over pieces)\n"
        )
        self.guide_label = tk.Label(root, text=guide_text, justify="left", font=("Arial", 12))
        self.guide_label.grid(row=1, column=1, sticky="nw", padx=10, pady=(10,0))

        self.captured_frame = tk.Frame(root)
        self.captured_frame.grid(row=2, column=1, sticky="nw", padx=10, pady=(20,0))

        tk.Label(self.captured_frame, text="Captured Pieces:", font=("Arial", 12, "underline")).pack(anchor="w")

        self.captured_by_p1_label = tk.Label(self.captured_frame, text="Captured by Player 1: ", font=("Arial", 12))
        self.captured_by_p1_label.pack(anchor="w")

        self.captured_by_p2_label = tk.Label(self.captured_frame, text="Captured by Player 2: ", font=("Arial", 12))
        self.captured_by_p2_label.pack(anchor="w")

        self.init_pieces_random()
        self.canvas.bind("<Button-1>", self.click)
        self.draw_board()
        self.update_captured_display()

    def init_pieces_random(self):
        kinds = ['D', 'D', 'F', 'F', 'H', 'H', 'J', 'J', 'F']
        kinds[kinds.index('F')] = 'W'
        kinds[kinds.index('D')] = 'S'
        kinds[kinds.index('J')] = 'W'

        positions_p1 = [(r, c) for r in range(6, 9) for c in range(BOARD_SIZE)]
        positions_p2 = [(r, c) for r in range(0, 3) for c in range(BOARD_SIZE)]
        random.shuffle(positions_p1)
        random.shuffle(positions_p2)

        for i, kind in enumerate(kinds):
            r, c = positions_p1[i]
            self.board[r][c] = Piece(1, kind)
        for i, kind in enumerate(kinds):
            r, c = positions_p2[i]
            self.board[r][c] = Piece(2, kind)

    def draw_board(self):
        self.canvas.delete("all")
        tan = "#D2B48C"   # tan color
        brown = "#8B4513" # brown color
        soft_red = "#E57373"  # soft red
        soft_blue = "#64B5F6" # soft blue

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1, y1 = col * CELL_SIZE, row * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE

                fill = tan if (row + col) % 2 == 0 else brown
                if (row, col) in self.valid_moves:
                    fill = "lightgreen"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill)

                piece = self.board[row][col]
                if piece:
                    self.canvas.create_oval(
                        x1 + 10, y1 + 10, x2 - 10, y2 - 10,
                        fill="black"
                    )

                    color = soft_red if piece.player == 1 else soft_blue
                    self.canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text=piece.kind,
                        font=("Arial", 24, "bold"),
                        fill=color
                    )

    def click(self, event):
        col, row = event.x // CELL_SIZE, event.y // CELL_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return

        forced_pieces = self.forced_capture_pieces()

        if self.selected:
            if (row, col) in self.valid_moves:
                r1, c1 = self.selected
                self.move_piece(r1, c1, row, col)
                self.selected = None
                self.valid_moves = []
                self.check_game_over()
                return
            else:
                self.selected = None
                self.valid_moves = []
                self.status.config(text=f"Invalid move. Player {self.turn}'s turn.")
                self.draw_board()
                return

        piece = self.board[row][col]
        if piece and piece.player == self.turn:
            if forced_pieces and (row, col) not in forced_pieces:
                self.status.config(text=f"You must move a piece that can capture the opponent's W!")
                return
            self.selected = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)
            if forced_pieces:
                self.valid_moves = [pos for pos in self.valid_moves if self.board[pos[0]][pos[1]] and self.board[pos[0]][pos[1]].kind == 'W' and self.board[pos[0]][pos[1]].player != self.turn]
                if not self.valid_moves:
                    self.status.config(text="No valid forced capture moves!")
                    self.selected = None
                    self.valid_moves = []
        else:
            self.selected = None
            self.valid_moves = []

        self.draw_board()

    def get_valid_moves(self, r, c):
        piece = self.board[r][c]
        directions = []

        if piece.kind == 'D':
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            valid = []
            for dr, dc in directions:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                    dest = self.board[r2][c2]
                    if not dest or dest.player != piece.player:
                        valid.append((r2, c2))
            return valid

        elif piece.kind == 'F' or piece.kind == 'W':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            valid = []
            for dr, dc in directions:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                    dest = self.board[r2][c2]
                    if not dest or dest.player != piece.player:
                        valid.append((r2, c2))
            return valid

        elif piece.kind == 'H':
            valid = []
            for dr in [-1, 1]:
                r2 = r + dr
                if 0 <= r2 < BOARD_SIZE:
                    if not self.board[r2][c] or self.board[r2][c].player != piece.player:
                        valid.append((r2, c))
            for dc in range(c-1, -1, -1):
                if self.board[r][dc]:
                    if self.board[r][dc].player != piece.player:
                        valid.append((r, dc))
                    break
                valid.append((r, dc))
            for dc in range(c+1, BOARD_SIZE):
                if self.board[r][dc]:
                    if self.board[r][dc].player != piece.player:
                        valid.append((r, dc))
                    break
                valid.append((r, dc))
            return valid

        elif piece.kind == 'J':
            directions = [(2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (2, -2), (-2, 2)]
            valid = []
            for dr, dc in directions:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                    dest = self.board[r2][c2]
                    if not dest or dest.player != piece.player:
                        valid.append((r2, c2))
            return valid

        elif piece.kind == 'S':
            valid = []
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                          (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                for dist in [2, 3]:
                    r2 = r + dr * dist
                    c2 = c + dc * dist
                    if 0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE:
                        blocked = False
                        for step in range(1, dist):
                            rr = r + dr * step
                            cc = c + dc * step
                            if self.board[rr][cc]:
                                blocked = True
                                break
                        if blocked:
                            continue
                        dest = self.board[r2][c2]
                        if not dest or dest.player != piece.player:
                            valid.append((r2, c2))
            return valid

        return []

    def move_piece(self, r1, c1, r2, c2):
        piece = self.board[r1][c1]
        captured_piece = self.board[r2][c2]

        if captured_piece:
            if captured_piece.player == 1:
                self.captured_p2.append(captured_piece.kind)
            else:
                self.captured_p1.append(captured_piece.kind)

        self.history.append((r1, c1, r2, c2, piece.kind, piece.player,
                             captured_piece.kind if captured_piece else None,
                             captured_piece.player if captured_piece else None))

        self.board[r2][c2] = piece
        self.board[r1][c1] = None

        if captured_piece:
            print(f"Player {3 - self.turn}'s {captured_piece.kind} captured!")

        self.turn = 3 - self.turn
        self.status.config(text=f"Player {self.turn}'s turn")
        self.update_captured_display()
        self.draw_board()

    def update_captured_display(self):
        c1 = " ".join(sorted(self.captured_p1)) if self.captured_p1 else "(none)"
        c2 = " ".join(sorted(self.captured_p2)) if self.captured_p2 else "(none)"
        self.captured_by_p1_label.config(text=f"Captured by Player 1: {c1}")
        self.captured_by_p2_label.config(text=f"Captured by Player 2: {c2}")

    def check_game_over(self):
        p1_count = sum(piece.player == 1 for row in self.board for piece in row if piece)
        p2_count = sum(piece.player == 2 for row in self.board for piece in row if piece)
        if p1_count <= 1 or p2_count <= 1:
            winner = "Player 2" if p1_count <= 1 else "Player 1"
            self.status.config(text=f"{winner} wins!")
            self.canvas.unbind("<Button-1>")
            self.show_replay_option()

    def show_replay_option(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.grid(row=3, column=1, sticky="nw", padx=10, pady=10)
        tk.Button(btn_frame, text="View Replay", command=self.view_replay).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Save Replay", command=self.save_replay).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Load Replay", command=self.load_replay).pack(side=tk.LEFT)

    def view_replay(self):
        ReplayWindow(self.root, self.history)

    def save_replay(self):
        with open("replay.json", "w") as f:
            json.dump(self.history, f)
        self.status.config(text="Replay saved to replay.json")

    def load_replay(self):
        try:
            with open("replay.json", "r") as f:
                history = json.load(f)
            ReplayWindow(self.root, history)
        except Exception as e:
            self.status.config(text=f"Failed to load replay: {e}")

    def forced_capture_pieces(self):
        forced = []
        opponent = 3 - self.turn
        w_positions = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                       if self.board[r][c] and self.board[r][c].kind == 'W' and self.board[r][c].player == opponent]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece and piece.player == self.turn:
                    moves = self.get_valid_moves(r, c)
                    for mr, mc in moves:
                        if (mr, mc) in w_positions:
                            forced.append((r, c))
                            break
        return forced

class ReplayWindow:
    def __init__(self, root, history):
        self.top = tk.Toplevel(root)
        self.top.title("Replay")
        self.canvas = tk.Canvas(self.top, width=BOARD_SIZE * CELL_SIZE, height=BOARD_SIZE * CELL_SIZE)
        self.canvas.pack()
        self.history = history
        self.step = 0

        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.init_board()

        self.btn_frame = tk.Frame(self.top)
        self.btn_frame.pack()
        tk.Button(self.btn_frame, text="Previous", command=self.prev_move).pack(side=tk.LEFT)
        tk.Button(self.btn_frame, text="Next", command=self.next_move).pack(side=tk.LEFT)

        self.draw_board()

    def init_board(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                self.board[r][c] = None

    def draw_board(self):
        self.canvas.delete("all")
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x1, y1 = col * CELL_SIZE, row * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                fill = "white" if (row + col) % 2 == 0 else "lightgray"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill)
                piece = self.board[row][col]
                if piece:
                    color = "red" if piece.player == 1 else "blue"
                    self.canvas.create_oval(x1+10, y1+10, x2-10, y2-10, fill=color)
                    self.canvas.create_text((x1+x2)//2, (y1+y2)//2, text=piece.kind, fill="white", font=("Arial", 14, "bold"))

    def next_move(self):
        if self.step >= len(self.history):
            return
        move = self.history[self.step]
        r1, c1, r2, c2, kind, player, captured_kind, captured_player = move

        self.board[r1][c1] = None
        self.board[r2][c2] = Piece(player, kind)
        if captured_kind and captured_player:
            pass

        self.step += 1
        self.draw_board()

    def prev_move(self):
        if self.step == 0:
            return
        self.step -= 1
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for i in range(self.step):
            move = self.history[i]
            r1, c1, r2, c2, kind, player, captured_kind, captured_player = move
            self.board[r1][c1] = None
            self.board[r2][c2] = Piece(player, kind)
        self.draw_board()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Jorro")
    game = Game(root)
    root.mainloop()
