import abc
import re

import logging
log = logging.getLogger('svg2excalidraw')

from collections import UserList

class Point(UserList):
    
    def __init__(self, x, y):
        super(Point, self).__init__([round(x),round(y)])

    @property
    def x(self):
        return self.data[0]

    @x.setter
    def x(self, x):
        self.data[0] = x

    @property
    def y(self):
        return self.data[1]

    @y.setter
    def y(self, y):
        self.data[1] = y


class PathCommand(abc.ABC):

    def __init__(self, param_list):
        log.debug('%s::__init__: %s' % (self.__class__.__name__, param_list))
        self.param_list = param_list
        pass

    @abc.abstractmethod
    def execute(self, start_point):
        pass


class RelativeMove(PathCommand):

    def __init__(self, param_list):
        log.debug('%s::__init__: %s' % (self.__class__.__name__, param_list))

        super().__init__(param_list)

    def execute(self, start_point):
        pass

class AbsoluteMove(PathCommand):

    def __init__(self, param_list):
        log.debug('AbsoluteMove::__init__: %s' % param_list)
        super().__init__()

    def execute(self, start_point):
            pass

class ClosePath(PathCommand):

    def __init__(self, param_list):
        super().__init__(param_list)

    def execute(self, start_point):
        pass

class PathHandler:

    num_pair = re.compile('(?P<x>[0..9+-e]+),(?P<y>[0..9+-e]+)')
    path_cmds = ['m', 'M', 'z', 'Z', 'l', 'L',
                 'v', 'V', 'h', 'H', 'c', 'C',
                 's', 'S', 'q', 'Q', 't', 'T',
                 'a', 'A']

    def __init__(self):
        self.init()

    def init(self):
        self.points = []
        self.current_point = Point(None, None)

    def make_cmd (self, cmd_param_list):
        log.debug('Path_Handler::make_cmd')

        if cmd_param_list[0] == 'm':
            c = RelativeMove(cmd_param_list[1:])
        elif cmd_param_list[0] == 'M':
            c = AbsoluteMove(cmd_param_list[1:])
        elif cmd_param_list[0] in ['z', 'Z']:
            c = ClosePath(cmd_param_list[1:])


    def determine_sub_paths__(self, path_data):

        l = path_data.split(' ')
        sl = [i for i, v in enumerate(l) if v in self.path_cmds]
        cmd_list = []
        for i,v in enumerate(sl[:-1]):
            lb = v
            ub = sl[i+1]
            cmd = self.make_cmd(l[lb:ub])
            cmd_list.append(cmd)
        lb = sl[-1]
        cmd = self.make_cmd(l[lb:])
        cmd_list.append(cmd)

        return cmd_list


    def __call__(self, path_data):
        log.debug('Path_Handler::__call__')

        self.init()
        cmds = self.determine_sub_paths__(path_data)

        log.debug('PathHandler::__call__: %s', cmds)


    def call(self, path_data):

        log.debug('PathHandler::__call__')
        self.init()
        l = path_data.split(' ')
        log.debug('After split %s' % l)

        i = 0
        while i < len(l):
            # log.debug ("%s %s" % (i, l[i]))
            if l[i] in ['m']:
                mode = 'relative'
                i += 1
                m = self.num_pair.match(l[i])
                x = int(float(m.group('x')))
                y = int(float(m.group('y')))
                self.x = x
                self.y = y
                self.points.append([0, 0])
                cur_x = self.x
                cur_y = self.y
                i += 1
            elif l[i] in ['M']:
                mode = 'absolute'
                i += 1
                m = self.num_pair.match(l[i])
                x = int(float(m.group('x')))
                y = int(float(m.group('y')))
                self.x = x
                self.y = y
                self.points.append([0, 0])
            elif l[i] in ['z', 'Z']:
                point = copy.deepcopy(self.points[0])
                self.points.append(point)
                i += 1
            else:
                m = self.num_pair.match(l[i])
                if m:
                    # log.debug("%s" % m.group('x'))
                    if mode == 'relative':
                        cur_x += int(float(m.group('x')))
                        cur_y += int(float(m.group('y')))
                    elif mode == 'absolute':
                        cur_x = int(float(m.group('x')))
                        cur_y = int(float(m.group('y')))
                    point = [cur_x - self.x, cur_y - self.y]
                    self.points.append(point)
                    log.debug('Match += %s' % self.points)
                else:
                    log.debug('Could not match %s' % l[i])
                i += 1

        return self.points


if __name__ == '__main__':

    p = Point(1,1)

    l = p
    print (l)
    p.x = 3
    print (l)
