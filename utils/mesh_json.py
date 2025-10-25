import bpy
import os
from ..globals import ADDON_DIRECTORY


def get_active_uv_layer(mesh: bpy.types.Mesh):

    uv_layer = mesh.uv_layers.active
    uv_data = []
    for loop in mesh.loops:
        uv = uv_layer.data[loop.index].uv
        uv_co = [uv[0], uv[1]]
        uv_co = [round(co, 5) for co in uv_co]
        uv_data.append(uv_co)
    
    return uv_data



def get_standard_meshes_dir():
    """Get the standard_meshes directory path"""
    meshes_dir = os.path.join(ADDON_DIRECTORY, "standard_meshes")
    
    # Create directory if it doesn't exist
    if not os.path.exists(meshes_dir):
        os.makedirs(meshes_dir)
    
    return meshes_dir


def mesh_to_dict(
        mesh: bpy.types.Mesh,
        co_3d: bool = True,
        co_uv: bool = True,
        write_vertex_groups: bool = True
):
    """Convert Blender mesh to dictionary with standard Python types"""
    
    # Get vertices
    vertex_count = len(mesh.vertices)

    mesh_data = dict(vertex_count=vertex_count)
    
    if co_3d:
        vertices = []
        for vert in mesh.vertices:
            vert = [vert.co[0], vert.co[1], vert.co[2]]
            vertices.append(vert)
        mesh_data['vertices'] = vertices
    
    # Get edges
    edges = []
    for edge in mesh.edges:
        edges.append([edge.vertices[0], edge.vertices[1]])
    mesh_data['edges'] = edges
    
    # Get polygons (faces)
    polygons = []
    for poly in mesh.polygons:
        polygons.append(list(poly.vertices))
    mesh_data['polygons'] = polygons
    
    # Get UV coordinates if they exist
    if co_uv:
        mesh_data['uv_layer'] = get_active_uv_layer(mesh)
    
    # Get vertex groups if requested
    if write_vertex_groups:
        vertex_groups = {}
        
        # Get the object that owns this mesh to access vertex groups
        # We need to find the object that uses this mesh
        obj = None
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.data == mesh:
                obj = o
                break
        
        if obj and obj.vertex_groups:
            for vg in obj.vertex_groups:
                vg_data = []
                # Iterate through all vertices to find which ones belong to this group
                for vertex_index in range(len(mesh.vertices)):
                    try:
                        # Get the weight of this vertex in this vertex group
                        weight = vg.weight(vertex_index)
                        if weight > 0.0:  # Only include vertices with non-zero weights
                            vg_data.append([vertex_index, weight])
                    except RuntimeError:
                        # Vertex is not in this group
                        continue
                
                if vg_data:  # Only add vertex groups that have vertices
                    vertex_groups[vg.name] = vg_data
        
        mesh_data['vertex_groups'] = vertex_groups

    return mesh_data


def dict_to_mesh(
        mesh_data,
        name: str = 'LoadedMesh',
):
    """Create Blender mesh from dictionary data"""
    
    # Create new mesh
    mesh = bpy.data.meshes.new(name)
    vertex_count = mesh_data['vertex_count']
    # Set vertices, edges, and faces
    if 'vertices' in mesh_data:
        vertices = mesh_data.get("vertices", [])
    else:
        vertices = [(0.0, 0.0, 0.0) for _ in range(vertex_count)]
    edges = mesh_data.get("edges", [])
    polygons = mesh_data.get("polygons", [])
    
    mesh.from_pydata(vertices, edges, polygons)
    
    # Update mesh
    mesh.update()
    
    # Add UV layers if they exist
    uv_data = mesh_data.get("uv_layer", [])
    if uv_data:
        uv_layer = mesh.uv_layers.new(name='UVMap')
        
        for i, loop in enumerate(mesh.loops):
            if i < len(uv_data):
                uv_layer.data[i].uv = uv_data[i]
    
    return mesh
