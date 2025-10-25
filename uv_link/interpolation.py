from typing import Dict, List
import time
from .geometry import TransferTrianglesCollection, TransferInput
import bpy


def get_transformed(
        triangles: TransferTrianglesCollection,
        vertices: Dict[int, List[TransferInput]]
):
    print("Searching for matching UV triangles...")
    t1 = time.time()
    new_vertices = dict()

    bpy.context.window_manager.progress_begin(0, len(vertices))
    # Find triangles which cover the target uv vertex
    for step, (vertex_index, uv_loops) in enumerate(vertices.items()):
        if step % 1000 == 0:
            bpy.context.window_manager.progress_update(step)
        options = list()
        for uv in uv_loops:
            new_3d_co = triangles.transfer_coordinates_using_closest_triangle(uv.co)
            if new_3d_co:
                options.append((new_3d_co, uv.weight))

        new_vertices[vertex_index] = options
    bpy.context.window_manager.progress_end()
    t2 = time.time()
    print(f"Finished. Time elapsed: {t2 - t1} seconds")
    return new_vertices
