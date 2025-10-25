from . import (
    message_box,
    setup_scene,
    file_selector,
    initialize,
    convert,
    generate_template,
    export_templates,
    show_hint,
    symmetrize_by_uvs 
)


modules = [
    show_hint,
    message_box,
    setup_scene,
    file_selector,
    initialize,
    convert,
    generate_template,
    export_templates,
    symmetrize_by_uvs
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()
