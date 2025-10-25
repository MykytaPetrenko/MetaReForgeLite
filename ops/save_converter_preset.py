import os
import bpy
import time
import json
import traceback
from .mesh_io import mesh_to_dict
from ..uv_link.geometry import (
    uv_transfer_initialize_target_vertices,
    uv_tranfer_initialize_triangles,
    TransferTrianglesCollection
)
from ..props.converter_prop import TRANSFER_PRESETS_PATH
from ..utils.config import get_converter_prop


class MRFL_OT_create_converter_preset(bpy.types.Operator):
    """Saves transfer cpreset with progress bar"""
    bl_idname = 'metareforge_lite.create_converter_preset'
    bl_label = 'Create Converter Preset [Test]'
    bl_options = {'REGISTER', 'UNDO'}

    # Static class attributes for progress tracking and UI
    is_running = False
    step = 0
    num_steps = 0
    status = ""
    
    # Internal working attributes
    timer = None
    process_generator = None
    start_time = 0
    source_obj = None
    target_obj = None
    converter_prop = None
    proxy_uvs = None
    source_triangles_collection = None
    smoothing_vertex_group = None
    preset_tag = ''
    
    preset_category: bpy.props.StringProperty(
        name='Preset Category', default='Custom', options={'HIDDEN'})
    preset_name: bpy.props.StringProperty(
        name='Preset Name', default='new', options={'HIDDEN'})
    
    
    
    @classmethod
    def poll(cls, context):
        # Don't allow multiple instances to run
        return not cls.is_running

    def invoke(self, context, event):
        try:
            converter_prop = get_converter_prop(context=context)
            self.__class__.converter_prop = converter_prop
            
            self.__class__.source_obj = converter_prop.new_preset_source_object
            self.__class__.target_obj = converter_prop.new_preset_target_object
            self.__class__.smoothing_vertex_group = converter_prop.smoothing_vertex_group
            self.__class__.preset_tag = converter_prop.new_preset_tag
            
            if not self.__class__.source_obj or not self.__class__.target_obj:
                self.report({'ERROR'}, 'Please select both source and target objects')
                return {'CANCELLED'}
            
            if self.__class__.source_obj.type != 'MESH' or self.__class__.target_obj.type != 'MESH':
                self.report({'ERROR'}, 'Both objects must be meshes')
                return {'CANCELLED'}

            # Initialize static attributes
            self.__class__.is_running = True
            self.__class__.step = 0
            self.__class__.num_steps = 100
            self.__class__.status = "Preparing..."
            self.__class__.start_time = time.time()
            
            # Reset progress
            context.scene.mrfl_converter_prop.preset_creation_progress = 0.0
            
            # Initialize process generator
            self.__class__.process_generator = self.process_preset()
            
            # Start timer
            wm = context.window_manager
            self.__class__.timer = wm.event_timer_add(0.01, window=context.window)
            wm.modal_handler_add(self)
            
            return {'RUNNING_MODAL'}
            
        except Exception as e:
            print(f'{self.__class__.__name__} operation failed: {str(e)}')
            print(traceback.format_exc())
            self.report({'ERROR'}, f'Preset creation failed: {str(e)}')
            
            self.finish(context)
            return {'CANCELLED'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                # Execute next step of the process
                next(self.__class__.process_generator)
                
                # Update UI progress
                context.scene.mrfl_converter_prop.preset_creation_progress = (
                    self.__class__.step / self.__class__.num_steps * 100.0
                )
                
                # Force UI update
                if context.area:
                    context.area.tag_redraw()
                
                return {'PASS_THROUGH'}
                
            except StopIteration:
                # Process completed successfully
                elapsed_time = time.time() - self.__class__.start_time
                self.report({'INFO'}, f'Preset creation completed in {elapsed_time:.2f} seconds')
                self.finish(context)
                return {'FINISHED'}
                
            except Exception as e:
                # Handle errors
                print(f'{self.__class__.__name__} operation failed: {str(e)}')
                print(traceback.format_exc())
                self.report({'ERROR'}, f'Error during preset creation: {str(e)}')
                
                self.finish(context)
                return {'CANCELLED'}
        
        elif event.type == 'ESC':
            # User cancelled
            self.report({'INFO'}, 'Preset creation cancelled by user')
            self.finish(context)
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}

    def finish(self, context):
        """Clean up resources and reset state - always called"""
        self.__class__.is_running = False
        self.__class__.step = 0
        self.__class__.num_steps = 0
        self.__class__.status = "Done"
        
        # Reset progress
        context.scene.mrfl_converter_prop.preset_creation_progress = 0.0
        
        # Force UI update
        if context.area:
            context.area.tag_redraw()
        
        # Remove timer
        if self.__class__.timer:
            wm = context.window_manager
            wm.event_timer_remove(self.__class__.timer)
            self.__class__.timer = None
        
        # Clear working attributes
        self.__class__.process_generator = None
        self.__class__.source_obj = None
        self.__class__.target_obj = None
        self.__class__.converter_prop = None
        self.__class__.proxy_uvs = None
        self.__class__.source_triangles_collection = None
        self.__class__.smoothing_vertex_group = None

    def process_preset(self):
        """Generator that yields control back to Blender during heavy operations"""
        
        # Phase 1: Preparing source triangles (0-50%)
        self.__class__.status = "Preparing source triangles..."
        self.__class__.num_steps = 100
        
        # Initialize source triangles with progress updates
        yield from self.initialize_source_triangles_with_progress()
        
        # Phase 2: Calculate new coordinates (50-90%)
        self.__class__.status = "Calculating target coordinates..."
        
        # Initialize target inputs (quick step)
        target_inputs = uv_transfer_initialize_target_vertices(self.__class__.target_obj, mode=1)
        
        # Get transformed coordinates with progress updates
        yield from self.get_transformed_with_progress(target_inputs)
        
        # Phase 3: Save Preset (90-100%)
        self.__class__.status = "Saving preset..."
        yield from self.save_preset_with_progress()

    def initialize_source_triangles_with_progress(self):
        """Initialize source triangles with progress updates"""
        # Simulate progress for source triangle initialization
        total_steps = 50
        for i in range(total_steps):
            self.__class__.step = i
            
            if i == 0:
                # Actually initialize triangles on first step
                self.__class__.source_triangles = uv_tranfer_initialize_triangles(self.__class__.source_obj, mode=1)
            elif i == total_steps - 1:
                # Create collection on last step
                self.__class__.source_triangles_collection = TransferTrianglesCollection(self.__class__.source_triangles)
            
            yield  # Yield control back to Blender
        
        self.__class__.step = 50

    def get_transformed_with_progress(self, target_inputs):
        """Get transformed coordinates with progress updates"""
        self.__class__.step = 50  # Start from 50%
        
        # Initialize result dictionary
        proxy_uvs = dict()
        
        # Process vertices in batches to show progress
        vertices_list = list(target_inputs.items())
        total_vertices = len(vertices_list)
        batch_size = max(1, total_vertices // 40)  # 40 steps for this phase (50-90%)
        
        for batch_start in range(0, total_vertices, batch_size):
            batch_end = min(batch_start + batch_size, total_vertices)
            
            # Process batch
            for vertex_index, uv_loops in vertices_list[batch_start:batch_end]:
                options = list()
                for uv in uv_loops:
                    new_3d_co = self.__class__.source_triangles_collection.transfer_coordinates_using_closest_triangle(uv.co)
                    if new_3d_co:
                        options.append((new_3d_co, uv.weight))
                proxy_uvs[vertex_index] = options
            
            # Update progress
            progress = batch_end / total_vertices
            self.__class__.step = 50 + int(progress * 40)
            
            yield  # Yield control back to Blender
        
        self.__class__.proxy_uvs = proxy_uvs
        self.__class__.step = 90

    def save_preset_with_progress(self):
        """Save preset with progress updates"""
        self.__class__.status = "Finalizing and saving..."
        
        # Create mesh data
        target_mesh = self.__class__.target_obj.data
        data = mesh_to_dict(target_mesh, co_3d=False, co_uv=True)
        if self.smoothing_vertex_group != '':
            smoothing_group = data['vertex_groups'].get(self.smoothing_vertex_group, None)
            if smoothing_group:
                data['verteg_groups'] = {'smoothing': smoothing_group}
            else:
                raise Exception(f'Smothing group "{self.smoothing_vertex_group}" is not found')
        self.__class__.step = 92
        yield
        
        # Process proxy UVs
        proxy_uvs_list = []
        for vert_index in range(len(target_mesh.vertices)):
            if vert_index in self.__class__.proxy_uvs and self.__class__.proxy_uvs[vert_index]:
                uv, weight = self.__class__.proxy_uvs[vert_index][0]
                uv = (uv[0], uv[1])
                proxy_uvs_list.append(uv)
            else:
                proxy_uvs_list.append((0.0, 0.0))  # Default UV if missing
        
        data['proxy_uvs'] = proxy_uvs_list
        
        self.__class__.step = 96
        yield
        
        data['tag'] = self.preset_tag
        # Save to file
        preset_folder = os.path.join(TRANSFER_PRESETS_PATH, self.preset_category)
        os.makedirs(preset_folder, exist_ok=True)
        save_path = os.path.join(preset_folder, f'{self.preset_name}.json')
        
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.__class__.step = 100
        yield


def register():
    bpy.utils.register_class(MRFL_OT_create_converter_preset)
    

def unregister():
    bpy.utils.unregister_class(MRFL_OT_create_converter_preset)