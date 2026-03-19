import random
import sys
from dataclasses import dataclass

import pygame


# Game configuration
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PLAY_WIDTH = GRID_WIDTH * CELL_SIZE
PLAY_HEIGHT = GRID_HEIGHT * CELL_SIZE
SIDE_PANEL = 220
WINDOW_WIDTH = PLAY_WIDTH + SIDE_PANEL
WINDOW_HEIGHT = PLAY_HEIGHT
FPS = 60


SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
]

COLORS = [
    (0, 255, 255),  # I
    (255, 255, 0),  # O
    (160, 32, 240),  # T
    (65, 105, 225),  # J
    (255, 140, 0),  # L
    (50, 205, 50),  # S
    (220, 20, 60),  # Z
]

BACKGROUND = (20, 20, 20)
GRID_COLOR = (45, 45, 45)
BORDER_COLOR = (200, 200, 200)
TEXT_COLOR = (245, 245, 245)


@dataclass
class Piece:
    x: int
    y: int
    shape_index: int
    rotation: int = 0

    @property
    def shape(self):
        matrix = SHAPES[self.shape_index]
        for _ in range(self.rotation % 4):
            matrix = [list(row) for row in zip(*matrix[::-1])]
        return matrix

    @property
    def color(self):
        return COLORS[self.shape_index]


class Tetris:
    def __init__(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False

        self.fall_timer = 0
        self.fall_delay = 600  # milliseconds

    def new_piece(self):
        shape_index = random.randrange(len(SHAPES))
        shape = SHAPES[shape_index]
        width = len(shape[0])
        x = GRID_WIDTH // 2 - width // 2
        return Piece(x=x, y=0, shape_index=shape_index)

    def valid_position(self, piece, offset_x=0, offset_y=0, rotation_delta=0):
        test_piece = Piece(
            x=piece.x + offset_x,
            y=piece.y + offset_y,
            shape_index=piece.shape_index,
            rotation=piece.rotation + rotation_delta,
        )
        matrix = test_piece.shape

        for row_idx, row in enumerate(matrix):
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                grid_x = test_piece.x + col_idx
                grid_y = test_piece.y + row_idx

                if grid_x < 0 or grid_x >= GRID_WIDTH:
                    return False
                if grid_y >= GRID_HEIGHT:
                    return False
                if grid_y >= 0 and self.grid[grid_y][grid_x] is not None:
                    return False
        return True

    def lock_piece(self):
        matrix = self.current_piece.shape
        color = self.current_piece.color
        for row_idx, row in enumerate(matrix):
            for col_idx, cell in enumerate(row):
                if cell:
                    grid_x = self.current_piece.x + col_idx
                    grid_y = self.current_piece.y + row_idx
                    if grid_y < 0:
                        self.game_over = True
                        return
                    self.grid[grid_y][grid_x] = color

        cleared = self.clear_lines()
        if cleared:
            self.lines_cleared += cleared
            self.score += self.calculate_score(cleared)
            self.level = 1 + self.lines_cleared // 10
            self.fall_delay = max(120, 600 - (self.level - 1) * 40)

        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid_position(self.current_piece):
            self.game_over = True

    def clear_lines(self):
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = GRID_HEIGHT - len(new_grid)
        while len(new_grid) < GRID_HEIGHT:
            new_grid.insert(0, [None for _ in range(GRID_WIDTH)])
        self.grid = new_grid
        return cleared

    @staticmethod
    def calculate_score(lines):
        table = {1: 100, 2: 300, 3: 500, 4: 800}
        return table.get(lines, 0)

    def move(self, dx, dy):
        if self.valid_position(self.current_piece, offset_x=dx, offset_y=dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def rotate(self):
        if self.valid_position(self.current_piece, rotation_delta=1):
            self.current_piece.rotation += 1
            return

        # Basic wall kick
        for kick_x in (-1, 1, -2, 2):
            if self.valid_position(self.current_piece, offset_x=kick_x, rotation_delta=1):
                self.current_piece.x += kick_x
                self.current_piece.rotation += 1
                return

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2
        self.lock_piece()

    def soft_drop(self):
        if self.move(0, 1):
            self.score += 1
        else:
            self.lock_piece()

    def update(self, dt_ms):
        if self.game_over:
            return
        self.fall_timer += dt_ms
        if self.fall_timer >= self.fall_delay:
            self.fall_timer = 0
            if not self.move(0, 1):
                self.lock_piece()


def draw_grid(surface, game, font, big_font):
    surface.fill(BACKGROUND)

    # Play field border
    pygame.draw.rect(surface, BORDER_COLOR, (0, 0, PLAY_WIDTH, PLAY_HEIGHT), 2)

    # Grid lines
    for x in range(0, PLAY_WIDTH, CELL_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, PLAY_HEIGHT))
    for y in range(0, PLAY_HEIGHT, CELL_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (PLAY_WIDTH, y))

    # Locked blocks
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            color = game.grid[y][x]
            if color:
                pygame.draw.rect(
                    surface,
                    color,
                    (x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2),
                )

    # Current piece
    matrix = game.current_piece.shape
    color = game.current_piece.color
    for row_idx, row in enumerate(matrix):
        for col_idx, cell in enumerate(row):
            if cell:
                x = (game.current_piece.x + col_idx) * CELL_SIZE
                y = (game.current_piece.y + row_idx) * CELL_SIZE
                if y >= 0:
                    pygame.draw.rect(
                        surface, color, (x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)
                    )

    # Side panel
    panel_x = PLAY_WIDTH + 20
    title = big_font.render("Tetris", True, TEXT_COLOR)
    surface.blit(title, (panel_x, 20))

    score_text = font.render(f"Score: {game.score}", True, TEXT_COLOR)
    lines_text = font.render(f"Lines: {game.lines_cleared}", True, TEXT_COLOR)
    level_text = font.render(f"Level: {game.level}", True, TEXT_COLOR)
    surface.blit(score_text, (panel_x, 90))
    surface.blit(lines_text, (panel_x, 120))
    surface.blit(level_text, (panel_x, 150))

    info_lines = [
        "Controls:",
        "Left/Right: Move",
        "Up: Rotate",
        "Down: Soft drop",
        "Space: Hard drop",
        "R: Restart",
        "Esc: Quit",
    ]
    y = 220
    for line in info_lines:
        text = font.render(line, True, TEXT_COLOR)
        surface.blit(text, (panel_x, y))
        y += 28

    # Preview next piece
    next_title = font.render("Next:", True, TEXT_COLOR)
    surface.blit(next_title, (panel_x, 420))

    next_matrix = game.next_piece.shape
    next_color = game.next_piece.color
    preview_x = panel_x
    preview_y = 460
    for row_idx, row in enumerate(next_matrix):
        for col_idx, cell in enumerate(row):
            if cell:
                pygame.draw.rect(
                    surface,
                    next_color,
                    (
                        preview_x + col_idx * CELL_SIZE + 1,
                        preview_y + row_idx * CELL_SIZE + 1,
                        CELL_SIZE - 2,
                        CELL_SIZE - 2,
                    ),
                )

    if game.game_over:
        overlay = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        over_text = big_font.render("Game Over", True, (255, 90, 90))
        restart_text = font.render("Press R to restart", True, TEXT_COLOR)
        surface.blit(over_text, (PLAY_WIDTH // 2 - over_text.get_width() // 2, 240))
        surface.blit(restart_text, (PLAY_WIDTH // 2 - restart_text.get_width() // 2, 290))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    # Use bundled default font to avoid Windows sysfont lookup issues.
    font = pygame.font.Font(None, 32)
    big_font = pygame.font.Font(None, 52)

    game = Tetris()

    while True:
        dt_ms = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    game = Tetris()
                if game.game_over:
                    continue
                if event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    game.soft_drop()
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()

        game.update(dt_ms)
        draw_grid(screen, game, font, big_font)
        pygame.display.flip()


if __name__ == "__main__":
    main()
