from . import (
    mesh_io
)


modules = [
    mesh_io
]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in modules:
        module.unregister()
