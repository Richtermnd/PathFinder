import math
import random
from typing import Self
from functools import total_ordering

from perlin_noise import PerlinNoise


@total_ordering
class Node:
    # Store max values to calculate color
    max_h = 1
    max_g = 1

    def __init__(self, x, y, is_obstacle, grid) -> None:
        self.pos = self.x, self.y = x, y
        self.grid: Grid = grid
        self.is_point = False

        self.is_obstacle = is_obstacle
        self.is_visited = False
        self._g = float('inf')
        self._h = float('inf')
        self.parent: None | Node = None

    def neighbors(self, cross=False) -> list[Self]:
        start_y, end_y = max(0, self.y - 1), min(self.grid.h, self.y + 2)
        start_x, end_x = max(0, self.x - 1), min(self.grid.w, self.x + 2)
        res = []
        for row in self.grid._grid[start_y:end_y]:
            for n_node in row[start_x:end_x]:
                dx, dy = self.x - n_node.x, self.y - n_node.y
                if cross and dx * dy:
                    continue
                if self is n_node:
                    continue
                res.append(n_node)
        return res

    def dist(self, other: Self):
        return round(math.dist(self.pos, other.pos), 2)

    def reset(self):
        self.is_visited = False
        self._g = float('inf')
        self._h = float('inf')
        self.parent = None

    @property
    def color(self):
        if self.is_point:
            return (255, 0, 0)
        # Obstacle - dark gray.
        if self.is_obstacle:
            return (64, 64, 64)  # 2 ** 7 - 2 ** 6
        # Not explored - light gray.
        if not self.is_explored:
            return (192, 192, 192)  # 2 ** 7 + 2 ** 6
        # Red always max, cuz it's pretty.
        r = 255
        # Green depend from h.
        g = int(255 * self.h / Node.max_h)
        # Blue depend from g.
        b = int(255 * self.g / Node.max_g)
        # Explored, but not visited
        if not self.is_visited:
            color_scale = 0.6
            r = int(r * color_scale)
            g = int(g * color_scale)
            b = int(b * color_scale)

        return (r, g, b)

    @property
    def is_explored(self):
        return self.f != float('inf')

    @property
    def f(self):
        return round(self._h + self._g, 2)

    @property
    def h(self):
        return round(self._h, 2)

    @h.setter
    def h(self, value):
        if value != float('inf'):
            Node.max_h = max(Node.max_h, value)
        self._h = value

    @property
    def g(self):
        return round(self._g, 2)

    @g.setter
    def g(self, value):
        if value != float('inf'):
            Node.max_g = max(Node.max_g, value)
        self._g = value

    def __hash__(self) -> int:
        return hash(self.pos)

    def __eq__(self, other):
        return (self.f, self.h, self.g) == (other.f, other.h, other.g)

    def __lt__(self, other):
        return (self.f, self.h, self.g) < (other.f, other.h, other.g)

    def __str__(self) -> str:
        return '#' if self.is_obstacle else ' '


class Grid:
    def __init__(self, w, h) -> None:
        self.size = self.w, self.h = w, h
        self._grid = [[Node(x, y, False, self) for x in range(w)] for y in range(h)]
        self._start = self._grid[0][0]
        self._finish = self._grid[h - 1][w - 1]

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value: Node | tuple[int, int]):
        if isinstance(value, Node):
            self._start = value
        elif isinstance(value, tuple[int, int]):
            self._start = self._grid[value[1]][value[0]]
        else:
            raise TypeError

    @property
    def finish(self):
        return self._finish

    @finish.setter
    def finish(self, value: Node | tuple[int, int]):
        if isinstance(value, Node):
            self._finish = value
        elif isinstance(value, tuple[int, int]):
            self._finish = self._grid[value[1]][value[0]]
        else:
            raise TypeError

    def reset(self):
        Node.max_g = 1
        Node.max_h = 1
        for row in self._grid:
            for node in row:
                node.reset()

    def image(self) -> tuple[tuple[tuple[int, int, int]]]:
        return tuple(tuple(node.color for node in row) for row in self._grid)

    def __getitem__(self, key: tuple[int, int]) -> Node:
        x, y = key
        return self._grid[y][x]

    def __iter__(self) -> Node:
        for x in range(self.w):
            for y in range(self.h):
                yield self[x, y]

    def __str__(self) -> str:
        return '\n'.join(''.join('@' if node is self.start or node is self.finish else str(node) for node in row) for row in self._grid)


    @staticmethod
    def load_file(filename: str):
        with open(filename) as f:
            grid = f.readlines()
            w, h = len(grid[0].strip("\n")), len(grid)
            print(w, h)
            res = Grid(w, h)
            is_second_point = False
            for y, row in enumerate(grid):
                for x, cell in enumerate(row.strip("\n")):
                    node = res[x, y]
                    if cell == '@':
                        if is_second_point:
                            res.finish = node
                        else:
                            res.start = node
                            is_second_point = True
                        node.is_point = True
                    elif cell == '#':
                        node.is_obstacle = True
        return res


class MazeGrid(Grid):
    def __init__(self, w, h) -> None:
        super().__init__(w * 2 + 1, h * 2 + 1)
        for node in self:
            node.is_obstacle = True

        # Generate maze.
        x, y = random.randrange(1, self.w, 2), random.randrange(1, self.h, 2)
        self[x, y].is_obstacle = False
        track = [self[x, y]]
        while track:
            node = track[-1]
            neighbors = self.maze_neighbors(node, True)
            if len(neighbors) == 0:
                track.pop()
            else:
                n_node: Node = random.choice(neighbors)
                n_node.is_obstacle = False
                self[(node.x + n_node.x) // 2, (node.y + n_node.y) // 2].is_obstacle = False
                track.append(n_node)

        # Place start and finish.
        free_nodes: list[Node] = [node for node in self if not node.is_obstacle]
        self.start = random.choice(free_nodes)
        self.start.is_point = True
        self.finish = random.choice(free_nodes)
        self.finish.is_point = True
        while self.start.dist(self.finish) < 0.4 * math.hypot(self.h, self.w):
            self.start.is_point = False
            self.finish.is_point = False
            self.start = random.choice(free_nodes)
            self.finish = random.choice(free_nodes)
            self.start.is_point = True
            self.finish.is_point = True

    def maze_neighbors(self, node: Node, is_wall=False):
        res = []
        x, y = node.pos

        if y > 1 and (self[x, y - 2].is_obstacle is is_wall):
            res.append(self[x, y - 2])

        if y < self.h - 2 and (self[x, y + 2].is_obstacle is is_wall):
            res.append(self[x, y + 2])

        if x > 1 and (self[x - 2, y].is_obstacle is is_wall):
            res.append(self[x - 2, y])

        if x < self.w - 2 and (self[x + 2, y].is_obstacle is is_wall):
            res.append(self[x + 2, y])
        return res



class RandomSurface(Grid):
    def __init__(self, w, h) -> None:
        super().__init__(w, h)
        noise = PerlinNoise(octaves=min(w, h) // 4)
        for x in range(w):
            for y in range(h):
                if self[x, y].is_point:
                    continue
                self[x, y].is_obstacle = noise((x / w, y / h)) > 0.1

        # Place start and finish.
        free_nodes: list[Node] = [node for node in self if not node.is_obstacle]
        self.start = random.choice(free_nodes)
        self.start.is_point = True
        self.finish = random.choice(free_nodes)
        self.finish.is_point = True
        while self.start.dist(self.finish) < 0.5 * math.hypot(self.h, self.w):
            self.start.is_point = False
            self.finish.is_point = False
            self.start = random.choice(free_nodes)
            self.finish = random.choice(free_nodes)
            self.start.is_point = True
            self.finish.is_point = True

    def num_grid(self):
        return [[int(self[x, y].is_obstacle) for x in range(self.w)] for y in range(self.h)]
