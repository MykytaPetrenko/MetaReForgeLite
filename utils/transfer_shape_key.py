import bpy
import bmesh
import random
from typing import List
from mathutils import Vector
from .blender.shape_keys import (
    restore_sk_values,
    get_sk_values
)
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree


def update_base_mesh(target: bpy.types.Object, new_coordinates: List[Vector]) -> None:
    """
    Updates the base mesh of the target object with new coordinates for all vertices, 
    including those with shape keys.

    This function creates a bmesh from the target object and updates each vertex 
    coordinate with the corresponding new coordinate provided in 'new_coordinates'. 
    The length of 'new_coordinates' must be the same as the number of vertices in the mesh.

    Args:
        target (bpy.types.Object): The target object whose base mesh is to be updated.
        new_coordinates (List[Vector]): A list of new vertex coordinates.

    Raises:
        ValueError: If the number of new coordinates does not match the number of vertices in the mesh.

    """
    mesh = target.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Check if the lengths
    if len(new_coordinates) != len(mesh.vertices):
        raise ValueError("The number of new coordinates must match the number of vertices in the mesh.")
    
    # Apply the shape
    for vert, new_co in zip(bm.verts, new_coordinates):
        vert.co = new_co

    bm.to_mesh(mesh)
    bm.free()
    target.data.update()


def add_delta_noise_shape_key(
        obj: bpy.types.Object,
        shape_key_name: str,
        min_limit: float,
        max_limit: float
    ) -> bpy.types.ShapeKey:
    """
    Adds a delta noise shape key to a specified Blender object.
    This shape key adjusts each vertex of the object by a random value 
    along its normal direction, within specified minimum and maximum limits.

    Args:
        obj (bpy.types.Object): The Blender object (Mesh) to which the shape key is added.
        shape_key_name (str): The name for the new shape key.
        min_limit (float): The minimum limit for the random movement of vertices.
        max_limit (float): The maximum limit for the random movement of vertices.

    Returns:
        bpy.types.ShapeKey: The newly created shape key.

    Raises:
        TypeError: If the provided object is not of the mesh type.
    """

    # Ensure we're in Object mode and that the object is a mesh
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    if obj.type != 'MESH':
        raise TypeError("Object must be of type 'MESH'.")

    # Add a new shape key
    shape_key = obj.shape_key_add(name=shape_key_name, from_mix=False)
    obj.data.update()
    
    # Get the vertex normals from the current shape
    normals = [vertex.normal for vertex in obj.data.vertices]
    
    # Apply random offset to each vertex in the shape key
    for i, vertex in enumerate(shape_key.data):
        offset = normals[i] * random.uniform(min_limit, max_limit)
        vertex.co += Vector(offset)

    return shape_key


def transfer_shapekeys_with_sd_modifier(
        context: bpy.types.Context,
        target: bpy.types.Object,
        proxy: bpy.types.Object,
        source: bpy.types.Object,
        basis_shape_key: str = None,
        bind_key_name: str = None,
        shape_keys: List[str] = None,
        surface_deform_params: dict = None,
        laplacian_deform: bool = False,
        laplacian_deform_params: dict = None,
        laplacian_anchor_threshold: float = 0.1
    ) -> None:
    """
    Transfers a shape key from a source object to a target object. The function 
    applies the shape key deformation from the source object to the target object, using 
    a target basis object with the same topology for intermediate calculations.

    Args:
        context (bpy.types.Context): The current context in Blender.
        target (bpy.types.Object): The object to which the shape key deformation is applied.
        proxy (bpy.types.Object): An object with the same topology as the target,
                                  used for intermediate calculations.
        source (bpy.types.Object): The object from which the shape key deformation is taken.
        source_key_name (str): The name of the shape key in the source object to be transferred.
        bind_key_name (str, optional): The name of the shape key used for fine-tuning the binding. 
                                       Defaults to None.

    Raises:
        Exception: If the bind shape key is not found in the source object.
        Exception: If unable to bind the Surface Deform modifier.
        Exception: If the target shape key is not found in the source object.
    """

    bpy.ops.object.select_all(action="DESELECT")
    context.view_layer.objects.active = proxy
    proxy.select_set(True)
    
    # Memorize shape key values and "pin" state
    source_obj_show_only_shape_key = source.show_only_shape_key
    source.show_only_shape_key = False
    # Memorize modifiers states
    source_modifier_states = {mod.name: mod.show_viewport for mod in source.modifiers}
    for mod in source.modifiers:
        mod.show_viewport = False
    proxy_modifier_states = {mod.name: mod.show_viewport for mod in proxy.modifiers}
    for mod in proxy.modifiers:
        mod.show_viewport = False

    # Memorize shape key values
    sk_values = get_sk_values(source)

    if bind_key_name:
        bind_sk = source.data.shape_keys.key_blocks.get(bind_key_name)
        if not bind_sk:
            raise Exception("Cannot find bind shape key")
        bind_sk.value = 1.0
    
    context.view_layer.objects.active = proxy
    
    # Manage Surface Deform Modifier
    sd_mod = proxy.modifiers.get("MRF_SD")
    if sd_mod:
        proxy.modifiers.remove(sd_mod)
    sd_mod = proxy.modifiers.new(name="MRF_SD", type="SURFACE_DEFORM")
    sd_mod.target = source
    if surface_deform_params:
        for param, value in surface_deform_params.items():
            setattr(sd_mod, param, value)
    bpy.ops.object.surfacedeform_bind(modifier=sd_mod.name)

    if not sd_mod.is_bound:
        raise Exception(
            f"Unable to bind Surface Deform modifier to \"{proxy.name}\"."
            f" SD Target = \"{source.name}\""
        )
    
    # Manage Laplacian Deform Modifier
    ld_mod = proxy.modifiers.get("MRF_LD")
    if ld_mod:
        ld_mod = proxy.modifiers.remove(ld_mod)
        ld_mod = None
        
    if laplacian_deform:
        kd = KDTree(size=len(source.data.vertices))
        for v in source.data.vertices:
            kd.insert(v.co, v.index)
        kd.balance()
        ld_verts = []
        for v in proxy.data.vertices:
            _, _, dist = kd.find(v.co)
            if dist < laplacian_anchor_threshold:
                ld_verts.append(v.index)

        vg = proxy.vertex_groups.get("MFR_ANCHOR")  
        if vg is not None:
            proxy.vertex_groups.remove(vg)
        vg = proxy.vertex_groups.new(name="MFR_ANCHOR")
        vg.add(ld_verts, 1.0, 'REPLACE')

        ld_mod = proxy.modifiers.new(name="MRF_LD", type="LAPLACIANDEFORM")
        ld_mod.vertex_group = vg.name
        if laplacian_deform_params:
            for param, value in laplacian_deform_params.items():
                setattr(ld_mod, param, value)
        bpy.ops.object.laplaciandeform_bind(modifier=ld_mod.name)

        if not ld_mod.is_bind:
            raise Exception("Unable to bind Laplacian Deform modifier")
        proxy.vertex_groups.remove(vg)

    # Update base mesh
    if basis_shape_key:
        sk = source.data.shape_keys.key_blocks.get(basis_shape_key)
        if not sk:
            raise Exception("Cannot find target shape key")
        sk.value = 1.0

        dg = context.evaluated_depsgraph_get()
        eval_obj = proxy.evaluated_get(dg)

        # Transfer vertex position from proxy to target mesh
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode='OBJECT')
        new_coordinates = [vert.co for vert in eval_obj.data.vertices]
        update_base_mesh(target, new_coordinates)
        sk.value = 0.0

    # Update shape keys
    shape_keys = shape_keys if shape_keys else list()
    for sk_name in shape_keys:
        if source.data.shape_keys is None:
            continue
        sk = source.data.shape_keys.key_blocks.get(sk_name)
        if not sk:
            continue
        sk.value = 1.0

        dg = context.evaluated_depsgraph_get()
        eval_obj = proxy.evaluated_get(dg)

        # Transfer vertex position from proxy to target mesh
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode='OBJECT')
        
        if target.data.shape_keys is None:
            target.shape_key_add(name="Basis", from_mix=False)
            target_sk = target.shape_key_add(name=sk_name, from_mix=False)
        else:
            target_sk = target.data.shape_keys.key_blocks.get(sk_name)
            if target_sk is None:
                target_sk = target.shape_key_add(name=sk_name, from_mix=False)
        flattened_coordinates = [co for vert in eval_obj.data.vertices for co in vert.co[:]]
        # Ensure the length matches
        if len(flattened_coordinates) == 3 * len(target_sk.data):
            target_sk.data.foreach_set("co", flattened_coordinates)
        else:
            raise ValueError("Mismatch in the number of vertices.")
        sk.value = 0.0

    proxy.modifiers.remove(sd_mod)
    if ld_mod:
        proxy.modifiers.remove(ld_mod)

    # Restore source modifier viewport states
    for mod in source.modifiers:
        mod.show_viewport = source_modifier_states.get(mod.name, False)

    # Restore target modifier viewport states
    for mod in proxy.modifiers:
        mod.show_viewport = proxy_modifier_states.get(mod.name, False)

    # Restore shape key values and "pin" state
    restore_sk_values(source, sk_values)
    source.show_only_shape_key = source_obj_show_only_shape_key
