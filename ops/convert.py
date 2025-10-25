import os
import bpy
import time
import json
from mathutils import Vector
from .mesh_io import mesh_to_dict, dict_to_mesh
from ..uv_link.geometry import (
    uv_transfer_initialize_target_vertices,
    uv_tranfer_initialize_triangles,
    TransferTrianglesCollection
)
from ..uv_link.interpolation import get_transformed
from ..props.converter_prop import TRANSFER_PRESETS_PATH
from ..utils.config import get_main_prop, get_converter_prop
from ..globals import MRFL_EDIT_MESHES_COLLECTION
from ..utils.blender.collection import get_collection



def get_vertex_to_uv_mapping(obj):
    """
    Get a mapping from vertex index to UV coordinates.
    Uses the first UV coordinate found for each vertex.
    
    Args:
        obj:
    
    Returns:
        dict: {vertex_index: (u, v)} mapping
    """    
    if not obj or obj.type != 'MESH':
        print("No valid mesh object found")
        return {}
    
    # Get mesh data
    mesh = obj.data
    
    # Check if UV map exists
    if not mesh.uv_layers:
        print("No UV layers found on the mesh")
        return {}
    
    # Use the active UV layer (or first one)
    uv_layer = mesh.uv_layers.active or mesh.uv_layers[0]
    
    # Dictionary to store vertex index -> UV mapping
    vertex_to_uv = {}
    
    # Iterate through all polygons and their loops
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vertex_idx = loop.vertex_index
            
            # Get UV coordinate for this loop
            uv_coord = uv_layer.data[loop_idx].uv
            
            # Store only the first UV coordinate found for each vertex
            if vertex_idx not in vertex_to_uv:
                vertex_to_uv[vertex_idx] = (uv_coord.x, uv_coord.y)
    
    return vertex_to_uv

# THIS OPERATOR IS REPLACED WITH SIMILAR WHICH HAS A PROGRESS BAR
# class MRFL_save_wrapping_preset(bpy.types.Operator):
#     """Saves transfer preset"""
#     bl_idname = 'metareforge_lite.create_wrapping_preset'
#     bl_label = 'Create Wrapping Preset [Test]'
#     bl_options = {'REGISTER', 'UNDO'}

#     preset_category: bpy.props.StringProperty(
#         name='Preset Category', default='Custom', options={'HIDDEN'})
#     preset_name: bpy.props.StringProperty(
#         name='Preset Name', default='new', options={'HIDDEN'})

#     def execute(self, context):
#         converter_prop = get_converter_prop(context=context)

#         source_obj = converter_prop.new_preset_source_object
#         target_obj = converter_prop.new_preset_target_object
        
#         if not source_obj or not target_obj:
#             self.report({'ERROR'}, 'Please select both source and target objects')
#             return {'CANCELLED'}
        
        
#         target_mesh = target_obj.data
        
#         if source_obj.type != 'MESH' or target_obj.type != 'MESH':
#             self.report({'ERROR'}, 'Both objects must be meshes')
#             return {'CANCELLED'}
        
#         # Start timing
#         start_time = time.time()

#         source_triangles = uv_tranfer_initialize_triangles(source_obj, mode=1)
#         source_triangles_collection = TransferTrianglesCollection(source_triangles)
#         target_inputs = uv_transfer_initialize_target_vertices(target_obj, mode=1)

#         proxy_uvs = get_transformed(source_triangles_collection, target_inputs)

#         data = mesh_to_dict(target_mesh, co_3d=False, co_uv=True)

#         proxy_uvs_list = []
#         for vert_index in range(len(target_mesh.vertices)):
#             uv, weight = proxy_uvs[vert_index][0]
#             uv = (uv[0], uv[1])
#             proxy_uvs_list.append(uv)

#         data['proxy_uvs'] = proxy_uvs_list

#         preset_folder = os.path.join(TRANSFER_PRESETS_PATH, self.preset_category)
#         os.makedirs(preset_folder, exist_ok=True)
#         save_path = os.path.join(preset_folder, f'{self.preset_name}.json')
#         with open(save_path, 'w') as f:
#             json.dump(data, f, indent=2)
        
#         # Report timing
#         elapsed_time = time.time() - start_time
#         self.report({'INFO'}, f'Preset creation completed in {elapsed_time:.2f} seconds')
#         return {'FINISHED'}
    

class MRFL_convert_to_edit_meshes(bpy.types.Operator):
    """Daz to metahuman"""
    bl_idname = 'metareforge_lite.convert_to_edit_meshes'
    bl_label = '[TEST] Convert to Edit Meshes'
    bl_options = {'REGISTER', 'UNDO'}

    preset_category: bpy.props.StringProperty(
        name='Preset Category', default='Custom', options={'HIDDEN'})
    preset_name: bpy.props.StringProperty(
        name='Preset Name', default='new', options={'HIDDEN'})

    selective_smoothing: bpy.props.BoolProperty(
        name='Selective Smooth', default=True, options={'HIDDEN'})
    selective_smoothing_factor: bpy.props.FloatProperty(
        name='Selective Smoothing Factor', default=0.25, min=0.0, max=1.0, options={'HIDDEN'})
    selective_smoothing_repeats: bpy.props.IntProperty(
        name='Selective Smoothing Repeats', default=30, min=0, max=50, options={'HIDDEN'})

    full_smoothing: bpy.props.BoolProperty(
        name='Smooth All', default=True, options={'HIDDEN'})
    full_smoothing_factor: bpy.props.FloatProperty(
        name='Smoothing Factor', default=0.05, min=0.0, max=1.0, options={'HIDDEN'})
    full_smoothing_repeats: bpy.props.IntProperty(
        name='Smoothing Repeats', default=30, min=0, max=50, options={'HIDDEN'})

    def execute(self, context):
        converter_prop = context.scene.mrfl_converter_prop
        source_obj = converter_prop.source_object

        triangles = uv_tranfer_initialize_triangles(source_obj, mode=0)
        triangles_collection = TransferTrianglesCollection(triangles)
        
        preset_subfolder = os.path.join(TRANSFER_PRESETS_PATH, self.preset_category)
        path = os.path.join(preset_subfolder, f'{self.preset_name}.json')
        with open(path, 'r') as f:
            data = json.load(f)

        tag = data.get('tag', None)

        mesh_name = self.preset_name
        mesh = dict_to_mesh(data, name=mesh_name)
        obj = bpy.data.objects.new(mesh_name, mesh)
        collection = get_collection(MRFL_EDIT_MESHES_COLLECTION, ensure_exist=True)
        collection.objects.link(obj)
        
        for vert_index, proxy_uv in enumerate(data['proxy_uvs']):
            co = triangles_collection.transfer_coordinates_using_closest_triangle(Vector(proxy_uv).to_3d())
            mesh.vertices[vert_index].co = co

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        mesh.update()
        context.view_layer.objects.active = obj

        if self.selective_smoothing:
            factor = self.selective_smoothing_factor
            repeats = self.selective_smoothing_repeats
            threshold = 0.1
            vertex_groups = data.get('vertex_groups', None)
            if vertex_groups:
                smoothing_group = vertex_groups.get('smoothing', None)
                if smoothing_group:
                    # Clear selection
                    bpy.ops.object.mode_set(mode='EDIT')    # Switch to edit mode
                    bpy.ops.mesh.select_mode(type='VERT')   # Select edge selection mode
                    bpy.ops.mesh.select_all(action='DESELECT')  # Deselect all edges
                    bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to object mode

                    smoothing_indices = set()
                    for index, weight in smoothing_group:
                        if weight >= threshold:
                            smoothing_indices.add(index)
                    for v in mesh.vertices:
                        if v.index in smoothing_indices:
                            v.select = True

                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.vertices_smooth(factor=factor, repeat=repeats)
                    bpy.ops.object.mode_set(mode='OBJECT')            

        if self.full_smoothing:
            factor = self.full_smoothing_factor
            repeats = self.full_smoothing_repeats
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.vertices_smooth(factor=factor, repeat=repeats)
            bpy.ops.object.mode_set(mode='OBJECT')

        # Assign the new object as an edit mesh
        main_prop = get_main_prop(context=context)
        if tag == 'body':
            main_prop.body = obj
        elif tag == 'teeth':
            main_prop.teeth = obj
        elif tag == 'left_eye':
            main_prop.left_eye = obj
        elif tag == 'right_eye':
            main_prop.right_eye = obj

        return {'FINISHED'}


# Registration
classes = [
    MRFL_convert_to_edit_meshes
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
