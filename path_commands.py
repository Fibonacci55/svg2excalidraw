# path_commands.py
import abc
from path_common import Point
import svg2exc_logging

log = svg2exc_logging.getLogger("path_commands")


class PathCommand(abc.ABC):
    def __init__(self, cmd, param_list):
        log.debug(f"{self.__class__.__name__}::__init__: {param_list}")

        self.param_list = param_list
        self.closed = False

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
        raise NotImplementedError

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
        return point_list


class Lineto(PathCommand):
    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, p)
            point_list.append(cur_p)
        return point_list


class VerticalLine(PathCommand):
    def adv_absolute(self, from_p, to_p):
        return Point(from_p.x, to_p.y)

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, Point(0, p))
            point_list.append(cur_p)
        return point_list


class HorizontalLine(PathCommand):
    def adv_absolute(self, from_p, to_p):
        return Point(to_p.x, from_p.y)

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, Point(p, 0))
            point_list.append(cur_p)
        return point_list


class CurveTo(PathCommand):
    def execute(self, start_point):
        log.warning("CurveTo execution is not fully implemented.")
        return []


class ClosePath(PathCommand):
    def execute(self, start_point):
        self.closed = True
        return []


class Command_Factory:
    command_list = []

    @classmethod
    def clear_cmd_list(cls):
        cls.command_list = []

    @classmethod
    def make_cmd(cls, token_list):
        if not token_list:
            return None

        cmd_str = token_list[0]
        log.info(f"command {cmd_str}")

        if cmd_str in ["m", "M"]:
            c = Move(cmd_str, token_list[1:])
        elif cmd_str in ["v", "V"]:
            c = VerticalLine(cmd_str, token_list[1:])
        elif cmd_str in ["h", "H"]:
            c = HorizontalLine(cmd_str, token_list[1:])
        elif cmd_str in ["c", "C"]:
            c = CurveTo(cmd_str, token_list[1:])
        elif cmd_str in ["z", "Z"]:
            c = ClosePath(cmd_str, token_list[1:])
        elif cmd_str in ["l", "L"]:
            c = Lineto(cmd_str, token_list[1:])
        else:
            log.warning(f"Unsupported command: {cmd_str}")
            return None

        cls.command_list.append(c)
        return c
