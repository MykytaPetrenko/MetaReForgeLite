import os
import bpy
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    PointerProperty,
    EnumProperty
)
from bpy.types import PropertyGroup, Object
from ..globals import ADDON_DIRECTORY


TRANSFER_PRESETS_PATH = os.path.join(ADDON_DIRECTORY, 'wrapping_presets')


# Global dictionary to store presets - populated at startup
PRESET_CACHE = {}

def scan_transfer_presets():
    """Scan the transfer presets directory and populate the cache"""
    global PRESET_CACHE
    PRESET_CACHE.clear()
    
    if not os.path.exists(TRANSFER_PRESETS_PATH):
        print(f"Transfer presets path does not exist: {TRANSFER_PRESETS_PATH}")
        return
    
    try:
        for item in os.listdir(TRANSFER_PRESETS_PATH):
            folder_path = os.path.join(TRANSFER_PRESETS_PATH, item)
            
            # Only process directories
            if os.path.isdir(folder_path):
                json_files = []
                
                # Get all JSON files in the folder
                for file in os.listdir(folder_path):
                    if file.endswith('.json'):
                        # Remove .json extension
                        preset_name = file[:-5]
                        json_files.append(preset_name)
                
                # Only add categories that have JSON files
                if json_files:
                    PRESET_CACHE[item] = sorted(json_files)
        
        print(f"Scanned {len(PRESET_CACHE)} categories with presets")
        
        print(PRESET_CACHE)
    except Exception as e:
        print(f"Error scanning transfer presets: {e}")

def get_category_items(self, context):
    """Return items for category enum"""
    items = []
    
    for i, category in enumerate(sorted(PRESET_CACHE.keys())):
        items.append((category, category, f"Category: {category}", i))
    
    if not items:
        items.append(('NONE', 'No Categories', 'No categories found', 0))
    
    return items

def get_main_prop_items(self, context):
    """Return items for preset enum based on selected category"""
    items = []
    props = context.scene.mrfl_converter_prop
    # Get the current category
    category = getattr(props, 'preset_category', None)
    
    if category and category in PRESET_CACHE:
        presets = PRESET_CACHE[category]
        
        for i, preset in enumerate(presets):
            items.append((preset, preset, f'Preset: {preset}', i))
    
    if not items:
        items.append(('NONE', 'No Presets', 'No presets found for this category', 0))
    
    return items

def update_category(self, context):
    """Called when category changes - forces preset enum to update"""
    # Force the preset property to update by clearing and resetting it
    props = context.scene.mrfl_converter_prop
    current_preset = props.preset_name
    
    # Trigger enum update by accessing the property
    # The enum will automatically update due to the callback
    try:
        props.preset_name = props.preset_name  
    except:
        pass

class MRFL_converter_property(PropertyGroup):
    """Properties for UV Transfer addon"""

    new_preset_category: StringProperty(name='Preset Category', default='Custom')
    new_preset_name: StringProperty(name='Preset Name', default='new')
    new_preset_source_object: PointerProperty(
        name="Source Object",
        description="Mesh object to copy UV coordinates from",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    new_preset_target_object: PointerProperty(
        name="Target Object", 
        description="Mesh object to apply UV coordinates to",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    new_preset_tag: StringProperty(
        name='Preset Tag',
        default=''
    )
    smoothing_vertex_group: StringProperty(
        name='Smooth Group',
        default=''
    )


    source_object: PointerProperty(
        name="Source Object",
        description="Mesh object to copy UV coordinates from",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    target_object: PointerProperty(
        name="Target Object",
        description="Mesh object to apply UV coordinates to",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )

    preset_category: EnumProperty(
        name="Category",
        description="Select transfer preset category (folder)",
        items=get_category_items,
        update=update_category
    )
    
    preset_name: EnumProperty(
        name="Preset",
        description="Select transfer preset (JSON file)",
        items=get_main_prop_items
    )

    selective_smoothing: BoolProperty(name='Selective Smooth', default=True)
    selective_smoothing_factor: FloatProperty(name='Selective Smoothing Factor', default=0.25, min=0.0, max=1.0)
    selective_smoothing_repeats: IntProperty(name='Selective Smoothing Repeats', default=30, min=0, max=50)

    full_smoothing: BoolProperty(name='Smooth All', default=True)
    full_smoothing_factor: FloatProperty(name='Smoothing Factor', default=0.05, min=0.0, max=1.0)
    full_smoothing_repeats: IntProperty(name='Smoothing Repeats', default=30, min=0, max=50)

    preset_creation_progress: FloatProperty(name='Preset Creaton Progress', default=0, min=0, max=100, subtype='PERCENTAGE')


def register():
    bpy.utils.register_class(MRFL_converter_property)
    bpy.types.Scene.mrfl_converter_prop = bpy.props.PointerProperty(type=MRFL_converter_property)
    scan_transfer_presets()


def unregister():
    bpy.utils.unregister_class(MRFL_converter_property)
    del bpy.types.Scene.mrfl_converter_prop

