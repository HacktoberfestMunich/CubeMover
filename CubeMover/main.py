import time
import itertools
import socket
from typing import Dict, Tuple, List

import argparse

from enum import Enum

class Operation(Enum):
    ADD    =  1, # Marker for foreground color command
    REMOVE = -1, # Marker for background color command
    NOOP   =  0  # Marker for no operation


class CubeMover:
    def __init__(self,
                 host: str, # target host
                 port: int, # target port
                 screen_origin_x: int, # relative horizontal origin offset for the CubeMover within bigger canvas
                 screen_origin_y: int, # relative vertical origin offset for the CubeMover within bigger canvas
                 screen_width: int, # width of CubeMovers drawable canvas
                 screen_height: int, # height of CubeMovers drawable canvas
                 object_width: int, # width of the square to color
                 object_height: int, # height of the square to color
                 step_size_x: int = 1, # horizontal step size
                 step_size_y: int = 1, # vertical step size
                 color_foreground: str = "bada55", # target object color
                 color_background: str = "000000", # background color of the canvas
                 delay: int = 1 # delay in seconds between updates
                 ):
        assert screen_height > (object_height + step_size_y), "Object does not fit into canvas"
        assert screen_width > (object_width + step_size_x), "Object does not fit into canvas"

        self.origin = (screen_origin_x, screen_origin_y) # canvas origin point (offset for Pixelflut command)
        self.size_screen = (screen_width, screen_height) # canvas size
        self.size_object = (object_width, object_height) # object size
        self.size_step = (step_size_x, step_size_y) # step dimensions
        self.position = (0, 0) # initial position of the object
        self.color_background = color_background # canvas background color
        self.color_foreground = color_foreground # object color
        self.delay = delay # delay in seconds

        # TODO: Add check whether or not the origin point is within the canvas
        # TODO: Add check whether or not the screen starting at the origin point is within the canvas

        # Generate a virtual representation of the canvas. Operations happen with this object before command assembly
        self.canvas: Dict[Tuple[int, int], Operation] = {}
        keys = [x for x in itertools.product(range(screen_width), range(screen_height))]
        for item in keys:
            self.canvas[item] = Operation.NOOP # Initially, nothing should happen (yes, this screws with the first image, sue me)
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.online: bool = True
        except:
            self.online: bool = False # If anything bad happens during socket creation, screw everything and be offline

    # Clear the canvas and retire every coloring operation of the current step
    def clear(self):
        x_start, x_end, y_start, y_end = self.get_paint_corners()

        for value in self.canvas.keys():
            if self.canvas[value] == Operation.REMOVE:
                self.canvas[value] = Operation.NOOP

        keys = [x for x in itertools.product(range(x_start, x_end), range(y_start, y_end))]
        for item in keys:
            if self.canvas[item] == Operation.REMOVE:
                self.canvas[item] = Operation.NOOP
            elif self.canvas[item] == Operation.ADD:
                self.canvas[item] = Operation.REMOVE

    # Update the current position on the canvas while changing directions on boop/wall collision
    def step(self):
        x_start, x_end, y_start, y_end = self.get_paint_corners()

        if self.size_step[0] > 0:
            if x_end == self.size_screen[0]:
                self.size_step = (-self.size_step[0], self.size_step[1])
        elif self.size_step[0] < 0:
            if x_start == 0:
                self.size_step = (-self.size_step[0], self.size_step[1])

        if self.size_step[1] > 0:
            if y_end == self.size_screen[1]:
                self.size_step = (self.size_step[0], -self.size_step[1])
        elif self.size_step[1] < 0:
            if y_start == 0:
                self.size_step = (self.size_step[0], -self.size_step[1])

        self.position = self.position[0] + self.size_step[0], self.position[1] + self.size_step[1]

    # Update the virtual canvas by adding the positions to be drawn
    def paint(self):
        x_start, x_end, y_start, y_end = self.get_paint_corners()

        keys = [x for x in itertools.product(range(x_start, x_end), range(y_start, y_end))]
        for item in keys:
            self.canvas[item] = Operation.ADD

    # Calculate the current object corners
    def get_paint_corners(self) -> List[int]:
        x_start, y_start = self.position[0], self.position[1]
        x_end, y_end = x_start + self.size_object[0], y_start + self.size_object[1]
        return [x_start, x_end, y_start, y_end]

    # Draw ASCII representation of the virtual canvas
    def draw_ascii(self):
        canvas = ""
        for y in range(self.size_screen[1]):
            for x in range(self.size_screen[0]):
                pos = (x,y)
                sign: str = "x"
                if self.canvas[pos] == Operation.NOOP:
                    sign = "x"
                elif self.canvas[pos] == Operation.ADD:
                    sign = "A"
                elif self.canvas[pos] == Operation.REMOVE:
                    sign = "R"
                canvas += sign
            canvas += "\n"
        canvas += "\n"
        print(canvas)

    # Do the Pixelflut
    def draw_canvas(self):
        # TODO: start at origin, iterate over canvas, determine lowest possible set of commands, start async writing
        removal_list: List[Tuple[int,int]] = []
        addlist_list: List[Tuple[int,int]] = []
        for key in self.canvas.keys():
            if self.canvas[key] == Operation.ADD:
                addlist_list.append(key)
            elif self.canvas[key] == Operation.REMOVE:
                removal_list.append(key)
        
        removal_command = "\n".join([f"PX {self.origin[0] + item[0]} {self.origin[1] + item[1]} {self.color_background}" for item in removal_list])
        insert_command = "\n".join([f"PX {self.origin[0] + item[0]} {self.origin[1] + item[1]} {self.color_foreground}" for item in addlist_list])

        total_command = removal_command + "\n" + insert_command + "\n"

        print(total_command)
        self.socket.sendall(bytes(total_command, "UTF-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Throw a simple DVD bouncer on a Pixelflut screen")
    parser.add_argument(dest='host',
                        metavar='h',
                        type=str,
                        help="Host of the Pixelflut server",
                        nargs="?",
                        default="127.0.0.1")
    parser.add_argument(dest='port',
                        metavar='p',
                        type=int,
                        help="Port of the Pixelflut server",
                        nargs="?",
                        default=1234)
    parser.add_argument(dest='screen_origin_x',
                        metavar='sox',
                        type=int,
                        help="Horizontal origin coordinate for reference within the Pixelflut canvas",
                        nargs="?",
                        default=0)
    parser.add_argument(dest='screen_origin_y',
                        metavar='soy',
                        type=int,
                        help="Vertical origin coordinate for reference within the Pixelflut canvas",
                        nargs="?",
                        default=0)
    parser.add_argument(dest='screen_width',
                        metavar='sw',
                        type=int,
                        help="Width of the screen area where the object may be drawn",
                        nargs="?",
                        default=400)
    parser.add_argument(dest='screen_height',
                        metavar='sh',
                        type=int,
                        help="Height of the screen area where the object may be drawn",
                        nargs="?",
                        default=200)
    parser.add_argument(dest='object_width',
                        metavar='ow',
                        type=int,
                        help="Width of the object",
                        nargs="?",
                        default=15)
    parser.add_argument(dest='object_height',
                        metavar='oh',
                        type=int,
                        help="Height of the object",
                        nargs="?",
                        default=9)
    parser.add_argument(dest='step_size_x',
                        metavar='dx',
                        type=int,
                        help="Horizontal step size",
                        nargs="?",
                        default=1)
    parser.add_argument(dest='step_size_y',
                        metavar='dy',
                        type=int,
                        help="Vertical step size",
                        nargs="?",
                        default=1)
    parser.add_argument(dest='color_foreground',
                        metavar='cf',
                        type=str,
                        help="Foreground color of the object",
                        nargs="?",
                        default="bada55")
    parser.add_argument(dest='color_background',
                        metavar='cb',
                        type=str,
                        help="Background color to be restored on step",
                        nargs="?",
                        default="000000")
    parser.add_argument(dest='delay',
                        metavar='d',
                        type=int,
                        help="Delay in seconds between object steps",
                        nargs="?",
                        default=2)

    args = parser.parse_args([])

    cm = CubeMover(
        host=args.host,
        port=args.port,
        screen_origin_x=args.screen_origin_x,
        screen_origin_y=args.screen_origin_y,
        screen_width=args.screen_width,
        screen_height=args.screen_height,
        object_width=args.object_width,
        object_height=args.object_height,
        step_size_x=args.step_size_x,
        step_size_y=args.step_size_y,
        color_foreground=args.color_foreground,
        color_background=args.color_background,
        delay=args.delay)

    while True:
        cm.draw_ascii()
        if cm.online:
            cm.draw_canvas()
        cm.clear()
        cm.step()
        cm.paint()
        time.sleep(cm.delay)
        
