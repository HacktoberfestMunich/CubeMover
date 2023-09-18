import asyncio
import itertools
from typing import Dict, Tuple, List

from enum import Enum

class Operation(Enum):
    ADD = 1,
    REMOVE = -1,
    NOOP = 0


class CubeMover:
    def __init__(self,
                 screen_origin_x: int,
                 screen_origin_y: int,
                 screen_width: int,
                 screen_height: int,
                 object_width: int,
                 object_height: int,
                 step_size_x: int = 1,
                 step_size_y: int = 1,
                 color: str = "bada55"):
        assert screen_height > (object_height + step_size_y), "Object does not fit into canvas"
        assert screen_width > (object_width + step_size_x), "Object does not fit into canvas"

        self.origin = (screen_origin_x, screen_origin_y)
        self.size_screen = (screen_width, screen_height)
        self.size_object = (object_width, object_height)
        self.size_step = (step_size_x, step_size_y)
        self.position = (0, 0)

        # TODO: Add check whether or not the origin point is within the canvas
        # TODO: Add check whether or not the screen starting at the origin point is within the canvas

        self.canvas: Dict[Tuple[int, int], Operation] = {}
        keys = [x for x in itertools.product(range(screen_width), range(screen_height))]
        for item in keys:
            print(item)
            self.canvas[item] = Operation.NOOP


    def clear(self):
        # x_start, y_start = self.position[0], self.position[1]
        # x_end, y_end = x_start + self.size_object[0], y_start + self.size_object[1]
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

    def step(self):
        # x_start, y_start = self.position[0], self.position[1]
        # x_end, y_end = x_start + self.size_object[0], y_start + self.size_object[1]
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
        print(self.position)

    def paint(self):
        # x_start, y_start = self.position[0], self.position[1]
        # x_end, y_end = x_start + self.size_object[0], y_start + self.size_object[1]
        x_start, x_end, y_start, y_end = self.get_paint_corners()

        keys = [x for x in itertools.product(range(x_start, x_end), range(y_start, y_end))]
        for item in keys:
            self.canvas[item] = Operation.ADD

    def get_paint_corners(self) -> List[int]:
        x_start, y_start = self.position[0], self.position[1]
        x_end, y_end = x_start + self.size_object[0], y_start + self.size_object[1]
        return [x_start, x_end, y_start, y_end]

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

    def draw_canvas(self):
        # TODO: start at origin, iterate over canvas, determine lowest possible set of commands, start async writing
        pass

if __name__ == "__main__":
    cm = CubeMover(0,0,15,10,3,2)

    while True:
        cm.draw_ascii()
        react = input("q to quit: ")
        if react == "q":
            break
        cm.clear()
        cm.step()
        cm.paint()
