from hetool.include.hetool import HeController, HeModel, HeView, Tesselation
import matplotlib.pyplot as plt
import numpy
import math

# From a node coordinate list and a connectivity list build a HE model

def edge(elems, nodes, elem_ID, local_edge_ID):
    # Find local node IDs
    if local_edge_ID==0:
        ini = 0
        fin = 1
    elif local_edge_ID==1:
        ini = 1
        fin = 2
    else: # local edge 2
        ini = 2
        fin = 0

    # Limiting edge nodes
    n1 = nodes[elems[elem_ID][ini]]
    n2 = nodes[elems[elem_ID][fin]]

    # Return correctly formatted list [x1, y1, x2, y2]
    return [ n1[0], n1[1], n2[0], n2[1]]

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
    # Define a sample node|connectivity list
    nodes = numpy.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [2.0, 0.0],
        [3.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0],
        [2.0, 1.0],
        [3.0, 1.0],
        [0.0, 2.0],
        [1.0, 2.0],
        [2.0, 2.0],
        [3.0, 2.0],
        [0.0, 3.0],
        [1.0, 3.0],
        [2.0, 3.0],
        [3.0, 3.0]]
    )
    connectivity = numpy.array([
        [ 0,  5,  4],
        [ 0,  1,  5],
        [ 1,  6,  5],
        [ 1,  2,  6],
        [ 2,  3,  6],
        [ 3,  7,  6],
        [ 4,  5,  8],
        [ 5,  9,  8],
        [ 6, 11, 10],
        [ 6,  7, 11],
        [ 8,  9, 12],
        [12,  9, 13],
        [ 9, 14, 13],
        [ 9, 10, 14],
        [10, 15, 14],
        [10, 11, 15]]
    )

    # Build up a model from adding every edge in the list

    # Set up Model-View-Controler
    main_heModel = HeModel()
    main_heView = HeView(main_heModel)
    main_heCtrl = HeController(main_heModel)
    tol = 1e-6
    
    # Loop over every element on the connectivity list
    for each_elem in range(len(connectivity)):
        # Add each one of the edges
        curr_edge = edge(connectivity, nodes, each_elem, 0)
        main_heCtrl.insertSegment(curr_edge, tol)
        curr_edge = edge(connectivity, nodes, each_elem, 1)
        main_heCtrl.insertSegment(curr_edge, tol)
        curr_edge = edge(connectivity, nodes, each_elem, 2)
        main_heCtrl.insertSegment(curr_edge, tol)
    
    # Remove closed square in the center
    main_heCtrl.selectPick(1.5, 1.5, 0.01, False)
    main_heCtrl.delSelectedEntities()
    
    # Print the model
    printHEModel(main_heView, main_heCtrl)


if __name__ == "__main__":
    main()

