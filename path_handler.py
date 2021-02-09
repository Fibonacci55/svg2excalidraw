import re
import copy

from excalidraw_writer import Line
from path_common import Point
from path_parser import svg_path
from path_commands import Command_Factory, ClosePath

import logging
log = logging.getLogger('svg2excalidraw')


class PathHandler:

    def __init__(self):
        self.init()

    def init(self):
        self.points = []
        self.cmd_list = []
        self.current_point = Point(None, None)


    def determine_sub_paths__(self, path_data):

        cmds = svg_path.parseString(path_data)
        #print("determine_sub_paths", Command_Factory().command_list)
        self.cmd_list = Command_Factory().command_list

    def handle_close_cmds__ (self):

        for i, c in enumerate(self.cmd_list):
            if type(c) == ClosePath:
               self.cmd_list[i-1].closed = True

        self.cmd_list = [c for c in self.cmd_list if type(c) != ClosePath]

    def __call__(self, path_data):
        log.debug('Path_Handler::__call__')

        self.init()
        self.determine_sub_paths__(path_data)
        self.handle_close_cmds__()

        self.current_point = Point(None, None)
        sub_path_list = []
        for cmd in self.cmd_list:
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
