import bpy

class MRFL_MessageBoxOperator(bpy.types.Operator):
    bl_idname = "metareforge_lite.messagebox"
    bl_label = "Message"
    bl_options = {'INTERNAL'}  # This will hide the Cancel button

    message: bpy.props.StringProperty(name="message")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)  # You can adjust width if needed

    def draw(self, context):
        self.layout.label(text=self.message)

    def check(self, context):
        return True  # Forces an instant redraw and close on any change

def show_message_box(message="", title="Message Box", icon='INFO'):
    bpy.ops.meta_reforge.messagebox('INVOKE_DEFAULT', message=message)

def register():
    bpy.utils.register_class(MRFL_MessageBoxOperator)

def unregister():
    bpy.utils.unregister_class(MRFL_MessageBoxOperator)
