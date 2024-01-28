from PIL import Image, ImageDraw
from pathfind.algorithm import Wave, Dijkstra, AStar
from pathfind.grid import Grid, MazeGrid, RandomSurface


class ImageMixin:
    def __init__(self, grid: Grid, resolution) -> None:
        super().__init__(grid)
        self.resolution = self.w, self.h = resolution
        self.rect_w, self.rect_h = self.w // grid.w, self.h // grid.h
        self.frames: list[tuple[tuple[tuple[tuple[int, int, int]]], list[tuple[int, int]]]] = []  # ЧТО ЭТО?

    def __iter__(self):
        self.frames = []
        return super().__iter__()

    def __next__(self):
        super().__next__()
        self.frames.append((self.grid.image(), self.path.copy()))

    def _draw_path(self, im, path):
        draw = ImageDraw.Draw(im, mode='RGB')
        offset_x, offset_y = self.rect_w // 2, self.rect_h // 2
        path = [(offset_x + self.rect_w * x, offset_y + self.rect_h * y) for (x, y) in path]
        draw.line(path, fill='black', width=2)

    def _draw_grid(self, im, grid):
        draw = ImageDraw.Draw(im, mode='RGB')
        grid_w, grid_h = len(grid[0]), len(grid)
        for y in range(grid_h):
            for x in range(grid_w):
                p1 = x * self.rect_w, y * self.rect_h
                p2 = (x + 1) * self.rect_w, (y + 1) * self.rect_h
                draw.rectangle((p1, p2), fill=grid[y][x])

    def _image_from_frame(self, frame):
        grid, path = frame
        im = Image.new('RGB', self.resolution)
        self._draw_grid(im, grid)
        self._draw_path(im, path)
        return im

    def images(self):
        return [self._image_from_frame(frame) for frame in self.frames]

    def save_as_gif(self, name: str, duration=150):
        images = self.images()
        first_image = images[0]
        first_image.save(
            name,
            format='GIF',
            append_images=images,
            save_all=True,
            duration=duration,
            loop=0
            )


class ImageWave(ImageMixin, Wave):
    pass


class ImageDijkstra(ImageMixin, Dijkstra):
    pass


class ImageAStar(ImageMixin, AStar):
    pass


def animate(prefix, grid, resolution):
    a_star = ImageAStar(grid, resolution)
    for _ in a_star:
        pass
    a_star.save_as_gif(f'gifs/{prefix}/big_{prefix}_a_star.gif')
    dijkstra = ImageDijkstra(grid, resolution)
    for _ in dijkstra:
        pass
    dijkstra.save_as_gif(f'gifs/{prefix}/big_{prefix}_dijkstra.gif')
    wave = ImageWave(grid, resolution)
    for _ in wave:
        pass
    wave.save_as_gif(f'gifs/{prefix}/big_{prefix}_wave.gif')


def is_valid_grid(grid):
    a_star = AStar(grid)
    a_star.solve()
    return a_star.path_length != float('inf')


def surface():
    resolution = (int(1280 / 2), int(720 / 2))
    grid = Grid.load_file('src/grid.txt')
    grid.reset()
    animate('surface', grid, resolution)


def maze():
    resolution = (int(1280 * 33 / 32 / 2), int(720 * 19 / 18 / 2))
    grid = MazeGrid(32, 18)
    animate('maze', grid, resolution)


def main():
    surface()


if __name__ == '__main__':
    main()
