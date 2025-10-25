import bpy
from bpy.types import Panel
from ..ops.save_converter_preset import MRFL_OT_create_converter_preset


class MRFL_PT_converter_panel(Panel):
    """Panel for shape transferring"""
    bl_label = 'Converter Presets'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MRF-L'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.mrfl_converter_prop

        # DEV TOOLS
        # New preset creation
        box = layout.box()
        box.label(text='[dev] Create New Preset')
        box.prop(props, 'new_preset_category', text='Category')
        box.prop(props, 'new_preset_name', text='Name')
        box.prop(props, 'new_preset_source_object', text='Source')
        box.prop(props, 'new_preset_target_object', text='Target')
        box.prop(props, 'new_preset_tag', text='Tag')
        box.prop(props, 'smoothing_vertex_group', text='Smoothing Group')
        layout.separator()

        if MRFL_OT_create_converter_preset.is_running:
            status = MRFL_OT_create_converter_preset.status
            layout.label(text=status)
            layout.prop(props, 'preset_creation_progress', text=f'Processing...', slider=True)
        else:
            op = layout.operator(MRFL_OT_create_converter_preset.bl_idname, text='Create Preset')
            op.preset_category = props.new_preset_category
            op.preset_name = props.new_preset_name


def register():
    bpy.utils.register_class(MRFL_PT_converter_panel)


def unregister():
    bpy.utils.unregister_class(MRFL_PT_converter_panel)
