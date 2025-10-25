import traceback
import bpy
from typing import Dict, List

from .collection import (
    get_collections_hide_viewport,
    get_view_layer_collections_hide_viewport,
    get_view_layer_collections_exclude,
    set_collections_hide_viewport,
    set_view_layer_collections_hide_viewport,
    set_view_layer_collections_exclude
)

from .object import (
    get_objects_hide_states,
    set_objects_hide_states
)


class EditorState:
    def __init__(
        self,
        mode: str,
        objects_hide_states: Dict[str, Dict[str, bool]],
        collections_hide_viewport_states: Dict[str, bool],
        view_layer_collections_hide_viewport_states: Dict[str, bool],
        view_layer_collections_exclude_states: Dict[str, bool],
        selected_objects: List[str],
        active_object_name: str
    ) -> None:
        self.mode = mode
        self.objects_hide_states = objects_hide_states
        self.collection_hide_viewport_states = collections_hide_viewport_states
        self.vl_collection_hide_viewport_states = view_layer_collections_hide_viewport_states
        self.vl_collection_exclude_states = view_layer_collections_exclude_states
        self.selected_objects = selected_objects
        self.active_object_name = active_object_name

    def restore_state(self, selected: List[bpy.types.Object] = None, active: bpy.types.Object = None) -> None:
        # Perform global deselection
        try:
            bpy.ops.object.mode_set("OBJECT")
            bpy.ops.object.select_all(action='DESELECT')
        except:
            pass
        

        # Restore the visibility states
        set_objects_hide_states(self.objects_hide_states)
        set_collections_hide_viewport(self.collection_hide_viewport_states)
        set_view_layer_collections_hide_viewport(self.vl_collection_hide_viewport_states)
        set_view_layer_collections_exclude(self.vl_collection_exclude_states)
        
        # Restore the active object and selection states
        try:
            if active:
                bpy.context.view_layer.objects.active = active
            elif self.active_object_name:
                bpy.context.view_layer.objects.active = bpy.data.objects.get(self.active_object_name)
        except RuntimeError:
            print("Unable to set active object")

        if bpy.context.view_layer.objects.active:
            if selected:
                for obj in selected:
                    obj.select_set(True)
            else:
                for obj_name in self.selected_objects:
                    obj = bpy.data.objects.get(obj_name)
                    if obj:
                        obj.select_set(True)

        # Restore the original mode if applicable
        if bpy.context.view_layer.objects.active and self.mode != 'OBJECT' and self.mode != None:
            bpy.ops.object.mode_set(mode=self.mode)

    def try_restore(self, selected: List[bpy.types.Object] = None, active: bpy.types.Object = None) -> None:
        try:
            self.restore_state(selected=selected, active=active)
        except Exception as ex:
            print(f"Unable to restore state: {str(ex)}")
            print(traceback.format_exc())


    @staticmethod
    def capture_current_state() -> "EditorState":
        current_mode = bpy.context.object.mode if bpy.context.object else None
        current_selected_objects = [obj.name for obj in bpy.context.selected_objects]
        current_active_object = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None

        return EditorState(
            mode=current_mode,
            objects_hide_states=get_objects_hide_states(),
            collections_hide_viewport_states=get_collections_hide_viewport(),
            view_layer_collections_hide_viewport_states=get_view_layer_collections_hide_viewport(),
            view_layer_collections_exclude_states=get_view_layer_collections_exclude(),
            selected_objects=current_selected_objects,
            active_object_name=current_active_object
        )
