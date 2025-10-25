import bpy
from bpy.types import Panel
from ..utils.config import get_mesh_edit_prop
from ..ops.symmetrize_by_uvs import (
    MRFL_OT_symmetrize_all_by_uvs,
    MRFL_OT_symmetrize_selected_by_uvs
)


class MRFL_PT_mesh_edit_panel(Panel):
    """
    Addon mesh edit menu (N-Panel)
    """
    bl_label = 'MetaReForge-Lite'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MRF-L'
    bl_context = 'mesh_edit'

    def draw(self, context):
        layout = self.layout
        config = get_mesh_edit_prop(context)

        box = layout.box()
        box.label(text='Symmetrizer')
        box.prop(config, 'mid_point_tolerance', text='Mid-Point Tolerance')
        other_box = box.box()
        other_box.prop(config, 'symmetrize_selected_mode', text='Mode')
        op_props = other_box.operator(MRFL_OT_symmetrize_selected_by_uvs.bl_idname, text='Symmetrize Selected')
        op_props.mode = config.symmetrize_selected_mode
        op_props.tolerance = config.mid_point_tolerance
        other_box = box.box()
        other_box.prop(config, 'symmetrize_all_mode', text='Mode')
        other_box.prop(config, 'save_original_shape', text='Save Original as a ShapeKey')
        op_props = other_box.operator(MRFL_OT_symmetrize_all_by_uvs.bl_idname, text='Symmetrize All')
        op_props.mode = config.symmetrize_all_mode
        op_props.tolerance = config.mid_point_tolerance
        op_props.save_original_shape = config.save_original_shape



def register():
    bpy.utils.register_class(MRFL_PT_mesh_edit_panel)


def unregister():
    bpy.utils.unregister_class(MRFL_PT_mesh_edit_panel)
