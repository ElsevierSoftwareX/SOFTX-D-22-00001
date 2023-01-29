import matplotlib.pyplot as plt
from hetool.include.hetool import Hetool
from pathlib import Path

def printHEModel():
    plt.figure('Geometric Model')
    scale = 0.25
    symbols = []

    # Draws Patches
    for patch in Hetool.getPatches():
        if patch.isDeleted:
            thecolor = "white"
        else:
            thecolor = "blue"
            att_pat = patch.attributes
            for att in att_pat:
                if att['type'] == "Material":
                    thecolor = att['properties']['Color']
                else:
                    symbol = Hetool.getAttributeSymbol(
                        att, scale, _patch=patch)
                    symbols.append(symbol)

        triangs = Hetool.tessellate(patch)
        for triangle in triangs:
            xt = []
            yt = []
            for pt in triangle:
                xt.append(pt.getX())
                yt.append(pt.getY())
            plt.fill(xt, yt, color=thecolor, zorder=0)

    # Draws Segments
    for segment in Hetool.getSegments():
        thecolor = "black"
        points = segment.getPointsToDraw()
        xp = []
        yp = []
        for pt in points:
            xp.append(pt.getX())
            yp.append(pt.getY())
        plt.plot(xp, yp, color=thecolor, zorder=1)

        attributes = segment.attributes
        for att in attributes:
            symbol = Hetool.getAttributeSymbol(att, scale, _seg=segment)
            if symbol['time'] == 'before':
                drawAttributeSymbol(symbol)
            else:
                symbols.append(symbol)

    # Draws Points
    for point in Hetool.getPoints():
        thecolor = "black"
        plt.scatter(point.getX(), point.getY(),
                    s=5, color=thecolor, zorder=2)

        attributes = point.attributes
        for att in attributes:
            symbol = Hetool.getAttributeSymbol(att, scale, _pt=point)
            if symbol['time'] == 'before':
                drawAttributeSymbol(symbol)
            else:
                symbols.append(symbol)

    # Draws remaining symbols
    for symbol in symbols:
        drawAttributeSymbol(symbol)

    plt.axis('equal')
    plt.axis('off')
    plt.show()


# This function draws all the symbols of the created attributes
def drawAttributeSymbol(_symbol):
    lines = _symbol['lines']
    triangles = _symbol['triangles']
    squares = _symbol['squares']
    circles = _symbol['circles']
    points = _symbol['points']
    regions = []

    if len(_symbol['colors']) > 0:
        thecolor = _symbol['colors'][-1]
    else:
        thecolor = [0, 0, 0]

    # Draws lines and circles
    lines.extend(circles)
    for line in lines:
        xp = []
        yp = []
        for pt in line:
            xp.append(pt.getX())
            yp.append(pt.getY())
        plt.plot(xp, yp, color=thecolor, zorder=1)

    # Draws regions
    regions.extend(squares)
    regions.extend(triangles)
    for region in regions:
        xt = []
        yt = []
        for pt in region:
            xt.append(pt.getX())
            yt.append(pt.getY())
        plt.fill(xt, yt, color=thecolor, zorder=0)

    # Draws points
    for point in points:
        plt.scatter(point.getX(), point.getY(),
                    s=5, color=thecolor, zorder=2)


pth = str(Path("models","model_1.json"))
Hetool.openFile(pth)
printHEModel()

pth = str(Path("models","model_2.json"))
Hetool.openFile(pth)
printHEModel()

pth = str(Path("models","model_3.json"))
Hetool.openFile(pth)
printHEModel()

Hetool.resetDataStructure()
Hetool.insertSegment([0, 0, 4, 0, 0, 4, 0, 0])
Hetool.insertSegment([1, 1, 2, 1, 1, 2, 1, 1])
Hetool.selectPick(1.1, 1.1, 0.01, False)
Hetool.delSelectedEntities()
pth = str(Path("models","model_5"))
Hetool.saveFile(pth)
printHEModel()
