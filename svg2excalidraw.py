import svg_reader
import excalidraw_writer
import jsonpickle
import re
import copy
from collections import UserDict

import logging as log

class Path_Handler:

    num_pair = re.compile('(?P<x>[0..9+-e]+),(?P<y>[0..9+-e]+)')

    def __init__(self):
        self.init()

    def init (self):
        self.points = []
        self.x = 0
        self.y = 0

    def __call__(self, path_data):

        log.debug('Path_Handler::__call__')
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


class Svg_Style2Excalidraw(UserDict):


    def __init__(self):

        def conv_width (w):
            if w[-2:] == 'px':
                return max(round(float(w[:-2])), 3)
            else:
                return max(round(float(w)), 3)

        super().__init__()
        ident = lambda x: x

        self.data['fill'] = ('backgroundColor', ident)
        self.data['fill-opacity'] = ('opacity', lambda x: 100*x)
        self.data['stroke-width'] = ('strokeWidth', conv_width)

    def __call__(self, svg_style):
        d = {}
        for k, v in svg_style.items():
            if k in self.data:
                exc_key=self.data[k][0]
                func=self.data[k][1]
                d[exc_key]=func(v)
        return d

class Converter:

    def __init__(self, log_level=None):
        pass
        self.elements = []
        self.path_handler = Path_Handler()
        self.style_converter = Svg_Style2Excalidraw()

    def visit_group(self, group):
        log.debug('visiting group')
        for el in group.group_elements:
            el.visit(self)

    def visit_rectangle(self, rectangle):
        log.debug('visiting rectangle')
        style = self.style_converter(rectangle.style)
        r = excalidraw_writer.Rectangle(id=rectangle.id,
                                        x=int(float(rectangle.x)),
                                        y = int(float(rectangle.y)),
                                        width = int(float(rectangle.width)),
                                        height=int(float(rectangle.height)),
                                        **style)

        self.elements.append(r)

    def visit_path(self, path):
        log.debug('visiting path %s %s' % (path.id, path.path_data))
        self.path_handler(path.path_data)
        style = self.style_converter(path.style)
        l=excalidraw_writer.Line(id=path.id,
                                   x=self.path_handler.x,
                                   y=self.path_handler.y,
                                   points=self.path_handler.points,
                                   **style
                                 )
        self.elements.append(l)

    def convert (self, svg_elements):

        converted_elements = []
        for el in svg_elements:
            el.visit (self)


if __name__ == '__main__':

    filename = 'D:\\Projects\\SVG2Excalidraw\\tangram-15.svg'
    #filename = 'D:\\Projects\\SVG2Excalidraw\\sample3.svg'
    log.basicConfig(level=log.DEBUG)
    w = svg_reader.My_Doc_Walker(filename)
    w.walk()

    c = Converter()
    print ("====================")
    c.convert(w.g.group_elements)

    outf_name = 'D:\\Projects\\SVG2Excalidraw\\test1.excalidraw'
    painting = excalidraw_writer.Excalidraw_Painting(elements=c.elements)
    pickl_painting = jsonpickle.encode(painting, unpicklable=False, indent=3)
    outf = open(outf_name, 'w')
    outf.write(pickl_painting)
    outf.close()
