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
    # Draw operators example
    Hetool.insertPoint([0,0])              # MFVS
    Hetool.insertSegment([0,0,0.5,1])      # MEV
    Hetool.insertSegment([0.5,1,1,0,0,0])  # MEF
    Hetool.insertPoint([1,0])              # MVSE
    Hetool.insertSegment([0.5,1,0.5,-0.2]) # MVSE-MEF-MEV
    Hetool.selectPick(0.5, -0.1, 0.01)
    Hetool.delSelectedEntities()           # KEMR-KVR

    printHEModel()


if __name__ == "__main__":
    main()
