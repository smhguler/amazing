import sys

if len(sys.argv) != 2:
    print("Usage: python3 a_maze_ing.py config.txt")
    sys.exit(1)

if sys.argv[1].endswith(".txt") == False:
    sys.exit("second parameter has to be in txt format")
try:
    clear_format_commands = []
    key_and_values = {}
    with open(sys.argv[1], "r") as config:
            config_txt = config.read()

#PARSLAMA KISMI
    config_lines = config_txt.splitlines()
    for line in config_lines:
        line = line.strip()
        if line == "":
            continue
        if line.startswith("#"):
            continue
        clear_format_commands.append(line)
    for line in clear_format_commands:
        key,value = line.split("=",1)
        key = key.strip()
        value = value.strip()
        key_and_values[key] = value

#Eksik key 
    required_keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"]
    missing_keys = []
    for key in required_keys:
        if key not in key_and_values:
            missing_keys.append(key)
    if missing_keys:
        print(f"missing keys in config file: {missing_keys}")
        sys.exit(1)

#PARSLANAN DEĞERLERİ DENEME KISMI
    perfect = (key_and_values["PERFECT"])
    if perfect not in ("True", "False"):
        print("perfect key invalid please print 'True or False ' ")
        sys.exit(1)

        
    output_file = key_and_values["OUTPUT_FILE"]
    if output_file != "maze.txt":
        sys.exit("in config file output file has to be maze.txt")
    
    width = int(key_and_values["WIDTH"])
    height = int(key_and_values["HEIGHT"])
    try:
        entry =(key_and_values["ENTRY"]).split(",",1)
        entry_x = int(entry[0])
        if entry_x < 0:
            sys.exit(" entry point cant be negative")
        entry_y = int(entry[1])
        if entry_y < 0:
            sys.exit(" entry point cant be negative")
    except (ValueError, IndexError):
        print("wrong entry key  value in config file please use as in exemple : 11,30")
        sys.exit(1)
    try:
        exit_point = (key_and_values["EXIT"]).split(",",1)
        exit_point_x = int(exit_point[0])
        if exit_point_x < 0:
            sys.exit("exit point cant be negative")
        exit_point_y = int(exit_point[1])
        if exit_point_y < 0:
            sys.exit(" exit point cant be negative")
    except (ValueError, IndexError) :
        print("wrong exit key  value in config file please use as in exemple : 99,30 ")
        sys.exit(1)

except (FileNotFoundError,PermissionError,IsADirectoryError,UnicodeDecodeError)as error:
    print(f"hata: {error}")
    sys.exit(1)
except KeyError  as error :
    print(f"missing key {error} in config file !")
    sys.exit(1)
except ValueError as error :
    print(f" vrong walue  {error} in config file pease use  numbers !")
    sys.exit(1)

if entry_x >= width :
    sys.exit("enthry point is not whit in  maze bouds")
if entry_y >= height :
    sys.exit("enthry point is not whit in  maze bouds")

    sys.exit("exit point and entry point cat be same ")
if exit_point_x >= width :
    sys.exit("exit point is not whit in  maze bouds")
if exit_point_y >= height :
    sys.exit("exit point is not whit in  maze bouds")


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


try:
    with open(output_file, "w", encoding="utf-8") as file:
        for row in grid:
            text: str = ""
            for cell in row:
                text += format(cell, "X")
            file.write(text + "\n")
except OSError as error:
    print(f"An Error:{error} Has accured in maze.txt ")