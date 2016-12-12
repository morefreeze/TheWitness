import sys
import logging

# create logger
logger = logging.getLogger('split_colors')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

class Pos(object):
    x = 0
    y = 0
    def __init__(self, x=0, y=0):
        self.x, self.y = int(x), int(y)
    def __add__(self, other):
        return Pos(self.x + other.x, self.y + other.y)
    def __minus__(self, other):
        return Pos(self.x - other.x, self.y - other.y)
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    def __repr__(self):
        return 'Pos(%s, %s)' % (self.x, self.y)
    def __hash__(self):
        return hash(self.__repr__())

class Grid(object):
    ''' '0': empty
    '1'-'9', 'a'-'z': some color
    'x': non-grid
    type = '0'
    '''
    pos = Pos()
    neighbors = []  # [Grid]
    def __init__(self, pos=Pos(), type='0'):
        self.pos = pos
        self.type = type
        self.neighbors = []
    def __eq__(self, other):
        return self.pos == other.pos
    def __repr__(self):
        return 'Grid(%s, %s, \'%s\')' % (self.pos.x, self.pos.y, self.type)
    def add_neighbor(self, g):
        if g.type != 'x' and self.type != 'x':
            self.neighbors.append(g)
    def remove_neighbor(self, g):
        self.neighbors = [neighbor for neighbor in self.neighbors if neighbor != g]

class Wall(object):
    start = Pos()
    end = Pos()
    def __init__(self, start=Pos(), end=Pos()):
        self.start = start
        self.end = end
    def __repr__(self):
        return 'Wall(%s - %s)' % (self.start, self.end)

class Maze(object):
    grids = []  # [[Grid], [], ...]
    walls = []  # [Wall]
    n = 0
    m = 0
    def __init__(self, maze):
        self.n = len(maze)
        self.m = len(maze[0]) if self.n > 0 else 0
        for i in range(len(maze)):
            cur_line = []
            for j in range(len(maze[i])):
                pos = Pos(i, j)
                cur_line.append(Grid(pos, maze[i][j]))
            self.grids.append(cur_line)
        for i in range(len(self.grids)):
            for j in range(len(self.grids[i])):
                if i < len(self.grids)-1:
                    self.grids[i][j].add_neighbor(self.grids[i+1][j])
                if i > 0:
                    self.grids[i][j].add_neighbor(self.grids[i-1][j])
                if j < len(self.grids[i])-1:
                    self.grids[i][j].add_neighbor(self.grids[i][j+1])
                if j > 0:
                    self.grids[i][j].add_neighbor(self.grids[i][j-1])

    def format_wall(self, wall):
        # keep left-top to right-bottom
        if wall.start.x > wall.end.x or wall.start.y > wall.end.y:
            wall.start, wall.end = wall.end, wall.start
        x1, y1 = wall.start.x, wall.start.y
        x2, y2 = wall.end.x, wall.end.y
        if not (0 <= x1 <= x2 <= self.n and 0 <= y1 <= y2 <= self.m):
            return None
        # Not a single wall
        if (x2 - x1) + (y2 - y1) > 1:
            return None
        return wall

    def add_wall(self, wall):
        wall = self.format_wall(wall)
        if not wall:
            return False
        self.walls.append(wall)
        x1, y1 = wall.start.x, wall.start.y
        x2, y2 = wall.end.x, wall.end.y
        # Bottom or right edge, no need add wall
        if x1 == self.n or y1 == self.m:
            return True
        cur_grid = self.grids[x1][y1]
        neighbor_grid = None
        if x2 > x1 and y1 > 0:
            neighbor_grid = self.grids[x1][y1-1]
        if y2 > y1 and x1 > 0:
            neighbor_grid = self.grids[x1-1][y1]
        if neighbor_grid:
            cur_grid.remove_neighbor(neighbor_grid)
            neighbor_grid.remove_neighbor(cur_grid)
        return True

    def remove_wall(self, wall):
        wall = self.format_wall(wall)
        if not wall:
            return False
        x1, y1 = wall.start.x, wall.start.y
        x2, y2 = wall.end.x, wall.end.y
        found = False
        for i in range(len(self.walls)):
            if self.walls[i] == wall:
                found = True
                break
        if not found:
            return False
        del self.walls[i]
        # Bottom or right edge, no need add wall
        if x1 == self.n or y1 == self.m:
            return True
        cur_grid = self.grids[x1][y1]
        neighbor_grid = None
        if x2 > x1 and y1 > 0:
            neighbor_grid = self.grids[x1][y1-1]
        if y2 > y1 and x1 > 0:
            neighbor_grid = self.grids[x1-1][y1]
        if neighbor_grid:
            cur_grid.add_neighbor(neighbor_grid)
            neighbor_grid.add_neighbor(cur_grid)
        return True

    def check(self, debug=False):
        touch = set()
        colors = set()
        for row in self.grids:
            for grid in row:
                if grid.pos in touch:
                    continue
                group_grids = []
                self.floodfill(grid, touch, group_grids)
                group_types = {grid.type for grid in group_grids if grid.type not in ['0', 'x']}
                # Multi color in a group
                if len(group_types) > 1:
                    return False
                if len(group_types) == 1:
                    color = group_types.pop()
                    # Same color split to multi group
                    if color in colors:
                        return False
                    colors.add(color)
        return True

    def floodfill(self, grid, touch, group_grids):
        queue = []
        queue.append(grid)
        group_grids.append(grid)
        while len(queue) > 0:
            cur_grid = queue[0]
            queue = queue[1:]
            for new_grid in cur_grid.neighbors:
                if new_grid.pos not in touch:
                    touch.add(new_grid.pos)
                    queue.append(new_grid)
                    group_grids.append(new_grid)

    move_rules = [Pos(0, 1), Pos(1, 0), Pos(0, -1), Pos(-1, 0)]
    ''' maze:
    1002
    0330
    0440
    1002
    ---
    x101x
    00000
    02220
    '''
    # cur: Pos
    # end: Pos
    def dfs(self, cur, end, path):
        if cur == end:
            return self.check()
        for dir in self.move_rules:
            new_pos = cur + dir
            if new_pos in path:
                continue
            wall = Wall(cur, new_pos)
            if not self.add_wall(wall):
                continue
            path.append(new_pos)
            if self.dfs(new_pos, end, path):
                return True
            path.pop()
            self.remove_wall(wall)
        return False

    def format_solution(self, solution):
        dirs = []
        if len(solution) == 0:
            return dirs
        last = solution[0]
        for i in range(1, len(solution)):
            cur = solution[i]
            if cur.x != last.x and cur.y != last.y:
                logger.warn('solution incorrect at index %s (%s, %s)' % (i, last, cur))
                return dirs
            if cur.x < last.x:
                dirs.append('UP')
            elif cur.x > last.x:
                dirs.append('DOWN')
            elif cur.y < last.y:
                dirs.append('LEFT')
            elif cur.y > last.y:
                dirs.append('RIGHT')
            else:
                pass
            last = cur
        return dirs

    def find_solution(self, start, end):
        solution = [start]
        if self.dfs(start, end, solution):
            print self.format_solution(solution)
        else:
            print 'No solutions!'

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        start = Pos(*f.readline().strip().split(','))
        end = Pos(*f.readline().strip().split(','))
        maze = Maze([line.strip() for line in f.readlines()])

    maze.find_solution(start, end)
