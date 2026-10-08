width: int = 20
height: int = 15
NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8

ALL_WALLS: int = NORTH+EAST+SOUTH+WEST


grid: list[list[int]] = []
for _ in range(height):
    row: list[int] = [ALL_WALLS]*width
    grid.append(row)


def open_wall(cell: int, wall: int) -> int:
    return cell & ~ wall


def open_east_passage(grid: list[list[int]], x: int, y: int) -> None:
    if x + 1 < len(grid[0]):
        grid[y][x] = open_wall(grid[y][x], EAST)
        grid[y][x+1] = open_wall(grid[y][x+1], WEST)


def open_south_passage(grid: list[list[int]], x: int, y: int) -> None:
    if y + 1 < len(grid):
        grid[y][x] = open_wall(grid[y][x], SOUTH)
        grid[y+1][x] = open_wall(grid[y+1][x], NORTH)


for y in range(height):
    for x in range(width-1):
        open_east_passage(grid, x, y)

for y in range(height-1):
    open_south_passage(grid, 0, y)

with open("maze.txt", "w", encoding="utf-8") as file:
    try: 
        for row in grid:
            text: str = ""
            for cell in row:
                text += format(cell, "X")
            file.write(text + "\n")
    except OSError as error:
        print(f"An Error:{error} Has accured in maze.txt ")