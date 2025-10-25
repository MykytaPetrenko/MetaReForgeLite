import bpy
import traceback
from collections import defaultdict
from bpy_extras.io_utils import ImportHelper
import os
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from ..utils.blender.unsorted import (
    join_objects,
    merge_by_distance,
    calc_adaptive_merge_distance
)
from ..utils.blender.collection import (
    get_collection,
    link_objects_to_collection,
    collection_set_exclude
)
from ..utils.blender.fbx_io import import_fbx
from ..utils.blender.separate_by_material import separate_by_material
from ..utils.blender.unsorted import duplicate_mesh_light, duplicate_object
from ..utils.config import get_main_prop
from ..utils.blender.collection import link_object_to_collection
from ..globals import (
    FBX_HEAD_COLLECTION,
    FBX_BODY_COLLECTION,
    ADDON_DIRECTORY,
    MRFL_EDIT_MESHES_COLLECTION
)
from ..enums import BodyPart
from .message_box import show_message_box


def sort_objects_by_base_name(objects):
    def get_base_name(obj):
        return obj.name.split('.')[0]
    
    return sorted(objects, key=get_base_name)



MESH_IDS = {
    'head',
    'teeth',
    'saliva',
    'eyeLeft',
    'eyeRight',
    'eyeshell',
    'eyelashes',
    'eyeEdge',
    'cartilage'
}

FBX_SHADER_INDICES = {
    0: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_saliva_shader',
        3: 'shader_eyeLeft_shader',
        4: 'shader_eyeRight_shader',
        5: 'shader_eyeshell_shader',
        6: 'shader_eyelashes_shader',
        7: 'shader_eyeEdge_shader',
        8: 'shader_cartilage_shader'
    },
    1: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_saliva_shader',
        3: 'shader_eyeLeft_shader',
        4: 'shader_eyeRight_shader',
        5: 'shader_eyeshell_shader',
        6: 'shader_eyelashes_shader',
        7: 'shader_eyeEdge_shader',
        8: 'shader_cartilage_shader'
    },
    2: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_saliva_shader',
        3: 'shader_eyeLeft_shader',
        4: 'shader_eyeRight_shader',
        5: 'shader_eyeshell_shader',
        6: 'shader_eyelashes_shader',
        7: 'shader_eyeEdge_shader'
    },
    3: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_eyeLeft_shader',
        3: 'shader_eyeRight_shader',
        4: 'shader_eyeshell_shader',
        5: 'shader_eyelashes_shader',
        6: 'shader_eyeEdge_shader'
    },
    4: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_eyeLeft_shader',
        3: 'shader_eyeRight_shader',
        4: 'shader_eyeshell_shader'
    },
    5: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_eyeLeft_shader',
        3: 'shader_eyeRight_shader'
    },
    6: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_eyeLeft_shader',
        3: 'shader_eyeRight_shader'
    },
    7: {
        0: 'shader_head_shader',
        1: 'shader_teeth_shader',
        2: 'shader_eyeLeft_shader',
        3: 'shader_eyeRight_shader'
    }
}

FBX_MATERIAL_INDEX_EDIT_ID_MAP = {
    0: {
        0: 'skin',
        1: 'teeth',
        2: 'saliva',
        3: 'eyeLeft',
        4: 'eyeRight',
        5: 'eyeshell',
        6: 'eyelashes',
        7: 'eyeEdge',
        8: 'cartilage'
    },
    1: {
        0: 'skin',
        1: 'teeth',
        2: 'saliva',
        3: 'eyeLeft',
        4: 'eyeRight',
        5: 'eyeshell',
        6: 'eyelashes',
        7: 'eyeEdge',
        8: 'cartilage'
    },
    2: {
        0: 'skin',
        1: 'teeth',
        2: 'saliva',
        3: 'eyeLeft',
        4: 'eyeRight',
        5: 'eyeshell',
        6: 'eyelashes',
        7: 'eyeEdge'
    },
    3: {
        0: 'skin',
        1: 'teeth',
        2: 'eyeLeft',
        3: 'eyeRight',
        4: 'eyeshell',
        5: 'eyelashes',
        6: 'eyeEdge'
    },
    4: {
        0: 'skin',
        1: 'teeth',
        2: 'eyeLeft',
        3: 'eyeRight',
        4: 'eyeshell'
    },
    5: {
        0: 'skin',
        1: 'teeth',
        2: 'eyeLeft',
        3: 'eyeRight'
    },
    6: {
        0: 'skin',
        1: 'teeth',
        2: 'eyeLeft',
        3: 'eyeRight'
    },
    7: {
        0: 'skin',
        1: 'teeth',
        2: 'eyeLeft',
        3: 'eyeRight'
    }
}


HEAD_EDIT_ID2MAT_MAP = {
    'default': {'name': 'default', 'rgba': (0.3, 0.3, 0.3, 1.0), 'roughness': 0.5, 'metallic': 0.0},
    'skin': {'name': 'shader_head_shader', 'rgba': (0.3, 0.3, 0.3, 1.0), 'roughness': 0.5, 'metallic': 0.0},
    'teeth': {
        'name': 'shader_teeth_shader',
        'rgba': (0.3, 0.3, 0.3, 1.0),
        'roughness': 0.1,
        'metallic': 0.0,
        'texture': os.path.join(ADDON_DIRECTORY, 'textures', 'teeth_simple.png')
    },
    'saliva': {
        'name': 'shader_saliva_shader',
        'rgba': (0.3, 0.3, 0.3, 0.25),
        'roughness': 0.1,
        'metallic': 0.0
    },
    'eyeLeft': {
        'name': 'shader_eyeLeft_shader',
        'rgba': (1.0, 1.0, 1.0, 1.0),
        'roughness': 0.1,
        'metallic': 0.0,
        'texture': os.path.join(ADDON_DIRECTORY, 'textures', 'eye_simple.png')
    },
    'eyeRight': {
        'name': 'shader_eyeRight_shader',
        'rgba': (1.0, 1.0, 1.0, 1.0),
        'roughness': 0.1,
        'metallic': 0.0,
        'texture': os.path.join(ADDON_DIRECTORY, 'textures', 'eye_simple.png')
    },
    'eyeshell': {'name': 'shader_eyeshell_shader', 'rgba': (0.3, 0.3, 0.3, 0.1), 'roughness': 0.1, 'metallic': 0.0},
    'eyelashes': {'name': 'shader_eyelashes_shader', 'rgba': (0.3, 0.3, 0.3, 1.0), 'roughness': 0.7, 'metallic': 0.0},
    'eyeEdge': {'name': 'shader_eyeEdge_shader', 'rgba': (0.3, 0.3, 0.3, 0.5), 'roughness': 0.1, 'metallic': 0.0},
    'cartilage': {'name': 'shader_cartilage_shader', 'rgba': (0.3, 0.3, 0.3, 0.5), 'roughness': 0.3, 'metallic': 0.0}
}

BODY_EDIT_ID2MAT_MAP = {
    'default': {'name': 'default', 'rgba': (0.3, 0.3, 0.3, 1.0), 'roughness': 0.5, 'metallic': 0.0},
    'skin': {'name': 'M_BodySynthesized', 'rgba': (0.3, 0.3, 0.3, 1.0), 'roughness': 0.5, 'metallic': 0.0}
}


DEFAULT_HEAD_FBX_TEMPLATE = r'.*LOD<LEVEL_INDEX>'
MRF_HEAD_FBX_TEMPLATE = r'.*lod<LEVEL_INDEX>_mesh'

def remove_empty_material_slots(obj):
    """
    Removes material slots from a mesh object if they are not assigned to any face.

    This function iterates through the material slots of a mesh object and identifies
    slots that are not referenced by any face. These unused material slots are then
    removed to optimize the object's material list.

    Args:
        obj (bpy.types.Object): The Blender object from which to remove empty material slots.
                                Must be of type 'MESH'.

    Returns:
        None: The function modifies the object in place and does not return a value.
    """
    if obj.type != 'MESH' or not obj.material_slots:
        return
    
    # Ensure the object is selected and active
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    mesh = obj.data
    used_slots = {face.material_index for face in mesh.polygons}  # Get used material indices
    all_slots = set(range(len(obj.material_slots)))  # All material slot indices
    
    unused_slots = all_slots - used_slots  # Identify unused slots
    
    # Remove slots in reverse order to avoid index shifting issues
    for slot_index in sorted(unused_slots, reverse=True):
        obj.active_material_index = slot_index  # Select the slot
        bpy.ops.object.material_slot_remove()  # Remove it


def sort_lods(objects: List[bpy.types.Object]) -> Dict[int, List[bpy.types.Object]]:
    """
    Sorts mesh objects into a dictionary based on their Level of Detail (LOD) suffix.

    This function searches for "lodX" in object names (case-insensitive) and 
    groups them accordingly.

    Args:
        objects (List[bpy.types.Object]): List of Blender objects to filter and sort.

    Returns:
        Dict[int, List[bpy.types.Object]]: Dictionary where keys are LOD levels (integers) 
                                           and values are lists of matching objects.
    """
    lod_groups = defaultdict(list)
    
    for obj in objects:
        if obj.type == 'MESH':
            name_lower = obj.name.lower()  # Convert to lowercase for case-insensitive matching
            for lod_level in range(10):  # Checking LOD0 to LOD9
                if f'lod{lod_level}' in name_lower:
                    lod_groups[lod_level].append(obj)
                    break  # Stop checking once matched

    return dict(lod_groups)


def remove_non_mesh_and_armature(objects: List[bpy.types.Object]) -> None:
    """Removes all objects that are not of type 'MESH' or 'ARMATURE' from the scene.

    Args:
        objects (List[bpy.types.Object]): List of Blender objects to filter.
    """
    for obj in objects:
        if obj.type not in {'MESH', 'ARMATURE'}:
            bpy.data.objects.remove(obj, do_unlink=True)
        

def set_material_texture(material: bpy.types.Material, image_path: str) -> None:
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Clear all nodes to start fresh
    for node in nodes:
        nodes.remove(node)

    # Create an Image Texture node
    texture_node = nodes.new(type='ShaderNodeTexImage')
    texture_node.location = (0,0)

    # Load the image
    image = bpy.data.images.load(image_path)
    texture_node.image = image

    # Create a BSDF shader
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (200,0)

    # Link Image Texture node to BSDF
    material.node_tree.links.new(bsdf.inputs['Base Color'], texture_node.outputs['Color'])

    # Create Material Output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400,0)

    # Link BSDF to Material Output
    material.node_tree.links.new(output_node.inputs['Surface'], bsdf.outputs['BSDF'])


def mrfl_import_head_mesh_from_fbx(
        context: bpy.types.Context,
        path: str) -> bpy.types.Object:
    path = bpy.path.abspath(path)
    objects = import_fbx(context, path)
    meshes = [obj for obj in objects if obj.type == 'MESH']

    if len(meshes) == 0:
        raise Exception('The face FBX file does not contain any mesh')
    
    grouped_by_lods = sort_lods(objects)
    min_lod = min(grouped_by_lods.keys())
    print(f"DEBUG: min lod = {min_lod}")
    lod_meshes = grouped_by_lods[min_lod]

    head, teeth, left_eye, right_eye = None, None, None, None
    if len(lod_meshes) == 1:
        # Split by material (default metahuman head right after "Export as FBX")
        merged_object = lod_meshes[0]
        remove_empty_material_slots(merged_object)
        head_parts = []

        for material_index in range(len(merged_object.data.materials)):
            shader_name = FBX_SHADER_INDICES[min_lod][material_index]
            mat = bpy.data.materials.get(shader_name, None)
            if mat is None:
                mat = bpy.data.materials.new(shader_name)
            merged_object.data.materials[material_index] = mat


        parts = separate_by_material(merged_object)
        # Remove slised object as it does not exists any more
        objects.remove(merged_object)
        # Add all the parts (necessarty for further clenaing)
        objects.extend(parts)
        head_parts.extend(parts)

    else:
        head_parts = lod_meshes

    for obj in head_parts:
        if len(obj.data.materials) == 0:
            raise Exception(
                f'The mesh object {obj.name} has no materials assigned which is necessary'
                ' to identify the head part (skin, teeth or eyes)'
            )
        shader_name = obj.data.materials[0].name.lower()
        shader_name = shader_name.split('.')[0]
        if 'head' in shader_name:
            head = obj
            obj.name = 'mrfl_head'
            obj.data.name = 'mrfl_head'
        elif 'teeth' in shader_name:
            teeth = obj
            obj.name = 'mrfl_teeth'
            obj.data.name = 'mrfl_teeth'
        elif 'eyeleft' in shader_name:
            left_eye = obj
            obj.name = 'mrfl_leftEye'
            obj.data.name = 'mrfl_leftEye'
        elif 'eyeright' in shader_name:
            right_eye = obj
            obj.name = 'mrfl_rightEye'
            obj.data.name = 'mrfl_rightEye'

    result = (head, teeth, left_eye, right_eye)
    
    # Clear all unnecessary objects
    for obj in objects:
        if obj not in result:
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            # Clear data
            obj.data.animation_data_clear()
            obj.modifiers.clear()
            obj.shape_key_clear()
            link_object_to_collection(obj, MRFL_EDIT_MESHES_COLLECTION, overwrite=True)

    return result



def mrfl_import_body_mesh_from_fbx(
        context: bpy.types.Context,
        path: str) -> bpy.types.Object:
    
    path = bpy.path.abspath(path)
    objects = import_fbx(context, path)
    meshes = [obj for obj in objects if obj.type == 'MESH']
    if len(meshes) >= 1:
        meshes = sort_objects_by_base_name(meshes)
        body_mesh = meshes[0]
    else:
        raise Exception('The body FBX file does not contain any mesh')
    
    # Clear all unnecessary objects
    for obj in objects:
        if obj is not body_mesh:
            bpy.data.objects.remove(obj, do_unlink=True)
    
    body_mesh.data.animation_data_clear()
    body_mesh.modifiers.clear()
    body_mesh.shape_key_clear()
    return body_mesh


def initialize(context: bpy.types.Context) -> None:
    config = get_main_prop(context)
    skin_meshes = []
    teeth = None
    left_eye = None
    right_eye = None
    if config.import_head:
        head, teeth, left_eye, right_eye = mrfl_import_head_mesh_from_fbx(context, config.fbx_head_path)
        skin_meshes.append(head)
    if config.import_body:
        body = mrfl_import_body_mesh_from_fbx(context, config.fbx_body_path)
        skin_meshes.append(body)

    if len(skin_meshes) == 1:
        body = skin_meshes[0]
    elif len(skin_meshes) > 1:
        # Generate a merged mesh for easeer sculpting
        body = join_objects(skin_meshes)
        merge_threshold = calc_adaptive_merge_distance(body, factor=0.1)
        print(f'Welding head and body with threshould={merge_threshold:.6f}')
        merge_by_distance(body, threshold=merge_threshold, boundary_edges=True)

    if body:
        config.body = body

    if teeth:
        config.teeth = teeth
    
    if left_eye:
        config.left_eye = left_eye

    if right_eye:
        config.right_eye = right_eye

    return {'FINISHED'}

"""
INPUT VALIDATION
"""
def filepath_is_valid(path: str, extention: str) -> bool:
    # Check if the file exists
    if not os.path.exists(path):
        return False
    _, ext = os.path.splitext(path)
    if ext.lower() != extention.lower():
        return False
    return True
    

def check_for_import(context: bpy.types.Context) -> Tuple[bool, str]:
    config = get_main_prop(context)
    if config.import_head:
        path = bpy.path.abspath(config.fbx_head_path)
        if not filepath_is_valid(path, '.fbx'):
            return False, 'Invalid head FBX path'
    if config.import_body:
        path = bpy.path.abspath(config.fbx_body_path)
        if not filepath_is_valid(path, '.fbx'):
            return False, 'Invalid body FBX path'
    return True, 'Ok'

"""
END OF INPUT VALIDATION
"""


class MRFL_OT_import(bpy.types.Operator):
    """
    Import MetaHuman head and body according to entered parameters.
    """
    bl_idname = 'metareforge_lite.import'
    bl_label = 'Import'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Import metahuman head and body. It is recommended to import both'
     
    def execute(self, context):
        try:
            initialize(context)
            self.report({'INFO'}, f'Import completed.')
            return {'FINISHED'}
        except Exception as ex:
            msg = f'Import failed: {str(ex)}'
            print('ERROR: {msg}')
            print(traceback.format_exc())
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
    


classes = [MRFL_OT_import]  

def register():
    for cl in classes:
        bpy.utils.register_class(cl)  


def unregister():
    for cl in classes:
        bpy.utils.unregister_class(cl)


if __name__ == '__main__':
    register()
