import bpy
import os
import traceback
from ..utils.config import get_main_prop
from ..utils.blender.object import ensure_objects_visible
from ..utils.blender.keep_state import EditorState
from ..utils.blender.obj_io import export_as_obj


class MRFL_OT_export_template_meshes(bpy.types.Operator):
    """TODO: Docstring"""

    bl_idname = 'metareforge_lite.export_template_meshes'
    bl_label = 'Setup Scene'
    bl_options = {'REGISTER', 'UNDO'}
    

    objects_to_export = []
    output_path = ''
    initial_state = None
    step = 0
    num_steps = 1
    is_running = False
    timer = None
    status = ''

    def invoke(self, context, event):
        config = get_main_prop(context=context)
        try:
            self.__class__.initial_state = EditorState.capture_current_state()
            self.__class__.output_path = bpy.path.abspath(config.export_path)
            objs = [
                config.head_template,
                config.body_template,
                config.left_eye_template,
                config.right_eye_template,
                config.teeth_template
            ]

            self.__class__.objects_to_export.clear()
            for obj in objs:
                if obj is not None:
                    self.__class__.objects_to_export.append(obj)

            ensure_objects_visible(self.__class__.objects_to_export)

            # Init progress bar parameters
            self.__class__.step = 0
            config.export_progress = 0.0
            self.__class__.is_running = True
            self.__class__.num_steps = len(self.__class__.objects_to_export)
            context.view_layer.update()
            
            # Add handler and timer
            self.__class__.timer = context.window_manager.event_timer_add(0.5, window=context.window)
            context.window_manager.modal_handler_add(self)
            
            return {'RUNNING_MODAL'}
        except Exception as e:
            print(f'{self.__class__.__name__} operation failed: {str(e)}')
            print(traceback.format_exc())
            self.report({'ERROR'}, f'Export failed: {str(e)}')
            
            self.restore(context=context)
            return {'CANCELLED'}
    
    def modal(self, context, event):
        if self.__class__.objects_to_export:
            obj = self.__class__.objects_to_export.pop(0)
            try:
                self.__class__.status = f'Exporting: {obj.name}'
                path = os.path.join(self.__class__.output_path, f'{obj.name}.obj')
                export_as_obj(context=context, obj=obj, file_path=path, up_axis='Z', forward_axis='Y')
                return {'RUNNING_MODAL'}
            except Exception as e:
                print(f'{self.__class__.__name__} operation failed: {str(e)}')
                print(traceback.format_exc())
                self.report({'ERROR'}, f'Export failed: {str(e)}')
                
                self.restore(context=context)
                return {'CANCELLED'}
        else:
            # FINISH AS THE IS NO OBJECT TO EXPORT
            self.restore(context=context)
            return {'FINISHED'}
    
    def restore(self, context: bpy.types.Context):
        self.__class__.is_running = False
        self.__class__.status = f'Done'
        config = get_main_prop(context=context)
        config.export_progress = 0.0
        context.area.tag_redraw()
        
        # Restore original editor state
        if self.__class__.initial_state:
            self.__class__.initial_state.try_restore()

        # Remove timer
        if self.__class__.timer:
            context.window_manager.event_timer_remove(self.__class__.timer)
            self.__class__.timer = None

    

def register():
    bpy.utils.register_class(MRFL_OT_export_template_meshes)  


def unregister():
    bpy.utils.unregister_class(MRFL_OT_export_template_meshes)  


if __name__ == '__main__':
    register()
