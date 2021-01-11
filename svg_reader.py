from lxml import etree, objectify
import logging
log = logging.getLogger('svg_reader')


class Svg_Element:

    def __init__(self, svg_element, groups):
        log.info ('svg_element::svg_element')
        self.id = svg_element.attrib['id']
        self.groups = groups
        if 'style' in svg_element.attrib:
            self.style = self.style_info(svg_element.attrib['style'])
        else:
            self.style = {}

    def style_info(self, style):
        log.debug('Svg_Element::style_info: %s' % style)
        d = {}
        if style:
            l = style.split(';')
            for e in l:
                s = e.split(':')
                d[s[0]] = s[1]
        return d

    def visit (self, visitor):
        pass

class Group (Svg_Element):

    def __init__(self, svg_element, groups):
        log.info ('Group::Group')
        super().__init__(svg_element, groups)
        self.group_elements = []

    def add_element (self, svg_element):
        self.group_elements.append(svg_element)

    def visit(self, visitor):
        return visitor.visit_group (self)

class Path (Svg_Element):

    def __init__(self, svg_element, groups):
        super().__init__(svg_element, groups)
        self.path_data = svg_element.attrib['d']
        log.info ('Path::End')

    def visit(self, visitor):
        return visitor.visit_path (self)

class Rectangle (Svg_Element):

    def __init__(self, svg_element, groups):
        super().__init__(svg_element, groups)
        self.x = svg_element.attrib['x']
        self.y = svg_element.attrib['y']
        self.height = svg_element.attrib['height']
        self.width = svg_element.attrib['width']

    def visit(self, visitor):
        return visitor.visit_rectangle (self)

class SVG_Doc_Walker_Base:

    NS ='{http://www.w3.org/2000/svg}'

    def __init__(self, filename='', tree=None):
        if filename:
            self.tree = etree.parse (filename)
        elif tree:
            self.tree = tree
        else:
            raise RuntimeError ('Filename or etree missing')


    def walk(self):

        def remove_prefix(text, prefix):
            if text.startswith(prefix):
                return text[len(prefix):]
            return text

        for action, elem in etree.iterwalk(self.tree, events=("start", "end")):
            elem_name = remove_prefix(elem.tag, self.NS)
            func_name = action + '_' + elem_name
            #log.debug("searching " + func_name)
            try:
                func = getattr(self, func_name)
                try:
                    func(elem)
                except Exception as e:
                    log.debug('error calling %s/%s' % (func_name, e))
            except:
                log.debug('ignoring %s of %s' % (action, elem_name))


class My_Doc_Walker (SVG_Doc_Walker_Base):

    def __init__(self, filename):
        super().__init__(filename)
        self.group_stack = []
        self.group_ids = []
        self.g = None

    def start_g(self, svg_group):
        if not self.g:
            self.g = Group(svg_group, self.group_ids)
        else:
           self.group_stack.append(self.g)
           self.g = Group(svg_group, self.group_ids)

        self.group_ids.append(self.g.id)

    def end_g(self, svg_group):
        g = self.g
        if len (self.group_stack) > 0:
            self.g = self.group_stack.pop()
            self.g.add_element(g)
        log.debug(self.g.group_elements)

    def start_path(self, svg_path):
        log.debug('starting path %s' % svg_path.attrib['id'])
        self.g.add_element(Path(svg_path, self.group_ids))

    def start_rect (self, svg_path):
        self.g.add_element(Rectangle(svg_path, self.group_ids))


if __name__ == '__main__':

    pass

    filename = 'D:\\Projects\\SVG2Excalidraw\\tangram-14.svg'
    filename = 'D:\\Projects\\SVG2Excalidraw\\sample2.svg'

    #tree = etree.parse(filename)
    #print(isinstance(tree.getroot(), objectify.ObjectifiedElement))
    loggging.basicConfig(level=log.DEBUG)
    #g = Group()
    #svg = etree.Element ("svg")
    #print (svg)
    #NS = '{http://www.w3.org/2000/svg}'
    #tabs = []
    w = My_Doc_Walker(filename)
    w.walk()
    #print (w.g.group_elements)
