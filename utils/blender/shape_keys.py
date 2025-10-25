import bpy
from typing import List, Dict


def get_sk_values(obj: bpy.types.Object) -> Dict[str, float]:
    sk_values = dict()
    for key_block in obj.data.shape_keys.key_blocks:
        sk_values[key_block.name] = key_block.value
        key_block.value = 0.0
    return sk_values


def restore_sk_values(obj: bpy.types.Object, sk_values: Dict[str, float]) -> None:
    for key_block in obj.data.shape_keys.key_blocks:
        key_block.value = sk_values.get(key_block.name, 0.0)


def get_shape_keys_count(obj: bpy.types.Object) -> int:
    if obj.type != "MESH":
        raise ValueError("Provided object is not a mesh")
    if obj.data.shape_keys:
        return len(obj.data.shape_keys.key_blocks)
    else:
        return 0


def remove_shape_key(obj: bpy.types.Object, shape_key_name: str) -> None:
    """
    Removes a specified shape key from a given mesh object.

    This function checks if the provided object is a mesh and if it contains the specified shape key. 
    If the shape key exists, it is removed from the object.

    Args:
        obj (bpy.types.Object): The mesh object from which the shape key is to be removed.
        shape_key_name (str): The name of the shape key to be removed.

    Raises:
        ValueError: If the provided object is not a mesh.
    """
    if obj.type != "MESH":
        raise ValueError("Provided object is not a mesh")
    if obj.data.shape_keys:
        sk = obj.data.shape_keys.key_blocks.get(shape_key_name)
        if sk:
            obj.shape_key_remove(sk)


def add_new_shape_key(
        obj: bpy.types.Object,
        shape_key_name: str,
        from_mix: bool = False,
        replace: bool = False
) -> bpy.types.ShapeKey:
    """
    Adds a new shape key to a given mesh object.

    This function creates a new shape key with the specified name for the provided mesh object. 
    If the object does not have any shape keys, a basis shape key is created first. 
    If the 'replace' flag is set to True and a shape key with the same name exists, 
    it is first removed before creating the new one.

    Args:
        obj (bpy.types.Object): The mesh object to which the shape key will be added.
        shape_key_name (str): The name of the new shape key.
        from_mix (bool, optional): Determines whether the new shape key is created from the current mix of existing shape keys. Defaults to False.
        replace (bool, optional): If True, any existing shape key with the same name will be replaced. Defaults to False.

    Returns:
        bpy.types.ShapeKey: The newly created shape key.

    Raises:
        ValueError: If the provided object is not a mesh.
    """
    if obj.type != "MESH":
        raise ValueError("Provided object is not a mesh")
    if not obj.data.shape_keys:
        obj.shape_key_add(name='Basis', from_mix=False)
    if replace:
        remove_shape_key(obj, shape_key_name)
        obj.data.update()
    shape_key = obj.shape_key_add(name=shape_key_name, from_mix=from_mix)
    return shape_key


def join_as_shape(
        target_object: bpy.types.Object,
        source_obj: bpy.types.Object,
        shape_key_name: str = None,
        replace: bool = False
) -> bpy.types.ShapeKey:
    """
    Joins a source object to a target object as a new shape key.

    This function transfers the vertex positions from the source object to a new shape key in the target object. 
    If no shape key name is provided, the name of the source object is used. The function allows for the option 
    to replace an existing shape key of the same name in the target object.

    Args:
        target_object (bpy.types.Object): The target object to which the shape key will be added.
        source_obj (bpy.types.Object): The source object whose vertex positions will be used.
        shape_key_name (str, optional): The name for the new shape key. If not provided, the source object's name is used. Defaults to None.
        replace (bool, optional): If True, an existing shape key with the same name on the target object will be replaced. Defaults to False.

    Returns:
        bpy.types.ShapeKey: The newly created shape key in the target object.

    Note:
        The function assumes both source and target objects are of the 'MESH' type and have the same number of vertices.
    """
    
    if not shape_key_name:
        shape_key_name = source_obj.name

    sk = add_new_shape_key(target_object, shape_key_name, from_mix=False, replace=replace)

    # Transfer vertex positions from the source object to the new shape key
    shape_keys = source_obj.data.shape_keys
    if shape_keys and len(shape_keys.key_blocks) > 0:
        source_vertices = shape_keys.key_blocks[0].data
    else:
        source_vertices = source_obj.data.vertices
    for i, vertex in enumerate(source_vertices):
        # Apply the vertex position from the source object to the new shape key
        sk.data[i].co = vertex.co

    return sk

def copy_shape_key(
        target: bpy.types.Object,
        source: bpy.types.Object,
        shape_key: str
) -> bpy.types.ShapeKey:
    source_sk = source.data.shape_keys.key_blocks.get(shape_key)
    if source_sk is None:
        raise ValueError(f'"{source.name}" object does not contain "{shape_key}" shape key')
    
    target_sk = target.data.shape_keys.key_blocks.get(shape_key)
    if target_sk is None:
        target_sk = target.shape_key_add(name=shape_key, from_mix=False)

    flattened_coordinates = [co for v in source_sk.data for co in v.co[:]]
    # Ensure the length matches
    if len(flattened_coordinates) == 3 * len(target_sk.data):
        target_sk.data.foreach_set("co", flattened_coordinates)
    else:
        raise ValueError("Mismatch in the number of vertices.")
    


def join_separate_as_shape_key(
    target_object: bpy.types.Object,
    source_objects: List[bpy.types.Object],
    start_vertex_indices: List[int],
    end_vertex_indices: List[int],
    shape_key_name: str
) -> bpy.types.ShapeKey:
    """
    Joins separate objects as a new shape key to a target object.

    This function takes a list of source objects and integrates them into the target object as a new shape key. 
    The vertices from the source objects are mapped to the target object based on provided start and end indices.

    Args:
        target_object (bpy.types.Object): The object to which the shape key will be added.
        source_objects (List[bpy.types.Object]): A list of objects whose mesh data will be used to create the shape key.
        start_vertex_indices (List[int]): A list of starting vertex indices in the target object for each source object.
        end_vertex_indices (List[int]): A list of ending vertex indices in the target object for each source object.
        shape_key_name (str): The name of the new shape key.

    Returns:
        bpy.types.ShapeKey: The newly created shape key.

    Raises:
        IndexError: If any vertex index is invalid or out of range.

    Note:
        The length of source_objects, start_vertex_indices, and end_vertex_indices must be the same.
    """

    # Add the new shape key to the target object
    print(target_object.name)
    new_shape_key = add_new_shape_key(target_object, shape_key_name, from_mix=False, replace=True)

    # Iterate through each source object and its corresponding vertex indices
    for mesh_index, source_obj in enumerate(source_objects): 
        source_mesh = source_obj.data
        start_index = start_vertex_indices[mesh_index]
        end_index = end_vertex_indices[mesh_index]

        # Map vertices from source mesh to the new shape key
        for vert in source_mesh.vertices:
            index = start_index + vert.index
            if index > end_index:
                raise IndexError(f"Invalid vertex index: {index} exceeds end index {end_index}")

            new_shape_key.data[index].co = vert.co

    # Update the target object's mesh data
    target_object.data.update()

    return new_shape_key
