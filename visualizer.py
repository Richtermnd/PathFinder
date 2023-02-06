import math

import pygame

pygame.init()

SIZE = W, H = 1280, 720
GRID_SIZE = G_W, G_H = 16, 9
TILESIZE = min(W // G_W, H // G_H)
FPS = 30
font = pygame.font.Font(None, TILESIZE // 3)


class Action:
    def __init__(self, action=None, delay=200, status=False):
        self.last_trigger = 0
        self.delay = delay
        if action:
            self.action = action
        else:
            self.status = status
            self.action = self.switch

    def trigger(self):
        if pygame.time.get_ticks() - self.last_trigger > self.delay:
            self.action()
            self.last_trigger = pygame.time.get_ticks()

    def switch(self):
        self.status = not self.status

    def __bool__(self):
        return self.status


class Node(pygame.sprite.Sprite):
    max_h = 0
    max_g = 1
    show_details = False

    def __init__(self, groups, x, y, grid):
        # После определния операции сравнения, ломается __hash__ в классе спрайта
        # Я перегрузил хэш, теперь он берёт позицию спрайта
        # Поэтому необходимо, чтобы позиция объявлялась до того, как вызовется __init__ базового класса
        self.pos = self.x, self.y = x, y
        super().__init__(*groups)
        self.grid = grid
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.rect.topleft = x * TILESIZE, y * TILESIZE

        self.is_visited = False
        self.is_obstacle = False
        self._h = float('inf')
        self._g = float('inf')
        self.parent = None

    def neighbors(self):
        start_y, end_y = max(0, self.y - 1), min(len(self.grid), self.y + 2)
        start_x, end_x = max(0, self.x - 1), min(len(self.grid[0]), self.x + 2)
        res = []
        for row in self.grid[start_y:end_y]:
            for n_node in row[start_x:end_x]:
                if self is n_node:
                    continue
                res.append(n_node)
        return res

    @property
    def f(self):
        return round(self._h * 1.1 + self._g, 2)

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, value):
        if value != float('inf'):
            Node.max_h = max(Node.max_h, value)
        self._h = value

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, value):
        if value != float('inf'):
            Node.max_g = max(Node.max_g, value)
        self._g = value

    @property
    def color(self):
        if self.is_obstacle:
            return pygame.Color(100, 100, 100)
        if self.f == float('inf'):
            return 'gray'
        color = pygame.Color(255 - 255 * (self.g != 0 and self.h != 0),
                             int(255 * self.h / Node.max_h),
                             int(255 * self.g / Node.max_g))
        if not self.is_visited:
            hsva = list(color.hsva)
            hsva[2] *= 0.2
            color.hsva = tuple(hsva)
        return color

    def reset(self):
        self.is_visited = False
        self._h, self._g = float('inf'), float('inf')
        self.parent = None

    def update(self):
        pygame.draw.rect(self.image, pygame.Color(100, 100, 100), self.image.get_rect(), 1)
        pygame.draw.rect(self.image, self.color, (1, 1, TILESIZE - 2, TILESIZE - 2))
        if self.f != float('inf') and Node.show_details:
            text = font.render(str(self.h), True, 'white')
            self.image.blit(text, (5, 5))
            text = font.render(str(self.f), True, 'white')
            self.image.blit(text, (TILESIZE / 2 - text.get_width() / 2, TILESIZE / 2 - text.get_height() / 2))
            text = font.render(str(self.g), True, 'white')
            self.image.blit(text, (TILESIZE - 5 - text.get_width(), TILESIZE - 5 - text.get_height()))

    def __eq__(self, other):
        return (self.f, self.h, self.g) == (other.f, other.h, other.g)

    def __lt__(self, other):
        return (self.f, self.h, self.g) < (other.f, other.h, other.g)

    def __hash__(self):
        return hash(self.pos)

    @staticmethod
    def switch():
        Node.show_details = not Node.show_details


class Visualizer(pygame.Surface):
    def __init__(self, surface):
        super().__init__(SIZE)
        # -- visualize stuff --
        self.surface = surface
        self.all_sprites = pygame.sprite.Group()
        self.play = Action(status=True)
        self.show_details = Action(action=Node.switch)
        self.animation = Action()
        self.next_step = Action(action=self.step, delay=100)
        self.reset = Action(action=self.reload_grid)
        self.running = True

        # -- path find --
        self.path = []
        self.grid = []
        for y in range(G_H):
            self.grid.append([Node((self.all_sprites,), x, y, self.grid) for x in range(G_W)])
        self.start = self.grid[0][0]
        self.finish = self.grid[G_H - 1][G_W - 1]
        self.reload_grid()
        self.pathfind = self.A_star()

    def reload_grid(self):
        self.path = []
        for node in self.all_sprites:
            node.reset()
        Node.max_h = 0
        Node.max_g = 1
        self.pathfind = self.A_star()

    def A_star(self):
        def h(_node: Node):
            return round(math.dist(_node.pos, self.finish.pos), 2)

        def build_path(target):
            if target.is_visited:
                _node = target
                path = [_node]
                while _node.parent:
                    _node = _node.parent
                    path.append(_node)
                self.path = path
            else:
                self.path = []

        self.start.is_visited = True
        self.start.h = h(self.start)
        self.start.g = 0
        # yield

        queue = [self.start]
        while queue:
            node = queue.pop()
            node.is_visited = True
            build_path(node)
            if node is self.finish:
                break
            for n_node in node.neighbors():
                if n_node.is_obstacle:
                    continue
                if not n_node.is_visited and n_node not in queue:
                    queue.append(n_node)
                temp_g = node.g + math.dist(n_node.pos, node.pos)
                if temp_g < n_node.g:
                    n_node.g = round(temp_g, 2)
                    n_node.parent = node
                    n_node.h = round(h(n_node), 2)
            queue.sort(reverse=True)
            if self.animation:
                yield
        build_path(self.finish)

    def event_handler(self):
        mouse_buttons = pygame.mouse.get_pressed(num_buttons=3)
        mouse_pos = pygame.mouse.get_pos()
        m_x, m_y = mouse_pos[0] // TILESIZE, mouse_pos[1] // TILESIZE
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            self.next_step.trigger()
        if keys[pygame.K_p]:
            self.play.trigger()
        if keys[pygame.K_a]:
            self.animation.trigger()
        if keys[pygame.K_r]:
            self.reset.trigger()
        if keys[pygame.K_d]:
            self.show_details.trigger()

        try:
            node = self.grid[m_y][m_x]
        except IndexError:
            return
        if mouse_buttons[0]:
            if keys[pygame.K_LSHIFT]:
                if node is not self.finish and not node.is_obstacle:
                    self.start = node
            else:
                if node is not self.finish and node is not self.start:
                    node.is_obstacle = True
        elif mouse_buttons[2]:
            if keys[pygame.K_LSHIFT]:
                if node is not self.start and not node.is_obstacle:
                    self.finish = node
            else:
                if node is not self.finish and node is not self.start:
                    node.is_obstacle = False
        if any(mouse_buttons):
            self.reload_grid()
            self.next_step.last_trigger = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def draw_path(self):
        if not self.path:
            return
        last_pos = self.path[0].rect.center
        for node in self.path[1:]:
            pos = node.rect.center
            pygame.draw.line(self, pygame.Color(50, 50, 50), last_pos, pos, 3)
            last_pos = pos

    def step(self):
        try:
            self.pathfind.__next__()
            return True
        except StopIteration:
            return False

    def update_grid(self):
        if self.animation:
            if self.play:
                self.next_step.trigger()
        else:
            while self.step():
                pass

    def update(self):
        self.fill('gray')
        self.update_grid()
        self.all_sprites.update()
        self.all_sprites.draw(self)
        self.draw_path()
        self.surface.blit(self, (0, 0))

    def main_cycle(self):
        clock = pygame.time.Clock()
        while self.running:
            clock.tick(FPS)
            self.event_handler()
            self.update()
            pygame.display.flip()
        pygame.quit()


def main():
    visualizer = Visualizer(pygame.display.set_mode(SIZE))
    visualizer.main_cycle()


if __name__ == '__main__':
    main()
