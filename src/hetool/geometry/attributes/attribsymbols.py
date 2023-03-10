from hetool.geometry.point import Point
from hetool.geometry.segments.line import Line
from hetool.compgeom.compgeom import CompGeom
import math


class AttribSymbols:

    @staticmethod
    def getSymbol(_attribute, _scale, _pt=None, _seg=None, _patch=None):

        lines = []
        triangles = []
        squares = []
        points = []
        circles = []
        time = "before"  # determines whether the attribute will be drawn before or after

        if _attribute['symbol'] == 'Support':
            time = "before"
            if _pt is not None:
                lines, triangles, squares, circles = AttribSymbols.supportPoint(
                    _attribute, _pt, _scale)
            else:
                lines, triangles, squares, circles = AttribSymbols.supportSegment(
                    _attribute, _seg, _scale)

        elif _attribute['symbol'] == 'Arrow':

            if _attribute['type'] == "Concentrated Load":
                time = "after"
                if _pt is not None:
                    lines, triangles, circles = AttribSymbols.arrowPointCL(
                        _attribute, _pt, _scale)

            elif _attribute['type'] == "Uniform Load":
                time = "after"
                if _seg is not None:
                    lines, triangles = AttribSymbols.arrowSegmentUL(
                        _attribute, _seg, _scale)

        elif _attribute['symbol'] == 'Nsbdvs':
            time = "after"
            if _seg is not None:
                points = AttribSymbols.Nsbdvs(_attribute, _seg)

        # get the colors
        colors = []
        index = 0
        for att_type in _attribute['properties_type']:
            if att_type == "color":
                colors.append(list(_attribute['properties'].values())[
                    index].copy())
            index += 1

        symbol = {
            "lines": lines,
            "triangles": triangles,
            "squares": squares,
            "circles": circles,
            "colors": colors,
            "points": points,
            "time": time
        }

        return symbol

    @ staticmethod
    def rotateCoord(_pt, _ang):
        pt = Point(_pt.getX(), _pt.getY())
        x = (pt.x*(math.cos(_ang))) + (pt.y*(math.sin(_ang)))
        y = (pt.y*(math.cos(_ang))) - (pt.x*(math.sin(_ang)))
        return Point(x, y)

    @ staticmethod
    def getAngWithXDirec(_v2):
        v1 = Point(1, 0)
        ang = math.acos(Point.dotprod(v1, _v2)/((Point.size(v1)) *
                                                (Point.size(_v2))))
        ang = ang*180/CompGeom.PI

        return ang

    @ staticmethod
    def triangleSymbol(_pt, _scale, _ang):

        _ang = _ang*CompGeom.PI/180
        x = AttribSymbols.rotateCoord(Point(1*_scale, 0), _ang)
        y = AttribSymbols.rotateCoord(Point(0, 1*_scale), _ang)

        pt_a = _pt - x*0.75
        pt_b = pt_a + (y/2)
        pt_c = pt_a - (y/2)

        return [_pt, pt_b, pt_c]

    def squareSymbol(_pt, _scale, _ang):

        _ang = _ang*CompGeom.PI/180
        x = AttribSymbols.rotateCoord(Point(1*_scale, 0), _ang)
        y = AttribSymbols.rotateCoord(Point(0, 1*_scale), _ang)

        pt_a = _pt - (x/4) + (y/4)
        pt_b = _pt + (x/4) + (y/4)
        pt_c = _pt + (x/4) - (y/4)
        pt_d = _pt - (x/4) - (y/4)

        return [pt_a, pt_b, pt_c, pt_d]

    def circleSymbol(_pt, _r):
        x = _pt.getX()
        y = _pt.getY()
        num = 30
        circ_points = []

        for i in range(0, num):
            theta = 2*CompGeom.PI*i/num
            pt = Point(x + _r*math.cos(theta), y + _r*math.sin(theta))
            circ_points.append(pt)

        return circ_points

    def arcCircleSymbol(_pt, _r, _ang):
        x = _pt.getX()
        y = _pt.getY()
        _ang = int((360-_ang)/10)
        num = 36
        arc_points = []

        for i in range(0, num-_ang+1):
            theta = 2*CompGeom.PI*i/num
            pt = Point(x + _r*math.cos(theta), y + _r*math.sin(theta))
            arc_points.append(pt)

        return arc_points

    @ staticmethod
    def arrowSymbol(_pt, _scale, _ang):

        _ang = _ang*CompGeom.PI/180
        x = AttribSymbols.rotateCoord(Point(3*_scale, 0), _ang)
        y = AttribSymbols.rotateCoord(Point(0, 3*_scale), _ang)

        pt = _pt + x*0.1
        pt_a = pt + x*0.1
        pt_b = pt_a + y*0.1
        pt_c = pt_a - y*0.1
        pt_d = pt + x

        return [pt, pt_d], [pt, pt_b, pt_c]

    def arrowPointCL(_attribute, _pt, _scale):

        properties = _attribute['properties']
        lines = []
        triangles = []
        circles = []

        if properties['Fx'] != 0:
            if properties['Fx'] < 0:
                line, tr = AttribSymbols.arrowSymbol(_pt, _scale, 0)
            else:
                line, tr = AttribSymbols.arrowSymbol(_pt, _scale, 180)
            lines.append(line)
            triangles.append(tr)

        if properties['Fy'] != 0:
            if properties['Fy'] < 0:
                line, tr = AttribSymbols.arrowSymbol(_pt, _scale, 270)

            else:
                line, tr = AttribSymbols.arrowSymbol(_pt, _scale, 90)

            lines.append(line)
            triangles.append(tr)

        if properties['Mz'] != 0:
            if properties['Mz'] < 0:
                cr = AttribSymbols.arcCircleSymbol(_pt, _scale, 180)
                tr = AttribSymbols.triangleSymbol(
                    cr[0], _scale*0.5, 90)
                circles.append(cr)
                triangles.append(tr)
            else:
                cr = AttribSymbols.arcCircleSymbol(_pt, _scale, 180)
                tr = AttribSymbols.triangleSymbol(
                    cr[-1], _scale*0.5, 90)
                circles.append(cr)
                triangles.append(tr)

        return lines, triangles, circles

    def arrowSegmentUL(_attribute, _seg, _scale):
        properties = _attribute['properties']
        lines = []
        triangles = []
        disp = Point(0, 0)
        points = _seg.getPoints().copy()

        while len(points) >= 2:
            aux_line = Line(points[0], points[1])

            if properties['Direction']["index"] == 1:
                local = True
                v = points[1] - points[0]
            else:
                local = False

            if properties['Qx'] != 0:
                if properties['Qx'] > 0:
                    ang = 180
                    if local:
                        ang = AttribSymbols.getAngWithXDirec(v)
                        if points[1].getY() < points[0].getY():
                            ang = ang + 180
                        else:
                            ang = - ang + 180

                    l, tr = AttribSymbols.arrowSegment(
                        _scale*0.45, disp, 0.2, 0.1, 0.9, aux_line, ang, True)
                else:
                    ang = 0
                    if local:
                        ang = AttribSymbols.getAngWithXDirec(v)
                        if not points[1].getY() < points[0].getY():
                            ang = -ang

                    l, tr = AttribSymbols.arrowSegment(
                        _scale*0.45, disp, 0.2, 0.1, 0.9, aux_line, ang, False)

                lines.extend(l)
                triangles.extend(tr)

            if properties['Qy'] != 0:
                if properties['Qy'] > 0:
                    ang = 90
                    if local:
                        ang = AttribSymbols.getAngWithXDirec(v)
                        if points[1].getY() < points[0].getY():
                            ang = ang + 90
                        else:
                            ang = -ang + 90

                    l, tr = AttribSymbols.arrowSegment(
                        _scale*0.5, disp, 0.2, 0, 1, aux_line, ang, True)
                else:
                    ang = 270
                    if local:
                        ang = AttribSymbols.getAngWithXDirec(v)
                        if points[1].getY() < points[0].getY():
                            ang = ang + 270
                        else:
                            ang = -ang + 270

                    l, tr = AttribSymbols.arrowSegment(
                        _scale*0.5, disp, 0.2, 0, 1, aux_line, ang, False)

                lines.extend(l)
                triangles.extend(tr)

            points.pop(0)

        return lines, triangles

    def arrowSegment(_scale, _displc, _step, _init, _end, _seg, _ang, _orient):

        lines = []
        triangles = []
        step = _step
        cont = _init

        if _orient:
            displc = _displc
        else:
            displc = _displc*(-1)

        while cont <= _end:
            pt = _seg.getPoint(cont)
            pt = pt - displc*0.2
            l, tr = AttribSymbols.arrowSymbol(
                pt, _scale, _ang)
            lines.append(l)
            triangles.append(tr)
            cont = cont + step

        return lines, triangles

    @ staticmethod
    def supportPoint(_attribute, _pt, _scale):
        _scale = _scale*0.6
        properties = _attribute['properties']
        x = Point(1*_scale, 0)
        y = Point(0, 1*_scale)
        lines = []
        triangles = []
        squares = []
        circles = []

        if properties['Dx']:

            pt = Point(_pt.getX(), _pt.getY())
            displac = Point(x.getX(), x.getY())

            if properties['Dx pos']["index"] == 0:
                displac = displac*(-1)
                # Left
                if properties['Rz']:
                    pt = pt + displac/4

                tr = AttribSymbols.triangleSymbol(pt, _scale, 0)
                pt_d = tr[1] - x*0.1
                pt_e = tr[2] - x*0.1
            else:
                # Right
                if properties['Rz']:
                    pt = pt + displac/4

                tr = AttribSymbols.triangleSymbol(pt, _scale, 180)
                pt_d = tr[1] + x*0.1
                pt_e = tr[2] + x*0.1

            lines.append([pt_d, pt_e])
            triangles.append(tr)

            if properties['Dx value'] != 0:

                if properties['Dx value'] < 0:

                    if displac.getX() < 0:
                        pt_arrow = (pt_d+pt_e)/2 + displac*2
                    else:
                        pt_arrow = (pt_d+pt_e)/2 + displac/4

                    l, tr = AttribSymbols.arrowSymbol(
                        pt_arrow, _scale*0.5, 0)
                else:
                    if displac.getX() < 0:
                        pt_arrow = (pt_d+pt_e)/2 + displac/4
                    else:
                        pt_arrow = (pt_d+pt_e)/2 + displac*2

                    l, tr = AttribSymbols.arrowSymbol(
                        pt_arrow, _scale*0.5, 180)

                lines.append(l)
                triangles.append(tr)

        if properties['Dy']:

            pt = Point(_pt.getX(), _pt.getY())
            displac = Point(y.getX(), y.getY())

            if properties['Dy pos']["index"] == 0:
                displac = displac*(-1)
                # Down
                if properties['Rz']:
                    pt = pt + displac/4

                tr = AttribSymbols.triangleSymbol(pt, _scale, 270)
                pt_d = tr[1] - y*0.1
                pt_e = tr[2] - y*0.1
            else:
                # Up
                if properties['Rz']:
                    pt = pt + displac/4

                tr = AttribSymbols.triangleSymbol(pt, _scale, 90)
                pt_d = tr[1] + y*0.1
                pt_e = tr[2] + y*0.1

            lines.append([pt_d, pt_e])
            triangles.append(tr)

            if properties['Dy value'] != 0:

                if properties['Dy value'] < 0:

                    if displac.getY() < 0:
                        pt_arrow = (pt_d+pt_e)/2 + displac*2
                    else:
                        pt_arrow = (pt_d+pt_e)/2 + displac/4

                    l, tr = AttribSymbols.arrowSymbol(
                        pt_arrow, _scale*0.5, 270)
                else:
                    if displac.getY() < 0:
                        pt_arrow = (pt_d+pt_e)/2 + displac/4
                    else:
                        pt_arrow = (pt_d+pt_e)/2 + displac*2

                    l, tr = AttribSymbols.arrowSymbol(
                        pt_arrow, _scale*0.5, 90)

                lines.append(l)
                triangles.append(tr)

        if properties['Rz']:
            sq = AttribSymbols.squareSymbol(_pt, _scale, 0)
            squares.append(sq)

            if properties['Rz value'] != 0:
                if properties['Rz value'] < 0:
                    cr = AttribSymbols.arcCircleSymbol(_pt, _scale*1.4, 180)
                    tr = AttribSymbols.triangleSymbol(
                        cr[0], _scale*0.5, 90)

                else:
                    cr = AttribSymbols.arcCircleSymbol(_pt, _scale*1.4, 180)
                    tr = AttribSymbols.triangleSymbol(
                        cr[-1], _scale*0.5, 90)

                circles.append(cr)
                triangles.append(tr)

        return lines, triangles, squares, circles

    @ staticmethod
    def supportSegment(_attribute, _seg, _scale):

        lines = []
        triangles = []
        squares = []
        circles = []
        seg_pts = _seg.getPoints()
        points = []
        points.append(seg_pts[0])
        points.append(seg_pts[-1])
        points.append(_seg.getPoint(0.5))

        for pt in points:
            l, tr, sq, circ = AttribSymbols.supportPoint(
                _attribute, pt, _scale)
            lines.extend(l)
            triangles.extend(tr)
            squares.extend(sq)
            circles.extend(circ)

        return lines, triangles, squares, circles

    def Nsbdvs(_attribute, _seg):
        points = []
        properties = _attribute['properties']
        nsudv = properties['Value']
        ratio = properties['Ratio']
        points = CompGeom.getNumberOfSudvisions(_seg, nsudv, ratio, False)

        return points
