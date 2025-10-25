import bpy
from bpy.types import Object as BObject
from bpy.types import PropertyGroup as BPropertyGroup

SYMMETRIZE_SELECTED_MODES =[
    ('SNAP_TO_SYMMETRICAL', 'Snap to Symmetrical', 'Snap selected vertices to their symmetrical positions'),
    ('COPY_TO_SYMMETRICAL', 'Copy to Symmetrical', 'Copy selected vertices positions to symmetrical side')
]

SYMMETRIZE_ALL_MODES = [
    ('AVERAGE', 'Average', 'Average left and right side positions'),
    ('LEFT_TO_RIGHT', 'Left to Right', 'Copy left side positions to right side'),
    ('RIGHT_TO_LEFT', 'Right to Left', 'Copy right side positions to left side')
]


class MRFL_mesh_edit_property(BPropertyGroup):
    mid_point_tolerance: bpy.props.FloatProperty(
        name="Mid Point Tolerance",
        default=0.001,
        min=0.00001,
        max=1.0,
        precision=5,
        description="Tolerance for detecting mid-point vertices"
    )

    symmetrize_selected_mode: bpy.props.EnumProperty(
        items=SYMMETRIZE_SELECTED_MODES,
        name="Mode",
        default='SNAP_TO_SYMMETRICAL'
    )

    symmetrize_all_mode: bpy.props.EnumProperty(
        items=SYMMETRIZE_ALL_MODES,
        name="Mode",
        default='AVERAGE'
    )

    save_original_shape: bpy.props.BoolProperty(
        name='Save Original Shape',
        default=True,
        description='Saves the original shape as a shape key named "OriginalShape"'
    )


def register():
    bpy.utils.register_class(MRFL_mesh_edit_property)
    bpy.types.Scene.mrfl_mesh_edit_prop = bpy.props.PointerProperty(type=MRFL_mesh_edit_property)


def unregister():
    bpy.utils.unregister_class(MRFL_mesh_edit_property)
    del bpy.types.Scene.mrfl_mesh_edit_prop