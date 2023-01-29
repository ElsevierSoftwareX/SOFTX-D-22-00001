from hetool.geometry.point import Point
from hetool.geometry.segments.line import Line
from hetool.geometry.segments.polyline import Polyline
from hetool.geometry.patch import Patch
from hetool.he.topologicalEntities.vertex import Vertex
from hetool.he.topologicalEntities.face import Face
from hetool.he.topologicalEntities.edge import Edge
from hetool.he.topologicalEntities.loop import Loop
from hetool.he.topologicalEntities.halfedge import HalfEdge
from hetool.he.topologicalEntities.shell import Shell
import json


class HeFile():

    @staticmethod
    def saveFile(_shell, _attributes, _filename):

        # get topological entities
        vertices = _shell.vertices
        edges = _shell.edges
        faces = _shell.faces

        # create/ open a file
        split_name = _filename.split('.')
        if split_name[-1] == 'json':
            file = open(f"{_filename}", "w")
        else:
            file = open(f"{_filename}.json", "w")

        # saves the vertices
        vertices_list = []
        for vertex in vertices:

            attributes = vertex.point.attributes
            att_list = []
            for att in attributes:
                att_list.append(att['name'])

            attributes_dict = {
                "att_names": att_list
            }

            if vertex.prev is None:
                prev_ID = None
            else:
                prev_ID = vertex.prev.ID

            if vertex.next is None:
                next_ID = None
            else:
                next_ID = vertex.next.ID

            vertex_dict = {
                'type': 'VERTEX',
                'ID': vertex.ID,
                'prev_ID': prev_ID,
                'next_ID': next_ID,
                'he_ID': vertex.he.ID,
                'point': (vertex.point.getX(), vertex.point.getY()),
                'attributes': attributes_dict
            }
            vertices_list.append(vertex_dict)

        # saves the edges
        edges_list = []
        for edge in edges:

            edge_pts = edge.segment.getPoints()
            pts = []
            for pt in edge_pts:
                pts.append([pt.getX(), pt.getY()])

            attributes = edge.segment.attributes.copy()
            if edge.segment.nsudv is not None:
                attributes.remove(edge.segment.nsudv)
            att_list = []
            for att in attributes:
                att_list.append(att['name'])

            attributes_dict = {
                "nsudv": edge.segment.nsudv,
                "att_names": att_list
            }

            if edge.prev is None:
                prev_ID = None
            else:
                prev_ID = edge.prev.ID

            if edge.next is None:
                next_ID = None
            else:
                next_ID = edge.next.ID

            edge_dict = {
                'type': 'EDGE',
                'ID': edge.ID,
                'prev_ID': prev_ID,
                'next_ID': next_ID,
                'he1_ID': edge.he1.ID,
                'he2_ID': edge.he2.ID,
                'segment_type': f'{edge.segment.getType()}',
                'points': pts,
                'attributes': attributes_dict
            }

            edges_list.append(edge_dict)

        faces_list = []
        for face in faces:

            if face.loop.next is None:
                next_ID = None
            else:
                next_ID = face.loop.next.ID

            # saves the external loop
            he = face.loop.he
            he_begin = he

            if he is None:
                he_list = None
            else:
                he_list = []
                while True:

                    he_dict = {
                        'type': 'HALF-EDGE',
                        'ID': he.ID,
                        'prev_ID': he.prev.ID,
                        'next_ID': he.next.ID,
                        'vertex_ID': he.vertex.ID,
                        'edge_ID': he.edge.ID,
                        'loop_ID': he.loop.ID
                    }

                    he_list.append(he_dict)
                    he = he.next

                    if he == he_begin:
                        break

            loop_dict = {
                'type': 'LOOP',
                'ID': face.loop.ID,
                'prev_ID': None,
                'next_ID': next_ID,
                'face_ID': face.ID,
                'he_loop': he_list,
                'isClosed': face.loop.isClosed

            }

            # saves the internal loops
            intLoops = []
            intLoop = face.loop.next
            while intLoop is not None:

                he = intLoop.he
                he_begin = he

                he_list = []
                while True:

                    if he.edge is None:
                        edge_ID = None
                    else:
                        edge_ID = he.edge.ID

                    he_dict = {
                        'type': 'HALF-EDGE',
                        'ID': he.ID,
                        'prev_ID': he.prev.ID,
                        'next_ID': he.next.ID,
                        'vertex_ID': he.vertex.ID,
                        'edge_ID': edge_ID,
                        'loop_ID': he.loop.ID
                    }

                    he_list.append(he_dict)
                    he = he.next

                    if he == he_begin:
                        break

                if intLoop.next is None:
                    next_ID = None
                else:
                    next_ID = intLoop.next.ID

                intLoop_dict = {
                    'type': 'LOOP',
                    'ID': intLoop.ID,
                    'prev_ID': intLoop.prev.ID,
                    'next_ID': next_ID,
                    'face_ID': face.ID,
                    'he_loop': he_list,
                    'isClosed': intLoop.isClosed
                }

                intLoops.append(intLoop_dict)
                intLoop = intLoop.next

            attributes = face.patch.attributes.copy()
            if face.patch.mesh is not None:
                mesh_dict = face.patch.mesh.mesh_dict
                attributes.remove(mesh_dict)
            else:
                mesh_dict = None

            att_list = []
            for att in attributes:
                att_list.append(att['name'])

            attributes_dict = {
                'isDeleted': face.patch.isDeleted,
                'mesh': mesh_dict,
                "att_names": att_list
            }

            if face.prev is None:
                prev_ID = None
            else:
                prev_ID = face.prev.ID

            if face.next is None:
                next_ID = None
            else:
                next_ID = face.next.ID

            face_dict = {
                'type': 'FACE',
                'ID': face.ID,
                'prev_ID': prev_ID,
                'next_ID': next_ID,
                'loop': loop_dict,
                'intLoops': intLoops,
                'attributes': attributes_dict
            }

            faces_list.append(face_dict)

        shell = {
            'type': 'SHELL',
            'vertices': vertices_list,
            'edges': edges_list,
            'faces': faces_list,
            'attributes_list': _attributes
        }

        json.dump(shell, file, indent=4)
        file.close()

    @ staticmethod
    def loadFile(_file):
        with open(_file, 'r') as file:
            input = json.load(file)

        vertices = input['vertices']
        edges = input['edges']
        faces = input['faces']
        attributes = input['attributes_list']

        # creates the shell
        shell = Shell()

        # creates the edges
        for edge_dict in edges:
            edge = Edge()
            edge.ID = edge_dict['ID']

            # creates a key for the edge
            edge_dict['edge'] = edge

            # set edge segment
            edge_pts = edge_dict['points']
            pts = []
            for pt in edge_pts:
                pts.append(Point(pt[0], pt[1]))

            type = edge_dict['segment_type']

            if type == 'LINE':
                segment = Line(pts[0], pts[1])
            elif type == 'POLYLINE':
                segment = Polyline(pts)

            edge.segment = segment

            # set segment attributes
            att_names = edge_dict['attributes']['att_names']
            for att_name in att_names:
                for attribute in attributes:
                    if att_name == attribute['name']:
                        segment.attributes.append(attribute)

            if edge_dict['attributes']['nsudv'] is not None:
                segment.setNumberOfSubdivisions(
                    edge_dict['attributes']['nsudv'])
                segment.attributes.append(edge_dict['attributes']['nsudv'])

        # creates the vertices
        for vertex_dict in vertices:
            vertex = Vertex()
            vertex.ID = vertex_dict['ID']

            # creates a key for the vertex
            vertex_dict['vertex'] = vertex

            # set the point
            pt = vertex_dict['point']
            vertex.point = Point(pt[0], pt[1])

            # set point attributes
            att_names = vertex_dict['attributes']['att_names']
            for att_name in att_names:
                for attribute in attributes:
                    if att_name == attribute['name']:
                        vertex.point.attributes.append(attribute)

        # creates the faces
        for face_dict in faces:
            face = Face(shell)
            face.patch = Patch()
            face.ID = face_dict['ID']

            # set patch attributes
            att_names = face_dict['attributes']['att_names']
            for att_name in att_names:
                for attribute in attributes:
                    if att_name == attribute['name']:
                        face.patch.attributes.append(attribute)

            # creates a key for the face
            face_dict['face'] = face

            # creates the outer loop
            loop_dict = face_dict['loop']
            loop = Loop(face)
            loop.ID = loop_dict['ID']
            loop.isClosed = loop_dict['isClosed']

            # creates the half-edges
            he_dicts = loop_dict['he_loop']
            if he_dicts is not None:
                for he_dict in he_dicts:
                    he = HalfEdge()
                    he.ID = he_dict['ID']
                    he.loop = loop

                    # creates a key for the he
                    he_dict['he'] = he

                    # set he.vertex and vertex.he
                    for vertex_dict in vertices:
                        if he_dict['vertex_ID'] == vertex_dict['ID']:
                            he.vertex = vertex_dict['vertex']

                            if vertex_dict['he_ID'] == he.ID:
                                he.vertex.he = he

                            break

                    # set he.edge and edge.he(1 or 2)
                    for edge_dict in edges:
                        if he_dict['edge_ID'] == edge_dict['ID']:
                            he.edge = edge_dict['edge']

                            if edge_dict['he1_ID'] == he.ID:
                                he.edge.he1 = he
                                he.edge.segment.setInitPoint(he.vertex.point)
                            else:
                                he.edge.he2 = he
                                he.edge.segment.setEndPoint(he.vertex.point)

                            break

                # set he.prev/next
                he_dicts[0]['he'].prev = he_dicts[-1]['he']
                he_dicts[-1]['he'].next = he_dicts[0]['he']
                for i in range(1, len(he_dicts)):
                    he_dicts[i]['he'].prev = he_dicts[i-1]['he']
                    he_dicts[i-1]['he'].next = he_dicts[i]['he']

                # set loop.he
                loop.he = he_dicts[0]['he']

            # creates internal loops
            intLoops_list = []
            intLoops_dict = face_dict['intLoops']
            for intLoop_dict in intLoops_dict:
                intLoop = Loop()
                intLoop.face = face
                intLoop.ID = intLoop_dict['ID']
                intLoop.isClosed = intLoop_dict['isClosed']
                intLoops_list.append(intLoop)

                # creates the half-edges
                he_dicts = intLoop_dict['he_loop']
                for he_dict in he_dicts:
                    he = HalfEdge()
                    he.ID = he_dict['ID']
                    he.loop = intLoop

                    # creates a key for the he
                    he_dict['he'] = he

                    # set he.vertex and vertex.he
                    for vertex_dict in vertices:
                        if he_dict['vertex_ID'] == vertex_dict['ID']:
                            he.vertex = vertex_dict['vertex']

                            if vertex_dict['he_ID'] == he.ID:
                                he.vertex.he = he

                            break

                    # set he.edge and edge.he(1 or 2)
                    for edge_dict in edges:
                        if he_dict['edge_ID'] == edge_dict['ID']:
                            he.edge = edge_dict['edge']

                            if edge_dict['he1_ID'] == he.ID:
                                he.edge.he1 = he
                                he.edge.segment.setInitPoint(he.vertex.point)
                            else:
                                he.edge.he2 = he
                                he.edge.segment.setEndPoint(he.vertex.point)

                # set he.prev/next
                he_dicts[0]['he'].prev = he_dicts[-1]['he']
                he_dicts[-1]['he'].next = he_dicts[0]['he']
                for i in range(1, len(he_dicts)):
                    he_dicts[i]['he'].prev = he_dicts[i-1]['he']
                    he_dicts[i-1]['he'].next = he_dicts[i]['he']

                # set loop.he
                intLoop.he = he_dicts[0]['he']

            # set loop.prev/next
            if len(intLoops_list) > 0:
                intLoops_list[0].prev = loop
                loop.next = intLoops_list[0]

            for i in range(1, len(intLoops_list)):
                intLoops_list[i].prev = intLoops_list[i-1]
                intLoops_list[i-1].next = intLoops_list[i]

            # set attributes
            attributes_dict = face_dict['attributes']
            face.patch.isDeleted = attributes_dict['isDeleted']

        # set shell face
        shell.face = faces[0]['face']

        # set face prev/next
        for i in range(1, len(faces)):
            faces[i]['face'].prev = faces[i-1]['face']
            faces[i-1]['face'].next = faces[i]['face']

        return vertices, edges, faces, attributes
