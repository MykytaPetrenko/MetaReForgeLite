import bpy
import bmesh
import math
from typing import List
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from .transfer_shape_key import update_base_mesh
from .smooth import calc_smooth, corrective_smooth
from mathutils.kdtree import KDTree


def create_surface_binding(source_obj: bpy.types.Object, target_obj: bpy.types.Object):
    """
    Bind target mesh vertices to the nearest source mesh triangle using BVHTree.

    This function binds each vertex of the target mesh to the closest triangle 
    on the source mesh. It uses the BVHTree structure for efficient nearest 
    neighbor search and calculates the barycentric coordinates of each binding.

    Args:
        source_obj (bpy.types.Object): The source object whose mesh will be used for binding.
        target_obj (bpy.types.Object): The target object whose vertices will be bound to the source mesh.

    Returns:
        list: A list of tuples containing binding data for each target vertex.
              Each tuple consists of:
              - vertex_indices (list of int): Indices of the vertices of the closest triangle in the source mesh.
              - normal (Vector): Normal of the closest triangle face.
              - b_coords (tuple of float): Barycentric coordinates of the target vertex relative to the closest triangle.
              - offset (float): Distance from the target vertex to the triangle plane along the normal.
    """
    source_mesh = source_obj.data
    target_mesh: bpy.types.Mesh = target_obj.data

    if target_mesh.shape_keys and len(target_mesh.shape_keys.key_blocks) >= 1:
        target_verts = target_mesh.shape_keys.key_blocks[0].data
    else:
        target_verts = target_mesh.vertices

    bm = bmesh.new()
    bm.from_mesh(source_mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm, epsilon=0.0001)

    # Barycentric coordinates helper function
    def barycentric_coords(pt, v1, v2, v3):
        v2_v1 = v2 - v1
        v3_v1 = v3 - v1
        pt_v1 = pt - v1
        d00 = v2_v1.dot(v2_v1)
        d01 = v2_v1.dot(v3_v1)
        d11 = v3_v1.dot(v3_v1)
        d20 = pt_v1.dot(v2_v1)
        d21 = pt_v1.dot(v3_v1)
        denom = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w
        return (u, v, w)

    # Bind each target vertex to the closest source triangle
    bind_data = []
    for v in target_verts:
        _, normal, index, _ = bvh.find_nearest(v.co)
        if index is not None:
            face = bm.faces[index]
            verts = [vert.co for vert in face.verts]
            vertex_indices = [vert.index for vert in face.verts]
            if face.normal.length <= 0.5:
                print(face.normal)
            b_coords = barycentric_coords(v.co, *verts)
            offset = (v.co - (verts[0] * b_coords[0] + verts[1] * b_coords[1] + verts[2] * b_coords[2])).dot(normal)
            bind_data.append((vertex_indices, face.normal.copy(), b_coords, offset))
            
        else:
            raise Exception

    bm.free()  # Free the BMesh

    return bind_data


def identify_problem_vertices(
        target_obj: bpy.types.Object,
        bind_data: dict,
        start_thresh: float = math.pi* 0.5,
        full_thresh: float = math.pi
    ) -> None:
    target_bm = bmesh.new()
    target_bm.from_mesh(target_obj.data)
    target_bm.verts.ensure_lookup_table()

    problem_verts = {}
    for vert_index, data in enumerate(bind_data):
        _, normal, _, _ = data
        bm_vert: bmesh.types.BMVert = target_bm.verts[vert_index]
        angles = []
        for edge in bm_vert.link_edges:
            other_vert = edge.other_vert(bm_vert)
            _, other_normal, _, _ = bind_data[other_vert.index]
            angles.append(normal.angle(other_normal))
        
        avg_angle = sum(angles) / len(bm_vert.link_edges)
        r = full_thresh - start_thresh


        if avg_angle > start_thresh:
            val = (avg_angle - start_thresh) / r
            problem_verts[vert_index] = min(1.0, val)
    
    target_bm.free()
    return problem_verts


def calc_surface_deform(
        bind_data,
        new_source_data: list
) -> None:
    """
    TODO check docstring
    Identify problem vertices based on angular deviation of binding normals.

    This function identifies vertices in the target mesh that may have problematic 
    bindings based on the angular deviation of the normals of their associated triangles 
    in the binding data. Vertices with an average normal deviation above a specified 
    threshold are flagged as problem vertices.

    Args:
        target_obj (bpy.types.Object): The target object whose vertices are being analyzed.
        bind_data (dict): Binding data for the target vertices. Each entry is a tuple containing
                          the vertex indices, normal, barycentric coordinates, and offset.

    Returns:
        dict: A dictionary where the keys are vertex indices and the values are the 
              normalized problem severity (ranging from 0.0 to 1.0).
    """
    
    new_co = list()
    # Apply deformations
    for vertices, normal, b_coords, offset in bind_data:

        verts = [new_source_data[idx] for idx in vertices]
        new_pos = verts[0] * b_coords[0] + verts[1] * b_coords[1] + verts[2] * b_coords[2]
        new_pos += normal * offset
        new_co.append(new_pos)
    return new_co


def merge_by_distance(verts, edges, merge_thresh=0.00001, merge_indices=None):
    """
    Merge vertices that are within a specified distance of each other and update the edge list,
    restricting merging to only those vertices specified in merge_indices. All vertices and edges
    are retained in the output, with changes applied only to specified vertices.

    Args:
        verts (list[Vector]): List of vertex coordinates.
        edges (list[tuple]): List of edges as tuples of vertex indices forming an edge.
        merge_thresh (float): Distance threshold for merging vertices.
        merge_indices (set or None): Set of vertex indices that are allowed to merge. If None, all vertices can merge.

    Returns:
        tuple: New list of vertices, updated list of edges, and a dictionary mapping old vertex indices to new indices.
    """
    # Initialize KDTree with potential merge candidates
    kd = KDTree(len(verts))
    if merge_indices is None:
        merge_indices = set(range(len(verts)))
    for i in merge_indices:
        kd.insert(verts[i], i)
    kd.balance()

    # Find all vertices to merge among the specified merge candidates
    to_merge = {}
    new_verts = []
    index_map = {}
    
    for i, vert in enumerate(verts):
        if i in merge_indices and i not in to_merge:
            # Find all vertices within the merge threshold among allowed merge candidates
            close_verts = kd.find_range(vert, merge_thresh)
            new_index = len(new_verts)
            new_verts.append(vert)
            index_map[i] = new_index
            for (_, idx, _) in close_verts:
                if idx in merge_indices:
                    to_merge[idx] = new_index
                    index_map[idx] = new_index
        elif i not in merge_indices:
            # For vertices not allowed to merge, add them as new vertices
            new_index = len(new_verts)
            new_verts.append(vert)
            index_map[i] = new_index 
    # Update edges with new vertex indices, ensuring no invalid edges
    new_edges = set()
    for v1, v2 in edges:
        new_v1 = index_map[v1]
        new_v2 = index_map[v2]
        if new_v1 != new_v2:
            new_edges.add(tuple(sorted([new_v1, new_v2])))

    return new_verts, list(new_edges), index_map


def get_boundary_verts(mesh: bpy.types.Mesh):
    """
    Identify the boundary vertices of a given mesh.

    This function determines the vertices that lie on the boundary of the mesh.
    Boundary vertices are defined as vertices that are part of at least one edge 
    that belongs to only one polygon.

    Args:
        mesh (bpy.types.Mesh): The mesh data from which to identify boundary vertices.

    Returns:
        set: A set of vertex indices representing the boundary vertices.
    """
    # Dictionary to count how many times each edge occurs in polygons
    edge_face_count = {e.key: 0 for e in mesh.edges}

    # Count the number of polygons each edge belongs to
    for poly in mesh.polygons:
        for edge in poly.edge_keys:
            edge_face_count[edge] += 1
    verts = set()
    for key, value in edge_face_count.items():
        if value == 1:
            verts.update(key)
    return verts


def transfer_shapekeys(
        context: bpy.types.Context,
        target_objects: bpy.types.Object,
        source_objects: bpy.types.Object,
        basis_shape_key: str = None,
        shape_keys: List[str] = None,
        corrective_iterations: int = 0,
        corrective_factor: float = 0.5,
        corrective_start_threshols: float = math.pi * 0.5,
        corrective_full_threshould: float = math.pi

    ) -> None:
    """
    Transfer shape keys from source objects to target objects.

    This function transfers shape key deformations from source objects to target objects.
    It can optionally apply corrective smoothing iterations to address any problematic
    vertex bindings.

    Args:
        context (bpy.types.Context): The current context in Blender.
        target_objects (bpy.types.Object): A tuple of target basis and target final objects.
        source_objects (bpy.types.Object): A tuple of source basis and source final objects.
        basis_shape_key (str, optional): The name of the basis shape key to use. Defaults to None.
        shape_keys (List[str], optional): A list of shape key names to transfer. Defaults to None.
        corrective_iterations (int, optional): The number of corrective smoothing iterations to apply. Defaults to 0.
        corrective_factor (float, optional): The factor to control the influence of corrective smoothing. Defaults to 0.5.
        corrective_start_threshols (float, optional): The starting threshold angle (in radians) for identifying problematic vertices. Defaults to π/2.
        corrective_full_threshould (float, optional): The full threshold angle (in radians) for identifying fully problematic vertices. Defaults to π.

    Returns:
        None

    Raises:
        Exception: If the target shape key is not found in the source object.
        ValueError: If there is a mismatch in the number of vertices.
    """
    source_basis, source_final = source_objects
    target_basis, target_final = target_objects
    binding = create_surface_binding(source_basis, target_basis)
    
    if corrective_iterations == 0:
        # Update base mesh
        shape_keys = shape_keys if shape_keys else list()
        shape_keys = ["Basis"] + shape_keys if basis_shape_key else shape_keys
        for sk_index, sk_name in enumerate(shape_keys):
            sk = source_final.data.shape_keys.key_blocks.get(sk_name)
            if not sk:
                continue
                raise Exception("Cannot find target shape key")
            
            new_coordinates = calc_surface_deform(binding, [v.co for v in sk.data])

            if sk_index == 0 and basis_shape_key:
                update_base_mesh(target_final, new_coordinates)
            else:
                if target_final.data.shape_keys is None:
                    target_final.shape_key_add(name="Basis", from_mix=False)
                    target_sk = target_final.shape_key_add(name=sk_name, from_mix=False)
                else:
                    target_sk = target_final.data.shape_keys.key_blocks.get(sk_name)
                    if target_sk is None:
                        target_sk = target_final.shape_key_add(name=sk_name, from_mix=False)
                flattened_coordinates = [value for co in new_coordinates for value in co[:]]
                # Ensure the length matches
                if len(flattened_coordinates) == 3 * len(target_sk.data):
                    target_sk.data.foreach_set("co", flattened_coordinates)
                else:
                    raise ValueError("Mismatch in the number of vertices.")
    else:
        problem_vertices = identify_problem_vertices(
            target_basis,
            binding,
            corrective_start_threshols,
            corrective_full_threshould
        )
        
        # Add vertex group for DEBUG
        group = target_final.vertex_groups.new(name = 'Group')
        for k, v in problem_vertices.items():
            group.add([k], v, 'REPLACE')

        edges = [edge.vertices for edge in target_basis.data.edges]

        # use initial data to calculate which vertices to merge
        basis_verts = [v.co for v in target_basis.data.vertices]
        boundary = get_boundary_verts(target_basis.data)

        # Calculate merge distance
        min_len = 9999.0
        for edge in target_basis.data.edges:
            verts = [target_basis.data.vertices[i].co for i in edge.vertices]
            l = (verts[1] - verts[0]).length
            min_len = min(l, min_len)

        merge_distance = min_len * 0.5

        # Find merged representation of the original mesh
        m_verts_basis, m_edges, m_index_map = merge_by_distance(
            basis_verts,
            edges,
            merge_thresh=merge_distance,
            merge_indices=boundary
        )
        m_problem_vertices = {m_index_map[k]: v for k, v in problem_vertices.items()}

        # Initialize adjacency list for each vertex of the merged mesh
        m_linked_verts = {i: set() for i in range(len(m_verts_basis))}
        for v1, v2 in m_edges:
            m_linked_verts[v1].add(v2)
            m_linked_verts[v2].add(v1)

        
        # Update base mesh
        shape_keys = shape_keys if shape_keys else list()
        shape_keys = ["Basis"] + shape_keys if basis_shape_key else shape_keys
        source_keys = source_final.data.shape_keys
        for sk_index, sk_name in enumerate(shape_keys):
            if sk_index == 0 and basis_shape_key:
                if source_keys and len(source_keys.key_blocks) >= 1: 
                    sk = source_final.data.shape_keys.key_blocks.get(sk_name)
                    if sk is None:
                        continue
                    source_verts = [v.co for v in sk.data]
                else:
                    source_verts = [v.co for v in source_final.data.vertices]
            else:
            
                if source_keys:
                    sk = source_keys.key_blocks.get(sk_name)
                else:
                    sk = None
                
                if sk is None:
                    continue
                    raise Exception("Cannot find target shape key")
                source_verts = [v.co for v in sk.data]
            
            new_coordinates = calc_surface_deform(binding, source_verts)

            m_verts = [0.0 for i in range(len(m_verts_basis))]
            for i, j in m_index_map.items():
                m_verts[j] = new_coordinates[i]

            # Smooth merged mesh representation
            smoothed_co = corrective_smooth(
                m_verts_basis,
                m_verts,
                m_linked_verts,
                m_problem_vertices,
                iterations=corrective_iterations,
                influence=corrective_factor
            )
            
            # Map smoothed vertex coordinates back to the original mesh
            temp = []
            for i in range(len(new_coordinates)):
                temp.append(smoothed_co[m_index_map[i]])

            if sk_index == 0 and basis_shape_key:
                update_base_mesh(target_final, temp)
            else:
                if target_final.data.shape_keys is None:
                    target_final.shape_key_add(name="Basis", from_mix=False)
                    target_sk = target_final.shape_key_add(name=sk_name, from_mix=False)
                else:
                    target_sk = target_final.data.shape_keys.key_blocks.get(sk_name)
                    if target_sk is None:
                        target_sk = target_final.shape_key_add(name=sk_name, from_mix=False)
                flattened_coordinates = [value for co in temp for value in co[:]]
                # Ensure the length matches
                if len(flattened_coordinates) == 3 * len(target_sk.data):
                    target_sk.data.foreach_set("co", flattened_coordinates)
                else:
                    raise ValueError("Mismatch in the number of vertices.")
