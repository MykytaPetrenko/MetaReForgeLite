import bpy
from bpy.types import Operator
from ..props.converter_prop import scan_transfer_presets


class MRFL_OT_refresh_converter_presets(Operator):
    """Refresh and rescan the transfer preset files.
    
    This operator rescans the wrapping_presets directory to update the available
    preset categories and JSON preset files. Use this when you have added,
    removed, or modified preset files outside of Blender and need to update the
    dropdown menus in the converter properties panel.
    """
    bl_idname = "metareforge_lite.refresh_converter_presets"
    bl_label = "Refresh Converter Presets"
    bl_description = "Rescan and refresh the transfer preset files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            scan_transfer_presets()
            self.report({'INFO'}, "Successfully refreshed converter presets")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to refresh presets: {str(e)}")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(MRFL_OT_refresh_converter_presets)


def unregister():
    bpy.utils.unregister_class(MRFL_OT_refresh_converter_presets)
