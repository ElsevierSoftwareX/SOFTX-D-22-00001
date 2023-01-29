import os
import sys
import math
from PyQt5.QtWidgets import *
from PyQt5 import QtOpenGL, QtCore
from OpenGL.GL import *
from PyQt5.QtGui import *
from hetool.include.hetool import Hetool

# BASIC GEOMETRIC MODELER
# App using Qt and OpenGL
# The usage of the Half Edge Data structure singleton is
# restricted to the canvas class, in the following ways:
# - Various checks to see if the model is empty or not
# - Using the model bounding box to adjust the canvas viewport
# - paintGL() , iterating over every geometric entity in order
#   to draw them, diferentiaitng over deleted or selected patches
# - Treating mouse click events using the mouse coordinate to:
#   finalize a curve collection and add it to the model or select
#   a patch
# - Deleting a selected Patch from the model

# Global parameter for window scaling - useful for High DPI displays
MY_SCALE_FACTOR = 1.0 # 100% (no scaling)
# Users may change this variable here, or pass a scale factor as input, via:
# ~$ python HE_curve_collector.py -s (SOME_NUMERIC_VALUE)
# Example: Scaling by 150%
# ~$ python HE_curve_collector.py -s 1.5

class AppCanvas(QtOpenGL.QGLWidget):
    def __init__(self):
        # Initializing the canvas
        super(AppCanvas, self).__init__()
        self.m_w = 0
        self.m_h = 0
        self.m_L = -1000.0
        self.m_R = 1000.0
        self.m_B = -1000.0
        self.m_T = 1000.0
        self.m_collector = AppCurveCollector()
        self.m_state = "View"
        self.m_mousePt = QtCore.QPointF(0.0, 0.0)
        self.m_heTol = 10.0

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    # Resizing uses the Hetool to check for an empty model
    def resizeGL(self, _w, _h):
        self.m_w = _w
        self.m_h = _h

        if Hetool.isEmpty():
            self.scaleWorldWindow(1.0)
        else:
            self.fitWorldToViewport()

        glViewport(0, 0, _w, _h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    # Paint GL needs to iterate over every entity in the model
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # Draw Patches
        glShadeModel(GL_SMOOTH)
        patches = Hetool.getPatches()
        for patch in patches:
            if patch.isDeleted:
                glColor3f(1.0, 1.0, 1.0)
            elif patch.isSelected():
                glColor3f(1.00, 0.75, 0.75)
            else:
                glColor3f(0.75, 0.75, 0.75)

            triangs = Hetool.tessellate(patch)
            for triangle in triangs:
                glBegin(GL_TRIANGLES)
                for pt in triangle:
                    glVertex2d(pt.getX(), pt.getY())
                glEnd()

        # Draw Segments
        segments = Hetool.getSegments()
        for segment in segments:
            pts = segment.getPointsToDraw()
            if segment.isSelected():
                glColor3f(1.0, 0.0, 0.0)
            else:
                glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_LINE_STRIP)
            for pt in pts:
                glVertex2f(pt.getX(), pt.getY())
            glEnd()

        # Draw Points
        points = Hetool.getPoints()
        for point in points:
            if point.isSelected():
                glColor3f(1.0, 0.0, 0.0)
            else:
                glColor3f(0.0, 0.0, 0.0)
            glPointSize(3)
            glBegin(GL_POINTS)
            glVertex2f(point.getX(), point.getY())
            glEnd()

        # Draw curves that are being collected
        if self.m_collector.isActive():
            tempCurve = self.m_collector.getCurveToDraw()
            if len(tempCurve) > 0:
                glColor3f(0.0, 0.0, 1.0)
                glBegin(GL_LINE_STRIP)
                for pti in tempCurve:
                    glVertex2f(pti[0], pti[1])
                glEnd()

    # Needs to check for emptiness and access the bounding box
    def fitWorldToViewport(self):
        if Hetool.isEmpty():
            return

        self.m_L, self.m_R, self.m_B, self.m_T = Hetool.getBoundBox()
        self.scaleWorldWindow(1.1)

    def scaleWorldWindow(self, _scaleFactor):
        cx = 0.5*(self.m_L + self.m_R)
        cy = 0.5*(self.m_B + self.m_T)
        dx = (self.m_R - self.m_L)*_scaleFactor
        dy = (self.m_T - self.m_B)*_scaleFactor

        ratioVP = self.m_h/self.m_w
        if dy > dx*ratioVP:
            dx = dy/ratioVP
        else:
            dy = dx*ratioVP

        self.m_L = cx - 0.5*dx
        self.m_R = cx + 0.5*dx
        self.m_B = cy - 0.5*dy
        self.m_T = cy + 0.5*dy

        self.m_heTol = 0.005*(dx+dy)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def setState(self, _state, _varg="default"):
        self.m_collector.deactivateCollector()
        if _state == "View":
            self.m_state = "View"
            Hetool.unSelectAll()
        elif _state == "Collect":
            self.m_state = "Collect"
            self.m_collector.activateCollector(_varg)
        elif _state == "Select":
            self.m_state = "Select"
        else:
            self.m_state = "View"

    def mouseMoveEvent(self, _event):
        pt = _event.pos()
        self.m_mousePt = pt
        if self.m_collector.isActive():
            pt = self.convertPtCoordsToUniverse(pt)
            self.m_collector.update(pt.x(), pt.y())
            self.update()

    # Uses the Hetool to:
    # - Snap coordinate to existing elements
    # - Add a finalized segment to the model
    # - Use click coord to select a patch
    def mouseReleaseEvent(self, _event):
        pt = _event.pos()
        if self.m_collector.isActive():
            pt_univ = self.convertPtCoordsToUniverse(pt)
            snaped, xs, ys = Hetool.snapToPoint(
                pt_univ.x(), pt_univ.y(), self.m_heTol)
            if snaped:
                isComplete = self.m_collector.collectPoint(xs, ys)
            else:
                snaped, xs, ys = Hetool.snapToSegment(
                    pt_univ.x(), pt_univ.y(), self.m_heTol)
                if snaped:
                    isComplete = self.m_collector.collectPoint(xs, ys)
                else:
                    isComplete = self.m_collector.collectPoint(
                        pt_univ.x(), pt_univ.y())

            if isComplete:
                self.setMouseTracking(False)
                curve = self.m_collector.getCurve()
                heSegment = []
                for pt in curve:
                    heSegment.append(pt[0])
                    heSegment.append(pt[1])
                Hetool.insertSegment(heSegment)
                self.update()
            else:
                self.setMouseTracking(True)

        if self.m_state == "Select":
            pt_univ = self.convertPtCoordsToUniverse(pt)
            Hetool.selectPick(pt_univ.x(), pt_univ.y(), self.m_heTol)
            self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scaleWorldWindow(0.9)
        else:
            self.scaleWorldWindow(1.1)
        self.update()

    def convertPtCoordsToUniverse(self, _pt):
        dX = self.m_R-self.m_L
        dY = self.m_T-self.m_B
        mX = _pt.x()*MY_SCALE_FACTOR * dX / self.m_w
        mY = (self.m_h-_pt.y()*MY_SCALE_FACTOR) * dY / self.m_h
        x = self.m_L + mX
        y = self.m_B + mY
        return QtCore.QPointF(x, y)


class AppCurveCollector():
    def __init__(self):
        # Initialization
        self.m_isActive = False
        self.m_curveType = "None"
        self.m_ctrlPts = []
        self.m_tempCurve = []

    def isActive(self):
        return self.m_isActive

    # Activation w/ curve type
    def activateCollector(self, _curve):
        self.m_isActive = True
        self.m_curveType = _curve

    # Deactivation clearing the collector
    def deactivateCollector(self):
        self.m_isActive = False
        self.m_curveType = "None"
        self.m_ctrlPts = []
        self.m_tempCurve = []

    # Point Collection (depends on curve type and points collected)
    def collectPoint(self, _x, _y):
        isComplete = False
        if self.m_isActive:
            if self.m_curveType == "Line":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
            elif self.m_curveType == "Bezier2":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 2:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
            elif self.m_curveType == "CircleCR":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
        return isComplete

    # Curve (temporary and finalized)
    def getCurveToDraw(self):
        return self.m_tempCurve

    def getCurve(self):
        if self.m_curveType == "Line":
            curve = self.m_ctrlPts
        else:
            curve = self.m_tempCurve
        self.m_ctrlPts = []
        self.m_tempCurve = []
        return curve

    # Update temporary curve (mouse tracking)
    def update(self, _x, _y):
        if self.m_curveType == "Line":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [self.m_ctrlPts[0], [_x, _y]]
        elif self.m_curveType == "Bezier2":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [self.m_ctrlPts[0], [_x, _y]]
            elif len(self.m_ctrlPts) == 2:
                nSampling = 20
                self.m_tempCurve = []
                for ii in range(nSampling+1):
                    t = ii/nSampling
                    ptx = (1-t)**2*self.m_ctrlPts[0][0] + \
                        2*(1-t)*t*_x + t**2*self.m_ctrlPts[1][0]
                    pty = (1-t)**2*self.m_ctrlPts[0][1] + \
                        2*(1-t)*t*_y + t**2*self.m_ctrlPts[1][1]
                    self.m_tempCurve.append([ptx, pty])
        elif self.m_curveType == "CircleCR":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                nSampling = 36
                self.m_tempCurve = []
                r = math.sqrt(
                    (_x-self.m_ctrlPts[0][0])**2 + (_y-self.m_ctrlPts[0][1])**2)
                for ii in range(nSampling):
                    theta = ii*(2*math.pi/nSampling)
                    ptx = self.m_ctrlPts[0][0] + r*math.cos(theta)
                    pty = self.m_ctrlPts[0][1] + r*math.sin(theta)
                    self.m_tempCurve.append([ptx, pty])
                self.m_tempCurve.append(
                    [self.m_tempCurve[0][0], self.m_tempCurve[0][1]])


class AppWindow(QMainWindow):
    def __init__(self):
        # Window initialization
        super(AppWindow, self).__init__()
        self.setGeometry(150, 100, 600, 400)
        self.setWindowTitle("Basic Modeler")
        self.m_canvas = AppCanvas()
        self.setCentralWidget(self.m_canvas)

        # ToolBar Actions
        tb = self.addToolBar("ToolBar")
        fit = QAction("Fit View", self)
        tb.addAction(fit)
        addLine = QAction("Add Line", self)
        tb.addAction(addLine)
        addBezier2 = QAction("Add 3 pt Bezier", self)
        tb.addAction(addBezier2)
        addCircleCR = QAction("Add Circle", self)
        tb.addAction(addCircleCR)
        select = QAction("Select", self)
        tb.addAction(select)
        delete = QAction("Delete", self)
        tb.addAction(delete)
        tb.actionTriggered[QAction].connect(self.tbpressed)
        undo = QAction("Undo", self)
        tb.addAction(undo)
        redo = QAction("Redo", self)
        tb.addAction(redo)

    # ToolBar Pressed Function
    def tbpressed(self, _action):
        if _action.text() == "Fit View":
            self.m_canvas.fitWorldToViewport()
            self.m_canvas.update()
        elif _action.text() == "Add Line":
            self.m_canvas.setState("Collect", "Line")
        elif _action.text() == "Add 3 pt Bezier":
            self.m_canvas.setState("Collect", "Bezier2")
        elif _action.text() == "Add Circle":
            self.m_canvas.setState("Collect", "CircleCR")
        elif _action.text() == "Select":
            self.m_canvas.setState("Select")
        elif _action.text() == "Delete":
            Hetool.delSelectedEntities()
            self.m_canvas.update()
        elif _action.text() == "Undo":
            Hetool.undo()
            self.m_canvas.update()
        elif _action.text() == "Redo":
            Hetool.redo()
            self.m_canvas.update()

def checkArgsForScaleFactor(arg_list):
    if "-scale_factor" in arg_list or "-s" in arg_list:
        try:
            flag_id = arg_list.index('-scale_factor')
        except ValueError:
            flag_id = arg_list.index('-s')
        flag = arg_list.pop(flag_id)
        if (flag_id >= len(arg_list)):
            print(f"WARNING: No scale factor was set. {flag} must be followed by a numeric value.")
        else:
            scl = abs(float(arg_list.pop(flag_id)))
            global MY_SCALE_FACTOR # global, initialized as 1.0
            MY_SCALE_FACTOR = scl if scl >= 1.0 else 1.0

def main():
    # Check if user provided scale factor (useful for high DPI systems)
    checkArgsForScaleFactor([x.lower() for x in sys.argv])
    os.environ["QT_SCALE_FACTOR"] = f"{MY_SCALE_FACTOR}"

    # Run app
    app = QApplication(sys.argv)
    gui = AppWindow()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
