import json

import logging as log
from dataclasses import dataclass, field
from typing import List, Dict

import jsonpickle

@dataclass
class Excalidraw_Element:

    """Base class for Excalidraw objects"""
    id: str = ''
    type: str = ''
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0
    strokeColor: str = field(default='#000000')
    backgroundColor: str = field(default='transparent')
    fillStyle: str = field(default='solid')
    strokeWidth: int = field(default=1)
    strokeStyle: str = field(default='solid')
    roughness: int = field(default=3)
    opacity: int = field(default=100)
    groupIds: List = field(default_factory=list)
    strokeSharpness: str = field(default='sharp')
    seed: int = 1234567
    version: int = field(default=316)
    versionNonce: int = 0
    isDeleted: bool = field(default=False)
    boundElementIds: list = field(default_factory=list)
    lastCommittedPoint: str = None
    startBinding: str = None
    endBinding: str = None
    startArrowhead: str = None
    endArrowhead: str = None

@dataclass
class Line (Excalidraw_Element):

    points : List = field(default_factory=list)
    from_init : bool = True

    def __post_init__(self):
        log.debug("Line::__post_init__ %s" % self.points)
        self.type = 'line'
        if self.from_init:
            self.points = [[v[0] - self.x, v[1] - self.y] for v in self.points]
        log.debug("Line::__post_init__ corrected %s" % self.points)
        xvals = [abs(e[0]) for e in self.points]
        yvals = [abs(e[1]) for e in self.points]
        self.width = max(xvals)
        self.height = max(yvals)

    @property
    def start_point (self):
        return (self.x, self.y)

    @property
    def end_point (self):
        if self.points[-1] == [0,0]:
            return (self.x, self.y)
        else:
            return (self.x + self.points[-1][0], self.y + self.points[-1][1])

@dataclass
class Rectangle(Excalidraw_Element):
    def __post_init__(self):
        self.type = 'rectangle'

@dataclass
class Txt(Excalidraw_Element):

    baseline: int = 0
    text: str = ''
    textAlign: str = 'left'
    fontFamily: int = 1
    fontSize: int = 20
    verticalAlign: str = 'top'

    def __post_init__(self):
        self.type = 'text'

@dataclass
class Excalidraw_Painting:

    def appStateDef():
        return {"gridSize": None, "viewBackgroundColor": "#ffffff"}

    type: str = 'excalidraw'
    version: int = 2
    source: str = 'https://excalidraw.com'
    elements: List[Excalidraw_Element] = field(default_factory=list)
    appState : Dict = field(default_factory=appStateDef)

if __name__ == '__main__':

    outf_name = 'D:\\Projects\\SVG2Excalidraw\\test.excalidraw'
    r = Rectangle(id='R1', x = 0.0, y=10.0, width=20.0, height=30.0, groupIds=['G1'])
    l = Line(points=[[10.0, 20.0], [30.0, 70.0]], id='L1', groupIds=['G1'])
    print (l)
    painting = Excalidraw_Painting(elements=[r, l])
    pickl_painting = jsonpickle.encode(painting, unpicklable=False, indent=3)
    #print (pickl_painting)
    json_painting = json.dumps(pickl_painting, indent=3)
    #print(json_painting)
    outf = open(outf_name, 'w')
    #outf.write(json_painting)
    outf.write(pickl_painting)
    outf.close()
