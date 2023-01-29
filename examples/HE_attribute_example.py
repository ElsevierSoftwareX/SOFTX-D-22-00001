import matplotlib.pyplot as plt
from hetool.include.hetool import Hetool
from pathlib import Path

# This example demonstrates creating a geometric model and using attributes
# The package provided already has some prototype attributes for demonstration
# The user of this package can set new attributes using the json file located
# in the directory hetool\geometry\attributes\attribprototype.json.
# Each object present in this json is a prototype attribute that can be
# configured and assigned to a geometric entity. It is advisable to look at the
# general model of an attribute prototype before working with the methods related
# to the attributes.


def printHEModel():
    plt.figure('Attribute example')
    scale = 0.1
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


# Creation of the geometric model
Hetool.insertSegment([0, 0, 4, 0])
Hetool.insertSegment([4, 0, 4, 0.5])
Hetool.insertSegment([4, 0.5, 0, 0.5])
Hetool.insertSegment([0, 0.5, 0, 0])
Hetool.insertSegment([2, 0, 2, 0.5])

# Creating attributes from attribute prototypes
Hetool.addAttribute("Material", "M1")
Hetool.addAttribute("Material", "M2")
Hetool.addAttribute("Support Conditions", "S1")
Hetool.addAttribute("Concentrated Load", "CL1")
Hetool.addAttribute("Uniform Load", "UL1")

# Getting the attributes to be configured
material_1 = Hetool.getAttributeByName("M1")
material_2 = Hetool.getAttributeByName("M2")
support = Hetool.getAttributeByName("S1")
concetratedLoad = Hetool.getAttributeByName("CL1")
uniformLoad = Hetool.getAttributeByName("UL1")

# Sets material values
material_1['properties']['YoungsModulus'] = 100000
material_1['properties']['PoisonsRatio'] = 0.3

material_2['properties']['YoungsModulus'] = 500000
material_2['properties']['PoisonsRatio'] = 0.25


# Adjust support conditions
support['properties']['Dx'] = True
support['properties']['Dy'] = True
support['properties']['Rz'] = True

# Sets the nodal value
concetratedLoad['properties']['Fy'] = -10.0
concetratedLoad['properties']['Mz'] = -2.0

# Sets the uniform charge value
uniformLoad['properties']['Qy'] = -3.0

# Sets attribute colors
material_1['properties']['Color'] = [0.5, 0.5, 0.5]  # gray
material_2['properties']['Color'] = [0.5, 0.75, 0.3]  # dark green
support['properties']['Color'] = [0.0, 0.0, 0.0]  # black
concetratedLoad['properties']['Color'] = [1.0, 0.0, 0.0]  # red
uniformLoad['properties']['Color'] = [0.0, 1.0, 0.0]  # green

# Selects the regions and adds the materials
Hetool.selectPick(1.0, 0.25, 0.01)
Hetool.setAttribute("M1")
Hetool.selectPick(3, 0.25, 0.01)
Hetool.setAttribute("M2")

# Selects the segment given by the coordinates [4,0.5,0,0] and adds the
# support condition
Hetool.selectPick(0, 0.25, 0.01)
Hetool.setAttribute("S1")

# Selects the point [4,0.5] and adds the concentrated load to this point
Hetool.selectPick(4, 0.5, 0.01)
Hetool.setAttribute("CL1")

# Selects the segment [4,0.5,0.0.5] and adds the uniform load
Hetool.selectPick(1, 0.5, 0.01)
Hetool.selectPick(3, 0.5, 0.01, True)
Hetool.setAttribute("UL1")

# Sets the number of subdivisions in all segments
Hetool.selectFence(-1, 5, -1, 1)
Hetool.setNumberOfSubdivisions(8)

# Save model (Creates a json file in the folder models)
# Try reading this file after seeing the example "HE_opensavefile_example.py"
# **** Tip: Hetool.OpenFile("models\model_4")
pth = Path("models","model_4")
Hetool.saveFile(str(pth))

# Display the model
printHEModel()
