import bpy


class MRFL_OT_setup_scene(bpy.types.Operator):
    """
    Set-up scene units for better compatibility of exported objects with Unreal Engine.
    (It sets scene units to 0.01 and makes sure the system is set to 'METRIC'). 
    """

    bl_idname = 'metareforge_lite.setup_scene'
    bl_label = 'Setup Scene Units'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = bpy.context.scene
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.scale_length = 0.01
        self.report({'INFO'}, 'Scene units are set up.')
        return {'FINISHED'}
    

def register():
    bpy.utils.register_class(MRFL_OT_setup_scene)  


def unregister():
    bpy.utils.unregister_class(MRFL_OT_setup_scene)  


if __name__ == '__main__':
    register()
