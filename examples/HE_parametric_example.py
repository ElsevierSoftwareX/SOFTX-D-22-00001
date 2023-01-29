from hetool.include.hetool import HeController, HeModel, HeView, Tesselation
import matplotlib.pyplot as plt
import numpy
import math

# PARAMETRIC MODEL USING THE HETOOL
# Plot using matplotlib

# 'rOut' sized disk w/ inner hole 'rIn' and 'n'
# slits of length 'l' and thickness 'e' w/ rounded tips


def perforatedDisk(heCtrl, heViewer, rOut, rIn, n, l, e, tol, meshsize):
    # ----- Check parameter set validity
    if rIn >= rOut:
        print("Cannot build model - inner radius is larger than outer radius")
        return
    if l < 2*e:
        print("Cannot build model - slit is ill defined")
        return
    if l >= rOut-rIn:
        print("Cannot build model - slit length too large")
        return
    r1 = rIn + (rOut-rIn-l)*0.5
    r2 = rOut - (rOut-rIn-l)*0.5
    if 2*numpy.pi*r1 < n*e:
        print("Cannot build model - cannot pack slits")
        return

    # ---- Build the model
    # Inner and outter circles
    heCtrl.insertSegment(semiCirclePoly(0.0, 0.0, rIn, 0.0, tol), tol)
    heCtrl.insertSegment(semiCirclePoly(0.0, 0.0, rIn, numpy.pi, tol), tol)
    heCtrl.insertSegment(semiCirclePoly(0.0, 0.0, rOut, 0.0, tol), tol)
    heCtrl.insertSegment(semiCirclePoly(0.0, 0.0, rOut, numpy.pi, tol), tol)
    heCtrl.changePatchSelect(True)
    heCtrl.selectPick(0.0, 0.0, tol, False)
    heCtrl.delSelectedEntities()
    # Slits
    slitPlacement = numpy.linspace(0, (2*numpy.pi*(1-1/n)), n)
    for angle in slitPlacement:
        c1_x = (r1+0.5*e)*math.cos(angle)
        c1_y = (r1+0.5*e)*math.sin(angle)
        c2_x = (r2-0.5*e)*math.cos(angle)
        c2_y = (r2-0.5*e)*math.sin(angle)
        nx = math.cos(-(numpy.pi/2-angle))
        ny = math.sin(-(numpy.pi/2-angle))

        heCtrl.insertSegment(
            [(c1_x+nx*0.5*e), (c1_y+ny*0.5*e), (c2_x+nx*0.5*e), (c2_y+ny*0.5*e)], 10*tol)
        heCtrl.insertSegment(semiCirclePoly(
            c2_x, c2_y, 0.5*e, -(numpy.pi/2-angle), tol), 10*tol)
        heCtrl.insertSegment(
            [(c1_x-nx*0.5*e), (c1_y-ny*0.5*e), (c2_x-nx*0.5*e), (c2_y-ny*0.5*e)], 10*tol)
        heCtrl.insertSegment(semiCirclePoly(
            c1_x, c1_y, 0.5*e, -(numpy.pi/2-angle)+numpy.pi, tol), 10*tol)
        heCtrl.selectPick(0.5*(c1_x+c2_x), 0.5*(c1_y+c2_y), 0.01, False)
        heCtrl.delSelectedEntities()

    # ----- Assign number of divisions in each segment
    for segment in heViewer.getSegments():
        middle = segment.getPoint(0.5)
        slength = segment.length(0, 1)
        meshdivs = math.ceil(slength/meshsize)
        heCtrl.changeSegmentSelect(True)
        heCtrl.selectPick(middle.getX(), middle.getY(), tol, False)
        heCtrl.setNumberOfSubdivisions(meshdivs, 1.0)


# Build polyline representing a semi-circle, using
# a given geometric tolerance
def semiCirclePoly(cx, cy, r, rot, tol):
    n = math.ceil(numpy.pi/numpy.arccos(1-tol/r))
    if n < 3:
        n = 3
    phi = numpy.linspace(0, numpy.pi, n+1)
    poly = []
    for angle in phi:
        xp = cx + r*math.cos(angle+rot)
        yp = cy + r*math.sin(angle+rot)
        poly.append(xp)
        poly.append(yp)
    return poly

# Draw the geometric model, using matplotlib


def printHEModel(viewer, controller):
    plt.figure('Disk with slits')

    # Draw Patches
    patches = viewer.getPatches()
    for patch in patches:
        if patch.isDeleted:
            thecolor = "white"
        else:
            thecolor = "blue"
        pts = patch.getPoints()
        triangs = Tesselation.tessellate(pts)
        for j in range(0, len(triangs)):
            xt = [triangs[j][0].getX(), triangs[j][1].getX(), triangs[j]
                  [2].getX(), triangs[j][0].getX()]
            yt = [triangs[j][0].getY(), triangs[j][1].getY(), triangs[j]
                  [2].getY(), triangs[j][0].getY()]
            plt.fill(xt, yt, color=thecolor, zorder=0)

    # Draw Segments
    for segment in viewer.getSegments():
        thecolor = "black"
        points = segment.getPointsToDraw()
        xp = []
        yp = []
        for pt in points:
            xp.append(pt.getX())
            yp.append(pt.getY())
        plt.plot(xp, yp, color=thecolor, zorder=1)

        atts = viewer.getEntityAttributes(segment)
        thecolor = "red"
        for attribute in atts:
            if attribute["type"] == "Number of Subdivisions":
                symbol = controller.getAttributeSymbol(
                    attribute, 1.0, _seg=segment)
                points = symbol['points']
                for pt in points:
                    plt.scatter(pt.getX(), pt.getY(), s=2,
                                color=thecolor, zorder=2)

    # Draw Points
    for point in viewer.getPoints():
        thecolor = "black"
        plt.scatter(point.getX(), point.getY(),
                    s=5, color=thecolor, zorder=2)

    plt.axis('equal')
    plt.axis('off')
    plt.show()


def main():
    # Set up Model-View-Controler
    main_heModel = HeModel()
    main_heView = HeView(main_heModel)
    main_heCtrl = HeController(main_heModel)

    # Geometric parameters
    rOut = 2.0
    rIn = 0.2
    nS = 5
    lS = 1.0
    eS = 0.1
    geotol = 0.001
    elmsize = eS/2

    perforatedDisk(
        main_heCtrl,
        main_heView,
        rOut,
        rIn,
        nS,
        lS,
        eS,
        geotol,
        elmsize)

    printHEModel(main_heView, main_heCtrl)


if __name__ == "__main__":
    main()
