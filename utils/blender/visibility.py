import bpy
from .collection import (
    collection_set_exclude,
    collection_set_hide_viewport,
    view_layer_collection_set_hide_viewport
    )
from ...globals import (
    FBX_BODY_COLLECTION,
    FBX_HEAD_COLLECTION,
    INITIAL_SHAPE_COLLECTION,
    FINAL_SHAPE_COLLECTION
)
from ...utils.config import get_main_prop


# Global dictionary to store the visibility settings
_hide = {}


def reveal_collection(collection_name: str) -> None:
    collection_set_exclude(collection_name, False)
    collection_set_hide_viewport(collection_name, False)
    view_layer_collection_set_hide_viewport(collection_name, False)


def reveal_all_collections():
    reveal_collection(FBX_BODY_COLLECTION)
    reveal_collection(FBX_HEAD_COLLECTION)
    reveal_collection(INITIAL_SHAPE_COLLECTION)
    reveal_collection(FINAL_SHAPE_COLLECTION)


def reveal_object(obj: bpy.types.Object) -> None:
    obj.hide_set(False)
    obj.hide_viewport = False


def fbx_reveal_all_objects(context: bpy.types.Context) -> None:
    config = get_main_prop(context)
    if config.fbx_head_armature is not None:
        reveal_object(config.fbx_head_armature)
    if config.fbx_body_armature is not None:
        reveal_object(config.fbx_body_armature)

    for item in config.fbx_head_lods:
        reveal_object(item.object)
    
    for item in config.fbx_body_lods:
        reveal_object(item.object)


def initial_reveal_all(context: bpy.types.Context) -> None:
    config = get_main_prop(context)
    if config.initial_edit_armature is not None:
        reveal_object(config.initial_edit_armature)
    if config.initial_edit_mesh is not None:
        reveal_object(config.initial_edit_mesh)


def final_reveal_all(context: bpy.types.Context) -> None:
    config = get_main_prop(context)
    if config.final_edit_armature is not None:
        reveal_object(config.final_edit_armature)
    if config.final_edit_mesh is not None:
        reveal_object(config.final_edit_mesh)


def memorize_objects_visibility():
    global _hide
    _hide.clear()
    for obj in bpy.context.scene.objects:
        _hide[obj.name] = (obj.hide_get(), obj.hide_viewport)


def restore_objects_visibility():
    global _hide
    for obj_name, (hide, hide_viewport) in _hide.items():
        obj = bpy.context.scene.objects.get(obj_name)
        if obj:
            obj.hide_set(hide)
            obj.hide_viewport = hide_viewport
