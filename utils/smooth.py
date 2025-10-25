import bpy
from mathutils import Vector


def calc_smooth(verts, linked_verts, vertex_indices, iterations=10, influence=0.5):
    """
    Perform smoothing on specified vertices of a mesh.

    Args:
        verts (list[Vector]): List of vertex coordinates.
        edges (list[tuple]): List of tuples each representing a pair of vertex indices forming an edge.
        vertex_indices (list[int]): List of vertex indices to be smoothed.
        iterations (int, optional): Number of smoothing iterations. Default is 10.
        influence (float, optional): Influence of smoothing each iteration (0.0 to 1.0). Default is 0.5.

    Returns:
        dict: A dictionary with vertex indices as keys and their new positions as values.
    """

    # Iterate to smooth the vertex positions
    for _ in range(iterations):
        new_positions = {}
        for vert_index in vertex_indices:
            if linked_verts[vert_index]:
                avg_pos = Vector((0, 0, 0))
                for other_index in linked_verts[vert_index]:
                    avg_pos += verts[other_index]
                avg_pos /= len(linked_verts[vert_index])
                new_positions[vert_index] = verts[vert_index].lerp(avg_pos, influence)
        
        # Apply new positions to the original vertices
        for index, new_pos in new_positions.items():
            verts[index] = new_pos

    return new_positions


def corrective_smooth(
        basis_verts,
        current_verts,
        linked_verts,
        vertex_group,
        iterations=10,
        influence=0.5
    ):
    """
    Performs corrective smoothing on specified vertices, trying to preserve the original form.
    
    Args:
        basis_verts (list[Vector]): Original coordinates of the vertices (base form).
        current_verts (list[Vector]): Current coordinates of the vertices to be smoothed.
        linked_verts (dict): Adjacency list for each vertex.
        vertex_indices (list[int]): Indices of vertices that will be smoothed.
        iterations (int): Number of smoothing iterations.
        influence (float): Influence of the smoothing each iteration.

    Returns:
        list[Vector]: New positions of the vertices after smoothing.
    """
    smoothed_verts = current_verts[:]
    
    for _ in range(iterations):
        temp_verts = smoothed_verts[:]
        
        for vert_index, vert_influence  in vertex_group.items():
            if vert_index not in linked_verts:
                continue
            
            average_pos = Vector((0, 0, 0))
            count = 0
            
            for neighbor in linked_verts[vert_index]:
                edge_vec = basis_verts[vert_index] - basis_verts[neighbor]
                target_pos = smoothed_verts[neighbor] + edge_vec
                average_pos += target_pos
                count += 1
            
            if count > 0:
                average_pos /= count
                delta = influence * vert_influence * (average_pos - smoothed_verts[vert_index])
                temp_verts[vert_index] = smoothed_verts[vert_index] + delta
        
        smoothed_verts = temp_verts
    
    return smoothed_verts


if __name__ == "__main__":
    sk_name = "Target"
    obj = bpy.context.object
    problem_verts = [205, 164]  # Indices of vertices to smooth
    original_verts = [v.co.copy() for v in obj.data.vertices]  # Basis vertices
    
    
    problem_verts = [i for i in range(len(original_verts))]
    sk_verts = [obj.data.shape_keys.key_blocks[sk_name].data[v.index].co.copy() for v in obj.data.vertices]  # Shape key vertices
    edges = [edge.vertices[:] for edge in obj.data.edges]
    
    linked_verts = {i: set() for i in range(len(original_verts))}
    for v1, v2 in edges:
        linked_verts[v1].add(v2)
        linked_verts[v2].add(v1)
    
    new_co = corrective_smooth(original_verts, sk_verts, linked_verts, problem_verts, iterations=20)
    # new_co = calc_smooth(sk_verts, linked_verts, problem_verts, iterations=20)
    for i, v in enumerate(obj.data.shape_keys.key_blocks[sk_name].data):
        v.co = new_co[i]
        
    obj.data.update()  # Ensure the mesh updates in the viewport
    