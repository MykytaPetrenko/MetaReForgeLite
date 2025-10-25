from . import (
    main_prop,
    converter_prop,
    mesh_edit_prop
)


modules = [
    main_prop,
    converter_prop,
    mesh_edit_prop
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()