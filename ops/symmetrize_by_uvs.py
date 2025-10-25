import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
from ..props.mesh_edit_prop import SYMMETRIZE_ALL_MODES, SYMMETRIZE_SELECTED_MODES


class UVSymmetrizeBase:
    """Base class with shared functionality for UV symmetrization"""
    
    def build_uv_data(self, mesh):
        """Build KDTree and mappings from UV coordinates"""
        uv_layer = mesh.uv_layers.active.data
        
        # Build KDTree with UV coordinates and create mappings
        kd = KDTree(len(mesh.loops))
        loop_to_vert = {}
        vert_to_loops = {}
        
        for loop_idx, loop in enumerate(mesh.loops):
            uv = uv_layer[loop_idx].uv
            uv_3d = Vector((uv.x, uv.y, 0.0))
            kd.insert(uv_3d, loop_idx)
            
            loop_to_vert[loop_idx] = loop.vertex_index
            if loop.vertex_index not in vert_to_loops:
                vert_to_loops[loop.vertex_index] = []
            vert_to_loops[loop.vertex_index].append(loop_idx)
        
        kd.balance()
        return kd, loop_to_vert, vert_to_loops, uv_layer
    
    def get_symmetrical_uv(self, original_uv):
        """Calculate symmetrical UV coordinate"""
        tile_u = int(original_uv.x // 1)
        fract_u = original_uv.x % 1
        new_u = tile_u + (1.0 - fract_u)
        return Vector((new_u, original_uv.y))
    
    def is_mid_point(self, uv, tolerance):
        """Check if UV coordinate is at the center (u % 1 == 0.5)"""
        fract_u = uv.x % 1
        return abs(fract_u - 0.5) < tolerance
    
    def find_symmetrical_vertex(self, vert_idx, kd, loop_to_vert, vert_to_loops, uv_layer):
        """Find the symmetrical vertex for a given vertex"""
        if vert_idx not in vert_to_loops:
            return None
        
        loop_idx = vert_to_loops[vert_idx][0]
        original_uv = uv_layer[loop_idx].uv
        symmetrical_uv = self.get_symmetrical_uv(original_uv)
        
        target_uv_3d = Vector((symmetrical_uv.x, symmetrical_uv.y, 0.0))
        closest_uv_3d, closest_loop_idx, dist = kd.find(target_uv_3d)
        
        if closest_loop_idx is not None:
            return loop_to_vert[closest_loop_idx]
        return None


class MRFL_OT_symmetrize_selected_by_uvs(bpy.types.Operator, UVSymmetrizeBase):
    """Symmetrize selected vertices based on UV coordinates"""
    bl_idname = "metareforge_lite.symmetrize_selected_by_uv"
    bl_label = "Symmetrize Selected by UVs"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: bpy.props.EnumProperty(
        items=SYMMETRIZE_SELECTED_MODES,
        name="Mode",
        default='SNAP_TO_SYMMETRICAL'
    )
    
    tolerance: bpy.props.FloatProperty(
        name="Mid Point Tolerance",
        default=0.001,
        min=0.00001,
        max=1.0,
        precision=5,
        description="Tolerance for detecting mid-point vertices"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        # Store original mode
        original_mode = context.mode
        
        # Switch to object mode to read vertex selection
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Get selected vertices
        selected_verts = [v.index for v in mesh.vertices if v.select]
        
        if not selected_verts:
            self.report({'WARNING'}, "No vertices selected")
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
        
        # Check UV layer
        if not mesh.uv_layers.active:
            self.report({'ERROR'}, "No active UV layer")
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
        
        # Build UV data
        kd, loop_to_vert, vert_to_loops, uv_layer = self.build_uv_data(mesh)
        
        # Track processed vertices to avoid double processing
        processed_verts = set()
        symmetrized_count = 0
        
        for vert_idx in selected_verts:
            if vert_idx in processed_verts:
                continue
            
            if vert_idx not in vert_to_loops:
                continue
            
            # Get original UV and check if it's a mid-point
            loop_idx = vert_to_loops[vert_idx][0]
            original_uv = uv_layer[loop_idx].uv

            # Check if it's a traditional mid-point (u % 1 == 0.5)
            is_traditional_mid = self.is_mid_point(original_uv, self.tolerance)

            # Check if symmetrical vertex is the same vertex (self-symmetrical)
            sym_vert_idx = self.find_symmetrical_vertex(vert_idx, kd, loop_to_vert, vert_to_loops, uv_layer)
            is_self_symmetrical = sym_vert_idx == vert_idx
            
            if is_traditional_mid or is_self_symmetrical:
                # Mid-point vertex - align to x=0
                original_vert = mesh.vertices[vert_idx]  # or mesh.vertices[vert_idx] for the second operator
                original_vert.co.x = 0.0
                processed_verts.add(vert_idx)
                symmetrized_count += 1
                continue
            
            # Find symmetrical vertex
            sym_vert_idx = self.find_symmetrical_vertex(vert_idx, kd, loop_to_vert, vert_to_loops, uv_layer)
            
            if sym_vert_idx is None:
                continue
            
            original_vert = mesh.vertices[vert_idx]
            sym_vert = mesh.vertices[sym_vert_idx]
            
            if self.mode == 'SNAP_TO_SYMMETRICAL':
                if sym_vert_idx in selected_verts:
                    # Both vertices are selected - average their positions
                    original_co = original_vert.co.copy()
                    sym_co = sym_vert.co.copy()
                    
                    new_co = (Vector([-sym_co.x, sym_co.y, sym_co.z]) + original_co) * 0.5
                    original_vert.co = new_co
                    sym_vert.co = Vector([-new_co.x, new_co.y, new_co.z])
                    
                    processed_verts.add(vert_idx)
                    processed_verts.add(sym_vert_idx)
                    symmetrized_count += 2
                else:
                    # Only original vertex is selected - snap to symmetrical
                    sym_co = sym_vert.co
                    original_vert.co = Vector([-sym_co.x, sym_co.y, sym_co.z])
                    processed_verts.add(vert_idx)
                    symmetrized_count += 1
                    
            elif self.mode == 'COPY_TO_SYMMETRICAL':
                # Copy original to symmetrical side
                original_co = original_vert.co
                sym_vert.co = Vector([-original_co.x, original_co.y, original_co.z])
                processed_verts.add(vert_idx)
                symmetrized_count += 1
        
        # Update mesh
        mesh.update()
        
        # Return to original mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
        
        self.report({'INFO'}, f"Processed {symmetrized_count} vertices")
        return {'FINISHED'}


class MRFL_OT_symmetrize_all_by_uvs(bpy.types.Operator, UVSymmetrizeBase):
    """Symmetrize entire model based on UV coordinates"""
    bl_idname = "metareforge_lite.symmetrize_all_by_uvs"
    bl_label = "Symmetrize All by UVs"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: bpy.props.EnumProperty(
        items=SYMMETRIZE_ALL_MODES,
        name="Mode",
        default='AVERAGE'
    )

    save_original_shape: bpy.props.BoolProperty(
        name='Save Original as a Shapekey',
        default=True
    )
    
    tolerance: bpy.props.FloatProperty(
        name="Mid Point Tolerance",
        default=0.001,
        min=0.00001,
        max=1.0,
        precision=5,
        description="Tolerance for detecting mid-point vertices"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # Store original coordinates if we need to create a shapekey
        original_coords = None
        if self.save_original_shape:
            original_coords = [v.co.copy() for v in mesh.vertices]
        
        # Store original mode
        original_mode = context.mode
        
        # Switch to object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Check UV layer
        if not mesh.uv_layers.active:
            self.report({'ERROR'}, "No active UV layer")
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
        
        # Build UV data
        kd, loop_to_vert, vert_to_loops, uv_layer = self.build_uv_data(mesh)
        
        # Process all vertices
        processed_verts = set()
        symmetrized_count = 0
        
        for vert_idx in range(len(mesh.vertices)):
            if vert_idx in processed_verts:
                continue
                
            if vert_idx not in vert_to_loops:
                continue
            
            # Get original UV and check if it's a mid-point
            loop_idx = vert_to_loops[vert_idx][0]
            original_uv = uv_layer[loop_idx].uv
            
            if self.is_mid_point(original_uv, self.tolerance):
                # Mid-point vertex - align to x=0
                mesh.vertices[vert_idx].co.x = 0.0
                processed_verts.add(vert_idx)
                symmetrized_count += 1
                continue
            
            # Find symmetrical vertex
            sym_vert_idx = self.find_symmetrical_vertex(vert_idx, kd, loop_to_vert, vert_to_loops, uv_layer)
            
            if sym_vert_idx is None:
                continue
            
            original_vert = mesh.vertices[vert_idx]
            sym_vert = mesh.vertices[sym_vert_idx]
            
            # Determine which side is left/right based on UV coordinates
            fract_u = original_uv.x % 1
            is_left_side = fract_u < 0.5
            
            if self.mode == 'LEFT_TO_RIGHT':
                if is_left_side:
                    # Copy left to right
                    original_co = original_vert.co
                    sym_vert.co = Vector([-original_co.x, original_co.y, original_co.z])
                else:
                    # This is right side, skip (will be processed by its left counterpart)
                    continue
                    
            elif self.mode == 'RIGHT_TO_LEFT':
                if not is_left_side:
                    # Copy right to left
                    original_co = original_vert.co
                    sym_vert.co = Vector([-original_co.x, original_co.y, original_co.z])
                else:
                    # This is left side, skip (will be processed by its right counterpart)
                    continue
                    
            elif self.mode == 'AVERAGE':
                # Average both sides
                original_co = original_vert.co.copy()
                sym_co = sym_vert.co.copy()
                
                new_co = (Vector([-sym_co.x, sym_co.y, sym_co.z]) + original_co) * 0.5
                original_vert.co = new_co
                sym_vert.co = Vector([-new_co.x, new_co.y, new_co.z])
            
            processed_verts.add(vert_idx)
            processed_verts.add(sym_vert_idx)
            symmetrized_count += 2

        # Update mesh
        mesh.update()

        # Create shapekey with original positions if requested
        if self.save_original_shape and original_coords:
            # Ensure the mesh has a basis shapekey
            if not mesh.shape_keys:
                obj.shape_key_add(name="Basis")
            
            # Add new shapekey with original coordinates
            shapekey = obj.shape_key_add(name='OriginalShape')
            for i, coord in enumerate(original_coords):
                shapekey.data[i].co = coord
        
        # Return to original mode
        if original_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
        
        self.report({'INFO'}, f"Processed {symmetrized_count} vertices")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.separator()
    self.layout.operator(MRFL_OT_symmetrize_selected_by_uvs.bl_idname)
    self.layout.operator(MRFL_OT_symmetrize_all_by_uvs.bl_idname)


def register():
    bpy.utils.register_class(MRFL_OT_symmetrize_selected_by_uvs)
    bpy.utils.register_class(MRFL_OT_symmetrize_all_by_uvs)
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func)


def unregister():
    bpy.utils.unregister_class(MRFL_OT_symmetrize_selected_by_uvs)
    bpy.utils.unregister_class(MRFL_OT_symmetrize_all_by_uvs)
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func)
