import bpy
import mathutils
from .collection import get_collection
from typing import List

_mem_active_object = None
_mem_selected_objects = None
_mem_mode = None



def find_minimal_edge_length(obj):
    if obj is None:
        print(f"Object '{object.name}' not found.")
        return None

    if obj.type != 'MESH':
        print(f"Object '{object.name}' is not a mesh.")
        return None

    mesh = obj.data()

    # Initialize minimum length as a very large number
    min_length = float('inf')

    # Iterate over edges
    for edge in mesh.edges:
        v1 = mesh.vertices[edge.vertices[0]].co
        v2 = mesh.vertices[edge.vertices[1]].co
        edge_length = (v2 - v1).length
        if edge_length < min_length:
            min_length = edge_length

    return min_length


def calc_adaptive_merge_distance(obj, factor=0.99):
    if obj is None:
        print(f"Object '{obj.name}' not found.")
        return None

    if obj.type != 'MESH':
        print(f"Object '{obj.name}' is not a mesh.")
        return None

    mesh = obj.data

    # Initialize minimum distance as a very large number
    min_distance = float('inf')

    # Iterate over polygons
    for poly in mesh.polygons:
        # Collect all vertex indices for the current polygon
        vertex_indices = poly.vertices
        num_vertices = len(vertex_indices)

        # Compare each pair of vertices in the polygon
        for i in range(num_vertices):
            for j in range(i + 1, num_vertices):  # Avoid duplicate comparisons
                v1 = mesh.vertices[vertex_indices[i]].co
                v2 = mesh.vertices[vertex_indices[j]].co
                distance = (v2 - v1).length
                if distance < min_distance:
                    min_distance = distance

    return min_distance * factor


def ensure_object_mode_and_deselect(context: bpy.types.Context):
    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')


def duplicate_object(
        context: bpy.types.Context,
        obj: bpy.types.Object,
        dup_name: str = None,
        collection_name: str = None) -> bpy.types.Object:
    """
    Duplicates a given object in Blender, including its data. The duplicated object 
    can be renamed and added to a specified collection. Blender must be in OBJECT mode 
    for this operation to succeed.

    Args:
        context (bpy.types.Context): The context in which the duplication is done.
        obj (bpy.types.Object): The object to be duplicated.
        dup_name (str, optional): The new name for the duplicated object, defaults to None.
        collection_name (str, optional): The name of the collection to add the duplicated
                                         object to, defaults to None.
    
    Returns:
        bpy.types.Object: The duplicated object.

    Raises:
        RuntimeError: If Blender is not in OBJECT mode when this function is called.
    """
    if context.mode != 'OBJECT':
        raise RuntimeError('Blender must be in OBJECT mode to duplicate objects.')
    dup_obj = obj.copy()
    if dup_name:
        dup_obj.name = dup_name
    if obj.data:
        dup_obj.data = obj.data.copy()  # Also duplicate object data if needed
        if dup_name:
            dup_obj.data.name = dup_name
            
    # Link it to the collection
    collection = get_collection(collection_name, ensure_exist=True) if collection_name else context.collection
    collection.objects.link(dup_obj)
    return dup_obj


def duplicate_mesh_light(
        context,
        mesh_obj: bpy.types.Object,
        dup_name: str = None,
        collection_name: str = None
    ) -> bpy.types.Object:
    """
    Duplicates a mesh object in Blender and clears its animation data and shape keys.
    If the object to duplicate is not a mesh, a TypeError is raised. Blender must be in 
    OBJECT mode for this operation to succeed.

    Args:
        context (bpy.types.Context): The context in which the duplication is done.
        mesh_obj (bpy.types.Object): The mesh object to be duplicated.
        dup_name (str): The new name for the duplicated mesh object.
        collection_name (str): The name of the collection to add the 
        duplicated mesh object to.
    
    Returns:
        bpy.types.Object: The duplicated mesh object with cleared animation data 
        and shape keys.

    Raises:
        TypeError: If the object to duplicate is not a mesh.
        RuntimeError: If Blender is not in OBJECT mode when this function is called.
    """
    if mesh_obj.type != 'MESH':
        raise TypeError('Object to duplicate must be a mesh.')
    dup_obj = duplicate_object(context, mesh_obj, dup_name, collection_name)
    dup_obj.data.animation_data_clear()
    dup_obj.modifiers.clear()
    # Remove all shape keys
    dup_obj.shape_key_clear()
    return dup_obj


def join_objects(objects: List[bpy.types.Object]) -> bpy.types.Object:
    # Memorize the current selection
    memorize_object_selection()

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # Check if the list is not empty
    if not objects:
        print("No objects provided for joining.")
        return

    for obj in objects:
        obj.select_set(True)  # Select the object

    # Set the first object in the list as the active object
    bpy.context.view_layer.objects.active = objects[0]
    
    # Join the objects
    bpy.ops.object.join()

    # Restore original selection
    restore_object_selection()
    return objects[0]


def merge_by_distance(obj: bpy.types.Object, threshold=0.001, boundary_edges: bool = False):
    """
    Merges vertices of a mesh object within a specified distance threshold.
    If 'boundary_edges' is set to True, the operation is limited to boundary vertices,
    which are vertices connected to edges that form the outer boundary of the mesh.
    This is particularly useful for cleaning up mesh edges while preserving the overall shape.

    Args:
        obj (bpy.types.Object): The mesh object on which to perform the vertex merge.
            Raises an exception if this is not a valid mesh object.
        threshold (float, optional): The distance threshold for merging vertices.
            Defaults to 0.001.
        boundary_edges (bool, optional): If True, only merges boundary vertices.
            Defaults to False.

    Raises:
        Exception: If 'obj' is None, not provided, or not a mesh object.
    """
    if not obj or obj.type != 'MESH':
        raise Exception("Invalid or non-mesh object provided.")
    
    # Manage selection in the object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set("OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Select vertices on the edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    if boundary_edges:
        mesh = obj.data
        bpy.ops.mesh.select_all(action="DESELECT")
        # Dictionary to count how many times each edge occurs in polygons
        edge_face_count = {e.key: 0 for e in mesh.edges}

        # Count the number of polygons each edge belongs to
        for poly in mesh.polygons:
            for edge in poly.edge_keys:
                edge_face_count[edge] += 1

        # Selecting edges
        bpy.ops.object.mode_set(mode='EDIT')  # Switch to edit mode
        bpy.ops.mesh.select_mode(type="EDGE")  # Select edge selection mode
        bpy.ops.mesh.select_all(action='DESELECT')  # Deselect all edges
        bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to object mode

        # Select edges that are only connected to one polygon
        for edge in mesh.edges:
            if edge_face_count[edge.key] == 1:
                edge.select = True

        bpy.ops.object.mode_set(mode='EDIT')  # Switch back to edit mode
        bpy.ops.mesh.select_mode(type="VERT")
    else:
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action="SELECT")
    
    # Merge
    bpy.ops.mesh.remove_doubles(threshold=threshold, use_unselected=False)  
    
    # Switch back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')


def create_empty_mesh_object(name: str, collection: bpy.types.Collection = None) -> bpy.types.Object:
    # Create new mesh and mesh object
    mesh = bpy.data.meshes.new(name=name)
    obj = bpy.data.objects.new(name, object_data=mesh)
    collection = collection if collection else bpy.context.collection
    collection.objects.link(obj)
    return obj


def get_deformed_vertices(context: bpy.types.Context, obj: bpy.types.Object) -> List[mathutils.Vector]:
    """
    Returns a list of deformed vertex positions for a given object in Blender.
    This function evaluates the object with all modifiers applied and retrieves
    the positions of its vertices in their deformed state.

    Args:
        context (bpy.types.Context): The current Blender context.
        obj (bpy.types.Object): The object to evaluate.

    Returns:
        List[mathutils.Vector]: A list of vertex positions after applying all modifiers.
    """
    # Get an evaluated version of the object (with modifiers applied)
    dg = context.evaluated_depsgraph_get()
    temp_obj = obj.evaluated_get(dg)

    return temp_obj.data.vertices


def toggle_to_object_edit_mode(context: bpy.types.Context, obj: bpy.types.Object):
    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")


def toggle_to_objects_edit_mode(context: bpy.types.Context, objs: List[bpy.types.Object]):
    if len(objs) == 0:
        raise IndexError("Empty list of object to select")
    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = objs[0]
    for obj in objs:
        obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")    


def check_scene_units(scene: bpy.types.Scene) -> bool:
    return scene.unit_settings.system == 'METRIC' and abs(scene.unit_settings.scale_length - 0.01) < 1e-6


def memorize_mode() -> None:
    global _mem_mode
    if bpy.context.active_object:
        _mem_mode = bpy.context.active_object.mode
    else:
        _mem_mode = "OBJECT"


def restore_mode() -> None:
    global _mem_mode
    if _mem_mode is not None:
        bpy.ops.object.mode_set(mode=_mem_mode)


def memorize_object_selection() -> None:
    """
    Memorize the current selection
    """
    global _mem_active_object, _mem_selected_objects
    _mem_active_object = bpy.context.view_layer.objects.active
    _mem_selected_objects = [obj for obj in bpy.context.selected_objects]


def restore_object_selection() -> None:
    """
    Restore original selection
    """
    bpy.ops.object.select_all(action='DESELECT')
    global _mem_active_object, _mem_selected_objects
    if _mem_selected_objects is not None:
        for obj in _mem_selected_objects:
            try:
                obj.select_set(True)
            except ReferenceError:
                pass
    if _mem_active_object:
        try:
            bpy.context.view_layer.objects.active = _mem_active_object
        except ReferenceError:
            pass


def add_armature_modifier(mesh_obj: bpy.types.Object, armature_obj: bpy.types.Object) -> None:
    """
    Adds a new Armature modifier to a mesh object and associates it
    with the given armature object.

    Args:
        mesh_obj (bpy.types.Object): The mesh object to which the modifier will be added.
            Raises ValueError if not a mesh.
        armature_obj (bpy.types.Object): The armature object to be used in the modifier.
            Raises ValueError if not an armature.

    Returns:
        bpy.types.ArmatureModifier: The newly created Armature modifier.

    Raises:
        ValueError: If either 'mesh_obj' is not a mesh or 'armature_obj' is not an armature.
    """
    if mesh_obj.type != "MESH":
        raise ValueError("Provided object is not a mesh")
    if armature_obj.type != "ARMATURE":
        raise ValueError("Provided object is not an armature")
    
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = armature_obj
    mod.use_vertex_groups = True
    return mod


def add_surface_deform_modifier(
        context: bpy.types.Context,
        obj: bpy.types.Object,
        name: str,
        target: bpy.types.Object,
        falloff: float = 4.0,
        strength: float = 1.0,
        ovewrite_if_exists: bool = False
    ) -> bpy.types.SurfaceDeformModifier:
    """
    Adds a Surface Deform modifier to an object and binds it to a target.

    This function creates a Surface Deform modifier with specified parameters and attempts 
    to bind it to the given target object. If 'ovewrite_if_exists' is True, it will replace
    any existing modifier with the same name.

    Args:
        obj (bpy.types.Object): The object to which the modifier is added.
        name (str): The name of the modifier.
        target (bpy.types.Object): Mesh object to deform with.
        falloff (float, optional): Controls how much nearby polygons influence deformation. Default is 4.0. Min=2, Max=16
        strength (float, optional): Strength of modifier deformations. Default is 1.0. Min = -100, Max = 100
        ovewrite_if_exists (bool, optional): Whether to replace the modifier if it already exists. Default is False.

    Returns:
        bpy.types.SurfaceDeformModifier: The created or modified Surface Deform modifier.
    """
    if context:
        context.view_layer.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj
    if ovewrite_if_exists:
        modifier = obj.modifiers.get(name)
        if modifier:
            obj.modifiers.remove(modifier)
    modifier = obj.modifiers.new(name=name, type="SURFACE_DEFORM")
    modifier.target = target
    modifier.falloff = falloff
    modifier.strength = strength
    bpy.ops.object.surfacedeform_bind(modifier=modifier.name)
    return modifier

    
def add_mesh_deform_modifier(
        context: bpy.types.Context,
        obj: bpy.types.Object,
        name: str,
        target: bpy.types.Object,
        precision: int = 5,
        ovewrite_if_exists: bool = False
    ) -> bpy.types.MeshDeformModifier:
    """
    Adds a Mesh Deform modifier to an object and binds it to a deform object.

    This function creates a Mesh Deform modifier with specified parameters and attempts
    to bind it to the given deform object.If 'ovewrite_if_exists' is True, it will replace
    any existing modifier with the same name.

    Args:
        obj (bpy.types.Object): The object to which the modifier is added.
        name (str): The name of the modifier.
        target (bpy.types.Object): Mesh object to deform with (original blender name is "object").
        precision (int, optional): The precision of the mesh deformation, between 2 and 10. Default is 5.
        ovewrite_if_exists (bool, optional): Whether to replace the modifier if it already exists. Default is False.

    Returns:
        bpy.types.MeshDeformModifier: The created or modified Mesh Deform modifier.
    """
    if context:
        context.view_layer.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj
    if ovewrite_if_exists:
        modifier = obj.modifiers.get(name)
        if modifier:
            obj.modifiers.remove(modifier)
    modifier = obj.modifiers.new(name=name, type="MESH_DEFORM")
    modifier.object = target
    modifier: bpy.types.MeshDeformModifier
    modifier.precision = precision
    bpy.ops.object.meshdeform_bind(modifier=modifier.name)
    return modifier
