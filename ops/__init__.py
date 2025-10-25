from . import (
    message_box,
    setup_scene,
    file_selector,
    initialize,
    convert,
    generate_template,
    export_templates,
    show_hint,
    symmetrize_by_uvs,
    save_converter_preset,
    refresh_converter_presets
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
    symmetrize_by_uvs,
    save_converter_preset,
    refresh_converter_presets
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()
