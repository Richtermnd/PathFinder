from collections import deque
import heapq

from .grid import Node, Grid
from constants import *


def contain(array: list[Node], key: Node):
    """Мне лень разбираться как работает питоновский bisect, я свой бинарный поиск напишу (украл с вики)"""
    low, high = 0, len(array) - 1
    while low <= high:
        mid = (high + low) // 2
        if array[mid] is key:
            return True
        elif array[mid] < key:
            low = mid + 1
        else:
            high = mid - 1
    return False


class Algorithm:
    def __init__(self, grid: Grid) -> None:
        # Сетка - представление местности
        self.grid = grid
        self._alg = self._algorithm()
        self.start = self.grid.start
        self.finish = self.grid.finish
        self.path: list[tuple[int, int]] = []

        # statistic
        self.visited = 0
        self.explored = 0
        self.path_length = 0

    def _algorithm(self):
        raise NotImplementedError

    def build_path(self, target: Node):
        raise NotImplementedError
    
    def __iter__(self):
        self.grid.reset()
        self._alg = self._algorithm()
        return self

    def __next__(self):
        return self._alg.__next__()

    def solve(self):
        # Ha-ha...
        for _ in self:
            pass

    @property
    def statistic(self):
        return {
            'name': self.__class__.__name__,
            'path': self.path_length,
            'visited': self.visited,
            'explored': self.explored
        }


class Wave(Algorithm):
    def _algorithm(self):
        """Это обычный DFS с парой модификаций, ничего сложного"""
        # Обозначаем стартовый узел
        self.start.g = 0
        self.start.h = 0
        # Очередь
        queue = [self.start]
        # Пока очередь не пуста и конечный узел не посещён.
        while queue and not self.finish.is_visited:
            new_queue: list[Node] = []
            for node in queue:
                node.is_visited = True
                self.build_path(node)
                self.visited += 1
                for n_node in node.neighbors():
                    # Don't explore obstacle.
                    if n_node.is_obstacle:
                        continue
                    # Dont't explore visited.
                    if n_node.is_visited:
                        continue
                    # Don't explore twice.
                    if n_node not in new_queue:
                        new_queue.append(n_node)
                    # Explore.
                    new_g = node.g + node.dist(n_node)
                    n_node.g = min(n_node.g, new_g)
                    n_node.h = 0
                    self.explored += 1
                    if n_node is self.finish:
                        queue = [n_node]
                        break
                yield
            queue = new_queue

        self.build_path(self.finish)
        self.path_length = self.finish.g
        yield

    def build_path(self, target: Node):
        if target.is_visited:
            path = [target.pos]
            while target is not self.start:
                target = min(target.neighbors())
                path.append(target.pos)
        else:
            path = []
        self.path = path.copy()
        return self.path


class Dijkstra(Algorithm):
    def _algorithm(self):
        # Обозначаем стартовый узел.
        self.start.g = 0
        self.start.h = 0
        queue: set[Node] = {self.start}
        # Пока очередь существует.
        while queue:
            # Махинации с конвертацией множества в список
            node = sorted(queue)[0]
            queue.remove(node)
            # Помечаем узел
            node.is_visited = True
            self.build_path(node)
            self.visited += 1
            if self.finish.is_visited:
                break
            
            # Обходим соседей
            for n_node in node.neighbors():
                # Don't explore obstacle.
                if n_node.is_obstacle:
                    continue
                # Dont't explore visited.
                if n_node.is_visited:
                    continue
                queue.add(n_node)
                new_g = node.g + node.dist(n_node)
                if new_g < n_node.g:
                    n_node.g = new_g
                    n_node.h = 0
                    n_node.parent = node
                self.explored += 1
            yield
        self.path_length = self.finish.g
        yield

    def build_path(self, target: Node):
        path = [target.pos]
        while target.parent is not None:
            target = target.parent
            path.append(target.pos)
        self.path = path.copy()
        return self.path
# 

class AStar(Algorithm):
    def __init__(self, grid: Grid, boost_h=False) -> None:
        super().__init__(grid)
        self.boost_h = boost_h
        
    def heuristic(self, node: Node):
        return node.dist(self.finish) ** (1 + 1 * self.boost_h)

    def _algorithm(self):
        self.start.g = 0
        self.start.h = 0
        queue: set[Node] = {self.start}
        while queue:
            node = sorted(queue)[0]
            queue.remove(node)

            node.is_visited = True
            self.build_path(node)
            self.visited += 1

            if self.finish.is_visited:
                break

            for n_node in node.neighbors():
                # Don't explore obstacle.
                if n_node.is_obstacle:
                    continue
                # Dont't explore visited.
                if n_node.is_visited:
                    continue
                queue.add(n_node)
                new_g = node.g + node.dist(n_node)
                if new_g < n_node.g:
                    n_node.g = new_g
                    n_node.h = self.heuristic(n_node)
                    n_node.parent = node
                self.explored += 1
            yield
        self.path_length = self.finish.g
        yield

    def build_path(self, target: Node):
        path = [target.pos]
        while target.parent is not None:
            target = target.parent
            path.append(target.pos)
        self.path = path.copy()
        return self.path