import bpy
from .dropdown import dropdown
from ..utils.blender.unsorted import check_scene_units
# from .. import icons
from ..utils.config import get_main_prop
from ..ops.file_selector import MRFL_file_selector
from ..ops.initialize import MRFL_OT_import, check_for_import
from ..ops.setup_scene import MRFL_OT_setup_scene
from ..ops.generate_template import MRFL_OT_generate_template_meshes
from ..ops.show_hint import MRFL_OT_show_hint
from ..ops.convert import MRFL_convert_to_edit_meshes
from ..ops.export_templates import MRFL_OT_export_template_meshes


class MRFL_PT_panel(bpy.types.Panel):
    """
    Addon main menu (N-Panel)
    """
    bl_label = 'MetaReForge-Lite'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MRF-L'
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout
        config = get_main_prop(context)
        is_units_ok = check_scene_units(context.scene)
        if not is_units_ok:
            layout.operator(MRFL_OT_setup_scene.bl_idname, text='Setup scene units!', icon='ERROR')

        # IMPORT SECTION
        result = {}
        box = layout.box()
        if dropdown(box, config, 'show_import_section', 'Import', result=result):
            row = box.row(align=True)
            row.prop(config, 'import_head', toggle=1)
            row.prop(config, 'import_body', toggle=1)    

            # HEAD PATH ROW
            row = box.row(align=True)
            row.prop(config, 'fbx_head_path', text='Head FBX')
            op_props = row.operator(
                MRFL_file_selector.bl_idname, text='', icon='FILE_FOLDER'
            )
            op_props.target_property = 'fbx_head_path'
            op_props.filter_glob = '*.fbx'
            if not config.import_head:
                row.enabled = False      
            
            # BODY PATH ROW
            row = box.row(align=True)
            row.prop(config, 'fbx_body_path', text='Body FBX')
            op_props = row.operator(
                MRFL_file_selector.bl_idname, text='', icon='FILE_FOLDER'
            )
            op_props.target_property = 'fbx_body_path'
            op_props.filter_glob = '*.fbx'
            if not config.import_body:
                row.enabled = False

                   
            can_import, error = check_for_import(context)
            if can_import and is_units_ok:
                box.operator(MRFL_OT_import.bl_idname)
            else:
                error = error if is_units_ok else 'Setup scene units!'
            
                col = box.column(align=True)
                col.operator(MRFL_OT_import.bl_idname)
                col.label(text=error)
                col.enabled = False
        
        row = result['dropdown_row']
        op_props = row.operator(MRFL_OT_show_hint.bl_idname, text='', icon='INFO')
        op_props.hint_title = 'Import'
        op_props.hint_name = 'import'
            
        # OBJECTS SECTION
        box = layout.box()
        if dropdown(box, config, 'show_edit_meshes_section', 'Edit Meshes', result=result):
            box.prop(config, 'body')
            box.prop(config, 'teeth')
            box.prop(config, 'left_eye')
            box.prop(config, 'right_eye')

        row = result['dropdown_row']
        op_props = row.operator(MRFL_OT_show_hint.bl_idname, text='', icon='INFO')
        op_props.hint_title = 'Edit Meshes'
        op_props.hint_name = 'edit_meshes'


        # TEMPLATE MESHES
        box = layout.box()
        result = {}
        if dropdown(box, config, 'show_template_meshes_section', 'Template Meshes', result=result):
            other_box = box.box()
            other_box.label(text='Objects:')
            other_box.prop(config, 'head_template', text='Head')
            other_box.prop(config, 'body_template', text='Body')
            other_box.prop(config, 'left_eye_template', text='Left Eye')
            other_box.prop(config, 'right_eye_template', text='Right Eye')
            other_box.prop(config, 'teeth_template', text='Teeth')

            other_box.prop(config, 'remove_old_templates', text='Remove Old')

            if MRFL_OT_generate_template_meshes.is_running:
                step = MRFL_OT_generate_template_meshes.step
                num_steps = MRFL_OT_generate_template_meshes.num_steps
                status = MRFL_OT_generate_template_meshes.status
                other_box.label(text=status)
                other_box.prop(config, 'conformal_init_percentage', text=f'Processing {step}/{num_steps}...', slider=True)
            else:
                other_box.operator(MRFL_OT_generate_template_meshes.bl_idname, text='Generate Templates')

            other_box = box.box()
            other_box.label(text='Export:')
            other_box.prop(config, 'export_path', text='Path')
            if MRFL_OT_export_template_meshes.is_running:
                step = MRFL_OT_export_template_meshes.step
                num_steps = MRFL_OT_export_template_meshes.num_steps
                status = MRFL_OT_export_template_meshes.status
                other_box.label(text=status)
                other_box.prop(config, 'export_progress', text=f'Processing {step}/{num_steps}...', slider=True)
            else:
                other_box.operator(MRFL_OT_export_template_meshes.bl_idname, text='Export Templates')

        row = result['dropdown_row']
        op_props = row.operator(MRFL_OT_show_hint.bl_idname, text='', icon='INFO')
        op_props.hint_title = 'Template Meshes'
        op_props.hint_name = 'template_meshes'

        # CONVERTER
        box = layout.box()
        if dropdown(box, config, 'show_converter_section', 'Converter [Daz3D]'):
            transfer_prop = context.scene.mrfl_converter_prop

            
            # Category dropdown
            box.prop(transfer_prop, "category")
            
            # Config dropdown (only show if category is selected)
            if transfer_prop.category and transfer_prop.category != 'NONE':
                box.prop(transfer_prop, "config")

            # Object selection
            box.prop(transfer_prop, 'source_object', text='Source')

            box.prop(transfer_prop, 'selective_smoothing', toggle=1)
            col = box.column()
            col.prop(transfer_prop, 'selective_smoothing_factor')
            col.prop(transfer_prop, 'selective_smoothing_repeats')
            col.enabled = transfer_prop.selective_smoothing

            box.prop(transfer_prop, 'full_smoothing', toggle=1)
            col = box.column()
            col.prop(transfer_prop, 'full_smoothing_factor')
            col.prop(transfer_prop, 'full_smoothing_repeats')
            col.enabled = transfer_prop.full_smoothing
            
            # Transfer button
            op = box.operator(MRFL_convert_to_edit_meshes.bl_idname, text='Convert to Edit Mesh')
            op.selective_smoothing = transfer_prop.selective_smoothing
            op.selective_smoothing_factor = transfer_prop.selective_smoothing_factor
            op.selective_smoothing_repeats = transfer_prop.selective_smoothing_repeats
            op.full_smoothing = transfer_prop.full_smoothing
            op.full_smoothing_factor = transfer_prop.full_smoothing_factor
            op.full_smoothing_repeats = transfer_prop.full_smoothing_repeats
            op.config_category = transfer_prop.category
            op.config_name = transfer_prop.config

        

def register():
    bpy.utils.register_class(MRFL_PT_panel)


def unregister():
    bpy.utils.unregister_class(MRFL_PT_panel)
