import svg_reader
import excalidraw_writer
import jsonpickle
from collections import UserDict
from path_handler import PathHandler
import dataclasses
import copy

import svg2exc_logging
log = svg2exc_logging.getLogger('svg2excalidraw')

class SvgStyle2Excalidraw(UserDict):

    def __init__(self):

        def conv_width(width):
            if width[-2:] != 'px':
                return max(round(float(width)), 3)
            else:
                return max(round(float(width[:-2])), 3)

        super().__init__()

        self.data['fill'] = ('backgroundColor', lambda x: x)
        self.data['fill-opacity'] = ('opacity', lambda x: 100 * int(x))
        self.data['stroke-width'] = ('strokeWidth', conv_width)

    def __call__(self, svg_style):
        d = {}
        for k, v in svg_style.items():
            if k in self.data:
                exc_key = self.data[k][0]
                func = self.data[k][1]
                d[exc_key] = func(v)
        return d


class Converter:

    def __init__(self):
        self.elements = []
        self.path_handler = PathHandler()
        self.style_converter = SvgStyle2Excalidraw()
        self.groups = []

    def visit_group(self, group):
        log.debug('>>>>> {}'.format(group.id))
        self.groups.append(group.id)
        for el in group.group_elements:
            el.visit(self)
        self.groups.pop()
        log.debug('<<<<< {}'.format(group.id))

    def visit_rectangle(self, rectangle):
        log.debug('visiting rectangle')
        style = self.style_converter(rectangle.style)
        r = excalidraw_writer.Rectangle(id=rectangle.id,
                                        x=int(float(rectangle.x)),
                                        y=int(float(rectangle.y)),
                                        width=int(float(rectangle.width)),
                                        height=int(float(rectangle.height)),
                                        groupIds=copy.deepcopy(self.groups),
                                        **style)

        self.elements.append(r)

    def visit_path(self, path):
        log.debug('>>>>> {} {}'.format(path.id, path.path_data))
        style = self.style_converter(path.style)
        line_list = self.path_handler(path.path_data)
        if len(line_list) > 1:
            self.groups.append ('g_%s' % path.id)
            for i, l in enumerate(line_list):
                nl = dataclasses.replace(l, id='%s_%s' % (path.id, i),
                                         groupIds=copy.deepcopy(self.groups),
                                         **style)
                self.elements.append(nl)
            self.groups.pop()
        else:
            nl = dataclasses.replace(line_list[0], id=path.id,
                                     groupIds=copy.deepcopy(self.groups),
                                     **style,
                                     from_init=False)
            self.elements.append(nl)

        log.debug('<<<<< {}'.format(path.id))

    def convert(self, svg_elements):

        for el in svg_elements:
            el.visit(self)


if __name__ == '__main__':
    filename = 'D:\\Projects\\svg2excalidraw\\test\\tangram-15.svg'
    #filename = 'D:\\Projects\\svg2excalidraw\\test\\yves-guillou-tangram-8.svg'
    #filename = 'D:\\Projects\\svg2excalidraw\\test\\yves-guillou-tangram-22.svg'
    #filename = 'D:\\Projects\\svg2excalidraw\\test\\sample3.svg'
    #logging.basicConfig(level=logging.DEBUG)
    #formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
    #log.addFilter(logging.Filter(name='svg2excalidraw'))

    w = svg_reader.My_Doc_Walker(filename)
    w.walk()

    c = Converter()
    print("====================")
    c.convert(w.g.group_elements)

    outf_name = 'D:\\Projects\\SVG2Excalidraw\\test2.excalidraw'
    painting = excalidraw_writer.Excalidraw_Painting(elements=c.elements)
    pickl_painting = jsonpickle.encode(painting, unpicklable=False, indent=3)
    outf = open(outf_name, 'w')
    outf.write(pickl_painting)
    outf.close()
