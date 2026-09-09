from pgl import GWindow, GRect
from random import randint


def make_grid(width, height):
    """Generates and seeds a random initial grid of the desired size"""
    grid = [[randint(0, 1) for _ in range(width)] for _ in range(height)]
    return grid


def get_neighbor_sum(row, col, grid):
    """Manually sums the neigboring points around a cell, being
    careful to account for edges properly.
    """
    g_width = len(grid[0])
    g_height = len(grid)
    sum = 0
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            new_r = row + dr
            new_c = col + dc
            if (0 <= new_r < g_height) and (0 <= new_c < g_width):
                sum += grid[new_r][new_c]
    sum -= grid[row][col]
    return sum


def get_all_neighbor_sums(grid):
    """Computes the number of neighbors surround each cell
    for the entire grid.
    """
    try:  # Try to use 2dconvolutions, as I'm pretty sure it is faster
        from scipy.signal import convolve2d
        import numpy as np

        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        return convolve2d(grid, kernel, mode="same")
    except ImportError:  # Falling back to basic computation
        g_width = len(grid[0])
        g_height = len(grid)
        sums = [
            [get_neighbor_sum(r, c, grid) for c in range(g_width)]
            for r in range(g_height)
        ]
        return sums


def play(grid, update_function):
    """Creates the window and plays the iterative animation"""

    NCELL_W = len(grid[0])
    NCELL_H = len(grid)
    CELL_SIZE = min(800 // NCELL_W, 800 // NCELL_H)
    GWIDTH = NCELL_W * CELL_SIZE
    GHEIGHT = NCELL_H * CELL_SIZE

    def toggle_play(e):
        gw.playing = not gw.playing

    def draw(e):
        mx, my = e.get_x(), e.get_y()
        sq = gw.get_element_at(mx, my)
        for row_id, row in enumerate(squares):
            if sq in row:
                col_id = row.index(sq)
                break
        grid[row_id][col_id] = 1
        sq.set_color(scalar_to_hex(255))

    def update_new():
        if gw.playing:
            neighbor_sums = get_all_neighbor_sums(grid)
            for r in range(NCELL_H):
                for c in range(NCELL_W):
                    sq = squares[r][c]
                    if sq:
                        current = grid[r][c]
                        neighbor_sum = neighbor_sums[r][c]
                        new = update_function(current, neighbor_sum)
                        grid[r][c] = new
                        sq.set_color(scalar_to_hex(new * 255))

    gw = GWindow(GWIDTH, GHEIGHT)
    gw.playing = False
    squares = []
    for r in range(NCELL_H):
        row = []
        for c in range(NCELL_W):
            sq = GRect(CELL_SIZE * c, CELL_SIZE * r, CELL_SIZE, CELL_SIZE)
            sq.set_filled(True)
            sq.set_color(scalar_to_hex(grid[r][c] * 255))
            gw.add(sq)
            row.append(sq)
        squares.append(row)

    gw.set_interval(update_new, 100)
    gw.add_event_listener("click", toggle_play)
    gw.add_event_listener("drag", draw)


def scalar_to_hex(value):
    v = max(0, min(255, int(value)))
    h = f"{v:02x}"
    return f"#{h}{h}{h}".upper()


if __name__ == "__main__":

    def conway(state, neighbors):
        if state == 1 and neighbors < 2:
            return 0
        elif state == 1 and neighbors > 3:
            return 0
        elif state == 0 and neighbors == 3:
            return 1
        else:
            return state

    g = make_grid(50, 50)
    play(g, conway)
