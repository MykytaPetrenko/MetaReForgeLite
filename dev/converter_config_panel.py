import bpy
from bpy.types import Panel
from ..ops.convert import MRFL_save_wrapping_config, MRFL_convert_to_edit_meshes


class MRFL_PT_wrapping_panel(Panel):
    """Panel for shape transferring"""
    bl_label = "Shape Transfer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MRF-L"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.mrfl_converter_prop
        
        # Category dropdown
        layout.prop(props, "category")
        
        # Config dropdown (only show if category is selected)
        if props.category and props.category != 'NONE':
            layout.prop(props, "config")

        # Object selection
        layout.prop(props, 'source_object', text='Source')

        if props.selective_smoothing:
            box = layout.box()
            box.prop(props, 'selective_smoothing')
            box.prop(props, 'selective_smoothing_factor')
            box.prop(props, 'selective_smoothing_repeats')
        else:
            layout.prop(props, 'selective_smoothing')

        if props.full_smoothing:
            box = layout.box()
            box.prop(props, 'full_smoothing')
            box.prop(props, 'full_smoothing_factor')
            box.prop(props, 'full_smoothing_repeats')
        else:
            layout.prop(props, 'full_smoothing')
        
        # Transfer button
        layout.separator()
        op = layout.operator(MRFL_convert_to_edit_meshes.bl_idname)
        op.selective_smoothing = props.selective_smoothing
        op.selective_smoothing_factor = props.selective_smoothing_factor
        op.selective_smoothing_repeats = props.selective_smoothing_repeats
        op.full_smoothing = props.full_smoothing
        op.full_smoothing_factor = props.full_smoothing_factor
        op.full_smoothing_repeats = props.full_smoothing_repeats
        op.config_category = props.category
        op.config_name =props.config

        # DEV TOOLS
        # New config creation
        box = layout.box()
        box.label(text='[dev] Create New Config')
        box.prop(props, 'new_config_category', text='Category')
        box.prop(props, 'new_config_name', text='Name')
        box.prop(props, 'new_config_source_object', text='Source')
        box.prop(props, 'new_config_target_object', text='Target')
        layout.separator()
        layout.operator(MRFL_save_wrapping_config.bl_idname, text='Create Config')


def register():
    bpy.utils.register_class(MRFL_PT_wrapping_panel)


def unregister():
    bpy.utils.unregister_class(MRFL_PT_wrapping_panel)
