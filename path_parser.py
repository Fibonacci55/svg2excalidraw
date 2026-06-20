# path_parser.py
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 09:31:42 2021

@author: margraf
"""

from pyparsing import (
    Literal, Word, OneOrMore, Optional, ZeroOrMore, Group,
    Forward, nums, one_of, pyparsing_common, Dict
)

from path_commands import Command_Factory
from path_common import Point


def parse_action(tokens):
    print('parse_action:', tokens)


def make_coord_pair(tokens):
    p = Point(float(tokens[0]), float(tokens[1]))
    return p


def make_coordinate_pair_double(tokens):
    return [Point(float(tokens[0]), float(tokens[1])),
            Point(float(tokens[2]), float(tokens[3]))]


def make_coordinate_pair_triple(tokens):
    return [tokens[0], tokens[1], tokens[2]]


sign = one_of("+ -")
sign.set_name('sign')

number = Word(nums)
number.set_name('number')

# pyparsing v3+: calling pyparsing_common.number() is deprecated
real_num = pyparsing_common.number.copy()
real_num.set_name('real number')

flag = one_of("0 1")
flag.set_name('flag')

wsp = Word(" \t")
wsp.set_name('white space')

comma_wsp = Group(OneOrMore(wsp) + Optional(',') + ZeroOrMore(wsp)) | \
            Group("," + ZeroOrMore(wsp))
comma_wsp.set_name('comma_wsp')

coordinate = real_num
coordinate.set_name('coordinate')
coordinate.set_parse_action(lambda tokens: float(tokens[0]))

coordinate_pair = coordinate.set_name('x') + Optional(comma_wsp).suppress() + coordinate.set_name('y')
coordinate_pair.set_name('coordinate pair')
coordinate_pair.set_parse_action(make_coord_pair)

coordinate_pair_double = coordinate_pair + Optional(comma_wsp).suppress() + coordinate_pair
coordinate_pair_double.set_name('coordinate pair double')
coordinate_pair_double.set_parse_action(make_coordinate_pair_double)

coordinate_pair_triplet = coordinate_pair + Optional(comma_wsp) + coordinate_pair + Optional(comma_wsp) + coordinate_pair
coordinate_pair_triplet.set_name('coordinate pair triplet')
coordinate_pair_triplet.set_parse_action(make_coordinate_pair_triple)

coordinate_squence = Forward()
coordinate_squence = coordinate | coordinate + Optional(comma_wsp) + coordinate_squence

coordinate_pair_sequence = Forward()
coordinate_pair_sequence <<= coordinate_pair + Optional(wsp) + coordinate_pair_sequence | coordinate_pair
coordinate_pair_sequence.set_name('coordinate pair sequence')

curveto_coordinate_sequence = Forward()
curveto_coordinate_sequence <<= (coordinate_pair_triplet + Optional(comma_wsp).suppress() + curveto_coordinate_sequence) | coordinate_pair_triplet
curveto_coordinate_sequence.set_name('curveto coordinate sequence')

smooth_curveto_coordinate_sequence = Forward()
smooth_curveto_coordinate_sequence <<= (coordinate_pair_double + Optional(comma_wsp) + smooth_curveto_coordinate_sequence) | coordinate_pair_double
smooth_curveto_coordinate_sequence.set_name('smooth curveto coordinate sequence')

quadratic_bezier_curveto_coordinate_sequence = Forward()
quadratic_bezier_curveto_coordinate_sequence <<= (coordinate_pair_double + Optional(comma_wsp) + quadratic_bezier_curveto_coordinate_sequence) \
    | coordinate_pair_double

elliptical_arc_argument = number + Optional(comma_wsp) + number + \
                          Optional(comma_wsp) + number + comma_wsp + flag + Optional(comma_wsp) + \
                          flag + Optional(comma_wsp) + coordinate_pair
elliptical_arc_argument.set_name('elliptical arc argument')

elliptical_arc_argument_squence = Forward()
elliptical_arc_argument_squence <<= (elliptical_arc_argument + Optional(comma_wsp) + elliptical_arc_argument_squence) | elliptical_arc_argument

#############  draw commands  ###############

moveto = one_of("m M") + ZeroOrMore(wsp) + coordinate_pair_sequence
moveto.set_name('moveto')
moveto.set_parse_action(Command_Factory.make_cmd)

closepath = one_of("z Z")
closepath.set_name('closepath')

lineto = one_of("l L") + ZeroOrMore(wsp) + coordinate_pair_sequence
lineto.set_name('lineto')

horizontal_lineto = one_of("h H") + ZeroOrMore(wsp) + coordinate_squence
horizontal_lineto.set_name('horizontal_lineto')

vertical_lineto = one_of("v V") + ZeroOrMore(wsp) + coordinate_squence
vertical_lineto.set_name('vertical_lineto')

curveto_command = one_of("c C") + curveto_coordinate_sequence
curveto_command.set_name('curveto command')

smooth_curveto = one_of("s S") + ZeroOrMore(wsp) + smooth_curveto_coordinate_sequence
smooth_curveto.set_name('smooth curvetoo')

quadratic_bezier_curvetoo = one_of("q Q") + quadratic_bezier_curveto_coordinate_sequence
quadratic_bezier_curvetoo.set_name('quadratic bezier_curvetoo')

elliptical_arc = one_of("a A") + ZeroOrMore(wsp) + elliptical_arc_argument_squence
elliptical_arc.set_name('elliptical arc')

drawto_command = (
    lineto
    | vertical_lineto
    | horizontal_lineto
    | closepath
    | curveto_command
    | smooth_curveto
    | quadratic_bezier_curvetoo
    | elliptical_arc
)

drawto_command.set_name('drawto_command')
drawto_command.set_parse_action(Command_Factory.make_cmd)

svg_path = Forward()
svg_path <<= ZeroOrMore(wsp) + moveto + OneOrMore(Group(drawto_command | moveto)) | drawto_command
# svg_path.set_parse_action(print)


if __name__ == '__main__':
    cs = "240.73222,231.5351 240.73222,139.2321 333.03522,231.5351 333.03522,323.8381 333.57372,323.75927"
    m = "m240.73222,231.5351 240.73222,139.2321 333.03522,231.5351 333.03522,323.8381 333.57372,323.75927"

    mm = "m367.11705,365.87146 121.2823,0 0.5553,-121.03735 -121.8377,-0.24504 1e-4,121.28238"

    ho = "m4673.6 4123h-250.5v-250.5l250.5 250.5z"
    hv = "h-250.5v-250.5l"
    co = "M 130.06654,96.751567 C 98.636629,114.65863 86.223135,151.80909 119.76598,141.65285 153.30883,131.49661 130.06654,96.751567 130.06654,96.751567 Z"

    # Deprecated API scanString -> scan_string (kept commented, but updated)
    # for toks, start, end in coordinate_pair_sequence.scan_string(cs):
    #     print(toks, start, end)

    result = svg_path.parse_string(ho)  # parseString -> parse_string
    print(result)
