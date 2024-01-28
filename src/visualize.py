from functools import partial

import pygame

from pathfind.algorithm import Wave, Dijkstra, AStar, Algorithm
from pathfind import grid
from constants import *

pygame.init()
font = pygame.font.Font(None, TILE_SIZE // 3)


class Action:
    def __init__(self, action=None, status=False, delay=200, *args, **kwargs) -> None:
        self.last_trigger = 0
        self.delay = delay
        if action:
            self.action = partial(action, *args, **kwargs)
        else:
            self.status = status
            self.action = partial(self.switch)

    def trigger(self, *args, **kwargs):
        if pygame.time.get_ticks() - self.last_trigger > self.delay:
            print(self.action.func.__name__)
            res = self.action(*args, **kwargs)
            self.last_trigger = pygame.time.get_ticks()
            return res

    def switch(self):
        self.status = not self.status

    def __bool__(self):
        return self.status


class Grid(pygame.Surface):
    def __init__(self, surface: pygame.Surface) -> None:
        super().__init__(SIZE)
        self.surface = surface

        # -- visualize --
        self.is_running = True

        # -- PathFind --
        self.grid = grid.Grid(G_W, G_H)
        self.grid.start = self.grid[0, 0]
        self.grid.finish = self.grid[G_W - 1, G_H - 1]
        self.algorithm = Wave
        self.alg: Algorithm = Wave(self.grid)
        self.play = Action(status=True)
        self.animation = Action()
        self.step = Action(self.next_step, delay=50)
        self.show_details = Action()

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
        mouse_buttons = pygame.mouse.get_pressed(num_buttons=3)
        mouse_pos = pygame.mouse.get_pos()
        m_x, m_y = mouse_pos[0] // TILE_SIZE, mouse_pos[1] // TILE_SIZE
        keys = pygame.key.get_pressed()
        # So cursed
        if keys[pygame.K_SPACE]:
            self.step.trigger()
        elif keys[pygame.K_z]:
            self.play.trigger()
        elif keys[pygame.K_x]:
            self.animation.trigger()
        elif keys[pygame.K_c]:
            self.show_details.trigger()
        elif keys[pygame.K_1]:
            self.algorithm = Wave
            self.reload()
        elif keys[pygame.K_2]:
            self.algorithm = Dijkstra
            self.reload()
        elif keys[pygame.K_3]:
            self.algorithm = AStar
            self.reload()
        elif keys[pygame.K_4]:
            self.algorithm = lambda grid: AStar(grid, True)
            self.reload()

        try:
            node = self.grid[m_x, m_y]
        except IndexError:
            return
        if mouse_buttons[0]:
            if keys[pygame.K_LSHIFT]:
                if not node.is_obstacle and node is not self.grid.finish:
                    self.grid.start.is_point = False
                    node.is_point = True
                    node.is_obstacle = False
                    self.grid.start = node
            else:
                if not node.is_point:
                    node.is_obstacle = True
        elif mouse_buttons[2]:
            if keys[pygame.K_LSHIFT]:
                if not node.is_obstacle and node is not self.grid.start:
                    self.grid.finish.is_point = False
                    node.is_point = True
                    node.is_obstacle = False
                    self.grid.finish = node
            else:
                if not node.is_point:
                    node.is_obstacle = False
        if any(mouse_buttons):
            self.reload()

    def reload(self):
        self.grid.reset()
        self.alg = self.algorithm(self.grid)
        self.step.last_trigger = 0

    def next_step(self):
        try:
            self.alg.__next__()
            return True
        except StopIteration:
            return False

    def draw(self):
        # Tiles.
        for node in self.grid:
            x, y = node.pos
            x, y = x * TILE_SIZE, y * TILE_SIZE
            rect = x, y, TILE_SIZE, TILE_SIZE
            pygame.draw.rect(self, node.color, rect)
            if self.show_details:
                text = font.render(str(node.h), True, 'white')
                self.blit(text, (x + 5, y + 5))
                text = font.render(str(node.f), True, 'white')
                self.blit(text, (x + TILE_SIZE / 2 - text.get_width() / 2, y + TILE_SIZE / 2 - text.get_height() / 2))
                text = font.render(str(node.g), True, 'white')
                self.blit(text, (x + TILE_SIZE - 5 - text.get_width(), y + TILE_SIZE - 5 - text.get_height()))

        # Grid lines.
        for y in range(G_H):
            pygame.draw.line(self, (0, 0, 0), (0, y * TILE_SIZE), (W, y * TILE_SIZE))

        for x in range(G_W):
            pygame.draw.line(self, (0, 0, 0), (x * TILE_SIZE, 0), (x * TILE_SIZE, H), width=2)

        # Path.
        if self.alg.path:
            last_x, last_y = self.alg.path[0]
            for x, y in self.alg.path:
                pygame.draw.line(
                    self,
                    'black',
                    (last_x * TILE_SIZE + TILE_SIZE // 2, last_y * TILE_SIZE + TILE_SIZE // 2),
                    (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2),
                    3)
                last_x, last_y = x, y


    def update(self):
        if self.animation:
            if self.play:
                self.step.trigger()
        else:
            while self.next_step():
                pass
        self.fill('gray')
        self.draw()
        self.surface.blit(self, (0, 0))

    def loop(self):
        clock = pygame.time.Clock()
        while self.is_running:
            clock.tick(FPS)
            self.event_handler()
            self.update()
            pygame.display.flip()
        pygame.quit()


def main():
    g = Grid(pygame.display.set_mode(SIZE))
    g.loop()


if __name__ == '__main__':
    main()