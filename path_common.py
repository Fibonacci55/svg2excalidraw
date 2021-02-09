
from collections import UserList

class Point(UserList):

    def __init__(self, x, y):
        if (x != None) and (y != None):
            super(Point, self).__init__([round(x), round(y)])
        else:
            super(Point, self).__init__([])

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


    def __iadd__(self, other):
        self.data[0] += other.x
        self.data[1] += other.y

    def __isub__(self, other):
        self.data[0] -= other.x
        self.data[1] -= other.y


def cubic_bezier (p0, p1, p2, p3, steps):

    point_list = []
    for i in range(0, steps):
        t = i / steps
        x = (1 - t)**3 * p0.x + (1 - t)**2 * 3 * t * p1.x + (1 - t) * 3 * t**2 * p2.x + t**3 * p3.x
        y = (1 - t)**3 * p0.y + (1 - t)**2 * 3 * t * p1.y + (1 - t) * 3 * t**2 * p2.y + t**3 * p3.y

        point_list.append(Point(x, y))

    return point_list



if __name__ == '__main__':

    import jsonpickle
    from excalidraw_writer import Line, Excalidraw_Painting

    p0 = Point(130, 97)
    p1 = Point(199, 115)
    p2 = Point(86, 152)
    p3 = Point(120, 142)

    points = cubic_bezier(p0, p1, p2, p3, 10)

    l = Line(x=p0.x, y=p0.y, points=points, id='L1', groupIds=['G1'])

    painting = Excalidraw_Painting(elements=[l])
    pickl_painting = jsonpickle.encode(painting, unpicklable=False, indent=3)

    outf_name = 'D:\\Projects\\svg2excalidraw\\bezier.excalidraw'

    outf = open(outf_name, 'w')
    outf.write(pickl_painting)
    outf.close()