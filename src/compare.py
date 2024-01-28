import csv

from pathfind.grid import Grid, MazeGrid, RandomSurface
from pathfind.algorithm import Wave, Dijkstra, AStar



# def fabric()


def compare(factory):
    f = open('results/surface.csv', mode='w', newline='')
    writer = csv.DictWriter(
        f,
        fieldnames=['name', 'side', 'path', 'visited', 'explored']
        )
    writer.writeheader()
    for side in range(10, 51, 10):
        print(f'== Side {side} == ')
        wave_statistic = {
            'name': 'wave',
            'side': side,
            'path': [],
            'visited': [],
            'explored': []
            }
        dijkstra_statistic = {
            'name': 'dijkstra',
            'side': side,
            'path': [],
            'visited': [],
            'explored': []
            }
        a_star_statistic = {
            'name': 'a_star',
            'side': side,
            'path': [],
            'visited': [],
            'explored': []
            }
        for _ in range(5):
            maze = factory(side, side)

            print('Start A*.')
            a_star = AStar(maze)
            a_star.solve()
            print('Solve A*.')
            print()

            while a_star.path_length == float('inf'):
                maze = factory(side, side)

                print('Start A*.')
                a_star = AStar(maze)
                a_star.solve()
                print('Solve A*.')
                print()

            maze.reset()
            a_star_statistic['path'].append(a_star.path_length)
            a_star_statistic['visited'].append(a_star.visited)
            a_star_statistic['explored'].append(a_star.explored)

            print('Start dijkstra.')
            dijkstra = Dijkstra(maze)
            dijkstra.solve()
            dijkstra_statistic['path'].append(dijkstra.path_length)
            dijkstra_statistic['visited'].append(dijkstra.visited)
            dijkstra_statistic['explored'].append(dijkstra.explored)
            maze.reset()
            print('Solve dijkstra')
            print()

            print('Start wave.')
            wave = Wave(maze)
            wave.solve()
            wave_statistic['path'].append(wave.path_length)
            wave_statistic['visited'].append(wave.visited)
            wave_statistic['explored'].append(wave.explored)
            maze.reset()
            print('Solve wave')
            print()

        for statistic in a_star_statistic, dijkstra_statistic, wave_statistic:
            statistic['path'] = sum(statistic['path']) / len(statistic['path'])
            statistic['visited'] = sum(statistic['visited']) / len(statistic['visited'])
            statistic['explored'] = sum(statistic['explored']) / len(statistic['explored'])
            writer.writerow(statistic)
    f.close()


def compare_a_star(factory):
    f = open('results/a_star.csv', mode='w', newline='')
    writer = csv.DictWriter(
        f,
        fieldnames=['name', 'side', 'path', 'visited', 'explored']
        )
    writer.writeheader()
    for side in range(10, 151, 10):
        print("SIDE^", side)
        a_star_statistic = {
            'name': 'a_star',
            'side': side,
            'path': [],
            'visited': [],
            'explored': []
            }
        a_star_boosted_statistic = {
            'name': 'a_star_boosted',
            'side': side,
            'path': [],
            'visited': [],
            'explored': []
            }
        for _ in range(5):
            maze = factory(side, side)

            # print('Start A*.')
            a_star = AStar(maze, False)
            a_star.solve()
            # print('Solve A*.')
            # print()

            while a_star.path_length == float('inf'):
                maze = factory(side, side)
                # print('Start A*.')
                a_star = AStar(maze, False)
                a_star.solve()
                # print('Solve A*.')
                # print()
            a_star_statistic['path'].append(a_star.path_length)
            a_star_statistic['visited'].append(a_star.visited)
            a_star_statistic['explored'].append(a_star.explored)
            maze.reset()

            # print('Start A*.')
            a_star = AStar(maze, True)
            a_star.solve()
            # print('Solve A*.')
            # print()
            a_star_boosted_statistic['path'].append(a_star.path_length)
            a_star_boosted_statistic['visited'].append(a_star.visited)
            a_star_boosted_statistic['explored'].append(a_star.explored)

        for statistic in a_star_statistic, a_star_boosted_statistic:
            statistic['path'] = sum(statistic['path']) / len(statistic['path'])
            statistic['visited'] = sum(statistic['visited']) / len(statistic['visited'])
            statistic['explored'] = sum(statistic['explored']) / len(statistic['explored'])
            writer.writerow(statistic)


def main():
    compare(RandomSurface)


if __name__ == '__main__':
    main()