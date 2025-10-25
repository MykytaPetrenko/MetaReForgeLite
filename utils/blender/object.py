import bpy
from typing import List, Dict
from .collection import (
    ensure_object_collections_visible,
    ensure_object_view_layer_collections_visible,
    ensure_object_view_layer_collections_included
)


def ensure_object_visible(obj: bpy.types.Object) -> None:
    """
    Ensures that the specified object is visible in the view layer, along with its parent collections.

    This function sets the object's visibility properties and calls other functions to ensure the visibility of the object's parent collections in the view layer and in the overall Blender data.

    Args:
        obj (bpy.types.Object): The object to make visible.
    """
    # Ensuring the object itself is visible in the viewport and not hidden
    obj.hide_viewport = False
    obj.hide_set(False)

    # Ensuring the visibility of collections in the view layer and Blender data
    ensure_object_collections_visible(obj)
    ensure_object_view_layer_collections_visible(obj)
    ensure_object_view_layer_collections_included(obj)


def ensure_objects_visible(objects: List[bpy.types.Object]) -> None:
    """
    Ensures that each object in the provided list is visible in the view layer, along with their parent collections.

    This function iterates through a list of objects, applying visibility settings to each object and their associated collections in the view layer and in the overall Blender data.

    Args:
        objects (List[bpy.types.Object]): A list of objects to make visible.
    """
    for obj in objects:
        ensure_object_visible(obj)


def get_objects_hide_states() -> Dict[str, Dict[str, bool]]:
    """
    Retrieves the visibility and selectability states of all objects in Blender.

    This function collects the hide (eye icon), hide_viewport (monitor icon), hide_render (camera icon), and hide_select (selectability) states for each object.

    Returns:
        dict: A dictionary mapping object names to a dictionary of their various hide states.
    """
    hide_states = {}
    for obj in bpy.data.objects:
        hide_states[obj.name] = dict(
            hide=obj.hide_get(),
            hide_viewport=obj.hide_viewport,
            hide_render=obj.hide_render,
            hide_select=obj.hide_select
        )

    return hide_states


def set_objects_hide_states(hide_states: Dict[str, Dict[str, bool]]) -> None:
    """
    Sets the visibility and selectability states of all objects in Blender based on the provided dictionary.

    This function updates the hide (eye icon), hide_viewport (monitor icon), hide_render (camera icon), and hide_select (selectability) states for each object according to the dictionary.

    Args:
        hide_states (dict): A dictionary mapping object names to their desired hide states.
    """
    for obj_name, states in hide_states.items():
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            obj.hide_set(states['hide'])
            obj.hide_viewport = states['hide_viewport']
            obj.hide_render = states['hide_render']
            obj.hide_select = states['hide_select']
