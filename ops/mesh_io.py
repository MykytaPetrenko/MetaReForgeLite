import bpy
import json
import os
from bpy.props import StringProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup
from ..utils.mesh_json import (
    mesh_to_dict,
    dict_to_mesh,
    get_standard_meshes_dir
)


class MeshJSONProperties(PropertyGroup):
    mesh_name: StringProperty(
        name="Mesh Name",
        description="Name for saving/loading mesh",
        default="my_mesh"
    )

    save_3d: BoolProperty(name='Save 3d Coordinates', default=True)
    save_uv: BoolProperty(name='Save UVs', default=True)


class MESH_OT_save_json(Operator):
    """Save selected mesh as JSON"""
    bl_idname = "mesh.save_json"
    bl_label = "Save Mesh as JSON"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.mesh_json_props
        
        if not props.mesh_name:
            self.report({'ERROR'}, "Please enter a mesh name")
            return {'CANCELLED'}
        
        # Check if an object is selected
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}
        
        obj = context.active_object
        mesh = obj.data
        
        # Convert mesh to dictionary
        mesh_data = mesh_to_dict(mesh, co_3d=props.save_3d, co_uv=props.save_uv)
        
        # Save to JSON file
        meshes_dir = get_standard_meshes_dir()
        filename = f"{props.mesh_name}.json"
        filepath = os.path.join(meshes_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(mesh_data, f, indent=2)
            
            self.report({'INFO'}, f"Mesh saved as {filename}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save mesh: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class MESH_OT_load_json(Operator):
    """Load mesh from JSON"""
    bl_idname = "mesh.load_json"
    bl_label = "Load Mesh from JSON"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.mesh_json_props
        
        if not props.mesh_name:
            self.report({'ERROR'}, "Please enter a mesh name")
            return {'CANCELLED'}
        
        # Build file path
        meshes_dir = get_standard_meshes_dir()
        filename = f"{props.mesh_name}.json"
        filepath = os.path.join(meshes_dir, filename)
        
        # Check if file exists
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"File {filename} not found")
            return {'CANCELLED'}
        
        try:
            # Load JSON data
            with open(filepath, 'r') as f:
                mesh_data = json.load(f)
            
            # Create mesh from data
            mesh = dict_to_mesh(mesh_data, props.mesh_name)
            
            # Create object and link to scene
            obj = bpy.data.objects.new(props.mesh_name, mesh)
            context.collection.objects.link(obj)
            
            # Select the new object
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            self.report({'INFO'}, f"Mesh {props.mesh_name} loaded successfully")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load mesh: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class VIEW3D_PT_mesh_json_panel(Panel):
    """UI Panel for Mesh JSON operations"""
    bl_label = "Mesh JSON"
    bl_idname = "VIEW3D_PT_mesh_json_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mesh JSON"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.mesh_json_props
        
        # Mesh name input
        layout.prop(props, "mesh_name")
        
        # Save button
        layout.separator()
        layout.label(text="Save:")
        layout.prop(props, 'save_3d', text='Vertex Coordinates')
        layout.prop(props, 'save_uv', text='Uvs')
        layout.operator('mesh.save_json', text='Save Selected Mesh')
        
        # Load button
        layout.separator()
        layout.label(text="Load:")
        layout.operator("mesh.load_json", text="Load Mesh")
        
        # Info
        layout.separator()
        layout.label(text="Files saved in:")
        layout.label(text="addon_directory/standard_meshes/")


classes = (
    MeshJSONProperties,
    MESH_OT_save_json,
    MESH_OT_load_json,
    VIEW3D_PT_mesh_json_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.mesh_json_props = bpy.props.PointerProperty(type=MeshJSONProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.mesh_json_props