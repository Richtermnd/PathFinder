import math
import pygame
from perlin_noise import PerlinNoise

pygame.init()

SIZE = W, H = 1280, 720
GRID_SIZE = G_W, G_H = 32, 18
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

    def trigger(self, *args, **kwargs):
        if pygame.time.get_ticks() - self.last_trigger > self.delay:
            self.action(*args, **kwargs)
            self.last_trigger = pygame.time.get_ticks()

    def switch(self):
        self.status = not self.status

    def __bool__(self):
        return self.status


class Node(pygame.sprite.Sprite):
    max_h = 1
    max_g = 1
    show_details = False
    grid = []

    def __init__(self, groups, x, y):
        # После определния операции сравнения, ломается __hash__ в классе спрайта
        # Я перегрузил хэш, теперь он берёт позицию спрайта
        # Поэтому необходимо, чтобы позиция объявлялась до того, как вызовется __init__ базового класса
        self.pos = self.x, self.y = x, y
        super().__init__(*groups)
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.rect.topleft = x * TILESIZE, y * TILESIZE

        self.is_visited = False
        self.is_obstacle = False
        self.is_key_node = False
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

    def reset(self):
        self.is_visited = False
        self._h, self._g = float('inf'), float('inf')
        self.parent = None

    def set_key_node(self, node):
        self.is_key_node, node.is_key_node = node.is_key_node, self.is_key_node
        return node

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

    def __repr__(self):
        return str(self.pos)

    def __str__(self):
        return self.__repr__()

    @property
    def f(self):
        return round(self._h + self._g, 2)

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
        r = 255 * (self.h == 0 or self.g == 0)
        g = int(255 * self.h / Node.max_h)
        b = int(255 * self.g / Node.max_g)
        color = pygame.Color(r, g, b)
        if not self.is_visited:
            hsva = list(color.hsva)
            hsva[2] *= 0.2
            color.hsva = tuple(hsva)
        return color

    @staticmethod
    def switch():
        Node.show_details = not Node.show_details

    @staticmethod
    def print_grid():
        print('\n'.join([''.join([str(int(node.is_visited)) for node in row])
                         for row in Node.grid]))


class Visualizer(pygame.Surface):
    def __init__(self, surface):
        super().__init__(SIZE)
        # -- visualize stuff --
        self.surface = surface
        self.all_sprites = pygame.sprite.Group()
        self.running = True

        self.play = Action(status=True)
        self.show_details = Action(action=Node.switch)
        self.animation = Action()
        self.next_step = Action(action=self.step, delay=100)
        self.reset = Action(action=self.reload_grid)
        self.clear = Action(action=self.clear_grid)
        self.noise = Action(action=self.perlin_noise)
        d = {pygame.K_1: self.wave,
             pygame.K_2: self.dijkstra,
             pygame.K_3: self.A_star}
        self.change_algorythm = Action(action=lambda key: self.set_algorythm(d[key]))

        # -- path find --
        self.path = []
        self.grid = [[Node((self.all_sprites,), x, y)
                      for x in range(G_W)]
                     for y in range(G_H)]
        Node.grid = self.grid
        self.start = self.grid[0][0]
        self.finish = self.grid[G_H - 1][G_W - 1]
        self.start.is_key_node, self.finish.is_key_node = True, True
        self.algorythm = self.dijkstra
        self.pathfind = self.algorythm()
        self.reload_grid()

    def reload_grid(self):
        self.path = []
        for node in self.all_sprites:
            node.reset()
        Node.max_h = 1
        Node.max_g = 1
        self.pathfind = self.algorythm()

    def clear_grid(self):
        self.path = []
        for node in self.all_sprites:
            node.reset()
            node.is_obstacle = False
        Node.max_h = 1
        Node.max_g = 1
        self.pathfind = self.algorythm()

    def perlin_noise(self):
        noise = PerlinNoise(octaves=10)
        for y in range(G_H):
            for x in range(G_W):
                if self.grid[y][x] is not self.start and self.grid[y][x] is not self.finish:
                    self.grid[y][x].is_obstacle = noise([x/G_W, y/G_H]) > 0.07

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
        yield

    def wave(self):
        def build_path(target):
            if target.is_visited:
                _node = target
                path = [_node]
                while _node is not self.start:
                    _node = min(_node.neighbors())
                    path.append(_node)
                self.path = path
            else:
                self.path = []

        self.start.g = 0
        self.start.h = 0
        queue: list[Node] = [self.start]
        while queue and not self.finish.is_visited:
            new_queue: list[Node] = []
            for node in queue:
                node.is_visited = True
                build_path(node)
                for n_node in node.neighbors():
                    # dx, dy = node.x - n_node.x, node.y - n_node.y
                    # if dx * dy:
                    #     continue
                    if n_node.is_obstacle:
                        continue
                    if n_node.is_visited:
                        continue
                    if n_node not in new_queue:
                        new_queue.append(n_node)
                    value = round(node.g + math.dist(node.pos, n_node.pos), 2)
                    n_node.g = min(value, n_node.g)
                    n_node.h = 0
                    if self.animation:
                        yield

            if self.finish.is_visited:
                break
            queue = new_queue
        build_path(self.finish)
        yield

    def dijkstra(self):
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

        self.start.g = 0
        self.start.h = 0
        self.start.is_visited = True
        queue: list[Node] = [self.start]
        node = self.start
        while node is not self.finish and queue:
            node = queue.pop()
            node.is_visited = True
            for n_node in node.neighbors():
                if n_node.is_obstacle:
                    continue
                if not n_node.is_visited and n_node not in queue:
                    queue.append(n_node)
                temp_g = round(node.g + math.dist(n_node.pos, node.pos), 2)
                if temp_g < n_node.g:
                    n_node.g = temp_g
                    n_node.parent = node
                    n_node.h = 0
            if self.animation:
                yield
            queue.sort(reverse=True)

        build_path(self.finish)
        yield

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        mouse_buttons = pygame.mouse.get_pressed(num_buttons=3)
        mouse_pos = pygame.mouse.get_pos()
        m_x, m_y = mouse_pos[0] // TILESIZE, mouse_pos[1] // TILESIZE
        keys = pygame.key.get_pressed()

        # So cursed
        if keys[pygame.K_SPACE]:
            self.next_step.trigger()
        elif keys[pygame.K_p]:
            self.play.trigger()
        elif keys[pygame.K_a]:
            self.animation.trigger()
        elif keys[pygame.K_r]:
            self.reset.trigger()
        elif keys[pygame.K_d]:
            self.show_details.trigger()
        elif keys[pygame.K_n]:
            self.noise.trigger()
            self.reset.trigger()
        elif keys[pygame.K_c]:
            self.clear.trigger()
        elif keys[pygame.K_1]:
            self.change_algorythm.trigger(pygame.K_1)
        elif keys[pygame.K_2]:
            self.change_algorythm.trigger(pygame.K_2)
        elif keys[pygame.K_3]:
            self.change_algorythm.trigger(pygame.K_3)

        try:
            node = self.grid[m_y][m_x]
        except IndexError:
            return
        if mouse_buttons[0]:
            if keys[pygame.K_LSHIFT]:
                if node is not self.finish and not node.is_obstacle:
                    self.start = self.start.set_key_node(node)
            else:
                if node is not self.finish and node is not self.start:
                    node.is_obstacle = True
        elif mouse_buttons[2]:
            if keys[pygame.K_LSHIFT]:
                if node is not self.start and not node.is_obstacle:
                    self.finish = self.finish.set_key_node(node)
            else:
                if node is not self.finish and node is not self.start:
                    node.is_obstacle = False
        if any(mouse_buttons):
            self.reload_grid()
            self.next_step.last_trigger = 0

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

    def set_algorythm(self, algorythm):
        self.algorythm = algorythm
        self.reload_grid()

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
