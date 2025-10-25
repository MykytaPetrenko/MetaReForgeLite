import bpy
import os
import json
import traceback
from bpy.types import Event, Context
from typing import Union, Set
from  mathutils import Vector
from ..utils.mesh_json import get_standard_meshes_dir, dict_to_mesh
from ..utils.blender.collection import link_object_to_collection
from ..utils.blender.keep_state import EditorState
from ..utils.config import get_main_prop
from ..uv_link.geometry import uv_tranfer_initialize_triangles, uv_transfer_initialize_target_vertices, TransferTrianglesCollection
from ..uv_link.interpolation import get_transformed
from ..globals import TEMPLATE_MESHES_COLLECTION


HEAD_MESH_NAME = 'head'
BODY_MESH_NAME = 'body'
TEETH_MESH_NAME = 'teeth'
LEFT_EYE_MESH_NAME = 'left_eye'
RIGHT_EYE_MESH_NAME = 'right_eye'

DEFAULT_MESHES = [
    HEAD_MESH_NAME,
    BODY_MESH_NAME,
    TEETH_MESH_NAME,
    LEFT_EYE_MESH_NAME,
    RIGHT_EYE_MESH_NAME
]


def load_template_mesh(context: bpy.types.Context, mesh_name: str) -> bpy.types.Object:
    # Build file path
    meshes_dir = get_standard_meshes_dir()
    filename = f"{mesh_name}.json"
    filepath = os.path.join(meshes_dir, filename)

    # Check if file exists
    if not os.path.exists(filepath):
        raise Exception(f"File {filename} not found")
    
    try:
        # Load JSON data
        with open(filepath, 'r') as f:
            mesh_data = json.load(f)
        
        # Create mesh from data
        mesh = dict_to_mesh(mesh_data, mesh_name)
        
        # Create object and link to scene
        obj = bpy.data.objects.new(mesh_name, mesh)
        context.collection.objects.link(obj)
    except Exception as e:
        raise Exception(f"Failed to load mesh: {str(e)}")
    return obj

def transfer_shape(target_object: bpy.types.Object, source_object: bpy.types.Object):
    source_triangles = uv_tranfer_initialize_triangles(obj=source_object)
    target_vertices = uv_transfer_initialize_target_vertices(obj=target_object)

    target_mesh = target_object.data
    
    triangles_collection = TransferTrianglesCollection(source_triangles)
    new_target_vertices = get_transformed(triangles_collection, target_vertices)
    invalid_vertices = []
    for i, vert_options in new_target_vertices.items():
        if len(vert_options) != 0:
            cum_co = Vector((0.0, 0.0, 0.0))
            cum_weight = 0.0
            for co, w in vert_options:
                cum_co += co * w
                cum_weight += w
            target_mesh.vertices[i].co = cum_co / cum_weight
        else:
            invalid_vertices.append(i)


class MRFL_OT_generate_template_meshes(bpy.types.Operator):
    bl_idname = "metareforge_lite.genearate_template_meshes"
    bl_label = "Generate Template Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    is_running = False
    step = 0
    num_steps = 0
    status = ''
    initial_state = None

    _import_tasks = []
    _transfer_tasks = []
    _mrf_meshes = {}
    _template_meshes = {}
    _remove_old_templates = False
    timer = None

    @classmethod
    def get_progress(cls) -> float:
        if cls.num_steps == 0:
            return 0
        else:
            return cls.step / cls.num_steps * 100

    def invoke(self, context: Context, event: Event) -> Union[Set[str], Set[int]]:
        try:
            self.__class__.initial_state = EditorState.capture_current_state()
            self.__class__.is_running =True
            config = get_main_prop(context)
            
            self.__class__.step = 0
            self.__class__._remove_old_templates = config.remove_old_templates
            config.conformal_init_percentage = 0.0
            self.__class__.status = 'Started'


            self.__class__._mrf_meshes = {
                BODY_MESH_NAME: config.body,
                HEAD_MESH_NAME: config.body,
                TEETH_MESH_NAME: config.teeth,
                LEFT_EYE_MESH_NAME: config.left_eye,
                RIGHT_EYE_MESH_NAME: config.right_eye
            }

            self.__class__._mrf_meshes = {
                k: v for k, v in self.__class__._mrf_meshes.items() if v is not None
            }

            self.__class__._import_tasks = list(self.__class__._mrf_meshes.keys())
            self.__class__._transfer_tasks = list(self.__class__._mrf_meshes.keys())

            self.__class__.num_steps = len(self.__class__._import_tasks) + \
                len(self.__class__._transfer_tasks)
            
            context.view_layer.update()
                
            # Add handler and timer
            self.__class__.timer = context.window_manager.event_timer_add(0.5, window=context.window)
            context.window_manager.modal_handler_add(self)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        except:
            self.end_routine(context=context, status='Error')
            return {'CANCELLED'}


    def modal(self, context, event):    
        try: 
            config = get_main_prop(context)

            if event.type != "TIMER":
                return {'RUNNING_MODAL'}

            if self.__class__._import_tasks:
                mesh_name = self.__class__._import_tasks.pop()
                template_mesh = load_template_mesh(context, mesh_name)
                self.__class__._template_meshes[mesh_name] = template_mesh
                self.__class__.step += 1
                config.conformal_init_percentage = self.__class__.get_progress()
                self.__class__.status = f'Loaded: "{mesh_name}"'

                # Assign the template mesh to corresponding property
                old_template = None
                if mesh_name == 'head':
                    old_template = config.head_template
                    config.head_template = template_mesh
                elif mesh_name == 'body':
                    old_template = config.body_template
                    config.body_template = template_mesh
                elif mesh_name == 'left_eye':
                    old_template = config.left_eye_template
                    config.left_eye_template = template_mesh
                elif mesh_name == 'right_eye':
                    old_template = config.right_eye_template
                    config.right_eye_template = template_mesh
                elif mesh_name == 'teeth':
                    old_template = config.teeth_template
                    config.teeth_template = template_mesh

                if self.__class__._remove_old_templates and old_template:
                    bpy.data.objects.remove(old_template, do_unlink=True)
                
                link_object_to_collection(template_mesh, TEMPLATE_MESHES_COLLECTION, overwrite=True)
                
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            if self.__class__._transfer_tasks:
                mesh_name = self.__class__._transfer_tasks.pop()
                template_mesh = self.__class__._template_meshes[mesh_name]
                mrf_mesh = self.__class__._mrf_meshes[mesh_name]
                transfer_shape(template_mesh, mrf_mesh)
                self.__class__.step += 1
                context.area.tag_redraw()
                config.conformal_init_percentage = self.__class__.get_progress()
                self.__class__.status = f'Shaped "{mesh_name}"'
                if self.__class__._transfer_tasks:
                    return {'RUNNING_MODAL'}
                else:
                    self.end_routine(context=context, status='Done')
                    return {'FINISHED'}
        except Exception as ex:
            print(f'Exception: {str(ex)}')
            print(traceback.format_exc())
            
            self.end_routine(context=context, status='Error')
            return {'CANCELLED'}

        self.end_routine(context=context, status='Done')
        return {'FINISHED'}
    
    def end_routine(self, context: bpy.types.Context, status: str = 'Done'):
        self.__class__.is_running = False
        self.__class__.status = status
        config = get_main_prop(context=context)
        config.conformal_init_percentage = 0.0
        context.area.tag_redraw()
        
        # Restore original editor state
        if self.__class__.initial_state:
            self.__class__.initial_state.try_restore()

        # Remove timer
        if self.__class__.timer:
            context.window_manager.event_timer_remove(self.__class__.timer)
            self.__class__.timer = None


classes = [MRFL_OT_generate_template_meshes]  

def register():
    for cl in classes:
        bpy.utils.register_class(cl)  

def unregister():
    for cl in classes:
        bpy.utils.unregister_class(cl)


if __name__ == '__main__':
    register()