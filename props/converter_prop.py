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


TRANSFER_CONFIGS_PATH = os.path.join(ADDON_DIRECTORY, 'wrapping_configs')


# Global dictionary to store configs - populated at startup
CONFIG_CACHE = {}

def scan_transfer_configs():
    """Scan the transfer configs directory and populate the cache"""
    global CONFIG_CACHE
    CONFIG_CACHE.clear()
    
    if not os.path.exists(TRANSFER_CONFIGS_PATH):
        print(f"Transfer configs path does not exist: {TRANSFER_CONFIGS_PATH}")
        return
    
    try:
        for item in os.listdir(TRANSFER_CONFIGS_PATH):
            folder_path = os.path.join(TRANSFER_CONFIGS_PATH, item)
            
            # Only process directories
            if os.path.isdir(folder_path):
                json_files = []
                
                # Get all JSON files in the folder
                for file in os.listdir(folder_path):
                    if file.endswith('.json'):
                        # Remove .json extension
                        config_name = file[:-5]
                        json_files.append(config_name)
                
                # Only add categories that have JSON files
                if json_files:
                    CONFIG_CACHE[item] = sorted(json_files)
        
        print(f"Scanned {len(CONFIG_CACHE)} categories with configs")
        
        print(CONFIG_CACHE)
    except Exception as e:
        print(f"Error scanning transfer configs: {e}")

def get_category_items(self, context):
    """Return items for category enum"""
    items = []
    
    for i, category in enumerate(sorted(CONFIG_CACHE.keys())):
        items.append((category, category, f"Category: {category}", i))
    
    if not items:
        items.append(('NONE', 'No Categories', 'No categories found', 0))
    
    return items

def get_main_prop_items(self, context):
    """Return items for config enum based on selected category"""
    items = []
    props = context.scene.mrfl_converter_prop
    # Get the current category
    category = getattr(props, 'category', None)
    
    if category and category in CONFIG_CACHE:
        configs = CONFIG_CACHE[category]
        
        for i, config in enumerate(configs):
            items.append((config, config, f"Config: {config}", i))
    
    if not items:
        items.append(('NONE', 'No Configs', 'No configs found for this category', 0))
    
    return items

def update_category(self, context):
    """Called when category changes - forces config enum to update"""
    # Force the config property to update by clearing and resetting it
    props = context.scene.mrfl_converter_prop
    current_config = props.config
    
    # Trigger enum update by accessing the property
    # The enum will automatically update due to the callback
    try:
        props.config = props.config  
    except:
        pass

class MRFL_converter_property(PropertyGroup):
    """Properties for UV Transfer addon"""

    new_config_category: StringProperty(name='Config Category', default='Custom')
    new_config_name: StringProperty(name='Config Name', default='new')
    new_config_source_object: PointerProperty(
        name="Source Object",
        description="Mesh object to copy UV coordinates from",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    new_config_target_object: PointerProperty(
        name="Target Object", 
        description="Mesh object to apply UV coordinates to",
        type=Object,
        poll=lambda self, obj: obj.type == 'MESH'
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

    category: EnumProperty(
        name="Category",
        description="Select transfer config category (folder)",
        items=get_category_items,
        update=update_category
    )
    
    config: EnumProperty(
        name="Config",
        description="Select transfer config (JSON file)",
        items=get_main_prop_items
    )

    selective_smoothing: BoolProperty(name='Selective Smooth', default=True)
    selective_smoothing_factor: FloatProperty(name='Selective Smoothing Factor', default=0.25, min=0.0, max=1.0)
    selective_smoothing_repeats: IntProperty(name='Selective Smoothing Repeats', default=30, min=0, max=50)

    full_smoothing: BoolProperty(name='Smooth All', default=True)
    full_smoothing_factor: FloatProperty(name='Smoothing Factor', default=0.05, min=0.0, max=1.0)
    full_smoothing_repeats: IntProperty(name='Smoothing Repeats', default=30, min=0, max=50)


def register():
    bpy.utils.register_class(MRFL_converter_property)
    bpy.types.Scene.mrfl_converter_prop = bpy.props.PointerProperty(type=MRFL_converter_property)
    scan_transfer_configs()


def unregister():
    bpy.utils.unregister_class(MRFL_converter_property)
    del bpy.types.Scene.mrfl_converter_prop

