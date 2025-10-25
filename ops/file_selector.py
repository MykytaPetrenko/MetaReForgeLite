import bpy
from bpy_extras.io_utils import ImportHelper


class MRFL_file_selector(bpy.types.Operator, ImportHelper):
    """Select an FBX File"""
    bl_idname = "metareforge_lite.select_file"
    bl_label = "Select File"
    
    
    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    target_property: bpy.props.StringProperty()
    
    def execute(self, context):
        # Store the selected file path in the target property
        setattr(context.scene.mrfl_main_prop, self.target_property, self.filepath)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(MRFL_file_selector)


def unregister():
    bpy.utils.unregister_class(MRFL_file_selector)
