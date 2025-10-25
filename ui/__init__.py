from . import (
    converter_preset_panel,
    main_panel,
    mesh_edit_panel
)


modules = [
    main_panel,
    mesh_edit_panel,
    converter_preset_panel
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()
