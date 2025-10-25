import bpy
import mathutils
import math
import json


def categorize_bones(armature_name, root_bone_name):
    # Get the armature object
    armature = bpy.data.objects.get(armature_name)
    if not armature or armature.type != 'ARMATURE':
        print(f"Error: Armature '{armature_name}' not found or not an armature.")
        return
    
    # Ensure the armature is in pose mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    # Get the root bone
    root_bone = armature.pose.bones.get(root_bone_name)
    if not root_bone:
        print(f"Error: Bone '{root_bone_name}' not found in armature '{armature_name}'.")
        return
    
    # Recursively categorize bones
    bone_categories = {}

    def categorize_recursive(bone):
        children = bone.children
        if not children:  # No child bones, level 0
            return 0
        
        # Get the levels of all children and add 1
        child_levels = [categorize_recursive(child) for child in children]
        level = max(child_levels) + 1
        return level

    def assign_categories(bone, category):
        if category not in bone_categories:
            bone_categories[category] = []
        bone_categories[category].append(bone)

    # Traverse the hierarchy and categorize
    def traverse_bone_hierarchy(bone):
        level = categorize_recursive(bone)
        assign_categories(bone, level)
        for child in bone.children:
            traverse_bone_hierarchy(child)

    # Start traversal from the root bone
    traverse_bone_hierarchy(root_bone)
    data = {cat: [b.name for b in bones]for cat, bones in bone_categories.items()}
    with open(f"{root_bone_name}.json", "w") as f:
        json.dump(data, f, indent=4)




# CREATE CONFIG
# armature_name=bpy.context.active_object.name
# 
# # Example usage
# for root in ["FACIAL_C_FacialRoot", "FACIAL_C_Neck1Root", "FACIAL_C_Neck2Root"]:
#     categorize_and_colorize_bones(
#         armature_name=armature_name,
#         root_bone_name=root
#     )
