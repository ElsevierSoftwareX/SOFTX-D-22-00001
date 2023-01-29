from hetool.he.hecontroller import HeController
from hetool.he.hemodel import HeModel
from hetool.he.heview import HeView
from hetool.compgeom.tesselation import Tesselation

# Hetool Library
# Half-Edge Based Data Structure for Two-Dimensional Solid Modeling
# Main developer: Danilo Silva Bomfim (dsbomfim2@hotmail.com)
# Contributors:
#              - André M. B. Pereira
#              - Luiz F. Bez
#              - Luiz F. Martha
#              - Pedro C. F. Lopes
#              - Rodrigo L. Soares


# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# ------------------------ INITIALIZE DATA STRUCTURE ----------------------------
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# This class initializes a new data structure and returns its controller and viewer.
# Note that multiple data structures can be created, enabling the simultaneous modeling
# of several solids from multiple modeling screens
class Hetool:
    __hemodel = HeModel()
    __heview = HeView(__hemodel)
    __hecontroller = HeController(__hemodel)

    def getHecontroller():
        return Hetool.__hecontroller

    def getHeView():
        return Hetool.__heview

    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # --------------------------- HECONTROLLER FUNCTIONS -------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------

    # This function tried to insert a new point in the model of a given controller.
    # Input data:
    #           - _pt: List containing the coordinates of a point (list);
    #                  Example (point zero): _pt = [0.0,0.0];
    #           - _tol: Tolerance used in geometric checks (float).
    # Output data: Returns a boolean (True or false) indicating whether the point was
    # added or not.
    def insertPoint(_pt, _tol=0.01):
        try:
            Hetool.__hecontroller.insertPoint(_pt, _tol)
            return True
        except:
            return False

    # This function tried to insert a new segment in the model of a given controller.
    # Input data:
    #           - _segment: List containing the coordinates of the segment;
    #                       Example 1(Polyline): _segment = [0.0,0.0,10.0,0.0,10.0,5.0];
    #                       Example 2 (Line): _segment = [0.0,0.0,10.0,0.0];
    #           - _tol: Tolerance used in geometric checks
    # Output data: Returns a boolean (True or false) indicating whether the segment was
    # added or not.
    def insertSegment(_segment, _tol=0.01):
        try:
            Hetool.__hecontroller.insertSegment(_segment, _tol)
            return True
        except:
            return False

    # This function removes all selected entities from the model.
    def delSelectedEntities():
        Hetool.__hecontroller.delSelectedEntities()

    # This function resets the data structure
    def resetDataStructure():
        Hetool.__hecontroller.resetDataStructure()

    # This function transform a hole into a face.
    def createPatch():
        Hetool.__hecontroller.createPatch()

    # This function selects a geometric entity from the x and y coordinates.
    # To select several entities in sequence just use the shift key.
    # Input data:
    #           - _x: Coordinate X (float);
    #           - _y: Coordinate Y (float);
    #           - _tol: Tolerance used in geometric checks (float);
    #           - _shiftkey: Boolean that determines if the shift key is pressed
    #                        (True or False). Determines if more than one entity
    #                        can be selected.
    def selectPick(_x,  _y,  _tol,  _shiftkey=False):
        Hetool.__hecontroller.selectPick(_x,  _y,  _tol,  _shiftkey)

    # This function selects all entities within a rectangular region.
    # To select several entities in sequence just use the shift key.
    # Input data:
    #           - _xmin,xmax: Minimum and maximum coordinates in x (float,float);
    #           - _ymin,ymax: Minimum and maximum coordinates in y (float,float);
    #           - _shiftkey: Boolean that determines if the shift key is pressed
    #                        (True or False).
    def selectFence(_xmin, _xmax, _ymin, _ymax, _shiftkey=False):
        Hetool.__hecontroller.selectFence(
            _xmin, _xmax, _ymin, _ymax, _shiftkey)

    # This function unselects all geometric elements of the data structure.
    def unSelectAll():
        Hetool.__hecontroller.unSelectAll()

    # This function determines whether or not the points will be selected by the user.
    # Input data:
    #           - _select: indicator that determines if the element can be selected
    #                      (True or False);
    def changePointSelect(_select):
        Hetool.__hecontroller.changePointSelect(_select)

    # This function determines whether or not the segments will be selected by the user.
    # Input data:
    #           - _select: indicator that determines if the element can be selected
    #                      (True or False);
    def changeSegmentSelect(_select):
        Hetool.__hecontroller.changeSegmentSelect(_select)

    # This function determines whether or not the patches will be selected by the user.
    # Input data:
    #           - _select: indicator that determines if the element can be selected
    #                      (True or False);
    def changePatchSelect(_select):
        Hetool.__hecontroller.changePatchSelect(_select)

    # This function undoes the last command executed by the data structure.
    def undo():
        Hetool.__hecontroller.undo()

    # This function redoes the last command executed by the data structure.
    def redo():
        Hetool.__hecontroller.redo()

    # This function saves a model to a file in json format.
    # Input data:
    #           - _filename: file name to be saved (str).
    def saveFile(_filename):
        Hetool.__hecontroller.saveFile(_filename)

    # This function reads a saved file.
    # Input data:
    #           - _pathfile: path to the file to be read (str).
    def openFile(_pathfile):
        Hetool.__hecontroller.openFile(_pathfile)

    # ----------------------------------------------------------------------------
    # -------------------------- Attributes Functions ----------------------------
    # ----------------------------------------------------------------------------

    # An attribute is represented by a dictionary that has the format key: value.
    # To add new attribute prototypes, go to the src\hetool\geometry\attributes\attribprototype.json
    # directory and add a new  dictionary following the general template that is
    # already contained in this file. It is advisable to look at the general model
    # of an attribute prototype before working with the methods related to the attributes.

    # This function returns the list of attribute prototypes. Attribute prototypes
    # are the different types of attributes that the user can create.
    # Output data: List of dict class objects.
    def getPrototypes():
        return Hetool.__hecontroller.attManager.getPrototypes()

    # This function returns a list containing all created attributes.
    # Output data: List of dict class object.
    def getAttributes():
        return Hetool.__hecontroller.attManager.getAttributes()

    # This function returns a given attribute from its name.
    # Input data:
    #           - _name: Attribute name (str).
    # Output data: dict class object.
    def getAttributeByName(_name):
        return Hetool.__hecontroller.attManager.getAttributeByName(_name)

    # This function returns a given attribute prototype from the type.
    # Input data:
    #           - _type: Attribute type (str).
    # Output data: dict class object
    def getPrototypeByType(_type):
        return Hetool.__hecontroller.attManager.getPrototypeByType(_type)

    # This function creates a new attribute from a prototype.
    # Input data:
    #           - _prototype: Prototype name of the attribute to be created  (str);
    #           - _name: Name of attribute to be created (created attributes must
    #                    have different names) (str).
    # Output data: Returns boolean (True or False) indicating whether the attribute
    # was created or not.
    def addAttribute(_prototype, _name):
        return Hetool.__hecontroller.addAttribute(_prototype, _name)

    # This function assigns a given attribute to one or more selected geometric entities.
    # Input data:
    #           - _name: attribute name (str).
    def setAttribute(_attribute):
        Hetool.__hecontroller.setAttribute(_attribute)

    # This function removes a given attribute to one or more selected geometric entities.
    # Input data:
    #           - _name: attribute name (str).
    def unSetAttribute(_attribute):
        Hetool.__hecontroller.unSetAttribute(_attribute)

    # This function changes the values of a given attribute.
    # Input data:
    #           - _name: attribute name to be created (str);
    #           - _values: A list containing all the values an attribute can have
    #                      (These values must be in the same order as the keys
    #                      belonging to the key properties of the attribute) (list).
    def saveAtribute(_name, _values):
        Hetool.__hecontroller.saveAtribute(_name, _values)

    # This function removes a created attribute.
    # Input data:
    #           - _name: attribute name (str).
    def removeAttribute(_name):
        Hetool.__hecontroller.removeAttribute(_name)

    # This function rename a created attribute.If the new name given is the same as
    # that of an existing attribute, the function will return False and no changes
    # will be made.
    # Input data:
    #           - _oldname: Current attribute name (str);
    #           - _newname: new attribute name (str).
    # Output data: Returns boolean (True or False) indicating whether the attribute
    #  name was modified or not.
    def renameAttribute(_oldname, _newname):
        return Hetool.__hecontroller.renameAttribute(_oldname, _newname)

    # This function returns a symbol for a given attribute. It is important to inform
    # one of the 3 geometric entities where the symbol will be drawn. The other variables
    # of the geometric elements must be passed equal to None.
    # Input data:
    #           - _attribute: Attribute to be drawn (It can be obtained from
    #                        the getAttributeByName function) (dict);
    #           - _scale: A value that determines the size of the symbol (float);
    #           - _pt: Point class object (class Point). For more information
    #                  about this class see src\hetool\geometry\point;
    #           - _seg: Segment class object (class Segment); For more information
    #                   about this class see src\hetool\geometry\segments\Line or
    #                   src\hetool\geometry\segments\Polyline;
    #           - _patch: Patch class object (class Patch);For more information
    #                     about this class see src\hetool\geometry\Patch;
    # Output data: Returns a dictionary that presents keys for each of the basic
    # shapes that can be drawn. To view the pattern of this dictionary see the getSymbol
    # function in the directory src\hetool\geometry\attributes\attribsymbols.
    def getAttributeSymbol(_attribute, _scale=1.0, _pt=None, _seg=None, _patch=None):
        return Hetool.__hecontroller.getAttributeSymbol(_attribute, _scale, _pt, _seg, _patch)

    # This function sets the number of subdivisions of a one or more selected segments.
    # Input data:
    #           - _number: number of subdivisions (int);
    #           - _ratio: proportion used for grading subdivisions (float);
    def setNumberOfSubdivisions(_number, _ratio=1):
        Hetool.__hecontroller.setNumberOfSubdivisions(_number, _ratio)

    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ---------------------------- HEVIEW FUNCTIONS ------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------

    # This function returns a list of points.
    # Output data: Returns a list of objects of class Point.For more information
    # about this class see src\hetool\geometry\point.
    def getPoints():
        return Hetool.__heview.getPoints()

    # This function returns a list of segments..
    # Output data: Returns a list of objects of class Segment.For more information
    # about this class see src\hetool\geometry\segments\line and
    # src\hetool\geometry\segments\polilyne.
    def getSegments():
        return Hetool.__heview.getSegments()

    # This function returns a list of patches
    # Output data: Returns a list of objects of class Patches.For more information
    # about this class see src\hetool\geometry\Patch.
    def getPatches():
        return Hetool.__heview.getPatches()

    # This function can be used to obtain the attributes of a geometric entity.
    # Input data:
    #           - _entity: geometric entity (class Point or class Segment or class Patch)
    # Output data: List of dict class objects
    def getEntityAttributes(_entity):
        return Hetool.__heview.getEntityAttributes(_entity)

    # This function returns a list of points that were selected by the user.
    # Output data: Returns a list of objects of class Point that were selected by
    # the user.
    def getSelectedPoints():
        return Hetool.__heview.getSelectedPoints()

    # This function returns a list of segments that were selected by the user.
    # Output data: Returns a list of objects of class Segment that were selected by
    # the user.
    def getSelectedSegments():
        return Hetool.__heview.getSelectedSegments()

    # This function returns a list of patches that were selected by the user.
    # Output data: Returns a list of objects of class Patch that were selected by
    # the user.
    def getSelectedPatches():
        return Hetool.__heview.getSelectedPatches()

    # This function can be used to check if the model is empty
    # Output data: Returns a boolean (True or False) indicating if the model is empty.
    def isEmpty():
        return Hetool.__heview.isEmpty()

    # This function can be used to determine the boundaries of a rectangular region
    #  that covers the entire model.
    # Output data: This function returns four terms that are detailed below.
    #           - xmin: Minimum coordinate value of the rectangular region in the x
    #                   direction (float);
    #           - xmax: Maximum coordinate value of the rectangular region in the x
    #                   direction (float);
    #           - ymin: Minimum coordinate value of the rectangular region in the y
    #                   direction (float);
    #           - yamx: Maximum coordinate value of the rectangular region in the y
    #                   direction (float);
    def getBoundBox():
        return Hetool.__heview.getBoundBox()

    # This function can be used to check if there is any segment of the model that
    #  is close to a user click.
    # Input data:
    #           - _x : Mouse click x coordinate (float);
    #           - _y : Mouse click y coordinate (float);
    #           - _tol : Tolerance used in geometric checks (float);
    # Output data: This function returns three terms that are detailed below.
    #           - boolean: Determines if there is a segment close to the click
    #                      according to the given tolerance (True or False);
    #           - xClst:Coordinate in the x direction of a point belongs to a segment
    #                   close to the click (float or int);
    #           - yClst: Coordinate in the y direction of a point belongs to a segment
    #                   close to the click (float or int).
    def snapToSegment(_x, _y, _tol):
        return Hetool.__heview.snapToSegment(_x, _y, _tol)

    # This function can be used to check if there is any point of the model that
    #  is close to a user click.
    # Input data:
    #           - _x : Mouse click x coordinate (float);
    #           - _y : Mouse click y coordinate (float);
    #           - _tol : Tolerance used in geometric checks (float);
    # Output data: This function returns three terms that are detailed below.
    #           - boolean: Determines if there is a model point close to the click
    #                      according to the given tolerance (True or False);
    #           - xClst:Coordinate in the x direction of a point belongs to the model
    #                   close to the click (float or int);
    #           - yClst: Coordinate in the y direction of a point belongs to the model
    #                   close to the click (float or int).
    def snapToPoint(_x, _y, _tol):
        return Hetool.__heview.snapToPoint(_x, _y, _tol)

    # ----------------------------------------------------------------------------
    # -------------------  Incidence and Adjacency Functions ---------------------
    # ----------------------------------------------------------------------------

    # This function returns a list of segments incident to a point.
    # Input data:
    #           - _point: Point class object (class Point). For more information
    #                     about this class see src\hetool\geometry\point;
    # Output data: Returns a list of objects of class Segment.
    def getIncidentSegmentsFromPoint(_point):
        return Hetool.__heview.getIncidentSegmentsFromPoint(_point)

    # This function returns a list of patches incident to a point.
    # Input data:
    #           - _point: Point class object (class Point). For more information
    #                     about this class see src\hetool\geometry\point;
    # Output data: Returns a list of objects of class Patch.
    def getIncidentPatchesFromPoint(_point):
        return Hetool.__heview.getIncidentPatchesFromPoint(_point)

    # This function returns a list of points adjacent to a point.
    # Input data:
    #           - _point: Point class object (class Point). For more information
    #                     about this class see src\hetool\geometry\point;
    # Output data: Returns a list of objects of class Point.
    def getAdjacentPointsFromPoint(_point):
        return Hetool.__heview.getAdjacentPointsFromPoint(_point)

    # This function returns a list of segments adjacent to a segment.
    # Input data:
    #           - _segment: Segment class object (class Segment). For more information
    #                       about this class see src\hetool\geometry\segments\Line or
    #                       src\hetool\geometry\segments\Polyline;
    # Output data: Returns a list of objects of class Segment.
    def getAdjacentSegmentsFromSegment(_segment):
        return Hetool.__heview.getAdjacentSegmentsFromSegment(_segment)

    # This function returns a list of patches incident to a segment.
    # Input data:
    #           - _segment: Segment class object (class Segment). For more information
    #                       about this class see src\hetool\geometry\segments\Line or
    #                       src\hetool\geometry\segments\Polyline;
    # Output data: Returns a list of objects of class Patch.
    def getIncidentPatchesFromSegment(_segment):
        return Hetool.__heview.getIncidentPatchesFromSegment(_segment)

    # This function returns a list of points incident to a segment.
    # Input data:
    #           - _segment: Segment class object (class Segment). For more information
    #                       about this class see src\hetool\geometry\segments\Line or
    #                       src\hetool\geometry\segments\Polyline;
    # Output data: Returns a list of objects of class Point.
    def getIncidentPointsFromSegment(_segment):
        return Hetool.__heview.getIncidentPointsFromSegment(_segment)

    # This function returns a list of segments incident to a patch.
    # Input data:
    #           - _patch: Patch class object (class Patch). For more information
    #                     about this class see src\hetool\geometry\Patch;
    # Output data: Returns a list of objects of class Segment.
    def getIncidentSegmentsFromPatch(_patch):
        return Hetool.__heview.getIncidentSegmentsFromPatch(_patch)

    # This function returns a list of patches adjacent to a patch.
    # Input data:
    #           - _patch: Patch class object (class Patch). For more information
    #                     about this class see src\hetool\geometry\Patch;
    # Output data: Returns a list of objects of class Patch.
    def getAdjacentPatchesFromPatch(_patch):
        return Hetool.__heview.getAdjacentPatchesFromPatch(_patch)

    # This function returns a list of points incident to a patch.
    # Input data:
    #           - _patch: Patch class object (class Patch). For more information
    #                     about this class see src\hetool\geometry\Patch;
    # Output data: Returns a list of objects of class Point.
    def getIncidentPointsFromPatch(_patch):
        return Hetool.__heview.getIncidentPointsFromPatch(_patch)

    # This function returns a list of pactches that are internal to a patch.
    # Input data:
    #           - _patch: Patch class object (class Patch);For more information
    #                     about this class see src\hetool\geometry\Patch;
    # Output data: Returns a list of objects of class Patch.
    def getInternalPacthesFromPatch(_patch):
        return Hetool.__heview.getInternalPacthesFromPatch(_patch)

    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # --------------------------- PATCH TRIANGULATION ----------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------

    # This function can be used to render a model patch through a set of triangles
    # that form the region of this patch.
    # # Input data:
    #           - _patch: Patch class object (class Patch);For more information
    #                     about this class see src\hetool\geometry\Patch;
    # Output data: Returns a list of triangles. Each triangle is represented by another
    # list of three points.
    # Note 1: To use this function efficiently, get all patches by "getPatches" function
    # which already returns all ordered regions from the outermost face to the innermost.
    # This ordering was created to enable the rendering of holes.
    # Note 2: To highlight the holes with another color, check if the patch was deleted
    # through the "isDeleted" attribute of the class Patch.
    def tessellate(_patch):
        pts = _patch.getPoints()
        return Tesselation.tessellate(pts)
