import abc
import logging
log = logging.getLogger('svg2excalidraw')


class PathCommand(abc.ABC):

    def __init__(self, cmd, param_list):
        log.debug('%s::__init__: %s' % (self.__class__.__name__, param_list))

        self.param_list = param_list
        self.closed = False
        self.relative = ord(cmd) > 90     # lower case character


    def absolute__(self, start_point):
        self.start_point = start_point

    @abc.abstractmethod
    def execute(self, start_point):
        pass

    def __str__(self):
        return self.__class__.__name__


class Move(PathCommand):

    def execute(self, start_point):
        pass

class ClosePath(PathCommand):

    def execute(self, start_point):
        pass


class RelativeCubicBezier(PathCommand):

    def execute(self, start_point):
        pass


class VerticalLine(PathCommand):

    def execute(self, start_point):
        pass

class HorzontalLine(PathCommand):

    def execute(self, start_point):
        pass

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
    def make_cmd(self, token_list):

        cmd_str = token_list[0]
        print ('make_cmd', cmd_str)
        if cmd_str in ['m', 'M']:
            c = Move(cmd_str, token_list[1:])
        elif cmd_str in ['v', 'V']:
            c = VerticalLine(cmd_str, token_list[1:])
        elif cmd_str in ['h', 'H']:
            c = HorzontalLine(cmd_str, token_list[1:])
        elif cmd_str in ['c', 'C']:
            c = CurveTo(cmd_str, token_list[1:])
        elif cmd_str in ['z', 'Z']:
            c = ClosePath(cmd_str, token_list[1:])

        self.command_list.append(c)

        return c


if __name__ == '__main__':

    c = ClosePath('c', [])
    print(type(c))
    if type(c) is ClosePath:
        print('ClosePath')
    else:
        print('something else')