# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 09:31:42 2021

@author: margraf
"""

from pyparsing import Literal, Word, OneOrMore, Optional, ZeroOrMore, Group, \
    Forward, nums, oneOf, pyparsing_common

def parse_action(tokens):
    print ('parse_action:', tokens)

sign = oneOf("+ -")
sign.setName('sign')

number = Word(nums)
number.setName('number')

real_num = pyparsing_common.number()  # Word(nums + "." + nums)
real_num.setName('real number')

flag = oneOf("0 1")
flag.setName('flag')

wsp = Word(" \t")
wsp.setName('white space')

comma_wsp = Group(OneOrMore(wsp) + Optional(',') + ZeroOrMore(wsp)) | \
            Group("," + ZeroOrMore(wsp))
comma_wsp.setName('comma_wsp')

#coordinate = Optional(sign) + real_num
coordinate = real_num
coordinate.setName('coordinate')

coordinate_pair = coordinate + Optional(comma_wsp).suppress() + coordinate
coordinate_pair.setName('coordinate pair')

coordinate_pair_double = coordinate_pair + Optional(comma_wsp) + coordinate_pair
coordinate_pair_double.setName('coordinate pair double')

coordinate_pair_triplet = coordinate_pair + Optional(comma_wsp) + coordinate_pair + Optional(comma_wsp) + coordinate_pair
coordinate_pair_triplet.setName('coordinate pair triplet')

coordinate_squence = Forward()
coordinate_squence = coordinate | coordinate + Optional(comma_wsp) + coordinate_squence

coordinate_pair_sequence = Forward()
coordinate_pair_sequence <<= coordinate_pair + Optional(wsp) + coordinate_pair_sequence | coordinate_pair
coordinate_pair_sequence.setName('coordinate pair sequence')


curveto_coordinate_sequence = Forward()
curveto_coordinate_sequence <<= (coordinate_pair_triplet + Optional(comma_wsp) + curveto_coordinate_sequence) | coordinate_pair_triplet
curveto_coordinate_sequence.setName('curveto coordinate sequence')

smooth_curveto_coordinate_sequence = Forward()
smooth_curveto_coordinate_sequence <<= (coordinate_pair_double + Optional(comma_wsp) + smooth_curveto_coordinate_sequence) | coordinate_pair_double
smooth_curveto_coordinate_sequence.setName('smooth curveto coordinate sequence')

quadratic_bezier_curveto_coordinate_sequence = Forward()
quadratic_bezier_curveto_coordinate_sequence <<= (coordinate_pair_double + Optional(comma_wsp) + quadratic_bezier_curveto_coordinate_sequence) \
    | coordinate_pair_double

elliptical_arc_argument = number + Optional(comma_wsp) + number + \
                          Optional(comma_wsp) + number + comma_wsp + flag + Optional(comma_wsp) + \
                          flag + Optional(comma_wsp) + coordinate_pair
elliptical_arc_argument.setName('elliptical arc argument')

elliptical_arc_argument_squence = Forward()
elliptical_arc_argument_squence <<= (elliptical_arc_argument + Optional(comma_wsp) + elliptical_arc_argument_squence) | elliptical_arc_argument

#############   draw commands  ###############

moveto = oneOf("m M") + ZeroOrMore(wsp) + coordinate_pair_sequence
moveto.setName('moveto')
moveto.setParseAction(parse_action)

closepath = oneOf("z Z")
closepath.setName('closepath')

lineto = oneOf("l L") + ZeroOrMore(wsp) + coordinate_pair_sequence
lineto.setName('lineto')

horizontal_lineto = oneOf("h H") + ZeroOrMore(wsp) + coordinate_squence
horizontal_lineto.setName('horizontal_lineto')

vertical_lineto = oneOf("v V") + ZeroOrMore(wsp) + coordinate_squence
vertical_lineto.setName('vertical_lineto')

curveto_command = oneOf("c C") + curveto_coordinate_sequence
curveto_command.setName('curveto command')

smooth_curveto = oneOf("s S") + ZeroOrMore(wsp) + smooth_curveto_coordinate_sequence
smooth_curveto.setName('smooth curvetoo')

quadratic_bezier_curvetoo = oneOf("q Q") + quadratic_bezier_curveto_coordinate_sequence
quadratic_bezier_curvetoo.setName('quadratic bezier_curvetoo')

elliptical_arc = oneOf("a A") + ZeroOrMore(wsp) + elliptical_arc_argument_squence
elliptical_arc.setName('elliptical arc')

drawto_command = \
        lineto \
        | vertical_lineto \
        | horizontal_lineto \
        | closepath \
        | curveto_command \
        | smooth_curveto \
        | quadratic_bezier_curvetoo \
        | elliptical_arc #| moveto


drawto_command.setName('drawto_command')
drawto_command.setParseAction(parse_action)

svg_path = Forward()
#svg_path <<= ZeroOrMore(wsp) + Optional(moveto) + OneOrMore(moveto + OneOrMore(drawto_command)) | drawto_command
svg_path <<= ZeroOrMore(wsp) + moveto + OneOrMore(Group(drawto_command | moveto)) | drawto_command
#svg_path <<= ZeroOrMore(wsp) + (moveto + OneOrMore(svg_path)) | drawto_command
#svg_path <<= ZeroOrMore(wsp) + Optional(moveto) + (drawto_command + ZeroOrMore(svg_path)) | drawto_command
#svg_path <<= (drawto_command + svg_path) | drawto_command

if __name__ == '__main__':
    pass

    cs = "240.73222,231.5351 240.73222,139.2321 333.03522,231.5351 333.03522,323.8381 333.57372,323.75927"
    m = "m240.73222,231.5351 240.73222,139.2321 333.03522,231.5351 333.03522,323.8381 333.57372,323.75927"

    mm = "m367.11705,365.87146 121.2823,0 0.5553,-121.03735 -121.8377,-0.24504 1e-4,121.28238"

    ho = "m4673.6 4123h-250.5v-250.5l250.5 250.5z"
    hv = "h-250.5v-250.5l"
    co = "M 130.06654,96.751567 C 98.636629,114.65863 86.223135,151.80909 119.76598,141.65285 153.30883,131.49661 130.06654,96.751567 130.06654,96.751567 Z"
    # cp = "240.73222,231.5351"

    # for toks, start, end in coordinate_pair_sequence.scanString(cs):
    #    #print (coordinate_pair_sequence.parseString(cs))
    #    print (toks, start, end)

    # for toks, start, end in moveto.scanString(m):
    #    #print (coordinate_pair_sequence.parseString(cs))
    #    print (toks, start, end)

    #result = coordinate_pair_sequence.parseString(cs)
    #print(result)

    #result = moveto.parseString(mm)
    #print(result)

    result = svg_path.parseString(co) #, parseAll=True)c    #print(result)
    # print (coordinate_pair.parseString(cp))
