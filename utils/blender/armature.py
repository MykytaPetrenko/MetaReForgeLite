import bpy
import math
import mathutils
from typing import List
from .unsorted import toggle_to_objects_edit_mode


def transfer_rest_pose(
        source_armature: bpy.types.Object,
        target_armature: bpy.types.Object,
        bone_names: List[str] = None
) -> None:
    """
    This function transfers the neutral (rest) bone transform matrices from the 
    source armature to the target armature. If a list of bone names is provided, 
    only those bones are affected. Otherwise, all bones are considered.

    Args:
        source_armature (bpy.types.Object): The source armature from which to copy.
        target_armature (bpy.types.Object): The target armature to apply the copied pose.
        bone_names (List[str], optional): Specific bone names to transfer. 
            If None, all bones are transferred. Defaults to None.

    Raises:
        TypeError: If either the source or target object is not an armature.

    Note:
        Both the source and target objects must be of type 'ARMATURE'.
    """
    # Ensure both objects are armatures
    if source_armature.type != 'ARMATURE' or target_armature.type != 'ARMATURE':
        raise TypeError("Error: Both source and target must be armatures.")
    
    toggle_to_objects_edit_mode(bpy.context, [source_armature, target_armature])

    for bone_name, source_bone in source_armature.data.edit_bones.items():
        if bone_name in target_armature.data.edit_bones:
            if bone_names and bone_name not in bone_names:
                continue
            target_armature.data.edit_bones[bone_name].matrix = source_bone.matrix

    bpy.ops.object.mode_set(mode='OBJECT')


def set_pose(armature_object: bpy.types.Object, pose_dict: dict, reset: bool = False):

    # Apply the translations to the specified pose bones
    for bone_name, transforms in pose_dict.items():
        if bone_name in armature_object.pose.bones:
            bone = armature_object.pose.bones[bone_name]
            if reset:
                zeros = mathutils.Vector([0.0, 0.0, 0.0])
                bone.location = zeros
                bone.rotation_mode = 'XYZ'
                bone.rotation_euler = zeros
                bone.scale = mathutils.Vector([1.0, 1.0, 1.0])
                continue
            location = transforms.get("LOC", None)
            if location:
                bone.location = mathutils.Vector(location)
            rotation = transforms.get("ROT", None)
            if rotation:
                bone.rotation_mode = 'XYZ'
                rotation = [math.radians(angle) for angle in rotation]
                bone.rotation_euler = mathutils.Euler(rotation, "XYZ")
            scale = transforms.get("SCALE", None)
            if scale:
                bone.scale = mathutils.Vector(scale)
        else:
            print(f"Bone '{bone_name}' not found in the armature.")


def reset_pose(armature_object: bpy.types.Object):
    # Apply the translations to the specified pose bones
    for bone in armature_object.pose.bones:
        zeros = mathutils.Vector([0.0, 0.0, 0.0])
        bone.location = zeros
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = zeros
        bone.scale = mathutils.Vector([1.0, 1.0, 1.0])


if __name__ == "__main__":
    pass
