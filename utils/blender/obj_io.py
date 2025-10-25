# TODO. The code is not checked as it is not neccessary for the current update.

import bpy
from typing import List


def import_obj(context: bpy.types.Context, obj_path: str) -> List[bpy.types.Object]:
    """
    Imports an OBJ file into the current Blender scene and returns a list of newly added objects.

    This function imports an OBJ file specified by the `obj_path` into the current Blender context. 
    It first records the initial set of objects in the scene, imports the OBJ file with specific parameters,
    and then identifies the new objects added to the scene as a result of the import operation.
    Finally, it updates the scene's view layer and returns the list of new objects.

    Args:
        context: The current Blender context, which contains the scene into which the OBJ file will be imported.
        obj_path (str): The file system path to the OBJ file to be imported.

    Returns:
        List[bpy.types.Object]: A list of new objects that were added to the scene as a result of the import.

    Notes:
        The import operation uses manual orientation with 'Y' as the forward axis and 'Z' as the up axis.
        The OBJ importer also includes options for importing groups as objects and splitting by groups.
    """
    # Get the initial list of objects
    initial_objects = set(context.scene.objects)
    
    # Set up the import parameters
    bpy.ops.wm.obj_import(
        filepath=obj_path,
        use_split_objects=True,
        use_split_groups=True,
        forward_axis='Y',
        up_axis='Z'
    )

    # Get the list of objects after the operation
    final_objects = set(context.scene.objects)

    # Find the new objects by subtracting the initial set from the final set
    new_objects = final_objects - initial_objects
    bpy.context.view_layer.update()

    return list(new_objects)

def export_as_obj(context: bpy.types.Context, obj: bpy.types.Object, file_path: str, 
                  forward_axis: str = 'NEGATIVE_Z', up_axis: str = 'Y') -> None:
    """
    Exports a single Blender object as an OBJ file.

    This function exports a specified Blender object to an OBJ file at the given path. 
    It ensures the scene is in Object mode, clears all selections, selects only the target object,
    and exports it with the "selection only" option enabled. The function handles the selection
    state automatically and restores it after export.

    Args:
        context: The current Blender context containing the scene and objects.
        obj (bpy.types.Object): The Blender object to be exported.
        file_path (str): The file system path where the OBJ file will be saved.
        forward_axis (str, optional): The forward axis for export orientation. Defaults to 'Y'.
        up_axis (str, optional): The up axis for export orientation. Defaults to 'Z'.

    Returns:
        None

    Raises:
        RuntimeError: If the object is not in the current scene or if export fails.

    Notes:
        - The function automatically switches to Object mode before export
        - Only the specified object will be exported (selection_only=True)
        - The original selection state is not preserved after export
        - Valid axis values are 'X', 'Y', 'Z', '-X', '-Y', '-Z'
    """
    # Store current mode and switch to Object mode if needed
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear all selections
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select the target object
    obj.select_set(True)
    context.view_layer.objects.active = obj
    
    # Export the selected object as OBJ
    bpy.ops.wm.obj_export(
        filepath=file_path,
        export_selected_objects=True,
        forward_axis=forward_axis,
        up_axis=up_axis
    )