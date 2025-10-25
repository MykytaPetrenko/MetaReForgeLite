import bpy
import math
import time
from typing import List, Set, Dict
from mathutils import Vector
from mathutils.kdtree import KDTree
from .utils import transpose, dot
from ..utils.mesh_json import get_active_uv_layer


EPS = 1e-20


class TransferInput:
    """
    Represents input data for coordinate transfer
    """
    def __init__(
            self,
            source_co: Vector,
            weight: float,
            id: str = None,
            loop_index: int = None
    ) -> None:
        self.co = source_co.copy()
        self.id = id
        self.loop_index = loop_index
        self.weight = weight

    @property
    def x(self) -> float:
        return self.co[0]

    @property
    def y(self) -> float:
        return self.co[1]

    def __eq__(self, other) -> bool:
        if self.co == other.co and self.id == other.id:
            return True
        return False


class TransferTriangle:
    def __init__(self, target_verts, source_verts, id: str = None) -> None:
        self.id = id

        self.is_valid = True

        # Reformat data for further calculations
        self.source_verts = source_verts
        self.target_verts = target_verts
        self.target_verts_t = transpose(self.target_verts)

        # Define rectangle sides and area
        self.ab_source = (self.b_source - self.a_source).length
        self.ac_source = (self.c_source - self.a_source).length
        self.bc_source = (self.c_source - self.b_source).length
        self.source_triangle_area = self.get_source_triangle_area()

        if self.source_triangle_area <= 1e-10:
            self.is_valid = False

        # Compute some variables that will be used to compute the barycentric coordinates of the point
        # multiple times
        self.v0 = [self.source_verts[1][i] - self.source_verts[0][i] for i in range(len(self.source_verts[0]))]
        self.v1 = [self.source_verts[2][i] - self.source_verts[0][i] for i in range(len(self.source_verts[0]))]
        self.d00 = dot(self.v0, self.v0)
        self.d01 = dot(self.v0, self.v1)
        self.d11 = dot(self.v1, self.v1)
        self.denominator = self.d00 * self.d11 - self.d01 * self.d01
        
        if self.denominator < EPS:
            self.is_valid = False

    @property
    def a_target(self) -> Vector:
        return self.target_verts[0]
    
    @property
    def b_target(self) -> Vector:
        return self.target_verts[1]
    
    @property
    def c_target(self) -> Vector:
        return self.target_verts[2]
    

    @property
    def a_source(self) -> Vector:
        return self.source_verts[0]
    
    @property
    def b_source(self) -> Vector:
        return self.source_verts[1]
    
    @property
    def c_source(self) -> Vector:
        return self.source_verts[2]
    
    def get_source_triangle_area(self) -> float:
        """
        Determines the area of the triangle ABC of the source mesh.
        """
        semi_abc = (self.ab_source + self.bc_source + self.ac_source) / 2
        area_sq = semi_abc * (semi_abc - self.ab_source) * (semi_abc - self.bc_source) * (semi_abc - self.ac_source)
        area = math.sqrt(max(0.0, area_sq))
        return area
    
    def source_outside_factor(self, source_co: Vector) -> float:
        """
        :param source_co: The point in source coordinates to check.
        """
        # Find distances from the input uv_point to the vertices
        pa = (source_co - self.a_source).length
        pb = (source_co - self.b_source).length
        pc = (source_co - self.c_source).length

        # Semi perimeters of triangles PAB, PAC, PBC on the uv plane
        semi_pab = (pa + pb + self.ab_source) / 2.0
        semi_pac = (pa + pc + self.ac_source) / 2.0
        semi_pbc = (pb + pc + self.bc_source) / 2.0

        # Squared areas
        area_pab_sq = semi_pab * (semi_pab - pa) * (semi_pab - pb) * (semi_pab - self.ab_source)
        area_pac_sq = semi_pac * (semi_pac - pa) * (semi_pac - pc) * (semi_pac - self.ac_source)
        area_pbc_sq = semi_pbc * (semi_pbc - pb) * (semi_pbc - pc) * (semi_pbc - self.bc_source)
        
        # Areas of the triangles PAB, PAC and PBC on the uv plane
        try:
            area_pab = math.sqrt(area_pab_sq)
            area_pac = math.sqrt(area_pac_sq)
            area_pbc = math.sqrt(area_pbc_sq)
        except ValueError:
            # Sometimes, due to computational errors, the expression under the square root
            # takes on a very small but negative value. Therefore, we limit this.
            area_pab_sq = max(area_pab_sq, 0.0)
            area_pac_sq = max(area_pac_sq, 0.0)
            area_pbc_sq = max(area_pbc_sq, 0.0)
            area_pab = math.sqrt(area_pab_sq)
            area_pac = math.sqrt(area_pac_sq)
            area_pbc = math.sqrt(area_pbc_sq)
        area = area_pab + area_pbc + area_pac
        return (area - self.source_triangle_area) / self.source_triangle_area

    
    def is_belongs(self, source_co: Vector, tolerance: float = 1e-2) -> bool:
        """
        Determines if the given source point lies inside the source triangle.
        The method checks if the source point is within the triangle formed by vertices a_source, b_source, and c_source.
        It uses the area of the triangle and the areas of the sub-triangles formed by the given source point
        with the vertices. The method returns False for degenerate triangles.

        :param source_co: The source coordinates to check.
        :param tolerance: The allowable percentage difference between the computed areas to consider the point
        as inside the triangle. Defaults to 1e-2.

        :return: True if the source point is inside the triangle, False otherwise. Also returns False if the triangle is degenerate.
        """
        factor = self.source_outside_factor(source_co)
        if factor is None:
            return False
        else:
            return abs(factor) < tolerance
    
    def get_matching_target_vertex(self, source_co: Vector, tolerance=1e-8):
        """
        Returns the corresponding target vertex if source_co matches a triangle vertex within tolerance.

        :param source_co: Source coordinates to check.
        :param tolerance: Distance tolerance for vertex matching. Defaults to 1e-8.
        :return: Matching target vertex or None if no match found.
        """
        if (source_co - self.a_source).length <= tolerance:
            return self.a_target
        if (source_co - self.b_source).length <= tolerance:
            return self.b_target
        if (source_co - self.c_source).length <= tolerance:
            return self.c_target
        return None
    
    def transfer_coordinates(self, source_co: Vector) -> Vector:
        """
        Interpolates target coordinates from source coordinates using barycentric interpolation.

        :param source_co: Source coordinates to interpolate from.
        :return: Interpolated target coordinates.
        """
        # Compute the barycentric coordinates of the point
        v2 = [source_co[i] - self.source_verts[0][i] for i in range(len(self.source_verts[0]))]
        d20, d21 = dot(v2, self.v0), dot(v2, self.v1)
        v = (self.d11 * d20 - self.d01 * d21) / self.denominator
        w = (self.d00 * d21 - self.d01 * d20) / self.denominator
        u = 1.0 - v - w
        bc = [u, v, w]

        # Interpolate the 3D coordinates of the point
        target_co = [dot(bc, self.target_verts_t[i]) for i in range(len(self.target_verts[0]))]

        return Vector(target_co)


class TransferTrianglesCollection:
    """
    A collection of TransferTriangles with optimized lookup using KD-tree for fast spatial queries.
    """
    def __init__(self, triangles: List[TransferTriangle]) -> None:
        """
        Initializes the collection with KD-tree for efficient triangle lookup.

        :param triangles: List of TransferTriangles to add to the collection.
        """
        self.triangles = dict()
        self.kd = KDTree(size=len(triangles) * 3)
        self.map = dict()
        i = 0
        invalid_triangle_count = 0
        for tri_index, tri in enumerate(triangles):
            # Skip invalid triangles
            if not tri.is_valid:
                invalid_triangle_count += 1
                continue
            for target_vert, source_vert in zip(tri.target_verts, tri.source_verts):
                self.kd.insert(source_vert, i)
                self.triangles[tri_index] = tri
                self.map[i] = tri_index
                i += 1
        if invalid_triangle_count != 0:
            print(f'Invalid triangles detected and ignored: {invalid_triangle_count} from {len(triangles)}')
        self.kd.balance()

    def transfer_coordinates_using_closest_triangle(self, source_co: Vector) -> Vector:
        """
        Finds the best triangle match and returns interpolated target coordinates.

        :param source_co: Source coordinates to find triangle for.
        :return: Interpolated target coordinates or None if no triangles found.
        """
        best_matches = self.kd.find_n(source_co, 10)
        # Make sure they are sorted by distance

        triangles = []
        for _, index, distance in best_matches:
            tri_index = self.map[index]
            tri: TransferTriangle = self.triangles[tri_index]
            outside_factor = tri.source_outside_factor(source_co)

            if outside_factor < 1e-8:
                interpolated_3d_co = tri.transfer_coordinates(source_co)
                return interpolated_3d_co
            
            triangles.append((outside_factor, tri))

        # if there are no triangle that fit threshold we need to choose the closest.
        triangles.sort(key=lambda t: t[0])  # Sort in-place by outside_factor
        if triangles:
            best_triangle: TransferTriangle = triangles[0][1]  # Return the TransferTriangle with the smallest factor
            interpolated_co = best_triangle.transfer_coordinates(source_co)
            return interpolated_co
        return None
    

def get_group_vertices(obj: bpy.types.Object, vertex_group: str) -> Set[int]:
    """
    Retrieves the indices of vertices from the given Blender object that have non-zero weights
    in the specified vertex group.
    Note:
    - The function uses a threshold of 0.01 for the vertex weight to be considered non-zero.
    - Vertices not part of the specified group will be skipped without error.

    :param obj: The target Blender object.
    :param vertex_group: The name of the vertex group to inspect.
    :returns: A set of vertex indices that have non-zero weights in the specified vertex group.
    """
    vg_vertices = set()
    vg = obj.vertex_groups[vertex_group]
    for vertex in obj.data.vertices:
        try:
            weight = vg.weight(vertex.index)
            if weight > 0.01:  # Check for non-zero weight with some threshold
                vg_vertices.add(vertex.index)
        except RuntimeError:  # weight() will throw an error if vertex is not part of the group
            continue
    return vg_vertices


def uv_transfer_initialize_target_vertices(obj: bpy.types.Object, mode: int = 0) -> Dict[int, List[TransferInput]]:
    print(f"Getting UV vertices of {obj.name}...")
    t1 = time.time()
    uv_layer = obj.data.uv_layers.active.data

    # Init all mesh vertices
    vertices = {vert.index: list() for vert in obj.data.vertices}

    if mode == 0:
        # Add all UV variants for each mesh vertex
        for face in obj.data.polygons:
            rng = range(face.loop_start, face.loop_start + face.loop_total)

            # Convert UV to 3D as KD tree does not works with 2D
            uv_coordinates = [uv_layer[j].uv.to_3d() for j in rng]
            vert_indices = [obj.data.loops[j].vertex_index for j in rng]

            for i, uv in zip(vert_indices, uv_coordinates):
                loop_vertices = vertices[i]
                new_input_element = TransferInput(uv, 1.0)
                if loop_vertices:
                    for other_input_element in loop_vertices:
                        if new_input_element == other_input_element:
                            other_input_element.weight += 1.0
                            break
                    else:
                        vertices[i].append(new_input_element)
                else:            
                    vertices[i].append(new_input_element)
    elif mode == 1:
        for vert in obj.data.vertices:
            vertices[vert.index].append(TransferInput(vert.co, 1.0))
        
    t2 = time.time()
    print(f"Finished. Time elapsed: {t2 - t1} seconds")
    return vertices

def init_triangles(vertices, polygons, uv_layer, mode: int = 0):
    triangles = list()

    def append_tringle(target_verts, source_verts):
        # Append triangle skipping invalid ones
        try:
            tri = TransferTriangle(target_verts, source_verts)
            triangles.append(tri)
        except:
            pass

    t1 = time.time()
    # Constructs custom triangle objects for each triangle and quad face of the source object
    loop_start = 0
    for _, vert_indices in enumerate(polygons):
        n = len(vert_indices)
        r = range(loop_start, loop_start + n)
        loop_start += n
        uv = [Vector(uv_layer[j]).to_3d() for j in r]
        co = [Vector(vertices[j]) for j in vert_indices]

        if mode == 0:
            target_co = co
            source_co = uv
        elif mode == 1:
            target_co = uv
            source_co = co

        if n == 4:
            append_tringle(
                [target_co[0], target_co[1], target_co[2]],
                [source_co[0], source_co[1], source_co[2]]
            )
            append_tringle(
                [target_co[0], target_co[3], target_co[2]],
                [source_co[0], source_co[3], source_co[2]]
            )
        elif n == 3:
            append_tringle(
                [target_co[0], target_co[1], target_co[2]],
                [source_co[0], source_co[1], source_co[2]]
            )
        else:
            raise Exception("Faces with a number of vertices more than 4 are not accepted.")
    
    t2 = time.time()
    print(f"Finished. Time elapsed: {t2 - t1} seconds")
    return triangles


def uv_tranfer_initialize_triangles(obj: bpy.types.Object, mode: int = 0) -> List[TransferTriangle]:
    print("Initializing source transfer triangles...")

    vertices = [v.co for v in obj.data.vertices]
    polygons = [p.vertices for p in obj.data.polygons]
    edges = [e.vertices for e in obj.data.edges]
    uv_layer = get_active_uv_layer(obj.data)

    triangles = init_triangles(vertices, polygons, uv_layer, mode)
    return triangles 
