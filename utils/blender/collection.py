import bpy
from typing import List, Dict


def get_collections_hide_viewport() -> Dict[str, bool]:
    """
    Retrieves the hide_viewport (eye icon in Blender's outliner) status of all collections in the Blender data block.

    Returns:
        dict: A dictionary mapping collection names to their hide_viewport status.
    """
    states = {}
    for collection in bpy.data.collections:
        states[collection.name] = collection.hide_viewport
    return states


def set_collections_hide_viewport(hide_viewport_dict: Dict[str, bool]) -> None:
    """
    Sets the hide_viewport status (eye icon in Blender's outliner) of all collections in the Blender data block based on a provided dictionary.

    Args:
        hide_viewport_dict (dict): A dictionary mapping collection names to their desired hide_viewport status.
    """
    for collection_name, hide_status in hide_viewport_dict.items():
        if collection_name in bpy.data.collections:
            bpy.data.collections[collection_name].hide_viewport = hide_status



def get_view_layer_collections_hide_viewport(layer_collection: bpy.types.LayerCollection = None) -> Dict[str, bool]:
    """
    Recursively retrieves the hide_viewport (monitor icon in Blender's outliner) status of collections in a view layer.

    Args:
        layer_collection (bpy.types.LayerCollection, optional): The starting layer collection. If None, starts with the main layer collection.

    Returns:
        dict: A dictionary mapping collection names to their hide_viewport status.
    """
    states = {}
    if layer_collection is None:
        layer_collection = bpy.context.view_layer.layer_collection

    for child in layer_collection.children:
        states[child.name] = child.hide_viewport
        states.update(get_view_layer_collections_hide_viewport(child))

    return states


def set_view_layer_collections_hide_viewport(hide_viewport_dict: Dict[str, bool], layer_collection: bpy.types.LayerCollection = None) -> None:
    """
    Sets the hide_viewport status (monitor icon in Blender's outliner) of collections in a view layer based on a provided dictionary.

    Args:
        hide_viewport_dict (dict): A dictionary mapping collection names to their desired hide_viewport status.
        layer_collection (bpy.types.LayerCollection, optional): The starting layer collection. If None, starts with the main layer collection.
    """
    if layer_collection is None:
        layer_collection = bpy.context.view_layer.layer_collection

    for child in layer_collection.children:
        if child.name in hide_viewport_dict:
            child.hide_viewport = hide_viewport_dict[child.name]
        set_view_layer_collections_hide_viewport(hide_viewport_dict, child)


def get_view_layer_collections_exclude(layer_collection: bpy.types.LayerCollection = None) -> Dict[str, bool]:
    """
    Recursively retrieves the exclude status of collections in a view layer.

    Args:
        layer_collection (bpy.types.LayerCollection, optional): The starting layer collection. If None, starts with the main layer collection.

    Returns:
        dict: A dictionary mapping collection names to their exclude status.
    """
    states = {}
    if layer_collection is None:
        layer_collection = bpy.context.view_layer.layer_collection

    for child in layer_collection.children:
        states[child.name] = child.exclude
        states.update(get_view_layer_collections_exclude(child))

    return states


def set_view_layer_collections_exclude(exclude_dict: Dict[str, bool], layer_collection: bpy.types.LayerCollection = None) -> None:
    """
    Sets the exclude status of collections in a view layer based on a provided dictionary.

    Args:
        exclude_dict (dict): A dictionary mapping collection names to their desired exclude status.
        layer_collection (bpy.types.LayerCollection, optional): The starting layer collection. If None, starts with the main layer collection.
    """
    if layer_collection is None:
        layer_collection = bpy.context.view_layer.layer_collection

    for child in layer_collection.children:
        if child.name in exclude_dict:
            child.exclude = exclude_dict[child.name]
        set_view_layer_collections_exclude(exclude_dict, child)


def get_collection(collection_name: str, ensure_exist: bool = False) -> bpy.types.Collection:    
    """
    Retrieves a collection by name or creates it if it doesn't exist and `ensure_exist` is True.

    Args:
        collection_name (str): The name of the collection to retrieve or create.
        ensure_exist (bool, optional): If True, creates the collection if it does not exist. Defaults to False.

    Returns:
        bpy.types.Collection: The found or created collection, or None if not found and `ensure_exist` is False.
    """
    if collection_name in bpy.data.collections:
        return bpy.data.collections[collection_name]
    else:
        if ensure_exist:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)
            return new_collection
        else:
            return None
    

def get_view_layer_collection(collection_name: str, layer_collection=None) -> bpy.types.LayerCollection:
    """
    Recursively searches and returns a LayerCollection by its name.

    Args:
        collection_name (str): The name of the collection to find.
        layer_collection (bpy.types.LayerCollection, optional): Starting point for the search. Defaults to the main layer collection.

    Returns:
        bpy.types.LayerCollection: The found layer collection or None if not found.
    """
    if layer_collection is None:
        layer_collection = bpy.context.view_layer.layer_collection

    if layer_collection.name == collection_name:
        return layer_collection

    for child in layer_collection.children:
        found = get_view_layer_collection(collection_name, child)
        if found:
            return found

    return None


def collection_set_exclude(collection_name: str, exclude: bool) -> None:
    """
    Sets the exclude state of a collection.

    Args:
        collection_name (str): The name of the collection to modify.
        exclude (bool): The state to set for the collection's exclude flag.
    """
    collection = get_view_layer_collection(collection_name)
    if collection:
        collection.exclude = exclude

def collection_get_exclude(collection_name: str) -> bool:
    """
    Gets the exclude state of a collection.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        bool: The exclude state of the collection, or None if the collection is not found.
    """
    collection = get_view_layer_collection(collection_name)
    return collection.exclude if collection else None


def collection_set_hide_viewport(collection_name: str, hide: bool) -> None:
    """
    Sets the visibility (corresponds to the eye icon in Blender's outliner) of a collection.

    Args:
        collection_name (str): The name of the collection to modify.
        hide (bool): True to hide the collection, False to show it.
    """
    collection = get_view_layer_collection(collection_name)
    if collection:
        collection.hide_viewport = hide



def view_layer_collection_set_hide_viewport(collection_name: str, hide: bool) -> None:
    """
    Sets the viewport visibility (corresponds to the monitor icon in Blender's outliner) 
    of a view layer collection.

    Args:
        collection_name (str): The name of the collection to modify.
        hide (bool): True to hide the collection in the viewport, False to show it.
    """
    collection = bpy.data.collections.get(collection_name)
    if collection:
        collection.hide_viewport = hide


"""
LINKING OBJECTS TO COLLECTIONS
"""


def link_objects_to_collection(objects: List[bpy.types.Object], collection_name: str, override: bool = False) -> None:
    """
    Links a list of objects to a specified collection, optionally removing them from other collections.

    This function links each object in the provided list to the specified collection. If `override` is True, it first unlinks the objects from all other collections they belong to.

    Args:
        objects (List[bpy.types.Object]): The list of objects to link.
        collection_name (str): The name of the collection to link the objects to.
        override (bool, optional): If True, removes the objects from all other collections before linking. Defaults to False.
    """
    collection = get_collection(collection_name, ensure_exist=True)
    for obj in objects:
        if override:
            for coll in obj.users_collection:
                if coll != collection:
                    coll.objects.unlink(obj)
                    
        if collection_name not in obj.users_collection:
            if obj.name not in collection.objects:
                collection.objects.link(obj)


def link_object_to_collection(obj: bpy.types.Object, collection_name: str, overwrite: bool = False) -> None:
    """
    Links a single object to a specified collection, with an option to remove it from other collections.

    This function links the specified object to the collection with the given name. If `overwrite` is True, the object is first unlinked from any other collections it belongs to.

    Args:
        obj (bpy.types.Object): The object to link.
        collection_name (str): The name of the collection to link the object to.
        overwrite (bool, optional): If True, unlinks the object from all other collections before linking. Defaults to False.
    """
    if overwrite:
        for coll in obj.users_collection:
            if coll != collection_name:
                coll.objects.unlink(obj)

    if collection_name not in obj.users_collection:
        collection = get_collection(collection_name, ensure_exist=True)
        collection.objects.link(obj)


"""
ENSURING VISIBILITY OF COLLECTIONS ASSOCIATED WITH AN OBJECT IN THE VIEW LAYER
"""


def ensure_object_collections_visible(obj: bpy.types.Object) -> None:
    """
    Ensures that all collections in bpy.data.collections containing the specified object, and their parent collections, are visible.

    Args:
        obj (bpy.types.Object): The object for which to ensure collection visibility.
    """

    def make_parents_visible(child_coll_name):
        # Iterate through all collections to find parents of the current collection
        for coll in bpy.data.collections:
            if child_coll_name in [c.name for c in coll.children]:
                coll.hide_viewport = False
                make_parents_visible(coll.name)  # Recursively make parent collections visible

    for coll in obj.users_collection:
        coll.hide_viewport = False  # Make the collection containing the object visible
        make_parents_visible(coll.name)  # Make all parent collections visible


def ensure_object_view_layer_collections_visible(obj: bpy.types.Object) -> None:
    """
    Ensures that all parent collections of the given object are visible in the view layer.

    Args:
        obj (bpy.types.Object): The object to check and modify parent collections for.
    """
    root_layer_coll = bpy.context.view_layer.layer_collection

    def make_layer_collection_visible(layer_coll, target_name):
        if layer_coll.name == target_name:
            layer_coll.hide_viewport = False
            return True
        for child in layer_coll.children:
            if make_layer_collection_visible(child, target_name):
                layer_coll.hide_viewport = False
                return True
        return False

    for coll in obj.users_collection:
        make_layer_collection_visible(root_layer_coll, coll.name)


def ensure_object_view_layer_collections_included(obj: bpy.types.Object) -> None:
    """
    Ensures that all parent collections of the given object are included in the view layer.

    Args:
        obj (bpy.types.Object): The object to check and modify parent collections for.
    """
    root_layer_coll = bpy.context.view_layer.layer_collection

    def make_layer_collection_included(layer_coll, target_name):
        if layer_coll.name == target_name:
            if layer_coll.exclude:
                layer_coll.exclude = False
            return True
        for child in layer_coll.children:
            if make_layer_collection_included(child, target_name):
                if layer_coll.exclude:
                    layer_coll.exclude = False
                return True
        return False

    for coll in obj.users_collection:
        make_layer_collection_included(root_layer_coll, coll.name)
