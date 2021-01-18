import abc
import re
from excalidraw_writer import Line
from path_common import Point

import logging
log = logging.getLogger('svg2excalidraw')



class PathCommand(abc.ABC):

    num_pair = re.compile('(?P<x>[0..9+-e]+),(?P<y>[0..9+-e]+)')

    def __init__(self, param_list):
        log.debug('%s::__init__: %s' % (self.__class__.__name__, param_list))

        self.param_list = param_list
        self.closed = False

        if self.param_list[-1] in ['z', 'Z']:
            self.param_list.pop()
            self.closed = True

    @abc.abstractmethod
    def execute(self, start_point):
        pass

    def __str__(self):
        return self.__class__.__name__


class RelativeMove(PathCommand):

    def __init__(self, param_list):
        super().__init__(param_list)

    def execute(self, start_point):
        m = self.num_pair.match(self.param_list[0])
        if not start_point:
            x = int(float(m.group('x')))
            y = int(float(m.group('y')))
        else:
            x = start_point.x + int(float(m.group('x')))
            y = start_point.y + int(float(m.group('y')))

        point_list = [Point(x, y)]

        cur_x = x
        cur_y = y
        for p in self.param_list[1:]:
            m = self.num_pair.match(p)
            cur_x += int(float(m.group('x')))
            cur_y += int(float(m.group('y')))
            point = Point(cur_x, cur_y)
            point_list.append(point)

        if self.closed:
            point_list.append(Point(x,y))

        line = Line (x=x, y=y, points=point_list)
        return line

class AbsoluteMove(PathCommand):

    def __init__(self, param_list):
        log.debug('AbsoluteMove::__init__: %s' % param_list)
        super().__init__(param_list)

    def execute(self, start_point):
        m = self.num_pair.match(self.param_list[0])
        x = int(float(m.group('x')))
        y = int(float(m.group('y')))
        point_list = [Point(x, y)]

        cur_x = x
        cur_y = y
        for p in self.param_list[1:]:
            m = self.num_pair.match(p)
            cur_x = int(float(m.group('x')))
            cur_y = int(float(m.group('y')))
            point = Point(cur_x, cur_y)
            point_list.append(point)

        if self.closed:
            point_list.append(Point(x,y))

        line = Line(x=x, y=y, points=point_list)
        return line

class ClosePath(PathCommand):

    def __init__(self, param_list):
        super().__init__(param_list)

    def execute(self, start_point):
        pass

class PathHandler:


    path_cmds = ['m', 'M', 'l', 'L', 'v', 'V',
                 'h', 'H', 'c', 'C', 's', 'S',
                 'q', 'Q', 't', 'T', 'a', 'A']
    close_cmds = ['z', 'Z']

    all_path_cmds = path_cmds + close_cmds

    def __init__(self):
        self.init()

    def init(self):
        self.points = []
        self.current_point = Point(None, None)

    def make_cmd (self, cmd_str, cmd_param_list):
        log.debug('Path_Handler::make_cmd')

        if cmd_str == 'm':
            c = RelativeMove(cmd_param_list)
        elif cmd_str == 'M':
            c = AbsoluteMove(cmd_param_list)

        return c

    def determine_sub_paths__(self, path_data):

        path_elements = path_data.split(' ')

        cmd_list = []
        cmd_str = path_elements[0]
        param_lst = []
        for el in path_elements[1:]:
            if el in self.path_cmds:
                cmd = self.make_cmd (cmd_str, param_lst)
                cmd_list.append(cmd)
                cmd_str = el
                param_lst = []
            else:
                param_lst.append(el)

        if cmd_str:
            cmd = self.make_cmd(cmd_str, param_lst)
            cmd_list.append(cmd)

        return cmd_list

    def __call__(self, path_data):
        log.debug('Path_Handler::__call__')

        self.init()
        cmd_list = self.determine_sub_paths__(path_data)

        self.current_point = Point(None, None)
        sub_path_list = []
        for cmd in cmd_list:
            sub_path = cmd.execute(self.current_point)
            sub_path_list.append(sub_path)
            self.current_point = Point(sub_path.end_point[0], sub_path.end_point[1])

        return sub_path_list
        log.debug('PathHandler::__call__, commands: %s', cmds)


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

    p= Point(None, None)

    if p:
        print ('Has values')
    else:
        print ('Has no values')
