import re
import copy

from excalidraw_writer import Line
from path_common import Point
from path_parser import svg_path
from path_commands import Command_Factory, ClosePath

import svg2exc_logging
log = svg2exc_logging.getLogger('path_handler')


class PathHandler:

    def __init__(self):
        self.init()

    def init(self):
        self.points = []
        self.cmd_list = []
        self.current_point = Point(None, None)


    def determine_sub_paths__(self, path_data):

        log.info('>>>>> {}'.format(path_data))
        Command_Factory().clear_cmd_list()
        cmds = svg_path.parseString(path_data)
        self.cmd_list = Command_Factory().command_list
        log.debug('cmd list {}'.format(self.cmd_list))
        log.info('<<<<< ')

    def handle_close_cmds__ (self):

        for i, c in enumerate(self.cmd_list):
            if type(c) == ClosePath:
               self.cmd_list[i-1].closed = True

        self.cmd_list = [c for c in self.cmd_list if type(c) != ClosePath]

    def __call__(self, path_data):
        log.debug('>>>>>')

        self.init()
        self.determine_sub_paths__(path_data)
        self.handle_close_cmds__()

        self.current_point = Point(None, None)
        sub_path_list = []
        for cmd in self.cmd_list:
            sub_path = cmd.execute(self.current_point)
            log.debug ('sub path {}'.format(sub_path))
            sub_path_list.append(sub_path)
            self.current_point = Point(sub_path.end_point[0], sub_path.end_point[1])
            log.debug ('current point {}'.format(self.current_point))

        log.debug('<<<<<<')
        return sub_path_list



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
