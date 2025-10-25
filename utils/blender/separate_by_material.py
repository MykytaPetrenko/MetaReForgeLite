import bpy


def separate_by_material(obj: bpy.types.Object):
    """
    This function takes a mesh object and creates separate mesh objects
    for each material slot, containing only the faces with that material.
    """
    initial_name = obj.name
    # Store the current object names before duplication
    initial_obj_list = set(obj.name for obj in bpy.data.objects)
    
    # Ensure we're in object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Select the target object
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Separate the faces by material
    bpy.ops.mesh.separate(type='MATERIAL')

    # Store the new object names after separation
    final_obj_list = set(obj.name for obj in bpy.data.objects)
    diff = final_obj_list - initial_obj_list

    new_objects = [bpy.data.objects[obj_name] for obj_name in diff]
    new_objects.insert(0, obj)
    # Rename the new objects based on the original object name and the material name 
    for new_obj in new_objects:
        material_name = new_obj.material_slots[0].name
        new_obj.name = f"{initial_name}_{material_name}"
    return new_objects


if __name__ == "__main__":
    # Call the function on the active object name
    result = separate_by_material(bpy.context.active_object)
    print(result)
