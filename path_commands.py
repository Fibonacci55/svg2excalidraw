import abc
from excalidraw_writer import Line
from path_common import Point

import svg2exc_logging
log = svg2exc_logging.getLogger('path_commands')

class PathCommand(abc.ABC):

    def __init__(self, cmd, param_list):
        log.debug('%s::__init__: %s' % (self.__class__.__name__, param_list))

        self.param_list = param_list
        self.closed = False
        if ord(cmd) > 90:
            self.relative = True
            self.advance = self.adv_relative
        else:
            self.relative = False
            self.advance = self.adv_absolute

    def adv_absolute(self, from_p, to_p):
        return to_p
        
    def adv_relative(self, from_p, to_p):
        #print(type(from_p), type(to_p), from_p, to_p)
        return from_p + to_p
        if from_p.x and from_p.y:
            return from_p + to_p
        else:
            return to_p

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
        return point_list #line

class Lineto(PathCommand):
    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, p)
            point_list.append(cur_p)
        #point_list.append(cur_p)
        return point_list #line


class RelativeCubicBezier(PathCommand):

    def execute(self, start_point):
        pass


class VerticalLine(PathCommand):

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, Point(0, p))
            point_list.append(cur_p)
        #point_list.append(cur_p)
        return point_list #line

class HorizontalLine(PathCommand):

    def execute(self, start_point):
        point_list = []
        cur_p = start_point
        for p in self.param_list:
            cur_p = self.advance(cur_p, Point(p, 0))
            point_list.append(cur_p)

        #point_list.append(cur_p)
        return point_list #line

class CurveTo(PathCommand):

    def execute(self, start_point):
        pass

class ClosePath(PathCommand):

    def execute(self, start_point):
        pass


class Command_Factory:

    command_list = []

    def __init__(self):
        command_list = []

    @classmethod
    def clear_cmd_list(cls):
        cls.command_list = []

    @classmethod
    def make_cmd(self, token_list):

        cmd_str = token_list[0]
        log.info('command {}'.format(cmd_str))
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
        self.command_list.append(c)

        return c


if __name__ == '__main__':

    c = ClosePath('c', [])
    print(type(c))
    if type(c) is ClosePath:
        print('ClosePath')
    else:
        print('something else')