from . import (
    main_panel,
    mesh_edit_panel
)


modules = [
    main_panel,
    mesh_edit_panel
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()
