import bpy
from typing import List


def import_fbx(context: bpy.types.Context, fbx_path: str) -> List[bpy.types.Object]:
    """
    Imports an FBX file into the current Blender scene and returns a list of newly added objects.

    This function imports an FBX file specified by the `fbx_path` into the current Blender context. 
    It first records the initial set of objects in the scene, imports the FBX file with specific parameters,
    and then identifies the new objects added to the scene as a result of the import operation.
    Finally, it updates the scene's view layer and returns the list of new objects.

    Args:
        context: The current Blender context, which contains the scene into which the FBX file will be imported.
        fbx_path (str): The file system path to the FBX file to be imported.

    Returns:
        List[bpy.types.Object]: A list of new objects that were added to the scene as a result of the import.

    Notes:
        The import operation uses manual orientation with 'Y' as the forward axis and 'Z' as the up axis.
    """
    # Get the initial list of objects
    initial_objects = set(context.scene.objects)
    
    # Set up the import parameters
    bpy.ops.import_scene.fbx(
        filepath=fbx_path,
        use_manual_orientation=True,
        axis_forward='Y',
        axis_up='Z'
    )

    # Get the list of objects after the operation
    final_objects = set(context.scene.objects)

    # Find the new objects by subtracting the initial set from the final set
    new_objects = final_objects - initial_objects
    bpy.context.view_layer.update()

    return list(new_objects)

