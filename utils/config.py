from bpy.types import Context
from ..props.main_prop import MRFL_main_prop
from ..props.converter_prop import MRFL_converter_property
from ..props.mesh_edit_prop import MRFL_mesh_edit_property


def get_main_prop(context: Context) -> MRFL_main_prop:
    return context.scene.mrfl_main_prop

def get_transfer_prop(context: Context) -> MRFL_converter_property:
    return context.scene.mrfl_converter_prop

def get_mesh_edit_prop(context: Context) -> MRFL_mesh_edit_property:
    return context.scene.mrfl_mesh_edit_prop
