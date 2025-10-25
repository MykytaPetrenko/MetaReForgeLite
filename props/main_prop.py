import bpy
from bpy.types import Object as BObject
from bpy.types import PropertyGroup as BPropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    PointerProperty,
    EnumProperty
)

# Define enum items for head types
head_types = [
    ('DEFAULT', 'Default Head', 'Standard metahuman head that needs to be "Export as" FBX from UE editor after Bridge download. Default head has one object per LOD and will be split into different objects based on material slots'),
    ('MRF_OUTPUT', 'MRF Output', 'Pre-split head from MRF output that is already divided into different objects')
]

def poll_mesh(self, object: BObject):
    return True if object.type == 'MESH' else False


class MRFL_main_prop(BPropertyGroup):
    import_head: BoolProperty(name="Import Head", default=True)
    import_body: BoolProperty(name="Import Body", default=True)

    show_import_section: BoolProperty(name="Show Import", default=False)
    show_edit_meshes_section: BoolProperty(name='Show MRF-L Meshes', default=False)
    show_template_meshes_section: BoolProperty(name='Show Template Meshes', default=False)
    show_converter_section: BoolProperty(name='Show Transfer Section', default=False)
    # Property definition
    fbx_head_type: EnumProperty(
        name="Head Type",
        description="Choose between Default head from Bridge or pre-split MRF Output head",
        items=head_types,
        default="DEFAULT"
    )
    fbx_head_path: StringProperty(name="FBX Head Path")
    fbx_body_path: StringProperty(name="FBX Body Path")
    body: PointerProperty(name="Body", type=BObject, poll=poll_mesh)
    teeth: PointerProperty(name="Teeth", type=BObject, poll=poll_mesh)
    left_eye: PointerProperty(name="Left Eye", type=BObject, poll=poll_mesh)
    right_eye: PointerProperty(name="Right Eye", type=BObject, poll=poll_mesh)

    head_template: PointerProperty(name='Head Template', type=BObject, poll=poll_mesh)
    body_template: PointerProperty(name='Body Template', type=BObject, poll=poll_mesh)
    teeth_template: PointerProperty(name='Teeth Template', type=BObject, poll=poll_mesh)
    left_eye_template: PointerProperty(name='Left Eye Template', type=BObject, poll=poll_mesh)
    right_eye_template: PointerProperty(name='Right Eye Template', type=BObject, poll=poll_mesh)
    remove_old_templates: BoolProperty(
        name='Remove Old Templates',
        default=True,
        description=(
            'If True, removes the old template objects before creating new ones. '
            'If False, the new template meshes will be assigned, but the old objects '
            'will remain in the scene.'
        )
    )

    conformal_init_percentage: FloatProperty(name="Progress", default=0, min=0, max=100, subtype="PERCENTAGE")

    export_path: StringProperty(name='Export Path', subtype='DIR_PATH', default='')
    export_progress: FloatProperty(name='Export Progress', default=0, min=0, max=100, subtype='PERCENTAGE')


def register():
    bpy.utils.register_class(MRFL_main_prop)
    bpy.types.Scene.mrfl_main_prop = bpy.props.PointerProperty(type=MRFL_main_prop)


def unregister():
    bpy.utils.unregister_class(MRFL_main_prop)
    del bpy.types.Scene.mrfl_main_prop
