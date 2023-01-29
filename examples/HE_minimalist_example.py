from hetool.include.hetool import Hetool
import matplotlib.pyplot as plt


def printHEModel():
    plt.figure('Minimalist example')

    # Draw Patches
    patches = Hetool.getPatches()
    for patch in patches:
        if patch.isDeleted:
            thecolor = "white"
        else:
            thecolor = "blue"
        triangs = Hetool.tessellate(patch)
        for triangle in triangs:
            xt = []
            yt = []
            for pt in triangle:
                xt.append(pt.getX())
                yt.append(pt.getY())
            plt.fill(xt, yt, color=thecolor, zorder=0)

    # Draw Segments
    for segment in Hetool.getSegments():
        thecolor = "black"
        points = segment.getPointsToDraw()
        xp = []
        yp = []
        for pt in points:
            xp.append(pt.getX())
            yp.append(pt.getY())
        plt.plot(xp, yp, color=thecolor, zorder=1)

    # Draw Points
    for point in Hetool.getPoints():
        thecolor = "black"
        plt.scatter(point.getX(), point.getY(),
                    s=5, color=thecolor, zorder=2)

    plt.axis('equal')
    plt.axis('off')
    plt.show()


def main():
    # Draw minimalist example
    Hetool.insertSegment([0, 0, 4, 0, 0, 4, 0, 0])
    Hetool.insertSegment([1, 1, 2, 1, 1, 2, 1, 1])
    Hetool.selectPick(1.1, 1.1, 0.01, False)
    Hetool.delSelectedEntities()

    printHEModel()


if __name__ == "__main__":
    main()
