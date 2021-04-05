import re
import copy

from excalidraw_writer import Line
from path_common import Point
from path_parser import svg_path
from path_commands import Command_Factory, ClosePath, Move

import svg2exc_logging
log = svg2exc_logging.getLogger('path_handler')


class PathHandler:

    def __init__(self):
        self.init()

    def init(self):
        self.points = []
        self.cmd_list = []
        self.sub_path_list = []
        self.current_point = Point(None, None)


    def determine_sub_paths__(self, path_data):

        log.info('>>>>> {}'.format(path_data))
        Command_Factory().clear_cmd_list()
        cmds = svg_path.parseString(path_data)
        self.cmd_list = Command_Factory().command_list
        cur_sub_path = []
        self.sub_path_list = []
        for c in self.cmd_list[1:]:
            if c.__class__.__name__ == 'Move':
                self.sub_path_list.append(cur_sub_path)
                cur_sub_path = [c]
            else:
                cur_sub_path.append(c)
        self.sub_path_list.append(cur_sub_path)
        self.sub_path_list[0].insert(0, self.cmd_list[0])
        log.debug('cmd list {}'.format(self.cmd_list))
        log.info('<<<<< ')

    def handle_close_cmds__ (self):

        for p in self.sub_path_list:
            for i, c in enumerate(p):
                if type(c) == ClosePath:
                   self.cmd_list[i-1].closed = True

        #self.cmd_list = [c for c in self.cmd_list if type(c) != ClosePath]

    def __call__(self, path_data):
        log.debug('>>>>>')

        self.init()
        self.determine_sub_paths__(path_data)
        #self.handle_close_cmds__()

        self.current_point = Point(None, None)
        line_list = []
        for p in self.sub_path_list:
            sub_path_point_list = []
            for cmd in p:
                if cmd.__class__.__name__ != 'ClosePath':
                    sub_path_point_list += cmd.execute(self.current_point)
                    self.current_point = sub_path_point_list[-1]
                else:
                    sub_path_point_list.append(sub_path_point_list[0])
                log.debug ('sub path {}'.format(sub_path_point_list))
                log.debug ('current point {}'.format(self.current_point))

            line = Line(x=sub_path_point_list[0].x, y=sub_path_point_list[0].y, points=sub_path_point_list)
            line_list.append(line)

        log.debug('<<<<<<')
        return line_list


if __name__ == '__main__':

    ho = "m4673.6 4123h-250.5v-250.5l250.5 250.5z"

    p = PathHandler()

    result = p(ho)
    print (result)

