import abc

class PathCommand(abc.ABC):

    def __init__(self):
        pass
    @abc.abstractmethod
    def execute(self):
        pass

class RelativeMove(PathCommand):

    def __init__(self, is_first=True):
        super().__init__()
        self.is_first=is_first

    def execute(self, points):
        pass

class AbsoluteMove(PathCommand):

    def __init__(self, is_first=True):
        super().__init__()
        self.is_first=is_first

    def execute(self, points):
        pass


class PathHandler:

    num_pair = re.compile('(?P<x>[0..9+-e]+),(?P<y>[0..9+-e]+)')

    def __init__(self):
        self.init()

    def init(self):
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

