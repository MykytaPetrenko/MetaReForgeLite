import bpy
import mathutils


def create_octahedron(name="Octahedron", location=(0, 0, 0), size=1):
    # Define vertices and faces for an octahedron
    vertices = [
        (0, 0, size),  # Top vertex
        (-size, 0, 0),  # Left vertex
        (size, 0, 0),  # Right vertex
        (0, -size, 0),  # Front vertex
        (0, size, 0),  # Back vertex
        (0, 0, -size)  # Bottom vertex
    ]
    
    faces = [
        (0, 1, 3),  # Top left front
        (0, 3, 2),  # Top front right
        (0, 2, 4),  # Top right back
        (0, 4, 1),  # Top back left
        (5, 3, 1),  # Bottom front left
        (5, 2, 3),  # Bottom front right
        (5, 4, 2),  # Bottom back right
        (5, 1, 4)   # Bottom back left
    ]
    
    # Create a new mesh and object
    mesh = bpy.data.meshes.new(name + "Mesh")
    obj = bpy.data.objects.new(name, mesh)
    
    # Add the object to the scene
    bpy.context.collection.objects.link(obj)
    
    # Create the mesh from the vertices and faces
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Set the object's location
    obj.location = location
    return obj


def create_box(
        context: bpy.types.Context,
        center: mathutils.Vector,
        size: mathutils.Vector
) -> bpy.types.Object:
    # Calculate half sizes
    half_size = size * 0.5
    
    # Define vertices based on the center and size
    vertices = [
        (center.x - half_size.x, center.y - half_size.y, center.z - half_size.z),  # Bottom-left-front
        (center.x + half_size.x, center.y - half_size.y, center.z - half_size.z),  # Bottom-right-front
        (center.x + half_size.x, center.y + half_size.y, center.z - half_size.z),  # Bottom-right-back
        (center.x - half_size.x, center.y + half_size.y, center.z - half_size.z),  # Bottom-left-back
        (center.x - half_size.x, center.y - half_size.y, center.z + half_size.z),  # Top-left-front
        (center.x + half_size.x, center.y - half_size.y, center.z + half_size.z),  # Top-right-front
        (center.x + half_size.x, center.y + half_size.y, center.z + half_size.z),  # Top-right-back
        (center.x - half_size.x, center.y + half_size.y, center.z + half_size.z),  # Top-left-back
    ]
    
    # Define faces using the vertices
    faces = [
        (0, 1, 2, 3),  # Bottom face
        (4, 5, 6, 7),  # Top face
        (0, 4, 7, 3),  # Left face
        (1, 5, 6, 2),  # Right face
        (3, 2, 6, 7),  # Back face
        (0, 1, 5, 4),  # Front face
    ]
    
    # Create a new mesh and object
    mesh = bpy.data.meshes.new("BoxMesh")
    obj = bpy.data.objects.new("Box", mesh)
    
    # Link the object to the current scene collection
    bpy.context.collection.objects.link(obj)
    
    # Create the mesh data from vertices and faces
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    if context.active_object:
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    # select al faces
    bpy.ops.mesh.select_all(action='SELECT')
    # recalculate outside normals 
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return obj
