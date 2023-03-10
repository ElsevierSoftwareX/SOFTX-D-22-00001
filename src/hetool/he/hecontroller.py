from hetool.he.eulerOperators.MEF_KEF import MEF, KEF
from hetool.he.eulerOperators.MVFS_KVFS import MVFS, KVFS
from hetool.he.eulerOperators.MEKR_KEMR import MEKR, KEMR
from hetool.he.eulerOperators.MVR_KVR import MVR, KVR
from hetool.he.eulerOperators.MEV_KEV import MEV
from hetool.he.eulerOperators.MVSE_KVJE import MVSE, KVJE
from hetool.he.auxoperations import *
from hetool.geometry.point import Point
from hetool.geometry.segments.polyline import Polyline
from hetool.he.undoredo import UndoRedo
from hetool.compgeom.compgeom import CompGeom
from hetool.he.hefile import HeFile
from hetool.geometry.attributes.attribmanager import AttribManager
from hetool.geometry.attributes.attribsymbols import AttribSymbols
import math


class HeController:
    def __init__(self, _hemodel):
        self.undoredo = UndoRedo(10)
        self.attManager = AttribManager()
        self.hemodel = _hemodel
        self.select_segment = True
        self.select_point = True
        self.select_patch = True
        self.file = None
        self.isChanged = False

    def resetDataStructure(self):
        self.undoredo = UndoRedo(10)
        self.attManager = AttribManager()
        self.hemodel.clearAll()
        self.select_segment = True
        self.select_point = True
        self.select_patch = True
        self.file = None
        self.isChanged = False

    def setHeModel(self, _hemodel):
        self.hemodel = _hemodel

    def insertPoint(self, _pt, _tol):
        self.undoredo.begin()

        if type(_pt) == list:
            _pt = Point(_pt[0], _pt[1])

        if self.hemodel.isEmpty():
            shell = self.makeVertexFace(_pt)
            self.hemodel.infinityFace = shell.face
        else:
            self.addPoint(_pt, _tol)

        self.undoredo.end()
        self.update()

    def addPoint(self, _pt, _tol):
        # check whether there is already a point with the same coordinates
        for point in self.hemodel.points:
            tol = Point(_tol, _tol)
            if Point.equal(_pt, point, tol):
                # in this case there is already a vertex with the same coordinates
                return

        # if there isn't one, check whether the point intersects an edge in model
        intersec = False
        edges = self.hemodel.shell.edges
        for edge in edges:
            intersec, param, pi = edge.segment.intersectPoint(_pt, _tol)

            if intersec:
                edge_target = edge
                break

        if intersec:
            # if there is an intersection, then split the edge
            segments = edge_target.segment.splitSegment(param, pi)
            mvse = self.splitEdge(pi, edge_target, segments[0], segments[1])

            # copy edge_split attributes
            mvse.edge1.segment.attributes = edge_target.segment.attributes.copy()
            mvse.edge2.segment.attributes = edge_target.segment.attributes.copy()
            mvse.edge1.segment.nsudv = edge_target.segment.nsudv
            mvse.edge2.segment.nsudv = edge_target.segment.nsudv

        else:
            # if it do not intersect, then find the face where it lies on.
            #  Then add a new vertex to the model
            face_target = self.hemodel.whichFace(_pt)
            self.makeVertexInsideFace(_pt, face_target)

    def insertSegment(self, _segment, _tol):
        self.undoredo.begin()

        if type(_segment) == list:
            pts = []
            while len(_segment) > 0:
                pts.append(Point(_segment.pop(0), _segment.pop(0)))
            _segment = Polyline(pts)

        status, pts, params = _segment.selfIntersect()
        if status:
            # if there are self-intersections, split the segment in segments and
            # then insert each segment at a time
            segment_segments = _segment.split(params, pts)

            for segment in segment_segments:
                if segment is not None:
                    self.addSegment(segment, _tol)
        else:
            self.addSegment(_segment, _tol)

        self.undoredo.end()
        self.update()

    def addSegment(self, _segment, _tol):
        segmentPts = _segment.getPoints()
        init_pt = segmentPts[0]
        end_pt = segmentPts[-1]
        is_closed = (Point.euclidiandistance(init_pt, end_pt) <= _tol)

        if self.hemodel.isEmpty():
            if is_closed:
                # in this case insert the initial point and then the closed segment
                shell = self.makeVertexFace(init_pt)
                self.makeEdge(_segment, init_pt, init_pt)
            else:
                shell = self.makeVertexFace(init_pt)
                self.makeVertexInsideFace(end_pt, shell.face)
                self.makeEdge(_segment, init_pt, end_pt)

        else:
            if is_closed:
                # in this case insert the initial point and then the closed segment
                self.addPoint(init_pt, _tol)

            # intersect incoming edge with existing model
            incoming_edge_split_map, existent_edges_split_map = self.intersectModel(
                _segment, _tol)

            # split the existing edges
            self.splitExistingEdges(existent_edges_split_map,_tol)

            # insert incoming segments
            self.insertIncomingSegments(
                _segment, incoming_edge_split_map, _tol)

    def update(self):

        if self.hemodel.isEmpty():
            return

        faces = self.hemodel.shell.faces
        for i in range(1, len(faces)):
            faces[i].updateBoundary()
            faces[i].updateHoles()

        # update internal loops of infinite Face
        loop = faces[0].loop.next
        faces[0].intLoops.clear()
        while loop is not None:
            faces[0].intLoops.append(loop)
            loop = loop.next

        self.isChanged = True

    def makeVertexFace(self, _point):

        # creates, executes and stores the operation
        mvfs = MVFS(_point)
        mvfs.execute()
        self.undoredo.insertOperation(mvfs)

        # insert entities into the model data structure
        insertShell = InsertShell(mvfs.shell, self.hemodel)
        insertShell.execute()
        self.undoredo.insertOperation(insertShell)
        insertFace = InsertFace(mvfs.face, self.hemodel)
        insertFace.execute()
        self.undoredo.insertOperation(insertFace)
        insertVertex = InsertVertex(mvfs.vertex, self.hemodel)
        insertVertex.execute()
        self.undoredo.insertOperation(insertVertex)

        return mvfs

    def makeVertexInsideFace(self, _point, _face):

        # creates, executes and stores the operation
        mvr = MVR(_point, _face)
        mvr.execute()
        self.undoredo.insertOperation(mvr)

        # insert the vertex into the model data structure
        insertVertex = InsertVertex(mvr.vertex, self.hemodel)
        insertVertex.execute()
        self.undoredo.insertOperation(insertVertex)

    def makeEdge(self, _segment, _init_point, _end_point):
        # This function should be used just when the model has already been stitched by the segment.
        # This means that the geometric checks and operations should be done before you call it.
        # If this is the case, then four possibilities may occour:
        # 1: if both end points of the segment belong to vertexes of the model
        # 2: if just the first point of the segment belongs to a vertex of the model
        # 3: if just the last point of the segment belongs to a vertex of the model
        # 4: if the boundary points of the segment do not belong to the model yet

        # check if the points are already present in the model
        initpoint_belongs = False
        endpoint_belongs = False
        init_vertex = _init_point.vertex
        end_vertex = _end_point.vertex

        if init_vertex is not None:
            initpoint_belongs = True

        if end_vertex is not None:
            endpoint_belongs = True

        # update segments points
        _segment.setInitPoint(_init_point)
        _segment.setEndPoint(_end_point)

        if initpoint_belongs and endpoint_belongs:

            begin_tan = _segment.tangent(0.0)
            begin_seg = _segment.curvature(0.0)
            begin_tan = Point.normalize(begin_tan)

            he1 = self.getHalfEdge(init_vertex, begin_tan.getX(), begin_tan.getY(),
                                   -begin_tan.getY(), begin_tan.getX(), begin_seg)

            end_tan = _segment.tangent(1.0)
            end_seg = _segment.curvature(1.0)
            end_tan = Point.normalize(end_tan)

            he2 = self.getHalfEdge(end_vertex, - end_tan.getX(), -end_tan.getY(),
                                   -end_tan.getY(), end_tan.getX(), end_seg)

            if init_vertex.point != end_vertex.point:
                # case 1.1: points are different, then it is an open segment
                # checks if the half-edges have the same loop to decide between MEF and MEKR

                if he1.loop != he2.loop:

                    # case 1.1.1: the half-edges belong to the different loops, then it's a MEKR
                    if he1.loop == he1.loop.face.loop:
                        # if he1 belongs to the outter loop, then no need to inverter
                        mekr = MEKR(_segment, init_vertex, end_vertex, he1.mate(
                        ).vertex, he2.mate().vertex, he1.loop.face)
                        mekr.execute()
                        self.undoredo.insertOperation(mekr)

                    else:
                        # if he2 belongs to the outter loop, then inverter the
                        # half-edges to keep the consistency with the parametric
                        # geometric definition
                        mekr = MEKR(_segment, end_vertex, init_vertex, he2.mate(
                        ).vertex, he1.mate().vertex, he2.loop.face)
                        mekr.execute()
                        self.undoredo.insertOperation(mekr)

                        # inverter the half-edges to keep the consistency with
                        # the parametric geometric definition
                        flip = Flip(mekr.edge)
                        flip.execute()
                        self.undoredo.insertOperation(flip)

                    # insert the entities into the model data structure
                    insertEdge = InsertEdge(mekr.edge, self.hemodel)
                    insertEdge.execute()
                    self.undoredo.insertOperation(insertEdge)

                else:  # case 1.1.2: the half-edges belong to same loops, then it's a MEF

                    existent_loop = he1.loop
                    existent_face = existent_loop.face

                    if self.isSegmentLoopOriented(_segment, he1, he2):
                        mef = MEF(_segment, init_vertex, end_vertex, he1.mate(
                        ).vertex, he2.mate().vertex, existent_face)
                        mef.execute()
                        self.undoredo.insertOperation(mef)
                    else:
                        mef = MEF(_segment, end_vertex, init_vertex, he2.mate(
                        ).vertex, he1.mate().vertex, existent_face)
                        mef.execute()
                        self.undoredo.insertOperation(mef)

                        # inverter the half-edges to keep the consistency with
                        # the parametric geometric definition
                        flip = Flip(mef.edge)
                        flip.execute()
                        self.undoredo.insertOperation(flip)

                    # copy existent_face attributes
                    if existent_face.patch is not None:
                        mef.face.patch.attributes = existent_face.patch.attributes.copy()
                        mef.face.patch.isDeleted = existent_face.patch.isDeleted

                    # insert the entities into the hemodel data structure
                    insertEdge = InsertEdge(mef.edge, self.hemodel)
                    insertEdge.execute()
                    self.undoredo.insertOperation(insertEdge)
                    insertFace = InsertFace(mef.face, self.hemodel)
                    insertFace.execute()
                    self.undoredo.insertOperation(insertFace)

                    mef.face.updateBoundary()

                    inner_loops = self.findInnerLoops(
                        existent_face, mef.face, existent_loop)
                    migrateLoops = MigrateLoops(
                        existent_face, mef.face, inner_loops)
                    migrateLoops.execute()
                    self.undoredo.insertOperation(migrateLoops)

                    mef.face.updateHoles()

            else:
                # case 1.2: points are the same, then it is a closed segment
                split_point = _segment.getPoint(0.5)
                _, param, _ = _segment.intersectPoint(split_point, 0.01)
                seg1, seg2 = _segment.splitSegment(param, split_point)

                if seg1 is None or seg2 is None:
                    print('ERROR: Size of segments are less than geometric tolerance')
                    if len(self.undoredo.temp) > 0:
                        self.undoredo.end()
                        self.undo()
                        self.undoredo.clearRedo()
                    else:
                        self.undoredo.end()
                    raise ValueError

                # --------- Insert first segment ---------------------

                # insert point and segment 1 into the half-edge data structure
                mev = MEV(split_point, seg1, init_vertex, he1.mate().vertex,
                          he1.loop.face)
                mev.execute()
                self.undoredo.insertOperation(mev)

                # # inverter the half-edges to keep the consistency with
                # the parametric geometric definition
                flip = Flip(mev.edge)
                flip.execute()
                self.undoredo.insertOperation(flip)

                insertVertex = InsertVertex(mev.vertex, self.hemodel)
                insertVertex.execute()
                self.undoredo.insertOperation(insertVertex)
                insertEdge1 = InsertEdge(mev.edge, self.hemodel)
                insertEdge1.execute()
                self.undoredo.insertOperation(insertEdge1)

                # --------- Insert second segment ---------------------

                begin_tan = seg2.tangent(0.0)
                begin_seg = seg2.curvature(0.0)
                begin_tan = Point.normalize(begin_tan)

                he1 = self.getHalfEdge(mev.vertex, begin_tan.getX(), begin_tan.getY(),
                                       -begin_tan.getY(), begin_tan.getX(), begin_seg)

                end_tan = seg2.tangent(1.0)
                end_seg = seg2.curvature(1.0)
                end_tan = Point.normalize(end_tan)

                he2 = self.getHalfEdge(end_vertex, - end_tan.getX(), -end_tan.getY(),
                                       -end_tan.getY(), end_tan.getX(), end_seg)

                existent_loop = he1.loop
                existent_face = existent_loop.face

                # check segment orientation
                if self.isSegmentLoopOriented(seg2, he1, he2):
                    mef = MEF(seg2, mev.vertex, end_vertex, he1.mate(
                    ).vertex, he2.mate().vertex, existent_face)
                    mef.execute()
                    self.undoredo.insertOperation(mef)
                else:
                    mef = MEF(seg2, end_vertex, mev.vertex, he2.mate(
                    ).vertex, he1.mate().vertex, existent_face)
                    mef.execute()
                    self.undoredo.insertOperation(mef)

                    # inverter the half-edges to keep the consistency with
                    # the parametric geometric definition
                    flip = Flip(mef.edge)
                    flip.execute()
                    self.undoredo.insertOperation(flip)

                # copy existent_face attributes
                if existent_face.patch is not None:
                    mef.face.patch.attributes = existent_face.patch.attributes.copy()
                    mef.face.patch.isDeleted = existent_face.patch.isDeleted

                # insert the entities into the hemodel data structure
                insertEdge2 = InsertEdge(mef.edge, self.hemodel)
                insertEdge2.execute()
                self.undoredo.insertOperation(insertEdge2)
                insertFace = InsertFace(mef.face, self.hemodel)
                insertFace.execute()
                self.undoredo.insertOperation(insertFace)

                mef.face.updateBoundary()

                inner_loops = self.findInnerLoops(
                    existent_face, mef.face, existent_loop)
                migrateLoops = MigrateLoops(
                    existent_face, mef.face, inner_loops)
                migrateLoops.execute()
                self.undoredo.insertOperation(migrateLoops)

                mef.face.updateHoles()

        elif initpoint_belongs and not endpoint_belongs:
            # case 2: only the initial point of the segment belongs to a vertex of the model

            # get the half-edge of the vertex
            begin_tan = _segment.tangent(0.0)
            begin_seg = _segment.curvature(0.0)
            begin_tan = Point.normalize(begin_tan)
            he = self.getHalfEdge(init_vertex, begin_tan.getX(), begin_tan.getY(),
                                  -begin_tan.getY(), begin_tan.getX(), begin_seg)

            # insert point and incoming segment into the half-edge data structure
            mev = MEV(_end_point, _segment, init_vertex, he.mate().vertex,
                      he.loop.face)
            mev.execute()
            self.undoredo.insertOperation(mev)

            # inverter the half-edges to keep the consistency with
            # the parametric geometric definition
            flip = Flip(mev.edge)
            flip.execute()
            self.undoredo.insertOperation(flip)

            # insert the entities into the model data structure
            insertEdge = InsertEdge(mev.edge, self.hemodel)
            insertEdge.execute()
            self.undoredo.insertOperation(insertEdge)
            insertVertex = InsertVertex(mev.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertOperation(insertVertex)

        elif not initpoint_belongs and endpoint_belongs:
            # case 3: only the end point of the segment belongs to a vertex of the model

            # get the half-edge of the vertex
            end_tan = _segment.tangent(1.0)
            end_seg = _segment.curvature(1.0)
            end_tan = Point.normalize(end_tan)
            he = self.getHalfEdge(
                end_vertex, - end_tan.getX(), -end_tan.getY(), -end_tan.getY(), end_tan.getX(), end_seg)

            # insert point and incoming segment into the half-edge data structure
            mev = MEV(_init_point, _segment, end_vertex, he.mate().vertex,
                      he.loop.face)
            mev.execute()
            self.undoredo.insertOperation(mev)

            # insert the entities into the model data structure
            insertEdge = InsertEdge(mev.edge, self.hemodel)
            insertEdge.execute()
            self.undoredo.insertOperation(insertEdge)
            insertVertex = InsertVertex(mev.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertOperation(insertVertex)

        else:
            # case 4: neither of segment's end points belong to the model yet

            # ------------- Insert the init point -------------------

            face_target = self.hemodel.whichFace(_init_point)
            mvr = MVR(_init_point, face_target)
            mvr.execute()
            self.undoredo.insertOperation(mvr)

            # insert the entities into the model data structure
            insertVertex = InsertVertex(mvr.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertOperation(insertVertex)

            # ----- Insert the point 2 and incoming segment -----

            he = mvr.vertex.he
            mev = MEV(_end_point, _segment, mvr.vertex, he.mate().vertex,
                      he.loop.face)
            mev.execute()
            self.undoredo.insertOperation(mev)

            # inverter the half-edges to keep the consistency with the
            # parametric geometric definition
            flip = Flip(mev.edge)
            flip.execute()
            self.undoredo.insertOperation(flip)

            # insert the entities into the hemodel data structure
            insertEdge = InsertEdge(mev.edge, self.hemodel)
            insertEdge.execute()
            self.undoredo.insertOperation(insertEdge)
            insertVertex = InsertVertex(mev.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertOperation(insertVertex)

    def delSelectedEntities(self):

        self.undoredo.begin()

        selectedEdges = self.hemodel.selectedEdges()
        selectedVertices = self.hemodel.selectedVertices()

        incidentVertices = []
        for edge in selectedEdges:
            vertices = edge.incidentVertices()
            incidentVertices.extend(vertices)
            self.killEdge(edge)

        incidentVertices = list(set(incidentVertices))  # removes duplicates

        for vertex in incidentVertices:
            if vertex not in selectedVertices:
                self.killVertex(vertex)

        for vertex in selectedVertices:
            edges = vertex.incidentEdges()
            check = False
            if len(edges) == 2:
                check = self.joinEdges(edges[0], edges[1], vertex)

            if not check:
                for edge in edges:
                    vertices = edge.incidentVertices()
                    self.killEdge(edge)

                    for incidentVertex in vertices:
                        if incidentVertex not in selectedVertices:
                            self.killVertex(incidentVertex)

                self.killVertex(vertex)

        selectedFaces = self.hemodel.selectedFaces()
        for face in selectedFaces:
            delPatch = DelPatch(face.patch)
            delPatch.execute()
            self.undoredo.insertOperation(delPatch)

        self.undoredo.end()
        self.update()

    def killVertex(self, _vertex):
        he = _vertex.he

        # # case 1: checks if the vertex which will be deleted belongs
        # to a closed segment (in this case the vertex must not be deleted)
        if he.edge is None:
            # case 1.1 : checks if the vertex which will be deleted is the only one (KVFS)
            vertices = _vertex.he.loop.face.shell.vertices
            if len(vertices) == 1:

                face = _vertex.he.loop.face
                shell = face.shell

                # removes vertex and face from model data structure
                removeFace = RemoveFace(face, self.hemodel)
                removeFace.execute()
                self.undoredo.insertOperation(removeFace)
                removeVertex = RemoveVertex(_vertex, self.hemodel)
                removeVertex.execute()
                self.undoredo.insertOperation(removeVertex)
                removeShell = RemoveShell(shell, self.hemodel)
                removeShell.execute()
                self.undoredo.insertOperation(removeShell)

                # removes shell , face and point from half-edge data structure
                kvfs = KVFS(_vertex, face)
                kvfs.execute()
                self.undoredo.insertOperation(kvfs)

            # case 1.2: the vertex which will be deleted is a floating one (KVR)
            else:

                # removes vertex from model data structure
                removeVertex = RemoveVertex(_vertex, self.hemodel)
                removeVertex.execute()
                self.undoredo.insertOperation(removeVertex)

                kvr = KVR(_vertex, he.loop.face)
                kvr.execute()
                self.undoredo.insertOperation(kvr)

    def killEdge(self, _edge):
        # Case 1: checks if the Edge belongs to a face (its half-edges are
        # in different loops) (KEF)
        # Case 2: checks if both of the Edge's vertexes are incident to more
        #  than one Edge (KEMR)

        he1 = _edge.he1
        he2 = _edge.he2

        if he1.loop != he2.loop:  # Case 1(it's a KEF)

            # find which of its half-edges belongs to an outter loop
            if he1.loop == he1.loop.face.loop:
                face_to_delete = he1.loop.face
                face_to_keep = he2.loop.face
            else:
                face_to_delete = he2.loop.face
                face_to_keep = he1.loop.face

            # store inner loops
            loop = face_to_delete.loop.next
            inner_loops = []

            while loop is not None:
                inner_loops.append(loop.he.vertex)
                loop = loop.next

            # migrate loops to face_to_keep
            migrateLoops = MigrateLoops(
                face_to_delete, face_to_keep, inner_loops)
            migrateLoops.execute()
            self.undoredo.insertOperation(migrateLoops)

            # checks if it is necessary to invert the half-edges
            if he1.loop.face == face_to_delete:
                # inverter the half-edges to keep the consistency with
                # the parametric geometric definition
                flip = Flip(_edge)
                flip.execute()
                self.undoredo.insertOperation(flip)

            # removes face_to_delete from model data structure
            removeFace = RemoveFace(face_to_delete, self.hemodel)
            removeFace.execute()
            self.undoredo.insertOperation(removeFace)
            removeEdge = RemoveEdge(_edge, self.hemodel)
            removeEdge.execute()
            self.undoredo.insertOperation(removeEdge)

            kef = KEF(_edge, face_to_delete)
            kef.execute()
            self.undoredo.insertOperation(kef)

        else:
            # Test whether the edge belongs to the outter loop of its face
            vertex_out = he1.vertex
            if he1.loop == he1.loop.face.loop:
                if self.isLoopCCW(he1.next, he2):
                    vertex_out = he2.vertex

                    # inverter the half-edges to keep the consistency with
                    # the parametric geometric definition
                    flip = Flip(_edge)
                    flip.execute()
                    self.undoredo.insertOperation(flip)

            # removes edge from model data structure
            removeEdge = RemoveEdge(_edge, self.hemodel)
            removeEdge.execute()
            self.undoredo.insertOperation(removeEdge)

            # removes edge from half-edge data structure
            kemr = KEMR(_edge, vertex_out)
            kemr.execute()
            self.undoredo.insertOperation(kemr)

    def getHalfEdge(self, vertex, _tanx, _tany, _normx, _normy, _curvature):

        # get the incident edges of the vertex
        edges = vertex.incidentEdges()

        # case the vertex contains only one edge then returns its half-edge,
        # otherwise returns the half-edge that is most right of the "new edge"
        if len(edges) < 2:
            return vertex.he

        # computes the angle with the horizontal for the "new edge"
        angle_min = 2*CompGeom.PI
        curv_vec_norm_min = 0
        curv_vec_norm_i = 0
        curv_vec_norm_min_first = True
        angleRef = math.atan2(_tany, _tanx)

        if angleRef < 0:
            angleRef += 2*CompGeom.PI

        # find vector normal to given tangent
        ref_norm = Point.normalize(Point(-_tany, _tany))
        curv_vec_ref = Point(_normx*_curvature, _normy*_curvature)
        dotprod_ref = Point.dotprod(curv_vec_ref, ref_norm)

        # loops over the vertex edges to identify the desired half-edge
        he_i = vertex.he

        while True:
            # computes the angle with the horizontal for the "current edge"
            # get the correct tangent

            if he_i == he_i.edge.he1:
                tan = Point.normalize(he_i.edge.segment.tangent(0.0))
                segment_curvature = he_i.edge.segment.curvature(0.0)
                curv_vec_i = Point(-tan.getY() * segment_curvature,
                                   tan.getX() * segment_curvature)
                angle_i = math.atan2(tan.getY(), tan.getX())
            else:
                tan = Point.normalize(he_i.edge.segment.tangent(1.0))
                segment_curvature = he_i.edge.segment.curvature(1.0)
                curv_vec_i = Point(-tan.getY() * segment_curvature,
                                   tan.getX() * segment_curvature)
                angle_i = math.atan2(-tan.getY(), -tan.getX())

            if angle_i < 0:
                angle_i += 2 * CompGeom.PI

            # obtains only positive values from reference edge in ccw
            angle_i = angleRef - angle_i

            if angle_i < 0:
                angle_i = angle_i + 2.0 * CompGeom.PI

            # check if model segment is above incoming
            if angle_i == 0.0 and Point.dotprod(curv_vec_i, ref_norm) > dotprod_ref:
                angle_i = 2.0 * CompGeom.PI

            if angle_i < angle_min:
                angle_min = angle_i
                he_min = he_i
            elif angle_i == angle_min:  # tie break using curvature
                curv_vec_norm_i = Point.dotprod(curv_vec_i, curv_vec_i)

                if curv_vec_norm_min_first:
                    curv_vec_norm_min_first = False
                    curv_vec_norm_min = curv_vec_norm_i
                elif curv_vec_norm_i < curv_vec_norm_min:
                    curv_vec_norm_min = curv_vec_norm_i
                    he_min = he_i

            he_i = he_i.mate().next

            if he_i == vertex.he:
                break

        return he_min

    def intersectModel(self, _segment, _tol):
        incoming_edge_split_map = []
        existent_edges_split_map = []

        # gets the incoming segment bounding box
        xmin, xmax, ymin, ymax = _segment.getBoundBox()

        # -------------------------VERTEX INTERSECTION-------------------------
        # OBS: only floating vertices
        verticesInBound = self.hemodel.verticesCrossingWindow(
            xmin, xmax, ymin, ymax)
        for vertex in verticesInBound:
            if vertex.he.edge is None:
                status, param, pi = _segment.intersectPoint(
                    vertex.point, _tol)
                if status:
                    incoming_edge_split_map.append([param, vertex.point])

        # -------------------------EDGE INTERSECTION---------------------------
        edgesInBound = self.hemodel.edgesCrossingWindow(
            xmin, xmax, ymin, ymax)
        for edge in edgesInBound:
            existent_edge_split_map = []
            segment = edge.segment
            status, pts, existent_params, incoming_params = segment.intersectSegment(
                _segment)

            if status:
                for i in range(0, len(pts)):
                    if abs(existent_params[i]) <= CompGeom.ABSTOL:
                        point = edge.he1.vertex.point
                    elif abs(existent_params[i]-1.0) <= CompGeom.ABSTOL:
                        point = edge.he2.vertex.point
                    else:
                        point = pts[i]
                        # insert at existent params map
                        existent_edge_split_map.append(
                            [existent_params[i], point])

                    # insert in incoming params map
                    incoming_edge_split_map.append(
                        [incoming_params[i], point])

                if len(existent_edge_split_map) > 0:

                    # removes duplicate elements
                    uniqueList = []
                    for item in existent_edge_split_map:
                        insert = True
                        for unique_item in uniqueList:
                            if abs(item[0]-unique_item[0]) <= _tol:
                                tol = Point(_tol, _tol)
                                if Point.equal(item[1], unique_item[1], tol):
                                    insert = False
                                    break

                        if insert:
                            uniqueList.append(item)

                    existent_edge_split_map = uniqueList
                    existent_edge_split_map.sort()

                    existent_edges_split_map.append(
                        [edge, existent_edge_split_map])

        # removes duplicate elements
        uniqueList = []
        for item in incoming_edge_split_map:
            if item not in uniqueList:
                uniqueList.append(item)

        incoming_edge_split_map = uniqueList
        incoming_edge_split_map.sort()

        # try to insert init and end points
        segment_pts = _segment.getPoints()
        if len(incoming_edge_split_map) == 0:
            incoming_edge_split_map.append([0.0, segment_pts[0]])
            incoming_edge_split_map.append([1.0, segment_pts[-1]])
        else:
            if incoming_edge_split_map[0][0] != 0.0:
                incoming_edge_split_map.insert(0, [0.0, segment_pts[0]])
            if incoming_edge_split_map[-1][0] != 1.0:
                incoming_edge_split_map.append([1.0, segment_pts[-1]])

        return incoming_edge_split_map, existent_edges_split_map

    def splitExistingEdges(self, _edges_split_map,_tol):

        # split each intersected existent segment and insert its segments
        for edge_split_map in _edges_split_map:
            # geometrically split segments
            split_params = []
            split_pts = []
            existent_edge = edge_split_map[0]
            for split_nodes in edge_split_map[1]:
                split_params.append(split_nodes[0])
                split_pts.append(split_nodes[1])

            segments = existent_edge.segment.split(split_params, split_pts)

            # for each split point, split the segment and insert seg1
            # seg2 will have the correct topology of the splitted existent edge
            # and the geometric information of the splitted existent edge
            # each subsequent call will insert a segment (seg1) which will both
            # have geometric and topological information
            # this loop go as far as there is more than 2 segments remaining

            initial_segment = existent_edge.segment.clone()
            while len(segments) > 2:

                # split the existent segment
                segment1, segment2 = initial_segment.splitSegment(
                    split_params[0], split_pts[0])

                if segments[0].length(0, 1) > _tol and segment2.length(0, 1) > _tol:
                    # split the edge
                    mvse = self.splitEdge(split_pts[0],
                                        existent_edge, segments[0], segment2)

                    # copy edge_split attributes
                    mvse.edge1.segment.attributes = existent_edge.segment.attributes.copy()
                    mvse.edge2.segment.attributes = existent_edge.segment.attributes.copy()
                    mvse.edge1.segment.nsudv = existent_edge.segment.nsudv
                    mvse.edge2.segment.nsudv = existent_edge.segment.nsudv

                    # update the next segment to be splitted
                    existent_edge = mvse.edge2

                    segments.pop(0)
                    split_params.pop(0)
                    split_pts.pop(0)

            if segments[0].length(0, 1) > _tol and segments[1].length(0, 1) > _tol:
                # at this point there are only two segments to be inserted
                # then insert them both at the same time
                mvse = self.splitEdge(split_pts[0], existent_edge,
                                    segments[0], segments[1])

                # copy edge_split attributes
                mvse.edge1.segment.attributes = existent_edge.segment.attributes.copy()
                mvse.edge2.segment.attributes = existent_edge.segment.attributes.copy()
                mvse.edge1.segment.nsudv = existent_edge.segment.nsudv
                mvse.edge2.segment.nsudv = existent_edge.segment.nsudv

    def splitEdge(self, _pt, _split_edge, _seg1, _seg2):

        if _seg1 is None or _seg2 is None:
            if len(self.undoredo.temp) > 0:
                self.undoredo.end()
                self.undo()
                self.undoredo.clearRedo()
            else:
                self.undoredo.end()
            print('Unable to insert the segment')
            raise ValueError

        # insert and remove entities in model data structure
        removeEdge = RemoveEdge(_split_edge, self.hemodel)
        removeEdge.execute()
        self.undoredo.insertOperation(removeEdge)

        mvse = MVSE(_pt, _seg1, _seg2, _split_edge)
        mvse.execute()
        self.undoredo.insertOperation(mvse)

        insertVertex = InsertVertex(mvse.vertex, self.hemodel)
        insertVertex.execute()
        self.undoredo.insertOperation(insertVertex)
        insertEdge = InsertEdge(mvse.edge1, self.hemodel)
        insertEdge.execute()
        self.undoredo.insertOperation(insertEdge)
        insertEdge = InsertEdge(mvse.edge2, self.hemodel)
        insertEdge.execute()
        self.undoredo.insertOperation(insertEdge)

        return mvse

    def joinEdges(self, _edge1, _edge2, _vertex):

        loop1 = _edge1.he1.loop
        loop2 = _edge1.he2.loop

        if self.checkClosedSegment(loop1) or self.checkClosedSegment(loop2):
            return False

        seg1_pts = _edge1.segment.getPoints().copy()
        seg2_pts = _edge2.segment.getPoints().copy()
        joinned_pts = []

        if seg1_pts[0] == _vertex.point:
            init_pt1 = True
        else:
            init_pt1 = False

        if seg2_pts[0] == _vertex.point:
            init_pt2 = True
        else:
            init_pt2 = False

        if init_pt1 and init_pt2:
            seg1_pts.reverse()
            seg1_pts.pop()
            joinned_pts.extend(seg1_pts)
            joinned_pts.extend(seg2_pts)
        elif not init_pt1 and not init_pt2:
            seg1_pts.pop()
            joinned_pts.extend(seg1_pts)
            seg2_pts.reverse()
            joinned_pts.extend(seg2_pts)
        elif init_pt1 and not init_pt2:
            joinned_pts.extend(seg2_pts)
            joinned_pts.pop()
            joinned_pts.extend(seg1_pts)
        elif not init_pt1 and init_pt2:
            joinned_pts.extend(seg1_pts)
            joinned_pts.pop()
            joinned_pts.extend(seg2_pts)

        segment = Polyline(joinned_pts)

        # removes entities
        removeVertex = RemoveVertex(_vertex, self.hemodel)
        removeVertex.execute()
        self.undoredo.insertOperation(removeVertex)

        removeEdge = RemoveEdge(_edge1, self.hemodel)
        removeEdge.execute()
        self.undoredo.insertOperation(removeEdge)

        removeEdge = RemoveEdge(_edge2, self.hemodel)
        removeEdge.execute()
        self.undoredo.insertOperation(removeEdge)

        # execute Euler operation
        if _edge1.he1.vertex == _vertex:
            if _edge2.he1.vertex == _vertex:
                flip = Flip(_edge1)
                flip.execute()
                self.undoredo.insertOperation(flip)

                kvje = KVJE(segment, _vertex, _edge1, _edge2)
                kvje.execute()
                self.undoredo.insertOperation(kvje)
            else:
                kvje = KVJE(segment, _vertex, _edge2, _edge1)
                kvje.execute()
                self.undoredo.insertOperation(kvje)
        else:
            if not _edge2.he1.vertex == _vertex:
                flip = Flip(_edge2)
                flip.execute()
                self.undoredo.insertOperation(flip)

            kvje = KVJE(segment, _vertex, _edge1, _edge2)
            kvje.execute()
            self.undoredo.insertOperation(kvje)

        # copy attributes
        if len(kvje.edge1.segment.attributes) > 0:
            kvje.new_edge.segment.attributes = kvje.edge1.segment.attributes.copy()
            kvje.new_edge.segment.nsudv = kvje.edge1.segment.nsudv
        else:
            kvje.new_edge.segment.attributes = kvje.edge2.segment.attributes.copy()
            kvje.new_edge.segment.nsudv = kvje.edge2.segment.nsudv

        # insert joinned edge in model data structure
        insertEdge = InsertEdge(kvje.new_edge, self.hemodel)
        insertEdge.execute()
        self.undoredo.insertOperation(insertEdge)

        return True

    def checkClosedSegment(self, _loop):
        he_begin = _loop.he
        he = he_begin

        vertices = []
        while True:
            if he.vertex not in vertices:
                vertices.append(he.vertex)
            he = he.next

            if he == he_begin:
                break

        if len(vertices) == 2:
            return True
        else:
            return False

    def insertIncomingSegments(self, _segment, _incoming_segment_split_map, _tol):
        # get the splitted segments
        split_params = []
        split_pts = []
        points = []
        tol = Point(_tol, _tol)

        for split_nodes in _incoming_segment_split_map:
            split_params.append(split_nodes[0])
            split_pts.append(split_nodes[1])
            points.append(split_nodes[1])

        split_params.pop(0)
        split_params.pop()
        split_pts.pop(0)
        split_pts.pop()

        segments = _segment.split(split_params, split_pts)

        # insert segments in model
        init_point = points.pop(0)

        for seg in segments:

            if seg is None:
                if len(self.undoredo.temp) > 0:
                    self.undoredo.end()
                    self.undo()
                    self.undoredo.clearRedo()
                else:
                    self.undoredo.end()
                print('it was not possible to insert the segment')
                raise ValueError

            # get end vertex and increment
            end_point = points.pop(0)

            # The list of vertices of the hemodel is checked, verifying if the
            # init_point and end_point are already exists in the model
            init_vertex = None
            end_vertex = None
            vertices = self.hemodel.shell.vertices
            for vertex in vertices:
                if Point.equal(vertex.point, init_point, tol):
                    init_vertex = vertex
                    init_point = init_vertex.point

                if Point.equal(vertex.point, end_point, tol):
                    end_vertex = vertex
                    end_point = end_vertex.point

            make_segment = True
            if seg.length(0, 1) <= _tol:
                make_segment = False
            # check if the segment to be inserted already exists in the model
            elif init_vertex is not None and end_vertex is not None:
                if init_vertex.he is not None and end_vertex.he is not None:
                    edgesBetween = self.edgesBetween(init_vertex, end_vertex)
                    for edge in edgesBetween:
                        if seg.isEqual(edge.segment, _tol):
                            make_segment = False
                            break

            # insert the segment
            if make_segment:
                self.makeEdge(seg, init_point, end_point)

            # change the initial point
            init_point = end_point

    def isSegmentLoopOriented(self, _segment, _he1, _he2):
        he = _he1
        area = 0.0
        while he != _he2:
            if he == he.edge.he1:
                area += he.edge.segment.boundIntegral()
            else:
                area -= he.edge.segment.boundIntegral()

            he = he.next

        area -= _segment.boundIntegral()

        return area >= 0

    def isLoopCCW(self, _he1, _he2):
        area = 0.0
        he = _he1

        while he != _he2:
            if he == he.edge.he1:
                area += he.edge.segment.boundIntegral()
            else:
                area -= he.edge.segment.boundIntegral()

            he = he.next

        return area > CompGeom.ABSTOL

    def findInnerLoops(self, _existent_face, _new_face, _existent_loop):
        loop = _existent_face.loop.next
        inner_loops = []

        while loop is not None:
            if loop != _existent_loop:
                if _new_face.patch.isPointInside(loop.he.vertex.point):
                    inner_loops.append(loop.he.vertex)

            loop = loop.next

        return inner_loops

    def edgesBetween(self, _v1, _v2):
        segments_between = []
        he = _v1.he
        he_begin = he

        # check for floating vertex
        if he.edge is None:
            return segments_between

        while True:
            he = he.mate()
            if he.vertex == _v2:
                segments_between.append(he.edge)

            he = he.next

            if he == he_begin:
                break

        return segments_between

    def createPatch(self):
        self.undoredo.begin()
        selectedFaces = self.hemodel.selectedFaces()

        for face in selectedFaces:
            if face.patch.isDeleted:
                createPatch = CreatePatch(face.patch)
                createPatch.execute()
                self.undoredo.insertOperation(createPatch)

        self.isChanged = True
        self.undoredo.end()

    def undo(self):
        # check whether has redo
        if not self.undoredo.hasUndo():
            return

        # update undo stack
        self.undoredo.undo()

        # undo last command
        lastCommand = self.undoredo.lastCommand()
        for comand in lastCommand:
            comand.unexecute()

        self.update()

    def redo(self):
        # check whether has redo
        if not self.undoredo.hasRedo():
            return

        # update redo stack
        self.undoredo.redo()

        lastCommand = self.undoredo.lastCommand()
        for i in range(len(lastCommand)-1, -1, -1):
            lastCommand[i].execute()

        self.update()

    def selectPick(self, _x,  _y,  _tol,  _shiftkey):

        if self.hemodel.isEmpty():
            return

        # select point
        ispointSelected = False
        id_target = -1
        dmin = _tol
        points = self.hemodel.getPoints()
        if self.select_point:
            for i in range(0, len(points)):
                dist = Point.euclidiandistance(Point(_x, _y), points[i])
                if dist < dmin:
                    dmin = dist
                    id_target = i

            # Revert selection of picked point
            if id_target > -1:
                ispointSelected = True
                if points[id_target].isSelected():
                    points[id_target].setSelected(False)
                else:
                    points[id_target].setSelected(True)

        if not _shiftkey:
            # If shift key is not pressed, unselect all points except
            # the picked one (if there was one selected)
            for i in range(0, len(points)):
                if i != id_target:
                    points[i].setSelected(False)

        # select segment
        issegmentselected = False
        id_target = -1
        dmin = _tol
        segments = self.hemodel.getSegments()
        if self.select_segment and not ispointSelected:
            for i in range(0, len(segments)):
                # Compute distance between given point and segment and
                # update minimum distance
                xC, yC, d = segments[i].closestPoint(_x, _y)
                if d < dmin:
                    dmin = d
                    id_target = i

            # Revert selection of picked segment
            if id_target > -1:
                issegmentselected = True
                if segments[id_target].isSelected():
                    segments[id_target].setSelected(False)
                else:
                    segments[id_target].setSelected(True)

        if not _shiftkey:
            # If shift key is not pressed, unselect all segments except
            # the picked one (if there was one selected)
            for i in range(0, len(segments)):
                if i != id_target:
                    segments[i].setSelected(False)

        patches = self.hemodel.getPatches()
        if self.select_patch and not ispointSelected and not issegmentselected:
            # Check whether point is inside a patch
            p = Point(_x, _y)

            for i in range(0, len(patches)):
                if patches[i].isPointInside(p):
                    if patches[i].isSelected():
                        patches[i].setSelected(False)
                    else:
                        patches[i].setSelected(True)
                else:
                    if not _shiftkey:
                        patches[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(patches)):
                patches[i].setSelected(False)

    def selectFence(self, _xmin, _xmax, _ymin, _ymax, _shiftkey):

        if self.hemodel.isEmpty():
            return

        segments = self.hemodel.getSegments()
        if self.select_segment:
            # select segments
            for i in range(0, len(segments)):
                xmin_c, xmax_c, ymin_c, ymax_c = segments[i].getBoundBox(
                )
                if ((xmin_c < _xmin) or (xmax_c > _xmax) or
                        (ymin_c < _ymin) or (ymax_c > _ymax)):
                    inFence = False
                else:
                    inFence = True

                if inFence:
                    # Select segment inside fence
                    segments[i].setSelected(True)
                else:
                    if not _shiftkey:
                        segments[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(segments)):
                segments[i].setSelected(False)

        points = self.hemodel.getPoints()
        if self.select_point:
            # select points
            for i in range(0, len(points)):
                x = points[i].getX()
                y = points[i].getY()

                if ((x < _xmin) or (x > _xmax) or
                        (y < _ymin) or (y > _ymax)):
                    inFence = False
                else:
                    inFence = True

                if inFence:
                    # Select segment inside fence
                    points[i].setSelected(True)
                else:
                    if not _shiftkey:
                        points[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(points)):
                points[i].setSelected(False)

        patches = self.hemodel.getPatches()
        if self.select_patch:
            # select patches
            for i in range(0, len(patches)):
                xmin_r, xmax_r, ymin_r, ymax_r = patches[i].getBoundBox(
                )
                if((xmin_r < _xmin) or (xmax_r > _xmax) or
                        (ymin_r < _ymin) or (ymax_r > _ymax)):
                    inFence = False
                else:
                    inFence = True

                if inFence:
                    # Select patch inside fence
                    patches[i].setSelected(True)
                else:
                    # If shift key is not pressed, unselect patch outside fence
                    if not _shiftkey:
                        patches[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(patches)):
                patches[i].setSelected(False)

    def unSelectAll(self):
        points = self.hemodel.getPoints()
        segments = self.hemodel.getSegments()
        patches = self.hemodel.getPatches()

        for point in points:
            point.setSelected(False)

        for segment in segments:
            segment.setSelected(False)

        for patch in patches:
            patch.setSelected(False)

    def changePointSelect(self, _select):
        self.select_point = _select

    def changeSegmentSelect(self, _select):
        self.select_segment = _select

    def changePatchSelect(self, _select):
        self.select_patch = _select

    def saveFile(self, _filename):

        self.file = _filename

        # renumber IDS
        self.hemodel.shell.renumberIDS()

        shell = self.hemodel.shell
        HeFile.saveFile(shell, self.attManager.getAttributes(), _filename)
        self.isChanged = False

    def openFile(self, _filename):

        self.file = _filename
        vertices, edges, faces, attributes = HeFile.loadFile(_filename)

        self.undoredo.clear()
        self.hemodel.clearAll()

        shell = faces[0]['face'].shell
        self.hemodel.insertShell(shell)
        self.attManager.attributes = attributes

        for vertex_dict in vertices:
            self.hemodel.insertVertex(vertex_dict['vertex'])

        for edge_dict in edges:
            self.hemodel.insertEdge(edge_dict['edge'])

        for face_dict in faces:
            self.hemodel.insertFace(face_dict['face'])

        self.update()
        self.isChanged = False

    def setAttribute(self, _name):

        attribute = self.attManager.getAttributeByName(_name)
        self.undoredo.begin()

        if attribute['applyOnVertex']:
            points = self.hemodel.getPoints()

            for pt in points:
                if pt.isSelected():
                    pt.setSelected(False)
                    setAtt = SetAttribute(pt, attribute)
                    setAtt.execute()
                    self.undoredo.insertOperation(setAtt)

        if attribute['applyOnEdge']:
            segments = self.hemodel.getSegments()

            for seg in segments:
                if seg.isSelected():
                    seg.setSelected(False)
                    setAtt = SetAttribute(seg, attribute)
                    setAtt.execute()
                    self.undoredo.insertOperation(setAtt)

                    # change the support conditions of the segment points
                    if attribute['type'] == 'Support Conditions':
                        seg_vertices = seg.edge.incidentVertices()
                        if attribute not in seg_vertices[0].point.attributes:
                            setAtt = SetAttribute(
                                seg_vertices[0].point, attribute)
                            setAtt.execute()
                            self.undoredo.insertOperation(setAtt)

                        if attribute not in seg_vertices[1].point.attributes:
                            setAtt = SetAttribute(
                                seg_vertices[-1].point, attribute)
                            setAtt.execute()
                            self.undoredo.insertOperation(setAtt)

        if attribute['applyOnFace']:
            patches = self.hemodel.getPatches()

            for patch in patches:
                if patch.isSelected() and not patch.isDeleted:
                    patch.setSelected(False)
                    setAtt = SetAttribute(patch, attribute)
                    setAtt.execute()
                    self.undoredo.insertOperation(setAtt)

        self.undoredo.end()
        self.isChanged = True

    def unSetAttribute(self, _name):

        attribute = self.attManager.getAttributeByName(_name)
        self.undoredo.begin()

        if attribute['applyOnVertex']:
            points = self.hemodel.getPoints()

            for pt in points:
                if pt.isSelected():
                    pt.setSelected(False)
                    if attribute in pt.attributes:
                        unsetAtt = UnSetAttribute(pt, attribute)
                        unsetAtt.execute()
                        self.undoredo.insertOperation(unsetAtt)

        if attribute['applyOnEdge']:
            segments = self.hemodel.getSegments()

            for seg in segments:
                if seg.isSelected():
                    seg.setSelected(False)
                    if attribute in seg.attributes:
                        unsetAtt = UnSetAttribute(seg, attribute)
                        unsetAtt.execute()
                        self.undoredo.insertOperation(unsetAtt)

                        # update mesh
                        if attribute['type'] == 'Number of Subdivisions':
                            face1 = seg.edge.he1.loop.face
                            face2 = seg.edge.he2.loop.face

                            if face1.patch.mesh is not None:
                                self.delMesh(face1)

                            if face2.patch.mesh is not None:
                                self.delMesh(face2)

                        # change the support conditions of the segment points
                        elif attribute['type'] == 'Support Conditions':
                            seg_vertices = seg.edge.incidentVertices()
                            if attribute in seg_vertices[0].point.attributes:
                                unsetAtt = UnSetAttribute(
                                    seg_vertices[0].point, attribute)
                                unsetAtt.execute()
                                self.undoredo.insertOperation(unsetAtt)

                            if attribute in seg_vertices[1].point.attributes:
                                unsetAtt = UnSetAttribute(
                                    seg_vertices[-1].point, attribute)
                                unsetAtt.execute()
                                self.undoredo.insertOperation(unsetAtt)

        if attribute['applyOnFace']:
            patches = self.hemodel.getPatches()
            for patch in patches:
                if patch.isSelected() and not patch.isDeleted:
                    patch.setSelected(False)
                    if attribute in patch.attributes:
                        unsetAtt = UnSetAttribute(patch, attribute)
                        unsetAtt.execute()
                        self.undoredo.insertOperation(unsetAtt)

        self.undoredo.end()
        self.isChanged = True

    def addAttribute(self, _prototype, _name):
        check = self.attManager.createAttributeFromPrototype(_prototype, _name)
        if check:
            self.isChanged = True
        return check

    def saveAtribute(self, _name, _values):
        self.attManager.setAttributeValues(_name, _values)
        self.isChanged = True

    def removeAttribute(self, _name):
        self.undoredo.begin()
        delAttribute = DelAttribute(
            self.attManager, _name, self.hemodel)
        delAttribute.execute()
        self.undoredo.insertOperation(delAttribute)
        self.undoredo.end()
        self.isChanged = True

    def renameAttribute(self, _oldname, _newname):
        attributes = self.attManager.getAttributes()

        for att in attributes:
            if att['name'] == _newname:
                return False

        attribute = self.attManager.getAttributeByName(_oldname)
        attribute['name'] = _newname
        self.isChanged = True
        return True

    def setNumberOfSubdivisions(self, _number, _ratio):
        nsudv_dict = {
            "type": "Number of Subdivisions",
            "symbol": "Nsbdvs",
            "name": "Nsbdvs",
            "properties": {
                "Value": _number,
                "Ratio": _ratio,
                "Color": [0, 0, 0]
            },
            "properties_type": ["int", "float", "color"],
            "applyOnVertex": False,
            "applyOnEdge": True,
            "applyOnFace": False
        }

        self.undoredo.begin()
        segments = self.hemodel.getSegments()

        for seg in segments:
            if seg.isSelected():

                setNumber = SetNumberOfSubdivisions(seg, nsudv_dict)
                setNumber.execute()
                self.undoredo.insertOperation(setNumber)

                setAtt = SetAttribute(seg, nsudv_dict)
                setAtt.execute()
                self.undoredo.insertOperation(setAtt)

                # update mesh
                face1 = seg.edge.he1.loop.face
                face2 = seg.edge.he2.loop.face

                if face1.patch.mesh is not None:
                    self.delMesh(face1)

                if face2.patch.mesh is not None:
                    self.delMesh(face2)

        self.undoredo.end()
        self.isChanged = True

    def getAttributeSymbol(self, _attribute, _scale, _pt=None, _seg=None, _patch=None):
        return AttribSymbols.getSymbol(_attribute, _scale, _pt, _seg, _patch)
