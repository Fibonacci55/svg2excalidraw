# path_commands.py
import abc
from excalidraw_writer import Line
from path_common import Point

import svg2exc_logging

log = svg2exc_logging.getLogger('path_commands')


class PathCommand(abc.ABC):

    def __init__(self, cmd, param_list):
        log.debug(f'{self.__class__.__name__}::__init__: {param_list}')

        self.param_list = param_list
        self.closed = False

        # Suggestion 5: Replaced magic number 90 with .islower()
        if cmd.islower():
            self.relative = True
            self.advance = self.adv_relative
        else:
            self.relative = False
            self.advance = self.adv_absolute

    def adv_absolute(self, from_p, to_p):
        return to_p

    def adv_relative(self, from_p, to_p):
        return from_p + to_p

    @abc.abstractmethod
    def execute(self, start_point):
        pass

    def __str__(self):
        return self.__class__.__name__


class Move(PathCommand):

    def execute(self, start_point):
        point_list = []
        cur_p = self.advance(start_point, self.param_list[0])
        for p in self.param_list[1:]:
            point_list.append(cur_p)
            cur_p = self.advance(cur_p, p)
        point_list.append(cur_p)
        return point_list  # line


class Lineto(PathCommand):

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, p)
            point_list.append(cur_p)
        return point_list  # line


class VerticalLine(PathCommand):

    # Suggestion 2: Fixed absolute coordinate calculation to preserve X
    def adv_absolute(self, from_p, to_p):
        return Point(from_p.x, to_p.y)

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, Point(0, p))
            point_list.append(cur_p)
        return point_list  # line


class HorizontalLine(PathCommand):

    # Suggestion 2: Fixed absolute coordinate calculation to preserve Y
    def adv_absolute(self, from_p, to_p):
        return Point(to_p.x, from_p.y)

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, Point(p, 0))
            point_list.append(cur_p)
        return point_list  # line


class CurveTo(PathCommand):

    def execute(self, start_point):
        # Suggestion 6: Prevent returning None to avoid downstream iteration errors
        log.warning("CurveTo execution is not fully implemented.")
        return []


class ClosePath(PathCommand):

    def execute(self, start_point):
        # Suggestion 6: Prevent returning None and properly flag closure
        self.closed = True
        return []


class Command_Factory:
    command_list = []

    def __init__(self):
        # Suggestion 4: Fixed variable scope (was a useless local variable)
        self.command_list = []

    @classmethod
    def clear_cmd_list(cls):
        cls.command_list = []

    @classmethod
    # Suggestion 4: Changed 'self' to 'cls' for classmethod
    def make_cmd(cls, token_list):
        if not token_list:
            return None

        cmd_str = token_list[0]
        log.info(f'command {cmd_str}')

        if cmd_str in ['m', 'M']:
            c = Move(cmd_str, token_list[1:])
        elif cmd_str in ['v', 'V']:
            c = VerticalLine(cmd_str, token_list[1:])
        elif cmd_str in ['h', 'H']:
            c = HorizontalLine(cmd_str, token_list[1:])
        elif cmd_str in ['c', 'C']:
            c = CurveTo(cmd_str, token_list[1:])
        elif cmd_str in ['z', 'Z']:
            c = ClosePath(cmd_str, token_list[1:])
        elif cmd_str in ['l', 'L']:
            c = Lineto(cmd_str, token_list[1:])
        else:
            # Suggestion 1: Fixed UnboundLocalError by handling unknown commands
            log.warning(f"Unsupported command: {cmd_str}")
            return None

        cls.command_list.append(c)
        return c


if __name__ == '__main__':

    c = ClosePath('c', [])
    print(type(c))

    # Suggestion 7: Modernized type checking using isinstance
    if isinstance(c, ClosePath):
        print('ClosePath')
    else:
        print('something else')
# -----
