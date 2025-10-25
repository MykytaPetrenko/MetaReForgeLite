import bpy
import bmesh
from mathutils import Vector
from heapq import heappop, heappush


def select_path(obj, path):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for face_index in path:
        obj.data.polygons[face_index].select = True
    bpy.ops.object.mode_set(mode='EDIT')


class Graph:
    def __init__(self):
        self.nodes = {}
    
    def from_bmesh(self, bm, median_distance=True, corner=False):
        self.nodes = {i: [] for i in range(len(bm.faces))}
        for face in bm.faces:
            checked_faces = set()
            if corner:
                # Connect nodes that share a vertex
                linked_faces = set()
                for vert in face.verts:
                    linked_faces.update([f for f in vert.link_faces if f != face])
                for linked_face in linked_faces:
                    self._add_edge(face, linked_face, median_distance)
            else:
                # Connect nodes that share an edge
                for edge in face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face != face and linked_face not in checked_faces:
                            self._add_edge(face, linked_face, median_distance)
                            checked_faces.add(linked_face)
    
    def _add_edge(self, face, linked_face, median_distance):
        if median_distance:
            distance = (face.calc_center_median() - linked_face.calc_center_median()).length
        else:
            distance = 1
        self.nodes[face.index].append((distance, linked_face.index))
    
    def dijkstra(self, start_index, end_index):
        min_heap = []
        heappush(min_heap, (0, start_index))
        distances = {node: float('inf') for node in self.nodes}
        distances[start_index] = 0
        previous_nodes = {node: None for node in self.nodes}
        while min_heap:
            current_distance, current_node = heappop(min_heap)
            if current_node == end_index:
                path = []
                while previous_nodes[current_node] is not None:
                    path.append(current_node)
                    current_node = previous_nodes[current_node]
                path.append(start_index)
                return path[::-1]
            if current_distance > distances[current_node]:
                continue
            for neighbor_distance, neighbor in self.nodes[current_node]:
                distance = current_distance + neighbor_distance
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heappush(min_heap, (distance, neighbor))
        return []


if __name__ == "__main__":
    # Example usage
    obj = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    graph = Graph()
    graph.from_bmesh(bm, median_distance=True, corner=False)

    selected_faces = [f.index for f in bm.faces if f.select]
    if len(selected_faces) >= 2:
        start_face = selected_faces[0]
        end_face = selected_faces[-1]
        path = graph.dijkstra(start_face, end_face)
        # select_path function needs to be implemented to highlight the path
        select_path(obj, path)

    bm.free()
